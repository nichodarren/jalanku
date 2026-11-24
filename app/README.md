# Aplikasi JalanKu

Backend FastAPI + SQLite, frontend PWA (HTML + JavaScript modul + Leaflet, tanpa build step), satu proses.
Arsitektur & aturan modul: [`../README.id.md`](../README.id.md#arsitektur).

## Pasang (sekali)

Butuh Python 3.12+ (tim memakai 3.13) dan Git.

```bash
cd app
python -m venv .venv
# Windows: .venv\Scripts\activate      macOS/Linux: source .venv/bin/activate
pip install -r requirements.lock        # versi PERSIS yang sama untuk semua anggota
pip install -e . --no-deps
python -m jalanku.modules.wilayah.data.setup_wilayah   # sekali: batas 42 kecamatan → var/
```

Langkah terakhir mengunduh batas kecamatan (GADM, dikunci SHA-256) ke `app/var/wilayah-dki-jakarta.geojson`. Data ini **tidak ikut repo** karena lisensi GADM melarang redistribusi; tanpa data ini penentuan Sudin, `contoh-data`, dan 20 test titik nyata wilayah tidak jalan. CI menyiapkannya otomatis. Ulangi bila folder `app/var/` dihapus.

## Jalankan

```bash
python -m jalanku contoh-data           # opsional: 30 laporan BERLABEL SIMULASI
python -m jalanku jalan --reload        # http://localhost:8000
```

- Aplikasi: http://localhost:8000 (menu **Akun → Masuk cepat** untuk masuk sebagai pelapor/admin/petugas di mode dev)
- Dokumentasi API interaktif: http://localhost:8000/api/docs
- Port 8000 dipakai? `python -m jalanku jalan --port 8765`
- Data lokal ada di `app/var/` (di-ignore Git). Hapus folder itu untuk mulai dari kosong.

## Test & cek kualitas (sama dengan CI)

```bash
python -m pytest                        # semua test
python -m pytest jalanku/modules/peta   # satu modul
python -m pytest tests/arsitektur       # batas modul + kontrak (wajib hijau)
python -m pytest --cov=jalanku --cov-report=term-missing
ruff check . && ruff format --check .   # lint & format (perbaiki: ruff check --fix . && ruff format .)
python -m jalanku kontrak               # kontrak cocok dengan snapshot?
```

## Struktur

```
app/
├── pyproject.toml        dependency + konfigurasi pytest/ruff
├── requirements.lock     versi persis (dibuat dari pip freeze)
├── conftest.py           fixture bersama: DB sementara per test, klien per peran
├── kontrak/              SNAPSHOT terkunci: openapi.json, modul.json
├── jalanku/
│   ├── main.py           perakit: memasang router semua modul + web
│   ├── __main__.py       CLI (python -m jalanku ...)
│   ├── kontrak.py        pembuat/pengecek snapshot kontrak
│   ├── contoh.py         data contoh berlabel simulasi
│   ├── core/             fondasi bersama (lihat core/README.md)
│   ├── modules/<modul>/  README.md, __init__.py (antarmuka publik), tipe, layanan, rute, skema, migrasi/, tests/
│   └── web/              index.html, app.js (router), shared/, modules/<modul>/, vendor/ (Leaflet, markercluster)
└── tests/
    ├── arsitektur/       batas modul & kontrak
    ├── integrasi/        lintas modul lewat HTTP
    ├── penerimaan/       acceptance criteria story (Given/When/Then)
    └── sistem/           alur browser (Playwright, ditambah QA lead)
```

## Konfigurasi (environment variable)

Lihat [`.env.example`](.env.example). Di produksi wajib: `JALANKU_MODE=prod`, `JALANKU_DATA` di disk persisten, `JALANKU_URL_DASAR` HTTPS, dan SMTP.

## Masalah umum

| Gejala | Penyebab / solusi |
|---|---|
| `test_kontrak_cocok_dengan_snapshot` gagal | Kamu mengubah endpoint/skema/antarmuka publik. Lihat docstring test itu |
| `test_modul_hanya_memakai_antarmuka_publik` gagal | Kamu mengimpor isi dalam modul lain, atau modul yang tidak diizinkan. Pakai `from jalanku.modules.<modul> import ...` |
| `test_titik_nyata` error "…wilayah-dki-jakarta.geojson belum tersedia", atau `contoh-data` berhenti dengan "Data contoh belum dibuat" | Data batas kecamatan belum disiapkan. Dari `app/`: `python -m jalanku.modules.wilayah.data.setup_wilayah` |
| Endpoint menjawab 501 | Fiturnya belum dibuat (stub). Pesan menyebut story & pemiliknya |
| Request POST dari JS ditolak 403 | Pakai `api.post()` dari `/shared/api.js` (menambah header `X-JalanKu: 1`) |
| Inline style tidak jalan | CSP melarangnya. Pakai kelas CSS |
