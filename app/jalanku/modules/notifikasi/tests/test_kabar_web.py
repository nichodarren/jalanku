"""Penjaga statis halaman #/kabar (US-25). Repo belum punya test runner JS; visual dicek di Chrome headless."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

FOLDER = Path(__file__).resolve().parents[3] / "web" / "modules" / "notifikasi"


def _baca(nama: str) -> str:
    return (FOLDER / nama).read_text(encoding="utf-8")


@pytest.mark.parametrize("nama", ["index.js", "notifikasi.css"])
def test_aset_tersaji(klien, nama):
    r = klien.get(f"/modules/notifikasi/{nama}")
    assert r.status_code == 200
    assert r.text == _baca(nama)


def test_js_aman_dan_memakai_kontrak():
    kode = _baca("index.js")
    for terlarang in ("innerHTML", "outerHTML", "insertAdjacentHTML", "document.write"):
        assert terlarang not in kode
    assert not re.search(r"""["'{,\s]style["']?\s*[:=]""", kode)
    assert 'jalur: "#/kabar"' in kode
    for jalur in ('"/api/notifikasi"', "/api/notifikasi/${k.id}/dibaca", '"/api/notifikasi/pengaturan"'):
        assert jalur in kode, jalur
    assert "encodeURIComponent(k.nomor)" in kode


def test_css_memakai_token_warna():
    css = re.sub(r"/\*.*?\*/", "", _baca("notifikasi.css"), flags=re.S)
    assert "var(--warna-" in css
    assert "#" not in css
