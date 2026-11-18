"""Skema HTTP modul ai."""

from __future__ import annotations

from pydantic import BaseModel


class HasilFotoKeluaran(BaseModel):
    kelas: str | None
    confidence: float | None
    kemiripan: float | None
    keputusan: str  # terima | tolak | admin
    alasan: str
    probabilitas: dict[str, float]


class InfoModelKeluaran(BaseModel):
    aktif: bool
    versi: str | None
    threshold_confidence: float
    threshold_kemiripan: float


class MetrikAIKeluaran(BaseModel):
    periode_hari: int
    jumlah_laporan: int
    persen_diputuskan_ai: float | None
    persen_kesepakatan_admin: float | None
    banding_diajukan: int
    banding_dikabulkan: int
    koreksi_tingkat: int
