-- Modul notifikasi: kabar in-app (FR-NTF-01). Pemilik: M1.

CREATE TABLE notifikasi_kabar (
  id          INTEGER PRIMARY KEY,
  pengguna_id INTEGER NOT NULL,
  nomor       TEXT NOT NULL,
  pesan       TEXT NOT NULL,
  dibaca      INTEGER NOT NULL DEFAULT 0,
  waktu       TEXT NOT NULL
);
CREATE INDEX notifikasi_kabar_pengguna ON notifikasi_kabar (pengguna_id, dibaca);

CREATE TABLE notifikasi_pengaturan (
  pengguna_id INTEGER PRIMARY KEY,
  aktif       INTEGER NOT NULL DEFAULT 1
);
