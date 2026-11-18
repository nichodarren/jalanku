# Modul `ai` (AI)

| | |
|---|---|
| **Pemilik** | M4 (lihat CODEOWNERS) |
| **Tanggung jawab** | Memeriksa foto (kelas, confidence, kemiripan), keputusan BR-07, info & metrik model, ekspor data latih. |
| **Requirement** | FR-AI-01..03, BR-07, NFR-FUN-02/03, NFR-PERF-01, NFR-REL-02, NFR-ETH-01 |
| **Story** | US-05 (5), US-06 (8), US-22 (5), SPIKE-02 (3) |
| **Boleh bergantung pada** | core, akun, laporan (untuk metrik & ekspor) |
| **Tabel milik modul** | — (membaca laporan lewat antarmuka publik) |
| **Kejadian** | — |
| **Frontend** | `app/jalanku/web/modules/ai/ (halaman Kinerja AI untuk Admin)` |

## Antarmuka publik

Hanya nama di `__all__` pada [`__init__.py`](__init__.py). Tanda tangan terkunci di `app/kontrak/modul.json`; endpoint di `app/kontrak/openapi.json` (lihat juga `/api/docs` saat server jalan). Mengubah yang sudah ada = change request (issue template *Change request*); menambah sesuatu yang opsional cukup PR biasa + `python -m jalanku kontrak --tulis`.

## Status stub (baseline 19 Nov 2026)

Model tidak aktif: setiap foto → admin, setiap laporan → `tidak_aktif`. `POST /api/ai/periksa` sudah memakai stub ini. 501: metrik, ekspor. Cari `TODO(` di folder ini.

## Pekerjaan

- [ ] US-05: port model (`backbone_efficientnet_b0.onnx`, `kepala.json`, `referensi_fitur.npy`, `metrik.json`) dan kode inferensi dari jalanku-v0 branch `trial/mvp-v2` ke `modules/ai/model/` + `_model.py`; model dimuat sekali saat start
- [ ] US-06: isi `putuskan` sesuai BR-07 (fungsi murni → mulai dari test, TDD)
- [ ] US-05: CLI `python -m jalanku uji-ai FOLDER --csv` (termasuk waktu per foto untuk NFR-PERF-01)
- [ ] SPIKE-02: ≥ 100 foto Jakarta asli → simpan hasil nyata (CSV `uji-ai`) untuk laporan testing
- [ ] US-22: metrik & ekspor; notebook ML pindah ke `app/ml/` (milik M4)

## Cara kerja di modul ini

```bash
cd app
python -m pytest jalanku/modules/ai     # test modul ini saja
python -m pytest tests/arsitektur        # batas modul & kontrak
python -m jalanku contoh-data            # data SIMULASI di DB lokal
python -m jalanku jalan --reload         # http://localhost:8000, dokumentasi API di /api/docs
```

Aturan: jangan mengimpor isi dalam modul lain (`from jalanku.modules.X.layanan import ...` ❌), jangan query tabel modul lain, dan file migrasi yang sudah di-merge tidak boleh diedit.
