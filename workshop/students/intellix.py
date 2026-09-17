def calculate(records, *, candidate_ids):
    """Validate weights sum to 1 and use only verified evidence scores.

    IX1 -> 86 points; IX2 -> total unknown, missing IC2, assessed weight 0.4.
    Separate mandatory conditions from scores. Return IDs and missing evidence;
    unknown is not zero and incomplete candidates must not be blindly ranked.
    """
    raise NotImplementedError("Implement calculate in workshop/students/intellix.py with Codex, then run tests.")
