"""Tipe publik modul wilayah."""

from __future__ import annotations

from dataclasses import dataclass

KOTA = ("Jakarta Pusat", "Jakarta Utara", "Jakarta Barat", "Jakarta Selatan", "Jakarta Timur")
ID_DINAS = "DINAS_BM"
KANAL_LUAR_WILAYAH = ("SP4N-LAPOR!", "https://www.lapor.go.id/")


@dataclass(frozen=True)
class Instansi:
    id: str
    nama: str
    nama_pendek: str
    kota: str | None  # None = Dinas provinsi
    kanal_nama: str
    kanal_url: str


@dataclass(frozen=True)
class HasilWilayah:
    di_dalam: bool
    kota: str | None
    kecamatan: str | None
    instansi: Instansi | None
