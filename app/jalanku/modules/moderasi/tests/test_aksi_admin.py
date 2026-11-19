from __future__ import annotations

from jalanku.modules.laporan import STATUS_BELUM, STATUS_DIGABUNG, STATUS_DITOLAK, ambil_laporan


def test_otorisasi_antrean_dan_aksi_admin(buat_klien, bikin_laporan):
    lap = bikin_laporan()
    tamu = buat_klien()
    pelapor = buat_klien("pelapor")
    assert tamu.get("/api/admin/antrean").status_code == 401
    assert pelapor.get("/api/admin/antrean").status_code == 403
    assert pelapor.post(f"/api/admin/laporan/{lap.nomor}/verifikasi", json={"tingkat": "rusak"}).status_code == 403
    assert pelapor.post(f"/api/admin/laporan/{lap.nomor}/tolak", json={"alasan": "Foto buram"}).status_code == 403
    assert pelapor.post(f"/api/admin/laporan/{lap.nomor}/gabung", json={"induk_nomor": lap.nomor}).status_code == 403


def test_verifikasi_berhasil_tingkat_salah_400_dan_bukan_menunggu_409(buat_klien, bikin_laporan):
    admin = buat_klien("admin")
    lap = bikin_laporan()
    assert admin.post(f"/api/admin/laporan/{lap.nomor}/verifikasi", json={"tingkat": "parah_sekali"}).status_code == 400
    ok = admin.post(f"/api/admin/laporan/{lap.nomor}/verifikasi", json={"tingkat": "rusak"})
    assert ok.status_code == 200
    assert ok.json() == {"nomor": lap.nomor, "status": STATUS_BELUM, "tingkat": "rusak"}
    assert ambil_laporan(lap.nomor).status == STATUS_BELUM
    assert admin.post(f"/api/admin/laporan/{lap.nomor}/verifikasi", json={"tingkat": "rusak"}).status_code == 409


def test_tolak_dengan_alasan_dan_label_serta_validasi_alasan(buat_klien, bikin_laporan):
    admin = buat_klien("admin")
    lap = bikin_laporan()
    kosong = admin.post(f"/api/admin/laporan/{lap.nomor}/tolak", json={"alasan": "  ", "label": "bukan_jalan"})
    assert kosong.status_code in (400, 422)
    ok = admin.post(
        f"/api/admin/laporan/{lap.nomor}/tolak",
        json={"alasan": "Bukan kerusakan jalan", "label": "bukan_jalan"},
    )
    assert ok.status_code == 200
    assert ok.json()["status"] == STATUS_DITOLAK
    assert ambil_laporan(lap.nomor).label_akhir == "bukan_jalan"


def test_gabung_induk_aktif_diri_sendiri_400_dan_induk_tidak_aktif_409(buat_klien, bikin_laporan):
    admin = buat_klien("admin")
    induk = bikin_laporan(status_awal=STATUS_BELUM)
    anak = bikin_laporan()
    ditolak = bikin_laporan(keputusan_ai=STATUS_DITOLAK)
    assert admin.post(f"/api/admin/laporan/{anak.nomor}/gabung", json={"induk_nomor": anak.nomor}).status_code == 400
    assert admin.post(f"/api/admin/laporan/{anak.nomor}/gabung", json={"induk_nomor": ditolak.nomor}).status_code == 409
    ok = admin.post(f"/api/admin/laporan/{anak.nomor}/gabung", json={"induk_nomor": induk.nomor})
    assert ok.status_code == 200
    assert ok.json()["status"] == STATUS_DIGABUNG
    assert ambil_laporan(anak.nomor).status == STATUS_DIGABUNG
