"""CLI ``python -m jalanku contoh-data``: berhenti rapi sebelum membuat data bila data wilayah belum siap.

Masukan M2 (PR #17): di folder data kosong, perintah ini dulu sudah membuat akun SIMULASI lalu
berhenti dengan traceback karena GeoJSON batas kecamatan belum disiapkan.
"""

from __future__ import annotations

import os
import shutil

import pytest

from jalanku.__main__ import main
from jalanku.core import GalatDomain, koneksi, pengaturan
from jalanku.core.config import FOLDER_APP
from jalanku.modules import wilayah

PETUNJUK = "python -m jalanku.modules.wilayah.data.setup_wilayah"
BERKAS_WILAYAH = "wilayah-dki-jakarta.geojson"  # nama berkas hasil setup_wilayah (modul wilayah, #17)


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


def _siapkan_data_wilayah() -> None:
    """Fixture bersama memakai folder data kosong per test. Bila GeoJSON wilayah sudah disiapkan di folder
    data bawaan (``app/var``, mis. oleh langkah CI ``setup_wilayah``), salin ke folder data test ini."""
    if not wilayah_siap():
        sumber = FOLDER_APP / "var" / BERKAS_WILAYAH
        if sumber.is_file():
            shutil.copyfile(sumber, pengaturan().folder_data / BERKAS_WILAYAH)


def wilayah_siap() -> bool:
    try:
        wilayah.tentukan_wilayah(-6.1754, 106.8272)
    except GalatDomain:
        return False
    return True


def test_wilayah_siap_contoh_data_berjalan_seperti_biasa(capsys):
    _siapkan_data_wilayah()
    if not wilayah_siap():
        # Di CI data wilayah wajib ada (langkah "Siapkan GeoJSON wilayah"), jadi test ini tidak boleh dilewati.
        assert not os.environ.get("CI"), "Data wilayah tidak tersedia di CI; cek langkah setup_wilayah di workflow."
        pytest.skip("Jalankan dulu: python -m jalanku.modules.wilayah.data.setup_wilayah")
    assert main(["contoh-data", "--jumlah", "5"]) == 0
    assert "laporan SIMULASI dibuat" in capsys.readouterr().out
    assert _jumlah_akun() >= 2
    with koneksi() as kon:
        assert kon.execute("SELECT COUNT(*) FROM laporan WHERE simulasi = 1").fetchone()[0] >= 1
