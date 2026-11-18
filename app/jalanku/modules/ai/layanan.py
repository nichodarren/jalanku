"""Pemeriksaan foto dan keputusan AI (FR-AI-01, FR-AI-02, BR-07).

STUB (baseline 19 Nov 2026): model belum dipasang, jadi berperilaku seperti "model tidak aktif"
(NFR-REL-02): setiap foto → ke Admin, setiap laporan → ``tidak_aktif`` → Menunggu Verifikasi.

Pekerjaan M4:
- US-05: port model dari jalanku-v0 branch trial/mvp-v2 (``app/jalanku/model/`` + ``app/jalanku/ai.py``)
  ke ``modules/ai/model/`` dan ``modules/ai/_model.py``; isi ``periksa_foto``.
- US-06: isi ``putuskan`` sesuai BR-07 (fungsi murni, mudah di-TDD).
- Threshold: ``pengaturan().ai_threshold_confidence`` / ``ai_threshold_kemiripan`` menimpa nilai di model.
"""

from __future__ import annotations

from jalanku.core import pengaturan

from .tipe import FOTO_ADMIN, KEPUTUSAN_PERLU_ADMIN, KEPUTUSAN_TIDAK_AKTIF, HasilFoto, KeputusanAI

T_CONF_BAWAAN = 0.80
T_MIRIP_BAWAAN = 0.708


def model_aktif() -> bool:
    return False  # STUB: TODO(US-05) True bila pengaturan().ai_aktif dan model berhasil dimuat


def periksa_foto(data: bytes) -> HasilFoto:
    # TODO(US-05): praproses + inferensi ONNX + classifier + kemiripan.
    return HasilFoto(
        kelas=None,
        confidence=None,
        kemiripan=None,
        keputusan=FOTO_ADMIN,
        alasan="Pemeriksaan otomatis sedang tidak aktif. Foto akan diperiksa Admin.",
    )


def putuskan(hasil: list[HasilFoto]) -> KeputusanAI:
    # TODO(US-06): BR-07 per laporan (ada terima → terverifikasi + tingkat terparah;
    #              semua tolak → ditolak; selainnya → perlu_admin).
    keputusan = KEPUTUSAN_PERLU_ADMIN if model_aktif() else KEPUTUSAN_TIDAK_AKTIF
    return KeputusanAI(keputusan=keputusan, tingkat=None, hasil_foto=list(hasil), versi_model=None)


def info_model() -> dict:
    cfg = pengaturan()
    return {
        "aktif": model_aktif(),
        "versi": None,
        "threshold_confidence": cfg.ai_threshold_confidence or T_CONF_BAWAAN,
        "threshold_kemiripan": cfg.ai_threshold_kemiripan or T_MIRIP_BAWAAN,
    }
