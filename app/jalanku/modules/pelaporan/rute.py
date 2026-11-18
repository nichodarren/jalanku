"""Endpoint alur warga. Pemilik: M3.

STUB: semua endpoint mengembalikan 501. Orkestrasi yang diharapkan untuk POST /api/laporan
(UC-02): batasi 10/jam → wilayah.tentukan_wilayah → cek duplikat (laporan.cari_aktif_dekat)
→ ai.periksa_foto per foto → ai.putuskan → laporan.buat_laporan(LaporanBaru(...)).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile, status

from jalanku.core import BelumDibuat
from jalanku.modules.akun import Pengguna, wajib_masuk, wajib_terverifikasi

from .skema import DukunganKeluaran, HasilKirimKeluaran, LaporanSayaKeluaran, LokasiMasukan, PratinjauLokasiKeluaran

router = APIRouter(tags=["pelaporan"])


@router.post("/api/lokasi", response_model=PratinjauLokasiKeluaran, summary="FR-WIL-01/02 + FR-PEL-05 pratinjau lokasi")
def pratinjau_lokasi(masukan: LokasiMasukan):
    raise BelumDibuat("US-07 / US-09", "M3 (memakai modul wilayah M2)")


@router.post(
    "/api/laporan",
    response_model=HasilKirimKeluaran,
    status_code=status.HTTP_201_CREATED,
    summary="FR-PEL-01..05 kirim laporan; 409 bila ada duplikat dan abaikan_duplikat=false",
)
async def kirim_laporan(
    foto: list[UploadFile] = File(..., description="1-3 foto JPEG/PNG/WebP, maks 10 MB"),
    lat: float = Form(...),
    lon: float = Form(...),
    sumber_lokasi: str = Form(..., description="exif | gps | manual"),
    akurasi_gps: float | None = Form(None),
    keterangan: str = Form("", max_length=280),
    abaikan_duplikat: bool = Form(False),
    pengguna: Pengguna = Depends(wajib_terverifikasi),
):
    raise BelumDibuat("US-03", "M3")


@router.post("/api/laporan/{nomor}/dukung", response_model=DukunganKeluaran, summary="FR-PEL-06 dukung laporan")
def dukung(nomor: str, pengguna: Pengguna = Depends(wajib_terverifikasi)):
    raise BelumDibuat("US-10", "M3")


@router.get("/api/saya/laporan", response_model=list[LaporanSayaKeluaran], summary="FR-PEL-07 laporan saya")
def laporan_saya(pengguna: Pengguna = Depends(wajib_masuk)):
    raise BelumDibuat("US-11", "M3")
