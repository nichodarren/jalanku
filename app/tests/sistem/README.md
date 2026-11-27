# Test sistem (alur browser)

Pemilik: QA lead (M5). Memakai Playwright (Python, `pytest-playwright` sudah ada di `requirements.lock` / extra `dev`) terhadap server sungguhan, ditandai `@pytest.mark.sistem`.

Test sistem **tidak** ikut `python -m pytest` biasa maupun CI (`addopts` memuat `-m 'not sistem'`), karena butuh browser. Jalankan terpisah:

```bash
python -m playwright install chromium   # sekali per laptop (±150 MB)
python -m pytest -m sistem               # semua test sistem
python -m pytest -m sistem --headed      # lihat browsernya (untuk debug/demo)
```

Bila Chromium belum terpasang, test sistem di-skip dengan pesan yang jelas.

Alur minimal (Sprint 3): masuk → lapor dengan foto → laporan tampil di peta → admin verifikasi → petugas selesai dengan foto → pindah ke riwayat. Alur yang endpoint-nya belum aktif di `main` (mis. pelaporan) ditambahkan begitu PR pemiliknya masuk.
