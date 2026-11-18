"""Skema HTTP modul penanganan."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ItemPetugasKeluaran(BaseModel):
    nomor: str
    status: str
    tingkat: str | None
    lat: float
    lon: float
    kota: str | None
    kecamatan: str | None
    jumlah_dukungan: int
    diverifikasi_pada: str | None
    skor_prioritas: float | None = Field(description="BR-05; null bila fitur prioritas belum aktif")


class StatusPetugasKeluaran(BaseModel):
    nomor: str
    status: str
    verifikasi_foto: dict | None = Field(
        default=None, description="US-31: hasil AI atas foto setelah perbaikan (kelas, confidence, alasan)"
    )
