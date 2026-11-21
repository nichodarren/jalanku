"""Pembersihan foto laporan sebelum disimpan (FR-LAP-04, NFR-SEC-02, NFR-PRI-02, NFR-PERF-03).

Diport dari MVP v2 (``jalanku-v0/app/jalanku/photos.py``, karya Yosua) dan disesuaikan ke
struktur modul: fungsi ini hanya mengubah bytes; penyimpanan berkas tetap lewat ``core``.

- Jenis file dicek dari isi (Pillow membaca header), bukan dari ekstensi/MIME kiriman klien.
- Foto selalu di-encode ulang menjadi JPEG baru. Metadata tidak disalin, sehingga seluruh EXIF
  (termasuk GPS kamera dan model perangkat) ikut terbuang.
- Orientasi EXIF diterapkan dulu ke piksel supaya foto tidak terbalik setelah EXIF dibuang.
"""

from __future__ import annotations

import io

from PIL import Image, ImageOps, UnidentifiedImageError

from jalanku.core import TidakValid

FORMAT_DIIZINKAN = frozenset({"JPEG", "PNG", "WEBP"})
MAKS_INPUT_BYTES = 10 * 1024 * 1024
MAKS_SIMPAN_BYTES = 1024 * 1024
SISI_MAKS_PX = 1600
_MAKS_PIKSEL = 40_000_000  # cegah decompression bomb
_KUALITAS = (82, 72, 62, 52, 42)


def _ke_rgb(img: Image.Image) -> Image.Image:
    if img.mode == "RGB":
        return img
    if img.mode == "L":
        return img.convert("RGB")
    latar = Image.new("RGB", img.size, (255, 255, 255))
    rgba = img.convert("RGBA")
    latar.paste(rgba, mask=rgba.split()[-1])
    return latar


def _encode(img: Image.Image, kualitas: int) -> bytes:
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=kualitas, optimize=True)  # tanpa exif=... → tidak ada metadata
    return buf.getvalue()


def bersihkan_foto(data: bytes) -> bytes:
    """Validasi isi foto lalu kembalikan JPEG baru tanpa metadata, ≤ 1 MB, sisi terpanjang ≤ 1600 px.

    Melempar ``TidakValid`` bila kosong, terlalu besar, bukan gambar, atau formatnya tidak didukung.
    """
    if not data:
        raise TidakValid("Foto kosong.")
    if len(data) > MAKS_INPUT_BYTES:
        raise TidakValid(f"Ukuran foto maksimal {MAKS_INPUT_BYTES // (1024 * 1024)} MB.")

    Image.MAX_IMAGE_PIXELS = _MAKS_PIKSEL
    try:
        with Image.open(io.BytesIO(data)) as uji:
            fmt = uji.format
            uji.verify()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, SyntaxError) as e:
        raise TidakValid("File bukan gambar yang bisa dibaca. Gunakan JPG, PNG, atau WebP.") from e
    if fmt not in FORMAT_DIIZINKAN:
        raise TidakValid("Format foto harus JPG, PNG, atau WebP.")

    with Image.open(io.BytesIO(data)) as asli:
        img = _ke_rgb(ImageOps.exif_transpose(asli))
        img.thumbnail((SISI_MAKS_PX, SISI_MAKS_PX), Image.Resampling.LANCZOS)

        for kualitas in _KUALITAS:
            hasil = _encode(img, kualitas)
            if len(hasil) <= MAKS_SIMPAN_BYTES:
                return hasil
        while len(hasil) > MAKS_SIMPAN_BYTES and min(img.size) > 320:
            img = img.resize((int(img.width * 0.8), int(img.height * 0.8)), Image.Resampling.LANCZOS)
            hasil = _encode(img, 60)
        return hasil
