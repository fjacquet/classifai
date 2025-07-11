"""
Geocoding module for ClassifAI.

This module handles converting GPS coordinates to human-readable locations.
"""

from geopy.geocoders import Nominatim
from loguru import logger


def get_location_from_gps(latitude: float, longitude: float) -> str | None:
    """
    Converts GPS coordinates to a location string (City, Country).

    Args:
        latitude (float): The latitude.
        longitude (float): The longitude.

    Returns:
        str | None: The location string or None if lookup fails.
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
            elif country:
                return country
        return None
    except Exception as e:
        logger.error(f"Error during reverse geocoding: {e}")
        return None
