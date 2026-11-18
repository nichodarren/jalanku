"""Tipe & konstanta publik domain laporan. Nilai string = istilah resmi proyek (lihat README.id.md, bagian Istilah)."""

from __future__ import annotations

from dataclasses import dataclass, field

STATUS_MENUNGGU = "menunggu_verifikasi"
STATUS_BELUM = "belum_dikerjakan"
STATUS_SEDANG = "sedang_dikerjakan"
STATUS_SELESAI = "selesai"
STATUS_DITOLAK = "ditolak"
STATUS_DIGABUNG = "digabung"

STATUS_AKTIF = (STATUS_MENUNGGU, STATUS_BELUM, STATUS_SEDANG)  # dipakai BR-02 (duplikat)
STATUS_PUBLIK = (STATUS_BELUM, STATUS_SEDANG, STATUS_SELESAI, STATUS_DIGABUNG)  # BR-06

TINGKAT_KURANG_BAIK = "kurang_baik"
TINGKAT_RUSAK = "rusak"
URUTAN_TINGKAT = {TINGKAT_KURANG_BAIK: 1, TINGKAT_RUSAK: 2}

PELAKU_AI = "ai"
PELAKU_ADMIN = "admin"
PELAKU_PETUGAS = "petugas"
PELAKU_PELAPOR = "pelapor"
PELAKU_SISTEM = "sistem"


@dataclass(frozen=True)
class Laporan:
    id: int
    nomor: str
    pelapor_id: int | None
    lat: float
    lon: float
    akurasi_gps: float | None
    sumber_lokasi: str
    kota: str | None
    kecamatan: str | None
    instansi_id: str
    status: str
    tingkat: str | None
    keterangan: str
    diperiksa_oleh: str | None
    keputusan_ai: str | None
    versi_model: str | None
    label_akhir: str | None
    induk_id: int | None
    banding_pada: str | None
    simulasi: bool
    dibuat_pada: str
    diverifikasi_pada: str | None
    mulai_dikerjakan_pada: str | None
    selesai_pada: str | None


@dataclass(frozen=True)
class Foto:
    id: int
    laporan_id: int
    jenis: str  # "bukti" | "sesudah"
    berkas: str
    hasil_ai: dict | None


@dataclass(frozen=True)
class EntriTimeline:
    dari_status: str | None
    ke_status: str
    pelaku: str
    catatan: str
    waktu: str


@dataclass(frozen=True)
class LaporanBaru:
    """Data untuk ``buat_laporan``. Dirakit modul pelaporan dari hasil wilayah + ai."""

    pelapor_id: int | None
    lat: float
    lon: float
    sumber_lokasi: str  # "exif" | "gps" | "manual"
    kota: str | None
    kecamatan: str | None
    instansi_id: str
    foto: list[bytes]
    keputusan_ai: str  # "terverifikasi" | "ditolak" | "perlu_admin" | "tidak_aktif"
    tingkat: str | None = None  # wajib bila keputusan_ai == "terverifikasi"
    hasil_ai: list[dict] = field(default_factory=list)  # satu dict per foto, urutan sama dengan foto
    akurasi_gps: float | None = None
    keterangan: str = ""
    versi_model: str | None = None
    simulasi: bool = False


@dataclass(frozen=True)
class LaporanDibuat:
    """Kejadian: laporan baru tersimpan."""

    laporan_id: int
    nomor: str
    status: str
    pelapor_id: int | None


@dataclass(frozen=True)
class StatusBerubah:
    """Kejadian: status laporan berubah (sudah tercatat di timeline)."""

    laporan_id: int
    nomor: str
    dari_status: str
    ke_status: str
    pelaku: str
    pelapor_id: int | None
