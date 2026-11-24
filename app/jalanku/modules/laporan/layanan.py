"""Domain laporan: penyimpanan, nomor, siklus status (BR-03), timeline, dukungan, visibilitas (BR-06).

TS-02 selesai: foto dibersihkan di ``_foto.py`` (validasi isi, buang EXIF, JPEG ≤ 1 MB); syarat transisi
BR-03 ditegakkan di ``_cek_syarat`` (siapa boleh apa ada di ``TRANSISI``); visibilitas BR-06 di
``boleh_dilihat`` dan ``boleh_lihat_hasil_ai``.
"""

from __future__ import annotations

import json
import sqlite3

from jalanku.core import (
    Konflik,
    TidakDitemukan,
    TidakValid,
    jarak_meter,
    koneksi,
    langganan,
    pengaturan,
    sekarang,
    simpan_berkas,
    terbitkan,
    transaksi,
)
from jalanku.modules.akun import PERAN_ADMIN, AkunDihapus, Pengguna

from ._foto import bersihkan_foto
from .tipe import (
    PELAKU_ADMIN,
    PELAKU_AI,
    PELAKU_PELAPOR,
    PELAKU_PETUGAS,
    PELAKU_SISTEM,
    STATUS_AKTIF,
    STATUS_BELUM,
    STATUS_DIGABUNG,
    STATUS_DITOLAK,
    STATUS_MENUNGGU,
    STATUS_PUBLIK,
    STATUS_SEDANG,
    STATUS_SELESAI,
    URUTAN_TINGKAT,
    EntriTimeline,
    Foto,
    Laporan,
    LaporanBaru,
    LaporanDibuat,
    StatusBerubah,
)

MAKS_KETERANGAN = 280  # FR-LAP-01
MIN_ALASAN = 5  # alasan penolakan Admin

# BR-03: (dari, ke) → pelaku yang boleh. Status awal ditentukan di buat_laporan.
TRANSISI: dict[tuple[str, str], set[str]] = {
    (STATUS_DITOLAK, STATUS_MENUNGGU): {PELAKU_PELAPOR},
    (STATUS_MENUNGGU, STATUS_BELUM): {PELAKU_ADMIN},
    (STATUS_MENUNGGU, STATUS_DITOLAK): {PELAKU_ADMIN},
    (STATUS_MENUNGGU, STATUS_DIGABUNG): {PELAKU_ADMIN},
    (STATUS_BELUM, STATUS_DIGABUNG): {PELAKU_ADMIN},
    (STATUS_BELUM, STATUS_SEDANG): {PELAKU_PETUGAS},
    (STATUS_BELUM, STATUS_SELESAI): {PELAKU_PETUGAS},
    (STATUS_SEDANG, STATUS_SELESAI): {PELAKU_PETUGAS},
}

_KOLOM = [
    "id",
    "nomor",
    "pelapor_id",
    "lat",
    "lon",
    "akurasi_gps",
    "sumber_lokasi",
    "kota",
    "kecamatan",
    "instansi_id",
    "status",
    "tingkat",
    "keterangan",
    "diperiksa_oleh",
    "keputusan_ai",
    "versi_model",
    "label_akhir",
    "induk_id",
    "banding_pada",
    "simulasi",
    "dibuat_pada",
    "diverifikasi_pada",
    "mulai_dikerjakan_pada",
    "selesai_pada",
]


def _ke_laporan(b: sqlite3.Row) -> Laporan:
    data = {k: b[k] for k in _KOLOM}
    data["simulasi"] = bool(data["simulasi"])
    return Laporan(**data)


def _simpan_foto(kon: sqlite3.Connection, laporan_id: int, jenis: str, bersih: bytes, hasil_ai: dict | None) -> None:
    """``bersih`` = hasil ``bersihkan_foto``; dibersihkan sebelum transaksi supaya foto tidak valid
    menggagalkan seluruh laporan sebelum ada berkas yang ditulis."""
    nama = simpan_berkas(bersih, ".jpg")
    kon.execute(
        "INSERT INTO laporan_foto (laporan_id, jenis, berkas, ai_json, dibuat_pada) VALUES (?, ?, ?, ?, ?)",
        (laporan_id, jenis, nama, json.dumps(hasil_ai) if hasil_ai else None, sekarang()),
    )


def _catat(kon, laporan_id: int, dari: str | None, ke: str, pelaku: str, pengguna_id: int | None, catatan: str):
    # TODO(US-32): hitung hash = sha256(hash entri sebelumnya laporan ini + dari|ke|pelaku|catatan|waktu)
    #              dan simpan ke kolom `hash` supaya riwayat tidak bisa diubah diam-diam.
    kon.execute(
        """INSERT INTO laporan_timeline (laporan_id, dari_status, ke_status, pelaku, pengguna_id, catatan, waktu)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (laporan_id, dari, ke, pelaku, pengguna_id, catatan, sekarang()),
    )


# --- Membuat & membaca -------------------------------------------------------------------------


def buat_laporan(data: LaporanBaru) -> Laporan:
    if not 1 <= len(data.foto) <= 3:
        raise TidakValid("Laporan butuh 1 sampai 3 foto.")
    if data.keputusan_ai == "terverifikasi" and data.tingkat not in URUTAN_TINGKAT:
        raise TidakValid("Keputusan terverifikasi wajib menyertakan tingkat.")
    if len(data.keterangan) > MAKS_KETERANGAN:
        raise TidakValid(f"Keterangan maksimal {MAKS_KETERANGAN} karakter.")
    bersih = [bersihkan_foto(f) for f in data.foto]
    if data.keputusan_ai == "terverifikasi":
        status, diperiksa, pelaku, catatan = STATUS_BELUM, PELAKU_AI, PELAKU_AI, "Diverifikasi oleh AI JalanKu"
    elif data.keputusan_ai == "ditolak":
        status, diperiksa, pelaku, catatan = (
            STATUS_DITOLAK,
            PELAKU_AI,
            PELAKU_AI,
            "AI JalanKu menilai jalan dalam kondisi baik",
        )
    else:
        status, diperiksa, pelaku, catatan = STATUS_MENUNGGU, None, PELAKU_SISTEM, "Menunggu pemeriksaan Admin"
    kini = sekarang()
    with transaksi() as kon:
        baru_id = kon.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM laporan").fetchone()[0]
        kon.execute(
            """INSERT INTO laporan (id, nomor, pelapor_id, lat, lon, akurasi_gps, sumber_lokasi, kota, kecamatan,
                 instansi_id, status, tingkat, keterangan, diperiksa_oleh, keputusan_ai, versi_model, simulasi,
                 dibuat_pada, diverifikasi_pada, diubah_pada)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                baru_id,
                f"JK-{baru_id:05d}",
                data.pelapor_id,
                data.lat,
                data.lon,
                data.akurasi_gps,
                data.sumber_lokasi,
                data.kota,
                data.kecamatan,
                data.instansi_id,
                status,
                data.tingkat if status == STATUS_BELUM else None,
                data.keterangan,
                diperiksa,
                data.keputusan_ai,
                data.versi_model,
                int(data.simulasi),
                kini,
                kini if status == STATUS_BELUM else None,
                kini,
            ),
        )
        for i, foto in enumerate(bersih):
            _simpan_foto(kon, baru_id, "bukti", foto, data.hasil_ai[i] if i < len(data.hasil_ai) else None)
        _catat(kon, baru_id, None, status, pelaku, None, catatan)
    laporan = ambil_laporan(f"JK-{baru_id:05d}")
    terbitkan(LaporanDibuat(laporan.id, laporan.nomor, laporan.status, laporan.pelapor_id))
    return laporan


def ambil_laporan(nomor: str) -> Laporan:
    """Tanpa cek visibilitas — hanya untuk logika server. Untuk pengguna pakai ``ambil_untuk_penonton``."""
    kon = koneksi()
    try:
        b = kon.execute("SELECT * FROM laporan WHERE nomor = ?", (nomor,)).fetchone()
    finally:
        kon.close()
    if b is None:
        raise TidakDitemukan("Laporan tidak ditemukan.")
    return _ke_laporan(b)


def _ambil_per_id(laporan_id: int) -> Laporan:
    kon = koneksi()
    try:
        b = kon.execute("SELECT * FROM laporan WHERE id = ?", (laporan_id,)).fetchone()
    finally:
        kon.close()
    if b is None:
        raise TidakDitemukan("Laporan tidak ditemukan.")
    return _ke_laporan(b)


def boleh_dilihat(laporan: Laporan, penonton: Pengguna | None) -> bool:
    """BR-06 (FR-LAP-03): berlaku untuk detail, timeline, dan berkas foto laporan.

    - Status publik (belum/sedang dikerjakan, selesai, digabung): semua orang, termasuk pengunjung.
    - Menunggu verifikasi & ditolak: hanya pelapornya dan Admin. Setelah akun pelapor dihapus
      (``pelapor_id`` kosong), hanya Admin.
    - Petugas tidak punya hak lihat tambahan; "laporan publik di wilayahnya" adalah aturan daftar
      tugas di modul ``penanganan``, bukan aturan lihat detail.
    Pemanggil yang menolak akses wajib menjawab 404 (bukan 403) agar keberadaan laporan tidak bocor.
    """
    if laporan.status in STATUS_PUBLIK:
        return True
    if penonton is None:
        return False
    if penonton.peran == PERAN_ADMIN:
        return True
    return laporan.pelapor_id is not None and penonton.id == laporan.pelapor_id


def boleh_lihat_hasil_ai(laporan: Laporan, foto: Foto, penonton: Pengguna | None) -> bool:
    """Hasil AI foto bukti hanya untuk pelapornya & Admin; hasil AI foto sesudah perbaikan publik (US-31)."""
    if foto.jenis == "sesudah":
        return True
    if penonton is None:
        return False
    return penonton.peran == PERAN_ADMIN or (laporan.pelapor_id is not None and penonton.id == laporan.pelapor_id)


def ambil_untuk_penonton(nomor: str, penonton: Pengguna | None) -> Laporan:
    laporan = ambil_laporan(nomor)
    if not boleh_dilihat(laporan, penonton):
        raise TidakDitemukan("Laporan tidak ditemukan.")  # 404, bukan 403: tidak membocorkan keberadaan
    return laporan


def cari_laporan(
    *,
    status: tuple[str, ...] | list[str] | str | None = None,
    instansi_id: str | None = None,
    kota: str | None = None,
    tingkat: str | None = None,
    pelapor_id: int | None = None,
    batas: int = 1000,
) -> list[Laporan]:
    syarat, nilai = [], []
    if status is not None:
        daftar = [status] if isinstance(status, str) else list(status)
        syarat.append(f"status IN ({','.join('?' * len(daftar))})")
        nilai += daftar
    for kolom, v in (("instansi_id", instansi_id), ("kota", kota), ("tingkat", tingkat), ("pelapor_id", pelapor_id)):
        if v is not None:
            syarat.append(f"{kolom} = ?")
            nilai.append(v)
    where = ("WHERE " + " AND ".join(syarat)) if syarat else ""
    kon = koneksi()
    try:
        rows = kon.execute(f"SELECT * FROM laporan {where} ORDER BY id DESC LIMIT ?", (*nilai, batas))  # noqa: S608
        return [_ke_laporan(b) for b in rows]
    finally:
        kon.close()


def cari_aktif_dekat(lat: float, lon: float, radius_m: float = 25) -> list[tuple[Laporan, float]]:
    """Laporan aktif (BR-02) dalam radius, urut dari yang terdekat."""
    d = radius_m / 111_000 + 0.0005  # saring kasar dengan kotak, lalu hitung haversine
    kon = koneksi()
    try:
        rows = kon.execute(
            f"""SELECT * FROM laporan WHERE status IN ({",".join("?" * len(STATUS_AKTIF))})
                AND lat BETWEEN ? AND ? AND lon BETWEEN ? AND ?""",  # noqa: S608
            (*STATUS_AKTIF, lat - d, lat + d, lon - d, lon + d),
        ).fetchall()
    finally:
        kon.close()
    hasil = [(_ke_laporan(b), jarak_meter(lat, lon, b["lat"], b["lon"])) for b in rows]
    return sorted([h for h in hasil if h[1] <= radius_m], key=lambda h: h[1])


def daftar_foto(laporan_id: int) -> list[Foto]:
    kon = koneksi()
    try:
        rows = kon.execute("SELECT * FROM laporan_foto WHERE laporan_id = ? ORDER BY id", (laporan_id,)).fetchall()
    finally:
        kon.close()
    return [
        Foto(b["id"], b["laporan_id"], b["jenis"], b["berkas"], json.loads(b["ai_json"]) if b["ai_json"] else None)
        for b in rows
    ]


def ambil_foto(foto_id: int) -> Foto:
    kon = koneksi()
    try:
        b = kon.execute("SELECT * FROM laporan_foto WHERE id = ?", (foto_id,)).fetchone()
    finally:
        kon.close()
    if b is None:
        raise TidakDitemukan("Foto tidak ditemukan.")
    return Foto(b["id"], b["laporan_id"], b["jenis"], b["berkas"], json.loads(b["ai_json"]) if b["ai_json"] else None)


def laporan_dari_foto(foto: Foto) -> Laporan:
    return _ambil_per_id(foto.laporan_id)


def timeline(laporan_id: int) -> list[EntriTimeline]:
    kon = koneksi()
    try:
        rows = kon.execute(
            "SELECT dari_status, ke_status, pelaku, catatan, waktu FROM laporan_timeline"
            " WHERE laporan_id = ? ORDER BY id",
            (laporan_id,),
        ).fetchall()
    finally:
        kon.close()
    return [EntriTimeline(b["dari_status"], b["ke_status"], b["pelaku"], b["catatan"], b["waktu"]) for b in rows]


# --- Mengubah ----------------------------------------------------------------------------------


def _cek_syarat(
    laporan: Laporan,
    ke: str,
    *,
    catatan: str,
    tingkat: str | None,
    induk_nomor: str | None,
    foto_sesudah: bytes | None,
) -> int | None:
    """Syarat tambahan per transisi BR-03 (dipanggil setelah pelaku dinyatakan boleh).

    Mengembalikan id laporan induk untuk transisi ke ``digabung``, selain itu ``None``.
    Data kurang/salah → ``TidakValid`` (400); keadaan laporan tidak memungkinkan → ``Konflik`` (409).
    """
    if laporan.status == STATUS_MENUNGGU and ke == STATUS_BELUM and tingkat not in URUTAN_TINGKAT:
        raise TidakValid("Pilih tingkat kerusakan: Kurang Baik atau Rusak.")
    if ke == STATUS_DITOLAK and len(catatan) < MIN_ALASAN:
        raise TidakValid(f"Alasan penolakan wajib diisi (minimal {MIN_ALASAN} karakter).")
    if (
        laporan.status == STATUS_DITOLAK
        and ke == STATUS_MENUNGGU
        and (laporan.diperiksa_oleh != PELAKU_AI or laporan.banding_pada is not None)
    ):
        raise Konflik("Peninjauan hanya bisa diminta sekali, untuk laporan yang ditolak otomatis oleh AI.")
    if ke == STATUS_SELESAI and foto_sesudah is None and pengaturan().wajib_foto_selesai:
        raise TidakValid("Lampirkan foto setelah perbaikan.")
    if ke != STATUS_DIGABUNG:
        return None
    if not induk_nomor:
        raise TidakValid("Pilih laporan induk untuk digabung.")
    if induk_nomor == laporan.nomor:
        raise TidakValid("Laporan tidak bisa digabung ke dirinya sendiri.")
    try:
        induk = ambil_laporan(induk_nomor)
    except TidakDitemukan as e:
        raise TidakValid("Laporan induk tidak ditemukan.") from e
    if induk.status not in STATUS_AKTIF:
        raise Konflik("Laporan induk harus masih aktif.")
    return induk.id


def ubah_status(
    nomor: str,
    ke: str,
    pelaku: str,
    *,
    pengguna_id: int | None = None,
    catatan: str = "",
    tingkat: str | None = None,
    induk_nomor: str | None = None,
    label_akhir: str | None = None,
    foto_sesudah: bytes | None = None,
    hasil_ai_sesudah: dict | None = None,
) -> Laporan:
    """Ubah status menurut BR-03. Pemanggil bertanggung jawab atas otorisasi per pengguna
    (mis. penanganan mengecek wilayah petugas); fungsi ini menegakkan siapa (peran pelaku) boleh apa.
    ``hasil_ai_sesudah`` = hasil pemeriksaan AI atas foto setelah perbaikan (US-31), tampil publik."""
    laporan = ambil_laporan(nomor)
    if pelaku not in TRANSISI.get((laporan.status, ke), set()):
        raise Konflik(f"Status tidak bisa diubah dari {laporan.status} ke {ke}.")
    catatan = catatan.strip()
    induk_id = _cek_syarat(
        laporan, ke, catatan=catatan, tingkat=tingkat, induk_nomor=induk_nomor, foto_sesudah=foto_sesudah
    )
    sesudah_bersih = bersihkan_foto(foto_sesudah) if foto_sesudah is not None else None
    kini = sekarang()
    set_kolom = {"status": ke, "diubah_pada": kini}
    if ke == STATUS_BELUM and laporan.status == STATUS_MENUNGGU:
        set_kolom.update(tingkat=tingkat, diperiksa_oleh=PELAKU_ADMIN, diverifikasi_pada=kini)
    if ke == STATUS_DITOLAK:
        set_kolom.update(diperiksa_oleh=PELAKU_ADMIN)
    if ke == STATUS_MENUNGGU and laporan.status == STATUS_DITOLAK:
        set_kolom.update(banding_pada=kini)
    if ke == STATUS_DIGABUNG:
        set_kolom.update(induk_id=induk_id)
    if ke == STATUS_SEDANG:
        set_kolom.update(mulai_dikerjakan_pada=kini)
    if ke == STATUS_SELESAI:
        set_kolom.update(selesai_pada=kini)
    if label_akhir is not None:
        set_kolom.update(label_akhir=label_akhir)
    with transaksi() as kon:
        kon.execute(
            f"UPDATE laporan SET {', '.join(f'{k} = ?' for k in set_kolom)} WHERE id = ?",  # noqa: S608
            (*set_kolom.values(), laporan.id),
        )
        if sesudah_bersih is not None:
            _simpan_foto(kon, laporan.id, "sesudah", sesudah_bersih, hasil_ai_sesudah)
        if ke == STATUS_DIGABUNG:
            _pindahkan_dukungan(kon, laporan, induk_id)
        _catat(kon, laporan.id, laporan.status, ke, pelaku, pengguna_id, catatan)
    terbitkan(StatusBerubah(laporan.id, laporan.nomor, laporan.status, ke, pelaku, laporan.pelapor_id))
    return ambil_laporan(nomor)


def ubah_tingkat(nomor: str, tingkat: str, pengguna_id: int, alasan: str) -> Laporan:
    if tingkat not in URUTAN_TINGKAT:
        raise TidakValid("Tingkat tidak dikenal.")
    if not alasan.strip():
        raise TidakValid("Alasan wajib diisi.")
    laporan = ambil_laporan(nomor)
    with transaksi() as kon:
        kon.execute(
            "UPDATE laporan SET tingkat = ?, label_akhir = ?, diubah_pada = ? WHERE id = ?",
            (tingkat, tingkat, sekarang(), laporan.id),
        )
        _catat(
            kon,
            laporan.id,
            laporan.status,
            laporan.status,
            PELAKU_ADMIN,
            pengguna_id,
            f"Tingkat dikoreksi dari {laporan.tingkat} ke {tingkat}: {alasan.strip()}",
        )
    return ambil_laporan(nomor)


# --- Dukungan ----------------------------------------------------------------------------------

_POTONG_ID = 500


def tambah_dukungan(laporan_id: int, pengguna_id: int) -> bool:
    """True bila dukungan baru tercatat; False bila pengguna ini sudah pernah mendukung."""
    with transaksi() as kon:
        cur = kon.execute(
            "INSERT OR IGNORE INTO laporan_dukungan (laporan_id, pengguna_id, waktu) VALUES (?, ?, ?)",
            (laporan_id, pengguna_id, sekarang()),
        )
        return cur.rowcount == 1


def jumlah_dukungan(laporan_id: int) -> int:
    kon = koneksi()
    try:
        return kon.execute("SELECT COUNT(*) FROM laporan_dukungan WHERE laporan_id = ?", (laporan_id,)).fetchone()[0]
    finally:
        kon.close()


def jumlah_dukungan_massal(laporan_ids: list[int]) -> dict[int, int]:
    """Jumlah dukungan banyak laporan sekaligus (CR #23, mencegah N+1 di peta). Id tanpa dukungan → 0.

    Satu query ``GROUP BY`` per potongan ``_POTONG_ID`` id, supaya tidak melewati batas variabel SQLite.
    """
    hasil = dict.fromkeys(laporan_ids, 0)
    ids = list(hasil)
    kon = koneksi()
    try:
        for awal in range(0, len(ids), _POTONG_ID):
            bagian = ids[awal : awal + _POTONG_ID]
            tanda = ", ".join("?" * len(bagian))
            baris = kon.execute(
                f"SELECT laporan_id, COUNT(*) FROM laporan_dukungan WHERE laporan_id IN ({tanda}) GROUP BY laporan_id",  # noqa: S608
                bagian,
            )
            hasil.update({laporan_id: n for laporan_id, n in baris})
    finally:
        kon.close()
    return hasil


def _pindahkan_dukungan(kon: sqlite3.Connection, laporan: Laporan, induk_id: int) -> None:
    """Saat ``laporan`` digabung ke induknya: pendukungnya dan pelapornya menjadi pendukung induk.

    Dukungan yang sudah ada di induk tidak ditimpa (waktu lama tetap), dan pelapor induk tidak
    pernah tercatat mendukung laporannya sendiri. Dipanggil di dalam transaksi ``ubah_status``.
    """
    kon.execute(
        "INSERT OR IGNORE INTO laporan_dukungan (laporan_id, pengguna_id, waktu) "
        "SELECT :induk, pengguna_id, waktu FROM laporan_dukungan "
        "WHERE laporan_id = :anak AND pengguna_id IS NOT (SELECT pelapor_id FROM laporan WHERE id = :induk)",
        {"induk": induk_id, "anak": laporan.id},
    )
    if laporan.pelapor_id is not None:
        kon.execute(
            "INSERT OR IGNORE INTO laporan_dukungan (laporan_id, pengguna_id, waktu) "
            "SELECT :induk, :pelapor, :waktu WHERE :pelapor IS NOT (SELECT pelapor_id FROM laporan WHERE id = :induk)",
            {"induk": induk_id, "pelapor": laporan.pelapor_id, "waktu": laporan.dibuat_pada},
        )
    kon.execute("DELETE FROM laporan_dukungan WHERE laporan_id = ?", (laporan.id,))


def pendukung(laporan_id: int) -> list[int]:
    kon = koneksi()
    try:
        rows = kon.execute("SELECT pengguna_id FROM laporan_dukungan WHERE laporan_id = ?", (laporan_id,))
        return [b[0] for b in rows]
    finally:
        kon.close()


# --- Pelanggan kejadian ------------------------------------------------------------------------


def _putus_tautan_pelapor(kejadian: AkunDihapus) -> None:
    with transaksi() as kon:
        kon.execute("UPDATE laporan SET pelapor_id = NULL WHERE pelapor_id = ?", (kejadian.pengguna_id,))
        kon.execute("DELETE FROM laporan_dukungan WHERE pengguna_id = ?", (kejadian.pengguna_id,))


def pasang() -> None:
    """Daftarkan pelanggan kejadian modul ini. Dipanggil sekali oleh main.py."""
    langganan(AkunDihapus, _putus_tautan_pelapor)
