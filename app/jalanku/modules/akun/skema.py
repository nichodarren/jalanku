"""Skema HTTP modul akun (masuk ke OpenAPI → dikunci di app/kontrak/openapi.json)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PenggunaKeluaran(BaseModel):
    id: int
    nama: str
    email: str
    peran: str = Field(description="pelapor | petugas | admin")
    instansi_id: str | None
    terverifikasi: bool


class DaftarMasukan(BaseModel):
    nama: str = Field(min_length=1, max_length=40)
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=128)
    setuju_privasi: bool


class MasukMasukan(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


class TokenMasukan(BaseModel):
    token: str = Field(max_length=200)


class EmailMasukan(BaseModel):
    email: str = Field(max_length=254)


class MasukDevMasukan(BaseModel):
    email: str = Field(max_length=254)
    peran: str = Field(default="pelapor", description="pelapor | petugas | admin")
    instansi_id: str | None = None
    nama: str | None = None


class Pesan(BaseModel):
    detail: str
