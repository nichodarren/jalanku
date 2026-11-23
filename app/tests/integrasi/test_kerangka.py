"""Walking skeleton: aplikasi utuh berjalan, aturan lintas modul berlaku (TS-01)."""

from __future__ import annotations

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient

from jalanku.core import BelumDibuat, jalankan_migrasi, muat_ulang_pengaturan
from jalanku.modules.akun import Pengguna, wajib_peran

# Route khusus test, supaya test mekanisme stub (501) & cek peran tidak bergantung pada modul mana
# yang kebetulan masih stub; kalau tidak, test ini patah setiap ada fitur yang selesai.
JALUR_STUB = "/api/_uji/stub"
JALUR_ADMIN = "/api/_uji/khusus-admin"


@pytest.fixture
def app():
    from jalanku.main import buat_app

    aplikasi = buat_app()

    def stub():
        raise BelumDibuat("US-00", "M1")

    def khusus_admin(pengguna: Pengguna = Depends(wajib_peran("admin"))) -> dict:
        return {"peran": pengguna.peran}

    jumlah = len(aplikasi.router.routes)
    aplikasi.add_api_route(JALUR_STUB, stub, methods=["GET"])
    aplikasi.add_api_route(JALUR_ADMIN, khusus_admin, methods=["GET"])
    # Taruh di depan: buat_app memasang berkas statis di "/" paling akhir, yang menangkap semua jalur.
    baru = aplikasi.router.routes[jumlah:]
    del aplikasi.router.routes[jumlah:]
    aplikasi.router.routes[0:0] = baru
    return aplikasi


def test_kesehatan(klien):
    r = klien.get("/api/kesehatan")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_web_app_tersaji(klien):
    r = klien.get("/")
    assert r.status_code == 200
    assert "JalanKu" in r.text


def test_header_keamanan(klien):
    for jalur in ("/", "/api/kesehatan"):
        h = klien.get(jalur).headers
        assert "script-src 'self'" in h["content-security-policy"]
        assert h["x-content-type-options"] == "nosniff"
        assert h["x-frame-options"] == "DENY"


def test_csrf_wajib_untuk_request_mengubah(app):
    tanpa_header = TestClient(app)
    r = tanpa_header.post("/api/akun/keluar")
    assert r.status_code == 403


def test_stub_mengembalikan_501_dengan_pesan(klien):
    r = klien.get(JALUR_STUB)
    assert r.status_code == 501
    assert r.json()["detail"] == "Fitur ini belum dibuat (US-00, pemilik M1)."


def test_masuk_dev_dan_sesi(buat_klien):
    admin = buat_klien("admin")
    saya = admin.get("/api/akun/saya").json()
    assert saya["peran"] == "admin" and saya["terverifikasi"] is True
    admin.post("/api/akun/keluar")
    assert admin.get("/api/akun/saya").json() is None


def test_peran_dicek_di_server(buat_klien, klien):
    assert klien.get(JALUR_ADMIN).status_code == 401
    assert buat_klien("pelapor").get(JALUR_ADMIN).status_code == 403
    assert buat_klien("petugas", instansi_id="SUDIN_JP").get(JALUR_ADMIN).status_code == 403
    r = buat_klien("admin").get(JALUR_ADMIN)
    assert r.status_code == 200
    assert r.json() == {"peran": "admin"}


def test_masuk_dev_tidak_ada_di_produksi(monkeypatch):
    monkeypatch.setenv("JALANKU_MODE", "prod")
    muat_ulang_pengaturan()
    from jalanku.main import buat_app

    klien = TestClient(buat_app(), headers={"X-JalanKu": "1"})
    r = klien.post("/api/dev/masuk", json={"email": "x@uji.test", "peran": "admin"})
    assert r.status_code in (404, 405)


def test_migrasi_idempoten():
    assert jalankan_migrasi() == []


def test_csp_longgar_hanya_di_dokumentasi_api(klien):
    assert "cdn.jsdelivr.net" in klien.get("/api/docs").headers["content-security-policy"]
    assert "cdn.jsdelivr.net" not in klien.get("/").headers["content-security-policy"]
