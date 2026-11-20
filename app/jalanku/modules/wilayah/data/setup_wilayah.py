"""Unduh dan siapkan batas kecamatan untuk checkout lokal atau runner CI."""

import hashlib
from http.client import HTTPException
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen

from jalanku.core import pengaturan

from .siapkan_wilayah import siapkan

URL_SUMBER = (
    "https://raw.githubusercontent.com/fahadh4ilyas/indonesia-geojson-archive/"
    "5925720d5cb627680d9245c5953e13a401077e01/Indonesia_subdistricts.geojson"
)
SHA256_SUMBER = "8a651286d9a7469e903ab098669617e9654fd8eaf77c85907ae5e79f5d3a45f5"


def unduh_dan_siapkan() -> Path:
    """Verifikasi arsip sebelum mengganti GeoJSON di folder data aplikasi."""
    tujuan = pengaturan().folder_data / "wilayah-dki-jakarta.geojson"
    with TemporaryDirectory() as folder:
        sumber = Path(folder) / "sumber.geojson"
        sidik = hashlib.sha256()
        with urlopen(URL_SUMBER, timeout=60) as respons, sumber.open("wb") as berkas:  # noqa: S310 (URL HTTPS tetap)
            while blok := respons.read(64 * 1024):
                sidik.update(blok)
                berkas.write(blok)
        if sidik.hexdigest() != SHA256_SUMBER:
            raise ValueError("SHA-256 unduhan tidak cocok dengan arsip TS-04.")
        siapkan(sumber, tujuan)
    return tujuan


if __name__ == "__main__":
    try:
        print(f"Data wilayah siap di {unduh_dan_siapkan()}")
    except (OSError, HTTPException, ValueError) as galat:
        raise SystemExit(f"Setup data wilayah gagal: {galat}") from None
