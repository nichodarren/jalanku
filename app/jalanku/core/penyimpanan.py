"""Penyimpanan berkas (foto) di ``<JALANKU_DATA>/berkas`` dengan nama acak.

Modul ini hanya menyimpan byte apa adanya. Validasi isi, pembuangan EXIF, dan
encode ulang adalah tanggung jawab modul ``laporan`` (FR-LAP-04).
"""

from __future__ import annotations

import contextlib
import re
import secrets
from pathlib import Path

from .config import pengaturan
from .galat import TidakDitemukan

_POLA_NAMA = re.compile(r"^[0-9a-f]{32}\.(jpg|png|webp)$")


def simpan_berkas(data: bytes, akhiran: str = ".jpg") -> str:
    akhiran = akhiran if akhiran.startswith(".") else "." + akhiran
    nama = secrets.token_hex(16) + akhiran
    folder = pengaturan().folder_berkas
    folder.mkdir(parents=True, exist_ok=True)
    (folder / nama).write_bytes(data)
    return nama


def jalur_berkas(nama: str) -> Path:
    """Path berkas yang sudah disimpan. Nama divalidasi ketat untuk mencegah path traversal."""
    if not _POLA_NAMA.match(nama):
        raise TidakDitemukan("Berkas tidak ditemukan.")
    jalur = pengaturan().folder_berkas / nama
    if not jalur.is_file():
        raise TidakDitemukan("Berkas tidak ditemukan.")
    return jalur


def hapus_berkas(nama: str) -> None:
    with contextlib.suppress(TidakDitemukan):
        jalur_berkas(nama).unlink()
