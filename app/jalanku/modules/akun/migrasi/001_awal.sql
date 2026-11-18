-- Modul akun: pengguna, sesi, token verifikasi. Pemilik: M2.
-- JANGAN edit file ini setelah di-merge; buat 002_*.sql untuk perubahan.

CREATE TABLE akun_pengguna (
  id                  INTEGER PRIMARY KEY,
  email               TEXT NOT NULL UNIQUE COLLATE NOCASE,
  nama                TEXT NOT NULL,
  password_hash       TEXT,                       -- argon2id; NULL untuk akun dev
  peran               TEXT NOT NULL DEFAULT 'pelapor' CHECK (peran IN ('pelapor', 'petugas', 'admin')),
  instansi_id         TEXT,                       -- wajib untuk petugas (lihat wilayah_instansi.id)
  terverifikasi       INTEGER NOT NULL DEFAULT 0,
  setuju_privasi_pada TEXT,
  dibuat_pada         TEXT NOT NULL,
  dihapus_pada        TEXT,
  CHECK (peran <> 'petugas' OR instansi_id IS NOT NULL)
);

CREATE TABLE akun_sesi (
  token_hash       TEXT PRIMARY KEY,               -- sha256 dari token di cookie
  pengguna_id      INTEGER NOT NULL REFERENCES akun_pengguna(id) ON DELETE CASCADE,
  dibuat_pada      TEXT NOT NULL,
  kedaluwarsa_pada TEXT NOT NULL
);
CREATE INDEX akun_sesi_pengguna ON akun_sesi (pengguna_id);

CREATE TABLE akun_token (
  token_hash       TEXT PRIMARY KEY,
  pengguna_id      INTEGER NOT NULL REFERENCES akun_pengguna(id) ON DELETE CASCADE,
  jenis            TEXT NOT NULL CHECK (jenis IN ('verifikasi_email')),
  dibuat_pada      TEXT NOT NULL,
  kedaluwarsa_pada TEXT NOT NULL,
  dipakai_pada     TEXT
);
