from lens_memory.mode_mapping import DEFAULT_MAPPING, ModeMapper


def make_mapper(tolerance=0.05):
    return ModeMapper(DEFAULT_MAPPING, tolerance=tolerance)


def test_exact_matches():
    mapper = make_mapper()
    assert mapper.resolve("2.39") == "mode_2"
    assert mapper.resolve("2.10") == "mode_4"
    assert mapper.resolve("1.85") == "mode_3"
    assert mapper.resolve("1.78") == "mode_1"
    assert mapper.resolve("1.37") == "mode_1"
    assert mapper.resolve("1.33") == "mode_1"


def test_nearest_within_tolerance():
    mapper = make_mapper()
    # Scanned 2.40 should fall into the 2.39 bucket.
    assert mapper.resolve("2.40") == "mode_2"
    # 1.90 is within 0.05 of 1.85.
    assert mapper.resolve("1.90") == "mode_3"


def test_outside_tolerance_returns_none():
    mapper = make_mapper()
    # 2.00 is >0.05 from both 1.85 and 2.10.
    assert mapper.resolve("2.00") is None


def test_non_numeric_and_none():
    mapper = make_mapper()
    assert mapper.resolve(None) is None
    assert mapper.resolve("unknown") is None
    assert mapper.resolve("NONE") is None


def test_custom_mapping():
    mapper = ModeMapper({"2.35": "cinemascope"}, tolerance=0.05)
    assert mapper.resolve("2.39") == "cinemascope"
