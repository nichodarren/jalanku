"""Endpoint dashboard petugas (US-18, US-19). Pemilik: M6. Logika ada di ``layanan.py``.

Otorisasi wilayah (NFR-SEC-01) dicek di server dengan ``wilayah.boleh_menangani`` sebelum
``laporan.ubah_status(..., pelaku=PELAKU_PETUGAS)``.
TODO(US-31): saat Selesai, periksa foto sesudah dengan ``ai.periksa_foto`` dan kirim hasilnya lewat
``hasil_ai_sesudah``; bila AI tidak menilai jalan sudah baik, tandai untuk ditinjau Admin.
TODO(US-20): ``urut=prioritas`` dengan skor BR-05 (saat ini 501).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile

from jalanku.core import TidakValid
from jalanku.modules.akun import PERAN_PETUGAS, Pengguna, wajib_peran

from . import layanan
from .skema import ItemPetugasKeluaran, StatusPetugasKeluaran

router = APIRouter(tags=["penanganan"])
petugas = wajib_peran(PERAN_PETUGAS)
UKURAN_FOTO_MAKS = 10 * 1024 * 1024  # NFR-PERF-03, sama dengan modul ai


@router.get("/api/petugas/laporan", response_model=list[ItemPetugasKeluaran], summary="FR-TGN-01/03 laporan wilayahku")
def daftar(status: str | None = None, urut: str = "waktu", pengguna: Pengguna = Depends(petugas)):
    return layanan.daftar_laporan(pengguna, status, urut)


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
    data = None
    if foto is not None:
        data = await foto.read(UKURAN_FOTO_MAKS + 1)  # baca terbatas supaya memori aman
        if len(data) > UKURAN_FOTO_MAKS:
            raise TidakValid("Ukuran foto maksimal 10 MB.")
    return layanan.ubah_status_petugas(pengguna, nomor, ke, catatan, data)
