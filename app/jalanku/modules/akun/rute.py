"""Endpoint modul akun. Kontrak (path, method, skema) dikunci di app/kontrak/openapi.json."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status

from jalanku.core import BelumDibuat, pengaturan

from . import layanan
from .skema import (
    DaftarMasukan,
    EmailMasukan,
    MasukDevMasukan,
    MasukMasukan,
    PenggunaKeluaran,
    Pesan,
    TokenMasukan,
)
from .tipe import Pengguna

router = APIRouter(prefix="/api/akun", tags=["akun"])
router_dev = APIRouter(prefix="/api/dev", tags=["dev (hanya mode dev/test)"])


def _keluaran(p: Pengguna) -> PenggunaKeluaran:
    return PenggunaKeluaran(**p.__dict__)


def _pasang_cookie(respons: Response, token: str) -> None:
    respons.set_cookie(
        layanan.NAMA_COOKIE,
        token,
        max_age=int(layanan.UMUR_SESI.total_seconds()),
        httponly=True,
        samesite="lax",
        secure=pengaturan().produksi,
        path="/",
    )


@router.get("/saya", response_model=PenggunaKeluaran | None, summary="Pengguna yang sedang masuk (null bila belum)")
def saya(pengguna: Pengguna | None = Depends(layanan.pengguna_opsional)):
    return _keluaran(pengguna) if pengguna else None


@router.post("/daftar", response_model=Pesan, status_code=status.HTTP_201_CREATED, summary="FR-AKN-02 daftar")
def daftar(masukan: DaftarMasukan):
    raise BelumDibuat("US-01", "M2")


@router.post("/verifikasi", response_model=PenggunaKeluaran, summary="FR-AKN-02 verifikasi email")
def verifikasi(masukan: TokenMasukan, respons: Response):
    raise BelumDibuat("US-01", "M2")


@router.post("/kirim-ulang", response_model=Pesan, summary="Kirim ulang email verifikasi")
def kirim_ulang(masukan: EmailMasukan):
    raise BelumDibuat("US-01", "M2")


@router.post("/masuk", response_model=PenggunaKeluaran, summary="FR-AKN-02 masuk dengan email + password")
def masuk(masukan: MasukMasukan, respons: Response):
    raise BelumDibuat("US-01", "M2")


@router.post("/keluar", response_model=Pesan, summary="Akhiri sesi")
def keluar(request: Request, respons: Response):
    layanan.akhiri_sesi(request.cookies.get(layanan.NAMA_COOKIE))
    respons.delete_cookie(layanan.NAMA_COOKIE, path="/")
    return Pesan(detail="Kamu sudah keluar.")


@router.delete("/saya", response_model=Pesan, summary="FR-AKN-04 hapus akun")
def hapus_akun(pengguna: Pengguna = Depends(layanan.wajib_masuk)):
    raise BelumDibuat("US-02", "M2")


@router_dev.post("/masuk", response_model=PenggunaKeluaran, summary="Masuk sebagai peran apa pun (dev/test)")
def masuk_dev(masukan: MasukDevMasukan, respons: Response):
    pengguna, token = layanan.masuk_dev(masukan.email, masukan.peran, masukan.instansi_id, masukan.nama)
    _pasang_cookie(respons, token)
    return _keluaran(pengguna)
