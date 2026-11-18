"""Sumber waktu tunggal. Semua modul memakai ``sekarang()`` supaya waktu bisa dipalsukan di test."""

from __future__ import annotations

from datetime import UTC, datetime

_jam_palsu: str | None = None


def sekarang() -> str:
    """Waktu UTC ISO-8601 detik, mis. ``2026-11-19T08:00:00+00:00``."""
    if _jam_palsu is not None:
        return _jam_palsu
    return datetime.now(UTC).isoformat(timespec="seconds")


def atur_waktu(iso: str | None) -> None:
    """Test: bekukan waktu ke nilai ISO tertentu (``None`` = kembali normal)."""
    global _jam_palsu
    _jam_palsu = iso


def ke_datetime(iso: str) -> datetime:
    return datetime.fromisoformat(iso)
