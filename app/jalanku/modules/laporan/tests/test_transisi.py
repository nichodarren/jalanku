"""Siklus status BR-03 dan syarat tiap transisi (TS-02).

Teknik: state transition (matriks lengkap status × status × pelaku), decision table (syarat per
transisi), boundary value (jumlah foto 0/1/3/4, keterangan 280/281, alasan 4/5 karakter).
Aturan syarat mengikuti MVP v2 (``jalanku-v0/app/jalanku/reports.py``: setujui, tolak, gabung,
banding, ubah_status_petugas).
"""

from __future__ import annotations

import io
import itertools

import pytest
from PIL import Image

from conftest import TITIK
from jalanku.core import Konflik, TidakValid, muat_ulang_pengaturan, transaksi
from jalanku.modules import laporan as L


def _foto(warna=(90, 90, 90)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 48), warna).save(buf, "JPEG")
    return buf.getvalue()


def _buat(keputusan="perlu_admin", *, foto=None, keterangan="") -> L.Laporan:
    lat, lon = TITIK["monas"]
    return L.buat_laporan(
        L.LaporanBaru(
            pelapor_id=1,
            lat=lat,
            lon=lon,
            sumber_lokasi="gps",
            kota="Jakarta Pusat",
            kecamatan="Gambir",
            instansi_id="SUDIN_JP",
            foto=[_foto()] if foto is None else foto,
            keputusan_ai=keputusan,
            tingkat=L.TINGKAT_RUSAK if keputusan == "terverifikasi" else None,
            keterangan=keterangan,
        )
    )


def _dalam_status(status: str) -> L.Laporan:
    """Laporan baru yang sudah berada di ``status`` lewat jalur sah BR-03."""
    if status == L.STATUS_MENUNGGU:
        return _buat()
    if status == L.STATUS_DITOLAK:
        return _buat("ditolak")
    if status == L.STATUS_BELUM:
        return _buat("terverifikasi")
    if status == L.STATUS_SEDANG:
        return L.ubah_status(_buat("terverifikasi").nomor, L.STATUS_SEDANG, L.PELAKU_PETUGAS)
    if status == L.STATUS_SELESAI:
        return L.ubah_status(_buat("terverifikasi").nomor, L.STATUS_SELESAI, L.PELAKU_PETUGAS, foto_sesudah=_foto())
    if status == L.STATUS_DIGABUNG:
        induk = _buat("terverifikasi")
        return L.ubah_status(_buat().nomor, L.STATUS_DIGABUNG, L.PELAKU_ADMIN, induk_nomor=induk.nomor)
    raise AssertionError(status)


def _argumen_sah(ke: str) -> dict:
    """Argumen yang memenuhi semua syarat transisi ke ``ke``, supaya yang diuji hanya aturan pelaku."""
    arg: dict = {"catatan": "Bukan jalan, foto halaman rumah"}
    if ke == L.STATUS_BELUM:
        arg["tingkat"] = L.TINGKAT_KURANG_BAIK
    if ke == L.STATUS_SELESAI:
        arg["foto_sesudah"] = _foto((200, 200, 200))
    if ke == L.STATUS_DIGABUNG:
        arg["induk_nomor"] = _buat("terverifikasi").nomor
    return arg


# Spesifikasi BR-03 (SRS), ditulis ulang di sini secara independen dari implementasi.
SAH = {
    (L.STATUS_DITOLAK, L.STATUS_MENUNGGU, L.PELAKU_PELAPOR),
    (L.STATUS_MENUNGGU, L.STATUS_BELUM, L.PELAKU_ADMIN),
    (L.STATUS_MENUNGGU, L.STATUS_DITOLAK, L.PELAKU_ADMIN),
    (L.STATUS_MENUNGGU, L.STATUS_DIGABUNG, L.PELAKU_ADMIN),
    (L.STATUS_BELUM, L.STATUS_DIGABUNG, L.PELAKU_ADMIN),
    (L.STATUS_BELUM, L.STATUS_SEDANG, L.PELAKU_PETUGAS),
    (L.STATUS_BELUM, L.STATUS_SELESAI, L.PELAKU_PETUGAS),
    (L.STATUS_SEDANG, L.STATUS_SELESAI, L.PELAKU_PETUGAS),
}
SEMUA_STATUS = [
    L.STATUS_MENUNGGU,
    L.STATUS_BELUM,
    L.STATUS_SEDANG,
    L.STATUS_SELESAI,
    L.STATUS_DITOLAK,
    L.STATUS_DIGABUNG,
]
SEMUA_PELAKU = [L.PELAKU_AI, L.PELAKU_ADMIN, L.PELAKU_PETUGAS, L.PELAKU_PELAPOR, L.PELAKU_SISTEM]


# --- Matriks state transition ------------------------------------------------------------------


@pytest.mark.parametrize(("dari", "ke", "pelaku"), list(itertools.product(SEMUA_STATUS, SEMUA_STATUS, SEMUA_PELAKU)))
def test_matriks_transisi_br03(dari, ke, pelaku):
    lap = _dalam_status(dari)
    assert lap.status == dari
    arg = _argumen_sah(ke)
    if (dari, ke, pelaku) in SAH:
        hasil = L.ubah_status(lap.nomor, ke, pelaku, **arg)
        assert hasil.status == ke
        assert L.timeline(lap.id)[-1].pelaku == pelaku
    else:
        with pytest.raises(Konflik):
            L.ubah_status(lap.nomor, ke, pelaku, **arg)
        assert L.ambil_laporan(lap.nomor).status == dari  # tidak ada perubahan setengah jalan


def test_spesifikasi_sama_dengan_tabel_transisi():
    """Penjaga: tabel di kode tidak boleh diam-diam menyimpang dari spesifikasi BR-03."""
    from jalanku.modules.laporan.layanan import TRANSISI

    assert {(d, k, p) for (d, k), ps in TRANSISI.items() for p in ps} == SAH


# --- Verifikasi Admin: tingkat wajib -----------------------------------------------------------


@pytest.mark.parametrize("tingkat", [None, "", "baik", "parah"])
def test_verifikasi_admin_tanpa_tingkat_sah_ditolak(tingkat):
    lap = _buat()
    with pytest.raises(TidakValid, match="tingkat"):
        L.ubah_status(lap.nomor, L.STATUS_BELUM, L.PELAKU_ADMIN, tingkat=tingkat)
    assert L.ambil_laporan(lap.nomor).status == L.STATUS_MENUNGGU


@pytest.mark.parametrize("tingkat", [L.TINGKAT_KURANG_BAIK, L.TINGKAT_RUSAK])
def test_verifikasi_admin_menyimpan_tingkat_dan_pemeriksa(tingkat):
    hasil = L.ubah_status(_buat().nomor, L.STATUS_BELUM, L.PELAKU_ADMIN, tingkat=tingkat)
    assert hasil.tingkat == tingkat
    assert hasil.diperiksa_oleh == L.PELAKU_ADMIN and hasil.diverifikasi_pada is not None


# --- Penolakan Admin: alasan wajib (boundary 4/5 karakter) --------------------------------------


@pytest.mark.parametrize("alasan", ["", "     ", "abcd", "  abcd  "])
def test_tolak_tanpa_alasan_cukup_ditolak(alasan):
    lap = _buat()
    with pytest.raises(TidakValid, match="Alasan"):
        L.ubah_status(lap.nomor, L.STATUS_DITOLAK, L.PELAKU_ADMIN, catatan=alasan)
    assert L.ambil_laporan(lap.nomor).status == L.STATUS_MENUNGGU


def test_tolak_dengan_alasan_5_karakter_diterima_dan_tercatat_rapi():
    lap = _buat()
    hasil = L.ubah_status(lap.nomor, L.STATUS_DITOLAK, L.PELAKU_ADMIN, catatan="  buram  ")
    assert hasil.status == L.STATUS_DITOLAK and hasil.diperiksa_oleh == L.PELAKU_ADMIN
    assert L.timeline(lap.id)[-1].catatan == "buram"


# --- Banding: hanya untuk penolakan AI, sekali ----------------------------------------------------


def test_banding_penolakan_ai_sekali_saja():
    lap = _buat("ditolak")
    hasil = L.ubah_status(lap.nomor, L.STATUS_MENUNGGU, L.PELAKU_PELAPOR)
    assert hasil.status == L.STATUS_MENUNGGU and hasil.banding_pada is not None
    L.ubah_status(lap.nomor, L.STATUS_DITOLAK, L.PELAKU_ADMIN, catatan="Tetap bukan jalan rusak")
    with pytest.raises(Konflik, match="sekali"):
        L.ubah_status(lap.nomor, L.STATUS_MENUNGGU, L.PELAKU_PELAPOR)


def test_banding_yang_sudah_tercatat_tidak_bisa_diulang_walau_pemeriksa_ai():
    """Pertahanan berlapis: ``banding_pada`` saja sudah cukup untuk menolak banding kedua."""
    lap = _buat("ditolak")
    with transaksi() as kon:
        kon.execute("UPDATE laporan SET banding_pada = '2026-11-19T10:00:00+07:00' WHERE id = ?", (lap.id,))
    with pytest.raises(Konflik, match="sekali"):
        L.ubah_status(lap.nomor, L.STATUS_MENUNGGU, L.PELAKU_PELAPOR)


def test_banding_atas_penolakan_admin_tidak_boleh():
    lap = _buat()
    L.ubah_status(lap.nomor, L.STATUS_DITOLAK, L.PELAKU_ADMIN, catatan="Foto bukan jalan")
    with pytest.raises(Konflik, match="ditolak otomatis oleh AI"):
        L.ubah_status(lap.nomor, L.STATUS_MENUNGGU, L.PELAKU_PELAPOR)
    assert L.ambil_laporan(lap.nomor).status == L.STATUS_DITOLAK


# --- Gabung: induk wajib, bukan diri sendiri, masih aktif ---------------------------------------


def test_gabung_menyimpan_induk():
    induk = _buat("terverifikasi")
    hasil = L.ubah_status(_buat().nomor, L.STATUS_DIGABUNG, L.PELAKU_ADMIN, induk_nomor=induk.nomor)
    assert hasil.induk_id == induk.id


@pytest.mark.parametrize(("induk", "pesan"), [(None, "induk"), ("", "induk"), ("JK-99999", "tidak ditemukan")])
def test_gabung_tanpa_induk_valid_ditolak(induk, pesan):
    lap = _buat()
    with pytest.raises(TidakValid, match=pesan):
        L.ubah_status(lap.nomor, L.STATUS_DIGABUNG, L.PELAKU_ADMIN, induk_nomor=induk)


def test_gabung_ke_diri_sendiri_ditolak():
    lap = _buat()
    with pytest.raises(TidakValid, match="dirinya sendiri"):
        L.ubah_status(lap.nomor, L.STATUS_DIGABUNG, L.PELAKU_ADMIN, induk_nomor=lap.nomor)


@pytest.mark.parametrize("status_induk", [L.STATUS_SELESAI, L.STATUS_DITOLAK, L.STATUS_DIGABUNG])
def test_gabung_ke_induk_tidak_aktif_ditolak(status_induk):
    induk = _dalam_status(status_induk)
    lap = _buat()
    with pytest.raises(Konflik, match="aktif"):
        L.ubah_status(lap.nomor, L.STATUS_DIGABUNG, L.PELAKU_ADMIN, induk_nomor=induk.nomor)
    assert L.ambil_laporan(lap.nomor).status == L.STATUS_MENUNGGU


@pytest.mark.parametrize("status_induk", [L.STATUS_MENUNGGU, L.STATUS_BELUM, L.STATUS_SEDANG])
def test_gabung_ke_induk_aktif_diterima(status_induk):
    induk = _dalam_status(status_induk)
    hasil = L.ubah_status(_buat().nomor, L.STATUS_DIGABUNG, L.PELAKU_ADMIN, induk_nomor=induk.nomor)
    assert hasil.status == L.STATUS_DIGABUNG


# --- Selesai: foto sesudah wajib bila konfigurasi aktif -----------------------------------------


@pytest.mark.parametrize("dari", [L.STATUS_BELUM, L.STATUS_SEDANG])
def test_selesai_tanpa_foto_sesudah_ditolak(dari):
    lap = _dalam_status(dari)
    with pytest.raises(TidakValid, match="foto setelah perbaikan"):
        L.ubah_status(lap.nomor, L.STATUS_SELESAI, L.PELAKU_PETUGAS)
    assert L.ambil_laporan(lap.nomor).status == dari


def test_selesai_tanpa_foto_boleh_bila_konfigurasi_mematikan(monkeypatch):
    monkeypatch.setenv("JALANKU_WAJIB_FOTO_SELESAI", "0")
    muat_ulang_pengaturan()
    hasil = L.ubah_status(_dalam_status(L.STATUS_SEDANG).nomor, L.STATUS_SELESAI, L.PELAKU_PETUGAS)
    assert hasil.status == L.STATUS_SELESAI and hasil.selesai_pada is not None


# --- Boundary saat membuat laporan --------------------------------------------------------------


@pytest.mark.parametrize(("jumlah", "boleh"), [(0, False), (1, True), (3, True), (4, False)])
def test_jumlah_foto_1_sampai_3(jumlah, boleh):
    foto = [_foto((i * 40, 90, 90)) for i in range(jumlah)]
    if boleh:
        assert _buat(foto=foto).nomor.startswith("JK-")
    else:
        with pytest.raises(TidakValid, match="1 sampai 3 foto"):
            _buat(foto=foto)


@pytest.mark.parametrize(("panjang", "boleh"), [(0, True), (280, True), (281, False)])
def test_keterangan_maksimal_280_karakter(panjang, boleh):
    teks = "a" * panjang
    if boleh:
        assert _buat(keterangan=teks).keterangan == teks  # disimpan utuh, tidak dipotong
    else:
        with pytest.raises(TidakValid, match="280"):
            _buat(keterangan=teks)
