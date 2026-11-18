"""Data contoh BERLABEL SIMULASI untuk mengembangkan modul tanpa menunggu modul lain.

Semua laporan dibuat dengan ``simulasi=True`` dan foto bertuliskan "SIMULASI". Tidak boleh dipakai
sebagai bukti hasil uji (aturan integritas: CONTRIBUTING.md). Hanya memakai antarmuka publik modul.
"""

from __future__ import annotations

import io
import random

from PIL import Image, ImageDraw

from jalanku.core import TidakValid, pengaturan
from jalanku.modules import laporan, wilayah
from jalanku.modules.akun import layanan as _akun_dev  # masuk_dev hanya untuk dev/test


def _foto_simulasi(teks: str) -> bytes:
    gambar = Image.new("RGB", (480, 360), (110, 110, 110))
    gores = ImageDraw.Draw(gambar)
    gores.text((20, 20), f"SIMULASI\n{teks}", fill=(255, 255, 255))
    buf = io.BytesIO()
    gambar.save(buf, "JPEG", quality=70)
    return buf.getvalue()


def buat_contoh_data(jumlah: int = 30, benih: int = 7) -> list[str]:
    if pengaturan().produksi:
        raise TidakValid("Data contoh tidak boleh dibuat di produksi.")
    acak = random.Random(benih)  # noqa: S311 - bukan kriptografi
    pelapor, _ = _akun_dev.masuk_dev("warga.simulasi@contoh.test", "pelapor", nama="Warga Simulasi")
    petugas, _ = _akun_dev.masuk_dev(
        "petugas.simulasi@contoh.test", "petugas", instansi_id="DINAS_BM", nama="Petugas Simulasi"
    )
    nomor = []
    for i in range(jumlah):
        lat = acak.uniform(-6.30, -6.12)
        lon = acak.uniform(106.72, 106.94)
        w = wilayah.tentukan_wilayah(lat, lon)
        if not w.di_dalam or w.instansi is None:
            continue
        yakin = acak.random() < 0.7
        lap = laporan.buat_laporan(
            laporan.LaporanBaru(
                pelapor_id=pelapor.id,
                lat=lat,
                lon=lon,
                sumber_lokasi=acak.choice(["exif", "gps", "manual"]),
                kota=w.kota,
                kecamatan=w.kecamatan,
                instansi_id=w.instansi.id,
                foto=[_foto_simulasi(f"contoh {i + 1}")],
                keputusan_ai="terverifikasi" if yakin else "perlu_admin",
                tingkat=acak.choice([laporan.TINGKAT_KURANG_BAIK, laporan.TINGKAT_RUSAK]) if yakin else None,
                keterangan="Data simulasi untuk pengembangan",
                simulasi=True,
            )
        )
        if lap.status == laporan.STATUS_BELUM and acak.random() < 0.4:
            lap = laporan.ubah_status(lap.nomor, laporan.STATUS_SEDANG, laporan.PELAKU_PETUGAS, pengguna_id=petugas.id)
            if acak.random() < 0.5:
                laporan.ubah_status(
                    lap.nomor,
                    laporan.STATUS_SELESAI,
                    laporan.PELAKU_PETUGAS,
                    pengguna_id=petugas.id,
                    foto_sesudah=_foto_simulasi("sesudah perbaikan"),
                )
        nomor.append(lap.nomor)
    return nomor
