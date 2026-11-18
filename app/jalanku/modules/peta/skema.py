"""Skema HTTP modul peta."""

from __future__ import annotations

from pydantic import BaseModel


class TitikPetaKeluaran(BaseModel):
    nomor: str
    lat: float
    lon: float
    status: str
    tingkat: str | None
    kota: str | None
    kecamatan: str | None
    jumlah_dukungan: int
    simulasi: bool
