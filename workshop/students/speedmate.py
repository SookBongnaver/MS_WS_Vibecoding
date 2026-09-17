def calculate(records, *, vehicle_id, service_id, start_date, end_date):
    """Match model, service, date range [start,end), capacity and duration.

    Return <=3 existing candidate slots and conditional warranty checks.
    DEMO-003 + SS1 in [2026-09-21,2026-09-28) -> ST1 only.
    Do not diagnose, assess driving safety, book or approve warranties.
    """
    raise NotImplementedError("Implement calculate in workshop/students/speedmate.py with Codex, then run tests.")
