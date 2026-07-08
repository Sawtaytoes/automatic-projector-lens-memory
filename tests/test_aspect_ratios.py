import os

from lens_memory.aspect_ratios import AspectRatioLookup

FIXTURE = os.path.join(os.path.dirname(__file__), "fixtures", "aspectRatioCalculations.sample.json")


def test_lookup_hit():
    lookup = AspectRatioLookup(FIXTURE, "relativeMedianAspectRadio")
    assert lookup.enabled
    assert lookup.lookup("/media/Movies/Interstellar (2014).mkv") == "2.39"


def test_lookup_alternate_calculation_type():
    lookup = AspectRatioLookup(FIXTURE, "exactMaxHeightAspectRatio")
    assert lookup.lookup("/media/Movies/Interstellar (2014).mkv") == "2.40"


def test_lookup_miss_returns_none():
    lookup = AspectRatioLookup(FIXTURE, "relativeMedianAspectRadio")
    assert lookup.lookup("/media/Movies/Unknown.mkv") is None
    assert lookup.lookup(None) is None


def test_missing_calculation_type_returns_none():
    lookup = AspectRatioLookup(FIXTURE, "relativeMedianAspectRadio")
    # The Incredibles has no exact calc; lookup for it under a missing type is None.
    lookup2 = AspectRatioLookup(FIXTURE, "exactMaxHeightAspectRatio")
    assert lookup2.lookup("/media/Movies/The Incredibles (2004).mkv") is None
    assert lookup.lookup("/media/Movies/The Incredibles (2004).mkv") == "1.85"


def test_missing_file_disables_lookup():
    lookup = AspectRatioLookup("/nonexistent/path.json", "relativeMedianAspectRadio")
    assert not lookup.enabled
    assert lookup.lookup("/anything") is None


def test_no_path_disables_lookup():
    lookup = AspectRatioLookup(None, "relativeMedianAspectRadio")
    assert not lookup.enabled
