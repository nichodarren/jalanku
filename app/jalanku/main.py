"""Perakit aplikasi (composition root). Pemilik: M1.

Satu-satunya tempat yang boleh mengenal SEMUA modul. Menambah modul baru = daftarkan di ``MODUL``
(dan di ``tests/arsitektur/test_batas_modul.py``) lewat change request.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from jalanku import __version__
from jalanku.core import jalankan_migrasi, pengaturan
from jalanku.core.galat import pasang_penangan_galat
from jalanku.core.keamanan import pasang_keamanan
from jalanku.modules import ai, akun, laporan, moderasi, notifikasi, pelaporan, penanganan, peta, statistik, wilayah

FOLDER_WEB = Path(__file__).resolve().parent / "web"

# Urutan = urutan tag di dokumentasi API.
MODUL = [akun, wilayah, laporan, ai, pelaporan, moderasi, penanganan, peta, statistik, notifikasi]


def buat_app(*, sertakan_dev: bool | None = None, migrasi: bool = True) -> FastAPI:
    cfg = pengaturan()
    if migrasi:
        jalankan_migrasi()

    app = FastAPI(
        title="JalanKu API",
        version=__version__,
        description="Lapor jalan rusak di DKI Jakarta. Kontrak terkunci: app/kontrak/openapi.json.",
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    pasang_penangan_galat(app)
    pasang_keamanan(app)

    for modul in MODUL:
        app.include_router(modul.router)
    if sertakan_dev if sertakan_dev is not None else cfg.mode in {"dev", "test"}:
        app.include_router(akun.router_dev)

    # Pelanggan kejadian (Dependency Inversion: modul bawah memberi tahu modul atas lewat kejadian)
    laporan.pasang()
    notifikasi.pasang()

    @app.get("/api/kesehatan", tags=["sistem"], summary="Cek hidup (untuk uptime monitor)")
    def kesehatan() -> dict:
        return {"status": "ok", "versi": __version__, "ai_aktif": ai.model_aktif()}

    app.mount("/", StaticFiles(directory=FOLDER_WEB, html=True), name="web")
    return app
