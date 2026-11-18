"""Konfigurasi aplikasi dari environment variable (12-factor: config).

Semua nama variabel diawali ``JALANKU_`` dan didokumentasikan di ``app/.env.example``.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

FOLDER_APP = Path(__file__).resolve().parents[2]  # .../app


def _bool(nama: str, bawaan: bool) -> bool:
    nilai = os.environ.get(nama)
    if nilai is None:
        return bawaan
    return nilai.strip().lower() in {"1", "true", "ya", "yes", "on"}


def _float(nama: str) -> float | None:
    nilai = os.environ.get(nama)
    return float(nilai) if nilai not in (None, "") else None


@dataclass(frozen=True)
class Pengaturan:
    mode: str  # "dev" | "test" | "prod"
    folder_data: Path
    url_dasar: str
    ai_aktif: bool
    ai_threshold_confidence: float | None
    ai_threshold_kemiripan: float | None
    wajib_foto_selesai: bool
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    email_pengirim: str

    @property
    def produksi(self) -> bool:
        return self.mode == "prod"

    @property
    def jalur_db(self) -> Path:
        return self.folder_data / "jalanku.db"

    @property
    def folder_berkas(self) -> Path:
        return self.folder_data / "berkas"


@lru_cache(maxsize=1)
def pengaturan() -> Pengaturan:
    mode = os.environ.get("JALANKU_MODE", "dev").strip().lower()
    if mode not in {"dev", "test", "prod"}:
        raise ValueError(f"JALANKU_MODE tidak dikenal: {mode!r} (pakai dev, test, atau prod)")
    return Pengaturan(
        mode=mode,
        folder_data=Path(os.environ.get("JALANKU_DATA", FOLDER_APP / "var")),
        url_dasar=os.environ.get("JALANKU_URL_DASAR", "http://localhost:8000").rstrip("/"),
        ai_aktif=_bool("JALANKU_AI_AKTIF", True),
        ai_threshold_confidence=_float("JALANKU_AI_THRESHOLD_CONFIDENCE"),
        ai_threshold_kemiripan=_float("JALANKU_AI_THRESHOLD_KEMIRIPAN"),
        wajib_foto_selesai=_bool("JALANKU_WAJIB_FOTO_SELESAI", True),
        smtp_host=os.environ.get("JALANKU_SMTP_HOST", ""),
        smtp_port=int(os.environ.get("JALANKU_SMTP_PORT", "587")),
        smtp_user=os.environ.get("JALANKU_SMTP_USER", ""),
        smtp_password=os.environ.get("JALANKU_SMTP_PASSWORD", ""),
        email_pengirim=os.environ.get("JALANKU_EMAIL_PENGIRIM", "JalanKu <noreply@localhost>"),
    )


def muat_ulang_pengaturan() -> Pengaturan:
    """Baca ulang environment (dipakai test)."""
    pengaturan.cache_clear()
    return pengaturan()
