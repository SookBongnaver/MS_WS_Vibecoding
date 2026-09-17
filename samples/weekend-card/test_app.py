from contextlib import closing
import copy
from datetime import date, timedelta
import json
from pathlib import Path
import sqlite3
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import app
import agent
import planner


def catalog():
    return json.loads(app.SNAPSHOT.read_text(encoding="utf-8"))


class CatalogTests(unittest.TestCase):
    def test_real_snapshot_shape_and_attribution(self):
        c = app.validate_catalog(catalog())
        self.assertEqual(len(c["items"]), 15)
        self.assertEqual(len({x["id"] for x in c["items"]}), 15)
        self.assertEqual({x["kind"] for x in c["items"]}, {"park", "culture", "event"})
        for item in c["items"]:
            self.assertTrue(item["source_name"])
        self.assertEqual(len(c["sources"]), 3)

    def test_coordinates_urls_and_missing(self):
        self.assertEqual(app.point("nan", "127"), (None, None))
        self.assertEqual(app.point("127", "37"), (None, None))
        self.assertEqual(app.point("37.5", "127.0"), (37.5, 127.0))
        self.assertIsNone(app.safe_url("javascript:alert(1)"))
        self.assertIsNone(app.safe_url("https://u:p@example.com"))
        p = app.normalize("culture", {"NUM":"1","FAC_NAME":"공간","X_COORD":"37.5","Y_COORD":"127"})
        self.assertEqual(p["lat"], 37.5)
        self.assertIsNone(p["fee_text"])
        self.assertIsNone(p["free"])
        with self.assertRaises(ValueError):
            app.normalize("event", {"TITLE":"행사"})

    def test_duplicate_snapshot_rejected(self):
        c = catalog()
        c["items"].append(c["items"][0])
        with self.assertRaises(ValueError):
            app.validate_catalog(c)

    def test_sqlite_roundtrip_and_invalid_preserves(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "weekend.sqlite3"
            with self.assertRaises(ValueError):
                app.read_catalog(db)
            self.assertFalse(db.exists())
            c = catalog()
            app.save_catalog(c, db)
            app.save_catalog(c, db)
            self.assertEqual(len(app.read_catalog(db)["items"]), 15)
            before = app.read_catalog(db)
            invalid = copy.deepcopy(c)
            invalid["mode"] = "fake"
            with self.assertRaises(ValueError):
                app.save_catalog(invalid, db)
            self.assertEqual(app.read_catalog(db), before)
            with closing(sqlite3.connect(db)) as conn:
                self.assertEqual(conn.execute("SELECT count(*) FROM catalog").fetchone()[0], 1)

    def test_http_routes(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "db.sqlite3"
            app.save_catalog(catalog(), db)
            server = app.ThreadingHTTPServer(("127.0.0.1", 0), app.handler(db))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            base = f"http://127.0.0.1:{server.server_port}"
            try:
                with urlopen(base + "/api/catalog", timeout=3) as r:
                    self.assertEqual(len(json.load(r)["items"]), 15)
                data = json.dumps({"preferences":{"date":"2026-09-19"}}).encode()
                with urlopen(Request(base + "/api/plan", data=data, headers={"Content-Type":"application/json"}), timeout=3) as r:
                    self.assertTrue(json.load(r)["courses"])
                for route in ("/app.py", "/data/weekend.sqlite3", "/../snapshot.json"):
                    with self.assertRaises(HTTPError) as caught:
                        urlopen(base + route, timeout=3)
                    self.assertEqual(caught.exception.code, 404)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()


class PlannerTests(unittest.TestCase):
    def test_three_courses_and_no_invented_ids(self):
        c = catalog()
        result = planner.candidates(c, {"date":"2026-09-19"})
        self.assertEqual(len(result["courses"]), 3)
        ids = {p["id"] for p in c["items"]}
        for course in result["courses"]:
            self.assertEqual(len({p["id"] for p in course["stops"]}), len(course["stops"]))
            self.assertLessEqual(len(course["stops"]), 3)
            self.assertTrue(all(p["id"] in ids for p in course["stops"]))
            self.assertFalse(any(p["kind"] == "event" for p in course["stops"]))

    def test_event_dates(self):
        c = catalog()
        event = next(p for p in c["items"] if p["kind"] == "event")
        r = planner.eligible(c, planner.preferences({"date":event["start_date"]}))
        self.assertIn(event["id"], [p["id"] for p in r])
        r = planner.eligible(c, planner.preferences({"date":event["start_date"],"exclude_events":True}))
        self.assertNotIn(event["id"], [p["id"] for p in r])

    def test_pinning_and_conflict(self):
        c = catalog()
        p = next(p for p in c["items"] if p["kind"]=="park")
        r = planner.candidates(c, {"date":"2026-09-19"}, p["id"], 1)
        self.assertTrue(r["courses"])
        self.assertTrue(all(p["id"] in [x["id"] for x in course["stops"]] for course in r["courses"]))
        r = planner.candidates(c, {"date":"2026-09-19","culture_only":True}, p["id"])
        self.assertEqual(r["courses"], [])
        self.assertIn("고정", r["reason"])

    def test_short_culture_empty_and_bad_input(self):
        c = catalog()
        r = planner.candidates(c, {"date":"2026-09-19","culture_only":True,"duration":"short"})
        for course in r["courses"]:
            self.assertLessEqual(len(course["stops"]), 2)
            self.assertTrue(all(p["kind"]=="culture" for p in course["stops"]))
        self.assertEqual(planner.candidates(c, {"date":"2026-09-19","district":"없는구"})["courses"], [])
        for p in ({}, {"date":"bad"}, {"date":"2026-09-19","mood":"bad"},
                  {"date":"2026-09-19","culture_only":"true"}):
            with self.assertRaises(ValueError):
                planner.candidates(c, p)


class AgentTests(unittest.TestCase):
    def test_rules_draft_and_stale_request(self):
        c = catalog()
        preview = agent.draft({"preferences":{"date":"2026-09-19"}}, c, "rules")
        self.assertIn("예약·결제는 하지 않았습니다", preview["text"])
        self.assertEqual(preview["mode"], "rules")
        with self.assertRaisesRegex(ValueError, "바뀌"):
            agent.request_courses({"preferences":{"date":"2026-09-19"}, "selected_ids":["park:1"],
                                   "catalog_fetched_at":"old"}, c)

    def test_model_must_use_tool_and_valid_course(self):
        c = catalog()
        pref, courses = agent.request_courses({"preferences":{"date":"2026-09-19"}}, c)
        responses = iter([
            {"choices":[{"message":{"role":"assistant","tool_calls":[{"id":"c1","type":"function",
                "function":{"name":"find_courses","arguments":"{}"}}]}}]},
            {"choices":[{"message":{"content":json.dumps({"course_id":courses[0]["id"],"reason":"공개 장소 조건과 일치합니다."})}}]},
        ])
        course, reason = agent.choose_with_model(pref, courses, lambda m,t: next(responses), log=lambda _:None)
        self.assertEqual(course["id"], courses[0]["id"])
        with self.assertRaises(ValueError):
            agent.choose_with_model(pref, courses, lambda m,t: {"choices":[{"message":{"content":'{"course_id":"invented","reason":"x"}'}}]})

    def test_notification_preview_no_mentions(self):
        p={"text":"@everyone 주말 한 장"}
        self.assertEqual(agent.notification_payload("discord", p)["allowed_mentions"]["parse"], [])
        self.assertEqual(agent.notification_payload("teams", p)["attachments"][0]["content"]["type"], "AdaptiveCard")
        with self.assertRaises(ValueError):
            agent.notification_payload("discord", {"text":"x"*2001})

    def test_no_send_without_confirmation_and_no_duplicate(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"preview.json"
            path.write_text(json.dumps({"text":"교육용 테스트입니다","date":(date.today()+timedelta(days=2)).isoformat()}),encoding="utf-8")
            with patch("agent.OUT",Path(tmp)), patch.dict("os.environ",{"DISCORD_WEBHOOK_URL":"https://discord.com/api/webhooks/123/FAKE_TEST_ONLY"}):
                with patch("agent.post_json") as post:
                    self.assertFalse(agent.send_preview(path,"discord","테스트",confirm=lambda _: "cancel"))
                    post.assert_not_called()
                with patch("agent.post_json",return_value=(200,{"id":"test"})) as post:
                    def approve(prompt):
                        return prompt.split("'")[1]
                    self.assertTrue(agent.send_preview(path,"discord","테스트",confirm=approve))
                    self.assertEqual(post.call_count,1)
                    with self.assertRaisesRegex(ValueError,"이미"):
                        agent.send_preview(path,"discord","다른 표시명",confirm=approve)

    def test_webhook_host_and_tls(self):
        for url in ("http://discord.com/api/webhooks/1/a", "https://discord.com.evil.test/api/webhooks/1/a"):
            with patch.dict("os.environ",{"DISCORD_WEBHOOK_URL":url}):
                with self.assertRaises(ValueError):
                    agent.webhook("discord")


if __name__ == "__main__":
    unittest.main()
