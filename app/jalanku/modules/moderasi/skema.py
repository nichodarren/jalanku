"""Skema HTTP modul moderasi."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FotoAntrean(BaseModel):
    url: str
    hasil_ai: dict | None


class DuplikatAntrean(BaseModel):
    nomor: str
    jarak_m: float


class ItemAntreanKeluaran(BaseModel):
    nomor: str
    dibuat_pada: str
    banding: bool = Field(description="True = permintaan peninjauan; tampil paling atas")
    kota: str | None
    kecamatan: str | None
    keterangan: str
    foto: list[FotoAntrean]
    duplikat: list[DuplikatAntrean]


class VerifikasiMasukan(BaseModel):
    tingkat: str = Field(description="kurang_baik | rusak")


class TolakMasukan(BaseModel):
    alasan: str = Field(min_length=3, max_length=200)
    label: str | None = Field(default=None, description="baik | bukan_jalan (untuk data latih)")


class GabungMasukan(BaseModel):
    induk_nomor: str


class KoreksiMasukan(BaseModel):
    tingkat: str = Field(description="kurang_baik | rusak")
    alasan: str = Field(min_length=3, max_length=200)


class AksiKeluaran(BaseModel):
    nomor: str
    status: str
    tingkat: str | None


class PaketKeluaran(BaseModel):
    nomor: str
    instansi_id: str
    kanal_nama: str
    kanal_url: str
    teks: str = Field(description="Ringkasan siap salin, TANPA identitas pelapor (NFR-PRI-01)")
