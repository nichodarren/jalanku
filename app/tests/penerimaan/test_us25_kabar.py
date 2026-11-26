"""US-25 Notifikasi in-app (pemilik M1). Skenario penerimaan lewat API."""

from __future__ import annotations

from conftest import TITIK, foto_bytes
from jalanku.modules import laporan as L


def _laporan_milik(klien) -> L.Laporan:
    pid = klien.get("/api/akun/saya").json()["id"]
    lat, lon = TITIK["monas"]
    return L.buat_laporan(
        L.LaporanBaru(
            pelapor_id=pid,
            lat=lat,
            lon=lon,
            sumber_lokasi="gps",
            kota="Jakarta Pusat",
            kecamatan="Gambir",
            instansi_id="SUDIN_JP",
            foto=[foto_bytes()],
            keputusan_ai="terverifikasi",
            tingkat=L.TINGKAT_RUSAK,
        )
    )


def test_us25_kabar_muncul_setelah_status_berubah(buat_klien):
    """Given saya pelapor sebuah laporan / When petugas mulai mengerjakannya
    / Then saya melihat kabar belum dibaca yang menautkan laporan itu."""
    warga = buat_klien("pelapor", email="kabar@uji.test")
    lap = _laporan_milik(warga)
    assert warga.get("/api/notifikasi").json() == []
    L.ubah_status(lap.nomor, L.STATUS_SEDANG, L.PELAKU_PETUGAS, pengguna_id=900)
    kabar = warga.get("/api/notifikasi").json()
    assert len(kabar) == 1
    assert kabar[0]["nomor"] == lap.nomor
    assert kabar[0]["dibaca"] is False
    assert "sedang dikerjakan" in kabar[0]["pesan"]


def test_us25_tandai_dibaca(buat_klien):
    """Given saya punya kabar belum dibaca / When saya membukanya / Then kabar itu tercatat dibaca."""
    warga = buat_klien("pelapor", email="baca@uji.test")
    lap = _laporan_milik(warga)
    L.ubah_status(lap.nomor, L.STATUS_SEDANG, L.PELAKU_PETUGAS, pengguna_id=900)
    kid = warga.get("/api/notifikasi").json()[0]["id"]
    r = warga.post(f"/api/notifikasi/{kid}/dibaca")
    assert r.status_code == 200
    assert r.json()["dibaca"] is True
    assert warga.get("/api/notifikasi").json()[0]["dibaca"] is True


def test_us25_kabar_orang_lain_tidak_bisa_dibaca_atau_ditandai(buat_klien):
    """Given kabar milik warga A / When warga B mencoba menandainya / Then 404 dan daftar B tetap kosong."""
    a = buat_klien("pelapor", email="a@uji.test")
    b = buat_klien("pelapor", email="b@uji.test")
    lap = _laporan_milik(a)
    L.ubah_status(lap.nomor, L.STATUS_SEDANG, L.PELAKU_PETUGAS, pengguna_id=900)
    kid = a.get("/api/notifikasi").json()[0]["id"]
    assert b.post(f"/api/notifikasi/{kid}/dibaca").status_code == 404
    assert b.get("/api/notifikasi").json() == []
    assert a.get("/api/notifikasi").json()[0]["dibaca"] is False


def test_us25_tidak_muncul_bila_dimatikan(buat_klien):
    """Given saya mematikan notifikasi / When status laporanku berubah / Then tidak ada kabar baru."""
    warga = buat_klien("pelapor", email="mati@uji.test")
    assert warga.get("/api/notifikasi/pengaturan").json() == {"aktif": True}
    assert warga.put("/api/notifikasi/pengaturan", json={"aktif": False}).json() == {"aktif": False}
    assert warga.get("/api/notifikasi/pengaturan").json() == {"aktif": False}
    lap = _laporan_milik(warga)
    L.ubah_status(lap.nomor, L.STATUS_SEDANG, L.PELAKU_PETUGAS, pengguna_id=900)
    assert warga.get("/api/notifikasi").json() == []


def test_us25_wajib_masuk(klien):
    """Given pengunjung belum masuk / When membuka kabar / Then 401."""
    assert klien.get("/api/notifikasi").status_code == 401
    assert klien.get("/api/notifikasi/pengaturan").status_code == 401
    assert klien.put("/api/notifikasi/pengaturan", json={"aktif": False}).status_code == 401
    assert klien.post("/api/notifikasi/1/dibaca").status_code == 401
