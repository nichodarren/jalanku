"""Perintah baris: ``python -m jalanku <perintah>``. Jalankan dari folder ``app/``.

jalan          jalankan server (http://localhost:8000)
migrasi        terapkan migrasi basis data
kontrak        cek kontrak cocok dengan snapshot (--tulis memperbarui, --tabel cetak daftar endpoint)
contoh-data    isi DB lokal dengan laporan BERLABEL SIMULASI
peran          (M2, US-01) beri peran petugas/admin ke akun
backup         (M4, TS-03) backup DB + foto
uji-ai         (M4, US-05/SPIKE-02) evaluasi model pada folder foto berlabel
"""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="python -m jalanku", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = p.add_subparsers(dest="perintah", required=True)
    j = sub.add_parser("jalan")
    j.add_argument("--host", default="127.0.0.1")
    j.add_argument("--port", type=int, default=8000)
    j.add_argument("--reload", action="store_true")
    sub.add_parser("migrasi")
    k = sub.add_parser("kontrak")
    k.add_argument("--tulis", action="store_true")
    k.add_argument("--tabel", action="store_true")
    c = sub.add_parser("contoh-data")
    c.add_argument("--jumlah", type=int, default=30)
    r = sub.add_parser("peran")
    r.add_argument("email")
    r.add_argument("peran", choices=["pelapor", "petugas", "admin"])
    r.add_argument("--instansi")
    sub.add_parser("backup")
    u = sub.add_parser("uji-ai")
    u.add_argument("folder")
    a = p.parse_args(argv)

    if a.perintah == "jalan":
        import uvicorn

        uvicorn.run("jalanku.main:buat_app", factory=True, host=a.host, port=a.port, reload=a.reload)
        return 0
    if a.perintah == "migrasi":
        from jalanku.core import jalankan_migrasi

        baru = jalankan_migrasi()
        print("Migrasi baru:", ", ".join(baru) if baru else "tidak ada")
        return 0
    if a.perintah == "kontrak":
        from jalanku import kontrak

        if a.tabel:
            print(kontrak.tabel_endpoint(kontrak.openapi_terkini()))
            return 0
        if a.tulis:
            kontrak.tulis()
            print("Snapshot kontrak ditulis ke app/kontrak/. Commit bersama perubahan kodenya.")
            return 0
        beda = kontrak.bandingkan()
        if beda:
            print("Kontrak BERBEDA dengan snapshot:\n  " + "\n  ".join(beda))
            return 1
        print("Kontrak cocok dengan snapshot.")
        return 0
    if a.perintah == "contoh-data":
        from jalanku.contoh import DataBelumSiap, buat_contoh_data
        from jalanku.core import jalankan_migrasi

        jalankan_migrasi()
        try:
            nomor = buat_contoh_data(a.jumlah)
        except DataBelumSiap as galat:
            print(f"Data contoh belum dibuat: {galat}", file=sys.stderr)
            print("Setelah itu jalankan lagi: python -m jalanku contoh-data", file=sys.stderr)
            return 1
        print(f"{len(nomor)} laporan SIMULASI dibuat ({nomor[0] if nomor else '-'} dst.).")
        return 0
    pemilik = {"peran": "US-01, M2", "backup": "TS-03, M4", "uji-ai": "US-05/SPIKE-02, M4"}[a.perintah]
    print(f"Perintah '{a.perintah}' belum dibuat ({pemilik}).", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
