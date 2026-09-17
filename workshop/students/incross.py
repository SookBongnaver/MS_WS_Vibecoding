def calculate(records, *, campaign_id, start_date, end_date):
    """Aggregate daily totals by channel in inclusive-start/exclusive-end range.

    Calculate CTR, CPC, CPA, ROAS from totals, not mean daily ratios.
    A zero denominator -> value None and explicit reason.
    DEMO-C01 August search: cost 400000, clicks 500, CPA 16000.
    Baseline metrics only; budget redistribution is outside this exercise.
    """
    raise NotImplementedError("Implement calculate in workshop/students/incross.py with Codex, then run tests.")
