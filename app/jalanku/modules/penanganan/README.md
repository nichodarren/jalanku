# Modul `penanganan` (TGN)

| | |
|---|---|
| **Pemilik** | M6 (lihat CODEOWNERS) |
| **Tanggung jawab** | Dashboard petugas per wilayah instansi, ubah status ke Sedang Dikerjakan / Selesai (foto wajib), urutan prioritas. |
| **Requirement** | FR-TGN-01..03, BR-05, BR-08, NFR-SEC-01 |
| **Story** | US-18 (5), US-19 (5), US-20 (3) |
| **Boleh bergantung pada** | core, akun, laporan, wilayah, ai |
| **Tabel milik modul** | — |
| **Kejadian** | — |
| **Frontend** | `app/jalanku/web/modules/penanganan/` |

## Antarmuka publik

Hanya nama di `__all__` pada [`__init__.py`](__init__.py). Tanda tangan terkunci di `app/kontrak/modul.json`; endpoint di `app/kontrak/openapi.json` (lihat juga `/api/docs` saat server jalan). Mengubah yang sudah ada = change request (issue template *Change request*); menambah sesuatu yang opsional cukup PR biasa + `python -m jalanku kontrak --tulis`.

## Status stub (baseline 19 Nov 2026)

`GET /api/petugas/laporan` dan `POST /api/petugas/laporan/{nomor}/status` sudah bekerja (wilayah dicek di server, foto wajib saat Selesai). Masih 501: `urut=prioritas` (US-20). `verifikasi_foto` masih `null` (US-31). Frontend `#/petugas` menyusul. Cari `TODO(` di folder ini.

## Pekerjaan

- [x] US-18 (backend): laporan Belum/Sedang/Selesai di kota instansinya (`wilayah.boleh_menangani`, DINAS_BM semua), filter status; test di `tests/test_petugas_api.py`
- [ ] US-18 (frontend): `#/petugas` peta + daftar
- [x] US-19 (backend): cek wilayah → 403 bila bukan wilayahnya (dicek sebelum foto); Selesai tanpa foto → 400 bila `pengaturan().wajib_foto_selesai`; foto maks 10 MB
- [ ] US-19 (frontend): tombol Mulai dikerjakan / Selesai + unggah foto
- [ ] US-20: skor BR-05 sebagai fungsi murni (TDD)

- [ ] **US-31 bukti perbaikan diverifikasi AI (Should, pembeda utama):** saat Selesai, `ai.periksa_foto(foto)` → `laporan.ubah_status(..., hasil_ai_sesudah=hasil.sebagai_dict())`; isi `verifikasi_foto` di respons; foto yang tidak dinilai `baik` → tanda "perlu ditinjau"

## Cara kerja di modul ini

```bash
cd app
python -m pytest jalanku/modules/penanganan     # test modul ini saja
python -m pytest tests/arsitektur        # batas modul & kontrak
python -m jalanku contoh-data            # data SIMULASI di DB lokal
python -m jalanku jalan --reload         # http://localhost:8000, dokumentasi API di /api/docs
```

Aturan: jangan mengimpor isi dalam modul lain (`from jalanku.modules.X.layanan import ...` ❌), jangan query tabel modul lain, dan file migrasi yang sudah di-merge tidak boleh diedit.
