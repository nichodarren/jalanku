"""Modul wilayah — ANTARMUKA PUBLIK. Pemilik: M2. Kartu modul: README.md."""

from .layanan import ambil_instansi, batas_wilayah_geojson, boleh_menangani, daftar_instansi, tentukan_wilayah
from .rute import router
from .tipe import ID_DINAS, KANAL_LUAR_WILAYAH, KOTA, HasilWilayah, Instansi

__all__ = [
    "ID_DINAS",
    "KANAL_LUAR_WILAYAH",
    "KOTA",
    "HasilWilayah",
    "Instansi",
    "ambil_instansi",
    "batas_wilayah_geojson",
    "boleh_menangani",
    "daftar_instansi",
    "router",
    "tentukan_wilayah",
]
