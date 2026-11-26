"""Kontrak wilayah: fixture kecil SIMULASI dan penerimaan dengan batas asli TS-04."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from shapely.geometry import box, mapping

from jalanku.core import TidakValid, pengaturan
from jalanku.modules import wilayah

NAMA_BERKAS = "wilayah-dki-jakarta.geojson"


@pytest.fixture
def simulasi():
    fitur = [
        {
            "type": "Feature",
            "properties": {"kota": kota, "kecamatan": f"SIMULASI {i}"},
            "geometry": mapping(box(100 + i, -7, 101 + i, -6)),
        }
        for i, kota in enumerate(["Jakarta Barat", "Jakarta Pusat"])
    ]
    data = {"type": "FeatureCollection", "features": fitur}
    (pengaturan().folder_data / NAMA_BERKAS).write_text(json.dumps(data), encoding="utf-8")
    return json.loads(json.dumps(data))


def test_dua_poligon_dan_tepi_bersama(simulasi):
    for lon, kec, inst in [
        (100.5, "SIMULASI 0", "SUDIN_JB"),
        (101.5, "SIMULASI 1", "SUDIN_JP"),
        (101, "SIMULASI 0", "SUDIN_JB"),
    ]:
        hasil = wilayah.tentukan_wilayah(-6.5, lon)
        assert hasil.di_dalam and hasil.kecamatan == kec and hasil.instansi.id == inst
    assert wilayah.tentukan_wilayah(-6.5, 103) == wilayah.HasilWilayah(False, None, None, None)


def test_kanal_luar_wilayah_sp4n_lapor():
    assert wilayah.KANAL_LUAR_WILAYAH == ("SP4N-LAPOR!", "https://www.lapor.go.id/")


def test_endpoint_batas(klien, simulasi):
    respons = klien.get("/api/wilayah")
    assert respons.status_code == 200
    assert respons.json() == simulasi


def test_lubang_poligon_tidak_mendapat_sudin(simulasi):
    fitur = simulasi["features"][0]
    fitur["geometry"]["coordinates"].append(list(box(100.2, -6.8, 100.8, -6.2).exterior.coords))
    (pengaturan().folder_data / NAMA_BERKAS).write_text(json.dumps(simulasi))
    assert wilayah.tentukan_wilayah(-6.5, 100.5) == wilayah.HasilWilayah(False, None, None, None)


@pytest.mark.parametrize("isi", [None, "{", '{"type":"FeatureCollection","features":[]}'])
def test_data_tidak_tersedia(klien, isi):
    if isi is not None:
        (pengaturan().folder_data / NAMA_BERKAS).write_text(isi)
    respons = klien.get("/api/wilayah")
    assert respons.status_code == 503
    assert "python -m jalanku.modules.wilayah.data.setup_wilayah" in respons.json()["detail"]


@pytest.mark.parametrize(("lat", "lon"), [(float("nan"), 100), (-91, 0), (0, 181)])
def test_koordinat_tidak_valid(lat, lon):
    with pytest.raises(TidakValid):
        wilayah.tentukan_wilayah(lat, lon)


# Lima landmark dari jalanku-v0@65db419:app/tests/conftest.py. Titik kelurahan dari
# lokasi.lat/lon/kecamatan/kotkab di https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4=<kode>.
# Nama kecamatan mengikuti ejaan TS-04. Titik laut berada di Laut Jawa (5° LS, 107° BT).
TITIK_NYATA = [
    ("Monas", -6.1754, 106.8272, "Jakarta Pusat", "Gambir", "SUDIN_JP"),
    ("Pasar Baru 31.71.02.1001", -6.1660294705, 106.8344840159, "Jakarta Pusat", "Sawah Besar", "SUDIN_JP"),
    ("Kemayoran 31.71.03.1001", -6.1647214778, 106.8453837867, "Jakarta Pusat", "Kemayoran", "SUDIN_JP"),
    ("Kelapa Gading", -6.1586, 106.9050, "Jakarta Utara", "Kelapa Gading", "SUDIN_JU"),
    ("Penjaringan 31.72.01.1001", -6.1220449172, 106.8000217808, "Jakarta Utara", "Penjaringan", "SUDIN_JU"),
    ("Tanjung Priok 31.72.02.1001", -6.1088734921, 106.8791491018, "Jakarta Utara", "Tanjung Priok", "SUDIN_JU"),
    ("Grogol", -6.1667, 106.7900, "Jakarta Barat", "Grogol Petamburan", "SUDIN_JB"),
    ("Cengkareng Barat 31.73.01.1001", -6.1386770759, 106.7237909972, "Jakarta Barat", "Cengkareng", "SUDIN_JB"),
    ("Taman Sari 31.73.03.1001", -6.1535766841, 106.8245312411, "Jakarta Barat", "Taman Sari", "SUDIN_JB"),
    ("Blok M", -6.2443, 106.7988, "Jakarta Selatan", "Kebayoran Baru", "SUDIN_JS"),
    ("Tebet Timur 31.74.01.1001", -6.2338194545, 106.8555231021, "Jakarta Selatan", "Tebet", "SUDIN_JS"),
    ("Setia Budi 31.74.02.1001", -6.2074199951, 106.825837938, "Jakarta Selatan", "Setiabudi", "SUDIN_JS"),
    ("Jatinegara", -6.2425, 106.8690, "Jakarta Timur", "Jatinegara", "SUDIN_JT"),
    ("Pisangan Baru 31.75.01.1001", -6.2117040208, 106.8689841425, "Jakarta Timur", "Matraman", "SUDIN_JT"),
    ("Pulo Gadung 31.75.02.1001", -6.1829906187, 106.898903552, "Jakarta Timur", "Pulo Gadung", "SUDIN_JT"),
    ("Kota Tangerang", -6.1800, 106.6300, None, None, None),
    ("Depok 32.76.03.1001", -6.4243518405, 106.7812136297, None, None, None),
    ("Bekasi 32.75.01.1001", -6.2333592197, 107.0135599618, None, None, None),
    ("Kepulauan Seribu 31.01.01.1001", -5.7337889508, 106.5900424295, None, None, None),
    ("Laut Jawa", -5.0, 107.0, None, None, None),
]


@pytest.fixture(scope="session")
def batas_asli() -> Path:
    # Ambil konfigurasi sesi sebelum fixture per-test mengisolasi DB dan folder data.
    sumber = pengaturan().folder_data / NAMA_BERKAS
    if not sumber.is_file():
        pytest.fail(
            f"{sumber} belum tersedia. Dari app/, jalankan python -m jalanku.modules.wilayah.data.setup_wilayah"
        )
    return sumber


@pytest.mark.parametrize(
    ("nama", "lat", "lon", "kota", "kecamatan", "instansi"), TITIK_NYATA, ids=[t[0] for t in TITIK_NYATA]
)
def test_titik_nyata(batas_asli, nama, lat, lon, kota, kecamatan, instansi):
    shutil.copyfile(batas_asli, pengaturan().folder_data / NAMA_BERKAS)
    hasil = wilayah.tentukan_wilayah(lat, lon)
    assert (hasil.di_dalam, hasil.kota, hasil.kecamatan, hasil.instansi.id if hasil.instansi else None) == (
        kota is not None,
        kota,
        kecamatan,
        instansi,
    ), nama


def test_enam_instansi_dan_kanal_https():
    daftar = wilayah.daftar_instansi()
    assert {i.id for i in daftar} == {"DINAS_BM", "SUDIN_JP", "SUDIN_JU", "SUDIN_JB", "SUDIN_JS", "SUDIN_JT"}
    assert all(i.kanal_url.startswith("https://") for i in daftar)


def test_dinas_boleh_semua_sudin_hanya_kotanya():
    assert wilayah.boleh_menangani("DINAS_BM", "Jakarta Selatan")
    assert wilayah.boleh_menangani("SUDIN_JS", "Jakarta Selatan")
    assert not wilayah.boleh_menangani("SUDIN_JS", "Jakarta Pusat")
