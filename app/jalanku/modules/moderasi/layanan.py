from __future__ import annotations

from jalanku.core import Konflik, TidakBerhak, TidakValid, pengaturan
from jalanku.modules.akun import Pengguna
from jalanku.modules.laporan import (
    PELAKU_ADMIN,
    PELAKU_PELAPOR,
    STATUS_AKTIF,
    STATUS_BELUM,
    STATUS_DIGABUNG,
    STATUS_DITOLAK,
    STATUS_MENUNGGU,
    STATUS_SEDANG,
    TINGKAT_KURANG_BAIK,
    TINGKAT_RUSAK,
    ambil_laporan,
    ambil_untuk_penonton,
    cari_aktif_dekat,
    cari_laporan,
    daftar_foto,
    jumlah_dukungan,
    ubah_status,
)
from jalanku.modules.wilayah import ambil_instansi

TINGKAT_SAH = {TINGKAT_KURANG_BAIK, TINGKAT_RUSAK}
MIN_ALASAN = 5  # samakan dengan syarat BR-03 di laporan.ubah_status
STATUS_BISA_DITERUSKAN = (STATUS_BELUM, STATUS_SEDANG)
LABEL_TINGKAT = {TINGKAT_KURANG_BAIK: "Kurang Baik", TINGKAT_RUSAK: "Rusak"}


def antrean() -> list[dict]:
    daftar = cari_laporan(status=STATUS_MENUNGGU)
    daftar_terurut = sorted(
        daftar,
        key=lambda lap: (0 if lap.banding_pada else 1, lap.dibuat_pada, lap.id),
    )
    hasil: list[dict] = []
    for lap in daftar_terurut:
        fotos = [
            {"url": f"/api/foto/{f.id}", "hasil_ai": f.hasil_ai} for f in daftar_foto(lap.id) if f.jenis == "bukti"
        ]
        dekat = cari_aktif_dekat(lap.lat, lap.lon, radius_m=25.0)
        duplikat = [{"nomor": rekan.nomor, "jarak_m": round(jarak, 1)} for rekan, jarak in dekat if rekan.id != lap.id]
        hasil.append(
            {
                "nomor": lap.nomor,
                "dibuat_pada": lap.dibuat_pada,
                "banding": bool(lap.banding_pada),
                "kota": lap.kota,
                "kecamatan": lap.kecamatan,
                "keterangan": lap.keterangan,
                "foto": fotos,
                "duplikat": duplikat,
            }
        )
    return hasil


def verifikasi(nomor: str, tingkat: str, pengguna_id: int) -> dict:
    if tingkat not in TINGKAT_SAH:
        raise TidakValid("Tingkat kerusakan harus kurang_baik atau rusak.")
    lap = ambil_laporan(nomor)
    if lap.status != STATUS_MENUNGGU:
        raise Konflik("Hanya laporan berstatus menunggu_verifikasi yang bisa diverifikasi.")
    hasil = ubah_status(
        nomor,
        STATUS_BELUM,
        PELAKU_ADMIN,
        pengguna_id=pengguna_id,
        tingkat=tingkat,
        label_akhir=tingkat,
        catatan=f"Diverifikasi Admin ({tingkat})",
    )
    return {"nomor": hasil.nomor, "status": hasil.status, "tingkat": hasil.tingkat}


def tolak(nomor: str, alasan: str, pengguna_id: int, label: str | None = None) -> dict:
    alasan_bersih = alasan.strip()
    if len(alasan_bersih) < MIN_ALASAN:
        raise TidakValid(f"Alasan penolakan wajib diisi (minimal {MIN_ALASAN} karakter).")
    lap = ambil_laporan(nomor)
    if lap.status != STATUS_MENUNGGU:
        raise Konflik("Hanya laporan berstatus menunggu_verifikasi yang bisa ditolak.")
    label_bersih = label.strip() if isinstance(label, str) and label.strip() else None
    hasil = ubah_status(
        nomor,
        STATUS_DITOLAK,
        PELAKU_ADMIN,
        pengguna_id=pengguna_id,
        catatan=alasan_bersih,
        label_akhir=label_bersih,
    )
    return {"nomor": hasil.nomor, "status": hasil.status, "tingkat": hasil.tingkat}


def gabung(nomor: str, induk_nomor: str, pengguna_id: int) -> dict:
    target_induk = induk_nomor.strip().upper()
    if not target_induk:
        raise TidakValid("Nomor laporan induk wajib diisi.")
    lap = ambil_laporan(nomor)
    induk = ambil_laporan(target_induk)
    if induk.id == lap.id:
        raise TidakValid("Laporan tidak bisa digabung ke dirinya sendiri.")
    if lap.status not in (STATUS_MENUNGGU, STATUS_BELUM):
        raise Konflik("Laporan tidak bisa digabung dari status saat ini.")
    if induk.status not in STATUS_AKTIF:
        raise Konflik("Laporan induk harus masih aktif.")
    hasil = ubah_status(
        nomor,
        STATUS_DIGABUNG,
        PELAKU_ADMIN,
        pengguna_id=pengguna_id,
        induk_nomor=induk.nomor,
        catatan=f"Digabung ke {induk.nomor}",
    )
    return {"nomor": hasil.nomor, "status": hasil.status, "tingkat": hasil.tingkat}


def banding(nomor: str, pengguna: Pengguna) -> dict:
    """US-13: pelapor meminta Admin meninjau penolakan AI (sekali per laporan).

    Syarat "hanya penolakan AI" dan "sekali" ditegakkan BR-03 di ``laporan.ubah_status``.
    Laporan yang tidak boleh dilihat pengguna (BR-06) dijawab 404 oleh ``ambil_untuk_penonton``.
    """
    lap = ambil_untuk_penonton(nomor, pengguna)
    if lap.pelapor_id != pengguna.id:
        raise TidakBerhak("Hanya pelapor yang bisa meminta peninjauan.")
    if lap.status != STATUS_DITOLAK:
        raise Konflik("Peninjauan hanya bisa diminta untuk laporan yang ditolak.")
    hasil = ubah_status(
        nomor,
        STATUS_MENUNGGU,
        PELAKU_PELAPOR,
        pengguna_id=pengguna.id,
        catatan="Pelapor meminta peninjauan Admin",
    )
    return {"nomor": hasil.nomor, "status": hasil.status, "tingkat": hasil.tingkat}


def paket(nomor: str) -> dict:
    """US-14: ringkasan siap salin untuk kanal resmi instansi tujuan.

    NFR-PRI-01: sengaja tidak menyentuh data pelapor (nama, email, id) sama sekali.
    Hanya laporan terverifikasi yang masih perlu ditangani yang bisa diteruskan.
    """
    lap = ambil_laporan(nomor)
    if lap.status not in STATUS_BISA_DITERUSKAN:
        raise Konflik("Paket penerusan hanya untuk laporan terverifikasi yang belum selesai.")
    instansi = ambil_instansi(lap.instansi_id)
    dasar = pengaturan().url_dasar
    foto = [f"{dasar}/api/foto/{f.id}" for f in daftar_foto(lap.id) if f.jenis == "bukti"]
    koordinat = f"{lap.lat:.6f}, {lap.lon:.6f}"
    tautan_peta = f"https://www.google.com/maps?q={lap.lat:.6f},{lap.lon:.6f}"
    teks = "\n".join(
        [
            f"Laporan jalan rusak {lap.nomor} (via JalanKu)",
            f"Tujuan: {instansi.nama}",
            f"Lokasi: Kec. {lap.kecamatan or '-'}, {lap.kota or '-'}, DKI Jakarta",
            f"Koordinat: {koordinat} ({tautan_peta})",
            f"Tingkat kerusakan: {LABEL_TINGKAT.get(lap.tingkat or '', '-')}",
            f"Didukung oleh {jumlah_dukungan(lap.id)} warga lain",
            f"Keterangan: {lap.keterangan or '-'}",
            f"Foto: {', '.join(foto) if foto else '-'}",
            f"Status publik: {dasar}/#/laporan/{lap.nomor}",
        ]
    )
    return {
        "nomor": lap.nomor,
        "instansi_id": instansi.id,
        "kanal_nama": instansi.kanal_nama,
        "kanal_url": instansi.kanal_url,
        "teks": teks,
    }
