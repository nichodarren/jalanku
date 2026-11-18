"""Perilaku stub wilayah yang dijamin ke modul lain. M2 mengganti test ini dengan test titik nyata
(NFR-FUN-01: ≥ 3 titik per kota + 5 titik luar Jakarta) saat TS-04/US-07 selesai."""

from __future__ import annotations

from conftest import TITIK
from jalanku.modules import wilayah


def test_titik_di_jakarta_dapat_instansi():
    h = wilayah.tentukan_wilayah(*TITIK["monas"])
    assert h.di_dalam and h.instansi is not None and h.instansi.id.startswith("SUDIN_")


def test_titik_luar_jakarta_ditolak():
    h = wilayah.tentukan_wilayah(*TITIK["kota_tangerang"])
    assert not h.di_dalam and h.instansi is None


def test_enam_instansi_dan_kanal_https():
    daftar = wilayah.daftar_instansi()
    assert {i.id for i in daftar} == {"DINAS_BM", "SUDIN_JP", "SUDIN_JU", "SUDIN_JB", "SUDIN_JS", "SUDIN_JT"}
    assert all(i.kanal_url.startswith("https://") for i in daftar)


def test_dinas_boleh_semua_sudin_hanya_kotanya():
    assert wilayah.boleh_menangani("DINAS_BM", "Jakarta Selatan")
    assert wilayah.boleh_menangani("SUDIN_JS", "Jakarta Selatan")
    assert not wilayah.boleh_menangani("SUDIN_JS", "Jakarta Pusat")
