"""Logika dashboard petugas: US-18 (laporan wilayahnya) dan US-19 (ubah status + foto). Pemilik: M6.

Diport dari jalanku-v0 ``app/jalanku/reports.py`` (karya Yosua): ``daftar_petugas``, ``berwenang``,
``ubah_status_petugas``. Disesuaikan: data lewat antarmuka publik ``laporan`` (bukan SQL langsung),
wilayah dicek dengan ``wilayah.boleh_menangani`` yang sama untuk melihat dan mengubah (NFR-SEC-01),
dan perubahan status hanya lewat ``laporan.ubah_status`` (BR-03).
"""

from __future__ import annotations

from jalanku.core import BelumDibuat, TidakBerhak, TidakValid, pengaturan
from jalanku.modules.akun import Pengguna
from jalanku.modules.laporan import (
    PELAKU_PETUGAS,
    STATUS_BELUM,
    STATUS_SEDANG,
    STATUS_SELESAI,
    Laporan,
    ambil_laporan,
    cari_laporan,
    jumlah_dukungan,
    ubah_status,
)
from jalanku.modules.wilayah import boleh_menangani

STATUS_DASHBOARD = (STATUS_BELUM, STATUS_SEDANG, STATUS_SELESAI)
STATUS_TUJUAN = (STATUS_SEDANG, STATUS_SELESAI)
URUTAN = ("waktu", "prioritas")
BATAS_DAFTAR = 2000
PESAN_FOTO_WAJIB = "Lampirkan foto setelah perbaikan."


def _instansi(pengguna: Pengguna) -> str:
    if not pengguna.instansi_id:
        raise TidakBerhak("Akun petugas belum terhubung ke instansi. Hubungi Admin.")
    return pengguna.instansi_id


def _ke_item(lap: Laporan) -> dict:
    return {
        "nomor": lap.nomor,
        "status": lap.status,
        "tingkat": lap.tingkat,
        "lat": lap.lat,
        "lon": lap.lon,
        "kota": lap.kota,
        "kecamatan": lap.kecamatan,
        "jumlah_dukungan": jumlah_dukungan(lap.id),
        "diverifikasi_pada": lap.diverifikasi_pada,
        "skor_prioritas": None,  # US-20 (BR-05) menyusul di S3
    }


def daftar_laporan(pengguna: Pengguna, status: str | None = None, urut: str = "waktu") -> list[dict]:
    """US-18: laporan terverifikasi di wilayah instansi petugas (DINAS_BM: semua wilayah).

    Menunggu verifikasi dan Ditolak tidak pernah tampil. Urutan ``waktu`` = terverifikasi terbaru dulu.
    """
    instansi_id = _instansi(pengguna)
    if status is not None and status not in STATUS_DASHBOARD:
        raise TidakValid("Filter status tidak dikenal.")
    if urut not in URUTAN:
        raise TidakValid("Urutan tidak dikenal (pakai waktu atau prioritas).")
    if urut == "prioritas":
        raise BelumDibuat("US-20", "M6")
    hasil = [
        lap
        for lap in cari_laporan(status=status or STATUS_DASHBOARD, batas=BATAS_DAFTAR)
        if boleh_menangani(instansi_id, lap.kota)
    ]
    hasil.sort(key=lambda lap: (lap.diverifikasi_pada or "", lap.id), reverse=True)
    return [_ke_item(lap) for lap in hasil]


def ubah_status_petugas(pengguna: Pengguna, nomor: str, ke: str, catatan: str = "", foto: bytes | None = None) -> dict:
    """US-19: petugas menandai Sedang Dikerjakan / Selesai.

    Urutan cek: tujuan sah, laporan ada (404), wilayah (403), foto wajib saat Selesai (400).
    Wilayah dicek sebelum foto supaya petugas wilayah lain tidak mendapat petunjuk apa pun.
    Syarat transisi (mis. Belum langsung ke Selesai) ditegakkan ``laporan.ubah_status`` (409).
    """
    instansi_id = _instansi(pengguna)
    if ke not in STATUS_TUJUAN:
        raise TidakValid("Status tujuan hanya boleh Sedang Dikerjakan atau Selesai.")
    lap = ambil_laporan(nomor)
    if not boleh_menangani(instansi_id, lap.kota):
        raise TidakBerhak("Laporan ini bukan wilayah instansimu.")
    if ke == STATUS_SELESAI and not foto and pengaturan().wajib_foto_selesai:
        raise TidakValid(PESAN_FOTO_WAJIB)
    baru = ubah_status(
        nomor,
        ke,
        PELAKU_PETUGAS,
        pengguna_id=pengguna.id,
        catatan=catatan.strip(),
        foto_sesudah=foto or None,
    )
    return {"nomor": baru.nomor, "status": baru.status, "verifikasi_foto": None}  # US-31 menyusul
