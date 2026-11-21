"""Proxy tile peta OpenStreetMap lewat server JalanKu, dengan cache di disk (issue #22).

Kenapa: di sebagian jaringan/perangkat (mis. GitHub Codespaces), tile yang diminta browser langsung
ke OSM dibalas gambar "Access blocked". Lewat proxy, browser hanya bicara ke origin sendiri (CSP
``img-src 'self'``), lalu server mengambil tile dengan User-Agent yang jelas sesuai Tile Usage
Policy OSM dan menyimpannya di ``<JALANKU_DATA>/tile`` selama 7 hari.

Bukan proxy terbuka: URL tujuan tetap (tidak ada SSRF), hanya zoom 10 sampai 19 di kotak DKI Jakarta
(termasuk Kepulauan Seribu), balasan wajib PNG ≤ 512 KB, dan unduhan ke OSM (cache miss) dibatasi
per klien dan untuk semua klien bersama. Hanya dipakai ``main.py``; tidak diekspor di ``__all__``.
"""

from __future__ import annotations

import contextlib
import math
import secrets
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path

from .config import pengaturan
from .keamanan import batasi

URL_OSM = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
USER_AGENT = "JalanKu/0.1 (+https://github.com/nichodarren/jalanku)"
ZOOM_MIN, ZOOM_MAX = 10, 19
# Kotak DKI Jakarta (daratan + Kepulauan Seribu) dengan sedikit kelonggaran. Sama dengan peta-dasar.js.
BATAS = {"lon_min": 106.3, "lon_max": 107.2, "lat_min": -6.5, "lat_max": -5.1}
UMUR_CACHE_DETIK = 7 * 24 * 3600
MAKS_BYTE_TILE = 512 * 1024
MAKS_UNDUH_PER_MENIT = 300  # per klien; tile dari cache tidak dihitung
MAKS_UNDUH_GLOBAL_PER_MENIT = 600  # semua klien bersama: mencegah unduhan massal (Tile Usage Policy OSM)
PNG_AWAL = b"\x89PNG\r\n\x1a\n"

Pengunduh = Callable[[int, int, int], bytes]


class TileTidakValid(ValueError):
    """Tile di luar zoom/wilayah yang dilayani."""


def _lon(x: int, z: int) -> float:
    return x / 2**z * 360.0 - 180.0


def _lat(y: int, z: int) -> float:
    return math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / 2**z))))


def periksa(z: int, x: int, y: int) -> None:
    """Tolak tile di luar zoom yang dipakai aplikasi atau yang tidak bersinggungan dengan kotak Jakarta."""
    if not ZOOM_MIN <= z <= ZOOM_MAX:
        raise TileTidakValid("Zoom di luar jangkauan.")
    # x/y di luar 0..2^z-1 otomatis jatuh di luar kotak Jakarta di bawah, jadi tidak perlu dicek terpisah.
    barat, timur = _lon(x, z), _lon(x + 1, z)
    utara, selatan = _lat(y, z), _lat(y + 1, z)
    if timur < BATAS["lon_min"] or barat > BATAS["lon_max"] or utara < BATAS["lat_min"] or selatan > BATAS["lat_max"]:
        raise TileTidakValid("Tile di luar wilayah DKI Jakarta.")


def unduh_osm(z: int, x: int, y: int, timeout: float = 10.0) -> bytes:
    # URL tetap (https ke OSM), bukan dari input pengguna: tidak ada SSRF.
    req = urllib.request.Request(URL_OSM.format(z=z, x=x, y=y), headers={"User-Agent": USER_AGENT})  # noqa: S310
    with urllib.request.urlopen(req, timeout=timeout) as r:  # noqa: S310
        return r.read(MAKS_BYTE_TILE + 1)


def _jalur(z: int, x: int, y: int) -> Path:
    return pengaturan().folder_data / "tile" / str(z) / str(x) / f"{y}.png"


def _tulis_atomik(jalur: Path, data: bytes) -> None:
    """Simpan ke cache tanpa pernah meninggalkan berkas setengah jadi. Cache bersifat best-effort:
    kalau gagal (disk penuh, atau di Windows berkas sedang dibuka request lain), tile tetap dikirim."""
    sementara = jalur.with_name(f"{jalur.stem}.{secrets.token_hex(6)}.tmp")
    try:
        jalur.parent.mkdir(parents=True, exist_ok=True)
        sementara.write_bytes(data)
        sementara.replace(jalur)
    except OSError:
        pass
    finally:
        with contextlib.suppress(FileNotFoundError):
            sementara.unlink()


def ambil(z: int, x: int, y: int, *, klien: str = "-", unduh: Pengunduh | None = None) -> bytes | None:
    """PNG tile dari cache, atau diunduh dari OSM bila belum ada/kedaluwarsa.

    Bila unduhan gagal tapi cache lama ada, cache lama tetap dipakai. ``None`` = tidak ada tile.
    Melempar ``TileTidakValid`` (tile tidak dilayani) atau ``TerlaluBanyak`` (jatah unduh klien habis).
    """
    periksa(z, x, y)
    jalur = _jalur(z, x, y)
    lama: bytes | None = None
    with contextlib.suppress(OSError):  # belum ada, atau sedang ditimpa request lain
        lama = jalur.read_bytes()
        if time.time() - jalur.stat().st_mtime < UMUR_CACHE_DETIK:
            return lama
    batasi("tile:semua", MAKS_UNDUH_GLOBAL_PER_MENIT, 60, "Peta sedang ramai. Coba lagi sebentar.")
    batasi(f"tile:{klien}", MAKS_UNDUH_PER_MENIT, 60, "Terlalu banyak permintaan peta. Coba lagi sebentar.")
    try:
        data = (unduh or unduh_osm)(z, x, y)
    except (urllib.error.URLError, TimeoutError, OSError):
        return lama
    if not data.startswith(PNG_AWAL) or len(data) > MAKS_BYTE_TILE:
        return lama
    _tulis_atomik(jalur, data)
    return data
