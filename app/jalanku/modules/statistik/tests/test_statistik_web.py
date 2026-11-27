"""Penjaga statis frontend #/statistik (US-23): aset tersaji, aman CSP, label simulasi, kontrak dipakai benar."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

FOLDER = Path(__file__).resolve().parents[3] / "web" / "modules" / "statistik"


def _baca(nama: str) -> str:
    return (FOLDER / nama).read_text(encoding="utf-8")


@pytest.mark.parametrize("nama", ["index.js", "statistik.css"])
def test_aset_tersaji(klien, nama):
    r = klien.get(f"/modules/statistik/{nama}")
    assert r.status_code == 200
    assert r.text == _baca(nama)


def test_js_tanpa_innerhtml_style_inline_dan_impor_modul_lain():
    kode = _baca("index.js")
    for terlarang in ("innerHTML", "outerHTML", "insertAdjacentHTML", 'setAttribute("style"'):
        assert terlarang not in kode
    assert not re.search(r"""["'{,\s]style["']?\s*[:=]""", kode)
    impor = re.findall(r'from\s+"([^"]+)"', kode)
    assert impor and all(i.startswith("/shared/") for i in impor), impor


def test_jalur_publik_tetap():
    kode = _baca("index.js")
    assert 'jalur: "#/statistik"' in kode
    assert "peran: null" in kode
    assert "belumDibuat" not in kode


def test_memakai_kontrak_statistik_dan_label_simulasi():
    kode = _baca("index.js")
    assert "/api/statistik?hari=" in kode
    for field in (
        "label_simulasi",
        "periode_hari",
        "persen_diputuskan_ai",
        "instansi",
        "jumlah_per_status",
        "median_jam_dikerjakan",
        "median_jam_selesai",
        "n_dikerjakan",
        "n_selesai",
        "nama_pendek",
    ):
        assert f".{field}" in kode, field
    assert "data uji/simulasi" in kode.lower()  # BR-04
    assert "minimal 5" in kode  # median kosong dijelaskan, bukan ditampilkan 0


def test_css_tombol_sentuh_dan_reduced_motion():
    css = _baca("statistik.css")
    assert "var(--sentuh-min)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
