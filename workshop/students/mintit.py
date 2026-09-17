def calculate(records, *, quote_id, promotion_ids, option_id, date, region):
    """Implement base + eligible bonuses - collection fee using record IDs.

    Check model, grade, inclusive promotion dates, service region and stacking.
    MQ1 + MP1 + MP2 - MO1 fee on 2026-09-26 in Seoul -> 205000 KRW.
    Run: python -m unittest tests.test_student_contract -v
    """
    raise NotImplementedError("Implement calculate in workshop/students/mintit.py with Codex; never silently substitute the solution.")
