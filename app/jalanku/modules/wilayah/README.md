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

## Menyiapkan data wilayah lokal (TS-04)

Dari `app/`, setelah memasang dependency, siapkan data satu kali per checkout atau runner CI:

```bash
python -m jalanku.modules.wilayah.data.setup_wilayah
```

Perintah ini membutuhkan internet, mengunduh arsip GADM pada revisi tetap, memeriksa SHA-256,
lalu menjalankan konverter TS-04 untuk 42 kecamatan di lima kota. Hasilnya ada di
`app/var/wilayah-dki-jakarta.geojson`. Jika memakai `JALANKU_DATA`, tetapkan folder yang sama
saat setup, menjalankan aplikasi, dan menguji. Aplikasi dapat memakai hasil setup secara offline.
Ulangi perintah jika berkas hilang atau rusak. Simpan data hanya untuk penggunaan lokal
atau pengujian akademik di runner. Jangan commit GeoJSON atau mengunggahnya sebagai artifact CI.

Jika arsip sudah tersedia, konverter juga bisa dijalankan secara manual dari `Indonesia_subdistricts.geojson` dari [arsip sumber pada revisi yang diuji](https://github.com/fahadh4ilyas/indonesia-geojson-archive/blob/5925720d5cb627680d9245c5953e13a401077e01/Indonesia_subdistricts.geojson).
Batas wilayah bersumber dari GADM. [Lisensi GADM](https://gadm.org/license.html) mengizinkan penggunaan akademik dan mensyaratkan izin untuk redistribusi.
Simpan arsip sumber di luar repo. Jika memakai `JALANKU_DATA`, sesuaikan juga path tujuan pada contoh berikut.

Dari folder `app/`, jalankan perintah berikut setelah menyesuaikan path sumber:

```bash
python -m jalanku.modules.wilayah.data.siapkan_wilayah ../../Indonesia_subdistricts.geojson var/wilayah-dki-jakarta.geojson
python -m pytest jalanku/modules/wilayah/tests/test_data_wilayah.py
```

Script diport dari karya Yosua, `jalanku-v0@65db419:app/scripts/siapkan_wilayah.py`. Script menyaring lima kota daratan,
menormalkan ejaan, dan menggabungkan poligon per kecamatan. Hasil lokal berupa GeoJSON dengan 42 fitur dan properti
`kota` serta `kecamatan`. Data Sudin tersedia dari migrasi `migrasi/001_awal.sql` melalui `daftar_instansi()`.

## Penentuan Sudin (US-07)

Panggil `tentukan_wilayah(lat, lon)` lewat antarmuka publik. Titik di dalam poligon menghasilkan kecamatan, kota,
dan Sudin kota itu. Titik luar menghasilkan `HasilWilayah(False, None, None, None)`. Jika dua kecamatan mencakup
titik persis di batas bersama, urutan alfabetis pasangan kota/kecamatan menentukan hasilnya.
Indeks spasial digunakan kembali selama path dan waktu modifikasi file sama.

`GET /api/wilayah` menyajikan GeoJSON tersebut, termasuk atribusinya. Untuk server publik, gunakan data yang
berizin untuk didistribusikan. Simpan data GADM untuk pengujian lokal sesuai [ketentuan GADM](https://gadm.org/license.html).
Data hilang atau rusak menghasilkan galat 503. Perubahan kanal instansi dijadwalkan pada US-26.

## Pekerjaan

- [x] TS-04: siapkan batas 42 kecamatan dan verifikasi pemetaan lima kota ke Sudin.
- [x] US-07: tentukan kecamatan dan Sudin dengan Shapely STRtree dan sajikan batas di endpoint wilayah.
- [ ] US-08: uji alur luar cakupan bersama M3 untuk menyelesaikan [issue #15](https://github.com/nichodarren/jalanku/issues/15).
  - [x] M2: untuk titik Kota Tangerang, `tentukan_wilayah` mengembalikan `di_dalam=False` tanpa Sudin.
    Modul pelaporan dapat mengambil pasangan nama dan URL SP4N-LAPOR! dari `wilayah.KANAL_LUAR_WILAYAH`.
  - [ ] M3 bersama M2: pastikan warga melihat alasan dan tautan kanal di form, serta server menolak pengiriman tanpa membuat laporan.
- [x] NFR-FUN-01: test 3 titik per kota + 5 titik luar cakupan di `tests/test_wilayah.py`.
  Dari `app/`, jalankan `python -m pytest jalanku/modules/wilayah/tests/test_wilayah.py -k titik_nyata -v`.
  Semua 20 kasus wajib berjalan. Jika setup belum dilakukan, pytest gagal dengan petunjuk setup.
- [ ] US-26: PATCH kanal instansi (URL wajib http/https), halaman `web/modules/wilayah/`

## Cara kerja di modul ini

```bash
cd app
python -m pytest jalanku/modules/wilayah     # test modul ini saja
python -m pytest tests/arsitektur        # batas modul & kontrak
python -m jalanku contoh-data            # data SIMULASI di DB lokal
python -m jalanku jalan --reload         # http://localhost:8000, dokumentasi API di /api/docs
```

Aturan: jangan mengimpor isi dalam modul lain (`from jalanku.modules.X.layanan import ...` ❌), jangan query tabel modul lain, dan file migrasi yang sudah di-merge tidak boleh diedit.
