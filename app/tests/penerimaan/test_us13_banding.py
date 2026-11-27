"""US-13 Ajukan banding atas penolakan AI (pemilik M5). Skenario penerimaan lewat API (issue #47)."""

from __future__ import annotations

from conftest import TITIK, foto_bytes
from jalanku.modules import laporan as L


def _laporan_milik(klien, keputusan_ai: str) -> L.Laporan:
    """Laporan SIMULASI milik pengguna ``klien`` dengan keputusan AI tertentu."""
    pid = klien.get("/api/akun/saya").json()["id"] if klien is not None else None
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
            keputusan_ai=keputusan_ai,
        )
    )


def test_us13_banding_penolakan_ai_naik_ke_atas_antrean(buat_klien):
    """Given laporan SIMULASI milik pelapor ditolak AI dan belum pernah dibanding / When pelapor
    mengajukan banding / Then status menjadi menunggu_verifikasi dan banding muncul di atas laporan
    biasa pada antrean Admin."""
    warga = buat_klien("pelapor", email="banding@uji.test")
    biasa = _laporan_milik(buat_klien("pelapor", email="biasa@uji.test"), "perlu_admin")
    ditolak = _laporan_milik(warga, "ditolak")
    assert ditolak.status == L.STATUS_DITOLAK

    r = warga.post(f"/api/laporan/{ditolak.nomor}/banding")

    assert r.status_code == 200
    assert r.json()["status"] == L.STATUS_MENUNGGU
    antrean = buat_klien("admin").get("/api/admin/antrean").json()
    assert [item["nomor"] for item in antrean] == [ditolak.nomor, biasa.nomor]
    assert antrean[0]["banding"] is True and antrean[1]["banding"] is False


def test_us13_banding_kedua_ditolak_tanpa_entri_baru(buat_klien):
    """Given laporan sudah pernah dibanding / When pelapor mengajukan lagi / Then banding kedua
    ditolak tanpa membuat entri baru."""
    warga = buat_klien("pelapor", email="dua-kali@uji.test")
    lap = _laporan_milik(warga, "ditolak")
    assert warga.post(f"/api/laporan/{lap.nomor}/banding").status_code == 200
    L.ubah_status(lap.nomor, L.STATUS_DITOLAK, L.PELAKU_ADMIN, pengguna_id=99, catatan="Tetap bukan jalan rusak")
    entri_sebelum = len(L.timeline(lap.id))

    r = warga.post(f"/api/laporan/{lap.nomor}/banding")

    assert r.status_code == 409
    assert len(L.timeline(lap.id)) == entri_sebelum


def test_us13_penolakan_admin_tidak_bisa_dibanding(buat_klien):
    """Given penolakan berasal dari Admin / When pelapor meminta banding / Then permintaan ditolak
    dan status tetap."""
    warga = buat_klien("pelapor", email="ditolak-admin@uji.test")
    lap = _laporan_milik(warga, "perlu_admin")
    L.ubah_status(lap.nomor, L.STATUS_DITOLAK, L.PELAKU_ADMIN, pengguna_id=99, catatan="Foto bukan jalan")

    r = warga.post(f"/api/laporan/{lap.nomor}/banding")

    assert r.status_code == 409
    assert L.ambil_laporan(lap.nomor).status == L.STATUS_DITOLAK
