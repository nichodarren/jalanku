"""Skema HTTP modul laporan. Identitas pelapor TIDAK pernah ada di skema publik (NFR-PRI-01)."""

from __future__ import annotations

from pydantic import BaseModel


class FotoKeluaran(BaseModel):
    id: int
    jenis: str  # bukti | sesudah
    url: str
    hasil_ai: dict | None = None  # hanya untuk pemilik laporan & Admin


class EntriTimelineKeluaran(BaseModel):
    dari_status: str | None
    ke_status: str
    pelaku: str  # ai | admin | petugas | pelapor | sistem
    catatan: str
    waktu: str


class EntriJejakKeluaran(BaseModel):
    ke_status: str
    pelaku: str
    waktu: str
    hash: str


class JejakKeluaran(BaseModel):
    nomor: str
    utuh: bool  # True bila rantai hash timeline cocok (tidak ada entri yang diubah/dihapus)
    entri: list[EntriJejakKeluaran]


class DetailLaporanKeluaran(BaseModel):
    nomor: str
    status: str
    tingkat: str | None
    lat: float
    lon: float
    kota: str | None
    kecamatan: str | None
    instansi_id: str
    keterangan: str
    diperiksa_oleh: str | None  # ai | admin
    jumlah_dukungan: int
    simulasi: bool
    dibuat_pada: str
    diverifikasi_pada: str | None
    mulai_dikerjakan_pada: str | None
    selesai_pada: str | None
    foto: list[FotoKeluaran]
    timeline: list[EntriTimelineKeluaran]
