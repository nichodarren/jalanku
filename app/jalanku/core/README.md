# `core`: fondasi bersama

| | |
|---|---|
| **Pemilik** | M1 (tech lead) |
| **Isi** | `config.py` (environment `JALANKU_*`), `db.py` (koneksi, transaksi, migrasi per modul), `kejadian.py` (bus kejadian), `galat.py` (galat → `{"detail": ...}`), `keamanan.py` (header, CSRF, rate limit), `penyimpanan.py` (berkas), `tile.py` (proxy + cache tile peta OSM untuk `GET /api/tile/{z}/{x}/{y}.png`, hanya dipakai `main.py`), `geodesi.py`, `waktu.py` |
| **Boleh bergantung pada** | tidak ada modul (dicek test arsitektur) |

**Tile peta.** Browser tidak meminta tile langsung ke OSM (sering dibalas "Access blocked", issue #22). `web/shared/peta-dasar.js` memakai `/api/tile`; server mengunduh dengan User-Agent JalanKu dan menyimpan cache 7 hari di `<JALANKU_DATA>/tile`. Hanya zoom 10–19 di kotak DKI Jakarta (selain itu 404), balasan wajib PNG ≤ 512 KB, unduhan ke OSM dibatasi 300/menit per klien, dan CSP `img-src` cukup `'self' data: blob:`. Route ini tidak masuk kontrak OpenAPI.

Modul lain memakai `from jalanku.core import ...` (nama di `__all__`). `pasang_keamanan`, `pasang_penangan_galat`, `reset_batas`, `hapus_semua_langganan`, dan `atur_waktu` hanya untuk `main.py` dan test.
