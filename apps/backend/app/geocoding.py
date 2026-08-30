from __future__ import annotations

import pandas as pd
import pgeocode


# Nominatim instances cache their country data file; reuse them across requests.
_noms: dict[str, pgeocode.Nominatim] = {}


def _nominatim(country_code: str) -> pgeocode.Nominatim:
    cc = country_code.strip().lower()
    if cc not in _noms:
        _noms[cc] = pgeocode.Nominatim(cc)
    return _noms[cc]


def geocode_postal(country_code: str, postal_code: str) -> dict | None:
    """Resolve a postal code to coordinates using local pgeocode/GeoNames data.

    Returns None when the postal code is unknown. Raises ValueError for an
    unsupported country code.
    """
    record = _nominatim(country_code).query_postal_code(postal_code.strip())
    lat = record.get("latitude")
    lon = record.get("longitude")
    if lat is None or lon is None or pd.isna(lat) or pd.isna(lon):
        return None

    place = record.get("place_name")
    if place is not None and pd.isna(place):
        place = None

    return {
        "country_code": country_code.strip().upper(),
        "postal_code": postal_code.strip(),
        "city": place,
        "latitude": float(lat),
        "longitude": float(lon),
    }
