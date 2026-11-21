"""Penjaga statis kerangka navigasi (web/app.js + web/shared/gaya.css), masukan UX M6.

Di layar sempit menu utama pindah ke bar bawah yang menempel, supaya tidak menumpuk di atas dan
mendorong peta ke bawah. Repo belum punya test runner JS; perilaku visual dicek di Chrome headless
(lihat PR). Yang dijaga di sini: aturan CSS-nya ada dan menu aktif ditandai untuk pembaca layar.
"""

from __future__ import annotations

import re
from pathlib import Path

WEB = Path(__file__).resolve().parents[2] / "jalanku" / "web"


def _blok_media_sempit(css: str) -> str:
    m = re.search(r"@media \(max-width: 719px\) \{(.*?)\n\}", css, re.S)
    assert m, "blok @media (max-width: 719px) tidak ada"
    return m.group(1)


def test_menu_jadi_bar_bawah_di_layar_sempit():
    blok = _blok_media_sempit((WEB / "shared" / "gaya.css").read_text(encoding="utf-8"))
    nav = re.search(r"#navigasi \{(.*?)\}", blok, re.S).group(1)
    for aturan in ("position: fixed", "bottom: 0", "flex-wrap: nowrap", "overflow-x: auto", "safe-area-inset-bottom"):
        assert aturan in nav, aturan
    # isi halaman & toast tidak tertutup bar
    assert re.search(r"body \{[^}]*padding-bottom", blok)
    assert re.search(r"\.toast \{[^}]*bottom", blok)
    # bar di atas kontrol peta Leaflet (z-index 1000)
    assert int(re.search(r"z-index: (\d+)", nav).group(1)) > 1000


def test_item_menu_tetap_mudah_disentuh():
    css = (WEB / "shared" / "gaya.css").read_text(encoding="utf-8")
    assert "min-height: var(--sentuh-min)" in re.search(r"#navigasi a \{(.*?)\}", css, re.S).group(1)


def test_menu_aktif_ditandai_dan_terlihat():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert '"aria-current"' in js
    assert "scrollIntoView" in js


def test_tampilan_lebar_tidak_berubah():
    # di luar blok media sempit, navigasi tetap di header (tidak fixed)
    css = (WEB / "shared" / "gaya.css").read_text(encoding="utf-8")
    luar = css.replace(_blok_media_sempit(css), "")
    assert "position: fixed" not in re.search(r"#navigasi \{(.*?)\}", luar, re.S).group(1)
