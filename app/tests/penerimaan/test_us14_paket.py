"""US-14 Ambil paket penerusan ke kanal resmi (pemilik M5). Skenario penerimaan lewat API (issue #48)."""

from __future__ import annotations

import json

from conftest import TITIK, foto_bytes
from jalanku.core import pengaturan
from jalanku.modules import laporan as L
from jalanku.modules.wilayah import ambil_instansi

NAMA = "Budi Santoso Simulasi"
EMAIL = "budi.pelapor@uji.test"


def _laporan_terverifikasi(buat_klien) -> L.Laporan:
    """Laporan SIMULASI terverifikasi AI milik pelapor bernama ``NAMA`` dengan email ``EMAIL``."""
    warga = buat_klien()
    assert warga.post("/api/dev/masuk", json={"email": EMAIL, "peran": "pelapor", "nama": NAMA}).status_code == 200
    lat, lon = TITIK["monas"]
    return L.buat_laporan(
        L.LaporanBaru(
            pelapor_id=warga.get("/api/akun/saya").json()["id"],
            lat=lat,
            lon=lon,
            sumber_lokasi="gps",
            kota="Jakarta Pusat",
            kecamatan="Gambir",
            instansi_id="SUDIN_JP",
            foto=[foto_bytes(), foto_bytes()],
            keputusan_ai="terverifikasi",
            tingkat=L.TINGKAT_RUSAK,
        )
    )


def test_us14_paket_memuat_data_penerusan(buat_klien):
    """Given laporan SIMULASI terverifikasi memiliki foto dan instansi tujuan / When Admin mengambil
    paket / Then paket memuat nomor, instansi, kanal resmi, koordinat, tautan foto, dan tautan
    halaman laporan."""
    lap = _laporan_terverifikasi(buat_klien)
    instansi = ambil_instansi("SUDIN_JP")
    dasar = pengaturan().url_dasar

    r = buat_klien("admin").get(f"/api/admin/laporan/{lap.nomor}/paket")

    assert r.status_code == 200
    paket = r.json()
    assert paket["nomor"] == lap.nomor
    assert paket["instansi_id"] == instansi.id
    assert (paket["kanal_nama"], paket["kanal_url"]) == (instansi.kanal_nama, instansi.kanal_url)
    assert instansi.nama in paket["teks"]
    assert f"{lap.lat:.6f}, {lap.lon:.6f}" in paket["teks"]
    assert paket["teks"].count(f"{dasar}/api/foto/") == 2
    assert f"{dasar}/#/laporan/{lap.nomor}" in paket["teks"]


def test_us14_paket_tanpa_nama_dan_email_pelapor(buat_klien):
    """Given pelapor SIMULASI memiliki nama dan email yang diketahui dalam test / When respons paket
    diperiksa / Then nama dan email tersebut tidak muncul di bagian mana pun."""
    lap = _laporan_terverifikasi(buat_klien)

    r = buat_klien("admin").get(f"/api/admin/laporan/{lap.nomor}/paket")

    assert r.status_code == 200
    mentah = json.dumps(r.json(), ensure_ascii=False).lower()
    assert NAMA.lower() not in mentah
    assert EMAIL.lower() not in mentah
