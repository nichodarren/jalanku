"""Perilaku domain laporan yang SUDAH dijamin sejak baseline (dipakai modul lain).

M1 menambah test untuk TODO(TS-02): foto tanpa EXIF, syarat transisi, visibilitas foto.
"""

from __future__ import annotations

import pytest

from conftest import TITIK, foto_bytes
from jalanku.core import Konflik, langganan
from jalanku.core.kejadian import terbitkan
from jalanku.modules import laporan
from jalanku.modules.akun import AkunDihapus


def _baru(keputusan="terverifikasi", tingkat="rusak", titik="monas", pelapor_id=1, **lain):
    lat, lon = TITIK[titik]
    return laporan.LaporanBaru(
        pelapor_id=pelapor_id,
        lat=lat,
        lon=lon,
        sumber_lokasi="gps",
        kota="Jakarta Pusat",
        kecamatan="Gambir",
        instansi_id="SUDIN_JP",
        foto=[foto_bytes()],
        keputusan_ai=keputusan,
        tingkat=tingkat if keputusan == "terverifikasi" else None,
        **lain,
    )


def test_nomor_berurutan_dan_status_awal_dari_keputusan_ai():
    a = laporan.buat_laporan(_baru())
    b = laporan.buat_laporan(_baru(keputusan="perlu_admin"))
    c = laporan.buat_laporan(_baru(keputusan="ditolak"))
    assert (a.nomor, b.nomor, c.nomor) == ("JK-00001", "JK-00002", "JK-00003")
    assert a.status == laporan.STATUS_BELUM and a.tingkat == "rusak" and a.diperiksa_oleh == "ai"
    assert b.status == laporan.STATUS_MENUNGGU and b.diperiksa_oleh is None
    assert c.status == laporan.STATUS_DITOLAK


def test_timeline_menyebut_ai():
    a = laporan.buat_laporan(_baru())
    entri = laporan.timeline(a.id)
    assert entri[0].pelaku == laporan.PELAKU_AI and "AI JalanKu" in entri[0].catatan


def test_transisi_di_luar_br03_ditolak():
    a = laporan.buat_laporan(_baru())
    with pytest.raises(Konflik):
        laporan.ubah_status(a.nomor, laporan.STATUS_SELESAI, laporan.PELAKU_ADMIN)  # admin tidak boleh menyelesaikan
    laporan.ubah_status(a.nomor, laporan.STATUS_SEDANG, laporan.PELAKU_PETUGAS)
    with pytest.raises(Konflik):
        laporan.ubah_status(a.nomor, laporan.STATUS_BELUM, laporan.PELAKU_PETUGAS)  # tidak bisa mundur


def test_status_berubah_diterbitkan():
    diterima = []
    langganan(laporan.StatusBerubah, diterima.append)
    a = laporan.buat_laporan(_baru())
    laporan.ubah_status(a.nomor, laporan.STATUS_SEDANG, laporan.PELAKU_PETUGAS)
    assert diterima and diterima[0].dari_status == "belum_dikerjakan" and diterima[0].ke_status == "sedang_dikerjakan"


def test_laporan_menunggu_tidak_terlihat_publik(buat_klien, klien):
    pelapor = buat_klien("pelapor")
    pid = pelapor.get("/api/akun/saya").json()["id"]
    lap = laporan.buat_laporan(_baru(keputusan="perlu_admin", pelapor_id=pid))
    assert klien.get(f"/api/laporan/{lap.nomor}").status_code == 404
    assert pelapor.get(f"/api/laporan/{lap.nomor}").status_code == 200
    assert buat_klien("admin").get(f"/api/laporan/{lap.nomor}").status_code == 200


def test_detail_publik_tanpa_identitas(klien):
    lap = laporan.buat_laporan(_baru())
    data = klien.get(f"/api/laporan/{lap.nomor}").json()
    assert "pelapor_id" not in data and "email" not in str(data)
    assert data["foto"][0]["hasil_ai"] is None  # hasil AI hanya untuk pemilik & admin


def test_satu_akun_satu_dukungan():
    lap = laporan.buat_laporan(_baru())
    assert laporan.tambah_dukungan(lap.id, 7) is True
    assert laporan.tambah_dukungan(lap.id, 7) is False
    assert laporan.jumlah_dukungan(lap.id) == 1


def test_cari_aktif_dekat_25_m():
    lap = laporan.buat_laporan(_baru())
    lat, lon = TITIK["monas"]
    dekat = laporan.cari_aktif_dekat(lat + 0.0001, lon, 25)  # ±11 m
    jauh = laporan.cari_aktif_dekat(lat + 0.001, lon, 25)  # ±111 m
    assert [d[0].nomor for d in dekat] == [lap.nomor] and jauh == []


def test_akun_dihapus_memutus_tautan_pelapor():
    laporan.pasang()
    lap = laporan.buat_laporan(_baru(pelapor_id=42))
    terbitkan(AkunDihapus(42))
    assert laporan.ambil_laporan(lap.nomor).pelapor_id is None


def test_hasil_ai_foto_sesudah_tampil_publik(klien):
    """US-31: bukti perbaikan (foto sesudah + penilaian AI) terbuka untuk publik."""
    lap = laporan.buat_laporan(_baru())
    laporan.ubah_status(lap.nomor, laporan.STATUS_SEDANG, laporan.PELAKU_PETUGAS)
    laporan.ubah_status(
        lap.nomor,
        laporan.STATUS_SELESAI,
        laporan.PELAKU_PETUGAS,
        foto_sesudah=foto_bytes(warna=(200, 200, 200)),
        hasil_ai_sesudah={"kelas": "baik", "keputusan": "terima", "alasan": "Jalan tampak sudah baik"},
    )
    foto = klien.get(f"/api/laporan/{lap.nomor}").json()["foto"]
    bukti = [f for f in foto if f["jenis"] == "bukti"][0]
    sesudah = [f for f in foto if f["jenis"] == "sesudah"][0]
    assert bukti["hasil_ai"] is None  # hasil AI foto laporan tetap privat
    assert sesudah["hasil_ai"]["kelas"] == "baik"


def test_jejak_audit_terdaftar_di_kontrak(klien):
    """US-32: endpoint jejak ada di kontrak OpenAPI. Perilakunya diuji di ``test_jejak.py``."""
    assert "/api/laporan/{nomor}/jejak" in klien.get("/api/openapi.json").json()["paths"]
