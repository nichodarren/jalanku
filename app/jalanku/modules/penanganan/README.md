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

Semua endpoint 501 dengan skema lengkap; otorisasi peran petugas sudah bekerja. Cari `TODO(` di folder ini.

## Pekerjaan

- [ ] US-18: laporan publik aktif di kota instansinya (`wilayah.boleh_menangani`), peta + daftar
- [ ] US-19: cek wilayah → 403 bila bukan wilayahnya; Selesai tanpa foto → 400 bila `pengaturan().wajib_foto_selesai`
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
