# Test penerimaan (acceptance)

Level **Acceptance** dari strategi 4 level: setiap skenario Given/When/Then di issue story **Must** punya satu test otomatis di sini. UAT dengan warga (manual) dicatat terpisah oleh QA + PO, hanya dari sesi nyata.

## Aturan

1. **Satu file per story:** `test_us<NN>_<ringkas>.py`, mis. `test_us13_banding.py`.
2. **Satu fungsi per skenario** di issue story-nya, nama `test_us<NN>_<perilaku>`.
3. **Docstring = kalimat skenario persis dari issue** (Given / When / Then), supaya bisa ditelusuri dari story ke test dan sebaliknya.
4. **Uji lewat HTTP** (`buat_klien(peran)`) seperti pengguna sungguhan. Menyiapkan data (Given) boleh lewat antarmuka publik modul (`from jalanku.modules import laporan as L`), bukan lewat tabel.
5. **Data uji fiktif:** laporan berlabel SIMULASI, email `@uji.test`, tanpa NIM/data pribadi.
6. **Assert hasil yang dilihat pengguna:** kode HTTP, isi respons, status laporan, timeline. Untuk skenario "ditolak", pastikan juga **tidak ada efek samping** (status tetap, tidak ada entri baru).
7. Ditulis **pemilik story**, di PR yang sama dengan fiturnya. QA lead (M5) me-review cakupannya.

## Contoh

```python
"""US-13 Ajukan banding atas penolakan AI (pemilik M5). Skenario penerimaan lewat API (issue #47)."""

from conftest import TITIK, foto_bytes
from jalanku.modules import laporan as L


def test_us13_penolakan_admin_tidak_bisa_dibanding(buat_klien):
    """Given penolakan berasal dari Admin / When pelapor meminta banding / Then permintaan ditolak
    dan status tetap."""
    warga = buat_klien("pelapor", email="ditolak-admin@uji.test")
    pid = warga.get("/api/akun/saya").json()["id"]
    lap = L.buat_laporan(L.LaporanBaru(pelapor_id=pid, lat=TITIK["monas"][0], lon=TITIK["monas"][1],
                                       sumber_lokasi="gps", kota="Jakarta Pusat", kecamatan="Gambir",
                                       instansi_id="SUDIN_JP", foto=[foto_bytes()], keputusan_ai="perlu_admin"))
    L.ubah_status(lap.nomor, L.STATUS_DITOLAK, L.PELAKU_ADMIN, pengguna_id=99, catatan="Foto bukan jalan")

    r = warga.post(f"/api/laporan/{lap.nomor}/banding")

    assert r.status_code == 409
    assert L.ambil_laporan(lap.nomor).status == L.STATUS_DITOLAK
```

## Fixture bersama (`app/conftest.py`)

| Nama | Isi |
|---|---|
| `buat_klien(peran=None, email=None, instansi_id=None)` | Klien HTTP; dengan `peran` sudah masuk (masuk cepat dev, mode test). Setiap klien = pengguna berbeda. |
| `klien` | Pengunjung tanpa login. |
| `TITIK["monas" \| "blok_m" \| "jatinegara" \| "kelapa_gading" \| "grogol" \| "kota_tangerang"]` | Koordinat nyata untuk skenario wilayah. |
| `foto_bytes()` | Gambar JPEG valid (bukan foto jalan sungguhan). |

Membekukan waktu (mis. skenario "lebih dari 24 jam"): `from jalanku.core.waktu import atur_waktu`, lalu `atur_waktu("2026-11-20T08:00:00+00:00")`; fixture `lingkungan` mengembalikannya setelah test.

## Teknik yang diharapkan

| Teknik | Contoh di proyek ini |
|---|---|
| Boundary value | duplikat 25 m, 0/1/3/4 foto, 280/281 karakter, confidence 0,80, median n = 4/5, alasan 4/5 karakter, rate limit ke-60/61 |
| State transition | transisi BR-03 yang sah **dan** yang terlarang (mis. banding kedua, banding atas penolakan Admin) |
| Decision table | BR-07 kombinasi keputusan per foto |
| Equivalence partitioning | peran (pengunjung / pelapor / petugas / admin) × aksi → 200 / 401 / 403 / 404 |

## Checklist review QA (tempel di komentar PR)

- [ ] Setiap skenario di issue punya satu fungsi test, docstring sama dengan kalimat skenario
- [ ] Test menguji **perilaku** lewat API, bukan detail implementasi
- [ ] Skenario negatif mengecek tidak ada efek samping
- [ ] Ada boundary value / state transition yang relevan
- [ ] Data uji SIMULASI / `@uji.test`
- [ ] `python -m pytest tests/penerimaan` lulus

## Menjalankan & merekap

```bash
cd app
python -m pytest tests/penerimaan -v                   # semua test penerimaan
python -m pytest tests/penerimaan --co -q              # jumlah skenario otomatis per story (bahan rekap bab Testing)
```
