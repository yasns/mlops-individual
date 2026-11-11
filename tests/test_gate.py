from gate import check

GATE = {"recall": 0.30, "precision": 0.60}


def test_gate_passes_good_model():
    assert check({"recall": 0.39, "precision": 0.63}, GATE) == []


def test_gate_blocks_bad_model():
    assert check({"recall": 0.0, "precision": 0.0}, GATE) == ["recall=0.0000 < 0.3", "precision=0.0000 < 0.6"]
