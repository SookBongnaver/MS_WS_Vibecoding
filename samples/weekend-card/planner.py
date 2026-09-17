"""Deterministic outing candidates: no AI, booking, weather or route-time claims."""
from datetime import date
from math import asin, cos, radians, sin, sqrt

MOODS = ("mixed", "walk", "culture")


def preferences(value):
    if not isinstance(value, dict):
        raise ValueError("조건은 객체여야 합니다.")
    allowed = {"date", "mood", "duration", "district", "culture_only", "exclude_events", "companion"}
    if set(value) - allowed:
        raise ValueError("알 수 없는 조건이 있습니다.")
    day = value.get("date")
    if not isinstance(day, str) or date.fromisoformat(day).isoformat() != day:
        raise ValueError("날짜는 YYYY-MM-DD입니다.")
    result = {"date": day, "mood": value.get("mood", "mixed"),
              "duration": value.get("duration", "half"), "district": value.get("district", ""),
              "culture_only": value.get("culture_only", False),
              "exclude_events": value.get("exclude_events", False),
              "companion": value.get("companion", "friends")}
    if (result["mood"] not in MOODS or result["duration"] not in ("short", "half")
            or result["companion"] not in ("solo", "two", "friends")
            or not isinstance(result["district"], str) or len(result["district"]) > 20
            or type(result["culture_only"]) is not bool or type(result["exclude_events"]) is not bool):
        raise ValueError("조건 값이 올바르지 않습니다.")
    return result


def distance(a, b):
    if any(p.get(k) is None for p in (a, b) for k in ("lat", "lon")):
        return None
    lat1, lat2 = radians(a["lat"]), radians(b["lat"])
    dlat, dlon = lat2 - lat1, radians(b["lon"] - a["lon"])
    return 6371 * 2 * asin(min(1, sqrt(sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2)))


def eligible(catalog, pref):
    selected = []
    for item in catalog["items"]:
        if pref["district"] and item["district"] != pref["district"]:
            continue
        if pref["culture_only"] and item["kind"] != "culture":
            continue
        if item["kind"] == "event":
            if pref["exclude_events"] or not item["start_date"] <= pref["date"] <= item["end_date"]:
                continue
        selected.append(item)
    return selected


def candidates(catalog, pref, pinned=None, offset=0):
    pref = preferences(pref)
    if type(offset) is not int or not 0 <= offset <= 10000:
        raise ValueError("다시 추천 횟수가 올바르지 않습니다.")
    if pinned is not None and (not isinstance(pinned, str) or len(pinned) > 80):
        raise ValueError("잘못된 고정 장소입니다.")
    pool = eligible(catalog, pref)
    anchor = next((p for p in pool if p["id"] == pinned), None)
    if pinned and not anchor:
        return {"courses": [], "reason": "고정한 장소가 새 조건과 맞지 않습니다. 고정을 해제하거나 조건을 바꿔주세요.",
                "eligible_count": len(pool), "preferences": pref}
    if not pool:
        return {"courses": [], "reason": "현재 수집된 예제 데이터에 조건을 만족하는 장소가 없습니다. 다른 날짜·지역을 선택하세요.",
                "eligible_count": 0, "preferences": pref}
    styles = {
        "walk": ("초록으로 쉬는 날", "공원을 중심으로 잠깐 일상 밖으로", ("park", "culture", "event")),
        "culture": ("취향을 채우는 날", "문화공간을 중심으로 새로운 자극", ("culture", "event", "park")),
        "mixed": ("조금씩 다 좋은 날", "다른 종류의 장소를 가볍게 연결", ("event", "culture", "park")),
    }
    order = [pref["mood"]] + [key for key in MOODS if key != pref["mood"]]
    courses, seen = [], set()
    for style_index, style in enumerate(order):
        title, subtitle, priority = styles[style]
        ranked = sorted(pool, key=lambda x: (priority.index(x["kind"]), x["id"]))
        if anchor:
            starts = [anchor]
        else:
            shift = (offset + (style_index if style == "mixed" else 0)) % len(ranked)
            starts = ranked[shift:] + ranked[:shift]
        for first in starts:
            stops = [first]
            others = [p for p in pool if p["id"] != first["id"] and distance(first, p) is not None
                      and distance(first, p) <= (4 if pref["duration"] == "short" else 8)]
            others.sort(key=lambda p: (
                (0 if p["kind"] != first["kind"] else 1) if style == "mixed" else priority.index(p["kind"]),
                distance(first, p), p["id"]))
            # Rotate alternatives, not the fixed first stop.
            if others:
                shift = offset % len(others)
                others = others[shift:] + others[:shift]
            max_stops = 2 if pref["duration"] == "short" else 3
            for other in others:
                if len(stops) >= max_stops:
                    break
                if distance(stops[-1], other) <= (4 if pref["duration"] == "short" else 8):
                    stops.append(other)
            key = tuple(p["id"] for p in stops)
            if key in seen:
                continue
            seen.add(key)
            total = sum(distance(a, b) for a, b in zip(stops, stops[1:]))
            courses.append({"id": style, "title": title, "subtitle": subtitle,
                            "stops": stops, "distance_km": round(total, 1),
                            "reason": f"{len(stops)}곳의 방문 순서 제안. 이동 거리는 좌표 간 직선거리입니다.",
                            "single_stop": len(stops) == 1})
            break
    return {"courses": courses, "reason": None, "preferences": pref, "eligible_count": len(pool),
            "notice": "운영·휴무·회차·요금·실내 이용 가능 여부는 공식 안내 확인이 필요합니다. 혼잡·날씨·길찾기·예약 재고는 조회하지 않습니다."}
