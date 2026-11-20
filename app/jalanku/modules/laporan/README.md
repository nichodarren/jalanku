# Modul `laporan` (LAP)

| | |
|---|---|
| **Pemilik** | M1 (lihat CODEOWNERS) |
| **Tanggung jawab** | Domain inti: laporan, nomor JK-xxxxx, siklus status BR-03, timeline, foto aman, dukungan, visibilitas BR-06, detail publik. |
| **Requirement** | FR-LAP-01..05, BR-03, BR-06, NFR-PRI-01/02, NFR-SEC-02 |
| **Story** | TS-02 (8), US-17 (5) |
| **Boleh bergantung pada** | core, akun |
| **Tabel milik modul** | laporan, laporan_foto, laporan_timeline, laporan_dukungan |
| **Kejadian** | Menerbitkan `LaporanDibuat`, `StatusBerubah`. Mendengarkan `AkunDihapus`. |
| **Frontend** | `app/jalanku/web/modules/laporan/` |

## Antarmuka publik

Hanya nama di `__all__` pada [`__init__.py`](__init__.py). Tanda tangan terkunci di `app/kontrak/modul.json`; endpoint di `app/kontrak/openapi.json` (lihat juga `/api/docs` saat server jalan). Mengubah yang sudah ada = change request (issue template *Change request*); menambah sesuatu yang opsional cukup PR biasa + `python -m jalanku kontrak --tulis`.

## Status stub (baseline 19 Nov 2026)

Sudah bekerja di DB: buat, ambil, cari, transisi BR-03 per pelaku, timeline, dukungan, detail publik, berkas foto. Foto dibersihkan sebelum disimpan (`_foto.py`). Syarat transisi BR-03 lengkap (`_cek_syarat`; data kurang → 400, keadaan tidak memungkinkan → 409). Belum: visibilitas petugas. Cari `TODO(` di folder ini.

## Pekerjaan

- [x] TS-02: foto aman di `_foto.py` → validasi isi (Pillow), buang EXIF, encode ulang JPEG ≤ 1 MB (NFR-PRI-02, NFR-SEC-02)
- [x] TS-02: syarat transisi di domain (`_cek_syarat`: tingkat wajib, alasan ≥ 5 karakter, induk aktif, banding sekali & hanya untuk penolakan AI, foto sesudah wajib) + keterangan ≤ 280 karakter ditolak bila lebih
- [ ] TS-02: visibilitas untuk petugas; test lengkap BR-06
- [ ] US-17: halaman detail `web/modules/laporan/` (foto sebelum/sesudah, timeline berlabel pelaku, penanda SIMULASI)

- [ ] **US-32 jejak audit (Should, nilai kompetisi tinggi):** isi `TODO(US-32)` di `_catat` (kolom `hash` sudah ada di migrasi) dan endpoint `GET /api/laporan/{nomor}/jejak` (masih 501)

## Cara kerja di modul ini

```bash
cd app
python -m pytest jalanku/modules/laporan     # test modul ini saja
python -m pytest tests/arsitektur        # batas modul & kontrak
python -m jalanku contoh-data            # data SIMULASI di DB lokal
python -m jalanku jalan --reload         # http://localhost:8000, dokumentasi API di /api/docs
```

Aturan: jangan mengimpor isi dalam modul lain (`from jalanku.modules.X.layanan import ...` ❌), jangan query tabel modul lain, dan file migrasi yang sudah di-merge tidak boleh diedit.
