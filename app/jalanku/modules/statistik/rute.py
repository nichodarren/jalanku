"""Endpoint statistik publik & metrik A3. Pemilik: M5. STUB: 501."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from jalanku.core import BelumDibuat
from jalanku.modules.akun import Pengguna, pengguna_opsional

from . import layanan
from .skema import KejadianMasukan, StatistikKeluaran

router = APIRouter(tags=["statistik"])


@router.get("/api/statistik", response_model=StatistikKeluaran, summary="FR-STAT-01 statistik per Sudin")
def statistik(hari: int = 30):
    return layanan.statistik(hari)


@router.post(
    "/api/statistik/kejadian", status_code=status.HTTP_204_NO_CONTENT, summary="FR-STAT-02 catat kejadian anonim"
)
def catat(masukan: KejadianMasukan, pengguna: Pengguna | None = Depends(pengguna_opsional)):
    raise BelumDibuat("US-24", "M5")
