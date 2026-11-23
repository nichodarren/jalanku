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


# --- Kontras teks (WCAG 2.2 AA, 4.5:1) - review PR #20 ------------------------------------------

GAYA = Path(__file__).resolve().parents[3] / "web" / "shared" / "gaya.css"


def _token(nama: str) -> str:
    cocok = re.search(rf"{re.escape(nama)}:\s*(#[0-9a-fA-F]{{6}})", GAYA.read_text(encoding="utf-8"))
    assert cocok, nama
    return cocok.group(1)


def _luminansi(hexa: str) -> float:
    def kanal(c: int) -> float:
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (int(hexa[i : i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * kanal(r) + 0.7152 * kanal(g) + 0.0722 * kanal(b)


def _kontras(a: str, b: str) -> float:
    la, lb = sorted((_luminansi(a), _luminansi(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _warna_teks(css: str, selektor: str) -> str:
    """Warna teks yang dipasang untuk selektor ini di peta.css (bawaan putih)."""
    cocok = re.search(rf"{re.escape(selektor)}\s*\{{[^}}]*?[^-]color:\s*(#[0-9a-fA-F]{{6}}|var\(--[\w-]+\))", css)
    if not cocok:
        return "#ffffff"
    nilai = cocok.group(1)
    return _token(nilai[4:-1]) if nilai.startswith("var(") else nilai


@pytest.mark.parametrize("kelas", ["rusak", "kurang-baik", "selesai"])
@pytest.mark.parametrize("dasar", [".bubble-cluster", ".lencana"])
def test_teks_di_atas_warna_tingkat_cukup_kontras(dasar, kelas):
    latar = _token(f"--warna-{kelas}")
    teks = _warna_teks(_baca("peta.css"), f"{dasar}.{kelas}")
    assert _kontras(latar, teks) >= 4.5, f"{dasar}.{kelas}: {teks} di atas {latar} = {_kontras(latar, teks):.2f}:1"


def test_titik_lama_dikosongkan_bila_peta_gagal_dimuat():
    kode = _baca("index.js")
    tangkap = kode.split("} catch (galat) {", 1)
    assert len(tangkap) == 2, "blok catch saat memuat /api/peta tidak ditemukan"
    blok = tangkap[1].split("umumkan(galat.message)", 1)[0]
    assert "cluster.clearLayers()" in blok
