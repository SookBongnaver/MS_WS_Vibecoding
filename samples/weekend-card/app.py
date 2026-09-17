"""Weekend Card: Seoul public example API -> SQLite -> local web service."""
import argparse
from contextlib import closing
from datetime import date, datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
from pathlib import Path
import sqlite3
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from planner import candidates

ROOT = Path(__file__).resolve().parent
DB = ROOT / "data" / "weekend.sqlite3"
SNAPSHOT = ROOT / "snapshot.json"
SOURCES = {
    "park": ("SearchParkInfoService", "서울시 주요 공원", "OA-394"),
    "culture": ("culturalSpaceInfo", "서울시 문화공간", "OA-15487"),
    "event": ("culturalEventInfo", "서울시 문화행사", "OA-15486"),
}
COVERAGE = "공원·문화공간·행사 각 5건의 공식 예제 API 범위입니다. 서울 전체 목록이 아닙니다."


def text(value, limit=200):
    return value.strip()[:limit] if isinstance(value, str) and value.strip() else None


def safe_url(value):
    value = text(value, 2000)
    if not value:
        return None
    parts = urlsplit(value)
    if parts.scheme not in ("https", "http") or not parts.hostname or parts.username or parts.password:
        return None
    return value


def point(lat, lon):
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return None, None
    if not math.isfinite(lat + lon) or not (36.8 <= lat <= 38.0 and 126 <= lon <= 128.5):
        return None, None
    return lat, lon


def event_date(value):
    value = text(value)
    if not value:
        raise ValueError("행사 시작일·종료일이 없습니다.")
    return date.fromisoformat(value[:10]).isoformat()


def normalize(kind, row):
    if not isinstance(row, dict):
        raise ValueError("API 행이 객체가 아닙니다.")
    if kind == "park":
        title, district, address = row.get("PARK_NM"), row.get("RGN"), row.get("PARK_ADDR")
        lat, lon = point(row.get("YCRD"), row.get("XCRD"))
        identifier = text(str(row.get("SN", "")), 60)
        category, venue = "공원", None
        fee, hours, closed, start, end, free = None, None, None, None, None, None
        url, booking, note = row.get("URL"), None, text(row.get("UTZTN_REF"), 400)
    elif kind == "culture":
        title, district, address = row.get("FAC_NAME"), row.get("GNGU"), row.get("ADDR")
        lat, lon = point(row.get("X_COORD"), row.get("Y_COORD"))
        identifier = text(str(row.get("NUM", "")), 60)
        category, venue = text(row.get("SUBJCODE")) or "문화공간", None
        fee, hours, closed = text(row.get("ENTR_FEE")), text(row.get("OPENHOUR")), text(row.get("CLOSEDAY"))
        start, end = None, None
        free = True if row.get("ENTRFREE") == "무료" and not fee else None
        url, booking, note = row.get("HOMEPAGE"), None, "공간 입장과 개별 프로그램의 요금·이용 조건은 다를 수 있습니다."
    else:
        title, district, address = row.get("TITLE"), row.get("GUNAME"), row.get("PLACE")
        lat, lon = point(row.get("LAT"), row.get("LOT"))
        start, end = event_date(row.get("STRTDATE")), event_date(row.get("END_DATE"))
        if start > end:
            raise ValueError("행사 날짜 순서가 올바르지 않습니다.")
        identifier = hashlib.sha256(f"{title}|{start}|{address}".encode()).hexdigest()[:16]
        category, venue = text(row.get("CODENAME")) or "행사", text(row.get("PLACE"))
        fee, hours, closed = text(row.get("USE_FEE")), text(row.get("PRO_TIME")), None
        free = True if row.get("IS_FREE") == "무료" else False if row.get("IS_FREE") == "유료" else None
        url, booking = row.get("HMPG_ADDR"), row.get("ORG_LINK")
        note = "행사 기간 내에도 회차·휴연·잔여 좌석은 공식 안내에서 확인하세요."
    if not text(title) or not identifier:
        raise ValueError("필수 장소 이름·ID가 없습니다.")
    return {
        "id": f"{kind}:{identifier}", "kind": kind, "title": text(title),
        "district": text(district) or "지역 미제공", "address": text(address),
        "lat": lat, "lon": lon, "source_url": safe_url(url), "booking_url": safe_url(booking),
        "source_name": SOURCES[kind][1], "category": category,
        "fee_text": fee, "free": free, "hours": hours, "closed": closed, "note": note,
        "start_date": start, "end_date": end, "venue": venue,
    }


def fetch_catalog():
    items, sources = [], []
    for kind, (service, name, catalog_id) in SOURCES.items():
        url = f"http://openapi.seoul.go.kr:8088/sample/json/{service}/1/5/"
        try:
            with urlopen(Request(url, headers={"User-Agent": "WeekendCard-Education/1.0"}), timeout=25) as response:
                raw = response.read(2_000_001)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise ValueError(f"{name} 공개 예제 API 조회 실패. 기존 데이터는 유지됩니다.") from exc
        if len(raw) > 2_000_000:
            raise ValueError("응답 크기 제한을 초과했습니다.")
        payload = json.loads(raw.decode("utf-8"))
        body = payload.get(service, {})
        rows, result = body.get("row"), body.get("RESULT", {})
        total = body.get("list_total_count")
        if (result.get("CODE") != "INFO-000" or not isinstance(rows, list)
                or not isinstance(total, int) or total < 0 or len(rows) != min(total, 5)):
            raise ValueError(f"{name}: 정상 예제 응답이 아닙니다.")
        items.extend(normalize(kind, row) for row in rows)
        sources.append({"kind": kind, "name": name, "url": url, "sample_count": len(rows),
                        "total_available": total,
                        "catalog_url": f"https://data.seoul.go.kr/dataList/{catalog_id}/S/1/datasetView.do"})
    if len({item["id"] for item in items}) != len(items):
        raise ValueError("중복 장소 ID가 있습니다.")
    return {"mode": "public-live", "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "coverage": COVERAGE, "sources": sources, "items": items}


def save_catalog(catalog, db=DB):
    validate_catalog(catalog)
    db.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(db)) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute("CREATE TABLE IF NOT EXISTS catalog (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)")
        conn.execute("INSERT INTO catalog VALUES(1,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload",
                     (json.dumps(catalog, ensure_ascii=False, allow_nan=False),))


def validate_catalog(catalog):
    if not isinstance(catalog, dict) or catalog.get("mode") not in ("public-live", "public-snapshot"):
        raise ValueError("잘못된 데이터 모드")
    datetime.fromisoformat(catalog["fetched_at"])
    items = catalog.get("items")
    if not isinstance(items, list) or len(items) > 500:
        raise ValueError("잘못된 장소 목록")
    seen = set()
    for item in items:
        if item["kind"] not in SOURCES or not text(item["title"]) or item["id"] in seen:
            raise ValueError("잘못된 장소 또는 중복 ID")
        seen.add(item["id"])
        for field in ("source_url", "booking_url"):
            if item.get(field) and safe_url(item[field]) != item[field]:
                raise ValueError("잘못된 링크")
        if item["kind"] == "event" and (
                event_date(item["start_date"]) > event_date(item["end_date"])):
            raise ValueError("행사 기간 오류")
    return catalog


def read_catalog(db=DB):
    if not db.exists():
        raise ValueError("먼저 python app.py seed 또는 python app.py refresh를 실행하세요.")
    with closing(sqlite3.connect(db.resolve().as_uri() + "?mode=ro", uri=True)) as conn:
        row = conn.execute("SELECT payload FROM catalog WHERE id=1").fetchone()
    if not row:
        raise ValueError("데이터가 비어 있습니다.")
    return validate_catalog(json.loads(row[0]))


def handler(db=DB):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if urlsplit(self.path).path != "/api/plan":
                self.respond(404, {"error": "Not found"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 4096:
                    raise ValueError("요청은 1~4096 bytes여야 합니다.")
                body = json.loads(self.rfile.read(length).decode("utf-8"))
                if not isinstance(body, dict) or set(body) - {"preferences", "pinned", "offset"}:
                    raise ValueError("요청 형식이 올바르지 않습니다.")
                result = candidates(read_catalog(db), body.get("preferences"),
                                    body.get("pinned"), body.get("offset", 0))
                self.respond(200, result)
            except (ValueError, UnicodeDecodeError, sqlite3.Error, OSError) as exc:
                self.respond(400, {"error": str(exc)})

        def do_GET(self):
            route = urlsplit(self.path).path
            if route == "/":
                self.respond(200, (ROOT / "index.html").read_bytes(), "text/html; charset=utf-8")
            elif route == "/api/catalog":
                try:
                    self.respond(200, read_catalog(db))
                except (ValueError, sqlite3.Error, OSError) as exc:
                    self.respond(503, {"error": str(exc)})
            elif route == "/favicon.ico":
                self.respond(204, b"", "image/x-icon")
            else:
                self.respond(404, {"error": "Not found"})

        def respond(self, status, body, content_type="application/json; charset=utf-8"):
            if not isinstance(body, bytes):
                body = json.dumps(body, ensure_ascii=False, allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy",
                             "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
                             "connect-src 'self'; img-src data:; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
            self.end_headers()
            self.wfile.write(body)
    return Handler


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    seed = sub.add_parser("seed", help="Load the bundled real public snapshot (no network)")
    seed.add_argument("--replace", action="store_true")
    sub.add_parser("refresh", help="Fetch official public sample API (15 rows), then replace catalog")
    sub.add_parser("capture-snapshot", help="Fetch public data into snapshot.json and SQLite")
    sub.add_parser("inspect")
    serve = sub.add_parser("serve")
    serve.add_argument("--port", type=int, default=8768)
    args = parser.parse_args()
    try:
        if args.command == "seed":
            if DB.exists() and not args.replace:
                raise ValueError("DB가 이미 있습니다. 보관 여부를 확인하고 seed --replace를 사용하세요.")
            catalog = validate_catalog(json.loads(SNAPSHOT.read_text(encoding="utf-8")))
            catalog["mode"] = "public-snapshot"
            save_catalog(catalog)
            print(f"공개 데이터 스냅샷 {len(catalog['items'])}건 적재. 실시간 조회 아님.")
        elif args.command in ("refresh", "capture-snapshot"):
            catalog = fetch_catalog()
            if args.command == "capture-snapshot":
                SNAPSHOT.write_text(json.dumps({**catalog, "mode": "public-snapshot"}, ensure_ascii=False, indent=2), encoding="utf-8")
            save_catalog(catalog)
            print(f"공개 API {len(catalog['items'])}건 적재. {COVERAGE}")
        elif args.command == "inspect":
            c = read_catalog()
            print(json.dumps({k: c[k] for k in ("mode", "fetched_at", "coverage", "sources")}, ensure_ascii=False, indent=2))
        else:
            if not 1 <= args.port <= 65535:
                raise ValueError("포트 범위는 1~65535입니다.")
            with ThreadingHTTPServer(("127.0.0.1", args.port), handler()) as server:
                print(f"주말 한 장: http://127.0.0.1:{args.port} (Ctrl+C 종료)", flush=True)
                server.serve_forever()
    except KeyboardInterrupt:
        return 0
    except (ValueError, sqlite3.Error, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
