"""Fixture geometri SIMULASI untuk persiapan data TS-04."""

import json

import pytest
from shapely.geometry import box, mapping, shape

from jalanku.modules.wilayah import daftar_instansi
from jalanku.modules.wilayah.data.siapkan_wilayah import siapkan


def fitur_simulasi(kota, kecamatan, x, provinsi="DKI Jakarta"):
    return {
        "type": "Feature",
        "properties": {"NAME_1": provinsi, "NAME_2": kota, "NAME_3": kecamatan},
        "geometry": mapping(box(x, 0, x + 1, 1)),
    }


def test_filter_normalisasi_dan_penggabungan(tmp_path):
    jumlah = {"Jakarta Pusat": 8, "Jakarta Utara": 6, "Jakarta Barat": 8, "Jakarta Selatan": 10, "Jakarta Timur": 10}
    fitur = [
        fitur_simulasi(kota, f"SIMULASI {i}", i)
        for kota, banyak in jumlah.items()
        for i in range(banyak - int(kota == "Jakarta Selatan"))
    ]
    fitur.extend(
        [
            fitur_simulasi("Jakarta Selatan", "Kabayoran Lama", 10),
            fitur_simulasi("Jakarta Selatan", "Kebayoran Lama", 11),
            fitur_simulasi("Kepulauan Seribu", "SIMULASI pulau", 12),
            fitur_simulasi("Jakarta Pusat", "SIMULASI luar provinsi", 13, "Banten"),
        ]
    )
    sumber = tmp_path / "SIMULASI.geojson"
    sumber.write_text(json.dumps({"type": "FeatureCollection", "features": fitur}))
    tujuan = tmp_path / "lokal" / "hasil.geojson"
    siapkan(sumber, tujuan)

    hasil = json.loads(tujuan.read_text(encoding="utf-8"))
    assert hasil["type"] == "FeatureCollection"
    assert "GADM" in hasil["jalanku"]["atribusi"]
    nama = [(f["properties"]["kota"], f["properties"]["kecamatan"]) for f in hasil["features"]]
    assert len(nama) == len(set(nama)) == 42
    assert nama == sorted(nama)
    assert {kota for kota, _ in nama} == jumlah.keys()
    assert all(n not in {"SIMULASI pulau", "SIMULASI luar provinsi"} for _, n in nama)
    indeks = nama.index(("Jakarta Selatan", "Kebayoran Lama"))
    assert shape(hasil["features"][indeks]["geometry"]).equals(box(10, 0, 12, 1))


def test_data_tidak_lengkap_tidak_menimpa_hasil(tmp_path):
    sumber = tmp_path / "SIMULASI.geojson"
    sumber.write_text('{"type":"FeatureCollection","features":[]}')
    tujuan = tmp_path / "hasil.geojson"
    tujuan.write_text("hasil lama")
    with pytest.raises(ValueError, match="42"):
        siapkan(sumber, tujuan)
    assert tujuan.read_text() == "hasil lama"


def test_setiap_kota_punya_satu_sudin_yang_tepat():
    assert sorted((i.kota, i.id) for i in daftar_instansi() if i.kota) == [
        ("Jakarta Barat", "SUDIN_JB"),
        ("Jakarta Pusat", "SUDIN_JP"),
        ("Jakarta Selatan", "SUDIN_JS"),
        ("Jakarta Timur", "SUDIN_JT"),
        ("Jakarta Utara", "SUDIN_JU"),
    ]
