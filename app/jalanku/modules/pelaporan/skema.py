"""Skema HTTP modul pelaporan."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LokasiMasukan(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    akurasi_gps: float | None = Field(default=None, ge=0)


class InstansiRingkas(BaseModel):
    id: str
    nama_pendek: str
    kanal_nama: str
    kanal_url: str


class KanalLuar(BaseModel):
    nama: str
    url: str


class DuplikatKeluaran(BaseModel):
    nomor: str
    jarak_m: float
    status: str
    tingkat: str | None
    jumlah_dukungan: int


class PratinjauLokasiKeluaran(BaseModel):
    di_dalam: bool
    kota: str | None
    kecamatan: str | None
    instansi: InstansiRingkas | None
    perlu_konfirmasi_pin: bool = Field(description="BR-01 c: akurasi GPS > 50 m")
    kanal_luar: KanalLuar | None = Field(description="Arahan bila di luar Jakarta (FR-WIL-02)")
    duplikat: list[DuplikatKeluaran]


class HasilKirimKeluaran(BaseModel):
    nomor: str
    status: str
    tingkat: str | None
    instansi_id: str
    instansi_nama: str
    url_status: str
    pesan: str


class DukunganKeluaran(BaseModel):
    nomor: str
    jumlah_dukungan: int
    baru: bool


class LaporanSayaKeluaran(BaseModel):
    nomor: str
    status: str
    tingkat: str | None
    kota: str | None
    kecamatan: str | None
    dibuat_pada: str
    foto_url: str | None
    bisa_banding: bool
