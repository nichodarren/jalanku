"""Penjaga statis frontend peta (US-15, US-16): aset tersaji, aman CSP, dan aksesibel.

Repo belum punya test runner JavaScript, jadi bagian yang bisa dicek tanpa browser diuji di sini:
berkas tersaji, tidak ada innerHTML atau atribut style inline (CSP style-src 'self'), warna lengkap,
dan animasi dimatikan untuk prefers-reduced-motion. Perilaku visual dicek manual (lihat PR).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

FOLDER = Path(__file__).resolve().parents[3] / "web" / "modules" / "peta"
BERKAS_JS = ("index.js", "bubble.js")


def _baca(nama: str) -> str:
    return (FOLDER / nama).read_text(encoding="utf-8")


@pytest.mark.parametrize("nama", [*BERKAS_JS, "peta.css"])
def test_aset_peta_tersaji(klien, nama):
    r = klien.get(f"/modules/peta/{nama}")
    assert r.status_code == 200
    assert r.text == _baca(nama)


@pytest.mark.parametrize("nama", BERKAS_JS)
def test_js_tanpa_innerhtml_dan_style_inline(nama):
    kode = _baca(nama)
    assert "innerHTML" not in kode
    assert "outerHTML" not in kode
    assert "insertAdjacentHTML" not in kode
    # Atribut style= diblokir CSP; skala lewat CSSOM style.setProperty diizinkan.
    assert not re.search(r"""["'{,\s]style["']?\s*[:=]""", kode)
    assert 'setAttribute("style"' not in kode


def test_js_tidak_memakai_field_di_luar_kontrak():
    kode = _baca("index.js") + _baca("bubble.js")
    for field in ("pelapor_id", "foto_id", "status_label", "tingkat_label"):
        assert field not in kode


def test_css_punya_warna_tiap_tingkat_dan_status():
    css = _baca("peta.css")
    for kelas in (".rusak", ".kurang-baik", ".sedang", ".selesai", ".simulasi"):
        assert kelas in css, kelas
    for ukuran in (".kecil", ".menengah", ".besar"):
        assert f".bubble-cluster{ukuran}" in css, ukuran


def test_css_mematikan_animasi_untuk_reduced_motion():
    css = _baca("peta.css")
    blok = css.split("@media (prefers-reduced-motion: reduce)", 1)
    assert len(blok) == 2, "blok prefers-reduced-motion tidak ada"
    assert "animation: none" in blok[1]


def test_rute_peta_dan_riwayat_terdaftar():
    kode = _baca("index.js")
    assert '"#/peta"' in kode and '"#/riwayat"' in kode
    assert "/api/peta?" in kode and "/api/wilayah" in kode
