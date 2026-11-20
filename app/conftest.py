"""Fixture bersama untuk SEMUA test (tests/ dan jalanku/modules/*/tests/). Pemilik: M1 + QA lead.

Setiap test berjalan dengan basis data & folder berkas baru di folder sementara (tidak menyentuh var/).
"""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from jalanku.core import jalankan_migrasi, muat_ulang_pengaturan
from jalanku.core.keamanan import reset_batas
from jalanku.core.kejadian import hapus_semua_langganan
from jalanku.core.waktu import atur_waktu

# Koordinat nyata untuk test (dipakai juga di acceptance criteria backlog).
TITIK = {
    "monas": (-6.1754, 106.8272),
    "blok_m": (-6.2441, 106.8003),
    "jatinegara": (-6.2153, 106.8707),
    "kelapa_gading": (-6.1588, 106.9056),
    "grogol": (-6.1666, 106.7900),
    "kota_tangerang": (-6.1781, 106.6300),
}


def foto_bytes(w: int = 800, h: int = 600, fmt: str = "JPEG", exif: bytes | None = None, warna=(90, 90, 90)) -> bytes:
    """Gambar uji asli (bukan foto jalan sungguhan) untuk test yang butuh foto valid."""
    buf = io.BytesIO()
    kw = {"exif": exif} if exif is not None else {}
    Image.new("RGB", (w, h), warna).save(buf, fmt, **kw)
    return buf.getvalue()


@pytest.fixture(autouse=True)
def lingkungan(tmp_path, monkeypatch):
    monkeypatch.setenv("JALANKU_MODE", "test")
    monkeypatch.setenv("JALANKU_DATA", str(tmp_path / "var"))
    muat_ulang_pengaturan()
    reset_batas()
    hapus_semua_langganan()
    atur_waktu(None)
    jalankan_migrasi()
    yield
    atur_waktu(None)
    hapus_semua_langganan()
    monkeypatch.undo()
    muat_ulang_pengaturan()


@pytest.fixture
def app():
    from jalanku.main import buat_app

    return buat_app()


@pytest.fixture
def buat_klien(app):
    """Pabrik klien HTTP. Setiap klien punya cookie sendiri (= pengguna berbeda)."""

    def _buat(peran: str | None = None, email: str | None = None, instansi_id: str | None = None) -> TestClient:
        klien = TestClient(app, headers={"X-JalanKu": "1"})
        if peran:
            r = klien.post(
                "/api/dev/masuk",
                json={"email": email or f"{peran}@uji.test", "peran": peran, "instansi_id": instansi_id},
            )
            assert r.status_code == 200, r.text
        return klien

    return _buat


@pytest.fixture
def klien(buat_klien) -> TestClient:
    """Klien tanpa login (pengunjung)."""
    return buat_klien()
