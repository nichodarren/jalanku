"""Bus kejadian (event) sinkron dalam satu proses.

Dipakai supaya modul "bawah" bisa memberi tahu modul "atas" tanpa mengimpornya
(Dependency Inversion). Kejadian = dataclass berisi fakta yang sudah terjadi.
Galat di pelanggan dicatat ke log dan TIDAK menggagalkan penerbit (OWASP A10).
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

log = logging.getLogger("jalanku.kejadian")

_pelanggan: dict[type, list[Callable[[Any], None]]] = defaultdict(list)


def langganan(tipe: type, fungsi: Callable[[Any], None]) -> None:
    """Daftarkan ``fungsi`` untuk dipanggil setiap kali kejadian bertipe ``tipe`` diterbitkan."""
    if fungsi not in _pelanggan[tipe]:
        _pelanggan[tipe].append(fungsi)


def terbitkan(kejadian: object) -> None:
    for fungsi in list(_pelanggan[type(kejadian)]):
        try:
            fungsi(kejadian)
        except Exception:
            log.exception("Pelanggan %s gagal memproses %s", getattr(fungsi, "__qualname__", fungsi), kejadian)


def hapus_semua_langganan() -> None:
    """Test: kosongkan semua pelanggan."""
    _pelanggan.clear()
