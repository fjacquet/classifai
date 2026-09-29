"""
Infrastructure for geocoding services.

This module contains impure functions for interacting with geocoding APIs.
Reverse geocoding sends photo GPS coordinates to OpenStreetMap's Nominatim,
so it is disabled unless ``online_geocoding: true`` is set in settings.yaml.
"""

from functools import cache, lru_cache

from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from loguru import logger

from classifai.config import app_config

COORDINATE_PRECISION = 3  # ~100 m: photos taken at the same place share one lookup


def _online_geocoding_enabled() -> bool:
    return app_config.online_geocoding


@cache
def _reverse() -> RateLimiter:
    """Nominatim reverse lookup limited to 1 request/second (Nominatim usage policy)."""
    return RateLimiter(Nominatim(user_agent="classifai").reverse, min_delay_seconds=1)


@lru_cache(maxsize=1024)
def _lookup(latitude: float, longitude: float) -> str | None:
    """Cached reverse lookup on rounded coordinates."""
    try:
        location = _reverse()((latitude, longitude), exactly_one=True)
    except Exception as e:
        logger.warning(f"Geocoding failed for ({latitude}, {longitude}): {e}")
        return None
    if not location or not location.address:
        return None
    address = location.raw.get("address", {})
    city = address.get("city", address.get("town", address.get("village", "")))
    country = address.get("country", "")
    if city and country:
        return f"{city}, {country}"
    return country or None


def get_location_from_gps(latitude: float, longitude: float) -> str | None:
    """
    Converts GPS coordinates to a location string (City, Country).

    Args:
        latitude: GPS latitude coordinate
        longitude: GPS longitude coordinate

    Returns:
        Location string (e.g., "Paris, France"), or None if online geocoding
        is disabled or the lookup fails
    """
    if not _online_geocoding_enabled():
        return None
    return _lookup(round(latitude, COORDINATE_PRECISION), round(longitude, COORDINATE_PRECISION))
