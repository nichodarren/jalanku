from __future__ import annotations

from jalanku.core.waktu import atur_waktu
from jalanku.modules.laporan import STATUS_BELUM, STATUS_DITOLAK


def test_antrean_hanya_menunggu_urut_banding_lalu_terlama(buat_klien, bikin_laporan):
    admin = buat_klien("admin")
    atur_waktu("2026-11-19T08:00:00Z")
    lap_lama = bikin_laporan(keterangan="Lama")
    atur_waktu("2026-11-19T09:00:00Z")
    lap_baru = bikin_laporan(keterangan="Baru")
    atur_waktu("2026-11-19T10:00:00Z")
    lap_banding = bikin_laporan(keterangan="Banding", banding=True)
    atur_waktu("2026-11-19T11:00:00Z")
    bikin_laporan(keterangan="Sudah verif", status_awal=STATUS_BELUM)
    bikin_laporan(keterangan="Ditolak AI", keputusan_ai=STATUS_DITOLAK)
    atur_waktu(None)

    resp = admin.get("/api/admin/antrean")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    nomors = [item["nomor"] for item in data]
    assert nomors == [lap_banding.nomor, lap_lama.nomor, lap_baru.nomor]
    assert data[0]["banding"] is True
    assert data[1]["banding"] is False


def test_antrean_tanpa_identitas_pelapor_dan_memuat_foto_serta_duplikat(buat_klien, bikin_laporan):
    admin = buat_klien("admin")
    induk_aktif = bikin_laporan(lat=-6.1754, lon=106.8272, status_awal=STATUS_BELUM)
    target = bikin_laporan(
        lat=-6.1755,
        lon=106.8272,
        pelapor_id=99,
        keterangan="Lubang dekat monas",
        hasil_ai=[{"kelas": "kurang_baik", "confidence": 0.62}],
    )
    bikin_laporan(lat=-6.2441, lon=106.8003, keterangan="Jauh")

    resp = admin.get("/api/admin/antrean")
    assert resp.status_code == 200
    items = {item["nomor"]: item for item in resp.json()}
    item = items[target.nomor]

    assert "pelapor_id" not in item
    assert "email" not in item
    assert len(item["foto"]) == 1
    assert item["foto"][0]["url"].startswith("/api/foto/")
    assert item["foto"][0]["hasil_ai"]["kelas"] == "kurang_baik"

    dups = [d["nomor"] for d in item["duplikat"]]
    assert induk_aktif.nomor in dups
    assert target.nomor not in dups
    for d in item["duplikat"]:
        assert d["jarak_m"] <= 25.0
