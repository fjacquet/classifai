"""Tests for reverse geocoding privacy and caching."""

from classifai.infrastructure import geocoding


def test_geocoding_is_off_by_default(mocker):
    """No coordinates leave the machine unless online_geocoding is enabled."""
    reverse = mocker.patch.object(geocoding, "_reverse")
    mocker.patch.object(geocoding, "_online_geocoding_enabled", return_value=False)

    assert geocoding.get_location_from_gps(46.52, 6.63) is None
    reverse.assert_not_called()


def test_geocoding_results_are_cached(mocker):
    """Photos from the same place trigger a single lookup."""
    geocoding._lookup.cache_clear()
    mocker.patch.object(geocoding, "_online_geocoding_enabled", return_value=True)
    location = mocker.MagicMock(address="x", raw={"address": {"city": "Lausanne", "country": "Suisse"}})
    reverse = mocker.MagicMock(return_value=location)
    mocker.patch.object(geocoding, "_reverse", return_value=reverse)

    assert geocoding.get_location_from_gps(46.5197, 6.6323) == "Lausanne, Suisse"
    assert geocoding.get_location_from_gps(46.5199, 6.6321) == "Lausanne, Suisse"
    assert reverse.call_count == 1
    geocoding._lookup.cache_clear()
