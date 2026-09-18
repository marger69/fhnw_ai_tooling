from demo_ai.pipeline import normalize


def test_normalize_sums_to_one():
    assert abs(sum(normalize([1, 2, 3])) - 1.0) < 1e-12
