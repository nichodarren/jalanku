"""Endpoint modul ai."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, UploadFile

from jalanku.core import BelumDibuat, TidakValid, batasi
from jalanku.modules.akun import PERAN_ADMIN, Pengguna, wajib_peran, wajib_terverifikasi

from . import layanan
from .skema import HasilFotoKeluaran, InfoModelKeluaran, MetrikAIKeluaran

router = APIRouter(tags=["ai"])

UKURAN_MAKS = 10 * 1024 * 1024  # NFR-PERF-03


@router.get("/api/ai/info", response_model=InfoModelKeluaran, summary="Status & threshold model")
def info():
    return layanan.info_model()


@router.post(
    "/api/ai/periksa", response_model=HasilFotoKeluaran, summary="FR-AI-01 pratinjau satu foto (tidak disimpan)"
)
async def periksa(foto: UploadFile = File(...), pengguna: Pengguna = Depends(wajib_terverifikasi)):
    batasi(f"ai:{pengguna.id}", 60, 3600, "Batas pemeriksaan foto tercapai (60 per jam).")
    data = await foto.read(UKURAN_MAKS + 1)
    if len(data) > UKURAN_MAKS:
        raise TidakValid("Foto terlalu besar (maks 10 MB).")
    return layanan.periksa_foto(data).sebagai_dict()


@router.get("/api/admin/ai/metrik", response_model=MetrikAIKeluaran, summary="FR-AI-03 kinerja AI")
def metrik(hari: int = 30, admin: Pengguna = Depends(wajib_peran(PERAN_ADMIN))):
    raise BelumDibuat("US-22", "M4")


@router.get("/api/admin/ai/ekspor", summary="FR-AI-03 ekspor foto berlabel (zip)")
def ekspor(admin: Pengguna = Depends(wajib_peran(PERAN_ADMIN))):
    raise BelumDibuat("US-22", "M4")
