"""Integrasi GET /api/peta (US-15 peta aktif, US-16 riwayat): status yang tampil, filter, tanpa identitas.

Diport dari jalanku-v0 tests/integration/test_api_laporan.py::test_peta_aktif_dan_filter dan
tests/acceptance/features/us09_us10_us27_peta.feature, disesuaikan ke kontrak (respons = list).
Data dibuat langsung di DB test sementara lewat antarmuka publik modul laporan.
"""

from __future__ import annotations

import io

import pytest
from PIL import Image

from conftest import TITIK
from jalanku.modules import laporan
from jalanku.modules.peta.skema import TitikPetaKeluaran

FIELD_KONTRAK = set(TitikPetaKeluaran.model_fields)


def _jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), (120, 120, 120)).save(buf, "JPEG")
    return buf.getvalue()


def _buat(
    status: str = laporan.STATUS_BELUM,
    tingkat: str = laporan.TINGKAT_RUSAK,
    titik: str = "monas",
    kota: str = "Jakarta Pusat",
    pelapor_id: int = 7,
    simulasi: bool = False,
) -> laporan.Laporan:
    """Buat laporan lalu bawa ke ``status`` lewat transisi BR-03 yang sah."""
    lat, lon = TITIK[titik]
    keputusan = {laporan.STATUS_MENUNGGU: "perlu_admin", laporan.STATUS_DITOLAK: "ditolak"}.get(status, "terverifikasi")
    lap = laporan.buat_laporan(
        laporan.LaporanBaru(
            pelapor_id=pelapor_id,
            lat=lat,
            lon=lon,
            sumber_lokasi="gps",
            kota=kota,
            kecamatan="Kecamatan Uji",
            instansi_id="SUDIN_JP",
            foto=[_jpeg()],
            keputusan_ai=keputusan,
            tingkat=tingkat if keputusan == "terverifikasi" else None,
            simulasi=simulasi,
        )
    )
    if status in (laporan.STATUS_SEDANG, laporan.STATUS_SELESAI):
        laporan.ubah_status(lap.nomor, laporan.STATUS_SEDANG, laporan.PELAKU_PETUGAS)
    if status == laporan.STATUS_SELESAI:
        laporan.ubah_status(lap.nomor, laporan.STATUS_SELESAI, laporan.PELAKU_PETUGAS, foto_sesudah=_jpeg())
    return laporan.ambil_laporan(lap.nomor)


def _nomor(klien, url: str) -> set[str]:
    r = klien.get(url)
    assert r.status_code == 200, r.text
    return {t["nomor"] for t in r.json()}


def test_peta_aktif_hanya_belum_dan_sedang_dikerjakan(klien):
    belum = _buat(laporan.STATUS_BELUM)
    sedang = _buat(laporan.STATUS_SEDANG)
    _buat(laporan.STATUS_MENUNGGU)
    _buat(laporan.STATUS_DITOLAK)
    _buat(laporan.STATUS_SELESAI)
    assert _nomor(klien, "/api/peta") == {belum.nomor, sedang.nomor}
    assert _nomor(klien, "/api/peta?mode=aktif") == {belum.nomor, sedang.nomor}


def test_peta_riwayat_hanya_selesai(klien):
    _buat(laporan.STATUS_BELUM)
    selesai = _buat(laporan.STATUS_SELESAI)
    assert _nomor(klien, "/api/peta?mode=riwayat") == {selesai.nomor}


def test_laporan_selesai_pindah_dari_aktif_ke_riwayat(klien):
    lap = _buat(laporan.STATUS_SEDANG)
    assert lap.nomor in _nomor(klien, "/api/peta")
    laporan.ubah_status(lap.nomor, laporan.STATUS_SELESAI, laporan.PELAKU_PETUGAS, foto_sesudah=_jpeg())
    assert lap.nomor not in _nomor(klien, "/api/peta")
    assert lap.nomor in _nomor(klien, "/api/peta?mode=riwayat")


def test_filter_kota_satu_dan_beberapa_nilai(klien):
    pusat = _buat(titik="monas", kota="Jakarta Pusat")
    barat = _buat(titik="grogol", kota="Jakarta Barat")
    timur = _buat(titik="jatinegara", kota="Jakarta Timur")
    assert _nomor(klien, "/api/peta?kota=Jakarta Barat") == {barat.nomor}
    assert _nomor(klien, "/api/peta?kota=Jakarta Barat,Jakarta Timur") == {barat.nomor, timur.nomor}
    assert pusat.nomor not in _nomor(klien, "/api/peta?kota=Jakarta Barat,Jakarta Timur")
    assert _nomor(klien, "/api/peta?kota=Kota Tangerang") == set()


def test_filter_tingkat_dan_gabungan_dengan_kota(klien):
    rusak = _buat(tingkat=laporan.TINGKAT_RUSAK, kota="Jakarta Pusat")
    kurang = _buat(tingkat=laporan.TINGKAT_KURANG_BAIK, kota="Jakarta Pusat")
    rusak_barat = _buat(tingkat=laporan.TINGKAT_RUSAK, titik="grogol", kota="Jakarta Barat")
    assert _nomor(klien, "/api/peta?tingkat=kurang_baik") == {kurang.nomor}
    assert _nomor(klien, "/api/peta?tingkat=rusak,kurang_baik") == {rusak.nomor, kurang.nomor, rusak_barat.nomor}
    assert _nomor(klien, "/api/peta?tingkat=rusak&kota=Jakarta Barat") == {rusak_barat.nomor}


def test_respons_hanya_field_kontrak_tanpa_identitas_pelapor(buat_klien, klien):
    pelapor = buat_klien("pelapor", email="siti.rahasia@uji.test")
    pelapor_id = pelapor.get("/api/akun/saya").json()["id"]
    _buat(pelapor_id=pelapor_id)
    r = klien.get("/api/peta")
    assert r.status_code == 200
    (titik,) = r.json()
    assert set(titik) == FIELD_KONTRAK
    assert "pelapor_id" not in titik
    assert "siti.rahasia" not in r.text


def test_isi_titik_dukungan_simulasi_dan_koordinat(klien):
    lap = _buat(simulasi=True)
    laporan.tambah_dukungan(lap.id, 101)
    laporan.tambah_dukungan(lap.id, 102)
    (titik,) = klien.get("/api/peta").json()
    assert titik["nomor"] == lap.nomor
    assert titik["status"] == laporan.STATUS_BELUM
    assert titik["tingkat"] == laporan.TINGKAT_RUSAK
    assert titik["kota"] == "Jakarta Pusat"
    assert titik["jumlah_dukungan"] == 2
    assert titik["simulasi"] is True
    assert titik["lat"] == pytest.approx(TITIK["monas"][0], abs=1e-6)
    assert titik["lon"] == pytest.approx(TITIK["monas"][1], abs=1e-6)


def test_peta_kosong_dan_mode_tidak_dikenal(klien):
    r = klien.get("/api/peta")
    assert r.status_code == 200 and r.json() == []
    assert klien.get("/api/peta?mode=semua").status_code == 422


def test_filter_dibatasi_sepuluh_nilai(klien):
    lap = _buat(kota="Jakarta Pusat")
    kota_palsu = ",".join(f"Kota {i}" for i in range(10))
    assert _nomor(klien, f"/api/peta?kota={kota_palsu},Jakarta Pusat") == set()
    assert lap.nomor in _nomor(klien, f"/api/peta?kota=Jakarta Pusat,{kota_palsu}")
