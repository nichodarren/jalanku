from __future__ import annotations

import io

import pytest
from PIL import Image

from jalanku.modules.laporan import (
    STATUS_BELUM,
    STATUS_MENUNGGU,
    LaporanBaru,
    buat_laporan,
    ubah_status,
)
from jalanku.modules.laporan.tipe import PELAKU_ADMIN, PELAKU_PELAPOR


def buat_jpeg_bytes(warna: tuple[int, int, int] = (120, 120, 120), ukuran: tuple[int, int] = (64, 64)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", ukuran, warna).save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture
def bikin_laporan():
    def _bikin(
        *,
        lat: float = -6.1754,
        lon: float = 106.8272,
        pelapor_id: int | None = 1,
        keputusan_ai: str = "perlu_admin",
        tingkat: str | None = None,
        keterangan: str = "Jalan berlubang",
        kota: str | None = "Jakarta Pusat",
        kecamatan: str | None = "Gambir",
        instansi_id: str = "SUDIN_JP",
        hasil_ai: list[dict] | None = None,
        banding: bool = False,
        status_awal: str | None = None,
    ):
        foto = [buat_jpeg_bytes()]
        ai_list = hasil_ai if hasil_ai is not None else [{"kelas": "rusak", "confidence": 0.55}]
        if banding:
            lap_ditolak = buat_laporan(
                LaporanBaru(
                    pelapor_id=pelapor_id,
                    lat=lat,
                    lon=lon,
                    sumber_lokasi="manual",
                    kota=kota,
                    kecamatan=kecamatan,
                    instansi_id=instansi_id,
                    foto=foto,
                    keputusan_ai="ditolak",
                    keterangan=keterangan,
                )
            )
            return ubah_status(
                lap_ditolak.nomor,
                STATUS_MENUNGGU,
                PELAKU_PELAPOR,
                pengguna_id=pelapor_id,
                catatan="Banding",
            )
        lap = buat_laporan(
            LaporanBaru(
                pelapor_id=pelapor_id,
                lat=lat,
                lon=lon,
                sumber_lokasi="manual",
                kota=kota,
                kecamatan=kecamatan,
                instansi_id=instansi_id,
                foto=foto,
                keputusan_ai=keputusan_ai,
                tingkat=tingkat,
                hasil_ai=ai_list,
                keterangan=keterangan,
            )
        )
        if status_awal == STATUS_BELUM:
            return ubah_status(lap.nomor, STATUS_BELUM, PELAKU_ADMIN, tingkat="rusak", catatan="Verif")
        return lap

    return _bikin
