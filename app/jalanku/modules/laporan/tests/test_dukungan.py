"""Dukungan laporan: pindah ke induk saat digabung (BR-02/BR-03) dan hitung massal (CR #23).

Saat laporan B digabung ke A (kerusakan yang sama), warga yang mendukung B, dan pelapor B sendiri,
dihitung sebagai pendukung A. Dengan begitu jumlah dukungan di peta dan prioritas petugas tidak
berkurang karena penggabungan. Diport dari jalanku-v0 ``reports.py`` ``gabung`` (karya Yosua),
dengan satu perbaikan: pelapor A tidak pernah tercatat sebagai pendukung laporannya sendiri.
"""

from __future__ import annotations

import pytest

from conftest import TITIK, foto_bytes
from jalanku.core import Konflik, koneksi
from jalanku.core.waktu import atur_waktu
from jalanku.modules import laporan as L

PELAPOR_A, PELAPOR_B = 1, 2
WARGA_1, WARGA_2, WARGA_3 = 11, 12, 13


def _buat(pelapor_id: int | None, keputusan: str = "terverifikasi") -> L.Laporan:
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


def _gabung(b: L.Laporan, a: L.Laporan) -> L.Laporan:
    return L.ubah_status(b.nomor, L.STATUS_DIGABUNG, L.PELAKU_ADMIN, pengguna_id=99, induk_nomor=a.nomor)


def _waktu_dukungan(laporan_id: int) -> dict[int, str]:
    kon = koneksi()
    try:
        rows = kon.execute("SELECT pengguna_id, waktu FROM laporan_dukungan WHERE laporan_id = ?", (laporan_id,))
        return {r[0]: r[1] for r in rows}
    finally:
        kon.close()


# --- Pindah dukungan saat digabung -----------------------------------------------------------------


def test_pendukung_b_dan_pelapor_b_pindah_ke_induk():
    a, b = _buat(PELAPOR_A), _buat(PELAPOR_B)
    L.tambah_dukungan(a.id, WARGA_1)
    L.tambah_dukungan(b.id, WARGA_2)
    L.tambah_dukungan(b.id, WARGA_3)

    _gabung(b, a)

    assert sorted(L.pendukung(a.id)) == sorted([WARGA_1, WARGA_2, WARGA_3, PELAPOR_B])
    assert L.jumlah_dukungan(a.id) == 4
    assert L.pendukung(b.id) == []


def test_pendukung_ganda_dihitung_sekali():
    a, b = _buat(PELAPOR_A), _buat(PELAPOR_B)
    L.tambah_dukungan(a.id, WARGA_1)
    L.tambah_dukungan(b.id, WARGA_1)
    _gabung(b, a)
    assert sorted(L.pendukung(a.id)) == sorted([WARGA_1, PELAPOR_B])


def test_pelapor_induk_tidak_menjadi_pendukung_laporannya_sendiri():
    # Pelapor A pernah mendukung B; setelah B digabung ke A, ia tidak boleh "mendukung" laporannya sendiri.
    a, b = _buat(PELAPOR_A), _buat(PELAPOR_B)
    L.tambah_dukungan(b.id, PELAPOR_A)
    _gabung(b, a)
    assert PELAPOR_A not in L.pendukung(a.id)
    assert L.pendukung(a.id) == [PELAPOR_B]


def test_pelapor_yang_sama_tidak_mendukung_dirinya():
    a, b = _buat(PELAPOR_A), _buat(PELAPOR_A)
    _gabung(b, a)
    assert L.pendukung(a.id) == []


def test_pelapor_b_yang_akunnya_dihapus_tidak_ditambahkan():
    a, b = _buat(PELAPOR_A), _buat(None)
    L.tambah_dukungan(b.id, WARGA_1)
    _gabung(b, a)
    assert L.pendukung(a.id) == [WARGA_1]


def test_waktu_dukungan_asli_dipertahankan():
    a, b = _buat(PELAPOR_A), _buat(PELAPOR_B)
    L.tambah_dukungan(b.id, WARGA_2)
    sebelum = _waktu_dukungan(b.id)
    _gabung(b, a)
    sesudah = _waktu_dukungan(a.id)
    assert sesudah[WARGA_2] == sebelum[WARGA_2]
    assert sesudah[PELAPOR_B] == b.dibuat_pada  # pelapor B "mendukung" sejak ia melapor


def test_dukungan_lama_induk_tidak_tertimpa():
    a, b = _buat(PELAPOR_A), _buat(PELAPOR_B)
    atur_waktu("2026-11-01T08:00:00+07:00")
    L.tambah_dukungan(a.id, WARGA_1)
    atur_waktu("2026-11-05T08:00:00+07:00")
    L.tambah_dukungan(b.id, WARGA_1)
    atur_waktu(None)
    _gabung(b, a)
    assert _waktu_dukungan(a.id)[WARGA_1] == "2026-11-01T08:00:00+07:00"


def test_dari_menunggu_verifikasi_juga_pindah():
    a, b = _buat(PELAPOR_A), _buat(PELAPOR_B, keputusan="perlu_admin")
    assert b.status == L.STATUS_MENUNGGU
    L.tambah_dukungan(b.id, WARGA_2)
    _gabung(b, a)
    assert sorted(L.pendukung(a.id)) == sorted([WARGA_2, PELAPOR_B])


def test_transisi_lain_tidak_memindahkan_dukungan():
    a = _buat(PELAPOR_A)
    L.tambah_dukungan(a.id, WARGA_1)
    L.ubah_status(a.nomor, L.STATUS_SEDANG, L.PELAKU_PETUGAS, pengguna_id=50)
    assert L.pendukung(a.id) == [WARGA_1]


def test_gabung_gagal_tidak_mengubah_dukungan():
    a, b = _buat(PELAPOR_A), _buat(PELAPOR_B)
    L.tambah_dukungan(b.id, WARGA_2)
    L.ubah_status(a.nomor, L.STATUS_SEDANG, L.PELAKU_PETUGAS, pengguna_id=50)
    L.ubah_status(a.nomor, L.STATUS_SELESAI, L.PELAKU_PETUGAS, pengguna_id=50, foto_sesudah=foto_bytes())
    with pytest.raises(Konflik):
        _gabung(b, a)  # induk sudah selesai
    assert L.pendukung(b.id) == [WARGA_2]
    assert L.pendukung(a.id) == []


# --- jumlah_dukungan_massal (CR #23) ------------------------------------------------------------


def test_massal_kosong():
    assert L.jumlah_dukungan_massal([]) == {}


def test_massal_sama_dengan_satu_per_satu_dan_nol_untuk_tanpa_dukungan():
    a, b, c = _buat(PELAPOR_A), _buat(PELAPOR_B), _buat(PELAPOR_A)
    for w in (WARGA_1, WARGA_2, WARGA_3):
        L.tambah_dukungan(a.id, w)
    L.tambah_dukungan(b.id, WARGA_1)
    hasil = L.jumlah_dukungan_massal([a.id, b.id, c.id])
    assert hasil == {a.id: 3, b.id: 1, c.id: 0}
    assert hasil == {i: L.jumlah_dukungan(i) for i in (a.id, b.id, c.id)}


def test_massal_id_ganda_dan_id_tidak_ada():
    a = _buat(PELAPOR_A)
    L.tambah_dukungan(a.id, WARGA_1)
    assert L.jumlah_dukungan_massal([a.id, a.id, 99999]) == {a.id: 1, 99999: 0}


def test_massal_ribuan_id_melewati_batas_variabel_sqlite():
    a = _buat(PELAPOR_A)
    L.tambah_dukungan(a.id, WARGA_1)
    ids = [a.id, *range(100_000, 140_000)]  # > 32.766 variabel per query
    hasil = L.jumlah_dukungan_massal(ids)
    assert len(hasil) == len(ids)
    assert hasil[a.id] == 1
    assert sum(hasil.values()) == 1
