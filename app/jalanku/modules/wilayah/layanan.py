"""Penentuan wilayah dan instansi (BR-01) dari batas kecamatan lokal TS-04."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from shapely import STRtree
from shapely.errors import ShapelyError
from shapely.geometry import Point, shape

from jalanku.core import GalatDomain, TidakDitemukan, TidakValid, koneksi, pengaturan

from .tipe import ID_DINAS, KOTA, HasilWilayah, Instansi


class _DataTidakTersedia(GalatDomain):
    kode_http = 503


@dataclass(frozen=True)
class _Indeks:
    geojson: dict
    nama: list[tuple[str, str]]
    pohon: STRtree


@lru_cache(maxsize=1)
def _muat_indeks(jalur: Path, revisi: int) -> _Indeks:
    """Gunakan ulang indeks sampai berkas di jalur itu diperbarui."""
    data = json.loads(jalur.read_text(encoding="utf-8"))
    if data["type"] != "FeatureCollection" or not data["features"]:
        raise ValueError("FeatureCollection wilayah kosong atau tidak valid.")
    nama = []
    geometri = []
    for fitur in data["features"]:
        properti = fitur["properties"]
        kota, kecamatan = properti["kota"], properti["kecamatan"]
        batas = shape(fitur["geometry"])
        if kota not in KOTA or not isinstance(kecamatan, str) or not kecamatan.strip():
            raise ValueError("Identitas kecamatan tidak valid.")
        if batas.geom_type not in {"Polygon", "MultiPolygon"} or batas.is_empty or not batas.is_valid:
            raise ValueError("Poligon kecamatan tidak valid.")
        nama.append((kota, kecamatan))
        geometri.append(batas)
    return _Indeks(data, nama, STRtree(geometri))


def _indeks() -> _Indeks:
    jalur = pengaturan().folder_data / "wilayah-dki-jakarta.geojson"
    try:
        return _muat_indeks(jalur, jalur.stat().st_mtime_ns)
    except (OSError, ValueError, TypeError, KeyError, IndexError, AttributeError, ShapelyError) as galat:
        raise _DataTidakTersedia("Data batas kecamatan belum tersedia atau rusak.") from galat


def _ke_instansi(b) -> Instansi:
    return Instansi(b["id"], b["nama"], b["nama_pendek"], b["kota"], b["kanal_nama"], b["kanal_url"])


def daftar_instansi() -> list[Instansi]:
    kon = koneksi()
    try:
        return [_ke_instansi(b) for b in kon.execute("SELECT * FROM wilayah_instansi ORDER BY id")]
    finally:
        kon.close()


def ambil_instansi(instansi_id: str) -> Instansi:
    kon = koneksi()
    try:
        b = kon.execute("SELECT * FROM wilayah_instansi WHERE id = ?", (instansi_id,)).fetchone()
    finally:
        kon.close()
    if b is None:
        raise TidakDitemukan("Instansi tidak ditemukan.")
    return _ke_instansi(b)


def tentukan_wilayah(lat: float, lon: float) -> HasilWilayah:
    """Cari kecamatan yang mencakup titik, termasuk tepi poligonnya."""
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise TidakValid("Koordinat di luar rentang yang diizinkan.")
    indeks = _indeks()
    cocok = indeks.pohon.query(Point(lon, lat), predicate="covered_by")
    if len(cocok) == 0:
        return HasilWilayah(di_dalam=False, kota=None, kecamatan=None, instansi=None)
    # Di batas bersama, pilih pasangan kota/kecamatan pertama secara alfabetis.
    kota, kecamatan = min(indeks.nama[i] for i in cocok)
    for instansi in daftar_instansi():
        if instansi.kota == kota:
            return HasilWilayah(True, kota, kecamatan, instansi)
    raise _DataTidakTersedia("Sudin untuk kota ini belum tersedia.")


def boleh_menangani(instansi_id: str, kota: str | None) -> bool:
    """BR-01 d: Dinas provinsi boleh semua kota; Sudin hanya kotanya sendiri."""
    if instansi_id == ID_DINAS:
        return True
    try:
        return ambil_instansi(instansi_id).kota == kota
    except TidakDitemukan:
        return False


def batas_wilayah_geojson() -> dict:
    """Kembalikan salinan batas kecamatan untuk peta."""
    return deepcopy(_indeks().geojson)
