"""Perilaku stub ai = perilaku 'model tidak aktif' (NFR-REL-02), tetap berlaku setelah model asli ada."""

from __future__ import annotations

from jalanku.modules import ai


def test_tanpa_model_semua_foto_ke_admin():
    h = ai.periksa_foto(b"apa saja")
    assert h.keputusan == ai.FOTO_ADMIN and h.alasan


def test_tanpa_model_laporan_tidak_diputuskan_otomatis():
    k = ai.putuskan([ai.periksa_foto(b"x")])
    assert k.keputusan in (ai.KEPUTUSAN_TIDAK_AKTIF, ai.KEPUTUSAN_PERLU_ADMIN) and k.tingkat is None


def test_threshold_bawaan_br07():
    info = ai.info_model()
    assert info["threshold_confidence"] == 0.80 and info["threshold_kemiripan"] == 0.708


def test_pratinjau_butuh_login(klien, buat_klien):
    assert klien.post("/api/ai/periksa", files={"foto": ("a.jpg", b"x", "image/jpeg")}).status_code == 401
    r = buat_klien("pelapor").post("/api/ai/periksa", files={"foto": ("a.jpg", b"x", "image/jpeg")})
    assert r.status_code == 200 and r.json()["keputusan"] == "admin"
