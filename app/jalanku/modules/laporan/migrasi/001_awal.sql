-- Modul laporan (domain inti). Pemilik: M1.
-- pelapor_id / pengguna_id merujuk akun_pengguna.id TANPA foreign key lintas modul (aturan kepemilikan tabel: README.id.md).

CREATE TABLE laporan (
  id                     INTEGER PRIMARY KEY,
  nomor                  TEXT NOT NULL UNIQUE,                    -- JK-00001
  pelapor_id             INTEGER,                                 -- NULL setelah akun dihapus
  lat                    REAL NOT NULL,
  lon                    REAL NOT NULL,
  akurasi_gps            REAL,
  sumber_lokasi          TEXT NOT NULL CHECK (sumber_lokasi IN ('exif', 'gps', 'manual')),
  kota                   TEXT,
  kecamatan              TEXT,
  instansi_id            TEXT NOT NULL,
  status                 TEXT NOT NULL CHECK (status IN ('menunggu_verifikasi', 'belum_dikerjakan',
                           'sedang_dikerjakan', 'selesai', 'ditolak', 'digabung')),
  tingkat                TEXT CHECK (tingkat IS NULL OR tingkat IN ('kurang_baik', 'rusak')),
  keterangan             TEXT NOT NULL DEFAULT '' CHECK (length(keterangan) <= 280),
  diperiksa_oleh         TEXT CHECK (diperiksa_oleh IS NULL OR diperiksa_oleh IN ('ai', 'admin')),
  keputusan_ai           TEXT CHECK (keputusan_ai IS NULL OR keputusan_ai IN
                           ('terverifikasi', 'ditolak', 'perlu_admin', 'tidak_aktif')),
  versi_model            TEXT,
  label_akhir            TEXT CHECK (label_akhir IS NULL OR label_akhir IN ('baik', 'kurang_baik', 'rusak', 'bukan_jalan')),
  induk_id               INTEGER REFERENCES laporan(id),
  banding_pada           TEXT,
  simulasi               INTEGER NOT NULL DEFAULT 0,              -- 1 = data contoh/uji, wajib dilabeli di UI
  dibuat_pada            TEXT NOT NULL,
  diverifikasi_pada      TEXT,
  mulai_dikerjakan_pada  TEXT,
  selesai_pada           TEXT,
  diubah_pada            TEXT NOT NULL
);
CREATE INDEX laporan_status ON laporan (status);
CREATE INDEX laporan_instansi ON laporan (instansi_id, status);
CREATE INDEX laporan_pelapor ON laporan (pelapor_id);

CREATE TABLE laporan_foto (
  id          INTEGER PRIMARY KEY,
  laporan_id  INTEGER NOT NULL REFERENCES laporan(id) ON DELETE CASCADE,
  jenis       TEXT NOT NULL CHECK (jenis IN ('bukti', 'sesudah')),
  berkas      TEXT NOT NULL,
  ai_json     TEXT,                                               -- hasil AI per foto (bukti)
  dibuat_pada TEXT NOT NULL
);
CREATE INDEX laporan_foto_laporan ON laporan_foto (laporan_id);

CREATE TABLE laporan_timeline (
  id          INTEGER PRIMARY KEY,
  laporan_id  INTEGER NOT NULL REFERENCES laporan(id) ON DELETE CASCADE,
  dari_status TEXT,
  ke_status   TEXT NOT NULL,
  pelaku      TEXT NOT NULL CHECK (pelaku IN ('ai', 'admin', 'petugas', 'pelapor', 'sistem')),
  pengguna_id INTEGER,
  catatan     TEXT NOT NULL DEFAULT '',
  waktu       TEXT NOT NULL,
  hash        TEXT          -- US-32: sha256(hash entri sebelumnya + isi entri); NULL sampai fitur dibuat
);
CREATE INDEX laporan_timeline_laporan ON laporan_timeline (laporan_id);

CREATE TABLE laporan_dukungan (
  laporan_id  INTEGER NOT NULL REFERENCES laporan(id) ON DELETE CASCADE,
  pengguna_id INTEGER NOT NULL,
  waktu       TEXT NOT NULL,
  PRIMARY KEY (laporan_id, pengguna_id)
);
