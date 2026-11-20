"""CLI ``python -m jalanku contoh-data``: berhenti rapi sebelum membuat data bila data wilayah belum siap.

Masukan M2 (PR #17): di folder data kosong, perintah ini dulu sudah membuat akun SIMULASI lalu
berhenti dengan traceback karena GeoJSON batas kecamatan belum disiapkan.
"""

from __future__ import annotations

import pytest

from jalanku.__main__ import main
from jalanku.core import GalatDomain, koneksi
from jalanku.modules import wilayah

PETUNJUK = "python -m jalanku.modules.wilayah.data.setup_wilayah"


class _DataBelumAda(GalatDomain):  # tiruan galat 503 modul wilayah saat GeoJSON belum disiapkan
    kode_http = 503


def _jumlah_akun() -> int:
    with koneksi() as kon:
        return kon.execute("SELECT COUNT(*) FROM akun_pengguna").fetchone()[0]


@pytest.fixture
def wilayah_belum_siap(monkeypatch):
    def gagal(lat, lon):
        raise _DataBelumAda(f"Data batas kecamatan belum tersedia atau rusak. Dari app/, jalankan {PETUNJUK}")

    monkeypatch.setattr(wilayah, "tentukan_wilayah", gagal)


def test_wilayah_belum_siap_keluar_kode_1_dengan_petunjuk_tanpa_traceback(wilayah_belum_siap, capsys):
    assert main(["contoh-data"]) == 1
    keluar = capsys.readouterr()
    assert PETUNJUK in keluar.err
    assert "Traceback" not in keluar.err + keluar.out
    assert "contoh-data" in keluar.err  # memberi tahu cara mengulang


def test_wilayah_belum_siap_tidak_ada_akun_atau_laporan_dibuat(wilayah_belum_siap):
    akun_awal = _jumlah_akun()
    main(["contoh-data"])
    assert _jumlah_akun() == akun_awal
    with koneksi() as kon:
        assert kon.execute("SELECT COUNT(*) FROM laporan").fetchone()[0] == 0


def test_galat_lain_tetap_terlihat(monkeypatch):
    # Hanya galat domain dari pengecekan wilayah yang diubah jadi pesan rapi; bug lain tidak disembunyikan.
    def rusak(lat, lon):
        raise RuntimeError("bug sungguhan")

    monkeypatch.setattr(wilayah, "tentukan_wilayah", rusak)
    with pytest.raises(RuntimeError, match="bug sungguhan"):
        main(["contoh-data"])


def test_wilayah_siap_contoh_data_berjalan_seperti_biasa(capsys):
    try:
        wilayah.tentukan_wilayah(-6.1754, 106.8272)
    except GalatDomain:
        pytest.skip("data batas kecamatan tidak tersedia di lingkungan test ini (lihat wilayah/README.md)")
    assert main(["contoh-data", "--jumlah", "5"]) == 0
    assert "laporan SIMULASI dibuat" in capsys.readouterr().out
    assert _jumlah_akun() >= 2
