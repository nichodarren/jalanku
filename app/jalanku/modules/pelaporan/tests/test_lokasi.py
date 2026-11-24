"""Test integrasi POST /api/lokasi (US-04 pratinjau lokasi, US-09 duplikat 25 m, BR-01, BR-02)."""

from __future__ import annotations

import io

from PIL import Image

from conftest import TITIK

MONAS = TITIK["monas"]


def _jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (120, 120, 120)).save(buf, "JPEG")
    return buf.getvalue()


def _lapor(klien, lat: float, lon: float):
    r = klien.post(
        "/api/laporan",
        data={"lat": str(lat), "lon": str(lon), "sumber_lokasi": "manual", "abaikan_duplikat": "true"},
        files=[("foto", ("a.jpg", _jpeg(), "image/jpeg"))],
    )
    assert r.status_code == 201, r.text
    return r.json()["nomor"]


def _lokasi(klien, lat: float, lon: float, akurasi_gps: float | None = None):
    isi = {"lat": lat, "lon": lon}
    if akurasi_gps is not None:
        isi["akurasi_gps"] = akurasi_gps
    return klien.post("/api/lokasi", json=isi)


def test_di_dalam_jakarta_mengembalikan_wilayah_dan_instansi(klien):
    r = _lokasi(klien, *MONAS)
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["di_dalam"] is True
    assert j["kota"] and j["kecamatan"]
    assert j["instansi"]["id"].startswith("SUDIN_")
    assert j["instansi"]["kanal_url"]
    assert j["kanal_luar"] is None
    assert j["duplikat"] == []


def test_di_luar_jakarta_mengarahkan_ke_kanal_resmi(klien):
    j = _lokasi(klien, *TITIK["kota_tangerang"]).json()
    assert j["di_dalam"] is False
    assert j["instansi"] is None
    assert j["kanal_luar"]["nama"] == "SP4N-LAPOR!"
    assert j["kanal_luar"]["url"].startswith("https://")
    assert j["duplikat"] == []


def test_akurasi_gps_50_m_tidak_perlu_konfirmasi_pin(klien):
    assert _lokasi(klien, *MONAS, akurasi_gps=50).json()["perlu_konfirmasi_pin"] is False


def test_akurasi_gps_lebih_dari_50_m_perlu_konfirmasi_pin(klien):
    assert _lokasi(klien, *MONAS, akurasi_gps=50.1).json()["perlu_konfirmasi_pin"] is True


def test_tanpa_akurasi_tidak_perlu_konfirmasi_pin(klien):
    """Titik dari EXIF / pin manual tidak punya akurasi GPS."""
    assert _lokasi(klien, *MONAS).json()["perlu_konfirmasi_pin"] is False


def test_koordinat_di_luar_rentang_ditolak(klien):
    assert _lokasi(klien, 91, 106.8).status_code == 422


def test_laporan_aktif_24_m_ditawarkan_sebagai_duplikat(buat_klien, klien):
    nomor = _lapor(buat_klien("pelapor"), *MONAS)
    j = _lokasi(klien, MONAS[0] + 0.000215, MONAS[1]).json()  # ±23,9 m
    assert [d["nomor"] for d in j["duplikat"]] == [nomor]
    assert 20 < j["duplikat"][0]["jarak_m"] <= 25
    assert j["duplikat"][0]["jumlah_dukungan"] == 0


def test_laporan_aktif_26_m_bukan_duplikat(buat_klien, klien):
    _lapor(buat_klien("pelapor"), *MONAS)
    assert _lokasi(klien, MONAS[0] + 0.000235, MONAS[1]).json()["duplikat"] == []  # ±26,1 m


def test_duplikat_tidak_membocorkan_identitas_pelapor(buat_klien, klien):
    _lapor(buat_klien("pelapor", email="rahasia@uji.test"), *MONAS)
    teks = _lokasi(klien, *MONAS).text
    assert "rahasia" not in teks
    assert "pelapor_id" not in teks
