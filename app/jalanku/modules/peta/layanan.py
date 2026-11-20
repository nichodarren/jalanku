"""Logika data peta publik (US-15 aktif, US-16 riwayat). Pemilik: M6.

Diport dari jalanku-v0 ``app/jalanku/reports.py::titik_peta`` (karya Yosua), disesuaikan:
data diambil lewat antarmuka publik ``laporan`` (bukan SQL langsung) dan keluaran hanya
field kontrak ``TitikPetaKeluaran``. Identitas pelapor tidak pernah ikut (NFR-PRI-01).
"""

from __future__ import annotations

from itertools import product

from jalanku.modules.laporan import STATUS_BELUM, STATUS_SEDANG, STATUS_SELESAI, Laporan, cari_laporan, jumlah_dukungan

STATUS_PER_MODE: dict[str, tuple[str, ...]] = {
    "aktif": (STATUS_BELUM, STATUS_SEDANG),
    "riwayat": (STATUS_SELESAI,),
}
MAKS_NILAI_FILTER = 10
BATAS_TITIK = 5000


def _pecah(nilai: str | None) -> list[str | None]:
    """``"a,b"`` -> ``["a", "b"]`` (maks. 10, tanpa duplikat); kosong -> ``[None]`` artinya tanpa filter."""
    if not nilai:
        return [None]
    daftar = list(dict.fromkeys(v.strip() for v in nilai.split(",") if v.strip()))
    return daftar[:MAKS_NILAI_FILTER] or [None]


def _ke_titik(lap: Laporan) -> dict:
    return {
        "nomor": lap.nomor,
        "lat": round(lap.lat, 6),
        "lon": round(lap.lon, 6),
        "status": lap.status,
        "tingkat": lap.tingkat,
        "kota": lap.kota,
        "kecamatan": lap.kecamatan,
        "jumlah_dukungan": jumlah_dukungan(lap.id),
        "simulasi": lap.simulasi,
    }


def titik_peta(mode: str = "aktif", kota: str | None = None, tingkat: str | None = None) -> list[dict]:
    """Titik bubble peta. ``mode`` aktif = belum/sedang dikerjakan, riwayat = selesai.

    ``kota`` dan ``tingkat`` boleh berisi beberapa nilai dipisah koma (chip filter multi-pilih).
    Urutan: laporan terbaru dulu.
    """
    status = STATUS_PER_MODE[mode]
    terkumpul: dict[str, Laporan] = {}
    for k, t in product(_pecah(kota), _pecah(tingkat)):
        for lap in cari_laporan(status=status, kota=k, tingkat=t, batas=BATAS_TITIK):
            terkumpul[lap.nomor] = lap
    urut = sorted(terkumpul.values(), key=lambda lap: lap.id, reverse=True)[:BATAS_TITIK]
    return [_ke_titik(lap) for lap in urut]
