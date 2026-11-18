"""Penentuan wilayah & instansi (BR-01).

STUB (baseline 19 Nov 2026): ``tentukan_wilayah`` memakai KOTAK KASAR Jakarta, dan semua titik
di dalamnya dianggap Gambir / Jakarta Pusat / SUDIN_JP. Cukup untuk modul lain mengembangkan
alurnya. M2 menggantinya dengan poligon 42 kecamatan GADM (TS-04, US-07) memakai shapely STRtree.
Sumber data & script di jalanku-v0 branch trial/mvp-v2: app/scripts/siapkan_wilayah.py,
app/jalanku/data/wilayah-dki-jakarta.geojson.
"""

from __future__ import annotations

from jalanku.core import TidakDitemukan, koneksi

from .tipe import ID_DINAS, HasilWilayah, Instansi

# Kotak kasar DKI Jakarta daratan (lat min, lat maks, lon min, lon maks). STUB.
_KOTAK_JAKARTA = (-6.375, -6.08, 106.685, 106.975)


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
    lat_min, lat_maks, lon_min, lon_maks = _KOTAK_JAKARTA
    if not (lat_min <= lat <= lat_maks and lon_min <= lon <= lon_maks):
        return HasilWilayah(di_dalam=False, kota=None, kecamatan=None, instansi=None)
    return HasilWilayah(di_dalam=True, kota="Jakarta Pusat", kecamatan="Gambir", instansi=ambil_instansi("SUDIN_JP"))


def boleh_menangani(instansi_id: str, kota: str | None) -> bool:
    """BR-01 d: Dinas provinsi boleh semua kota; Sudin hanya kotanya sendiri."""
    if instansi_id == ID_DINAS:
        return True
    try:
        return ambil_instansi(instansi_id).kota == kota
    except TidakDitemukan:
        return False


def batas_wilayah_geojson() -> dict:
    """GeoJSON FeatureCollection kecamatan. STUB: satu kotak kasar."""
    lat_min, lat_maks, lon_min, lon_maks = _KOTAK_JAKARTA
    kotak = [[lon_min, lat_min], [lon_maks, lat_min], [lon_maks, lat_maks], [lon_min, lat_maks], [lon_min, lat_min]]
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"kota": "STUB", "kecamatan": "STUB (kotak kasar, bukan batas asli)"},
                "geometry": {"type": "Polygon", "coordinates": [kotak]},
            }
        ],
    }
