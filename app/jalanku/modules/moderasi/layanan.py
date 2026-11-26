from __future__ import annotations

from jalanku.core import Konflik, TidakValid
from jalanku.modules.laporan import (
    PELAKU_ADMIN,
    STATUS_AKTIF,
    STATUS_BELUM,
    STATUS_DIGABUNG,
    STATUS_DITOLAK,
    STATUS_MENUNGGU,
    TINGKAT_KURANG_BAIK,
    TINGKAT_RUSAK,
    ambil_laporan,
    cari_aktif_dekat,
    cari_laporan,
    daftar_foto,
    ubah_status,
)

TINGKAT_SAH = {TINGKAT_KURANG_BAIK, TINGKAT_RUSAK}
MIN_ALASAN = 5  # samakan dengan syarat BR-03 di laporan.ubah_status


def antrean() -> list[dict]:
    daftar = cari_laporan(status=STATUS_MENUNGGU)
    daftar_terurut = sorted(
        daftar,
        key=lambda lap: (0 if lap.banding_pada else 1, lap.dibuat_pada, lap.id),
    )
    hasil: list[dict] = []
    for lap in daftar_terurut:
        fotos = [
            {"url": f"/api/foto/{f.id}", "hasil_ai": f.hasil_ai} for f in daftar_foto(lap.id) if f.jenis == "bukti"
        ]
        dekat = cari_aktif_dekat(lap.lat, lap.lon, radius_m=25.0)
        duplikat = [{"nomor": rekan.nomor, "jarak_m": round(jarak, 1)} for rekan, jarak in dekat if rekan.id != lap.id]
        hasil.append(
            {
                "nomor": lap.nomor,
                "dibuat_pada": lap.dibuat_pada,
                "banding": bool(lap.banding_pada),
                "kota": lap.kota,
                "kecamatan": lap.kecamatan,
                "keterangan": lap.keterangan,
                "foto": fotos,
                "duplikat": duplikat,
            }
        )
    return hasil


def verifikasi(nomor: str, tingkat: str, pengguna_id: int) -> dict:
    if tingkat not in TINGKAT_SAH:
        raise TidakValid("Tingkat kerusakan harus kurang_baik atau rusak.")
    lap = ambil_laporan(nomor)
    if lap.status != STATUS_MENUNGGU:
        raise Konflik("Hanya laporan berstatus menunggu_verifikasi yang bisa diverifikasi.")
    hasil = ubah_status(
        nomor,
        STATUS_BELUM,
        PELAKU_ADMIN,
        pengguna_id=pengguna_id,
        tingkat=tingkat,
        label_akhir=tingkat,
        catatan=f"Diverifikasi Admin ({tingkat})",
    )
    return {"nomor": hasil.nomor, "status": hasil.status, "tingkat": hasil.tingkat}


def tolak(nomor: str, alasan: str, pengguna_id: int, label: str | None = None) -> dict:
    alasan_bersih = alasan.strip()
    if len(alasan_bersih) < MIN_ALASAN:
        raise TidakValid(f"Alasan penolakan wajib diisi (minimal {MIN_ALASAN} karakter).")
    lap = ambil_laporan(nomor)
    if lap.status != STATUS_MENUNGGU:
        raise Konflik("Hanya laporan berstatus menunggu_verifikasi yang bisa ditolak.")
    label_bersih = label.strip() if isinstance(label, str) and label.strip() else None
    hasil = ubah_status(
        nomor,
        STATUS_DITOLAK,
        PELAKU_ADMIN,
        pengguna_id=pengguna_id,
        catatan=alasan_bersih,
        label_akhir=label_bersih,
    )
    return {"nomor": hasil.nomor, "status": hasil.status, "tingkat": hasil.tingkat}


def gabung(nomor: str, induk_nomor: str, pengguna_id: int) -> dict:
    target_induk = induk_nomor.strip().upper()
    if not target_induk:
        raise TidakValid("Nomor laporan induk wajib diisi.")
    lap = ambil_laporan(nomor)
    induk = ambil_laporan(target_induk)
    if induk.id == lap.id:
        raise TidakValid("Laporan tidak bisa digabung ke dirinya sendiri.")
    if lap.status not in (STATUS_MENUNGGU, STATUS_BELUM):
        raise Konflik("Laporan tidak bisa digabung dari status saat ini.")
    if induk.status not in STATUS_AKTIF:
        raise Konflik("Laporan induk harus masih aktif.")
    hasil = ubah_status(
        nomor,
        STATUS_DIGABUNG,
        PELAKU_ADMIN,
        pengguna_id=pengguna_id,
        induk_nomor=induk.nomor,
        catatan=f"Digabung ke {induk.nomor}",
    )
    return {"nomor": hasil.nomor, "status": hasil.status, "tingkat": hasil.tingkat}
