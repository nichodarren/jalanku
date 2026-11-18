# Modul `wilayah` (WIL)

| | |
|---|---|
| **Pemilik** | M2 (lihat CODEOWNERS) |
| **Tanggung jawab** | Menentukan kecamatan, kota administrasi, dan Sudin dari koordinat (BR-01); data instansi & kanal resmi. |
| **Requirement** | FR-WIL-01..03, BR-01, NFR-FUN-01 |
| **Story** | TS-04 (3), US-07 (3), US-08 (2), US-26 (3) |
| **Boleh bergantung pada** | core, akun |
| **Tabel milik modul** | wilayah_instansi |
| **Kejadian** | — |
| **Frontend** | `app/jalanku/web/modules/wilayah/` |

## Antarmuka publik

Hanya nama di `__all__` pada [`__init__.py`](__init__.py). Tanda tangan terkunci di `app/kontrak/modul.json`; endpoint di `app/kontrak/openapi.json` (lihat juga `/api/docs` saat server jalan). Mengubah yang sudah ada = change request (issue template *Change request*); menambah sesuatu yang opsional cukup PR biasa + `python -m jalanku kontrak --tulis`.

## Status stub (baseline 19 Nov 2026)

`tentukan_wilayah` memakai KOTAK KASAR: semua titik di Jakarta = Gambir / Jakarta Pusat / SUDIN_JP. Data 6 instansi asli sudah ada (migrasi). 501: ubah kanal. Cari `TODO(` di folder ini.

## Pekerjaan

- [ ] TS-04: port `scripts/siapkan_wilayah.py` + `wilayah-dki-jakarta.geojson` (42 kecamatan, GADM) dari jalanku-v0 branch `trial/mvp-v2` ke `modules/wilayah/data/`; cek syarat lisensi GADM & atribusi
- [ ] US-07: shapely STRtree point-in-polygon; ganti isi `tentukan_wilayah` dan `batas_wilayah_geojson`
- [ ] US-08: di luar → `KANAL_LUAR_WILAYAH` (SP4N-LAPOR!)
- [ ] NFR-FUN-01: test titik nyata ≥ 3 per kota + 5 titik luar Jakarta (ganti `tests/test_wilayah_stub.py`)
- [ ] US-26: PATCH kanal instansi (URL wajib http/https), halaman `web/modules/wilayah/`

## Cara kerja di modul ini

```bash
cd app
python -m pytest jalanku/modules/wilayah     # test modul ini saja
python -m pytest tests/arsitektur        # batas modul & kontrak
python -m jalanku contoh-data            # data SIMULASI di DB lokal
python -m jalanku jalan --reload         # http://localhost:8000, dokumentasi API di /api/docs
```

Aturan: jangan mengimpor isi dalam modul lain (`from jalanku.modules.X.layanan import ...` ❌), jangan query tabel modul lain, dan file migrasi yang sudah di-merge tidak boleh diedit.
