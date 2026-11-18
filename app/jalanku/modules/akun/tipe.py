"""Tipe publik modul akun (ikut dalam kontrak)."""

from __future__ import annotations

from dataclasses import dataclass

PERAN_PELAPOR = "pelapor"
PERAN_PETUGAS = "petugas"
PERAN_ADMIN = "admin"
SEMUA_PERAN = (PERAN_PELAPOR, PERAN_PETUGAS, PERAN_ADMIN)


@dataclass(frozen=True)
class Pengguna:
    id: int
    email: str
    nama: str
    peran: str
    instansi_id: str | None
    terverifikasi: bool


@dataclass(frozen=True)
class AkunDihapus:
    """Kejadian: identitas pengguna sudah dihapus (FR-AKN-04)."""

    pengguna_id: int
