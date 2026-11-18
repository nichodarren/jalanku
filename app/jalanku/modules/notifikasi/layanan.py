"""Notifikasi in-app (FR-NTF-01). Pemilik: M1.

STUB: pelanggan kejadian sudah terpasang tetapi belum menyimpan apa pun.
TODO(US-25): untuk setiap StatusBerubah ke status publik, buat kabar untuk pelapor + pendukung
(``laporan.pendukung``) yang pengaturannya aktif; jangan buat kabar untuk pelaku perubahan itu sendiri.
"""

from __future__ import annotations

from jalanku.core import langganan
from jalanku.modules.laporan import StatusBerubah


def _saat_status_berubah(kejadian: StatusBerubah) -> None:
    return None  # TODO(US-25)


def pasang() -> None:
    """Daftarkan pelanggan kejadian. Dipanggil sekali oleh main.py."""
    langganan(StatusBerubah, _saat_status_berubah)
