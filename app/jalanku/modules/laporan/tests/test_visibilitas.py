"""Visibilitas BR-06 (FR-LAP-03) lewat API: detail, timeline, berkas foto, hasil AI, header cache (TS-02).

Teknik: decision table status × penonton. Penonton: pengunjung, pelapor pemilik, pelapor lain,
petugas instansi laporan, petugas instansi lain, Admin. Yang tidak boleh melihat → 404 yang sama persis
dengan 404 laporan yang tidak ada (keberadaan laporan tidak bocor).
"""

from __future__ import annotations

import io

import pytest
from PIL import Image

from conftest import TITIK
from jalanku.core.kejadian import terbitkan
from jalanku.modules import laporan as L
from jalanku.modules.akun import AkunDihapus

PUBLIK = [L.STATUS_BELUM, L.STATUS_SEDANG, L.STATUS_SELESAI, L.STATUS_DIGABUNG]
PRIVAT = [L.STATUS_MENUNGGU, L.STATUS_DITOLAK]
HASIL_AI_BUKTI = {"kelas": "rusak", "confidence": 0.93, "keputusan": "terima"}
HASIL_AI_SESUDAH = {"kelas": "baik", "keputusan": "terima", "alasan": "Jalan tampak sudah baik"}


def _foto(warna=(90, 90, 90)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (64, 48), warna).save(buf, "JPEG")
    return buf.getvalue()


def _buat(pelapor_id: int | None, keputusan: str = "perlu_admin") -> L.Laporan:
    lat, lon = TITIK["monas"]
    return L.buat_laporan(
        L.LaporanBaru(
            pelapor_id=pelapor_id,
            lat=lat,
            lon=lon,
            sumber_lokasi="gps",
            kota="Jakarta Pusat",
            kecamatan="Gambir",
            instansi_id="SUDIN_JP",
            foto=[_foto()],
            keputusan_ai=keputusan,
            tingkat=L.TINGKAT_RUSAK if keputusan == "terverifikasi" else None,
            hasil_ai=[HASIL_AI_BUKTI],
        )
    )


def _dalam_status(status: str, pelapor_id: int | None) -> L.Laporan:
    if status == L.STATUS_MENUNGGU:
        return _buat(pelapor_id)
    if status == L.STATUS_DITOLAK:
        return _buat(pelapor_id, "ditolak")
    if status == L.STATUS_BELUM:
        return _buat(pelapor_id, "terverifikasi")
    if status == L.STATUS_SEDANG:
        return L.ubah_status(_buat(pelapor_id, "terverifikasi").nomor, L.STATUS_SEDANG, L.PELAKU_PETUGAS)
    if status == L.STATUS_SELESAI:
        return L.ubah_status(
            _buat(pelapor_id, "terverifikasi").nomor,
            L.STATUS_SELESAI,
            L.PELAKU_PETUGAS,
            foto_sesudah=_foto((200, 200, 200)),
            hasil_ai_sesudah=HASIL_AI_SESUDAH,
        )
    if status == L.STATUS_DIGABUNG:
        induk = _buat(None, "terverifikasi")
        return L.ubah_status(_buat(pelapor_id).nomor, L.STATUS_DIGABUNG, L.PELAKU_ADMIN, induk_nomor=induk.nomor)
    raise AssertionError(status)


@pytest.fixture
def penonton(buat_klien):
    """Enam jenis penonton → (klien, boleh melihat laporan privat milik ``pemilik``?)."""
    daftar = {
        "pengunjung": (buat_klien(), False),
        "pemilik": (buat_klien("pelapor", email="pemilik@uji.test"), True),
        "pelapor_lain": (buat_klien("pelapor", email="lain@uji.test"), False),
        "petugas_instansi_sama": (buat_klien("petugas", email="ptg1@uji.test", instansi_id="SUDIN_JP"), False),
        "petugas_instansi_lain": (buat_klien("petugas", email="ptg2@uji.test", instansi_id="SUDIN_JS"), False),
        "admin": (buat_klien("admin"), True),
    }
    return daftar


def _id(klien) -> int:
    return klien.get("/api/akun/saya").json()["id"]


def _url_foto(admin, nomor: str) -> list[str]:
    return [f["url"] for f in admin.get(f"/api/laporan/{nomor}").json()["foto"]]


# --- Matriks status × penonton --------------------------------------------------------------------


@pytest.mark.parametrize("status", PUBLIK + PRIVAT)
def test_matriks_detail_dan_foto(status, penonton):
    pemilik_id = _id(penonton["pemilik"][0])
    lap = _dalam_status(status, pemilik_id)
    assert lap.status == status
    urls = _url_foto(penonton["admin"][0], lap.nomor)
    assert urls  # setiap laporan punya minimal 1 foto
    for nama, (klien, boleh_privat) in penonton.items():
        harap = 200 if (status in PUBLIK or boleh_privat) else 404
        assert klien.get(f"/api/laporan/{lap.nomor}").status_code == harap, (status, nama, "detail")
        for url in urls:
            assert klien.get(url).status_code == harap, (status, nama, url)


@pytest.mark.parametrize("status", PRIVAT)
def test_404_privat_sama_persis_dengan_laporan_tidak_ada(status, klien, buat_klien):
    lap = _dalam_status(status, _id(buat_klien("pelapor", email="pemilik@uji.test")))
    tersembunyi = klien.get(f"/api/laporan/{lap.nomor}")
    tidak_ada = klien.get("/api/laporan/JK-99999")
    assert tersembunyi.status_code == tidak_ada.status_code == 404
    assert tersembunyi.json() == tidak_ada.json()


def test_foto_tidak_ada_404(klien):
    assert klien.get("/api/foto/999999").status_code == 404


# --- Hasil AI ----------------------------------------------------------------------------------


@pytest.mark.parametrize("status", PUBLIK)
def test_hasil_ai_foto_bukti_hanya_pemilik_dan_admin(status, penonton):
    lap = _dalam_status(status, _id(penonton["pemilik"][0]))
    for nama, (klien, boleh) in penonton.items():
        bukti = [f for f in klien.get(f"/api/laporan/{lap.nomor}").json()["foto"] if f["jenis"] == "bukti"]
        assert bukti, nama
        for f in bukti:
            assert (f["hasil_ai"] == HASIL_AI_BUKTI) if boleh else (f["hasil_ai"] is None), (status, nama)


def test_hasil_ai_foto_sesudah_publik_untuk_semua(penonton):
    lap = _dalam_status(L.STATUS_SELESAI, _id(penonton["pemilik"][0]))
    for nama, (klien, _) in penonton.items():
        sesudah = [f for f in klien.get(f"/api/laporan/{lap.nomor}").json()["foto"] if f["jenis"] == "sesudah"]
        assert len(sesudah) == 1 and sesudah[0]["hasil_ai"] == HASIL_AI_SESUDAH, nama


# --- Identitas pelapor -------------------------------------------------------------------------


@pytest.mark.parametrize("status", PUBLIK + PRIVAT)
def test_identitas_pelapor_tidak_pernah_tampil(status, penonton):
    lap = _dalam_status(status, _id(penonton["pemilik"][0]))
    for nama, (klien, _) in penonton.items():
        r = klien.get(f"/api/laporan/{lap.nomor}")
        if r.status_code == 200:
            teks = r.text
            assert "pelapor_id" not in teks and "pemilik@uji.test" not in teks and "pengguna_id" not in teks, nama


# --- Akun pelapor dihapus ----------------------------------------------------------------------


def test_setelah_akun_dihapus_laporan_privat_hanya_untuk_admin(buat_klien):
    L.pasang()
    pemilik = buat_klien("pelapor", email="pemilik@uji.test")
    lap = _dalam_status(L.STATUS_MENUNGGU, _id(pemilik))
    assert pemilik.get(f"/api/laporan/{lap.nomor}").status_code == 200
    terbitkan(AkunDihapus(_id(pemilik)))
    assert pemilik.get(f"/api/laporan/{lap.nomor}").status_code == 404
    assert buat_klien("admin").get(f"/api/laporan/{lap.nomor}").status_code == 200


def test_laporan_tanpa_pelapor_tidak_terbuka_untuk_siapa_pun_selain_admin():
    """Penjaga: pelapor_id kosong tidak boleh cocok dengan penonton mana pun."""
    lap = _dalam_status(L.STATUS_MENUNGGU, None)
    hantu = type("P", (), {"id": None, "peran": "pelapor"})()
    assert L.boleh_dilihat(lap, hantu) is False


# --- Header cache foto -------------------------------------------------------------------------


@pytest.mark.parametrize("status", PUBLIK)
def test_foto_laporan_publik_boleh_di_cache_bersama(status, klien, buat_klien):
    lap = _dalam_status(status, None)
    for url in _url_foto(buat_klien("admin"), lap.nomor):
        r = klien.get(url)
        assert r.status_code == 200 and r.headers["content-type"] == "image/jpeg"
        assert r.headers["cache-control"] == "public, max-age=86400"


@pytest.mark.parametrize("status", PRIVAT)
def test_foto_laporan_privat_tidak_boleh_disimpan_cache(status, buat_klien):
    pemilik = buat_klien("pelapor", email="pemilik@uji.test")
    lap = _dalam_status(status, _id(pemilik))
    for url in _url_foto(pemilik, lap.nomor):
        r = pemilik.get(url)
        assert r.status_code == 200 and r.headers["cache-control"] == "private, no-store"
