"""Endpoint data peta publik. Pemilik: M6. STUB: 501.

Petunjuk: aktif = laporan.cari_laporan(status=(STATUS_BELUM, STATUS_SEDANG)); riwayat = STATUS_SELESAI.
Jangan pernah menyertakan pelapor_id (NFR-PRI-01).
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter

from jalanku.core import BelumDibuat

from .skema import TitikPetaKeluaran

router = APIRouter(tags=["peta"])


@router.get("/api/peta", response_model=list[TitikPetaKeluaran], summary="FR-PETA-01/02 data bubble")
def data_peta(mode: Literal["aktif", "riwayat"] = "aktif", kota: str | None = None, tingkat: str | None = None):
    raise BelumDibuat("US-15 / US-16", "M6")
