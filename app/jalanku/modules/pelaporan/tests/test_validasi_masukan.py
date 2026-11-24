"""Unit test langsung ``validasi_masukan`` (FR-PEL-01..03), tanpa lewat FastAPI, laporan, atau wilayah."""

from __future__ import annotations

import pytest

from jalanku.core import TidakValid
from jalanku.modules.pelaporan.layanan import (
    MAKS_BYTE_FOTO,
    MAKS_FOTO,
    MAKS_KETERANGAN,
    SUMBER_LOKASI,
    validasi_masukan,
)

# Hanya tanda tangan berkas yang dicek di sini; validasi isi mendalam dilakukan modul laporan (TS-02).
JPEG = bytes.fromhex("ffd8ff") + bytes(16)
PNG = bytes.fromhex("89504e470d0a1a0a") + bytes(16)
WEBP = b"RIFF" + bytes(4) + b"WEBP" + bytes(16)
GIF = b"GIF89a" + bytes(16)


def _ok(**ubah):
    argumen = {"foto": [JPEG], "lat": -6.17, "lon": 106.82, "sumber_lokasi": "manual", "keterangan": ""}
    argumen.update(ubah)
    validasi_masukan(**argumen)


def test_masukan_sah_lolos():
    _ok()


@pytest.mark.parametrize("jumlah", [1, 2, MAKS_FOTO])
def test_jumlah_foto_1_sampai_3_lolos(jumlah):
    _ok(foto=[JPEG] * jumlah)


def test_tanpa_foto_ditolak():
    with pytest.raises(TidakValid, match="minimal 1 foto"):
        _ok(foto=[])


def test_empat_foto_ditolak():
    with pytest.raises(TidakValid, match="Maksimal 3 foto"):
        _ok(foto=[JPEG] * (MAKS_FOTO + 1))


@pytest.mark.parametrize("isi", [JPEG, PNG, WEBP])
def test_jpeg_png_webp_diterima(isi):
    _ok(foto=[isi])


@pytest.mark.parametrize("isi", [GIF, b"%PDF-1.7", b"teks biasa", b""])
def test_bukan_jpeg_png_webp_ditolak(isi):
    with pytest.raises(TidakValid, match="JPEG, PNG, atau WebP"):
        _ok(foto=[isi])


def test_ukuran_tepat_10_mb_lolos_lebih_satu_byte_ditolak():
    _ok(foto=[JPEG + bytes(MAKS_BYTE_FOTO - len(JPEG))])
    with pytest.raises(TidakValid, match="10 MB"):
        _ok(foto=[JPEG + bytes(MAKS_BYTE_FOTO - len(JPEG) + 1)])


@pytest.mark.parametrize(("lat", "lon"), [(-90, 0), (90, 0), (0, -180), (0, 180)])
def test_koordinat_di_batas_lolos(lat, lon):
    _ok(lat=lat, lon=lon)


@pytest.mark.parametrize(("lat", "lon"), [(-90.01, 0), (90.01, 0), (0, -180.01), (0, 180.01)])
def test_koordinat_di_luar_rentang_ditolak(lat, lon):
    with pytest.raises(TidakValid, match="Koordinat"):
        _ok(lat=lat, lon=lon)


@pytest.mark.parametrize("sumber", SUMBER_LOKASI)
def test_sumber_lokasi_dikenal_lolos(sumber):
    _ok(sumber_lokasi=sumber)


def test_sumber_lokasi_tak_dikenal_ditolak():
    with pytest.raises(TidakValid, match="Sumber lokasi"):
        _ok(sumber_lokasi="tebakan")


def test_keterangan_280_lolos_281_ditolak():
    _ok(keterangan="a" * MAKS_KETERANGAN)
    with pytest.raises(TidakValid, match="280 karakter"):
        _ok(keterangan="a" * (MAKS_KETERANGAN + 1))
