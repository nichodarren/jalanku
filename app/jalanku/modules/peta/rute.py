"""Endpoint data peta publik (US-15 aktif, US-16 riwayat). Pemilik: M6.

Publik tanpa login; hanya status publik yang tampil dan pelapor_id tidak pernah ikut (NFR-PRI-01).
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter

from .layanan import titik_peta
from .skema import TitikPetaKeluaran

router = APIRouter(tags=["peta"])


@router.get("/api/peta", response_model=list[TitikPetaKeluaran], summary="FR-PETA-01/02 data bubble")
def data_peta(mode: Literal["aktif", "riwayat"] = "aktif", kota: str | None = None, tingkat: str | None = None):
    # kota & tingkat boleh beberapa nilai dipisah koma (maks. 10). Sengaja tanpa docstring:
    # docstring ikut masuk OpenAPI dan mengubah snapshot kontrak.
    return titik_peta(mode, kota, tingkat)
