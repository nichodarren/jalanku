"""Koneksi SQLite dan migrasi per modul.

Aturan:
- Setiap modul menyimpan migrasinya di ``modules/<modul>/migrasi/NNN_nama.sql``.
- File migrasi yang sudah di-merge TIDAK BOLEH diedit; perubahan = file baru dengan nomor berikutnya.
- Tabel milik modul diberi prefiks nama modul (dicek ``tests/arsitektur``).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from .config import pengaturan
from .waktu import sekarang

FOLDER_MODUL = Path(__file__).resolve().parents[1] / "modules"


def koneksi() -> sqlite3.Connection:
    """Koneksi baru ke basis data. Baris bisa diakses seperti dict (``baris["kolom"]``)."""
    jalur = pengaturan().jalur_db
    jalur.parent.mkdir(parents=True, exist_ok=True)
    kon = sqlite3.connect(jalur, timeout=10)
    kon.row_factory = sqlite3.Row
    kon.execute("PRAGMA foreign_keys = ON")
    kon.execute("PRAGMA busy_timeout = 10000")
    return kon


@contextmanager
def transaksi() -> Iterator[sqlite3.Connection]:
    """``with transaksi() as kon:`` → commit bila sukses, rollback bila galat, lalu ditutup."""
    kon = koneksi()
    try:
        kon.execute("BEGIN IMMEDIATE")
        yield kon
        kon.commit()
    except BaseException:
        kon.rollback()
        raise
    finally:
        kon.close()


def daftar_migrasi() -> list[tuple[str, Path]]:
    """Semua file migrasi, urut per modul lalu nomor file. ID = ``<modul>/<nama file>``."""
    hasil = []
    for folder in sorted(FOLDER_MODUL.glob("*/migrasi")):
        modul = folder.parent.name
        for berkas in sorted(folder.glob("*.sql")):
            hasil.append((f"{modul}/{berkas.name}", berkas))
    return hasil


def jalankan_migrasi() -> list[str]:
    """Terapkan migrasi yang belum pernah dijalankan. Mengembalikan ID yang baru diterapkan."""
    kon = koneksi()
    try:
        kon.execute("PRAGMA journal_mode = WAL")
        kon.execute("CREATE TABLE IF NOT EXISTS _migrasi (id TEXT PRIMARY KEY, diterapkan_pada TEXT NOT NULL)")
        sudah = {b["id"] for b in kon.execute("SELECT id FROM _migrasi")}
        baru = []
        for id_migrasi, berkas in daftar_migrasi():
            if id_migrasi in sudah:
                continue
            kon.executescript("BEGIN;\n" + berkas.read_text(encoding="utf-8") + "\nCOMMIT;")
            kon.execute("INSERT INTO _migrasi (id, diterapkan_pada) VALUES (?, ?)", (id_migrasi, sekarang()))
            kon.commit()
            baru.append(id_migrasi)
        return baru
    finally:
        kon.close()
