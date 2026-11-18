"""Galat domain dengan pesan Bahasa Indonesia yang aman ditampilkan ke pengguna.

Modul melempar galat ini; ``pasang_penangan_galat`` mengubahnya menjadi respons
``{"detail": "<pesan>"}`` dengan kode HTTP yang sesuai. Jangan memasukkan data
pribadi atau detail internal ke pesan.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

log = logging.getLogger("jalanku")


class GalatDomain(Exception):
    kode_http = 400

    def __init__(self, pesan: str):
        super().__init__(pesan)
        self.pesan = pesan


class TidakValid(GalatDomain):
    kode_http = 400


class PerluMasuk(GalatDomain):
    kode_http = 401


class TidakBerhak(GalatDomain):
    kode_http = 403


class TidakDitemukan(GalatDomain):
    kode_http = 404


class Konflik(GalatDomain):
    kode_http = 409


class TerlaluBanyak(GalatDomain):
    kode_http = 429


class BelumDibuat(GalatDomain):
    """Endpoint/fungsi yang kontraknya sudah ada tetapi implementasinya belum (stub)."""

    kode_http = 501

    def __init__(self, story: str, pemilik: str):
        super().__init__(f"Fitur ini belum dibuat ({story}, pemilik {pemilik}).")


def pasang_penangan_galat(app: FastAPI) -> None:
    @app.exception_handler(GalatDomain)
    async def _galat_domain(_: Request, galat: GalatDomain) -> JSONResponse:
        return JSONResponse({"detail": galat.pesan}, status_code=galat.kode_http)

    @app.exception_handler(Exception)
    async def _galat_tak_terduga(_: Request, galat: Exception) -> JSONResponse:
        log.exception("Galat tak terduga", exc_info=galat)
        return JSONResponse({"detail": "Terjadi kesalahan di server. Coba lagi nanti."}, status_code=500)
