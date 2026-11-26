# Modul `peta` (PETA)

| | |
|---|---|
| **Pemilik** | M6 (lihat CODEOWNERS) |
| **Tanggung jawab** | Data & tampilan bubble peta aktif dan peta riwayat. |
| **Requirement** | FR-PETA-01..02, NFR-PERF-02, NFR-LEG-01, NFR-USA-02 |
| **Story** | US-15 (8), US-16 (3) |
| **Boleh bergantung pada** | core, akun, laporan, wilayah |
| **Tabel milik modul** | — |
| **Kejadian** | — |
| **Frontend** | `app/jalanku/web/modules/peta/` |

## Antarmuka publik

Hanya nama di `__all__` pada [`__init__.py`](__init__.py). Tanda tangan terkunci di `app/kontrak/modul.json`; endpoint di `app/kontrak/openapi.json` (lihat juga `/api/docs` saat server jalan). Mengubah yang sudah ada = change request (issue template *Change request*); menambah sesuatu yang opsional cukup PR biasa + `python -m jalanku kontrak --tulis`.

## Status stub (baseline 19 Nov 2026)

`GET /api/peta` sudah bekerja (mode aktif & riwayat, filter kota/tingkat multi-nilai dipisah koma, tanpa identitas pelapor). Frontend `#/peta` dan `#/riwayat` menampilkan bubble berkelompok (Leaflet.markercluster), filter, legenda, dan penanda SIMULASI.

## Pekerjaan

- [x] US-15: endpoint data bubble `GET /api/peta` (tanpa pelapor_id); test di `tests/test_peta_api.py`
- [x] US-15: frontend markercluster, warna per tingkat, ukuran ikut zoom, animasi pop yang menghormati prefers-reduced-motion (`web/modules/peta/`, penjaga statis di `tests/test_peta_web.py`)
- [x] US-16 (backend): `mode=riwayat` mengembalikan status Selesai
- [x] US-16 (frontend): rute `#/riwayat`, warna hijau
- [ ] Pakai `python -m jalanku contoh-data` (data SIMULASI) selama modul pelaporan belum selesai

## Cara kerja di modul ini

```bash
cd app
python -m pytest jalanku/modules/peta     # test modul ini saja
python -m pytest tests/arsitektur        # batas modul & kontrak
python -m jalanku contoh-data            # data SIMULASI di DB lokal
python -m jalanku jalan --reload         # http://localhost:8000, dokumentasi API di /api/docs
```

Aturan: jangan mengimpor isi dalam modul lain (`from jalanku.modules.X.layanan import ...` ❌), jangan query tabel modul lain, dan file migrasi yang sudah di-merge tidak boleh diedit.
