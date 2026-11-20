"""Endpoint modul laporan: detail publik (FR-LAP-05) dan berkas foto (BR-06)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from jalanku.core import TidakDitemukan, jalur_berkas
from jalanku.modules.akun import PERAN_ADMIN, Pengguna, pengguna_opsional

from . import layanan
from .skema import DetailLaporanKeluaran, EntriJejakKeluaran, EntriTimelineKeluaran, FotoKeluaran, JejakKeluaran

router = APIRouter(tags=["laporan"])


@router.get("/api/laporan/{nomor}", response_model=DetailLaporanKeluaran, summary="FR-LAP-05 detail + timeline")
def detail(nomor: str, penonton: Pengguna | None = Depends(pengguna_opsional)):
    lap = layanan.ambil_untuk_penonton(nomor, penonton)
    lihat_ai = penonton is not None and (penonton.peran == PERAN_ADMIN or penonton.id == lap.pelapor_id)
    return DetailLaporanKeluaran(
        nomor=lap.nomor,
        status=lap.status,
        tingkat=lap.tingkat,
        lat=lap.lat,
        lon=lap.lon,
        kota=lap.kota,
        kecamatan=lap.kecamatan,
        instansi_id=lap.instansi_id,
        keterangan=lap.keterangan,
        diperiksa_oleh=lap.diperiksa_oleh,
        jumlah_dukungan=layanan.jumlah_dukungan(lap.id),
        simulasi=lap.simulasi,
        dibuat_pada=lap.dibuat_pada,
        diverifikasi_pada=lap.diverifikasi_pada,
        mulai_dikerjakan_pada=lap.mulai_dikerjakan_pada,
        selesai_pada=lap.selesai_pada,
        foto=[
            FotoKeluaran(
                id=f.id,
                jenis=f.jenis,
                url=f"/api/foto/{f.id}",
                hasil_ai=f.hasil_ai if (lihat_ai or f.jenis == "sesudah") else None,  # bukti perbaikan publik
            )
            for f in layanan.daftar_foto(lap.id)
        ],
        timeline=[EntriTimelineKeluaran(**e.__dict__) for e in layanan.timeline(lap.id)],
    )


@router.get(
    "/api/laporan/{nomor}/jejak",
    response_model=JejakKeluaran,
    summary="US-32 jejak audit anti-ubah (rantai hash timeline)",
)
def jejak(nomor: str, penonton: Pengguna | None = Depends(pengguna_opsional)):
    lap = layanan.ambil_untuk_penonton(nomor, penonton)  # BR-06: sama dengan detail (404 bila tidak boleh)
    utuh, entri = layanan.periksa_jejak(lap)
    return JejakKeluaran(nomor=lap.nomor, utuh=utuh, entri=[EntriJejakKeluaran(**e) for e in entri])


@router.get("/api/foto/{foto_id}", response_class=FileResponse, summary="Berkas foto (tanpa EXIF) sesuai visibilitas")
def foto(foto_id: int, penonton: Pengguna | None = Depends(pengguna_opsional)):
    f = layanan.ambil_foto(foto_id)
    if not layanan.boleh_dilihat(layanan.laporan_dari_foto(f), penonton):
        raise TidakDitemukan("Foto tidak ditemukan.")
    return FileResponse(
        jalur_berkas(f.berkas), media_type="image/jpeg", headers={"Cache-Control": "private, max-age=300"}
    )
