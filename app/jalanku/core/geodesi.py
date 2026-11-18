"""Perhitungan jarak di permukaan bumi."""

from __future__ import annotations

import math

JARI_JARI_BUMI_M = 6_371_008.8


def jarak_meter(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Jarak haversine dalam meter."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * JARI_JARI_BUMI_M * math.asin(math.sqrt(a))
