"""Test fondasi bersama (core)."""

from __future__ import annotations

import pytest

from jalanku.core import (
    TerlaluBanyak,
    TidakDitemukan,
    batasi,
    jalur_berkas,
    jarak_meter,
    langganan,
    simpan_berkas,
    terbitkan,
)


def test_jarak_monas_ke_bundaran_hi_sekitar_2_km():
    assert 2000 < jarak_meter(-6.1754, 106.8272, -6.1950, 106.8230) < 2400


def test_rate_limit():
    for _ in range(3):
        batasi("uji", 3, 60)
    with pytest.raises(TerlaluBanyak):
        batasi("uji", 3, 60)


def test_galat_pelanggan_tidak_menjatuhkan_penerbit():
    class Kejadian:
        pass

    tercatat = []

    def rusak(_):
        raise RuntimeError("pelanggan rusak")

    langganan(Kejadian, rusak)
    langganan(Kejadian, tercatat.append)
    terbitkan(Kejadian())
    assert len(tercatat) == 1


def test_penyimpanan_menolak_path_traversal():
    nama = simpan_berkas(b"isi", ".jpg")
    assert jalur_berkas(nama).read_bytes() == b"isi"
    with pytest.raises(TidakDitemukan):
        jalur_berkas("../jalanku.db")
