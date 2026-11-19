"""Test integrasi POST /api/laporan (US-03). Lewat HTTP TestClient, DB sementara per test (conftest)."""

from __future__ import annotations

import io

import pytest
from PIL import Image

from conftest import TITIK
from jalanku.modules.ai import (
    FOTO_TERIMA,
    KELAS_RUSAK,
    KEPUTUSAN_DITOLAK,
    KEPUTUSAN_TERVERIFIKASI,
    HasilFoto,
    KeputusanAI,
)
from jalanku.modules.laporan import ambil_laporan, daftar_foto

MONAS = TITIK["monas"]


def _jpeg(ukuran: tuple[int, int] = (8, 8)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", ukuran, (120, 120, 120)).save(buf, "JPEG")
    return buf.getvalue()


def _kirim(klien, *, jumlah_foto: int = 1, titik=MONAS, berkas=None, **data):
    isi = {"lat": str(titik[0]), "lon": str(titik[1]), "sumber_lokasi": "manual", **data}
    if berkas is None:
        berkas = [("foto", (f"foto{i}.jpg", _jpeg(), "image/jpeg")) for i in range(jumlah_foto)]
    return klien.post("/api/laporan", data=isi, files=berkas or None)


@pytest.fixture
def pelapor(buat_klien):
    return buat_klien("pelapor")


def test_sukses_dengan_ai_tidak_aktif_menunggu_verifikasi(pelapor):
    """AI stub (model mati) → semua ke Admin → 201 berstatus menunggu_verifikasi."""
    r = _kirim(pelapor, keterangan="lubang besar")
    assert r.status_code == 201, r.text
    j = r.json()
    assert j["nomor"].startswith("JK-")
    assert j["status"] == "menunggu_verifikasi"
    assert j["tingkat"] is None
    assert j["instansi_id"] == "SUDIN_JP"
    assert j["url_status"].endswith(j["nomor"])
    assert j["pesan"]


def test_tiga_foto_diterima_dan_tersimpan(pelapor):
    r = _kirim(pelapor, jumlah_foto=3)
    assert r.status_code == 201, r.text
    lap = ambil_laporan(r.json()["nomor"])
    assert len(daftar_foto(lap.id)) == 3


def test_tanpa_foto_ditolak(pelapor):
    """Field foto wajib (kontrak) → FastAPI membalas 422 sebelum masuk logika."""
    r = _kirim(pelapor, berkas=[])
    assert r.status_code in (400, 422)


def test_empat_foto_ditolak(pelapor):
    r = _kirim(pelapor, jumlah_foto=4)
    assert r.status_code == 400
    assert "3 foto" in r.json()["detail"]


def test_file_bukan_gambar_ditolak(pelapor):
    r = _kirim(pelapor, berkas=[("foto", ("a.jpg", b"ini bukan gambar", "image/jpeg"))])
    assert r.status_code == 400


def test_foto_lebih_dari_10_mb_ditolak(pelapor):
    besar = _jpeg() + b"\x00" * (10 * 1024 * 1024)
    r = _kirim(pelapor, berkas=[("foto", ("besar.jpg", besar, "image/jpeg"))])
    assert r.status_code == 400
    assert "10 MB" in r.json()["detail"]


def test_sumber_lokasi_tidak_dikenal_ditolak(pelapor):
    r = _kirim(pelapor, sumber_lokasi="dukun")
    assert r.status_code == 400


def test_di_luar_jakarta_ditolak_dengan_arahan_kanal_resmi(pelapor):
    r = _kirim(pelapor, titik=TITIK["kota_tangerang"])
    assert r.status_code == 400
    assert "SP4N-LAPOR!" in r.json()["detail"]


def test_duplikat_dalam_25_m_dapat_tawaran_dukung(buat_klien):
    pertama = _kirim(buat_klien("pelapor", email="satu@uji.test"))
    assert pertama.status_code == 201
    kedua = _kirim(buat_klien("pelapor", email="dua@uji.test"))
    assert kedua.status_code == 409
    j = kedua.json()
    assert j["duplikat"][0]["nomor"] == pertama.json()["nomor"]
    assert j["duplikat"][0]["jarak_m"] <= 25
    assert j["duplikat"][0]["jumlah_dukungan"] == 0


def test_duplikat_boleh_diabaikan_pelapor_tetap_bisa_buat_baru(buat_klien):
    _kirim(buat_klien("pelapor", email="satu@uji.test"))
    r = _kirim(buat_klien("pelapor", email="dua@uji.test"), abaikan_duplikat="true")
    assert r.status_code == 201


def test_laporan_ke_11_dalam_satu_jam_kena_rate_limit(pelapor):
    for _ in range(10):
        assert _kirim(pelapor, abaikan_duplikat="true").status_code == 201
    r = _kirim(pelapor, abaikan_duplikat="true")
    assert r.status_code == 429


def test_tanpa_login_ditolak(klien):
    assert _kirim(klien).status_code == 401


def _paksa_keputusan(monkeypatch, keputusan: str, tingkat: str | None):
    hasil = HasilFoto(kelas=KELAS_RUSAK, confidence=0.95, kemiripan=0.9, keputusan=FOTO_TERIMA, alasan="uji")
    monkeypatch.setattr("jalanku.modules.pelaporan.layanan.periksa_foto", lambda data: hasil)
    monkeypatch.setattr(
        "jalanku.modules.pelaporan.layanan.putuskan",
        lambda daftar: KeputusanAI(keputusan=keputusan, tingkat=tingkat, hasil_foto=list(daftar), versi_model="uji-1"),
    )


def test_keputusan_ai_terverifikasi_langsung_belum_dikerjakan(pelapor, monkeypatch):
    _paksa_keputusan(monkeypatch, KEPUTUSAN_TERVERIFIKASI, KELAS_RUSAK)
    r = _kirim(pelapor, jumlah_foto=2)
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "belum_dikerjakan"
    assert r.json()["tingkat"] == "rusak"
    lap = ambil_laporan(r.json()["nomor"])
    assert lap.versi_model == "uji-1"
    fotos = daftar_foto(lap.id)
    assert [f.hasil_ai["kelas"] for f in fotos] == ["rusak", "rusak"]  # satu hasil per foto, urutan sama


def test_keputusan_ai_ditolak_menjadi_ditolak(pelapor, monkeypatch):
    _paksa_keputusan(monkeypatch, KEPUTUSAN_DITOLAK, None)
    r = _kirim(pelapor)
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "ditolak"
