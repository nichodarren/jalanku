# Modul `wilayah` (WIL)

| | |
|---|---|
| **Pemilik** | M2 (lihat CODEOWNERS) |
| **Tanggung jawab** | Menentukan kecamatan, kota administrasi, dan Sudin dari koordinat (BR-01); data instansi & kanal resmi. |
| **Requirement** | FR-WIL-01..03, BR-01, NFR-FUN-01 |
| **Story** | TS-04 (3), US-07 (3), US-08 (2), US-26 (3) |
| **Boleh bergantung pada** | core, akun |
| **Tabel milik modul** | wilayah_instansi |
| **Kejadian** | — |
| **Frontend** | `app/jalanku/web/modules/wilayah/` |

## Antarmuka publik

Hanya nama di `__all__` pada [`__init__.py`](__init__.py). Tanda tangan terkunci di `app/kontrak/modul.json`; endpoint di `app/kontrak/openapi.json` (lihat juga `/api/docs` saat server jalan). Mengubah yang sudah ada = change request (issue template *Change request*); menambah sesuatu yang opsional cukup PR biasa + `python -m jalanku kontrak --tulis`.

## Status stub (baseline 19 Nov 2026)

`tentukan_wilayah` memakai KOTAK KASAR: semua titik di Jakarta = Gambir / Jakarta Pusat / SUDIN_JP. Data 6 instansi asli sudah ada (migrasi). 501: ubah kanal. Cari `TODO(` di folder ini.

## Pekerjaan

- [x] TS-04: siapkan batas 42 kecamatan dan verifikasi pemetaan lima kota ke Sudin (lihat langkah lokal di bawah).
- [ ] US-07: shapely STRtree point-in-polygon; ganti isi `tentukan_wilayah` dan `batas_wilayah_geojson`
- [ ] US-08: di luar → `KANAL_LUAR_WILAYAH` (SP4N-LAPOR!)
- [ ] NFR-FUN-01: test titik nyata ≥ 3 per kota + 5 titik luar Jakarta (ganti `tests/test_wilayah_stub.py`)
- [ ] US-26: PATCH kanal instansi (URL wajib http/https), halaman `web/modules/wilayah/`

## Menyiapkan data wilayah lokal (TS-04)

Gunakan `Indonesia_subdistricts.geojson` dari [arsip sumber pada revisi yang diuji](https://github.com/fahadh4ilyas/indonesia-geojson-archive/blob/5925720d5cb627680d9245c5953e13a401077e01/Indonesia_subdistricts.geojson).
Batas wilayah bersumber dari GADM. [Lisensi GADM](https://gadm.org/license.html) mengizinkan penggunaan akademik dan mensyaratkan izin untuk redistribusi.
Simpan sumber di luar repo dan hasil di folder lokal `app/var/` yang diabaikan Git.

Dari folder `app/`, jalankan perintah berikut setelah menyesuaikan path sumber:

```bash
python -m jalanku.modules.wilayah.data.siapkan_wilayah ../../Indonesia_subdistricts.geojson var/wilayah-dki-jakarta.geojson
python -m pytest jalanku/modules/wilayah/tests/test_data_wilayah.py
```

Script diport dari karya Yosua, `jalanku-v0@65db419:app/scripts/siapkan_wilayah.py`. Script menyaring lima kota daratan,
menormalkan ejaan, dan menggabungkan poligon per kecamatan. Hasil lokal berupa GeoJSON dengan 42 fitur dan properti
`kota` serta `kecamatan`. Data Sudin tersedia dari migrasi `migrasi/001_awal.sql` melalui `daftar_instansi()`.
Integrasi batas ini dengan pencarian koordinat dan endpoint peta dijadwalkan dalam US-07.

## Cara kerja di modul ini

```bash
cd app
python -m pytest jalanku/modules/wilayah     # test modul ini saja
python -m pytest tests/arsitektur        # batas modul & kontrak
python -m jalanku contoh-data            # data SIMULASI di DB lokal
python -m jalanku jalan --reload         # http://localhost:8000, dokumentasi API di /api/docs
```

Aturan: jangan mengimpor isi dalam modul lain (`from jalanku.modules.X.layanan import ...` ❌), jangan query tabel modul lain, dan file migrasi yang sudah di-merge tidak boleh diedit.
