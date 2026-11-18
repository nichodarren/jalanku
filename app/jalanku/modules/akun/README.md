# Modul `akun` (AKN)

| | |
|---|---|
| **Pemilik** | M2 (lihat CODEOWNERS) |
| **Tanggung jawab** | Pengguna, peran, sesi (cookie httpOnly), daftar + verifikasi email + masuk dengan password (argon2id), hapus akun. |
| **Requirement** | FR-AKN-01..04, NFR-SEC-04, NFR-PRI-03 |
| **Story** | US-01 (8), US-02 (3) |
| **Boleh bergantung pada** | core |
| **Tabel milik modul** | akun_pengguna, akun_sesi, akun_token |
| **Kejadian** | Menerbitkan `AkunDihapus`. |
| **Frontend** | `app/jalanku/web/modules/akun/` |

## Antarmuka publik

Hanya nama di `__all__` pada [`__init__.py`](__init__.py). Tanda tangan terkunci di `app/kontrak/modul.json`; endpoint di `app/kontrak/openapi.json` (lihat juga `/api/docs` saat server jalan). Mengubah yang sudah ada = change request (issue template *Change request*); menambah sesuatu yang opsional cukup PR biasa + `python -m jalanku kontrak --tulis`.

## Status stub (baseline 19 Nov 2026)

Sesi & `POST /api/dev/masuk` (dev/test) sudah bekerja. 501: daftar, verifikasi, kirim-ulang, masuk, hapus akun. CLI `peran` belum. Cari `TODO(` di folder ini.

## Pekerjaan

- [ ] US-01: daftar (nama, email, password ≥ 8, setuju_privasi wajib) → token verifikasi (hash) → email (SMTP, atau dicetak ke log di mode dev)
- [ ] US-01: masuk dengan password argon2id; rate limit 10 gagal per IP per 15 menit (NFR-SEC-03)
- [ ] US-01: CLI `python -m jalanku peran EMAIL admin|petugas --instansi ID` (FR-AKN-03)
- [ ] US-02: hapus akun → hapus identitas, akhiri semua sesi, terbitkan `AkunDihapus`
- [ ] Frontend `web/modules/akun/`: form daftar/masuk/verifikasi; masuk cepat hanya muncul bila `/api/dev/masuk` ada

## Cara kerja di modul ini

```bash
cd app
python -m pytest jalanku/modules/akun     # test modul ini saja
python -m pytest tests/arsitektur        # batas modul & kontrak
python -m jalanku contoh-data            # data SIMULASI di DB lokal
python -m jalanku jalan --reload         # http://localhost:8000, dokumentasi API di /api/docs
```

Aturan: jangan mengimpor isi dalam modul lain (`from jalanku.modules.X.layanan import ...` ❌), jangan query tabel modul lain, dan file migrasi yang sudah di-merge tidak boleh diedit.
