"""Skema HTTP modul wilayah."""

from __future__ import annotations

from pydantic import BaseModel, Field


class InstansiKeluaran(BaseModel):
    id: str
    nama: str
    nama_pendek: str
    kota: str | None
    kanal_nama: str
    kanal_url: str


class UbahInstansiMasukan(BaseModel):
    kanal_nama: str | None = Field(default=None, max_length=120)
    kanal_url: str | None = Field(default=None, max_length=300, description="wajib http:// atau https://")
