"""Endpoint dashboard petugas. Pemilik: M6. STUB: semua 501.

Otorisasi wilayah (NFR-SEC-01) wajib dicek di sini dengan ``wilayah.boleh_menangani``
sebelum memanggil ``laporan.ubah_status(..., pelaku=PELAKU_PETUGAS)``.
US-31: saat Selesai, periksa foto sesudah dengan ``ai.periksa_foto`` dan kirim hasilnya lewat
``hasil_ai_sesudah``; bila AI tidak menilai jalan sudah baik, tandai untuk ditinjau Admin.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from jalanku.core import BelumDibuat
from jalanku.modules.akun import PERAN_PETUGAS, Pengguna, wajib_peran

from .skema import ItemPetugasKeluaran, StatusPetugasKeluaran

router = APIRouter(tags=["penanganan"])
petugas = wajib_peran(PERAN_PETUGAS)


@router.get("/api/petugas/laporan", response_model=list[ItemPetugasKeluaran], summary="FR-TGN-01/03 laporan wilayahku")
def daftar(status: str | None = None, urut: str = "waktu", pengguna: Pengguna = Depends(petugas)):
    raise BelumDibuat("US-18", "M6")


@router.post(
    "/api/petugas/laporan/{nomor}/status", response_model=StatusPetugasKeluaran, summary="FR-TGN-02 ubah status"
)
async def ubah_status(
    nomor: str,
    ke: str = Form(..., description="sedang_dikerjakan | selesai"),
    catatan: str = Form("", max_length=200),
    foto: UploadFile | None = File(None, description="wajib bila ke=selesai (BR-08)"),
    pengguna: Pengguna = Depends(petugas),
):
    raise BelumDibuat("US-19", "M6")
