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

## Status

US-25 selesai (21 Nov 2026):

- **Kabar:** setiap `StatusBerubah` → kabar untuk pelapor + `laporan.pendukung()` yang notifikasinya aktif (bawaan aktif). Pelapor tidak dikabari tindakannya sendiri (banding); kejadian tidak membawa id pelaku, jadi pengecualian dilakukan per peran.
- **Endpoint (wajib masuk, hanya data sendiri):** `GET /api/notifikasi` (terbaru dulu, maks. 100), `POST /api/notifikasi/{id}/dibaca` (404 untuk kabar orang lain), `GET`/`PUT /api/notifikasi/pengaturan`.
- **Privasi:** `AkunDihapus` → kabar & pengaturan pengguna itu dihapus.
- **Frontend:** `#/kabar` (daftar, penanda belum dibaca, klik = buka detail + tandai dibaca, sakelar notifikasi).

## Pekerjaan

- [x] US-25: buat kabar untuk pelapor + `laporan.pendukung()` yang pengaturannya aktif; endpoint daftar, dibaca, pengaturan

## Cara kerja di modul ini

```bash
cd app
python -m pytest jalanku/modules/notifikasi     # test modul ini saja
python -m pytest tests/arsitektur        # batas modul & kontrak
python -m jalanku contoh-data            # data SIMULASI di DB lokal
python -m jalanku jalan --reload         # http://localhost:8000, dokumentasi API di /api/docs
```

Aturan: jangan mengimpor isi dalam modul lain (`from jalanku.modules.X.layanan import ...` ❌), jangan query tabel modul lain, dan file migrasi yang sudah di-merge tidak boleh diedit.
