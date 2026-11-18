"""Endpoint notifikasi. Pemilik: M1. STUB: 501."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from jalanku.core import BelumDibuat
from jalanku.modules.akun import Pengguna, wajib_masuk

from .skema import KabarKeluaran, PengaturanNotifikasi

router = APIRouter(prefix="/api/notifikasi", tags=["notifikasi"])


@router.get("", response_model=list[KabarKeluaran], summary="FR-NTF-01 daftar kabar")
def daftar(pengguna: Pengguna = Depends(wajib_masuk)):
    raise BelumDibuat("US-25", "M1")


@router.post("/{kabar_id}/dibaca", response_model=KabarKeluaran, summary="Tandai sudah dibaca")
def dibaca(kabar_id: int, pengguna: Pengguna = Depends(wajib_masuk)):
    raise BelumDibuat("US-25", "M1")


@router.put("/pengaturan", response_model=PengaturanNotifikasi, summary="Nyalakan/matikan notifikasi")
def pengaturan_notifikasi(masukan: PengaturanNotifikasi, pengguna: Pengguna = Depends(wajib_masuk)):
    raise BelumDibuat("US-25", "M1")
