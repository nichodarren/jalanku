"""Header keamanan, pengecekan CSRF, dan rate limit (NFR-SEC-03, NFR-SEC-04, OWASP A02/A06)."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .config import pengaturan
from .galat import TerlaluBanyak

HEADER_CSRF = "X-JalanKu"
METODE_MENGUBAH = {"POST", "PUT", "PATCH", "DELETE"}

CSP = (
    "default-src 'self'; "
    "img-src 'self' data: blob:; "  # tile peta lewat /api/tile (core/tile.py)
    "script-src 'self'; style-src 'self'; connect-src 'self'; "
    "font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
)
# Halaman dokumentasi API (Swagger UI) memuat aset dari jsDelivr + satu script inline.
# Pelonggaran HANYA berlaku di path ini; halaman aplikasi tetap memakai CSP ketat di atas.
JALUR_DOKUMENTASI = ("/api/docs", "/api/docs/oauth2-redirect")
CSP_DOKUMENTASI = (
    "default-src 'self'; img-src 'self' data: https://fastapi.tiangolo.com; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' https://cdn.jsdelivr.net; "
    "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'"
)


def pasang_keamanan(app: FastAPI) -> None:
    @app.middleware("http")
    async def _keamanan(request: Request, call_next):
        # CSRF: request yang mengubah data ke /api wajib membawa header khusus.
        # Browser tidak mengirim header kustom lintas situs tanpa izin CORS, jadi ini menolak CSRF
        # (cookie sesi juga SameSite=Lax).
        if (
            request.method in METODE_MENGUBAH
            and request.url.path.startswith("/api/")
            and request.headers.get(HEADER_CSRF) != "1"
        ):
            return JSONResponse({"detail": f"Header {HEADER_CSRF} wajib ada."}, status_code=403)

        respons = await call_next(request)
        h = respons.headers
        h.setdefault("Content-Security-Policy", CSP_DOKUMENTASI if request.url.path in JALUR_DOKUMENTASI else CSP)
        h.setdefault("X-Content-Type-Options", "nosniff")
        h.setdefault("X-Frame-Options", "DENY")
        h.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        h.setdefault("Permissions-Policy", "camera=(self), geolocation=(self), microphone=()")
        if pengaturan().produksi:
            h.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        if request.url.path.startswith("/api/"):
            h.setdefault("Cache-Control", "no-store")
        return respons


# --- Rate limit -------------------------------------------------------------------------------
# Sederhana, di memori proses (cukup untuk satu proses server). Kunci contoh: "laporan:<id pengguna>".

_jejak: dict[str, deque[float]] = defaultdict(deque)
_kunci_thread = threading.Lock()


def batasi(kunci: str, maks: int, jendela_detik: int, pesan: str | None = None) -> None:
    """Lempar ``TerlaluBanyak`` (429) bila ``kunci`` sudah dipakai ``maks`` kali dalam jendela waktu."""
    kini = time.monotonic()
    with _kunci_thread:
        antre = _jejak[kunci]
        while antre and kini - antre[0] > jendela_detik:
            antre.popleft()
        if len(antre) >= maks:
            raise TerlaluBanyak(pesan or "Terlalu banyak permintaan. Coba lagi nanti.")
        antre.append(kini)


def reset_batas() -> None:
    """Test: hapus semua jejak rate limit."""
    with _kunci_thread:
        _jejak.clear()
