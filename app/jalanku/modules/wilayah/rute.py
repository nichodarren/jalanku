"""Endpoint modul wilayah."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from jalanku.core import BelumDibuat
from jalanku.modules.akun import PERAN_ADMIN, Pengguna, wajib_peran

from . import layanan
from .skema import InstansiKeluaran, UbahInstansiMasukan

router = APIRouter(tags=["wilayah"])


@router.get("/api/wilayah", summary="Batas kecamatan (GeoJSON) untuk peta")
def wilayah() -> dict:
    return layanan.batas_wilayah_geojson()


@router.get("/api/instansi", response_model=list[InstansiKeluaran], summary="Daftar instansi & kanal resmi")
def instansi():
    return [InstansiKeluaran(**i.__dict__) for i in layanan.daftar_instansi()]


@router.patch("/api/admin/instansi/{instansi_id}", response_model=InstansiKeluaran, summary="FR-WIL-03 ubah kanal")
def ubah_instansi(instansi_id: str, masukan: UbahInstansiMasukan, admin: Pengguna = Depends(wajib_peran(PERAN_ADMIN))):
    raise BelumDibuat("US-26", "M2")
