"""Penjaga statis frontend #/petugas (US-18, US-19): aset tersaji, aman CSP, kontras, dan kontrak dipakai benar.

Repo belum punya test runner JavaScript; perilaku di browser dicek manual (lihat PR).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

WEB = Path(__file__).resolve().parents[3] / "web"
FOLDER = WEB / "modules" / "penanganan"


def _baca(nama: str) -> str:
    return (FOLDER / nama).read_text(encoding="utf-8")


@pytest.mark.parametrize("nama", ["index.js", "penanganan.css"])
def test_aset_tersaji(klien, nama):
    r = klien.get(f"/modules/penanganan/{nama}")
    assert r.status_code == 200
    assert r.text == _baca(nama)


def test_js_tanpa_innerhtml_style_inline_dan_impor_modul_lain():
    kode = _baca("index.js")
    for terlarang in ("innerHTML", "outerHTML", "insertAdjacentHTML", 'setAttribute("style"'):
        assert terlarang not in kode
    assert not re.search(r"""["'{,\s]style["']?\s*[:=]""", kode)
    impor = re.findall(r'from\s+"([^"]+)"', kode)
    assert impor and all(i.startswith("/shared/") for i in impor), impor


def test_memakai_kontrak_petugas():
    kode = _baca("index.js")
    assert '"#/petugas"' in kode
    assert "/api/petugas/laporan" in kode
    assert "/status`" in kode and "new FormData()" in kode
    for field in ('"ke"', '"catatan"', '"foto"'):
        assert f"append({field}" in kode, field
    assert 'accept: "image/*"' in kode
    for field in ("pelapor_id", "skor_prioritas", "status_label", "tingkat_label"):
        assert field not in kode, field


def test_daftar_dan_titik_dikosongkan_bila_gagal_memuat():
    kode = _baca("index.js").split('semua = await api.get("/api/petugas/laporan");', 1)[1]
    blok = kode.split("} catch (galat) {", 1)
    assert len(blok) == 2
    isi = blok[1].split("umumkan(galat.message)", 1)[0]
    assert "lapisan.clearLayers()" in isi and "kosongkan(daftar)" in isi


GAYA = WEB / "shared" / "gaya.css"


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


@pytest.mark.parametrize("kelas", ["rusak", "kurang-baik", "selesai", "dikerjakan"])
def test_lencana_status_dan_tingkat_cukup_kontras(kelas):
    css = _baca("penanganan.css")
    cocok = re.search(rf"\.lencana-p\.{kelas}\s*\{{([^}}]*)\}}", css)
    assert cocok, kelas
    teks = re.search(r"[^-]color:\s*var\((--[\w-]+)\)", cocok.group(1))
    warna_teks = _token(teks.group(1)) if teks else "#ffffff"
    latar = _token(f"--warna-{kelas}")
    assert _kontras(latar, warna_teks) >= 4.5, f"{kelas}: {_kontras(latar, warna_teks):.2f}:1"


def test_css_tombol_sentuh_dan_reduced_motion():
    css = _baca("penanganan.css")
    assert "var(--sentuh-min)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css


def test_batas_catatan_di_form_sama_dengan_api(klien):
    # Review #40 (Neilson): form dulu mengizinkan 500 karakter, API menolak di atas 200 dengan 422 yang terlalu umum.
    skema = klien.get("/api/openapi.json").json()["components"]["schemas"]
    form = [s["properties"]["catatan"] for s in skema.values() if "catatan" in s.get("properties", {})]
    batas_api = form[0]["maxLength"]
    kode = _baca("index.js")
    assert re.findall(r'name: "catatan", rows: "2", maxlength: "(\d+)"', kode) == [str(batas_api)]
    assert f'"Catatan (opsional, maks. {batas_api} karakter)"' in kode
