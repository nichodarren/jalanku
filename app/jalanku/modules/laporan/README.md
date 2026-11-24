# Modul `laporan` (LAP)

| | |
|---|---|
| **Pemilik** | M1 (lihat CODEOWNERS) |
| **Tanggung jawab** | Domain inti: laporan, nomor JK-xxxxx, siklus status BR-03, timeline, foto aman, dukungan, visibilitas BR-06, detail publik. |
| **Requirement** | FR-LAP-01..05, BR-03, BR-06, BR-09, NFR-PRI-01/02, NFR-SEC-02 |
| **Story** | TS-02 (8), US-17 (5), US-32 (2) |
| **Boleh bergantung pada** | core, akun |
| **Tabel milik modul** | laporan, laporan_foto, laporan_timeline, laporan_dukungan |
| **Kejadian** | Menerbitkan `LaporanDibuat`, `StatusBerubah`. Mendengarkan `AkunDihapus`. |
| **Frontend** | `app/jalanku/web/modules/laporan/` |

## Antarmuka publik

Hanya nama di `__all__` pada [`__init__.py`](__init__.py). Tanda tangan terkunci di `app/kontrak/modul.json`; endpoint di `app/kontrak/openapi.json` (lihat juga `/api/docs` saat server jalan). Mengubah yang sudah ada = change request (issue template *Change request*); menambah sesuatu yang opsional cukup PR biasa + `python -m jalanku kontrak --tulis`.

## Dukungan

- `tambah_dukungan` (1 per akun per laporan), `jumlah_dukungan`, `pendukung`.
- `jumlah_dukungan_massal(laporan_ids) -> dict[int, int]`: hitung banyak laporan sekaligus dengan `GROUP BY` (CR #23, untuk `GET /api/peta`). Id tanpa dukungan → 0.
- **Saat digabung** (`ubah_status(..., STATUS_DIGABUNG, induk_nomor=...)`): pendukung laporan anak dan pelapornya otomatis menjadi pendukung induk, di dalam transaksi yang sama (port `reports.py` `gabung` jalanku-v0). Dukungan lama induk tidak ditimpa, dan pelapor induk tidak pernah tercatat mendukung laporannya sendiri. Pemanggil (moderasi) tidak perlu melakukan apa-apa.

## Jejak audit (US-32)

Setiap baris timeline menyimpan `hash = sha256(hash_sebelumnya + JSON[dari, ke, pelaku, catatan, waktu])`. Entri pertama memakai string kosong sebagai hash sebelumnya. Mengubah, menghapus, atau menyisipkan satu baris membuat semua hash sesudahnya tidak cocok.

- `periksa_jejak(laporan) -> (utuh, entri)`: hitung ulang rantai dari awal, lalu cek juga bahwa ujung rantai sama dengan status laporan saat ini. Dengan begitu status yang diubah langsung di DB tanpa lewat `ubah_status` ikut ketahuan.
- `GET /api/laporan/{nomor}/jejak`: entri (status, pelaku, waktu, hash; tanpa catatan dan id pengguna) + `utuh`, dengan aturan visibilitas yang sama dengan detail (BR-06, 404 untuk yang tidak boleh melihat).
- Halaman detail menampilkan lencana "Riwayat terverifikasi" bila `utuh` bernilai benar.

## Status (24 Nov 2026)

Semua story modul ini selesai dan sudah di `main`: TS-02 (#4, #5, #6), dukungan saat digabung + CR #23 (#34), US-17 (#35), US-32 (#36). Tidak ada lagi `TODO(` atau endpoint 501 di modul ini.

## Pekerjaan

- [x] TS-02: foto aman di `_foto.py` → validasi isi (Pillow), buang EXIF, encode ulang JPEG ≤ 1 MB (NFR-PRI-02, NFR-SEC-02)
- [x] TS-02: syarat transisi di domain (`_cek_syarat`: tingkat wajib, alasan ≥ 5 karakter, induk aktif, banding sekali & hanya untuk penolakan AI, foto sesudah wajib) + keterangan ≤ 280 karakter ditolak bila lebih
- [x] TS-02: visibilitas BR-06 (`boleh_dilihat`, `boleh_lihat_hasil_ai`) + test matriks status × penonton; petugas tidak punya hak lihat tambahan (daftar tugas per wilayah = modul `penanganan`); header cache foto publik/privat
- [x] Dukungan pindah ke induk saat digabung + `jumlah_dukungan_massal` (CR #23)
- [x] US-17: halaman detail `#/laporan/:nomor` (foto sebelum/sesudah, timeline berlabel pelaku, instansi + channel resmi, peta kecil, penanda SIMULASI, 404 ramah)
- [x] US-32: jejak audit rantai hash + `GET /api/laporan/{nomor}/jejak` + lencana di halaman detail

## Cara kerja di modul ini

```bash
cd app
python -m pytest jalanku/modules/laporan     # test modul ini saja
python -m pytest tests/arsitektur        # batas modul & kontrak
python -m jalanku contoh-data            # data SIMULASI di DB lokal
python -m jalanku jalan --reload         # http://localhost:8000, dokumentasi API di /api/docs
```

Aturan: jangan mengimpor isi dalam modul lain (`from jalanku.modules.X.layanan import ...` ❌), jangan query tabel modul lain, dan file migrasi yang sudah di-merge tidak boleh diedit.
