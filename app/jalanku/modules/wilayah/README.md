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

## Penentuan Sudin (US-07)

Sediakan hasil TS-04 di `app/var/wilayah-dki-jakarta.geojson`, atau di folder `JALANKU_DATA` yang dipakai server.
Panggil `tentukan_wilayah(lat, lon)` lewat antarmuka publik. Titik di dalam poligon menghasilkan kecamatan, kota,
dan Sudin kota itu. Titik luar menghasilkan `HasilWilayah(False, None, None, None)`. Jika dua kecamatan mencakup
titik persis di batas bersama, urutan alfabetis pasangan kota/kecamatan menentukan hasilnya.
Indeks spasial digunakan kembali selama path dan waktu modifikasi file sama.

`GET /api/wilayah` menyajikan GeoJSON tersebut, termasuk atribusinya. Untuk server publik, gunakan data yang
berizin untuk didistribusikan. Simpan data GADM untuk pengujian lokal sesuai [ketentuan GADM](https://gadm.org/license.html).
Data hilang atau rusak menghasilkan galat 503. Perubahan kanal instansi dijadwalkan pada US-26.

## Pekerjaan

- [ ] TS-04: port `scripts/siapkan_wilayah.py` + `wilayah-dki-jakarta.geojson` (42 kecamatan, GADM) dari jalanku-v0 branch `trial/mvp-v2` ke `modules/wilayah/data/`; cek syarat lisensi GADM & atribusi
- [x] US-07: tentukan kecamatan dan Sudin dengan Shapely STRtree dan sajikan batas di endpoint wilayah.
- [ ] US-08: di luar → `KANAL_LUAR_WILAYAH` (SP4N-LAPOR!)
- [x] NFR-FUN-01: test 3 titik per kota + 5 titik luar cakupan di `tests/test_wilayah.py`.
  Dari `app/`, jalankan `python -m pytest jalanku/modules/wilayah/tests/test_wilayah.py -k titik_nyata -v`.
  Siapkan GeoJSON TS-04 di `app/var/` untuk menjalankan 20 kasus ini. Pada checkout tanpa data lokal,
  pytest menandainya sebagai dilewati; test SIMULASI tetap berjalan.
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
