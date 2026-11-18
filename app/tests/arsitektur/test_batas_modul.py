"""NFR-MNT-02: modul hanya bergantung pada antarmuka publik modul lain, mengikuti graf yang diizinkan.

Graf ini juga tertulis di README.id.md (bagian Arsitektur). Mengubahnya = change request.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

AKAR = Path(__file__).resolve().parents[2] / "jalanku"
FOLDER_MODUL = AKAR / "modules"

IZIN: dict[str, set[str]] = {
    "akun": set(),
    "wilayah": {"akun"},
    "laporan": {"akun"},
    "ai": {"akun", "laporan"},
    "pelaporan": {"akun", "laporan", "wilayah", "ai"},
    "moderasi": {"akun", "laporan", "wilayah"},
    "penanganan": {"akun", "laporan", "wilayah", "ai"},
    "peta": {"akun", "laporan", "wilayah"},
    "statistik": {"akun", "laporan", "wilayah"},
    "notifikasi": {"akun", "laporan"},
}
TERLARANG_DARI_MODUL = ("jalanku.main", "jalanku.kontrak", "jalanku.contoh", "jalanku.__main__")


def _berkas_produksi(folder: Path):
    for berkas in folder.rglob("*.py"):
        if "tests" in berkas.relative_to(folder).parts:
            continue
        yield berkas


def _impor(berkas: Path, paket: str) -> list[tuple[int, str, list[str]]]:
    """(baris, modul yang diimpor (absolut), nama yang diambil)."""
    pohon = ast.parse(berkas.read_text(encoding="utf-8"))
    hasil = []
    for node in ast.walk(pohon):
        if isinstance(node, ast.Import):
            hasil += [(node.lineno, a.name, []) for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # impor relatif → ubah ke absolut
                dasar = paket.split(".")
                dasar = dasar[: len(dasar) - node.level + 1]
                nama = ".".join(dasar + ([node.module] if node.module else []))
            else:
                nama = node.module or ""
            hasil.append((node.lineno, nama, [a.name for a in node.names]))
    return hasil


def _paket(berkas: Path) -> str:
    rel = berkas.relative_to(AKAR.parent).with_suffix("")
    # Paket tempat berkas berada (untuk __init__.py maupun berkas biasa = folder induknya).
    return ".".join(rel.parts[:-1])


def test_daftar_modul_sama_dengan_folder():
    ada = {p.name for p in FOLDER_MODUL.iterdir() if p.is_dir() and not p.name.startswith("_")}
    assert ada == set(IZIN), "Modul baru/hilang? Perbarui IZIN di test ini lewat change request."


@pytest.mark.parametrize("modul", sorted(IZIN))
def test_modul_hanya_memakai_antarmuka_publik(modul):
    pelanggaran = []
    for berkas in _berkas_produksi(FOLDER_MODUL / modul):
        for baris, nama, diambil in _impor(berkas, _paket(berkas)):
            lokasi = f"{berkas.relative_to(AKAR.parent)}:{baris}"
            if nama.startswith(TERLARANG_DARI_MODUL):
                pelanggaran.append(f"{lokasi} mengimpor {nama} (hanya untuk perakit)")
            if nama.startswith("jalanku.core."):
                pelanggaran.append(f"{lokasi} mengimpor {nama}; pakai `from jalanku.core import ...`")
            if nama == "jalanku.modules":
                target = set(diambil)
            elif nama.startswith("jalanku.modules."):
                bagian = nama.split(".")
                target = {bagian[2]}
                if bagian[2] != modul and len(bagian) > 3:
                    pelanggaran.append(
                        f"{lokasi} mengimpor isi dalam {nama}; pakai `from jalanku.modules.{bagian[2]} import ...`"
                    )
            else:
                continue
            for t in target - {modul}:
                if t not in IZIN[modul]:
                    pelanggaran.append(
                        f"{lokasi}: modul '{modul}' tidak boleh bergantung pada '{t}' (lihat graf dependensi)"
                    )
    assert not pelanggaran, "\n".join(pelanggaran)


def test_core_tidak_mengenal_modul():
    for berkas in _berkas_produksi(AKAR / "core"):
        for _, nama, _ in _impor(berkas, _paket(berkas)):
            assert not nama.startswith("jalanku.modules"), f"{berkas.name}: core tidak boleh mengimpor modul"


def test_graf_dependensi_tanpa_siklus():
    sudah, sedang = set(), set()

    def kunjungi(m):
        assert m not in sedang, f"Siklus dependensi melibatkan {m}"
        if m in sudah:
            return
        sedang.add(m)
        for t in IZIN[m]:
            kunjungi(t)
        sedang.discard(m)
        sudah.add(m)

    for m in IZIN:
        kunjungi(m)


@pytest.mark.parametrize("modul", sorted(IZIN))
def test_tabel_berprefiks_nama_modul(modul):
    for berkas in (
        (FOLDER_MODUL / modul / "migrasi").glob("*.sql") if (FOLDER_MODUL / modul / "migrasi").exists() else []
    ):
        for tabel in re.findall(
            r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(\w+)", berkas.read_text(encoding="utf-8"), re.I
        ):
            assert tabel == modul or tabel.startswith(modul + "_"), (
                f"{berkas.name}: tabel '{tabel}' harus berprefiks '{modul}_'"
            )


@pytest.mark.parametrize("modul", sorted(IZIN))
def test_setiap_modul_punya_kartu_dan_antarmuka(modul):
    folder = FOLDER_MODUL / modul
    assert (folder / "README.md").is_file(), f"{modul}: README.md (kartu modul) wajib ada"
    assert (folder / "__init__.py").is_file()
    teks = (folder / "__init__.py").read_text(encoding="utf-8")
    assert "__all__" in teks, f"{modul}: __init__.py wajib mendefinisikan __all__ (antarmuka publik)"
