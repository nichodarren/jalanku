"""Snapshot kontrak (ADR-0005): OpenAPI + antarmuka publik setiap modul.

``python -m jalanku kontrak``          → cek kode masih cocok dengan snapshot
``python -m jalanku kontrak --tulis``  → tulis ulang snapshot (hanya setelah change request disetujui,
                                         atau untuk penambahan yang backward compatible)
"""

from __future__ import annotations

import dataclasses
import importlib
import inspect
import json
import re
from pathlib import Path

from fastapi import APIRouter

FOLDER_KONTRAK = Path(__file__).resolve().parents[1] / "kontrak"
NAMA_MODUL = [
    "core",
    "akun",
    "wilayah",
    "laporan",
    "ai",
    "pelaporan",
    "moderasi",
    "penanganan",
    "peta",
    "statistik",
    "notifikasi",
]
_ALAMAT = re.compile(r" at 0x[0-9a-fA-F]+")
# repr Depends berbeda antarversi FastAPI → ringkas menjadi Depends(nama_fungsi)
_DEPENDS = re.compile(r"Depends\((?:dependency=)?<function ([\w.<>]+)>[^)]*\)")


def _impor(nama: str):
    return importlib.import_module("jalanku.core" if nama == "core" else f"jalanku.modules.{nama}")


def _uraikan(obj) -> dict:
    if isinstance(obj, APIRouter):
        return {"jenis": "router"}
    if inspect.isclass(obj) and dataclasses.is_dataclass(obj):
        return {"jenis": "dataclass", "field": [f"{f.name}: {f.type}" for f in dataclasses.fields(obj)]}
    if inspect.isclass(obj) and issubclass(obj, BaseException):
        return {"jenis": "galat", "induk": obj.__mro__[1].__name__, "kode_http": getattr(obj, "kode_http", None)}
    if inspect.isclass(obj):
        return {"jenis": "kelas"}
    if callable(obj):
        teks = _ALAMAT.sub("", str(inspect.signature(obj)))
        return {"jenis": "fungsi", "tanda_tangan": _DEPENDS.sub(r"Depends(\1)", teks)}
    return {"jenis": "konstanta", "nilai": repr(obj)}


def antarmuka_modul() -> dict:
    hasil = {}
    for nama in NAMA_MODUL:
        modul = _impor(nama)
        hasil[nama] = {n: _uraikan(getattr(modul, n)) for n in sorted(modul.__all__)}
    return hasil


def openapi_terkini() -> dict:
    from jalanku.main import buat_app

    spek = buat_app(sertakan_dev=False, migrasi=False).openapi()
    spek.get("info", {}).pop("version", None)  # versi rilis bukan bagian kontrak
    return spek


def _json(data: dict) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def _akses(metode: str, jalur: str) -> str:
    """Konvensi akses berdasarkan path. Pengecekan sebenarnya ada di kode."""
    if jalur.startswith("/api/admin/"):
        return "admin"
    if jalur.startswith("/api/petugas/"):
        return "petugas"
    if metode == "post" and (jalur in ("/api/laporan", "/api/ai/periksa") or jalur.endswith(("/dukung", "/banding"))):
        return "pelapor terverifikasi"
    if jalur.startswith(("/api/saya/", "/api/notifikasi")) or jalur == "/api/akun/saya" and metode == "delete":
        return "login"
    return "publik"


def tabel_endpoint(spek: dict) -> str:
    baris = ["| Modul | Method | Path | Fungsi | Akses |", "|---|---|---|---|---|"]
    urutan = [nama for nama in NAMA_MODUL if nama != "core"] + ["sistem"]
    semua = [(op["tags"][0], jalur, metode, op) for jalur, isi in spek["paths"].items() for metode, op in isi.items()]
    for tag, jalur, metode, op in sorted(semua, key=lambda x: (urutan.index(x[0]) if x[0] in urutan else 99, x[1])):
        baris.append(f"| {tag} | {metode.upper()} | `{jalur}` | {op.get('summary', '')} | {_akses(metode, jalur)} |")
    return "\n".join(baris)


def tulis() -> None:
    FOLDER_KONTRAK.mkdir(exist_ok=True)
    (FOLDER_KONTRAK / "openapi.json").write_text(_json(openapi_terkini()), encoding="utf-8", newline="\n")
    (FOLDER_KONTRAK / "modul.json").write_text(_json(antarmuka_modul()), encoding="utf-8", newline="\n")


def bandingkan() -> list[str]:
    """Daftar perbedaan antara kode dan snapshot (kosong = cocok)."""
    beda = []
    for berkas, terkini in (("openapi.json", openapi_terkini()), ("modul.json", antarmuka_modul())):
        jalur = FOLDER_KONTRAK / berkas
        if not jalur.exists():
            beda.append(f"{berkas}: snapshot belum ada (jalankan `python -m jalanku kontrak --tulis`)")
            continue
        lama = json.loads(jalur.read_text(encoding="utf-8"))
        beda += [f"{berkas}: {d}" for d in _beda(lama, json.loads(_json(terkini)))]
    return beda


def _beda(lama, baru, jalur: str = "") -> list[str]:
    if isinstance(lama, dict) and isinstance(baru, dict):
        hasil = []
        for k in sorted(set(lama) | set(baru)):
            p = f"{jalur}/{k}"
            if k not in baru:
                hasil.append(f"DIHAPUS {p}")
            elif k not in lama:
                hasil.append(f"DITAMBAH {p}")
            else:
                hasil += _beda(lama[k], baru[k], p)
        return hasil
    return [] if lama == baru else [f"DIUBAH {jalur or '/'}"]
