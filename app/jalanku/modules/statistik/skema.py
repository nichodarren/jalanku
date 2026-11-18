"""Skema HTTP modul statistik."""

from __future__ import annotations

from pydantic import BaseModel, Field


class StatistikInstansi(BaseModel):
    instansi_id: str
    nama_pendek: str
    jumlah_per_status: dict[str, int]
    median_jam_dikerjakan: float | None = Field(description="null bila n < 5 (BR-04)")
    median_jam_selesai: float | None = Field(description="null bila n < 5 (BR-04)")
    n_dikerjakan: int
    n_selesai: int


class StatistikKeluaran(BaseModel):
    label_simulasi: bool = Field(description="True selama petugas diperankan tim (BR-04)")
    periode_hari: int
    persen_diputuskan_ai: float | None
    instansi: list[StatistikInstansi]


class KejadianMasukan(BaseModel):
    jenis: str = Field(description="buka_status")
    nomor: str
