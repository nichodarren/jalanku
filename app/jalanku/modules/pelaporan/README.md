# Modul `pelaporan` (PEL)

| | |
|---|---|
| **Pemilik** | M3 (lihat CODEOWNERS) |
| **Tanggung jawab** | Alur warga: kirim laporan (orkestrasi wilayah → duplikat → ai → laporan), pratinjau lokasi, dukung, laporan saya. |
| **Requirement** | FR-PEL-01..07, BR-02, NFR-USA-01, NFR-PERF-03, NFR-SAF-01 |
| **Story** | US-03 (8), US-04 (5), US-09 (3), US-10 (2), US-11 (3), SPIKE-01 (2) |
| **Boleh bergantung pada** | core, akun, laporan, wilayah, ai |
| **Tabel milik modul** | — (dukungan disimpan modul laporan) |
| **Kejadian** | — |
| **Frontend** | `app/jalanku/web/modules/pelaporan/` |

## Antarmuka publik

Hanya nama di `__all__` pada [`__init__.py`](__init__.py). Tanda tangan terkunci di `app/kontrak/modul.json`; endpoint di `app/kontrak/openapi.json` (lihat juga `/api/docs` saat server jalan). Mengubah yang sudah ada = change request (issue template *Change request*); menambah sesuatu yang opsional cukup PR biasa + `python -m jalanku kontrak --tulis`.

## Status stub (baseline 19 Nov 2026)

Semua endpoint 501 dengan skema lengkap. Cari `TODO(` di folder ini.

## Pekerjaan

- [x] US-03: `POST /api/laporan` (1–3 foto, maks 10 MB, rate limit 10/jam, 409 bila ada duplikat dan `abaikan_duplikat=false`)
- [ ] US-04: frontend membaca GPS EXIF di perangkat (port `exif.js` dari jalanku-v0), GPS perangkat, pin manual; kompres ≤ 1 MB
- [ ] US-09/US-10: `POST /api/lokasi` (wilayah + duplikat 25 m), `POST /api/laporan/{nomor}/dukung`
- [ ] US-11: `GET /api/saya/laporan`
- [ ] NFR-SAF-01: peringatan keselamatan sebelum laporan pertama

## Cara kerja di modul ini

```bash
cd app
python -m pytest jalanku/modules/pelaporan     # test modul ini saja
python -m pytest tests/arsitektur        # batas modul & kontrak
python -m jalanku contoh-data            # data SIMULASI di DB lokal
python -m jalanku jalan --reload         # http://localhost:8000, dokumentasi API di /api/docs
```

Aturan: jangan mengimpor isi dalam modul lain (`from jalanku.modules.X.layanan import ...` ❌), jangan query tabel modul lain, dan file migrasi yang sudah di-merge tidak boleh diedit.
