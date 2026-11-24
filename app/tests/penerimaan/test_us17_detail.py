"""US-17 Detail laporan + timeline (pemilik M1). Skenario penerimaan lewat API publik.

Halaman `#/laporan/:nomor` (web/modules/laporan/) hanya menampilkan data dari `GET /api/laporan/{nomor}`;
yang dijaga di sini adalah data yang sampai ke warga: tanpa identitas pelapor, foto sebelum/sesudah,
timeline dengan pelaku, dan penanda SIMULASI.
"""

from __future__ import annotations

from conftest import TITIK, foto_bytes
from jalanku.modules import laporan as L

EMAIL_PELAPOR = "rahasia.pelapor@uji.test"


def _laporan_selesai(pelapor_id: int, *, simulasi: bool = False) -> L.Laporan:
    lat, lon = TITIK["monas"]
    lap = L.buat_laporan(
        L.LaporanBaru(
            pelapor_id=pelapor_id,
            lat=lat,
            lon=lon,
            sumber_lokasi="gps",
            kota="Jakarta Pusat",
            kecamatan="Gambir",
            instansi_id="SUDIN_JP",
            foto=[foto_bytes(warna=(80, 80, 80)), foto_bytes(warna=(120, 120, 120))],
            keputusan_ai="terverifikasi",
            tingkat=L.TINGKAT_RUSAK,
            keterangan="Lubang di lajur kiri",
            simulasi=simulasi,
        )
    )
    L.ubah_status(lap.nomor, L.STATUS_SEDANG, L.PELAKU_PETUGAS, pengguna_id=900)
    return L.ubah_status(
        lap.nomor,
        L.STATUS_SELESAI,
        L.PELAKU_PETUGAS,
        pengguna_id=900,
        catatan="Tambal sulam 2 x 3 m",
        foto_sesudah=foto_bytes(warna=(30, 30, 30)),
    )


def _id_pelapor(buat_klien) -> int:
    pelapor = buat_klien("pelapor", email=EMAIL_PELAPOR)
    return pelapor.get("/api/akun/saya").json()["id"]


def test_us17_identitas_pelapor_tidak_ada_di_respons(buat_klien, klien):
    """Given laporan publik milik seorang warga / When pengunjung membuka detailnya
    / Then respons tidak memuat id, nama, atau email pelapor."""
    lap = _laporan_selesai(_id_pelapor(buat_klien))
    r = klien.get(f"/api/laporan/{lap.nomor}")
    assert r.status_code == 200
    teks = r.text
    assert "pelapor_id" not in teks
    assert "rahasia.pelapor" not in teks
    assert "uji.test" not in teks


def test_us17_foto_sebelum_dan_sesudah_tampil_untuk_laporan_selesai(buat_klien, klien):
    """Given laporan berstatus Selesai dengan foto perbaikan / When pengunjung membuka detailnya
    / Then foto bukti (sebelum) dan foto sesudah tersedia dan bisa diambil."""
    lap = _laporan_selesai(_id_pelapor(buat_klien))
    d = klien.get(f"/api/laporan/{lap.nomor}").json()
    assert d["status"] == L.STATUS_SELESAI
    jenis = [f["jenis"] for f in d["foto"]]
    assert jenis.count("bukti") == 2
    assert jenis.count("sesudah") == 1
    for f in d["foto"]:
        g = klien.get(f["url"])
        assert g.status_code == 200
        assert g.headers["content-type"] == "image/jpeg"


def test_us17_timeline_menyebut_pelaku_setiap_langkah(buat_klien, klien):
    """Given laporan yang diverifikasi AI lalu dikerjakan petugas sampai selesai / When detailnya dibuka
    / Then timeline urut waktu dan setiap entri menyebut pelakunya (AI JalanKu, Petugas)."""
    lap = _laporan_selesai(_id_pelapor(buat_klien))
    d = klien.get(f"/api/laporan/{lap.nomor}").json()
    langkah = [(t["ke_status"], t["pelaku"]) for t in d["timeline"]]
    assert langkah == [
        (L.STATUS_BELUM, L.PELAKU_AI),
        (L.STATUS_SEDANG, L.PELAKU_PETUGAS),
        (L.STATUS_SELESAI, L.PELAKU_PETUGAS),
    ]
    assert d["timeline"][-1]["catatan"] == "Tambal sulam 2 x 3 m"
    assert d["diperiksa_oleh"] == L.PELAKU_AI


def test_us17_penanda_simulasi(buat_klien, klien):
    """Given laporan data SIMULASI / When detailnya dibuka / Then respons menandainya simulasi."""
    asli = _laporan_selesai(_id_pelapor(buat_klien))
    simulasi = _laporan_selesai(_id_pelapor(buat_klien), simulasi=True)
    assert klien.get(f"/api/laporan/{asli.nomor}").json()["simulasi"] is False
    assert klien.get(f"/api/laporan/{simulasi.nomor}").json()["simulasi"] is True


def test_us17_instansi_tujuan_bisa_ditampilkan(buat_klien, klien):
    """Given laporan diteruskan ke Sudin / When halaman detail mencari nama & kanal resminya
    / Then instansi_id di detail ada di daftar GET /api/instansi."""
    lap = _laporan_selesai(_id_pelapor(buat_klien))
    d = klien.get(f"/api/laporan/{lap.nomor}").json()
    instansi = {i["id"]: i for i in klien.get("/api/instansi").json()}
    assert d["instansi_id"] in instansi
    assert instansi[d["instansi_id"]]["kanal_url"].startswith("https://")


def test_us17_laporan_tidak_ada_404(klien):
    """Given nomor yang tidak ada / When dibuka / Then 404 dengan pesan, bukan halaman rusak."""
    r = klien.get("/api/laporan/JK-99999")
    assert r.status_code == 404
    assert r.json()["detail"]
