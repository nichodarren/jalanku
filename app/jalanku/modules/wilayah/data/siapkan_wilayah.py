"""Siapkan batas kecamatan Jakarta daratan dari GeoJSON GADM untuk pemakaian lokal."""

import argparse
import json
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory

from shapely.geometry import mapping, shape
from shapely.ops import unary_union

from ..tipe import KOTA

# Variasi nama pada arsip GADM. Danau Sunter tergabung dalam Tanjung Priok.
NAMA_RESMI = {
    "Grogolpetamburan": "Grogol Petamburan",
    "Kebonjeruk": "Kebon Jeruk",
    "Tamansari": "Taman Sari",
    "Tanahabang": "Tanah Abang",
    "Kabayoran Lama": "Kebayoran Lama",
    "Setia Budi": "Setiabudi",
    "Kramatjati": "Kramat Jati",
    "Pasarrebo": "Pasar Rebo",
    "Pulogadung": "Pulo Gadung",
    "Danau Sunter Dll": "Tanjung Priok",
}


def siapkan(sumber: Path, tujuan: Path) -> None:
    """Gabungkan poligon per kecamatan dan tulis hasil lengkap secara atomik."""
    if sumber.resolve() == tujuan.resolve():
        raise ValueError("Pilih tujuan yang berbeda dari berkas sumber.")
    data = json.loads(sumber.read_text(encoding="utf-8"))
    kelompok = defaultdict(list)
    for fitur in data["features"]:
        properti = fitur["properties"]
        kota = properti.get("NAME_2")
        if properti.get("NAME_1") != "DKI Jakarta" or kota not in KOTA:
            continue
        nama = properti["NAME_3"]
        geometri = shape(fitur["geometry"])
        if geometri.geom_type not in {"Polygon", "MultiPolygon"} or geometri.is_empty:
            raise ValueError(f"Batas {kota}, {nama} harus berupa poligon berisi.")
        kelompok[kota, NAMA_RESMI.get(nama, nama)].append(geometri.buffer(0))

    if len(kelompok) != 42 or {kota for kota, _ in kelompok} != set(KOTA):
        raise ValueError("Data harus mencakup 42 kecamatan di lima kota administrasi Jakarta.")
    fitur_hasil = []
    for (kota, kecamatan), bagian in sorted(kelompok.items()):
        batas = unary_union(bagian)
        if batas.is_empty or not batas.is_valid or batas.geom_type not in {"Polygon", "MultiPolygon"}:
            raise ValueError(f"Geometri hasil tidak valid untuk {kecamatan}, {kota}.")
        fitur_hasil.append(
            {
                "type": "Feature",
                "properties": {"kota": kota, "kecamatan": kecamatan},
                "geometry": mapping(batas),
            }
        )
    hasil = {
        "type": "FeatureCollection",
        "jalanku": {
            "sumber": "GADM via github.com/fahadh4ilyas/indonesia-geojson-archive",
            "atribusi": "Batas wilayah: GADM",
        },
        "features": fitur_hasil,
    }
    tujuan.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=tujuan.parent) as folder:
        jalur = Path(folder) / "wilayah.geojson"
        with jalur.open("w", encoding="utf-8") as sementara:
            json.dump(hasil, sementara, ensure_ascii=False, separators=(",", ":"))
        jalur.replace(tujuan)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sumber", type=Path)
    parser.add_argument("tujuan", type=Path)
    args = parser.parse_args()
    siapkan(args.sumber, args.tujuan)
