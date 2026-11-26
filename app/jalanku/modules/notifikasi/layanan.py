"""Notifikasi in-app (FR-NTF-01, US-25). Pemilik: M1.

Setiap ``StatusBerubah`` menjadi kabar untuk pelapor + pendukung laporan itu (``laporan.pendukung``),
kecuali yang mematikan notifikasi dan pelaku perubahan itu sendiri. Pola diport dari jalanku-v0
``reports.py`` ``_notifikasi`` (karya Yosua). Kejadian ``StatusBerubah`` tidak membawa id pengguna
pelaku, jadi pengecualian pelaku dilakukan per peran: bila pelakunya pelapor (mis. mengajukan banding),
pelapor tidak dikabari tindakannya sendiri. Petugas/Admin bukan penerima kecuali kebetulan mendukung.
"""

from __future__ import annotations

from dataclasses import dataclass

from jalanku.core import koneksi, langganan, sekarang, transaksi
from jalanku.modules.akun import AkunDihapus
from jalanku.modules.laporan import (
    PELAKU_PELAPOR,
    STATUS_BELUM,
    STATUS_DIGABUNG,
    STATUS_DITOLAK,
    STATUS_MENUNGGU,
    STATUS_SEDANG,
    STATUS_SELESAI,
    StatusBerubah,
    pendukung,
)

BATAS_DAFTAR = 100

PESAN = {
    STATUS_BELUM: "Laporan {nomor} sudah diverifikasi dan diteruskan ke Sudin Bina Marga.",
    STATUS_SEDANG: "Laporan {nomor} sedang dikerjakan petugas.",
    STATUS_SELESAI: "Kabar baik: jalan di laporan {nomor} sudah diperbaiki. Lihat foto perbaikannya.",
    STATUS_DITOLAK: "Laporan {nomor} ditolak. Lihat alasannya di halaman laporan.",
    STATUS_DIGABUNG: "Laporan {nomor} digabung ke laporan lain tentang kerusakan yang sama.",
    STATUS_MENUNGGU: "Laporan {nomor} sedang ditinjau ulang oleh Admin JalanKu.",
}


@dataclass(frozen=True)
class Kabar:
    id: int
    nomor: str
    pesan: str
    dibaca: bool
    waktu: str


def _ke_kabar(b) -> Kabar:
    return Kabar(b["id"], b["nomor"], b["pesan"], bool(b["dibaca"]), b["waktu"])


# --- Pengaturan -----------------------------------------------------------------------------------


def aktif(pengguna_id: int) -> bool:
    """Notifikasi menyala kecuali pengguna mematikannya (bawaan: menyala)."""
    kon = koneksi()
    try:
        b = kon.execute("SELECT aktif FROM notifikasi_pengaturan WHERE pengguna_id = ?", (pengguna_id,)).fetchone()
    finally:
        kon.close()
    return True if b is None else bool(b["aktif"])


def atur_aktif(pengguna_id: int, nyala: bool) -> bool:
    with transaksi() as kon:
        kon.execute(
            "INSERT INTO notifikasi_pengaturan (pengguna_id, aktif) VALUES (?, ?)"
            " ON CONFLICT (pengguna_id) DO UPDATE SET aktif = excluded.aktif",
            (pengguna_id, int(nyala)),
        )
    return nyala


# --- Kabar ----------------------------------------------------------------------------------------


def daftar_kabar(pengguna_id: int) -> list[Kabar]:
    """Kabar milik pengguna ini saja, terbaru dulu (maks. ``BATAS_DAFTAR``)."""
    kon = koneksi()
    try:
        rows = kon.execute(
            "SELECT * FROM notifikasi_kabar WHERE pengguna_id = ? ORDER BY id DESC LIMIT ?",
            (pengguna_id, BATAS_DAFTAR),
        ).fetchall()
    finally:
        kon.close()
    return [_ke_kabar(b) for b in rows]


def tandai_dibaca(pengguna_id: int, kabar_id: int) -> Kabar | None:
    """``None`` bila kabar tidak ada atau milik orang lain (rute menjawab 404, tidak membocorkan keberadaan)."""
    with transaksi() as kon:
        kon.execute("UPDATE notifikasi_kabar SET dibaca = 1 WHERE id = ? AND pengguna_id = ?", (kabar_id, pengguna_id))
        b = kon.execute(
            "SELECT * FROM notifikasi_kabar WHERE id = ? AND pengguna_id = ?", (kabar_id, pengguna_id)
        ).fetchone()
    return _ke_kabar(b) if b else None


# --- Pelanggan kejadian ---------------------------------------------------------------------------


def _saat_status_berubah(kejadian: StatusBerubah) -> None:
    penerima = set(pendukung(kejadian.laporan_id))
    if kejadian.pelapor_id is not None:
        penerima.add(kejadian.pelapor_id)
    if kejadian.pelaku == PELAKU_PELAPOR:
        penerima.discard(kejadian.pelapor_id)
    penerima = {pid for pid in penerima if aktif(pid)}
    if not penerima:
        return
    pesan = PESAN.get(kejadian.ke_status, "Status laporan {nomor} berubah.").format(nomor=kejadian.nomor)
    waktu = sekarang()
    with transaksi() as kon:
        kon.executemany(
            "INSERT INTO notifikasi_kabar (pengguna_id, nomor, pesan, waktu) VALUES (?, ?, ?, ?)",
            [(pid, kejadian.nomor, pesan, waktu) for pid in sorted(penerima)],
        )


def _saat_akun_dihapus(kejadian: AkunDihapus) -> None:
    with transaksi() as kon:
        kon.execute("DELETE FROM notifikasi_kabar WHERE pengguna_id = ?", (kejadian.pengguna_id,))
        kon.execute("DELETE FROM notifikasi_pengaturan WHERE pengguna_id = ?", (kejadian.pengguna_id,))


def pasang() -> None:
    """Daftarkan pelanggan kejadian. Dipanggil sekali oleh main.py."""
    langganan(StatusBerubah, _saat_status_berubah)
    langganan(AkunDihapus, _saat_akun_dihapus)
