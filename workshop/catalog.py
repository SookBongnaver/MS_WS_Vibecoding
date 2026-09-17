from .config import SCENARIOS

CATEGORIES = {
    "walkerhill": ("program", "slot"),
    "mintit": ("quote", "promotion", "option"),
    "speedmate": ("vehicle", "service", "warranty", "slot"),
    "incross": ("campaign", "daily"),
    "intellix": ("candidate", "criterion", "evidence"),
}

CALCULATOR_NAMES = {
    "walkerhill": "calculate_itinerary_cost",
    "mintit": "calculate_estimate",
    "speedmate": "match_available_slots",
    "incross": "calculate_media_metrics",
    "intellix": "compare_partners",
}

FIELDS = {
    "walkerhill": "program: name, price_per_person (KRW), duration_minutes, indoor; slot: program_id, date, start (HH:MM), capacity, transfer_minutes (required gap after previous activity)",
    "mintit": "quote: model, capacity_gb, grade, price (KRW); promotion: model, grades, start/end (inclusive ISO dates), amount, stackable; option: method, regions, fee",
    "speedmate": "vehicle: model, mileage_km, history[]; service: models[], duration_minutes; warranty: models[], start/end (inclusive), max_mileage_km, conditions[]; slot: service_id, date, start/end (HH:MM), capacity",
    "incross": "campaign: name, goal; daily: campaign_id, date, channel, cost, impressions, clicks, conversions, revenue. Metrics use inclusive start, exclusive end. Baseline metrics ONLY: no budget redistribution.",
    "intellix": "candidate: name, country; criterion: name, weight (sum=1), required, minimum (0..100); evidence: candidate_id, criterion_id, score (0..100 or null), verified, updated, note. Unknown/unverified is NOT zero; no ranking.",
}


def object_schema(properties, required=None):
    return {"type": "object", "properties": properties,
            "required": list(properties) if required is None else required,
            "additionalProperties": False}


def ids():
    return {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 10, "uniqueItems": True}


STRING = {"type": "string"}
DATE = {"type": "string", "description": "Explicit ISO date YYYY-MM-DD; ask user, never assume current year"}
CALC_ARGS = {
    "walkerhill": object_schema({"slot_ids": ids(), "date": DATE, "people": {"type": "integer", "minimum": 1, "maximum": 100},
                                 "budget": {"type": "integer", "minimum": 0}, "start": STRING, "end": STRING}),
    "mintit": object_schema({"quote_id": STRING, "promotion_ids": {"type": "array", "items": STRING, "maxItems": 10, "uniqueItems": True},
                             "option_id": STRING, "date": DATE, "region": STRING}),
    "speedmate": object_schema({"vehicle_id": STRING, "service_id": STRING, "start_date": DATE, "end_date": DATE}),
    "incross": object_schema({"campaign_id": STRING, "start_date": DATE, "end_date": DATE}),
    "intellix": object_schema({"candidate_ids": ids()}),
}

EXAMPLES = {
    "walkerhill": {"slot_ids": ["WS1", "WS2"], "date": "2026-09-26", "people": 2, "budget": 200000, "start": "14:00", "end": "18:00"},
    "mintit": {"quote_id": "MQ1", "promotion_ids": ["MP1", "MP2"], "option_id": "MO1", "date": "2026-09-26", "region": "Seoul"},
    "speedmate": {"vehicle_id": "DEMO-003", "service_id": "SS1", "start_date": "2026-09-21", "end_date": "2026-09-28"},
    "incross": {"campaign_id": "DEMO-C01", "start_date": "2026-08-01", "end_date": "2026-09-01"},
    "intellix": {"candidate_ids": ["IX1", "IX2"]},
}


def tool_definitions(scenario):
    if scenario not in SCENARIOS:
        raise ValueError("Unknown scenario")
    category = {"type": "string", "enum": list(CATEGORIES[scenario])}
    entries = [
        ("list_records", f"Read up to 30 synthetic {scenario} records in one allowed category. IDs are in record_id. {FIELDS[scenario]}",
         object_schema({"category": category})),
        ("get_record", "Read one synthetic record by exact category and record_id; returns null if missing.",
         object_schema({"category": category, "record_id": STRING})),
        (CALCULATOR_NAMES[scenario],
         "Deterministic business calculation using IDs in the scenario database, not model-provided prices or scores. "
         f"Example arguments: {EXAMPLES[scenario]}. {FIELDS[scenario]}",
         CALC_ARGS[scenario]),
    ]
    return [{"type": "function", "function": {"name": name, "description": desc, "parameters": schema}}
            for name, desc, schema in entries]
