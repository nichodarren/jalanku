## Apa yang berubah

<!-- 1–3 kalimat. Judul PR: Conventional Commits + ID, mis. "feat(peta): bubble berkelompok (US-15)" -->

Closes #<!-- nomor issue; kata kunci Closes wajib bahasa Inggris supaya issue tertutup otomatis -->  ·  Story/CR: <!-- US-NN / CR-NN -->  ·  Modul: <!-- nama modul -->

## Cara menguji

<!-- Langkah singkat yang bisa diulang reviewer, mis. "masuk cepat sebagai admin → buka #/admin" -->

## Checklist Definition of Done

- [ ] Acceptance criteria punya test otomatis yang lulus
- [ ] `python -m pytest` hijau lokal, termasuk `tests/arsitektur`
- [ ] `ruff check . && ruff format --check .` bersih
- [ ] Tidak mengimpor isi dalam modul lain; tidak query tabel modul lain
- [ ] Kontrak: tidak berubah / berubah backward compatible + snapshot diperbarui / berubah memecah dengan CR-NN disetujui
- [ ] Input pengguna divalidasi di server; tidak ada secret di kode
- [ ] UI: Bahasa Indonesia, layar 360 px, bisa dengan keyboard (bila ada UI)
- [ ] README modul diperbarui bila antarmuka/perilaku berubah
- [ ] Pemakaian AI dicatat di log AI tim (atau: tidak memakai AI)
- [ ] Commit tanpa trailer `Co-Authored-By` asisten AI

## Catatan untuk reviewer

<!-- Hal yang ingin kamu minta dicek secara khusus -->
