"""
Infrastructure for geocoding services.

This module contains impure functions for interacting with geocoding APIs.
"""

from geopy.geocoders import Nominatim
from returns.result import safe


@safe
def get_location_from_gps(latitude: float, longitude: float) -> str | None:
    """
    Converts GPS coordinates to a location string (City, Country).
    Returns a Result container.
    """
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
