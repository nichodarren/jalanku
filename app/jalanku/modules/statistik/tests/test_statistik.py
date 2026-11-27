"""US-23 statistik per Sudin (FR-STAT-01, BR-04): jumlah per status, median jam, persen keputusan AI."""

from __future__ import annotations

from datetime import timedelta

import pytest

from conftest import foto_bytes
from jalanku.core import ke_datetime
from jalanku.core.waktu import atur_waktu
from jalanku.modules import laporan as L

T0 = "2026-11-20T08:00:00+00:00"


def _jam(iso: str, jam: float) -> str:
    return (ke_datetime(iso) + timedelta(hours=jam)).isoformat(timespec="seconds")


def _laporan(instansi_id: str = "SUDIN_JP", keputusan_ai: str = "terverifikasi") -> L.Laporan:
    """Laporan SIMULASI; ``terverifikasi`` = langsung belum_dikerjakan dengan diverifikasi_pada = sekarang()."""
    return L.buat_laporan(
        L.LaporanBaru(
            pelapor_id=None,
            lat=-6.1754,
            lon=106.8272,
            sumber_lokasi="gps",
            kota="Jakarta Pusat",
            kecamatan="Gambir",
            instansi_id=instansi_id,
            foto=[foto_bytes()],
            keputusan_ai=keputusan_ai,
            tingkat=L.TINGKAT_RUSAK if keputusan_ai == "terverifikasi" else None,
            simulasi=True,
        )
    )


def _dikerjakan(lap: L.Laporan, jam_setelah_verifikasi: float) -> None:
    atur_waktu(_jam(lap.diverifikasi_pada, jam_setelah_verifikasi))
    L.ubah_status(lap.nomor, L.STATUS_SEDANG, L.PELAKU_PETUGAS, pengguna_id=900)


def _selesai(lap: L.Laporan, jam_setelah_verifikasi: float) -> None:
    atur_waktu(_jam(lap.diverifikasi_pada, jam_setelah_verifikasi))
    L.ubah_status(lap.nomor, L.STATUS_SELESAI, L.PELAKU_PETUGAS, pengguna_id=900, foto_sesudah=foto_bytes())


def _per_instansi(data: dict) -> dict[str, dict]:
    return {i["instansi_id"]: i for i in data["instansi"]}


def test_statistik_kosong_tetap_lengkap_dan_berlabel_simulasi(klien):
    r = klien.get("/api/statistik")

    assert r.status_code == 200
    data = r.json()
    assert data["label_simulasi"] is True
    assert data["periode_hari"] == 30
    assert data["persen_diputuskan_ai"] is None
    per = _per_instansi(data)
    assert set(per) == {"SUDIN_JP", "SUDIN_JU", "SUDIN_JB", "SUDIN_JS", "SUDIN_JT"}  # tanpa DINAS_BM
    for item in per.values():
        assert item["jumlah_per_status"] == {"belum_dikerjakan": 0, "sedang_dikerjakan": 0, "selesai": 0}
        assert item["median_jam_dikerjakan"] is None and item["median_jam_selesai"] is None
        assert item["n_dikerjakan"] == 0 and item["n_selesai"] == 0


def test_jumlah_per_status_hanya_laporan_terverifikasi_per_instansi(klien):
    atur_waktu(T0)
    _laporan("SUDIN_JP")
    _dikerjakan(_laporan("SUDIN_JP"), 2)
    _selesai(_laporan("SUDIN_JS"), 5)
    _laporan("SUDIN_JP", keputusan_ai="perlu_admin")  # menunggu: belum terverifikasi
    _laporan("SUDIN_JP", keputusan_ai="ditolak")
    atur_waktu(_jam(T0, 24))

    per = _per_instansi(klien.get("/api/statistik").json())

    assert per["SUDIN_JP"]["jumlah_per_status"] == {"belum_dikerjakan": 1, "sedang_dikerjakan": 1, "selesai": 0}
    assert per["SUDIN_JS"]["jumlah_per_status"] == {"belum_dikerjakan": 0, "sedang_dikerjakan": 0, "selesai": 1}
    assert per["SUDIN_JS"]["nama_pendek"]


@pytest.mark.parametrize(("n", "harap"), [(4, None), (5, 3.0)])
def test_median_dikerjakan_hanya_bila_n_minimal_5(klien, n, harap):
    """Boundary value BR-04: n = 4 → null, n = 5 → median (jam 1..5 → 3,0)."""
    atur_waktu(T0)
    laporan = [_laporan("SUDIN_JP") for _ in range(n)]
    for i, lap in enumerate(laporan, start=1):
        _dikerjakan(lap, i)
    atur_waktu(_jam(T0, 24))

    jp = _per_instansi(klien.get("/api/statistik").json())["SUDIN_JP"]

    assert jp["n_dikerjakan"] == n
    assert jp["median_jam_dikerjakan"] == harap


def test_median_selesai_dan_langsung_selesai_dihitung_sebagai_mulai_dikerjakan(klien):
    atur_waktu(T0)
    laporan = [_laporan("SUDIN_JT") for _ in range(5)]
    for i, lap in enumerate(laporan):
        _dikerjakan(lap, 1)
        _selesai(lap, 10 + 2 * i)  # 10, 12, 14, 16, 18 jam
    langsung = _laporan("SUDIN_JT")
    _selesai(langsung, 7.5)  # belum → selesai tanpa sedang: waktu mulai = waktu selesai
    atur_waktu(_jam(T0, 48))

    jt = _per_instansi(klien.get("/api/statistik").json())["SUDIN_JT"]

    assert jt["n_selesai"] == 6
    assert jt["median_jam_selesai"] == 13.0  # median 7,5 10 12 14 16 18
    assert jt["n_dikerjakan"] == 6
    assert jt["median_jam_dikerjakan"] == 1.0


def test_periode_hari_menyaring_berdasarkan_waktu_verifikasi(klien):
    atur_waktu(_jam(T0, -24 * 40))
    _laporan("SUDIN_JB")  # diverifikasi 40 hari lalu
    atur_waktu(T0)
    _laporan("SUDIN_JB")

    hari30 = _per_instansi(klien.get("/api/statistik?hari=30").json())["SUDIN_JB"]
    data90 = klien.get("/api/statistik?hari=90").json()

    assert hari30["jumlah_per_status"]["belum_dikerjakan"] == 1
    assert data90["periode_hari"] == 90
    assert _per_instansi(data90)["SUDIN_JB"]["jumlah_per_status"]["belum_dikerjakan"] == 2


@pytest.mark.parametrize("hari", [0, -1, 366])
def test_periode_di_luar_batas_400(klien, hari):
    assert klien.get(f"/api/statistik?hari={hari}").status_code == 400


def test_persen_diputuskan_ai(klien):
    atur_waktu(T0)
    _laporan(keputusan_ai="terverifikasi")
    _laporan(keputusan_ai="terverifikasi")
    _laporan(keputusan_ai="ditolak")
    _laporan(keputusan_ai="perlu_admin")

    assert klien.get("/api/statistik").json()["persen_diputuskan_ai"] == 75.0


def test_statistik_publik_tanpa_data_pelapor(klien, buat_klien):
    atur_waktu(T0)
    _laporan()
    for k in (klien, buat_klien("pelapor"), buat_klien("admin")):
        r = k.get("/api/statistik")
        assert r.status_code == 200
        assert "pelapor" not in r.text and "@" not in r.text
