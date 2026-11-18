# Test penerimaan (acceptance)

Satu file per story, nama `test_us<NN>_<ringkas>.py`, satu fungsi test per skenario Given/When/Then di issue story-nya (GitHub Projects). Docstring fungsi = kalimat skenario aslinya, supaya mudah ditelusuri dari story.

```python
def test_us06_foto_rusak_yang_diyakini_ai(buat_klien):
    """Given saya pelapor terverifikasi / When saya mengirim foto rusak yang diyakini AI di Monas
    / Then laporan berstatus Belum Dikerjakan dengan tingkat Rusak dan timeline menyebut AI JalanKu."""
```

Ditulis oleh pemilik story; QA lead me-review cakupannya. Fixture bersama ada di `app/conftest.py` (`buat_klien(peran)`, `TITIK`).
