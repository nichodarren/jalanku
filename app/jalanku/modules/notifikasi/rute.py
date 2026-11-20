"""Endpoint notifikasi (US-25). Pemilik: M1. Semua hanya untuk pengguna yang masuk, atas datanya sendiri."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from jalanku.core import TidakDitemukan
from jalanku.modules.akun import Pengguna, wajib_masuk

from . import layanan
from .skema import KabarKeluaran, PengaturanNotifikasi

router = APIRouter(prefix="/api/notifikasi", tags=["notifikasi"])


@router.get("", response_model=list[KabarKeluaran], summary="FR-NTF-01 daftar kabar")
def daftar(pengguna: Pengguna = Depends(wajib_masuk)):
    return [KabarKeluaran(**k.__dict__) for k in layanan.daftar_kabar(pengguna.id)]


@router.post("/{kabar_id}/dibaca", response_model=KabarKeluaran, summary="Tandai sudah dibaca")
def dibaca(kabar_id: int, pengguna: Pengguna = Depends(wajib_masuk)):
    kabar = layanan.tandai_dibaca(pengguna.id, kabar_id)
    if kabar is None:
        raise TidakDitemukan("Kabar tidak ditemukan.")  # 404 juga untuk kabar milik orang lain
    return KabarKeluaran(**kabar.__dict__)


@router.get("/pengaturan", response_model=PengaturanNotifikasi, summary="Status notifikasi pengguna ini")
def lihat_pengaturan(pengguna: Pengguna = Depends(wajib_masuk)):
    return PengaturanNotifikasi(aktif=layanan.aktif(pengguna.id))


@router.put("/pengaturan", response_model=PengaturanNotifikasi, summary="Nyalakan/matikan notifikasi")
def pengaturan_notifikasi(masukan: PengaturanNotifikasi, pengguna: Pengguna = Depends(wajib_masuk)):
    return PengaturanNotifikasi(aktif=layanan.atur_aktif(pengguna.id, masukan.aktif))
