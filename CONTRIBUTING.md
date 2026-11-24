# Cara berkontribusi

## Sekali di awal: identitas Git

Setiap commit harus atas nama **kamu sendiri** (penilaian kontribusi per anggota). Pakai email yang terdaftar di akun GitHub-mu:

```bash
git config --global user.name  "Nama Kamu"
git config --global user.email "email-akun-github@kamu"
```

## Alur kerja (GitHub Flow)

```
kartu di board  →  branch dari main  →  commit kecil  →  PR  →  CI hijau + review  →  squash merge  →  hapus branch
```

1. **Ambil kartu** di board GitHub Projects (kolom *Siap*), isi Pemilik, pindahkan ke *Dikerjakan* (maks 2 kartu per orang).
2. **Buat branch** dari `main` terbaru:
   ```bash
   git switch main && git pull
   git switch -c feat/us-15-bubble-peta        # <jenis>/<id>-<ringkas>
   ```
   Jenis: `feat`, `fix`, `test`, `refactor`, `chore`, `ci`, `docs`.
3. **Commit kecil & sering** dengan Conventional Commits + ID story. Scope = nama modul:
   ```
   feat(peta): tampilkan bubble berkelompok (US-15)
   test(ai): kasus confidence tepat di batas 0,80 (US-06)
   fix(laporan): tolak transisi selesai → sedang (TS-02)
   ```
4. **Sebelum push**, dari folder `app/` (pertama kali di laptop baru: `python -m jalanku.modules.wilayah.data.setup_wilayah`, lihat `app/README.md`):
   ```bash
   ruff check --fix . && ruff format .
   python -m pytest
   ```
5. **Buka PR** ke `main` dengan template yang tersedia. Tautkan issue dengan kata kunci GitHub **`Closes #12`** (harus bahasa Inggris: `Closes`/`Fixes`; tulisan `Menutup #12` tidak menutup issue otomatis saat PR di-merge).
6. **Review**: pemilik modul terkait (otomatis dari CODEOWNERS) + pasangan review-mu. Reviewer menjawab ≤ 48 jam (lihat *Panduan review* di bawah).
7. **Merge**: *Squash and merge* setelah CI hijau + ≥ 1 approve. Penulis PR yang menekan merge, lalu hapus branch.

Target ukuran PR ≤ 300 baris berubah (di luar snapshot kontrak, data, dan model). PR besar dipecah: kontrak dulu, lalu logika, lalu UI.

## Mem-port kode dari `jalanku-v0`

Prototipe sebelumnya ada di repo `nichodarren/jalanku-v0` (branch `trial/mvp-v2`). Kode di sana **boleh dan dianjurkan** dipakai ulang. Saat mem-port:
- Sesuaikan dengan struktur & kontrak modul di repo ini (jangan menyalin file datar apa adanya).
- Tulis/porting test-nya juga; pastikan `python -m pytest` hijau.
- Sebutkan asal kode di deskripsi PR, misalnya: *"Diport dari jalanku-v0@65db419 `app/jalanku/geo.py` (karya Yosua), disesuaikan ke kontrak modul wilayah + test titik nyata."*

## Konflik merge

```bash
git switch main && git pull
git switch feat/us-15-bubble-peta
git merge main            # selesaikan konflik, lalu:
python -m pytest && git commit
```
Konflik di file milik orang lain → tanyakan pemiliknya. Konflik di `app/kontrak/*.json` → jangan edit manual; jalankan `python -m jalanku kontrak --tulis` setelah merge.

## Panduan review

Periksa: (1) acceptance criteria story terpenuhi; (2) test menguji perilaku, bukan detail implementasi; (3) batas modul & kontrak dipatuhi; (4) input pengguna divalidasi di server dan otorisasi benar; (5) nama mengikuti istilah resmi (README); (6) README modul diperbarui bila perlu. Komentar spesifik dan sopan; awali dengan `nit:` untuk hal kecil yang tidak memblokir.

## Memakai asisten AI

Boleh, dengan syarat:
1. Kamu **memahami dan me-review setiap baris** yang kamu commit, dan bisa menjelaskannya ke dosen.
2. **Commit tetap atas namamu**, tanpa trailer `Co-Authored-By` asisten AI dan tanpa tanda "Generated with ..." di PR.
3. **Catat pemakaiannya di log AI tim** (tanggal, nama, bagian, tool, ringkasan prompt). Ini dibutuhkan untuk form deklarasi pemakaian AI di laporan akhir.
4. Tidak boleh memakai AI untuk membuat data wawancara, hasil uji, atau bukti palsu.

## Yang TIDAK boleh

- Push langsung ke `main`, `git push --force` ke branch bersama, atau merge PR sendiri tanpa review.
- Mengedit file migrasi yang sudah di-merge (buat migrasi baru).
- Mengimpor isi dalam modul lain atau query tabel modul lain.
- Commit secret, file `.env`, database, dataset foto, file konteks AI pribadi, atau data pribadi (NIM, email asli).
- Commit atas nama orang lain.
