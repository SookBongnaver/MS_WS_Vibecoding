"""Offline contract tests; generated fixture values are never used by the app."""

from contextlib import closing
import copy
import io
import json
from pathlib import Path
import shutil
import sqlite3
import threading
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from uuid import uuid4

import app


def fixture(indicator):
    rows = [
        {"countryiso3code": code, "country": {"id": names[0]},
         "indicator": {"id": indicator}, "date": str(year), "value": 1000}
        for code, names in app.COUNTRIES.items() for year in app.YEARS
    ]
    return [{"page": 1, "pages": 1, "total": 30, "per_page": 100,
             "sourceid": "2", "lastupdated": "2024-07-01"}, rows]


def fixture_fetch(url):
    indicator = url.split("/indicator/")[1].split("?")[0]
    return fixture(indicator)


class ParseTests(unittest.TestCase):
    def test_missing_is_null_not_zero(self):
        payload = fixture("SP.POP.TOTL")
        payload[1][0]["value"], payload[1][1]["value"] = None, 0
        rows, updated = app.parse_response(payload, "SP.POP.TOTL")
        self.assertIsNone(rows[0][3])
        self.assertEqual(rows[1][3], 0)
        self.assertEqual(updated, "2024-07-01")
        self.assertEqual(len(rows), 30)

    def test_malformed_envelopes(self):
        for payload in (None, {}, [], [{"message": "Invalid value"}], [{}, None], [[], []]):
            with self.subTest(payload=payload), self.assertRaises(app.DataError):
                app.parse_response(payload, "SP.POP.TOTL")

    def test_reject_pagination_metadata_and_dates(self):
        changes = [
            ("page", 2), ("pages", 2), ("total", 29), ("per_page", 5),
            ("page", True), ("per_page", None), ("per_page", "many"),
            ("sourceid", "1"), ("lastupdated", None), ("lastupdated", "2024-02-30"),
            ("lastupdated", "20240701"), ("lastupdated", "9999-12-31"),
        ]
        for field, value in changes:
            payload = fixture("SP.POP.TOTL")
            payload[0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(app.DataError):
                app.parse_response(payload, "SP.POP.TOTL")

    def test_reject_invalid_ids_years_and_values(self):
        changes = [
            ("countryiso3code", "USA"), ("countryiso3code", []),
            ("country", {"id": "US"}), ("indicator", {"id": "UNKNOWN"}),
            ("date", "2019"), ("date", 2024), ("date", "2024-01-01"),
            ("value", True), ("value", "1000"), ("value", float("nan")),
            ("value", float("inf")), ("value", -1), ("value", 2**60),
            ("value", 1.5),
        ]
        for field, value in changes:
            payload = fixture("SP.POP.TOTL")
            payload[1][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(app.DataError):
                app.parse_response(payload, "SP.POP.TOTL")

    def test_reject_omissions_duplicates_and_nonobjects(self):
        base = fixture("SP.POP.TOTL")
        for change in ("short", "duplicate", "missing-value", "nonobject"):
            payload = copy.deepcopy(base)
            if change == "short":
                payload[1].pop()
            elif change == "duplicate":
                payload[1][0] = payload[1][1]
            elif change == "missing-value":
                del payload[1][0]["value"]
            else:
                payload[1][0] = None
            with self.subTest(change=change), self.assertRaises(app.DataError):
                app.parse_response(payload, "SP.POP.TOTL")

    def test_decimal_gdp_and_string_pagination_are_valid(self):
        payload = fixture("NY.GDP.PCAP.CD")
        payload[0].update(page="1", pages="1", total="30", per_page="100")
        payload[1][0]["value"] = 1234.56
        self.assertEqual(app.parse_response(payload, "NY.GDP.PCAP.CD")[0][0][3], 1234.56)


class FetchTests(unittest.TestCase):
    def fetch_bytes(self, content):
        response = io.BytesIO(content)
        response.status = 200
        with patch("app.urlopen", return_value=response) as opener:
            result = app.fetch_json("https://api.worldbank.org/test")
            self.assertEqual(opener.call_args.kwargs["timeout"], app.TIMEOUT)
            return result

    def test_valid_json(self):
        self.assertEqual(self.fetch_bytes(b'{"value":null}'), {"value": None})

    def test_reject_invalid_json_nonfinite_duplicate_fields_and_size(self):
        for content in (b"{bad", b"\xff", b'{"value":NaN}', b'{"x":1,"x":2}',
                        b" " * (app.MAX_BYTES + 1)):
            with self.subTest(size=len(content)), self.assertRaises(app.DataError):
                self.fetch_bytes(content)

    def test_network_failures_are_explicit(self):
        for error in (HTTPError("url", 503, "Unavailable", {}, None),
                      URLError("network unavailable"), TimeoutError("timed out")):
            with patch("app.urlopen", side_effect=error), self.assertRaises(app.DataError) as caught:
                app.fetch_json("https://api.worldbank.org/test")
            self.assertIn("https://api.worldbank.org/test", str(caught.exception))


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.directory = app.ROOT / "data" / ("test-" + uuid4().hex)
        self.directory.mkdir(parents=True)
        self.db = self.directory / "market.sqlite3"

    def tearDown(self):
        shutil.rmtree(self.directory)

    def snapshot(self):
        with closing(sqlite3.connect(self.db)) as connection:
            return (
                connection.execute("SELECT * FROM observations ORDER BY 1,2,3").fetchall(),
                connection.execute("SELECT * FROM sources ORDER BY 1").fetchall(),
            )

    def test_empty_read_does_not_create_database(self):
        self.assertEqual(app.read_data(self.db)["status"], "empty")
        self.assertFalse(self.db.exists())

    def test_idempotent_bounded_ingest_and_integrity(self):
        first = app.ingest(self.db, fixture_fetch)
        self.assertEqual(first["rows"], 60)
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("INSERT INTO observations VALUES ('USA','SP.POP.TOTL',2024,123)")
        second = app.ingest(self.db, fixture_fetch)
        self.assertEqual(second["rows"], 60)
        with closing(sqlite3.connect(self.db)) as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM observations").fetchone()[0], 61)
            self.assertEqual(connection.execute("SELECT value FROM observations WHERE country='USA'").fetchone()[0], 123)
            self.assertEqual(connection.execute("PRAGMA integrity_check").fetchone()[0], "ok")
        result = app.read_data(self.db)
        self.assertEqual(result["status"], "ready")
        self.assertEqual(len(result["observations"]), 60)
        self.assertEqual(len(result["sources"]), 2)
        self.assertTrue(all(source["fetched_at"].endswith("+00:00") for source in result["sources"]))

    def test_sql_null_and_zero_survive_ingest(self):
        def fetch(url):
            payload = fixture_fetch(url)
            payload[1][0]["value"], payload[1][1]["value"] = None, 0
            return payload
        self.assertEqual(app.ingest(self.db, fetch)["missing"], 2)
        values = [row["value"] for row in app.read_data(self.db)["observations"]]
        self.assertEqual(values.count(None), 2)
        self.assertEqual(values.count(0), 2)

    def test_invalid_second_response_leaves_old_database_unchanged(self):
        app.ingest(self.db, fixture_fetch)
        before = self.snapshot()
        def fetch(url):
            payload = fixture_fetch(url)
            if "NY.GDP.PCAP.CD" in url:
                payload[1].pop()
            return payload
        with self.assertRaises(app.DataError):
            app.ingest(self.db, fetch)
        self.assertEqual(self.snapshot(), before)

    def test_failed_first_ingest_does_not_create_database(self):
        with self.assertRaises(app.DataError):
            app.ingest(self.db, lambda url: [])
        self.assertFalse(self.db.exists())

    def test_database_failure_rolls_back_rows_and_provenance(self):
        app.ingest(self.db, fixture_fetch)
        before = self.snapshot()
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("""
                CREATE TRIGGER reject_insert BEFORE INSERT ON observations
                WHEN NEW.country='MYS' BEGIN SELECT RAISE(ABORT,'test failure'); END
            """)
        with self.assertRaises(sqlite3.IntegrityError):
            app.ingest(self.db, fixture_fetch)
        self.assertEqual(self.snapshot(), before)

    def test_read_uses_readonly_uri(self):
        app.ingest(self.db, fixture_fetch)
        original = sqlite3.connect
        with patch("app.sqlite3.connect", wraps=original) as connect:
            app.read_data(self.db)
        self.assertTrue(connect.call_args.args[0].endswith("?mode=ro"))
        self.assertTrue(connect.call_args.kwargs["uri"])

    def test_incomplete_database_is_an_error_not_an_empty_state(self):
        app.ingest(self.db, fixture_fetch)
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("DELETE FROM observations WHERE country='KOR'")
        with self.assertRaisesRegex(app.DataError, "incomplete"):
            app.read_data(self.db)

    def test_server_explicit_routes_and_no_writes(self):
        server = app.ThreadingHTTPServer(("127.0.0.1", 0), app.make_handler(self.db))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with urlopen(base + "/?scoutTheme=light", timeout=3) as response:
                self.assertEqual(response.status, 200)
                self.assertIn(b"MARKET EXPLORER", response.read())
                self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])
            with urlopen(base + "/api/data", timeout=3) as response:
                self.assertEqual(json.load(response)["status"], "empty")
            for route in ("/app.py", "/data/market.sqlite3", "/../app.py", "/%2e%2e/app.py",
                          "//api/data/extra", "/api/data/"):
                with self.subTest(route=route), self.assertRaises(HTTPError) as caught:
                    urlopen(base + route, timeout=3)
                self.assertEqual(caught.exception.code, 404)
            for method in ("POST", "PUT", "DELETE"):
                with self.subTest(method=method), self.assertRaises(HTTPError) as caught:
                    urlopen(Request(base + "/api/data", method=method), timeout=3)
                self.assertEqual(caught.exception.code, 501)
            self.assertFalse(self.db.exists())
            app.ingest(self.db, fixture_fetch)
            with urlopen(base + "/api/data", timeout=3) as response:
                self.assertEqual(len(json.load(response)["observations"]), 60)
            with closing(sqlite3.connect(self.db)) as connection, connection:
                connection.execute("DROP TABLE sources")
            with self.assertRaises(HTTPError) as caught:
                urlopen(base + "/api/data", timeout=3)
            self.assertEqual(caught.exception.code, 503)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
