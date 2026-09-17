import copy
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from workshop.catalog import EXAMPLES
from workshop.config import SCENARIOS, validate_endpoint
from workshop.runtime import calculate, dispatch, save_report, turn
from workshop.storage import FixtureStore


class WorkshopTests(unittest.TestCase):
    def result(self, scenario, **overrides):
        return calculate(FixtureStore(scenario), "solution", {**EXAMPLES[scenario], **overrides})

    def test_all_examples(self):
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                self.assertTrue(self.result(scenario)["synthetic"])

    def test_starter_modules_available(self):
        import importlib
        for scenario in SCENARIOS:
            with self.subTest(scenario=scenario):
                module = importlib.import_module(f"workshop.students.{scenario}")
                self.assertTrue(callable(module.calculate))

    def test_walkerhill_constraints(self):
        result = self.result("walkerhill")
        self.assertTrue(result["feasible"])
        self.assertEqual(result["total"], 160000)
        self.assertFalse(self.result("walkerhill", budget=0)["feasible"])
        self.assertFalse(self.result("walkerhill", date="2026-09-27")["feasible"])
        with self.assertRaises(ValueError):
            self.result("walkerhill", slot_ids=["WS1", "WS1"])

    def test_mintit_dates_and_ids(self):
        result = self.result("mintit")
        self.assertEqual(result["estimated_total"], 205000)
        self.assertEqual(result["estimated_total"], result["base"] + result["bonus"] - result["fee"])
        with self.assertRaises(ValueError):
            self.result("mintit", date="2027-01-01")
        with self.assertRaises(ValueError):
            self.result("mintit", quote_id="unknown")
        with self.assertRaises(ValueError):
            self.result("mintit", promotion_ids=["MP1", "MP3"])

    def test_speedmate(self):
        result = self.result("speedmate")
        self.assertGreater(len(result["candidates"]), 0)
        self.assertEqual([r["slot_id"] for r in result["candidates"]], ["ST1"])
        self.assertLessEqual(len(result["candidates"]), 3)
        self.assertEqual(self.result("speedmate", start_date="2027-01-01",
                                     end_date="2027-01-02")["candidates"], [])

    def test_incross_aggregate_and_empty(self):
        result = self.result("incross")
        self.assertEqual(result["totals"]["cost"], 450000)
        self.assertEqual(result["channels"]["search"]["metrics"]["CPA"]["value"], 16000)
        self.assertEqual(result["channels"]["search"]["metrics"]["CTR"]["value"], 0.0125)
        for channel in result["channels"].values():
            totals = channel["totals"]
            if totals["clicks"]:
                self.assertEqual(channel["metrics"]["CPC"]["value"], totals["cost"] / totals["clicks"])
        empty = self.result("incross", start_date="2027-01-01", end_date="2027-02-01")
        self.assertIsNone(empty["metrics"]["CPA"]["value"])
        self.assertTrue(empty["missing"])

    def test_intellix_unknown_not_zero(self):
        result = self.result("intellix")
        self.assertEqual(result["assessments"][0]["weighted_score"], 86)
        self.assertIsNone(result["ranking"])
        missing = [a for a in result["assessments"] if a["missing"]]
        self.assertTrue(missing)
        self.assertIsNone(missing[0]["weighted_score"])

    def test_queries_and_allowlist(self):
        store = FixtureStore("walkerhill")
        self.assertIsNone(store.get_record("program", "unknown"))
        for category in ("../../config.local.json", "daily"):
            with self.assertRaises(ValueError):
                store.list_records(category)
        with self.assertRaises(ValueError):
            dispatch(store, "solution", "run_sql", {"query": "DROP TABLE x"})

    def test_endpoint(self):
        validate_endpoint("https://demo.openai.azure.com/openai/v1/")
        for endpoint in ("https://evil.example/openai/v1/",
                         "https://demo.openai.azure.com/api/projects/x",
                         "http://demo.openai.azure.com/openai/v1/",
                         "https://demo.openai.azure.com.evil.example/openai/v1/"):
            with self.assertRaises(ValueError):
                validate_endpoint(endpoint)

    def test_save_boundary_and_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = save_report("synthetic", "report.txt", tmp)
            self.assertIn("synthetic", path.read_text(encoding="utf-8"))
            with self.assertRaises(FileExistsError):
                save_report("new", "report.txt", tmp)
            for bad in ("../leak.txt", "C:\\leak.txt", "sub/a.txt", ".env"):
                with self.assertRaises(ValueError):
                    save_report("data", bad, tmp)

    def test_model_tool_loop(self):
        call = SimpleNamespace(id="call1", function=SimpleNamespace(
            name="list_records", arguments='{"category":"program"}'))
        first = SimpleNamespace(tool_calls=[call], content=None)
        first.model_dump = lambda **kwargs: {
            "role": "assistant", "tool_calls": [{"id": "call1", "type": "function",
            "function": {"name": "list_records", "arguments": '{"category":"program"}'}}]}
        second = SimpleNamespace(tool_calls=None, content="Synthetic result")
        responses = iter([first, second])
        seen = []

        def create(**kwargs):
            seen.append(copy.deepcopy(kwargs["messages"]))
            return SimpleNamespace(choices=[SimpleNamespace(message=next(responses), finish_reason="stop")])

        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        history = [{"role": "system", "content": "test"}]
        self.assertEqual(turn(client, "deployment", FixtureStore("walkerhill"),
                              "solution", history, "test", log=lambda _: None), "Synthetic result")
        self.assertEqual(seen[1][-1]["role"], "tool")
        self.assertEqual(history[-1]["role"], "assistant")

    def test_model_limit_preserves_history(self):
        call = SimpleNamespace(id="repeat", function=SimpleNamespace(
            name="list_records", arguments='{"category":"program"}'))
        message = SimpleNamespace(tool_calls=[call], content=None)
        message.model_dump = lambda **kwargs: {
            "role": "assistant", "tool_calls": [{"id": "repeat", "type": "function",
            "function": {"name": "list_records", "arguments": '{"category":"program"}'}}]}
        def create(**kwargs):
            return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason="tool_calls")])
        client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
        history = [{"role": "system", "content": "test"}]
        with self.assertRaisesRegex(RuntimeError, "round limit"):
            turn(client, "deployment", FixtureStore("walkerhill"),
                 "solution", history, "test", log=lambda _: None)
        self.assertEqual(len(history), 1)

    def test_readonly_permissions(self):
        from workshop.__main__ import readonly_check
        for row, allowed in [((1, 0, 0, 0, 0, 0, 0), True),
                             ((1, 1, 0, 0, 0, 0, 0), False),
                             ((1, 0, 0, 0, 0, 0, 1), False),
                             ((None, None, None, None, None, None, None), False)]:
            with self.subTest(row=row):
                cursor = SimpleNamespace(execute=lambda query: None, fetchone=lambda: row, close=lambda: None)
                connection = SimpleNamespace(cursor=lambda: cursor)
                if allowed:
                    readonly_check(connection)
                else:
                    with self.assertRaises(PermissionError):
                        readonly_check(connection)


if __name__ == "__main__":
    unittest.main()
