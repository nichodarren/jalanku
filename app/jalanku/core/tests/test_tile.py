"""Proxy tile peta OSM (``core/tile.py`` + ``GET /api/tile/{z}/{x}/{y}.png``), issue #22.

Tidak ada test yang menghubungi OSM sungguhan: pengunduh selalu diganti.
"""

from __future__ import annotations

import contextlib
import os
import threading
import time
import urllib.error

import pytest

from jalanku.core import TerlaluBanyak, pengaturan
from jalanku.core import tile as t

PNG = t.PNG_AWAL + b"isi-tile"
JKT = (12, 3263, 2118)  # tile Jakarta Pusat di zoom 12


def _jalur(z, x, y):
    return pengaturan().folder_data / "tile" / str(z) / str(x) / f"{y}.png"


# --- Batas: bukan proxy terbuka -----------------------------------------------------------------


@pytest.mark.parametrize(
    "z,x,y",
    [
        JKT,
        (10, 815, 529),  # zoom terkecil
        (19, 417722, 271155),  # zoom terbesar (Monas)
        (12, 3260, 2111),  # Kepulauan Seribu
        (12, 3263, 2122),  # tepi selatan kotak masih bersinggungan
        (12, 3267, 2118),  # tepi timur kotak masih bersinggungan
    ],
)
def test_tile_jakarta_diterima(z, x, y):
    t.periksa(z, x, y)


@pytest.mark.parametrize(
    "z,x,y",
    [
        (9, 407, 264),  # zoom terlalu kecil
        (20, 835444, 542310),  # zoom terlalu besar (Monas)
        (12, 0, 0),  # ujung dunia
        (12, 3263, 1900),  # jauh di utara
        (12, 3268, 2118),  # tepat di luar tepi timur
        (12, 3263, 2123),  # tepat di luar tepi selatan
        (12, 3263, 2105),  # tepat di luar tepi utara
        (12, 3256, 2118),  # di barat (Tangerang barat jauh)
        (12, -1, 2118),  # negatif
        (12, 4096, 2118),  # melewati jumlah tile di zoom ini
    ],
)
def test_tile_di_luar_jakarta_atau_zoom_ditolak(z, x, y):
    with pytest.raises(t.TileTidakValid):
        t.periksa(z, x, y)


def test_ambil_menolak_sebelum_mengunduh():
    dipanggil = []
    with pytest.raises(t.TileTidakValid):
        t.ambil(12, 0, 0, unduh=lambda *a: dipanggil.append(a) or PNG)
    assert dipanggil == []


# --- Cache ---------------------------------------------------------------------------------------


def test_unduh_sekali_lalu_dari_cache():
    panggil = []

    def unduh(*a):
        panggil.append(a)
        return PNG

    assert t.ambil(*JKT, unduh=unduh) == PNG
    assert t.ambil(*JKT, unduh=unduh) == PNG
    assert panggil == [JKT]
    assert _jalur(*JKT).read_bytes() == PNG


def test_cache_kedaluwarsa_diunduh_ulang():
    t.ambil(*JKT, unduh=lambda *a: PNG)
    tua = time.time() - t.UMUR_CACHE_DETIK - 10
    os.utime(_jalur(*JKT), (tua, tua))
    baru = t.PNG_AWAL + b"versi-baru"
    assert t.ambil(*JKT, unduh=lambda *a: baru) == baru


@pytest.mark.parametrize(
    "galat",
    [
        urllib.error.URLError("offline"),
        TimeoutError(),
        OSError("putus"),
        urllib.error.HTTPError("u", 429, "", {}, None),
    ],
)
def test_cache_lama_tetap_dipakai_saat_osm_gagal(galat):
    t.ambil(*JKT, unduh=lambda *a: PNG)
    tua = time.time() - t.UMUR_CACHE_DETIK - 10
    os.utime(_jalur(*JKT), (tua, tua))

    def gagal(*a):
        raise galat

    assert t.ambil(*JKT, unduh=gagal) == PNG


def test_tanpa_cache_dan_osm_gagal_hasilnya_none():
    def gagal(*a):
        raise TimeoutError

    assert t.ambil(*JKT, unduh=gagal) is None
    assert not _jalur(*JKT).exists()


@pytest.mark.parametrize("isi", [b"<html>Access blocked</html>", b"", t.PNG_AWAL + b"x" * t.MAKS_BYTE_TILE])
def test_balasan_bukan_png_atau_terlalu_besar_tidak_disimpan(isi):
    assert t.ambil(*JKT, unduh=lambda *a: isi) is None
    assert not _jalur(*JKT).exists()


def test_tidak_ada_berkas_sementara_tertinggal():
    t.ambil(*JKT, unduh=lambda *a: PNG)
    folder = _jalur(*JKT).parent
    assert [p.name for p in folder.iterdir()] == [f"{JKT[2]}.png"]


def test_gagal_menyimpan_cache_tile_tetap_dikirim_tanpa_sisa(monkeypatch):
    def gagal_replace(self, target):
        raise PermissionError("berkas sedang dibuka")

    monkeypatch.setattr(t.Path, "replace", gagal_replace)
    assert t.ambil(*JKT, unduh=lambda *a: PNG) == PNG
    assert list(_jalur(*JKT).parent.iterdir()) == []


def test_unduhan_bersamaan_tidak_saling_merusak():
    mulai = threading.Barrier(8)
    hasil, galat = [], []

    def unduh(*a):
        mulai.wait(timeout=5)
        return PNG

    def kerja():
        try:
            hasil.append(t.ambil(*JKT, unduh=unduh))
        except Exception as e:  # noqa: BLE001
            galat.append(e)

    utas = [threading.Thread(target=kerja) for _ in range(8)]
    for u in utas:
        u.start()
    for u in utas:
        u.join()
    assert galat == []
    assert hasil == [PNG] * 8
    assert _jalur(*JKT).read_bytes() == PNG


# --- Rate limit unduhan ke OSM (hanya cache miss) -------------------------------------------------


def test_unduhan_ke_osm_dibatasi_per_klien():
    for i in range(t.MAKS_UNDUH_PER_MENIT):  # tile berbeda-beda → semuanya cache miss
        t.ambil(19, 417722 + i, 271155, klien="1.2.3.4", unduh=lambda *a: PNG)
    with pytest.raises(TerlaluBanyak):
        t.ambil(19, 417722, 271156, klien="1.2.3.4", unduh=lambda *a: PNG)
    # klien lain tidak terdampak
    assert t.ambil(19, 417722, 271156, klien="5.6.7.8", unduh=lambda *a: PNG) == PNG


def test_tile_dari_cache_tidak_menghabiskan_jatah():
    t.ambil(*JKT, klien="1.2.3.4", unduh=lambda *a: PNG)
    for _ in range(t.MAKS_UNDUH_PER_MENIT * 2):
        assert t.ambil(*JKT, klien="1.2.3.4", unduh=lambda *a: PNG) == PNG


def test_unduh_osm_memakai_url_tetap_dan_user_agent(monkeypatch):
    diminta = {}

    class Balasan:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def read(self, n=-1):
            diminta["n"] = n
            return PNG

    def urlopen(req, timeout):
        diminta.update(url=req.full_url, ua=req.get_header("User-agent"), timeout=timeout)
        return Balasan()

    monkeypatch.setattr(t.urllib.request, "urlopen", urlopen)
    assert t.unduh_osm(*JKT) == PNG
    assert diminta["url"] == "https://tile.openstreetmap.org/12/3263/2118.png"
    assert "JalanKu" in diminta["ua"]
    assert diminta["n"] == t.MAKS_BYTE_TILE + 1  # tidak membaca balasan tanpa batas
    assert diminta["timeout"] <= 10


# --- Lewat HTTP -----------------------------------------------------------------------------------


def test_endpoint_tile(klien, monkeypatch):
    monkeypatch.setattr(t, "unduh_osm", lambda z, x, y: PNG)
    r = klien.get("/api/tile/12/3263/2118.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.headers["cache-control"] == "public, max-age=86400"
    assert r.content == PNG


def test_endpoint_tile_luar_jakarta_404(klien, monkeypatch):
    monkeypatch.setattr(t, "unduh_osm", lambda z, x, y: pytest.fail("tidak boleh mengunduh"))
    assert klien.get("/api/tile/12/0/0.png").status_code == 404
    assert klien.get("/api/tile/5/25/16.png").status_code == 404


def test_endpoint_tile_osm_gagal_502_tanpa_cache(klien, monkeypatch):
    def gagal(*a):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(t, "unduh_osm", gagal)
    r = klien.get("/api/tile/12/3263/2118.png")
    assert r.status_code == 502
    assert r.headers["cache-control"] == "no-store"


def test_endpoint_tile_tidak_ada_di_kontrak_openapi(klien):
    assert not any(j.startswith("/api/tile") for j in klien.get("/api/openapi.json").json()["paths"])


def test_csp_hanya_mengizinkan_gambar_dari_server_sendiri(klien):
    csp = klien.get("/").headers["content-security-policy"]
    img = next(b for b in csp.split(";") if b.strip().startswith("img-src")).split()
    assert img == ["img-src", "'self'", "data:", "blob:"]


# --- Sisi browser (web/shared/peta-dasar.js) ------------------------------------------------------


def test_peta_dasar_memakai_proxy_dengan_batas_yang_sama_dengan_server():
    import re
    from pathlib import Path

    js = (Path(t.__file__).resolve().parents[1] / "web" / "shared" / "peta-dasar.js").read_text(encoding="utf-8")
    assert 'tileLayer("/api/tile/{z}/{x}/{y}.png"' in js
    assert "tile.openstreetmap.org/{z}" not in js  # tidak ada lagi permintaan tile langsung ke OSM
    assert "openstreetmap.org/copyright" in js  # atribusi wajib (NFR-LEG-01)
    assert f"const ZOOM_MIN = {t.ZOOM_MIN};" in js
    assert f"const ZOOM_MAKS = {t.ZOOM_MAX};" in js
    angka = [float(a) for a in re.findall(r"-?\d+\.\d+", js.split("const BATAS_TILE")[1].split(";")[0])]
    b = t.BATAS
    assert angka == [b["lat_min"], b["lon_min"], b["lat_max"], b["lon_max"]]


def test_unduhan_ke_osm_dibatasi_global_walau_tiap_klien_masih_di_bawah_jatah():
    # Saran review #31: banyak IP bersama-sama tidak boleh membuat server mengunduh massal dari OSM.
    per_klien = t.MAKS_UNDUH_PER_MENIT // 2
    jumlah_klien = t.MAKS_UNDUH_GLOBAL_PER_MENIT // per_klien
    n = 0
    for k in range(jumlah_klien):
        for _ in range(per_klien):
            t.ambil(19, 417000 + n, 271155, klien=f"10.0.0.{k}", unduh=lambda *a: PNG)
            n += 1
    assert n == t.MAKS_UNDUH_GLOBAL_PER_MENIT
    with pytest.raises(TerlaluBanyak):
        t.ambil(19, 417000 + n, 271155, klien="10.0.9.9", unduh=lambda *a: PNG)  # klien baru pun ditolak
    assert t.MAKS_UNDUH_PER_MENIT < t.MAKS_UNDUH_GLOBAL_PER_MENIT


def test_satu_klien_nakal_tidak_menghabiskan_jatah_global():
    # Review #39 (Yosua): permintaan yang ditolak batas per klien tidak boleh ikut memakai jatah global (DoS).
    n = 0
    for _ in range(t.MAKS_UNDUH_GLOBAL_PER_MENIT):
        with contextlib.suppress(TerlaluBanyak):
            t.ambil(19, 417000 + n, 271155, klien="6.6.6.6", unduh=lambda *a: PNG)
        n += 1
    assert t.ambil(19, 417000 + n, 271155, klien="10.1.1.1", unduh=lambda *a: PNG) == PNG
