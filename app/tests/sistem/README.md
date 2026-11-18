# Test sistem (alur browser)

Pemilik: QA lead. Memakai Playwright (Python) terhadap server yang berjalan, ditandai `@pytest.mark.sistem` supaya bisa dijalankan terpisah:

```bash
pip install pytest-playwright && python -m playwright install chromium   # sekali
python -m pytest -m sistem
```

Alur minimal (Sprint 3): masuk → lapor dengan foto → laporan tampil di peta → admin verifikasi → petugas selesai dengan foto → pindah ke riwayat. Tambahkan `pytest-playwright` ke `pyproject.toml` (extra `dev`) lewat PR saat test pertama ditulis.
