"""Pemeriksaan unduhan lokal tanpa bergantung pada jaringan di unit test."""

import hashlib
from io import BytesIO

import pytest

from jalanku.core import pengaturan
from jalanku.modules.wilayah.data import setup_wilayah


def test_unduhan_salah_mempertahankan_data_lama(monkeypatch):
    tujuan = pengaturan().folder_data / "wilayah-dki-jakarta.geojson"
    tujuan.write_bytes(b"SIMULASI data lama")
    monkeypatch.setattr(setup_wilayah, "urlopen", lambda *a, **kw: BytesIO(b"SIMULASI unduhan terpotong"))
    with pytest.raises(ValueError, match="SHA-256"):
        setup_wilayah.unduh_dan_siapkan()
    assert tujuan.read_bytes() == b"SIMULASI data lama"


def test_unduhan_terverifikasi_diserahkan_ke_konverter(monkeypatch):
    isi = b"SIMULASI sumber"
    tujuan = pengaturan().folder_data / "wilayah-dki-jakarta.geojson"
    monkeypatch.setattr(setup_wilayah, "SHA256_SUMBER", hashlib.sha256(isi).hexdigest())
    monkeypatch.setattr(setup_wilayah, "urlopen", lambda *a, **kw: BytesIO(isi))
    diterima = []
    monkeypatch.setattr(setup_wilayah, "siapkan", lambda sumber, hasil: diterima.append((sumber.read_bytes(), hasil)))
    assert setup_wilayah.unduh_dan_siapkan() == tujuan
    assert diterima == [(isi, tujuan)]
