# `core`: fondasi bersama

| | |
|---|---|
| **Pemilik** | M1 (tech lead) |
| **Isi** | `config.py` (environment `JALANKU_*`), `db.py` (koneksi, transaksi, migrasi per modul), `kejadian.py` (bus kejadian), `galat.py` (galat → `{"detail": ...}`), `keamanan.py` (header, CSRF, rate limit), `penyimpanan.py` (berkas), `geodesi.py`, `waktu.py` |
| **Boleh bergantung pada** | tidak ada modul (dicek test arsitektur) |

Modul lain memakai `from jalanku.core import ...` (nama di `__all__`). `pasang_keamanan`, `pasang_penangan_galat`, `reset_batas`, `hapus_semua_langganan`, dan `atur_waktu` hanya untuk `main.py` dan test.
