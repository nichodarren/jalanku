"""Statistik per Sudin (US-23, FR-STAT-01, BR-04). Pemilik: M5.

Data laporan diambil lewat antarmuka publik ``laporan.cari_laporan`` (bukan query tabel laporan) dan
daftar instansi lewat ``wilayah.daftar_instansi``. Waktu tunggu dihitung dari saat terverifikasi.
"""

from __future__ import annotations

import statistics
from datetime import timedelta

from jalanku.core import TidakValid, ke_datetime, sekarang
from jalanku.modules.laporan import STATUS_BELUM, STATUS_SEDANG, STATUS_SELESAI, Laporan, cari_laporan
from jalanku.modules.wilayah import daftar_instansi

N_MINIMUM = 5  # BR-04: median hanya bila n >= 5
HARI_MIN, HARI_MAKS = 1, 365
STATUS_DIHITUNG = (STATUS_BELUM, STATUS_SEDANG, STATUS_SELESAI)
KEPUTUSAN_OTOMATIS = ("terverifikasi", "ditolak")
SEMUA_LAPORAN = 1_000_000  # batas atas cari_laporan; volume MVP jauh di bawah ini
LABEL_SIMULASI = True  # BR-04: selama petugas diperankan tim proyek


def _jam(mulai: str, akhir: str) -> float:
    return (ke_datetime(akhir) - ke_datetime(mulai)).total_seconds() / 3600


def _median(nilai: list[float]) -> float | None:
    return round(statistics.median(nilai), 1) if len(nilai) >= N_MINIMUM else None


def _ringkas_instansi(instansi_id: str, nama_pendek: str, laporan: list[Laporan]) -> dict:
    dikerjakan = [
        _jam(lap.diverifikasi_pada, lap.mulai_dikerjakan_pada or lap.selesai_pada)
        for lap in laporan
        if lap.mulai_dikerjakan_pada or lap.selesai_pada
    ]
    selesai = [_jam(lap.diverifikasi_pada, lap.selesai_pada) for lap in laporan if lap.selesai_pada]
    return {
        "instansi_id": instansi_id,
        "nama_pendek": nama_pendek,
        "jumlah_per_status": {s: sum(1 for lap in laporan if lap.status == s) for s in STATUS_DIHITUNG},
        "median_jam_dikerjakan": _median(dikerjakan),
        "median_jam_selesai": _median(selesai),
        "n_dikerjakan": len(dikerjakan),
        "n_selesai": len(selesai),
    }


def statistik(hari: int = 30) -> dict:
    """Ringkasan publik per Sudin untuk laporan yang terverifikasi dalam ``hari`` terakhir."""
    if not HARI_MIN <= hari <= HARI_MAKS:
        raise TidakValid(f"Periode harus {HARI_MIN}–{HARI_MAKS} hari.")
    batas = ke_datetime(sekarang()) - timedelta(days=hari)
    semua = cari_laporan(batas=SEMUA_LAPORAN)

    dalam_periode = [lap for lap in semua if ke_datetime(lap.dibuat_pada) >= batas]
    otomatis = sum(1 for lap in dalam_periode if lap.keputusan_ai in KEPUTUSAN_OTOMATIS)
    persen_ai = round(100 * otomatis / len(dalam_periode), 1) if dalam_periode else None

    terverifikasi = [
        lap
        for lap in semua
        if lap.diverifikasi_pada and lap.status in STATUS_DIHITUNG and ke_datetime(lap.diverifikasi_pada) >= batas
    ]
    instansi = [
        _ringkas_instansi(i.id, i.nama_pendek, [lap for lap in terverifikasi if lap.instansi_id == i.id])
        for i in daftar_instansi()
        if i.kota is not None  # hanya Sudin; Dinas provinsi tidak menangani laporan langsung
    ]
    return {
        "label_simulasi": LABEL_SIMULASI,
        "periode_hari": hari,
        "persen_diputuskan_ai": persen_ai,
        "instansi": instansi,
    }
