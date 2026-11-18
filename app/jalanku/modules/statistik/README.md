# Modul `statistik` (STAT)

| | |
|---|---|
| **Pemilik** | M5 (lihat CODEOWNERS) |
| **Tanggung jawab** | Statistik per Sudin (median hanya bila n ≥ 5, berlabel simulasi), metrik hipotesis A3 tanpa data pribadi. |
| **Requirement** | FR-STAT-01..02, BR-04 |
| **Story** | US-23 (5), US-24 (3) |
| **Boleh bergantung pada** | core, akun, laporan, wilayah |
| **Tabel milik modul** | statistik_kejadian |
| **Kejadian** | (rencana) mendengarkan `LaporanDibuat`. |
| **Frontend** | `app/jalanku/web/modules/statistik/` |

## Antarmuka publik

Hanya nama di `__all__` pada [`__init__.py`](__init__.py). Tanda tangan terkunci di `app/kontrak/modul.json`; endpoint di `app/kontrak/openapi.json` (lihat juga `/api/docs` saat server jalan). Mengubah yang sudah ada = change request (issue template *Change request*); menambah sesuatu yang opsional cukup PR biasa + `python -m jalanku kontrak --tulis`.

## Status stub (baseline 19 Nov 2026)

Semua endpoint 501 dengan skema lengkap. Cari `TODO(` di folder ini.

## Pekerjaan

- [ ] US-23: median jam terverifikasi → sedang dikerjakan / → selesai per instansi; null bila n < 5
- [ ] US-24: `POST /api/statistik/kejadian` (buka_status) + dua metrik A3

## Cara kerja di modul ini

```bash
cd app
python -m pytest jalanku/modules/statistik     # test modul ini saja
python -m pytest tests/arsitektur        # batas modul & kontrak
python -m jalanku contoh-data            # data SIMULASI di DB lokal
python -m jalanku jalan --reload         # http://localhost:8000, dokumentasi API di /api/docs
```

Aturan: jangan mengimpor isi dalam modul lain (`from jalanku.modules.X.layanan import ...` ❌), jangan query tabel modul lain, dan file migrasi yang sudah di-merge tidak boleh diedit.
