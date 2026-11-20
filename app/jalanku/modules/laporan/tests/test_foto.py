"""Foto aman (TS-02): NFR-SEC-02 validasi isi, NFR-PRI-02 EXIF dibuang, NFR-PERF-03 ≤ 1 MB.

Diport dari MVP v2 (``jalanku-v0/app/tests/unit/test_foto.py``, karya Yosua); di sini yang diuji
adalah bytes hasil ``bersihkan_foto`` dan berkas yang benar-benar tersimpan lewat ``buat_laporan``.
"""

from __future__ import annotations

import io
import os

import pytest
from PIL import Image

from conftest import TITIK, foto_bytes
from jalanku.core import TidakValid, pengaturan, transaksi
from jalanku.core.penyimpanan import jalur_berkas
from jalanku.modules import laporan
from jalanku.modules.laporan._foto import MAKS_INPUT_BYTES, MAKS_SIMPAN_BYTES, SISI_MAKS_PX, bersihkan_foto


def _exif_gps() -> bytes:
    exif = Image.Exif()
    exif[0x010F] = "MerekHP"  # Make
    exif[0x0110] = "ModelHP X"  # Model
    gps = exif.get_ifd(0x8825)
    gps[1] = "S"
    gps[2] = (6.0, 10.0, 30.0)
    gps[3] = "E"
    gps[4] = (106.0, 38.0, 20.0)
    return exif.tobytes()


def _buka(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data))


def test_exif_termasuk_gps_dihapus():
    asli = foto_bytes(exif=_exif_gps())
    assert _buka(asli).getexif()  # pastikan sampel memang ber-EXIF
    hasil = bersihkan_foto(asli)
    im = _buka(hasil)
    assert len(im.getexif()) == 0 and "exif" not in im.info
    assert b"MerekHP" not in hasil and b"Exif" not in hasil


def test_orientasi_exif_diterapkan():
    exif = Image.Exif()
    exif[0x0112] = 6  # rotasi 90 derajat
    im = _buka(bersihkan_foto(foto_bytes(w=400, h=200, exif=exif.tobytes())))
    assert im.size == (200, 400)


@pytest.mark.parametrize("fmt", ["PNG", "WEBP"])
def test_png_webp_diterima_jadi_jpeg(fmt):
    assert _buka(bersihkan_foto(foto_bytes(fmt=fmt))).format == "JPEG"


def test_png_transparan_tidak_error():
    buf = io.BytesIO()
    Image.new("RGBA", (300, 200), (0, 0, 0, 0)).save(buf, "PNG")
    assert _buka(bersihkan_foto(buf.getvalue())).size == (300, 200)


def test_file_bukan_gambar_ditolak_walau_namanya_jpg():
    with pytest.raises(TidakValid, match="bukan gambar"):
        bersihkan_foto(b"<?php echo 'bukan foto'; ?>")


def test_format_lain_ditolak():
    with pytest.raises(TidakValid, match="Format"):
        bersihkan_foto(foto_bytes(fmt="GIF"))


def test_kosong_dan_terlalu_besar_ditolak():
    with pytest.raises(TidakValid, match="kosong"):
        bersihkan_foto(b"")
    with pytest.raises(TidakValid, match="maksimal"):
        bersihkan_foto(b"x" * (MAKS_INPUT_BYTES + 1))


def test_batas_ukuran_tepat_10mb_diterima_lebih_satu_byte_ditolak():
    # JPEG asli + padding setelah penanda akhir: ukurannya persis di batas, isinya tetap gambar sah.
    foto = foto_bytes()
    pas = foto + b"\0" * (MAKS_INPUT_BYTES - len(foto))
    assert len(pas) == MAKS_INPUT_BYTES
    assert len(bersihkan_foto(pas)) <= MAKS_SIMPAN_BYTES
    with pytest.raises(TidakValid, match="maksimal"):
        bersihkan_foto(pas + b"\0")


def test_foto_besar_dikompres_di_bawah_1mb():
    im = Image.frombytes("RGB", (1800, 1400), os.urandom(1800 * 1400 * 3))  # derau acak: sulit dikompres
    buf = io.BytesIO()
    im.save(buf, "PNG")
    assert len(buf.getvalue()) > MAKS_SIMPAN_BYTES
    hasil = bersihkan_foto(buf.getvalue())
    assert len(hasil) <= MAKS_SIMPAN_BYTES
    assert max(_buka(hasil).size) <= SISI_MAKS_PX


def test_berkas_tersimpan_lewat_buat_laporan_bersih_dan_bernama_acak():
    lat, lon = TITIK["monas"]
    lap = laporan.buat_laporan(
        laporan.LaporanBaru(
            pelapor_id=1,
            lat=lat,
            lon=lon,
            sumber_lokasi="gps",
            kota="Jakarta Pusat",
            kecamatan="Gambir",
            instansi_id="SUDIN_JP",
            foto=[foto_bytes(exif=_exif_gps()), foto_bytes(fmt="PNG")],
            keputusan_ai="perlu_admin",
        )
    )
    with transaksi() as kon:
        nama = [b["berkas"] for b in kon.execute("SELECT berkas FROM laporan_foto WHERE laporan_id = ?", (lap.id,))]
    assert len(nama) == 2 and nama[0] != nama[1]
    for n in nama:
        data = jalur_berkas(n).read_bytes()
        assert _buka(data).format == "JPEG" and b"MerekHP" not in data


def test_foto_tidak_valid_menggagalkan_laporan_tanpa_sisa():
    lat, lon = TITIK["monas"]
    baru = laporan.LaporanBaru(
        pelapor_id=1,
        lat=lat,
        lon=lon,
        sumber_lokasi="gps",
        kota="Jakarta Pusat",
        kecamatan="Gambir",
        instansi_id="SUDIN_JP",
        foto=[foto_bytes(), b"bukan foto"],
        keputusan_ai="perlu_admin",
    )
    with pytest.raises(TidakValid):
        laporan.buat_laporan(baru)
    with transaksi() as kon:
        assert kon.execute("SELECT COUNT(*) FROM laporan").fetchone()[0] == 0
    folder = pengaturan().folder_berkas
    assert not folder.exists() or not any(folder.iterdir())  # tidak ada berkas yatim
