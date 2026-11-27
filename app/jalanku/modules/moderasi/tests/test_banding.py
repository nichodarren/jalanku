"""US-13 banding: pelapor meminta Admin meninjau penolakan AI (BR-03, sekali)."""

from __future__ import annotations

from jalanku.modules.laporan import (
    PELAKU_ADMIN,
    PELAKU_PELAPOR,
    STATUS_DITOLAK,
    STATUS_MENUNGGU,
    ambil_laporan,
    timeline,
    ubah_status,
)


def _id(klien) -> int:
    return klien.get("/api/akun/saya").json()["id"]


def _banding(klien, nomor: str):
    return klien.post(f"/api/laporan/{nomor}/banding")


def test_banding_penolakan_ai_jadi_menunggu_dan_tercatat(buat_klien, bikin_laporan):
    pelapor = buat_klien("pelapor")
    lap = bikin_laporan(pelapor_id=_id(pelapor), keputusan_ai=STATUS_DITOLAK)
    assert lap.status == STATUS_DITOLAK and lap.diperiksa_oleh == "ai"

    r = _banding(pelapor, lap.nomor)

    assert r.status_code == 200
    assert r.json() == {"nomor": lap.nomor, "status": STATUS_MENUNGGU, "tingkat": None}
    sesudah = ambil_laporan(lap.nomor)
    assert sesudah.status == STATUS_MENUNGGU
    assert sesudah.banding_pada is not None
    terakhir = timeline(lap.id)[-1]
    assert (terakhir.dari_status, terakhir.ke_status, terakhir.pelaku) == (
        STATUS_DITOLAK,
        STATUS_MENUNGGU,
        PELAKU_PELAPOR,
    )


def test_banding_kedua_409_tanpa_entri_timeline_baru(buat_klien, bikin_laporan):
    pelapor = buat_klien("pelapor")
    pid = _id(pelapor)
    lap = bikin_laporan(pelapor_id=pid, keputusan_ai=STATUS_DITOLAK)
    assert _banding(pelapor, lap.nomor).status_code == 200
    # Admin menolak lagi setelah meninjau; pelapor mencoba banding kedua kalinya.
    ubah_status(lap.nomor, STATUS_DITOLAK, PELAKU_ADMIN, pengguna_id=99, catatan="Tetap bukan jalan rusak")
    jumlah_entri = len(timeline(lap.id))

    r = _banding(pelapor, lap.nomor)

    assert r.status_code == 409
    assert len(timeline(lap.id)) == jumlah_entri
    assert ambil_laporan(lap.nomor).status == STATUS_DITOLAK


def test_penolakan_admin_tidak_bisa_dibanding(buat_klien, bikin_laporan):
    pelapor = buat_klien("pelapor")
    lap = bikin_laporan(pelapor_id=_id(pelapor))
    ubah_status(lap.nomor, STATUS_DITOLAK, PELAKU_ADMIN, pengguna_id=99, catatan="Foto bukan jalan")

    r = _banding(pelapor, lap.nomor)

    assert r.status_code == 409
    assert ambil_laporan(lap.nomor).status == STATUS_DITOLAK


def test_laporan_yang_tidak_ditolak_tidak_bisa_dibanding(buat_klien, bikin_laporan):
    pelapor = buat_klien("pelapor")
    lap = bikin_laporan(pelapor_id=_id(pelapor))  # menunggu_verifikasi

    r = _banding(pelapor, lap.nomor)

    assert r.status_code == 409
    assert ambil_laporan(lap.nomor).status == STATUS_MENUNGGU


def test_otorisasi_banding(buat_klien, bikin_laporan):
    pemilik = buat_klien("pelapor", email="pemilik@uji.test")
    lain = buat_klien("pelapor", email="lain@uji.test")
    admin = buat_klien("admin")
    lap = bikin_laporan(pelapor_id=_id(pemilik), keputusan_ai=STATUS_DITOLAK)

    assert _banding(buat_klien(), lap.nomor).status_code == 401
    # BR-06: laporan ditolak tidak terlihat oleh pelapor lain → 404, bukan 403.
    assert _banding(lain, lap.nomor).status_code == 404
    # Admin boleh melihat, tetapi banding hanya hak pelapornya.
    assert _banding(admin, lap.nomor).status_code == 403
    assert _banding(pemilik, "JK-99999").status_code == 404
    assert ambil_laporan(lap.nomor).status == STATUS_DITOLAK
