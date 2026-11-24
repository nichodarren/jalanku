"""Test integrasi POST /api/laporan/{nomor}/dukung (US-10, BR-02)."""

from __future__ import annotations

import io

from PIL import Image

from conftest import TITIK
from jalanku.modules.laporan import LaporanBaru, buat_laporan, jumlah_dukungan

MONAS = TITIK["monas"]


def _jpeg() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (8, 8), (120, 120, 120)).save(buf, "JPEG")
    return buf.getvalue()


def _siapkan(keputusan: str = "terverifikasi", pelapor_id: int | None = None, geser: float = 0.0):
    """Laporan langsung lewat antarmuka publik laporan (tanpa HTTP), supaya test dukung tidak bergantung alur lapor."""
    return buat_laporan(
        LaporanBaru(
            pelapor_id=pelapor_id,
            lat=MONAS[0] + geser,
            lon=MONAS[1],
            sumber_lokasi="manual",
            kota="Jakarta Pusat",
            kecamatan="Gambir",
            instansi_id="SUDIN_JP",
            foto=[_jpeg()],
            keputusan_ai=keputusan,
            tingkat="rusak" if keputusan == "terverifikasi" else None,
        )
    )


def _dukung(klien, nomor: str):
    return klien.post(f"/api/laporan/{nomor}/dukung")


def test_dukungan_pertama_tercatat(buat_klien):
    lap = _siapkan()
    r = _dukung(buat_klien("pelapor"), lap.nomor)
    assert r.status_code == 200, r.text
    assert r.json() == {"nomor": lap.nomor, "jumlah_dukungan": 1, "baru": True}


def test_dukungan_kedua_dari_akun_sama_tidak_menambah(buat_klien):
    lap = _siapkan()
    klien = buat_klien("pelapor")
    _dukung(klien, lap.nomor)
    r = _dukung(klien, lap.nomor)
    assert r.status_code == 200
    assert r.json() == {"nomor": lap.nomor, "jumlah_dukungan": 1, "baru": False}


def test_dua_akun_berbeda_menambah_jumlah(buat_klien):
    lap = _siapkan()
    _dukung(buat_klien("pelapor", email="satu@uji.test"), lap.nomor)
    r = _dukung(buat_klien("pelapor", email="dua@uji.test"), lap.nomor)
    assert r.json()["jumlah_dukungan"] == 2
    assert jumlah_dukungan(lap.id) == 2


def test_laporan_menunggu_verifikasi_boleh_didukung(buat_klien):
    """BR-02: laporan aktif termasuk yang menunggu verifikasi (tawaran dukung bisa menunjuknya)."""
    lap = _siapkan(keputusan="perlu_admin")
    assert lap.status == "menunggu_verifikasi"
    assert _dukung(buat_klien("pelapor"), lap.nomor).status_code == 200


def test_laporan_sendiri_tidak_bisa_didukung(buat_klien):
    klien = buat_klien("pelapor")
    r = klien.post(
        "/api/laporan",
        data={"lat": str(MONAS[0]), "lon": str(MONAS[1]), "sumber_lokasi": "manual"},
        files=[("foto", ("a.jpg", _jpeg(), "image/jpeg"))],
    )
    assert r.status_code == 201, r.text
    r2 = _dukung(klien, r.json()["nomor"])
    assert r2.status_code == 409
    assert "sendiri" in r2.json()["detail"]


def test_laporan_ditolak_tidak_bisa_didukung(buat_klien):
    lap = _siapkan(keputusan="ditolak")
    r = _dukung(buat_klien("pelapor"), lap.nomor)
    assert r.status_code == 409


def test_laporan_tidak_ada_404(buat_klien):
    assert _dukung(buat_klien("pelapor"), "JK-99999").status_code == 404


def test_tanpa_login_401(klien):
    lap = _siapkan()
    assert _dukung(klien, lap.nomor).status_code == 401


def test_dukungan_ke_60_lolos_ke_61_kena_rate_limit(buat_klien):
    klien = buat_klien("pelapor")
    laporan = [_siapkan(geser=i * 0.001) for i in range(61)]
    for lap in laporan[:60]:
        assert _dukung(klien, lap.nomor).status_code == 200
    assert _dukung(klien, laporan[60].nomor).status_code == 429
