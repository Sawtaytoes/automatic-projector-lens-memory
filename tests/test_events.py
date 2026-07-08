from lens_memory.events import PlaybackEvent


def test_playing_event():
    event = PlaybackEvent.from_dict(
        {"state": "playing", "player": "media_player.shield", "rating_key": "12345"}
    )
    assert event.is_playing
    assert event.rating_key == "12345"
    assert event.player == "media_player.shield"


def test_rating_key_from_library_path():
    event = PlaybackEvent.from_dict({"state": "playing", "rating_key": "/library/metadata/98765"})
    assert event.rating_key == "98765"


def test_null_and_unknown_attributes_tolerated():
    event = PlaybackEvent.from_dict(
        {
            "state": "playing",
            "rating_key": None,
            "title": "unknown",
            "year": "unavailable",
        }
    )
    assert event.rating_key is None
    assert event.title is None
    assert event.year is None


def test_year_extraction():
    event = PlaybackEvent.from_dict({"state": "playing", "title": "Dune", "year": "2021"})
    assert event.year == 2021


def test_idle_default_and_normalization():
    assert not PlaybackEvent.from_dict({"state": "idle"}).is_playing
    assert not PlaybackEvent.from_dict({"state": "unavailable"}).is_playing
    assert not PlaybackEvent.from_dict({}).is_playing
