"""World Bank public API -> local SQLite -> read-only localhost UI (stdlib only)."""

import argparse
from contextlib import closing
from datetime import date, datetime, timezone
from http import HTTPStatus
from http.client import HTTPException
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
from pathlib import Path
import sqlite3
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "market.sqlite3"
YEARS = tuple(range(2020, 2025))
COUNTRIES = {
    "KOR": ("KR", "대한민국", "Korea, Rep."),
    "MYS": ("MY", "말레이시아", "Malaysia"),
    "VNM": ("VN", "베트남", "Viet Nam"),
    "IDN": ("ID", "인도네시아", "Indonesia"),
    "THA": ("TH", "태국", "Thailand"),
    "IND": ("IN", "인도", "India"),
}
INDICATORS = {
    "SP.POP.TOTL": {"name": "인구", "unit": "명"},
    "NY.GDP.PCAP.CD": {"name": "1인당 GDP", "unit": "현재 US$ / 명"},
}
TIMEOUT = 20
MAX_BYTES = 1_048_576
EXPECTED_ROWS = len(COUNTRIES) * len(YEARS)


class DataError(ValueError):
    """An upstream response is unsafe to persist."""


def source_url(indicator):
    countries = ";".join(COUNTRIES).lower()
    return (
        f"https://api.worldbank.org/v2/country/{countries}/indicator/{indicator}"
        f"?format=json&date={YEARS[0]}:{YEARS[-1]}&per_page=100&source=2"
    )


def fetch_json(url):
    request = Request(url, headers={"Accept": "application/json",
                                   "User-Agent": "MarketExplorer-Workshop/1.0"})
    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            if response.status != 200:
                raise DataError(f"{url}: expected HTTP 200, got {response.status}")
            raw = response.read(MAX_BYTES + 1)
    except HTTPError as exc:
        raise DataError(f"{url}: HTTP {exc.code} {exc.reason}; retry ingest later") from exc
    except (URLError, TimeoutError, OSError, HTTPException) as exc:
        raise DataError(f"{url}: download failed ({exc}); timeout={TIMEOUT}s") from exc
    if len(raw) > MAX_BYTES:
        raise DataError(f"{url}: response exceeds {MAX_BYTES} bytes")

    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise DataError(f"{url}: duplicate JSON field {key!r}")
            result[key] = value
        return result

    def invalid_constant(value):
        raise DataError(f"{url}: non-finite JSON number {value}")

    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object,
                          parse_constant=invalid_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DataError(f"{url}: invalid UTF-8 JSON ({exc})") from exc


def parse_response(payload, indicator):
    """Require all 6 x 5 keys, including explicit null observations, on one page."""
    if indicator not in INDICATORS:
        raise DataError(f"Unsupported indicator: {indicator}")
    if not isinstance(payload, list) or len(payload) != 2:
        raise DataError(f"{indicator}: expected [metadata, observations], not an API error")
    meta, observations = payload
    if not isinstance(meta, dict) or not isinstance(observations, list):
        raise DataError(f"{indicator}: invalid metadata or observation list")
    for field, expected in (("page", 1), ("pages", 1), ("total", EXPECTED_ROWS)):
        value = meta.get(field)
        if type(value) not in (int, str) or str(value) != str(expected):
            raise DataError(f"{indicator}: {field} must be {expected}; got {value!r}. "
                            "Incomplete/paginated responses are rejected.")
    page_size = meta.get("per_page")
    if (type(page_size) not in (int, str) or not str(page_size).isascii()
            or not str(page_size).isdigit() or int(page_size) < EXPECTED_ROWS):
        raise DataError(f"{indicator}: invalid per_page: {page_size!r}")
    if meta.get("sourceid") != "2":
        raise DataError(f"{indicator}: expected World Development Indicators sourceid '2'")
    updated = meta.get("lastupdated")
    try:
        if not isinstance(updated, str) or len(updated) != 10:
            raise ValueError("expected YYYY-MM-DD")
        parsed_date = date.fromisoformat(updated)
        if parsed_date.isoformat() != updated or parsed_date > datetime.now(timezone.utc).date():
            raise ValueError("non-canonical or future date")
    except ValueError as exc:
        raise DataError(f"{indicator}: invalid lastupdated {updated!r}: {exc}") from exc
    if len(observations) != EXPECTED_ROWS:
        raise DataError(f"{indicator}: expected {EXPECTED_ROWS} observations; got {len(observations)}")
    rows, seen = [], set()
    for position, item in enumerate(observations, 1):
        prefix = f"{indicator} row {position}"
        if not isinstance(item, dict):
            raise DataError(f"{prefix}: observation must be an object")
        code, year = item.get("countryiso3code"), item.get("date")
        if not isinstance(code, str) or code not in COUNTRIES:
            raise DataError(f"{prefix}: invalid country ID {code!r}")
        country, series = item.get("country"), item.get("indicator")
        if not isinstance(country, dict) or country.get("id") != COUNTRIES[code][0]:
            raise DataError(f"{prefix}: mismatched ISO2/ISO3 country IDs")
        if not isinstance(series, dict) or series.get("id") != indicator:
            raise DataError(f"{prefix}: mismatched indicator ID")
        if type(year) is not str or year not in {str(y) for y in YEARS}:
            raise DataError(f"{prefix}: invalid year {year!r}")
        key = (code, int(year))
        if key in seen:
            raise DataError(f"{prefix}: duplicate country/year {key}")
        seen.add(key)
        if "value" not in item:
            raise DataError(f"{prefix}: missing value field (explicit null is allowed)")
        value = item["value"]
        if value is not None:
            if (type(value) not in (int, float) or not 0 <= value <= 2**53 - 1
                    or not math.isfinite(value)):
                raise DataError(f"{prefix}: value must be null or a finite nonnegative number")
            if indicator == "SP.POP.TOTL" and int(value) != value:
                raise DataError(f"{prefix}: population must be an integer")
        rows.append((code, indicator, int(year), value))
    expected = {(code, year) for code in COUNTRIES for year in YEARS}
    if seen != expected:
        raise DataError(f"{indicator}: incomplete country/year coverage")
    return rows, updated


def ingest(db_path=DB_PATH, fetcher=fetch_json):
    rows, sources = [], []
    for indicator in INDICATORS:
        url = source_url(indicator)
        parsed, updated = parse_response(fetcher(url), indicator)
        rows.extend(parsed)
        sources.append((indicator, url, updated))
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db_path, timeout=5)) as connection:
        # DDL, deletion and replacement share one explicit transaction.
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("""
                CREATE TABLE IF NOT EXISTS observations (
                    country TEXT NOT NULL, indicator TEXT NOT NULL,
                    year INTEGER NOT NULL, value REAL,
                    PRIMARY KEY (country, indicator, year)
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    indicator TEXT PRIMARY KEY, url TEXT NOT NULL,
                    lastupdated TEXT NOT NULL, fetched_at TEXT NOT NULL
                )
            """)
            connection.executemany(
                "DELETE FROM observations WHERE country=? AND indicator=? AND year=?",
                [(country, indicator, year) for country, indicator, year, _ in rows])
            connection.executemany("INSERT INTO observations VALUES (?, ?, ?, ?)", rows)
            connection.executemany("""
                INSERT INTO sources VALUES (?, ?, ?, ?)
                ON CONFLICT(indicator) DO UPDATE SET
                    url=excluded.url, lastupdated=excluded.lastupdated,
                    fetched_at=excluded.fetched_at
            """, [(*source, fetched_at) for source in sources])
    return {"rows": len(rows), "missing": sum(row[3] is None for row in rows),
            "fetched_at": fetched_at,
            "sources": [{"indicator": i, "url": url, "lastupdated": d} for i, url, d in sources]}


def read_data(db_path=DB_PATH):
    result = {
        "status": "empty", "years": list(YEARS),
        "countries": [{"code": code, "name": names[1], "english": names[2]}
                      for code, names in COUNTRIES.items()],
        "indicators": INDICATORS, "observations": [], "sources": [],
    }
    db_path = Path(db_path)
    if not db_path.exists():
        return result
    with closing(sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro",
                                uri=True, timeout=5)) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("BEGIN")
        result["observations"] = [
            dict(row) for row in connection.execute("""
                SELECT country, indicator, year, value FROM observations
                WHERE country IN (?, ?, ?, ?, ?, ?) AND indicator IN (?, ?)
                    AND year BETWEEN ? AND ?
                ORDER BY country, indicator, year
            """, (*COUNTRIES, *INDICATORS, YEARS[0], YEARS[-1]))]
        result["sources"] = [
            dict(row) for row in connection.execute(
                "SELECT indicator, url, lastupdated, fetched_at FROM sources "
                "WHERE indicator IN (?, ?) ORDER BY indicator", tuple(INDICATORS))]
    if (len(result["observations"]) != EXPECTED_ROWS * len(INDICATORS)
            or len(result["sources"]) != len(INDICATORS)):
        raise DataError("SQLite dataset is incomplete; run python app.py ingest again")
    result["status"] = "ready"
    return result


def make_handler(db_path=DB_PATH):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            route = urlsplit(self.path).path
            if route == "/":
                try:
                    content = (ROOT / "index.html").read_bytes()
                except OSError as exc:
                    self.respond(HTTPStatus.SERVICE_UNAVAILABLE, {"error": str(exc)})
                    return
                self.respond(HTTPStatus.OK, content, "text/html; charset=utf-8")
            elif route == "/api/data":
                try:
                    self.respond(HTTPStatus.OK, read_data(db_path))
                except (sqlite3.Error, DataError, OSError) as exc:
                    self.respond(HTTPStatus.SERVICE_UNAVAILABLE,
                                 {"error": f"SQLite read failed: {exc}"})
            else:
                self.respond(HTTPStatus.NOT_FOUND, {"error": "Route not found"})

        def respond(self, status, body, content_type="application/json; charset=utf-8"):
            if not isinstance(body, bytes):
                body = json.dumps(body, ensure_ascii=False, allow_nan=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy",
                             "default-src 'none'; script-src 'unsafe-inline'; "
                             "style-src 'unsafe-inline'; connect-src 'self'; "
                             "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

    return Handler


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("ingest", help="Fetch and validate 60 public observations, then commit")
    serve = commands.add_parser("serve", help="Serve existing SQLite data on 127.0.0.1 only")
    serve.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv)
    if args.command == "serve" and not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    try:
        if args.command == "ingest":
            print(json.dumps(ingest(), ensure_ascii=False, indent=2))
        else:
            with ThreadingHTTPServer(("127.0.0.1", args.port), make_handler()) as server:
                print(f"Market Explorer: http://127.0.0.1:{args.port} (Ctrl+C to stop)",
                      flush=True)
                server.serve_forever()
    except KeyboardInterrupt:
        return 0
    except (DataError, sqlite3.Error, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
