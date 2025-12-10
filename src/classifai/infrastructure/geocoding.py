"""
Infrastructure for geocoding services.

This module contains impure functions for interacting with geocoding APIs.
"""

from geopy.geocoders import Nominatim
from loguru import logger


def get_location_from_gps(latitude: float, longitude: float) -> str | None:
    """
    Converts GPS coordinates to a location string (City, Country).

    Args:
        latitude: GPS latitude coordinate
        longitude: GPS longitude coordinate

    Returns:
        Location string (e.g., "Paris, France") or None if lookup fails
    """
    try:
        geolocator = Nominatim(user_agent="classifai")
        location = geolocator.reverse((latitude, longitude), exactly_one=True)
        if location and location.address:
            address = location.raw.get("address", {})
            city = address.get("city", address.get("town", address.get("village", "")))
            country = address.get("country", "")
            if city and country:
                return f"{city}, {country}"
            if country:
                return country
        return None
    except Exception as e:
        logger.warning(f"Geocoding failed for ({latitude}, {longitude}): {e}")
        return None
