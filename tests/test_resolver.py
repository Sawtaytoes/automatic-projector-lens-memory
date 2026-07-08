from lens_memory.events import PlaybackEvent
from lens_memory.mode_mapping import DEFAULT_MAPPING, ModeMapper
from lens_memory.resolver import Resolver


class FakePlex:
    enabled = True

    def __init__(self, path=None):
        self._path = path

    def get_media_file_path(self, rating_key):
        return self._path


class FakeAspectRatios:
    def __init__(self, mapping=None):
        self._mapping = mapping or {}

    def lookup(self, path):
        return self._mapping.get(path)


class FakeBluray:
    def __init__(self, result=None):
        self._result = result

    def get_aspect_ratio(self, title, year=None):
        return self._result


def make_resolver(plex, aspect_ratios, bluray):
    return Resolver(
        plex=plex,
        aspect_ratios=aspect_ratios,
        bluray_com=bluray,
        mode_mapper=ModeMapper(DEFAULT_MAPPING),
        idle_mode="mode_1",
    )


def test_idle_returns_reset_mode():
    resolver = make_resolver(FakePlex(), FakeAspectRatios(), FakeBluray())
    result = resolver.resolve(PlaybackEvent(state="idle"))
    assert result.mode == "mode_1"
    assert result.aspect_ratio is None
    assert result.source == "idle"


def test_json_path_resolves():
    resolver = make_resolver(
        FakePlex("/media/x.mkv"),
        FakeAspectRatios({"/media/x.mkv": "2.39"}),
        FakeBluray(),
    )
    result = resolver.resolve(PlaybackEvent(state="playing", rating_key="1", title="X"))
    assert result.aspect_ratio == "2.39"
    assert result.mode == "mode_2"
    assert result.source == "aspect-ratios-json"


def test_bluray_fallback_when_json_misses():
    resolver = make_resolver(
        FakePlex("/media/x.mkv"),
        FakeAspectRatios({}),  # miss
        FakeBluray("1.85"),
    )
    result = resolver.resolve(PlaybackEvent(state="playing", rating_key="1", title="X", year=2004))
    assert result.aspect_ratio == "1.85"
    assert result.mode == "mode_3"
    assert result.source == "bluray-com"


def test_unknown_when_all_miss():
    resolver = make_resolver(FakePlex(None), FakeAspectRatios({}), FakeBluray(None))
    result = resolver.resolve(PlaybackEvent(state="playing", rating_key="1", title="X"))
    assert result.aspect_ratio is None
    assert result.mode is None
