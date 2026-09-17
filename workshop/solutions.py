"""Instructor reference implementations. Starter mode never imports this module."""
import math
from datetime import date as Date


def iso_date(value):
    if not isinstance(value, str):
        raise ValueError("Use an explicit ISO date YYYY-MM-DD")
    parsed = Date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("Use an explicit ISO date YYYY-MM-DD")
    return parsed


def minute(value):
    if not isinstance(value, str) or len(value) != 5 or value[2] != ":":
        raise ValueError("Time must be HH:MM")
    h, m = int(value[:2]), int(value[3:])
    if not 0 <= h < 24 or not 0 <= m < 60:
        raise ValueError("Invalid clock time")
    return h * 60 + m


def number(value, label, *, integer=False, minimum=0):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label} missing/invalid; staff confirmation required")
    if value < minimum or (integer and not isinstance(value, int)):
        raise ValueError(f"{label} must be {'an integer' if integer else 'a number'} >= {minimum}")
    return value


def unique_ids(values, *, allow_empty=False):
    if not isinstance(values, list) or not (0 if allow_empty else 1) <= len(values) <= 10:
        raise ValueError("Provide 1-10 unique IDs (promotions may be empty)")
    if any(not isinstance(v, str) for v in values) or len(set(values)) != len(values):
        raise ValueError("Duplicate or invalid IDs")
    return values


def index(records, category):
    rows = records[category]
    result = {r["record_id"]: r["payload"] for r in rows}
    if len(result) != len(rows):
        raise ValueError("Duplicate source IDs")
    return result


def required(mapping, key):
    if key not in mapping:
        raise ValueError(f"Unknown ID: {key}; query existing IDs first")
    return mapping[key]


def walkerhill(records, *, slot_ids, date, people, budget, start, end):
    unique_ids(slot_ids)
    visit = iso_date(date)
    number(people, "people", integer=True, minimum=1)
    if people > 100:
        raise ValueError("Workshop limit is 100 people")
    number(budget, "budget", integer=True)
    begin, finish = minute(start), minute(end)
    if begin >= finish:
        raise ValueError("Visit end must be after start (same day)")
    programs, slots = index(records, "program"), index(records, "slot")
    selected = [(sid, required(slots, sid)) for sid in slot_ids]
    selected.sort(key=lambda item: minute(item[1]["start"]))
    total, previous_end, issues, itinerary = 0, None, [], []
    for sid, slot in selected:
        program = required(programs, slot["program_id"])
        price = number(program.get("price_per_person"), "price_per_person", integer=True)
        duration = number(program.get("duration_minutes"), "duration_minutes", integer=True, minimum=1)
        capacity = number(slot.get("capacity"), "capacity", integer=True)
        transfer = number(slot.get("transfer_minutes"), "transfer_minutes", integer=True)
        st = minute(slot["start"])
        en = st + duration
        if iso_date(slot["date"]) != visit:
            issues.append(f"{sid}: wrong date")
        if st < begin or en > finish:
            issues.append(f"{sid}: outside visit window")
        if previous_end is not None and st < previous_end + transfer:
            issues.append(f"{sid}: overlap or insufficient transfer time")
        if people > capacity:
            issues.append(f"{sid}: insufficient capacity")
        subtotal = price * people
        total += subtotal
        previous_end = en
        itinerary.append({"slot_id": sid, "program_id": slot["program_id"], "start": slot["start"],
                          "duration_minutes": duration, "subtotal": subtotal})
    if total > budget:
        issues.append("Total exceeds budget")
    return {"synthetic": True, "total": total, "currency": "KRW", "within_budget": total <= budget,
            "feasible": not issues, "issues": issues, "itinerary": itinerary, "reservation": False}


def mintit(records, *, quote_id, promotion_ids, option_id, date, region):
    unique_ids(promotion_ids, allow_empty=True)
    sale = iso_date(date)
    quote = required(index(records, "quote"), quote_id)
    option = required(index(records, "option"), option_id)
    if region not in option["regions"]:
        raise ValueError("Collection option is not available in the selected synthetic region")
    base = number(quote.get("price"), "quote price", integer=True)
    fee = number(option.get("fee"), "collection fee", integer=True)
    promotions = index(records, "promotion")
    bonus = 0
    for pid in promotion_ids:
        promo = required(promotions, pid)
        if not isinstance(promo.get("stackable"), bool):
            raise ValueError(f"{pid}: unknown stacking policy")
        if len(promotion_ids) > 1 and not promo["stackable"]:
            raise ValueError(f"{pid}: non-stackable promotion cannot be combined")
        first, last = iso_date(promo["start"]), iso_date(promo["end"])
        if first > last:
            raise ValueError(f"{pid}: invalid promotion period")
        if not first <= sale <= last:
            raise ValueError(f"{pid}: promotion outside inclusive eligibility dates")
        if promo["model"] != quote["model"] or quote["grade"] not in promo["grades"]:
            raise ValueError(f"{pid}: model or assumed grade is ineligible")
        bonus += number(promo.get("amount"), "promotion amount", integer=True)
    if base + bonus < fee:
        raise ValueError("Collection fee exceeds estimate; staff confirmation required")
    return {"synthetic": True, "quote_id": quote_id, "promotion_ids": promotion_ids, "option_id": option_id,
            "assumed_grade": quote["grade"], "base": base, "bonus": bonus, "fee": fee,
            "estimated_total": base + bonus - fee, "currency": "KRW",
            "notice": "Estimate only; actual inspection and policy confirmation required. No valuation or payment."}


def speedmate(records, *, vehicle_id, service_id, start_date, end_date):
    first, last = iso_date(start_date), iso_date(end_date)
    if first >= last:
        raise ValueError("Date range must be nonempty: inclusive start, exclusive end")
    vehicle = required(index(records, "vehicle"), vehicle_id)
    service = required(index(records, "service"), service_id)
    duration = number(service.get("duration_minutes"), "service duration", integer=True, minimum=1)
    if vehicle["model"] not in service["models"]:
        raise ValueError("Service is incompatible with this synthetic vehicle model")
    candidates = []
    for sid, slot in index(records, "slot").items():
        day = iso_date(slot["date"])
        if slot["service_id"] != service_id or not first <= day < last:
            continue
        available = minute(slot["end"]) - minute(slot["start"])
        capacity = number(slot.get("capacity"), "slot capacity", integer=True)
        if available >= duration and capacity >= 1:
            candidates.append({"slot_id": sid, "date": slot["date"], "start": slot["start"], "duration_minutes": duration})
    candidates.sort(key=lambda x: (x["date"], x["start"], x["slot_id"]))
    warranty = []
    for wid, rule in index(records, "warranty").items():
        if vehicle["model"] not in rule["models"]:
            continue
        mileage = vehicle.get("mileage_km")
        mileage_ok = None if mileage is None else number(mileage, "mileage", integer=True) <= number(rule["max_mileage_km"], "maximum mileage", integer=True)
        for slot in candidates[:3]:
            day = iso_date(slot["date"])
            warranty.append({"warranty_id": wid, "slot_id": slot["slot_id"],
                             "date_condition_met": iso_date(rule["start"]) <= day <= iso_date(rule["end"]),
                             "mileage_condition_met": mileage_ok, "conditions": rule["conditions"],
                             "final_coverage": "Staff confirmation required"})
    return {"synthetic": True, "vehicle_id": vehicle_id, "service_id": service_id,
            "history": vehicle.get("history", []), "candidates": candidates[:3], "warranty_checks": warranty,
            "missing": ([] if vehicle.get("history") else ["No recorded history"]) + ([] if warranty else ["No applicable warranty evidence for candidates"]),
            "notice": "Candidate times only. No booking, diagnosis, driving-safety advice or warranty approval."}


def media_ratios(totals):
    result = {}
    for metric, numerator, denominator in (
        ("CTR", "clicks", "impressions"), ("CPC", "cost", "clicks"),
        ("CPA", "cost", "conversions"), ("ROAS", "revenue", "cost"),
    ):
        d = totals[denominator]
        result[metric] = {"value": totals[numerator] / d if d else None,
                          "reason": None if d else f"{denominator} is zero"}
    return result


def incross(records, *, campaign_id, start_date, end_date):
    first, last = iso_date(start_date), iso_date(end_date)
    if first >= last:
        raise ValueError("Date range must be nonempty: inclusive start, exclusive end")
    required(index(records, "campaign"), campaign_id)
    fields = ("cost", "impressions", "clicks", "conversions", "revenue")
    channels, seen = {}, set()
    for rid, row in index(records, "daily").items():
        if row["campaign_id"] != campaign_id or not first <= iso_date(row["date"]) < last:
            continue
        key = (row["campaign_id"], row["date"], row["channel"])
        if key in seen:
            raise ValueError("Duplicate daily campaign/channel row; refusing double-counting")
        seen.add(key)
        channel = channels.setdefault(row["channel"], {"record_ids": [], "totals": dict.fromkeys(fields, 0)})
        channel["record_ids"].append(rid)
        for field in fields:
            channel["totals"][field] += number(row.get(field), field, integer=True)
    overall = dict.fromkeys(fields, 0)
    for channel in channels.values():
        channel["metrics"] = media_ratios(channel["totals"])
        for field in fields:
            overall[field] += channel["totals"][field]
    return {"synthetic": True, "campaign_id": campaign_id, "start_inclusive": start_date, "end_exclusive": end_date,
            "channels": channels, "totals": overall, "metrics": media_ratios(overall),
            "missing": [] if channels else ["No performance rows in requested range"],
            "notice": "Ratios of totals, CTR is a fraction. Historical baseline only; no budget redistribution or execution."}


def intellix(records, *, candidate_ids):
    unique_ids(candidate_ids)
    criteria, candidates = index(records, "criterion"), index(records, "candidate")
    if not criteria:
        raise ValueError("No evaluation criteria")
    for cid, criterion in criteria.items():
        number(criterion.get("weight"), f"{cid} weight")
        number(criterion.get("minimum"), f"{cid} minimum")
        if criterion["minimum"] > 100 or not isinstance(criterion.get("required"), bool):
            raise ValueError("Invalid criterion minimum/required flag")
    if not math.isclose(sum(c["weight"] for c in criteria.values()), 1.0, abs_tol=1e-9):
        raise ValueError("Criterion weights must sum to 1")
    evidence = {}
    for eid, ev in index(records, "evidence").items():
        key = (ev["candidate_id"], ev["criterion_id"])
        if key in evidence:
            raise ValueError("Multiple evidence rows for one criterion; resolve ambiguity first")
        evidence[key] = (eid, ev)
    assessments = []
    for pid in candidate_ids:
        candidate = required(candidates, pid)
        missing, unmet, checked, required_unknown = [], [], [], []
        weighted, coverage = 0.0, 0.0
        for cid, criterion in criteria.items():
            item = evidence.get((pid, cid))
            if not item or item[1].get("verified") is not True or item[1].get("score") is None:
                missing.append(cid)
                if criterion["required"]:
                    required_unknown.append(cid)
                continue
            eid, ev = item
            score = number(ev["score"], f"{eid} score")
            if score > 100:
                raise ValueError("Evidence score exceeds 100")
            iso_date(ev["updated"])
            weighted += score * criterion["weight"]
            coverage += criterion["weight"]
            if criterion["required"] and score < criterion["minimum"]:
                unmet.append(cid)
            checked.append({"criterion_id": cid, "evidence_id": eid, "score": score, "updated": ev["updated"]})
        assessments.append({"candidate_id": pid, "name": candidate["name"], "country": candidate["country"],
                            "weighted_score": round(weighted, 6) if not missing else None,
                            "known_weighted_points": round(weighted, 6), "assessed_weight": round(coverage, 6),
                            "missing": missing, "unmet_required": unmet,
                            "required_status": "not_met" if unmet else ("unknown" if required_unknown else "met"),
                            "evidence": checked})
    return {"synthetic": True, "assessments": assessments, "ranking": None,
            "notice": "Unknown is not zero. Partial points are not comparable totals. No ranking, contact or contract."}
