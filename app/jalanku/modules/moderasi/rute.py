from __future__ import annotations

from fastapi import APIRouter, Depends

from jalanku.core import BelumDibuat
from jalanku.modules.akun import PERAN_ADMIN, Pengguna, wajib_peran, wajib_terverifikasi

from . import layanan
from .skema import (
    AksiKeluaran,
    GabungMasukan,
    ItemAntreanKeluaran,
    KoreksiMasukan,
    PaketKeluaran,
    TolakMasukan,
    VerifikasiMasukan,
)

router = APIRouter(tags=["moderasi"])
admin = wajib_peran(PERAN_ADMIN)


@router.get(
    "/api/admin/antrean", response_model=list[ItemAntreanKeluaran], summary="FR-MOD-01 antrean (banding di atas)"
)
def antrean(pengguna: Pengguna = Depends(admin)):
    return layanan.antrean()


@router.post("/api/admin/laporan/{nomor}/verifikasi", response_model=AksiKeluaran, summary="FR-MOD-01 verifikasi")
def verifikasi(nomor: str, masukan: VerifikasiMasukan, pengguna: Pengguna = Depends(admin)):
    return layanan.verifikasi(nomor, masukan.tingkat, pengguna.id)


@router.post("/api/admin/laporan/{nomor}/tolak", response_model=AksiKeluaran, summary="FR-MOD-01 tolak")
def tolak(nomor: str, masukan: TolakMasukan, pengguna: Pengguna = Depends(admin)):
    return layanan.tolak(nomor, masukan.alasan, pengguna.id, masukan.label)


@router.post("/api/admin/laporan/{nomor}/gabung", response_model=AksiKeluaran, summary="FR-MOD-01 gabung")
def gabung(nomor: str, masukan: GabungMasukan, pengguna: Pengguna = Depends(admin)):
    return layanan.gabung(nomor, masukan.induk_nomor, pengguna.id)


@router.post("/api/admin/laporan/{nomor}/tingkat", response_model=AksiKeluaran, summary="FR-MOD-03 koreksi tingkat")
def koreksi(nomor: str, masukan: KoreksiMasukan, pengguna: Pengguna = Depends(admin)):
    raise BelumDibuat("US-21", "M5")


@router.get("/api/admin/laporan/{nomor}/paket", response_model=PaketKeluaran, summary="FR-MOD-04 paket penerusan")
def paket(nomor: str, pengguna: Pengguna = Depends(admin)):
    raise BelumDibuat("US-14", "M5")


@router.post("/api/laporan/{nomor}/banding", response_model=AksiKeluaran, summary="FR-MOD-02 minta peninjauan (sekali)")
def banding(nomor: str, pengguna: Pengguna = Depends(wajib_terverifikasi)):
    raise BelumDibuat("US-13", "M5")
