"""Endpoint alur warga. Pemilik: M3.

STUB: semua endpoint mengembalikan 501. Orkestrasi yang diharapkan untuk POST /api/laporan
(UC-02): batasi 10/jam → wilayah.tentukan_wilayah → cek duplikat (laporan.cari_aktif_dekat)
→ ai.periksa_foto per foto → ai.putuskan → laporan.buat_laporan(LaporanBaru(...)).
"""

from __future__ import annotations

from dataclasses import asdict

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from jalanku.core import BelumDibuat
from jalanku.modules.akun import Pengguna, wajib_masuk, wajib_terverifikasi

from .layanan import MAKS_BYTE_FOTO, DuplikatDitemukan, dukung_laporan
from .layanan import kirim_laporan as kirim
from .layanan import pratinjau_lokasi as pratinjau
from .skema import (
    DukunganKeluaran,
    DuplikatKeluaran,
    HasilKirimKeluaran,
    InstansiRingkas,
    KanalLuar,
    LaporanSayaKeluaran,
    LokasiMasukan,
    PratinjauLokasiKeluaran,
)

router = APIRouter(tags=["pelaporan"])


@router.post("/api/lokasi", response_model=PratinjauLokasiKeluaran, summary="FR-WIL-01/02 + FR-PEL-05 pratinjau lokasi")
def pratinjau_lokasi(masukan: LokasiMasukan):
    hasil = pratinjau(masukan.lat, masukan.lon, masukan.akurasi_gps)
    inst = hasil.wilayah.instansi
    return PratinjauLokasiKeluaran(
        di_dalam=hasil.wilayah.di_dalam,
        kota=hasil.wilayah.kota,
        kecamatan=hasil.wilayah.kecamatan,
        instansi=InstansiRingkas(
            id=inst.id, nama_pendek=inst.nama_pendek, kanal_nama=inst.kanal_nama, kanal_url=inst.kanal_url
        )
        if inst
        else None,
        perlu_konfirmasi_pin=hasil.perlu_konfirmasi_pin,
        kanal_luar=KanalLuar(nama=hasil.kanal_luar[0], url=hasil.kanal_luar[1]) if hasil.kanal_luar else None,
        duplikat=[DuplikatKeluaran(**asdict(k)) for k in hasil.duplikat],
    )


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
    # Baca satu byte lebih dari batas supaya foto > 10 MB terdeteksi tanpa memuat seluruh berkasnya.
    data = [await f.read(MAKS_BYTE_FOTO + 1) for f in foto]
    try:
        hasil = await run_in_threadpool(
            kirim,
            pengguna,
            data,
            lat,
            lon,
            sumber_lokasi,
            akurasi_gps,
            keterangan,
            abaikan_duplikat,
        )
    except DuplikatDitemukan as d:
        return JSONResponse(
            {
                "detail": "Kerusakan ini mungkin sudah dilaporkan. Dukung laporan yang sudah ada?",
                "duplikat": [asdict(k) for k in d.kandidat],
            },
            status_code=status.HTTP_409_CONFLICT,
        )
    lap = hasil.laporan
    return HasilKirimKeluaran(
        nomor=lap.nomor,
        status=lap.status,
        tingkat=lap.tingkat,
        instansi_id=hasil.instansi.id,
        instansi_nama=hasil.instansi.nama,
        url_status=f"/#/laporan/{lap.nomor}",
        pesan=hasil.pesan,
    )


@router.post("/api/laporan/{nomor}/dukung", response_model=DukunganKeluaran, summary="FR-PEL-06 dukung laporan")
def dukung(nomor: str, pengguna: Pengguna = Depends(wajib_terverifikasi)):
    hasil = dukung_laporan(pengguna, nomor)
    return DukunganKeluaran(nomor=hasil.nomor, jumlah_dukungan=hasil.jumlah_dukungan, baru=hasil.baru)


@router.get("/api/saya/laporan", response_model=list[LaporanSayaKeluaran], summary="FR-PEL-07 laporan saya")
def laporan_saya(pengguna: Pengguna = Depends(wajib_masuk)):
    raise BelumDibuat("US-11", "M3")
