"""Endpoint modul laporan: detail publik (FR-LAP-05) dan berkas foto (BR-06)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from jalanku.core import BelumDibuat, TidakDitemukan, jalur_berkas
from jalanku.modules.akun import Pengguna, pengguna_opsional

from . import layanan
from .skema import DetailLaporanKeluaran, EntriTimelineKeluaran, FotoKeluaran, JejakKeluaran
from .tipe import STATUS_PUBLIK

router = APIRouter(tags=["laporan"])


@router.get("/api/laporan/{nomor}", response_model=DetailLaporanKeluaran, summary="FR-LAP-05 detail + timeline")
def detail(nomor: str, penonton: Pengguna | None = Depends(pengguna_opsional)):
    lap = layanan.ambil_untuk_penonton(nomor, penonton)
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
                hasil_ai=f.hasil_ai if layanan.boleh_lihat_hasil_ai(lap, f, penonton) else None,
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
    raise BelumDibuat("US-32", "M1")


@router.get("/api/foto/{foto_id}", response_class=FileResponse, summary="Berkas foto (tanpa EXIF) sesuai visibilitas")
def foto(foto_id: int, penonton: Pengguna | None = Depends(pengguna_opsional)):
    f = layanan.ambil_foto(foto_id)
    lap = layanan.laporan_dari_foto(f)
    if not layanan.boleh_dilihat(lap, penonton):
        raise TidakDitemukan("Foto tidak ditemukan.")
    # Laporan publik tidak pernah kembali privat (BR-03), jadi fotonya aman di-cache bersama.
    # Foto laporan privat tidak boleh tersimpan di cache browser/proxy mana pun.
    cache = "public, max-age=86400" if lap.status in STATUS_PUBLIK else "private, no-store"
    return FileResponse(jalur_berkas(f.berkas), media_type="image/jpeg", headers={"Cache-Control": cache})
