"""Penjaga statis halaman detail laporan (US-17, web/modules/laporan/).

Repo belum punya test runner JS; perilaku visual dicek di Chrome headless (lihat PR). Yang dijaga di
sini: aset tersaji, aman CSP & XSS (tanpa innerHTML/style inline), memakai kontrak yang benar, dan
tidak mengubah jalur rute yang dipakai modul lain sebagai tautan.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

FOLDER = Path(__file__).resolve().parents[3] / "web" / "modules" / "laporan"


def _baca(nama: str) -> str:
    return (FOLDER / nama).read_text(encoding="utf-8")


@pytest.mark.parametrize("nama", ["index.js", "laporan.css"])
def test_aset_tersaji(klien, nama):
    r = klien.get(f"/modules/laporan/{nama}")
    assert r.status_code == 200
    assert r.text == _baca(nama)


def test_js_tanpa_html_mentah_dan_style_inline():
    kode = _baca("index.js")
    for terlarang in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write"):
        assert terlarang not in kode, terlarang
    assert not re.search(r"""["'{,\s]style["']?\s*[:=]""", kode)


def test_jalur_rute_tetap():
    assert 'jalur: "#/laporan/:nomor"' in _baca("index.js")


def test_memakai_kontrak_detail_dan_instansi():
    kode = _baca("index.js")
    assert "/api/laporan/${encodeURIComponent(" in kode  # nomor dari URL di-encode
    assert '"/api/instansi"' in kode
    for field in (
        "foto",
        "timeline",
        "jumlah_dukungan",
        "diperiksa_oleh",
        "simulasi",
        "instansi_id",
        "ke_status",
        "pelaku",
    ):
        assert field in kode, field
    assert "pelapor_id" not in kode


def test_foto_sebelum_sesudah_dan_label_pelaku():
    kode = _baca("index.js")
    assert '"bukti"' in kode and '"sesudah"' in kode
    assert "LABEL_PELAKU" in kode and "LABEL_STATUS" in kode
    assert "SIMULASI" in kode


def test_tautan_luar_aman():
    # Tautan kanal resmi membuka tab baru tanpa memberi akses window.opener.
    kode = _baca("index.js")
    assert 'target: "_blank"' in kode
    assert 'rel: "noopener noreferrer"' in kode


def test_css_memakai_token_warna():
    css = _baca("laporan.css")
    assert "var(--warna-" in css
    assert "#" not in re.sub(r"/\*.*?\*/", "", css, flags=re.S).replace("#fff", ""), "pakai token warna, bukan hex"
