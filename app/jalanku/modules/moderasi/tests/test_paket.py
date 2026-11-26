"""US-14 paket penerusan: ringkasan untuk kanal resmi TANPA identitas pelapor (NFR-PRI-01)."""

from __future__ import annotations

import json

from fastapi.testclient import TestClient

from jalanku.core import pengaturan
from jalanku.modules.laporan import STATUS_BELUM, STATUS_DITOLAK, daftar_foto
from jalanku.modules.wilayah import ambil_instansi

NAMA_PELAPOR = "Sinta Rahmawati Simulasi"
EMAIL_PELAPOR = "sinta.rahasia@uji.test"


def _pelapor_dikenal(buat_klien) -> tuple[TestClient, int]:
    klien = buat_klien()
    r = klien.post("/api/dev/masuk", json={"email": EMAIL_PELAPOR, "peran": "pelapor", "nama": NAMA_PELAPOR})
    assert r.status_code == 200, r.text
    saya = klien.get("/api/akun/saya").json()
    assert saya["nama"] == NAMA_PELAPOR
    return klien, saya["id"]


def _paket(klien, nomor: str):
    return klien.get(f"/api/admin/laporan/{nomor}/paket")


def test_paket_memuat_instansi_kanal_koordinat_foto_dan_tautan(buat_klien, bikin_laporan):
    _, pid = _pelapor_dikenal(buat_klien)
    lap = bikin_laporan(pelapor_id=pid, status_awal=STATUS_BELUM, keterangan="Lubang dalam di lajur kiri")
    instansi = ambil_instansi("SUDIN_JP")
    dasar = pengaturan().url_dasar

    r = _paket(buat_klien("admin"), lap.nomor)

    assert r.status_code == 200
    paket = r.json()
    assert paket["nomor"] == lap.nomor
    assert paket["instansi_id"] == "SUDIN_JP"
    assert paket["kanal_nama"] == instansi.kanal_nama
    assert paket["kanal_url"] == instansi.kanal_url
    teks = paket["teks"]
    assert lap.nomor in teks
    assert instansi.nama in teks
    assert f"{lap.lat:.6f}, {lap.lon:.6f}" in teks
    assert "Rusak" in teks
    assert "Lubang dalam di lajur kiri" in teks
    for foto in daftar_foto(lap.id):
        assert f"{dasar}/api/foto/{foto.id}" in teks
    assert f"{dasar}/#/laporan/{lap.nomor}" in teks


def test_paket_tidak_memuat_identitas_pelapor(buat_klien, bikin_laporan):
    _, pid = _pelapor_dikenal(buat_klien)
    lap = bikin_laporan(pelapor_id=pid, status_awal=STATUS_BELUM)

    r = _paket(buat_klien("admin"), lap.nomor)

    assert r.status_code == 200
    mentah = json.dumps(r.json(), ensure_ascii=False).lower()
    assert NAMA_PELAPOR.lower() not in mentah
    assert "sinta" not in mentah
    assert EMAIL_PELAPOR.lower() not in mentah
    assert "sinta.rahasia" not in mentah
    assert "pelapor_id" not in mentah


def test_paket_hanya_untuk_laporan_terverifikasi(buat_klien, bikin_laporan):
    admin = buat_klien("admin")
    menunggu = bikin_laporan()
    ditolak = bikin_laporan(keputusan_ai=STATUS_DITOLAK)

    assert _paket(admin, menunggu.nomor).status_code == 409
    assert _paket(admin, ditolak.nomor).status_code == 409
    assert _paket(admin, "JK-99999").status_code == 404


def test_otorisasi_paket(buat_klien, bikin_laporan):
    lap = bikin_laporan(status_awal=STATUS_BELUM)

    assert _paket(buat_klien(), lap.nomor).status_code == 401
    assert _paket(buat_klien("pelapor"), lap.nomor).status_code == 403
    assert _paket(buat_klien("petugas", instansi_id="SUDIN_JP"), lap.nomor).status_code == 403
