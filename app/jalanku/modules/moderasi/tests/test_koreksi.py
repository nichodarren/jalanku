"""US-21 koreksi tingkat oleh Admin: laporan.ubah_tingkat + baris moderasi_koreksi (FR-MOD-03)."""

from __future__ import annotations

from jalanku.core import koneksi
from jalanku.modules.laporan import (
    PELAKU_ADMIN,
    PELAKU_PETUGAS,
    STATUS_BELUM,
    STATUS_DITOLAK,
    STATUS_SEDANG,
    ambil_laporan,
    timeline,
    ubah_status,
)


def _koreksi(klien, nomor: str, tingkat: str = "kurang_baik", alasan: str = "Lubang ternyata dangkal"):
    return klien.post(f"/api/admin/laporan/{nomor}/tingkat", json={"tingkat": tingkat, "alasan": alasan})


def _baris_koreksi(laporan_id: int) -> list[tuple]:
    kon = koneksi()
    try:
        return kon.execute(
            "SELECT admin_id, tingkat_lama, tingkat_baru, alasan FROM moderasi_koreksi WHERE laporan_id = ?",
            (laporan_id,),
        ).fetchall()
    finally:
        kon.close()


def test_koreksi_mengubah_tingkat_dan_tercatat(buat_klien, bikin_laporan):
    admin = buat_klien("admin")
    admin_id = admin.get("/api/akun/saya").json()["id"]
    lap = bikin_laporan(status_awal=STATUS_BELUM)  # tingkat rusak
    assert lap.tingkat == "rusak"

    r = _koreksi(admin, lap.nomor, alasan="  Lubang ternyata dangkal  ")

    assert r.status_code == 200
    assert r.json() == {"nomor": lap.nomor, "status": STATUS_BELUM, "tingkat": "kurang_baik"}
    sesudah = ambil_laporan(lap.nomor)
    assert sesudah.tingkat == "kurang_baik"
    assert sesudah.label_akhir == "kurang_baik"
    assert [tuple(b) for b in _baris_koreksi(lap.id)] == [(admin_id, "rusak", "kurang_baik", "Lubang ternyata dangkal")]
    terakhir = timeline(lap.id)[-1]
    assert terakhir.pelaku == PELAKU_ADMIN and "kurang_baik" in terakhir.catatan


def test_koreksi_laporan_sedang_dikerjakan_boleh(buat_klien, bikin_laporan):
    lap = bikin_laporan(status_awal=STATUS_BELUM)
    ubah_status(lap.nomor, STATUS_SEDANG, PELAKU_PETUGAS, pengguna_id=900)

    r = _koreksi(buat_klien("admin"), lap.nomor)

    assert r.status_code == 200
    assert r.json()["status"] == STATUS_SEDANG


def test_koreksi_validasi_masukan_400_tanpa_baris_baru(buat_klien, bikin_laporan):
    admin = buat_klien("admin")
    lap = bikin_laporan(status_awal=STATUS_BELUM)

    assert _koreksi(admin, lap.nomor, tingkat="parah").status_code == 400
    assert _koreksi(admin, lap.nomor, tingkat="rusak").status_code == 400  # sama dengan sekarang
    pendek = _koreksi(admin, lap.nomor, alasan="  abcd ")  # lolos skema, 4 karakter setelah strip
    assert pendek.status_code == 400
    assert "minimal 5 karakter" in pendek.json()["detail"]
    assert _baris_koreksi(lap.id) == []
    assert ambil_laporan(lap.nomor).tingkat == "rusak"


def test_koreksi_hanya_laporan_terverifikasi_yang_belum_selesai(buat_klien, bikin_laporan):
    admin = buat_klien("admin")
    menunggu = bikin_laporan()
    ditolak = bikin_laporan(keputusan_ai=STATUS_DITOLAK)

    assert _koreksi(admin, menunggu.nomor).status_code == 409
    assert _koreksi(admin, ditolak.nomor).status_code == 409
    assert _koreksi(admin, "JK-99999").status_code == 404
    assert _baris_koreksi(menunggu.id) == [] and _baris_koreksi(ditolak.id) == []


def test_otorisasi_koreksi(buat_klien, bikin_laporan):
    lap = bikin_laporan(status_awal=STATUS_BELUM)

    assert _koreksi(buat_klien(), lap.nomor).status_code == 401
    assert _koreksi(buat_klien("pelapor"), lap.nomor).status_code == 403
    assert _koreksi(buat_klien("petugas", instansi_id="SUDIN_JP"), lap.nomor).status_code == 403
    assert ambil_laporan(lap.nomor).tingkat == "rusak"
