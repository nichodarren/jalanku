"""NFR-MNT-03 / ADR-0005: kode harus cocok dengan snapshot kontrak di app/kontrak/.

Kalau test ini gagal:
- Perubahanmu TIDAK sengaja mengubah kontrak → kembalikan.
- Sengaja & backward compatible (endpoint/field opsional baru) → jalankan
  `python -m jalanku kontrak --tulis` dan commit snapshot-nya; M1 akan me-review.
- Sengaja & memecah kontrak (hapus/ganti nama/ubah tipe) → butuh change request dulu (issue template *Change request*).
"""

from __future__ import annotations

from jalanku import kontrak


def test_kontrak_cocok_dengan_snapshot():
    beda = kontrak.bandingkan()
    assert not beda, "Kontrak berbeda dengan snapshot:\n  " + "\n  ".join(beda[:40])


def test_setiap_endpoint_terdokumentasi():
    spek = kontrak.openapi_terkini()
    kurang = [
        f"{metode.upper()} {jalur}"
        for jalur, isi in spek["paths"].items()
        for metode, op in isi.items()
        if not op.get("summary") or not op.get("tags")
    ]
    assert not kurang, f"Endpoint tanpa summary/tag: {kurang}"
