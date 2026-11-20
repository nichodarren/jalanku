"""Integrasi dashboard petugas: US-18 (lihat laporan wilayahnya) dan US-19 (ubah status + foto).

Diport dari jalanku-v0 tests/integration/test_api_penanganan.py
(test_petugas_hanya_bisa_mengubah_laporan_wilayahnya, test_petugas_tidak_melihat_laporan_belum_terverifikasi,
test_selesai_wajib_foto_lalu_pindah_ke_riwayat, test_foto_selesai_bisa_tidak_wajib_lewat_konfigurasi)
dan skenario backlog US-18/US-19. Data dibuat di DB test sementara lewat antarmuka publik modul laporan.
"""

from __future__ import annotations

import io

import pytest
from PIL import Image

from conftest import TITIK
from jalanku.core import muat_ulang_pengaturan
from jalanku.modules import laporan
from jalanku.modules.penanganan.skema import ItemPetugasKeluaran

URL = "/api/petugas/laporan"


def _jpeg(warna=(90, 90, 90)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 64), warna).save(buf, "JPEG")
    return buf.getvalue()


def _buat(titik: str, kota: str, instansi_id: str, status: str = laporan.STATUS_BELUM) -> laporan.Laporan:
    lat, lon = TITIK[titik]
    keputusan = {laporan.STATUS_MENUNGGU: "perlu_admin", laporan.STATUS_DITOLAK: "ditolak"}.get(status, "terverifikasi")
    lap = laporan.buat_laporan(
        laporan.LaporanBaru(
            pelapor_id=7,
            lat=lat,
            lon=lon,
            sumber_lokasi="gps",
            kota=kota,
            kecamatan="Kecamatan Uji",
            instansi_id=instansi_id,
            foto=[_jpeg()],
            keputusan_ai=keputusan,
            tingkat=laporan.TINGKAT_RUSAK if keputusan == "terverifikasi" else None,
        )
    )
    if status in (laporan.STATUS_SEDANG, laporan.STATUS_SELESAI):
        laporan.ubah_status(lap.nomor, laporan.STATUS_SEDANG, laporan.PELAKU_PETUGAS)
    if status == laporan.STATUS_SELESAI:
        laporan.ubah_status(lap.nomor, laporan.STATUS_SELESAI, laporan.PELAKU_PETUGAS, foto_sesudah=_jpeg())
    return laporan.ambil_laporan(lap.nomor)


@pytest.fixture
def monas():
    return _buat("monas", "Jakarta Pusat", "SUDIN_JP")


@pytest.fixture
def blok_m():
    return _buat("blok_m", "Jakarta Selatan", "SUDIN_JS")


@pytest.fixture
def petugas_js(buat_klien):
    return buat_klien("petugas", email="petugas.js@uji.test", instansi_id="SUDIN_JS")


@pytest.fixture
def petugas_jp(buat_klien):
    return buat_klien("petugas", email="petugas.jp@uji.test", instansi_id="SUDIN_JP")


def _nomor(klien, url: str = URL) -> set[str]:
    r = klien.get(url)
    assert r.status_code == 200, r.text
    return {x["nomor"] for x in r.json()}


def _ubah(klien, nomor: str, ke: str, foto: bytes | None = None, catatan: str = ""):
    berkas = {"foto": ("sesudah.jpg", foto, "image/jpeg")} if foto is not None else None
    return klien.post(f"{URL}/{nomor}/status", data={"ke": ke, "catatan": catatan}, files=berkas)


# --- US-18: melihat laporan wilayahnya -----------------------------------------------------------


def test_petugas_hanya_melihat_laporan_di_wilayahnya(petugas_js, monas, blok_m):
    """Given laporan terverifikasi di Monas dan Blok M, when petugas SUDIN_JS membuka dashboard,
    then hanya laporan di Blok M yang tampil."""
    assert _nomor(petugas_js) == {blok_m.nomor}


def test_petugas_dinas_melihat_semua_wilayah(buat_klien, monas, blok_m):
    dinas = buat_klien("petugas", email="petugas.dinas@uji.test", instansi_id="DINAS_BM")
    assert _nomor(dinas) == {monas.nomor, blok_m.nomor}


def test_laporan_menunggu_dan_ditolak_tidak_tampil_di_dashboard(petugas_jp, monas):
    _buat("monas", "Jakarta Pusat", "SUDIN_JP", laporan.STATUS_MENUNGGU)
    _buat("monas", "Jakarta Pusat", "SUDIN_JP", laporan.STATUS_DITOLAK)
    assert _nomor(petugas_jp) == {monas.nomor}


def test_filter_status_dan_isi_item_sesuai_kontrak(petugas_jp, monas):
    sedang = _buat("monas", "Jakarta Pusat", "SUDIN_JP", laporan.STATUS_SEDANG)
    selesai = _buat("monas", "Jakarta Pusat", "SUDIN_JP", laporan.STATUS_SELESAI)
    assert _nomor(petugas_jp) == {monas.nomor, sedang.nomor, selesai.nomor}
    assert _nomor(petugas_jp, f"{URL}?status=sedang_dikerjakan") == {sedang.nomor}
    item = next(x for x in petugas_jp.get(URL).json() if x["nomor"] == monas.nomor)
    assert set(item) == set(ItemPetugasKeluaran.model_fields)
    assert item["status"] == laporan.STATUS_BELUM and item["kota"] == "Jakarta Pusat"
    assert item["diverifikasi_pada"] is not None
    assert item["skor_prioritas"] is None  # US-20 belum aktif
    assert "pelapor_id" not in item


def test_parameter_tidak_dikenal_ditolak(petugas_jp):
    assert petugas_jp.get(f"{URL}?status=menunggu_verifikasi").status_code == 400
    assert petugas_jp.get(f"{URL}?urut=acak").status_code == 400
    assert petugas_jp.get(f"{URL}?urut=prioritas").status_code == 501  # US-20 (S3)


def test_bukan_petugas_tidak_bisa_membuka_dashboard(klien, buat_klien):
    assert klien.get(URL).status_code == 401
    assert buat_klien("pelapor").get(URL).status_code == 403
    assert buat_klien("admin").get(URL).status_code == 403


# --- US-19: mengubah status --------------------------------------------------------------------


def test_petugas_wilayah_lain_ditolak_dan_status_tetap(petugas_js, monas):
    """When petugas SUDIN_JS mengubah status laporan di Monas, then respons 403."""
    r = _ubah(petugas_js, monas.nomor, laporan.STATUS_SEDANG)
    assert r.status_code == 403
    assert laporan.ambil_laporan(monas.nomor).status == laporan.STATUS_BELUM


def test_wilayah_dicek_sebelum_foto(petugas_js, monas):
    # Petugas wilayah lain tidak boleh mendapat petunjuk apa pun dari validasi foto.
    assert _ubah(petugas_js, monas.nomor, laporan.STATUS_SELESAI).status_code == 403


def test_selesai_tanpa_foto_ditolak_dan_status_tetap(petugas_jp):
    """When petugas SUDIN_JP menandai laporan di Monas selesai tanpa foto,
    then status tidak berubah dan muncul "Lampirkan foto setelah perbaikan"."""
    lap = _buat("monas", "Jakarta Pusat", "SUDIN_JP", laporan.STATUS_SEDANG)
    r = _ubah(petugas_jp, lap.nomor, laporan.STATUS_SELESAI)
    assert r.status_code == 400
    assert "Lampirkan foto setelah perbaikan" in r.json()["detail"]
    assert laporan.ambil_laporan(lap.nomor).status == laporan.STATUS_SEDANG


def test_alur_lengkap_sampai_pindah_ke_peta_riwayat(petugas_jp, klien, monas):
    """US-16: laporan Sedang Dikerjakan yang ditandai Selesai dengan foto pindah dari peta aktif ke riwayat."""
    r = _ubah(petugas_jp, monas.nomor, laporan.STATUS_SEDANG, catatan="Tim menuju lokasi")
    assert r.status_code == 200, r.text
    assert r.json() == {"nomor": monas.nomor, "status": laporan.STATUS_SEDANG, "verifikasi_foto": None}

    r = _ubah(petugas_jp, monas.nomor, laporan.STATUS_SELESAI, foto=_jpeg((40, 40, 40)))
    assert r.status_code == 200, r.text
    assert r.json()["status"] == laporan.STATUS_SELESAI

    jenis = [f.jenis for f in laporan.daftar_foto(laporan.ambil_laporan(monas.nomor).id)]
    assert jenis.count("sesudah") == 1
    aktif = {t["nomor"] for t in klien.get("/api/peta").json()}
    riwayat = {t["nomor"] for t in klien.get("/api/peta?mode=riwayat").json()}
    assert monas.nomor not in aktif and monas.nomor in riwayat


def test_belum_dikerjakan_boleh_langsung_selesai_dengan_foto(petugas_jp, monas):
    # BR-03: belum_dikerjakan -> selesai oleh petugas wilayahnya, wajib foto.
    r = _ubah(petugas_jp, monas.nomor, laporan.STATUS_SELESAI, foto=_jpeg())
    assert r.status_code == 200, r.text
    assert laporan.ambil_laporan(monas.nomor).status == laporan.STATUS_SELESAI


def test_laporan_selesai_tidak_bisa_dibuka_lagi(petugas_jp):
    lap = _buat("monas", "Jakarta Pusat", "SUDIN_JP", laporan.STATUS_SELESAI)
    assert _ubah(petugas_jp, lap.nomor, laporan.STATUS_SEDANG).status_code == 409
    assert laporan.ambil_laporan(lap.nomor).status == laporan.STATUS_SELESAI


def test_status_tujuan_tidak_dikenal_ditolak(petugas_jp, monas):
    for ke in ("ditolak", "belum_dikerjakan", "apa saja"):
        assert _ubah(petugas_jp, monas.nomor, ke).status_code == 400, ke


def test_laporan_tidak_ada_404(petugas_jp):
    assert _ubah(petugas_jp, "JK-99999", laporan.STATUS_SEDANG).status_code == 404


def test_foto_bukan_gambar_ditolak(petugas_jp):
    lap = _buat("monas", "Jakarta Pusat", "SUDIN_JP", laporan.STATUS_SEDANG)
    r = _ubah(petugas_jp, lap.nomor, laporan.STATUS_SELESAI, foto=b"%PDF-1.4 bukan foto")
    assert r.status_code == 400
    assert laporan.ambil_laporan(lap.nomor).status == laporan.STATUS_SEDANG


def test_foto_selesai_boleh_tidak_wajib_lewat_konfigurasi(monkeypatch, petugas_jp):
    monkeypatch.setenv("JALANKU_WAJIB_FOTO_SELESAI", "0")
    muat_ulang_pengaturan()
    lap = _buat("monas", "Jakarta Pusat", "SUDIN_JP", laporan.STATUS_SEDANG)
    assert _ubah(petugas_jp, lap.nomor, laporan.STATUS_SELESAI).status_code == 200
    assert laporan.ambil_laporan(lap.nomor).status == laporan.STATUS_SELESAI
