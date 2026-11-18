"""Logika akun: sesi & pengguna.

STUB (baseline 19 Nov 2026): sesi dan masuk-dev sudah bekerja supaya modul lain bisa diuji
dengan peran apa pun. Daftar, verifikasi email, masuk dengan password, dan hapus akun
dikerjakan M2 (US-01, US-02) — lihat README modul.
"""

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta

from fastapi import Depends, Request

from jalanku.core import PerluMasuk, TidakBerhak, TidakValid, ke_datetime, koneksi, sekarang, transaksi

from .tipe import PERAN_PETUGAS, SEMUA_PERAN, Pengguna

NAMA_COOKIE = "jalanku_sesi"
UMUR_SESI = timedelta(days=30)


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _ke_pengguna(baris) -> Pengguna:
    return Pengguna(
        id=baris["id"],
        email=baris["email"],
        nama=baris["nama"],
        peran=baris["peran"],
        instansi_id=baris["instansi_id"],
        terverifikasi=bool(baris["terverifikasi"]),
    )


def ambil_pengguna(pengguna_id: int) -> Pengguna | None:
    kon = koneksi()
    try:
        baris = kon.execute(
            "SELECT * FROM akun_pengguna WHERE id = ? AND dihapus_pada IS NULL", (pengguna_id,)
        ).fetchone()
        return _ke_pengguna(baris) if baris else None
    finally:
        kon.close()


# --- Sesi -------------------------------------------------------------------------------------


def buat_sesi(pengguna_id: int) -> str:
    """Buat sesi baru dan kembalikan token mentah (hanya disimpan di cookie)."""
    token = secrets.token_urlsafe(32)
    kini = sekarang()
    kedaluwarsa = (ke_datetime(kini) + UMUR_SESI).isoformat(timespec="seconds")
    with transaksi() as kon:
        kon.execute(
            "INSERT INTO akun_sesi (token_hash, pengguna_id, dibuat_pada, kedaluwarsa_pada) VALUES (?, ?, ?, ?)",
            (_hash(token), pengguna_id, kini, kedaluwarsa),
        )
    return token


def akhiri_sesi(token: str | None) -> None:
    if not token:
        return
    with transaksi() as kon:
        kon.execute("DELETE FROM akun_sesi WHERE token_hash = ?", (_hash(token),))


def pengguna_dari_token(token: str | None) -> Pengguna | None:
    if not token:
        return None
    kon = koneksi()
    try:
        baris = kon.execute(
            """SELECT p.* FROM akun_sesi s JOIN akun_pengguna p ON p.id = s.pengguna_id
               WHERE s.token_hash = ? AND s.kedaluwarsa_pada > ? AND p.dihapus_pada IS NULL""",
            (_hash(token), sekarang()),
        ).fetchone()
        return _ke_pengguna(baris) if baris else None
    finally:
        kon.close()


# --- Dependency FastAPI (antarmuka publik) ----------------------------------------------------


def pengguna_opsional(request: Request) -> Pengguna | None:
    return pengguna_dari_token(request.cookies.get(NAMA_COOKIE))


def wajib_masuk(pengguna: Pengguna | None = Depends(pengguna_opsional)) -> Pengguna:
    if pengguna is None:
        raise PerluMasuk("Silakan masuk dulu.")
    return pengguna


def wajib_terverifikasi(pengguna: Pengguna = Depends(wajib_masuk)) -> Pengguna:
    if not pengguna.terverifikasi:
        raise TidakBerhak("Verifikasi email dulu sebelum melanjutkan.")
    return pengguna


def wajib_peran(*peran: str):
    """Pabrik dependency: ``Depends(wajib_peran("admin"))``."""
    for p in peran:
        if p not in SEMUA_PERAN:
            raise ValueError(f"Peran tidak dikenal: {p}")

    def _cek(pengguna: Pengguna = Depends(wajib_terverifikasi)) -> Pengguna:
        if pengguna.peran not in peran:
            raise TidakBerhak("Kamu tidak punya akses ke fitur ini.")
        return pengguna

    return _cek


# --- Khusus mode dev/test ---------------------------------------------------------------------


def masuk_dev(email: str, peran: str, instansi_id: str | None = None, nama: str | None = None) -> tuple[Pengguna, str]:
    """Buat/perbarui pengguna terverifikasi dengan peran tertentu lalu buka sesi. HANYA dev/test."""
    if peran not in SEMUA_PERAN:
        raise TidakValid("Peran tidak dikenal.")
    if peran == PERAN_PETUGAS and not instansi_id:
        raise TidakValid("Petugas wajib punya instansi_id.")
    with transaksi() as kon:
        kon.execute(
            """INSERT INTO akun_pengguna
                 (email, nama, peran, instansi_id, terverifikasi, setuju_privasi_pada, dibuat_pada)
               VALUES (?, ?, ?, ?, 1, ?, ?)
               ON CONFLICT(email) DO UPDATE SET peran = excluded.peran, instansi_id = excluded.instansi_id,
                 terverifikasi = 1, dihapus_pada = NULL""",
            (email.lower(), nama or email.split("@")[0], peran, instansi_id, sekarang(), sekarang()),
        )
        baris = kon.execute("SELECT * FROM akun_pengguna WHERE email = ?", (email.lower(),)).fetchone()
    pengguna = _ke_pengguna(baris)
    return pengguna, buat_sesi(pengguna.id)
