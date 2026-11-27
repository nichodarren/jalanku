"""Penjaga statis frontend #/admin (US-12, US-13, US-14): aset tersaji, aman CSP, kontrak dipakai benar.

Repo belum punya test runner JavaScript; perilaku di browser dicek manual (lihat PR) dan nanti
lewat test sistem Playwright di tests/sistem/.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

WEB = Path(__file__).resolve().parents[3] / "web"
FOLDER = WEB / "modules" / "moderasi"
GAYA = WEB / "shared" / "gaya.css"


def _baca(nama: str) -> str:
    return (FOLDER / nama).read_text(encoding="utf-8")


@pytest.mark.parametrize("nama", ["index.js", "moderasi.css"])
def test_aset_tersaji(klien, nama):
    r = klien.get(f"/modules/moderasi/{nama}")
    assert r.status_code == 200
    assert r.text == _baca(nama)


def test_js_tanpa_innerhtml_style_inline_dan_impor_modul_lain():
    kode = _baca("index.js")
    for terlarang in ("innerHTML", "outerHTML", "insertAdjacentHTML", 'setAttribute("style"'):
        assert terlarang not in kode
    assert not re.search(r"""["'{,\s]style["']?\s*[:=]""", kode)
    impor = re.findall(r'from\s+"([^"]+)"', kode)
    assert impor and all(i.startswith("/shared/") for i in impor), impor


def test_jalur_rute_tetap_dan_hanya_admin():
    kode = _baca("index.js")
    assert 'jalur: "#/admin"' in kode
    assert 'peran: ["admin"]' in kode
    assert "belumDibuat" not in kode


def test_memakai_kontrak_moderasi():
    kode = _baca("index.js")
    assert '"/api/admin/antrean"' in kode
    for aksi in ("/verifikasi`", "/tolak`", "/gabung`", "/paket`", "/tingkat`"):
        assert aksi in kode, aksi
    for field in ("tingkat:", "alasan:", "label:", "induk_nomor:"):
        assert field in kode, field
    for field in ("banding", "duplikat", "hasil_ai", "jarak_m", "kanal_url", "kanal_nama", "teks"):
        assert f".{field}" in kode, field
    # Antrean & paket tidak pernah memuat identitas pelapor (NFR-PRI-01).
    for field in ("pelapor_id", "email", "nama_pelapor"):
        assert field not in kode, field


def test_batas_alasan_tolak_dan_koreksi_di_form_sama_dengan_server(klien):
    skema = klien.get("/api/openapi.json").json()["components"]["schemas"]
    maks_tolak = skema["TolakMasukan"]["properties"]["alasan"]["maxLength"]
    maks_koreksi = skema["KoreksiMasukan"]["properties"]["alasan"]["maxLength"]
    kode = _baca("index.js")
    # Minimal 5 = syarat moderasi.tolak/koreksi (BR-03), lebih ketat dari skema 3.
    assert re.findall(r'name: "alasan",[^}]*minlength: "(\d+)",\s*maxlength: "(\d+)"', kode) == [
        ("5", str(maks_tolak)),
        ("5", str(maks_koreksi)),
    ]


def test_tautan_kanal_resmi_aman():
    kode = _baca("index.js")
    assert 'rel: "noopener noreferrer"' in kode
    assert 'target: "_blank"' in kode


def test_css_tombol_sentuh_dan_reduced_motion():
    css = _baca("moderasi.css")
    assert "var(--sentuh-min)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css


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


def test_lencana_banding_cukup_kontras():
    css = _baca("moderasi.css")
    blok = re.search(r"\.lencana-banding\s*\{([^}]*)\}", css)
    assert blok
    latar = _token(re.search(r"background:\s*var\((--[\w-]+)\)", blok.group(1)).group(1))
    teks = _token(re.search(r"[^-]color:\s*var\((--[\w-]+)\)", blok.group(1)).group(1))
    la, lb = sorted((_luminansi(latar), _luminansi(teks)), reverse=True)
    assert (la + 0.05) / (lb + 0.05) >= 4.5
