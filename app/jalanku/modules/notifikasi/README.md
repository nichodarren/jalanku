# Modul `notifikasi` (NTF)

| | |
|---|---|
| **Pemilik** | M1 (lihat CODEOWNERS) |
| **Tanggung jawab** | Kabar in-app untuk pelapor & pendukung saat status berubah. |
| **Requirement** | FR-NTF-01 |
| **Story** | US-25 (3) |
| **Boleh bergantung pada** | core, akun, laporan |
| **Tabel milik modul** | notifikasi_kabar, notifikasi_pengaturan |
| **Kejadian** | Mendengarkan `StatusBerubah`. |
| **Frontend** | `app/jalanku/web/modules/notifikasi/` |

## Antarmuka publik

Hanya nama di `__all__` pada [`__init__.py`](__init__.py). Tanda tangan terkunci di `app/kontrak/modul.json`; endpoint di `app/kontrak/openapi.json` (lihat juga `/api/docs` saat server jalan). Mengubah yang sudah ada = change request (issue template *Change request*); menambah sesuatu yang opsional cukup PR biasa + `python -m jalanku kontrak --tulis`.

## Status stub (baseline 19 Nov 2026)

Pelanggan kejadian terpasang tetapi belum menyimpan apa pun; endpoint 501. Cari `TODO(` di folder ini.

## Pekerjaan

- [ ] US-25: buat kabar untuk pelapor + `laporan.pendukung()` yang pengaturannya aktif; endpoint daftar, dibaca, pengaturan

## Cara kerja di modul ini

```bash
cd app
python -m pytest jalanku/modules/notifikasi     # test modul ini saja
python -m pytest tests/arsitektur        # batas modul & kontrak
python -m jalanku contoh-data            # data SIMULASI di DB lokal
python -m jalanku jalan --reload         # http://localhost:8000, dokumentasi API di /api/docs
```

Aturan: jangan mengimpor isi dalam modul lain (`from jalanku.modules.X.layanan import ...` ❌), jangan query tabel modul lain, dan file migrasi yang sudah di-merge tidak boleh diedit.
