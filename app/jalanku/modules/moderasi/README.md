# Modul `moderasi` (MOD)

| | |
|---|---|
| **Pemilik** | M5 (lihat CODEOWNERS) |
| **Tanggung jawab** | Antrean Admin (banding di atas), verifikasi / tolak / gabung, banding pelapor, koreksi tingkat, paket penerusan. |
| **Requirement** | FR-MOD-01..04, NFR-ETH-01, NFR-PRI-01 |
| **Story** | US-12 (8), US-13 (3), US-14 (3), US-21 (2) |
| **Boleh bergantung pada** | core, akun, laporan, wilayah |
| **Tabel milik modul** | moderasi_koreksi |
| **Kejadian** | — |
| **Frontend** | `app/jalanku/web/modules/moderasi/` |

## Antarmuka publik

Hanya nama di `__all__` pada [`__init__.py`](__init__.py). Tanda tangan terkunci di `app/kontrak/modul.json`; endpoint di `app/kontrak/openapi.json` (lihat juga `/api/docs` saat server jalan). Mengubah yang sudah ada = change request (issue template *Change request*); menambah sesuatu yang opsional cukup PR biasa + `python -m jalanku kontrak --tulis`.

## Status stub (baseline 19 Nov 2026)

Sudah aktif: antrean, verifikasi, tolak, gabung (US-12), banding (US-13), paket penerusan (US-14), koreksi tingkat (US-21). Halaman `#/admin` memakai semuanya.

## Pekerjaan

- [x] US-12: antrean = `laporan.cari_laporan(status=STATUS_MENUNGGU)` urut banding dulu; aksi lewat `laporan.ubah_status(..., pelaku=PELAKU_ADMIN, label_akhir=...)`
- [x] US-13: banding hanya bila `diperiksa_oleh == 'ai'` dan `banding_pada is None`
- [x] US-14: paket penerusan tanpa identitas (test eksplisit: email & nama pelapor tidak muncul)
- [x] US-21: koreksi → `laporan.ubah_tingkat` + baris `moderasi_koreksi`

## Cara kerja di modul ini

```bash
cd app
python -m pytest jalanku/modules/moderasi     # test modul ini saja
python -m pytest tests/arsitektur        # batas modul & kontrak
python -m jalanku contoh-data            # data SIMULASI di DB lokal
python -m jalanku jalan --reload         # http://localhost:8000, dokumentasi API di /api/docs
```

Aturan: jangan mengimpor isi dalam modul lain (`from jalanku.modules.X.layanan import ...` ❌), jangan query tabel modul lain, dan file migrasi yang sudah di-merge tidak boleh diedit.
