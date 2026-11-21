"""CLI ``python -m jalanku jalan``: IP klien asli di balik reverse proxy (saran review #31).

Rate limit memakai ``request.client.host``. Di balik reverse proxy semua pengguna terbaca satu IP,
kecuali uvicorn mempercayai ``X-Forwarded-For`` dari proxy itu. Daftar proxy tepercaya diatur lewat
``JALANKU_PROXY_TEPERCAYA``; bawaan hanya 127.0.0.1 supaya header palsu dari internet tidak dipercaya.
"""

from __future__ import annotations

import uvicorn

from jalanku.__main__ import main


def _jalankan(monkeypatch) -> dict:
    tercatat = {}
    monkeypatch.setattr(uvicorn, "run", lambda *a, **kw: tercatat.update(kw))
    assert main(["jalan"]) == 0
    return tercatat


def test_bawaan_hanya_mempercayai_proxy_lokal(monkeypatch):
    monkeypatch.delenv("JALANKU_PROXY_TEPERCAYA", raising=False)
    kw = _jalankan(monkeypatch)
    assert kw["proxy_headers"] is True
    assert kw["forwarded_allow_ips"] == "127.0.0.1"


def test_proxy_tepercaya_dari_environment(monkeypatch):
    monkeypatch.setenv("JALANKU_PROXY_TEPERCAYA", "10.0.0.5,10.0.0.6")
    assert _jalankan(monkeypatch)["forwarded_allow_ips"] == "10.0.0.5,10.0.0.6"
