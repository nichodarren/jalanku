"""US-32 / BR-09 jejak audit: setiap entri timeline dirantai hash; publik bisa memeriksa keutuhannya.

Rantai: ``hash_n = sha256(hash_(n-1) + isi entri n)``, entri pertama memakai string kosong. Mengubah,
menghapus, atau menyisipkan entri langsung di DB (di luar aplikasi) membuat ``utuh = false``.
"""

from __future__ import annotations

import hashlib
import json

import pytest

from conftest import TITIK, foto_bytes
from jalanku.core import koneksi
from jalanku.modules import laporan as L
from jalanku.modules.laporan.layanan import _hash_entri


def _buat(keputusan: str = "terverifikasi", pelapor_id: int | None = 1) -> L.Laporan:
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
            foto=[foto_bytes()],
            keputusan_ai=keputusan,
            tingkat=L.TINGKAT_RUSAK if keputusan == "terverifikasi" else None,
        )
    )


def _selesai() -> L.Laporan:
    lap = _buat()
    L.ubah_status(lap.nomor, L.STATUS_SEDANG, L.PELAKU_PETUGAS, pengguna_id=50, catatan="Mulai | tambal")
    return L.ubah_status(lap.nomor, L.STATUS_SELESAI, L.PELAKU_PETUGAS, pengguna_id=50, foto_sesudah=foto_bytes())


def _baris(laporan_id: int) -> list[dict]:
    kon = koneksi()
    try:
        rows = kon.execute("SELECT * FROM laporan_timeline WHERE laporan_id = ? ORDER BY id", (laporan_id,))
        return [dict(r) for r in rows]
    finally:
        kon.close()


def _sql(perintah: str, *param) -> None:
    kon = koneksi()
    try:
        kon.execute(perintah, param)
        kon.commit()
    finally:
        kon.close()


# --- Hash saat mencatat ---------------------------------------------------------------------------


def test_setiap_entri_punya_hash_sha256():
    lap = _selesai()
    hashes = [b["hash"] for b in _baris(lap.id)]
    assert len(hashes) == 3
    assert all(isinstance(h, str) and len(h) == 64 and int(h, 16) >= 0 for h in hashes)
    assert len(set(hashes)) == 3


def test_entri_pertama_memakai_string_kosong_lalu_berantai():
    lap = _selesai()
    b = _baris(lap.id)
    isi = lambda r: json.dumps(  # noqa: E731
        [r["dari_status"], r["ke_status"], r["pelaku"], r["catatan"], r["waktu"]],
        ensure_ascii=False,
        separators=(",", ":"),
    )
    assert b[0]["hash"] == hashlib.sha256(("" + isi(b[0])).encode()).hexdigest()
    assert b[1]["hash"] == hashlib.sha256((b[0]["hash"] + isi(b[1])).encode()).hexdigest()
    assert b[2]["hash"] == hashlib.sha256((b[1]["hash"] + isi(b[2])).encode()).hexdigest()


def test_isi_berbeda_dengan_pemisah_dalam_catatan_menghasilkan_hash_berbeda():
    # "|" di catatan tidak bisa dipakai menggeser isi antar-field (pengodean JSON tidak ambigu).
    a = _hash_entri("", None, "selesai", "petugas", "a|b", "2026-11-20T10:00:00+07:00")
    b = _hash_entri("", None, "selesai", "petugas|a", "b", "2026-11-20T10:00:00+07:00")
    assert a != b


def test_rantai_per_laporan_tidak_saling_memengaruhi():
    a = _buat()
    hash_a = [b["hash"] for b in _baris(a.id)]
    b = _buat()
    L.ubah_status(b.nomor, L.STATUS_SEDANG, L.PELAKU_PETUGAS, pengguna_id=50)
    assert [r["hash"] for r in _baris(a.id)] == hash_a
    # entri pertama B berantai dari string kosong, bukan dari entri terakhir A
    assert _baris(b.id)[0]["hash"] == _hash_entri(
        "", *(_baris(b.id)[0][k] for k in ("dari_status", "ke_status", "pelaku", "catatan", "waktu"))
    )


# --- Pemeriksaan keutuhan lewat API --------------------------------------------------------------


def test_jejak_utuh_untuk_riwayat_normal(klien):
    lap = _selesai()
    r = klien.get(f"/api/laporan/{lap.nomor}/jejak")
    assert r.status_code == 200
    j = r.json()
    assert j["nomor"] == lap.nomor
    assert j["utuh"] is True
    assert [e["ke_status"] for e in j["entri"]] == [L.STATUS_BELUM, L.STATUS_SEDANG, L.STATUS_SELESAI]
    assert [e["hash"] for e in j["entri"]] == [b["hash"] for b in _baris(lap.id)]
    assert set(j["entri"][0]) == {"ke_status", "pelaku", "waktu", "hash"}  # tanpa pengguna_id / catatan


@pytest.mark.parametrize(
    "ubah",
    [
        "UPDATE laporan_timeline SET catatan = 'diubah diam-diam' WHERE id = :id",
        "UPDATE laporan_timeline SET waktu = '2020-01-01T00:00:00+07:00' WHERE id = :id",
        "UPDATE laporan_timeline SET pelaku = 'admin' WHERE id = :id",
        "UPDATE laporan_timeline SET ke_status = 'ditolak' WHERE id = :id",
        "UPDATE laporan_timeline SET dari_status = 'menunggu_verifikasi' WHERE id = :id",
        "UPDATE laporan_timeline SET hash = NULL WHERE id = :id",
        "DELETE FROM laporan_timeline WHERE id = :id",
    ],
    ids=["catatan", "waktu", "pelaku", "ke_status", "dari_status", "hash-dihapus", "entri-dihapus"],
)
def test_mengubah_satu_entri_di_db_membuat_tidak_utuh(klien, ubah):
    lap = _selesai()
    tengah = _baris(lap.id)[1]["id"]
    kon = koneksi()
    try:
        kon.execute(ubah, {"id": tengah})
        kon.commit()
    finally:
        kon.close()
    assert klien.get(f"/api/laporan/{lap.nomor}/jejak").json()["utuh"] is False


def test_menyisipkan_entri_palsu_membuat_tidak_utuh(klien):
    lap = _selesai()
    _sql(
        "INSERT INTO laporan_timeline (laporan_id, dari_status, ke_status, pelaku, catatan, waktu, hash) "
        "VALUES (?, 'selesai', 'selesai', 'admin', 'palsu', '2026-12-01T00:00:00+07:00', ?)",
        lap.id,
        "0" * 64,
    )
    assert klien.get(f"/api/laporan/{lap.nomor}/jejak").json()["utuh"] is False


def test_menghapus_entri_terakhir_tidak_bisa_disembunyikan_dari_status(klien):
    # Entri terakhir dihapus: rantai sisa tetap cocok, tapi status laporan tidak lagi sama dengan ujung rantai.
    lap = _selesai()
    _sql("DELETE FROM laporan_timeline WHERE id = ?", _baris(lap.id)[-1]["id"])
    assert klien.get(f"/api/laporan/{lap.nomor}/jejak").json()["utuh"] is False


def test_jejak_mengikuti_visibilitas_br06(buat_klien, klien):
    pelapor = buat_klien("pelapor", email="jejak@uji.test")
    pid = pelapor.get("/api/akun/saya").json()["id"]
    lap = _buat(keputusan="perlu_admin", pelapor_id=pid)  # menunggu verifikasi = privat
    assert klien.get(f"/api/laporan/{lap.nomor}/jejak").status_code == 404
    assert pelapor.get(f"/api/laporan/{lap.nomor}/jejak").json()["utuh"] is True


def test_jejak_laporan_tidak_ada_404(klien):
    assert klien.get("/api/laporan/JK-99999/jejak").status_code == 404
