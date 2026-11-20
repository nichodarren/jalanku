"""Test integrasi GET /api/saya/laporan (US-11)."""

from __future__ import annotations

import io

from PIL import Image

from conftest import TITIK
from jalanku.modules.laporan import LaporanBaru, buat_laporan, ubah_status

MONAS = TITIK["monas"]


def _jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (120, 120, 120)).save(buf, "JPEG")
    return buf.getvalue()


def _lapor(klien, geser: float = 0.0):
    r = klien.post(
        "/api/laporan",
        data={"lat": str(MONAS[0] + geser), "lon": str(MONAS[1]), "sumber_lokasi": "manual"},
        files=[("foto", ("a.jpg", _jpeg(), "image/jpeg"))],
    )
    assert r.status_code == 201, r.text
    return r.json()["nomor"]


def _laporan_orang_lain(keputusan: str = "terverifikasi"):
    return buat_laporan(
        LaporanBaru(
            pelapor_id=None,
            lat=MONAS[0] + 0.01,
            lon=MONAS[1],
            sumber_lokasi="manual",
            kota="Jakarta Pusat",
            kecamatan="Gambir",
            instansi_id="SUDIN_JP",
            foto=[_jpeg()],
            keputusan_ai=keputusan,
            tingkat="rusak" if keputusan == "terverifikasi" else None,
        )
    )


def test_tanpa_login_401(klien):
    assert klien.get("/api/saya/laporan").status_code == 401


def test_pelapor_baru_belum_punya_laporan(buat_klien):
    r = buat_klien("pelapor").get("/api/saya/laporan")
    assert r.status_code == 200
    assert r.json() == []


def test_hanya_laporan_milik_sendiri_terbaru_dulu(buat_klien):
    saya = buat_klien("pelapor", email="saya@uji.test")
    n1 = _lapor(saya, geser=0.0)
    n2 = _lapor(saya, geser=0.002)
    _lapor(buat_klien("pelapor", email="lain@uji.test"), geser=0.004)
    _laporan_orang_lain()
    daftar = saya.get("/api/saya/laporan").json()
    assert [d["nomor"] for d in daftar] == [n2, n1]


def test_isi_item_lengkap_dan_foto_bisa_diambil(buat_klien):
    saya = buat_klien("pelapor")
    nomor = _lapor(saya)
    item = saya.get("/api/saya/laporan").json()[0]
    assert item["nomor"] == nomor
    assert item["status"] == "menunggu_verifikasi"
    assert item["kota"] == "Jakarta Pusat" and item["kecamatan"]
    assert item["dibuat_pada"]
    assert item["foto_url"].startswith("/api/foto/")
    assert saya.get(item["foto_url"]).status_code == 200  # pelapor boleh melihat fotonya (BR-06)


def test_laporan_menunggu_tidak_bisa_banding(buat_klien):
    saya = buat_klien("pelapor")
    _lapor(saya)
    assert saya.get("/api/saya/laporan").json()[0]["bisa_banding"] is False


def test_penolakan_ai_bisa_banding(buat_klien, monkeypatch):
    """Penolakan oleh AI (semua foto Baik dengan yakin) boleh dibanding sekali."""
    from jalanku.modules.ai import FOTO_TOLAK, KELAS_BAIK, HasilFoto, KeputusanAI

    hasil = HasilFoto(kelas=KELAS_BAIK, confidence=0.97, kemiripan=0.9, keputusan=FOTO_TOLAK, alasan="uji")
    monkeypatch.setattr("jalanku.modules.pelaporan.layanan.periksa_foto", lambda data: hasil)
    monkeypatch.setattr(
        "jalanku.modules.pelaporan.layanan.putuskan",
        lambda daftar: KeputusanAI("ditolak", None, list(daftar), "uji-1"),
    )
    saya = buat_klien("pelapor")
    _lapor(saya)
    item = saya.get("/api/saya/laporan").json()[0]
    assert item["status"] == "ditolak"
    assert item["bisa_banding"] is True


def _ai_menolak(monkeypatch):
    """Semua foto dinilai Baik dengan yakin, jadi laporan langsung ditolak oleh AI."""
    from jalanku.modules.ai import FOTO_TOLAK, KELAS_BAIK, HasilFoto, KeputusanAI

    hasil = HasilFoto(kelas=KELAS_BAIK, confidence=0.97, kemiripan=0.9, keputusan=FOTO_TOLAK, alasan="uji")
    monkeypatch.setattr("jalanku.modules.pelaporan.layanan.periksa_foto", lambda data: hasil)
    monkeypatch.setattr(
        "jalanku.modules.pelaporan.layanan.putuskan",
        lambda daftar: KeputusanAI("ditolak", None, list(daftar), "uji-1"),
    )


def test_penolakan_ai_yang_sudah_dibanding_tidak_bisa_banding_lagi(buat_klien, monkeypatch):
    """Banding hanya sekali (BR-03). Syarat ``banding_pada is None`` diuji sendirian: pemeriksa tetap AI,
    hanya ``banding_pada`` yang diisi, jadi test ini merah bila syarat itu dihapus."""
    from dataclasses import replace

    from jalanku.modules.pelaporan import layanan

    _ai_menolak(monkeypatch)
    saya = buat_klien("pelapor")
    _lapor(saya)
    assert saya.get("/api/saya/laporan").json()[0]["bisa_banding"] is True

    asli = layanan.cari_laporan
    monkeypatch.setattr(
        "jalanku.modules.pelaporan.layanan.cari_laporan",
        lambda **kw: [replace(lap, banding_pada="2026-11-20T10:00:00") for lap in asli(**kw)],
    )
    item = saya.get("/api/saya/laporan").json()[0]
    assert item["status"] == "ditolak"
    assert item["bisa_banding"] is False


def test_sudah_dibanding_lalu_ditolak_admin_tidak_bisa_banding(buat_klien, monkeypatch):
    """Alur nyata: ditolak AI → banding → ditolak Admin. Penolakan kedua final."""
    _ai_menolak(monkeypatch)
    saya = buat_klien("pelapor")
    nomor = _lapor(saya)
    ubah_status(nomor, "menunggu_verifikasi", "pelapor", pengguna_id=None)
    ubah_status(nomor, "ditolak", "admin", pengguna_id=None, catatan="Foto bukan jalan")
    item = saya.get("/api/saya/laporan").json()[0]
    assert item["status"] == "ditolak"
    assert item["bisa_banding"] is False


def test_penolakan_admin_tidak_bisa_banding(buat_klien):
    """Banding hanya untuk penolakan AI (BR-03); penolakan Admin sudah final."""
    saya = buat_klien("pelapor")
    nomor = _lapor(saya)
    ubah_status(nomor, "ditolak", "admin", pengguna_id=None, catatan="Foto bukan jalan")
    item = saya.get("/api/saya/laporan").json()[0]
    assert item["status"] == "ditolak"
    assert item["bisa_banding"] is False


def test_respons_tidak_memuat_data_pribadi(buat_klien):
    saya = buat_klien("pelapor", email="rahasia@uji.test")
    _lapor(saya)
    teks = saya.get("/api/saya/laporan").text
    assert "rahasia" not in teks
    assert "pelapor_id" not in teks
