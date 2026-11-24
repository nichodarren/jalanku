"""US-25 / FR-NTF-01: kabar in-app untuk pelapor & pendukung saat status laporan berubah.

Pola diport dari jalanku-v0 ``reports.py`` ``_notifikasi`` (karya Yosua): penerima = pelapor + pendukung,
dikurangi yang mematikan notifikasi dan pelaku perubahan itu sendiri.
"""

from __future__ import annotations

import pytest

from conftest import TITIK, foto_bytes
from jalanku.core import koneksi, terbitkan
from jalanku.modules import laporan as L
from jalanku.modules import notifikasi
from jalanku.modules.akun import AkunDihapus
from jalanku.modules.notifikasi import layanan as N


@pytest.fixture(autouse=True)
def terpasang():
    notifikasi.pasang()


def _buat(pelapor_id: int | None = 1, keputusan: str = "terverifikasi") -> L.Laporan:
    lat, lon = TITIK["monas"]
    return L.buat_laporan(
        L.LaporanBaru(
            pelapor_id=pelapor_id,
            lat=lat,
            lon=lon,
            sumber_lokasi="gps",
            kota="Jakarta Pusat",
            kecamatan="Gambir",
            instansi_id="SUDIN_JP",
            foto=[foto_bytes()],
            keputusan_ai=keputusan,
            tingkat=L.TINGKAT_RUSAK if keputusan == "terverifikasi" else None,
        )
    )


def _pesan(pengguna_id: int) -> list[str]:
    return [k.pesan for k in N.daftar_kabar(pengguna_id)]


def test_pelapor_dan_pendukung_dapat_kabar_saat_dikerjakan():
    lap = _buat(pelapor_id=1)
    L.tambah_dukungan(lap.id, 2)
    L.tambah_dukungan(lap.id, 3)
    L.ubah_status(lap.nomor, L.STATUS_SEDANG, L.PELAKU_PETUGAS, pengguna_id=50)
    for pid in (1, 2, 3):
        kabar = N.daftar_kabar(pid)
        assert len(kabar) == 1
        assert kabar[0].nomor == lap.nomor
        assert "sedang dikerjakan" in kabar[0].pesan
        assert kabar[0].dibaca is False
    assert N.daftar_kabar(50) == []  # petugas bukan pelapor/pendukung


@pytest.mark.parametrize(
    "ke,kata",
    [
        (L.STATUS_SEDANG, "sedang dikerjakan"),
        (L.STATUS_SELESAI, "sudah diperbaiki"),
    ],
)
def test_pesan_sesuai_status(ke, kata):
    lap = _buat()
    if ke == L.STATUS_SELESAI:
        L.ubah_status(lap.nomor, L.STATUS_SEDANG, L.PELAKU_PETUGAS, pengguna_id=50)
        L.ubah_status(lap.nomor, ke, L.PELAKU_PETUGAS, pengguna_id=50, foto_sesudah=foto_bytes())
    else:
        L.ubah_status(lap.nomor, ke, L.PELAKU_PETUGAS, pengguna_id=50)
    assert kata in _pesan(1)[0]
    assert lap.nomor in _pesan(1)[0]


def test_verifikasi_dan_penolakan_admin_dikabarkan_ke_pelapor():
    a = _buat(keputusan="perlu_admin")
    L.ubah_status(a.nomor, L.STATUS_BELUM, L.PELAKU_ADMIN, pengguna_id=9, tingkat=L.TINGKAT_RUSAK)
    b = _buat(pelapor_id=4, keputusan="perlu_admin")
    L.ubah_status(b.nomor, L.STATUS_DITOLAK, L.PELAKU_ADMIN, pengguna_id=9, catatan="Bukan foto jalan")
    assert "diteruskan" in _pesan(1)[0]
    assert "ditolak" in _pesan(4)[0]


def test_pendukung_laporan_menunggu_tidak_dikabari_saat_ditolak_admin():
    """BR-06: laporan Ditolak hanya terlihat pelapornya dan Admin, jadi pendukung (boleh mendukung laporan
    yang masih menunggu, BR-02) tidak diberi kabar dengan tautan yang akan 404. Pelapor tetap dikabari."""
    lap = _buat(pelapor_id=1, keputusan="perlu_admin")
    L.tambah_dukungan(lap.id, 2)
    L.ubah_status(lap.nomor, L.STATUS_DITOLAK, L.PELAKU_ADMIN, pengguna_id=9, catatan="Bukan foto jalan")
    assert "ditolak" in _pesan(1)[0]
    assert N.daftar_kabar(2) == []


def test_pendukung_tetap_dikabari_saat_laporan_menunggu_diverifikasi_admin():
    """Setelah diverifikasi, laporan publik (BR-06), jadi pendukung boleh tahu."""
    lap = _buat(pelapor_id=1, keputusan="perlu_admin")
    L.tambah_dukungan(lap.id, 2)
    L.ubah_status(lap.nomor, L.STATUS_BELUM, L.PELAKU_ADMIN, pengguna_id=9, tingkat=L.TINGKAT_RUSAK)
    assert "diteruskan" in _pesan(1)[0]
    assert "diteruskan" in _pesan(2)[0]


def test_pelapor_tidak_dikabari_tindakannya_sendiri():
    # Banding diajukan pelapor sendiri: ia tidak perlu kabar "laporanmu menunggu verifikasi".
    lap = _buat(keputusan="ditolak")
    L.tambah_dukungan(lap.id, 2)
    L.ubah_status(lap.nomor, L.STATUS_MENUNGGU, L.PELAKU_PELAPOR, pengguna_id=1)
    assert _pesan(1) == []
    assert len(_pesan(2)) == 1


def test_tidak_ada_kabar_bila_dimatikan_dan_kembali_saat_dinyalakan():
    lap = _buat()
    N.atur_aktif(1, False)
    L.ubah_status(lap.nomor, L.STATUS_SEDANG, L.PELAKU_PETUGAS, pengguna_id=50)
    assert _pesan(1) == []
    N.atur_aktif(1, True)
    L.ubah_status(lap.nomor, L.STATUS_SELESAI, L.PELAKU_PETUGAS, pengguna_id=50, foto_sesudah=foto_bytes())
    assert len(_pesan(1)) == 1


def test_pengaturan_bawaan_aktif():
    assert N.aktif(123) is True
    N.atur_aktif(123, False)
    assert N.aktif(123) is False


def test_laporan_tanpa_pelapor_dan_pendukung_tidak_membuat_kabar():
    lap = _buat(pelapor_id=None)
    L.ubah_status(lap.nomor, L.STATUS_SEDANG, L.PELAKU_PETUGAS, pengguna_id=50)
    kon = koneksi()
    try:
        assert kon.execute("SELECT COUNT(*) FROM notifikasi_kabar").fetchone()[0] == 0
    finally:
        kon.close()


def test_daftar_terbaru_dulu_dan_tandai_dibaca_hanya_milik_sendiri():
    lap = _buat()
    L.ubah_status(lap.nomor, L.STATUS_SEDANG, L.PELAKU_PETUGAS, pengguna_id=50)
    L.ubah_status(lap.nomor, L.STATUS_SELESAI, L.PELAKU_PETUGAS, pengguna_id=50, foto_sesudah=foto_bytes())
    kabar = N.daftar_kabar(1)
    assert ["sudah diperbaiki" in kabar[0].pesan, "sedang dikerjakan" in kabar[1].pesan] == [True, True]
    assert N.tandai_dibaca(2, kabar[0].id) is None  # bukan milik pengguna 2
    assert N.daftar_kabar(1)[0].dibaca is False
    assert N.tandai_dibaca(1, kabar[0].id).dibaca is True
    assert [k.dibaca for k in N.daftar_kabar(1)] == [True, False]


def test_akun_dihapus_kabar_dan_pengaturannya_ikut_dihapus():
    lap = _buat()
    N.atur_aktif(1, False)
    N.atur_aktif(1, True)
    L.ubah_status(lap.nomor, L.STATUS_SEDANG, L.PELAKU_PETUGAS, pengguna_id=50)
    assert _pesan(1)
    terbitkan(AkunDihapus(pengguna_id=1))
    kon = koneksi()
    try:
        assert kon.execute("SELECT COUNT(*) FROM notifikasi_kabar WHERE pengguna_id = 1").fetchone()[0] == 0
        assert kon.execute("SELECT COUNT(*) FROM notifikasi_pengaturan WHERE pengguna_id = 1").fetchone()[0] == 0
    finally:
        kon.close()
