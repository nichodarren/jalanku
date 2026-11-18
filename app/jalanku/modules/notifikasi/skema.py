"""Skema HTTP modul notifikasi."""

from __future__ import annotations

from pydantic import BaseModel


class KabarKeluaran(BaseModel):
    id: int
    nomor: str
    pesan: str
    dibaca: bool
    waktu: str


class PengaturanNotifikasi(BaseModel):
    aktif: bool
