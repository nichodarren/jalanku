"""Orkestrasi alur warga melapor (UC-02, US-03). Pemilik: M3.

Modul ini hanya merangkai modul lain lewat antarmuka publiknya:
batasi → validasi → wilayah → duplikat (25 m) → ai per foto → keputusan → ``laporan.buat_laporan``.

Diport (logika validasi & urutan langkah) dari jalanku-v0@65db419 ``app/jalanku/reports.py``
(``validasi_data``) dan ``app/jalanku/api.py`` (``POST /api/laporan``), karya Yosua. Penyimpanan
langsung ke DB dan hitungan rate limit lewat SQL diganti dengan ``laporan.buat_laporan`` dan ``core.batasi``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from jalanku.core import TidakValid, batasi
from jalanku.modules.ai import periksa_foto, putuskan
from jalanku.modules.akun import Pengguna
from jalanku.modules.laporan import (
    STATUS_BELUM,
    STATUS_DITOLAK,
    Laporan,
    LaporanBaru,
    buat_laporan,
    cari_aktif_dekat,
    jumlah_dukungan,
)
from jalanku.modules.wilayah import KANAL_LUAR_WILAYAH, Instansi, tentukan_wilayah

log = logging.getLogger("jalanku.pelaporan")

MAKS_FOTO = 3
MAKS_BYTE_FOTO = 10 * 1024 * 1024
MAKS_KETERANGAN = 280
BATAS_LAPORAN_PER_JAM = 10
JENDELA_DETIK = 3600
RADIUS_DUPLIKAT_M = 25
SUMBER_LOKASI = ("exif", "gps", "manual")


@dataclass(frozen=True)
class KandidatDuplikat:
    nomor: str
    jarak_m: float
    status: str
    tingkat: str | None
    jumlah_dukungan: int


class DuplikatDitemukan(Exception):  # noqa: N818  (bukan galat domain: membawa data untuk respons 409)
    """Ada laporan aktif ≤ 25 m dan pelapor belum memilih mengabaikannya (BR-02)."""

    def __init__(self, kandidat: list[KandidatDuplikat]):
        super().__init__("Kerusakan ini mungkin sudah dilaporkan.")
        self.kandidat = kandidat


@dataclass(frozen=True)
class HasilKirim:
    laporan: Laporan
    instansi: Instansi
    pesan: str


def _jenis_gambar(data: bytes) -> bool:
    """Tanda tangan berkas JPEG / PNG / WebP. Validasi isi mendalam dilakukan modul laporan (TS-02)."""
    return (
        data.startswith(b"\xff\xd8\xff")
        or data.startswith(b"\x89PNG\r\n\x1a\n")
        or (data[:4] == b"RIFF" and data[8:12] == b"WEBP")
    )


def validasi_masukan(foto: list[bytes], lat: float, lon: float, sumber_lokasi: str, keterangan: str) -> None:
    """Validasi di server (tidak percaya klien). Lempar ``TidakValid`` (400) dengan pesan bahasa awam."""
    if len(foto) < 1:
        raise TidakValid("Tambahkan minimal 1 foto jalan.")
    if len(foto) > MAKS_FOTO:
        raise TidakValid(f"Maksimal {MAKS_FOTO} foto per laporan.")
    for data in foto:
        if len(data) > MAKS_BYTE_FOTO:
            raise TidakValid("Ukuran satu foto maksimal 10 MB.")
        if not _jenis_gambar(data):
            raise TidakValid("File harus berupa foto JPEG, PNG, atau WebP.")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise TidakValid("Koordinat lokasi tidak valid.")
    if sumber_lokasi not in SUMBER_LOKASI:
        raise TidakValid("Sumber lokasi tidak dikenal.")
    if len(keterangan) > MAKS_KETERANGAN:
        raise TidakValid(f"Keterangan maksimal {MAKS_KETERANGAN} karakter.")


def _pesan(laporan: Laporan, instansi: Instansi) -> str:
    if laporan.status == STATUS_BELUM:
        return f"Terima kasih! Laporanmu sudah diteruskan ke {instansi.nama_pendek}."
    if laporan.status == STATUS_DITOLAK:
        return "AI menilai jalan ini masih baik, jadi laporan tidak diteruskan. Kamu bisa mengajukan banding sekali."
    return "Terima kasih! Laporanmu sedang diperiksa Admin sebelum diteruskan."


def kirim_laporan(
    pengguna: Pengguna,
    foto: list[bytes],
    lat: float,
    lon: float,
    sumber_lokasi: str,
    akurasi_gps: float | None = None,
    keterangan: str = "",
    abaikan_duplikat: bool = False,
) -> HasilKirim:
    """Alur UC-02. Urutan sesuai M3.md; tiap langkah gagal cepat dengan galat domain."""
    batasi(
        f"laporan:{pengguna.id}",
        BATAS_LAPORAN_PER_JAM,
        JENDELA_DETIK,
        "Batas 10 laporan per jam tercapai. Coba lagi nanti.",
    )
    keterangan = keterangan.strip()
    validasi_masukan(foto, lat, lon, sumber_lokasi, keterangan)

    wilayah = tentukan_wilayah(lat, lon)
    if not wilayah.di_dalam or wilayah.instansi is None:
        nama, url = KANAL_LUAR_WILAYAH
        raise TidakValid(
            f"Lokasi ini di luar wilayah layanan JalanKu (DKI Jakarta daratan). Silakan lapor lewat {nama} di {url}."
        )

    if not abaikan_duplikat:
        dekat = cari_aktif_dekat(lat, lon, RADIUS_DUPLIKAT_M)
        if dekat:
            raise DuplikatDitemukan(
                [
                    KandidatDuplikat(lap.nomor, round(jarak, 1), lap.status, lap.tingkat, jumlah_dukungan(lap.id))
                    for lap, jarak in dekat
                ]
            )

    hasil_foto = [periksa_foto(data) for data in foto]
    keputusan = putuskan(hasil_foto)
    laporan = buat_laporan(
        LaporanBaru(
            pelapor_id=pengguna.id,
            lat=lat,
            lon=lon,
            sumber_lokasi=sumber_lokasi,
            kota=wilayah.kota,
            kecamatan=wilayah.kecamatan,
            instansi_id=wilayah.instansi.id,
            foto=foto,
            keputusan_ai=keputusan.keputusan,
            tingkat=keputusan.tingkat,
            hasil_ai=[h.sebagai_dict() for h in keputusan.hasil_foto],
            akurasi_gps=akurasi_gps,
            keterangan=keterangan,
            versi_model=keputusan.versi_model,
        )
    )
    log.info("Laporan %s dibuat (status %s)", laporan.nomor, laporan.status)
    return HasilKirim(laporan=laporan, instansi=wilayah.instansi, pesan=_pesan(laporan, wilayah.instansi))
