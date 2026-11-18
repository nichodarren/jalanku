"""Tipe publik modul ai (BR-07)."""

from __future__ import annotations

from dataclasses import dataclass, field

KELAS_BAIK = "baik"
KELAS_KURANG_BAIK = "kurang_baik"
KELAS_RUSAK = "rusak"

# Keputusan per foto
FOTO_TERIMA = "terima"
FOTO_TOLAK = "tolak"
FOTO_ADMIN = "admin"

# Keputusan per laporan (nilai sama dengan kolom laporan.keputusan_ai)
KEPUTUSAN_TERVERIFIKASI = "terverifikasi"
KEPUTUSAN_DITOLAK = "ditolak"
KEPUTUSAN_PERLU_ADMIN = "perlu_admin"
KEPUTUSAN_TIDAK_AKTIF = "tidak_aktif"


@dataclass(frozen=True)
class HasilFoto:
    kelas: str | None  # baik | kurang_baik | rusak | None (model tidak aktif)
    confidence: float | None
    kemiripan: float | None
    keputusan: str  # terima | tolak | admin
    alasan: str  # penjelasan bahasa awam (NFR-USA-03)
    probabilitas: dict[str, float] = field(default_factory=dict)

    def sebagai_dict(self) -> dict:
        return {
            "kelas": self.kelas,
            "confidence": self.confidence,
            "kemiripan": self.kemiripan,
            "keputusan": self.keputusan,
            "alasan": self.alasan,
            "probabilitas": dict(self.probabilitas),
        }


@dataclass(frozen=True)
class KeputusanAI:
    keputusan: str  # terverifikasi | ditolak | perlu_admin | tidak_aktif
    tingkat: str | None  # kurang_baik | rusak bila terverifikasi
    hasil_foto: list[HasilFoto]
    versi_model: str | None
