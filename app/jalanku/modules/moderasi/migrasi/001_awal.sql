-- Modul moderasi: catatan koreksi tingkat oleh Admin (FR-MOD-03). Pemilik: M5.

CREATE TABLE moderasi_koreksi (
  id          INTEGER PRIMARY KEY,
  laporan_id  INTEGER NOT NULL,          -- laporan.id (tanpa FK lintas modul)
  admin_id    INTEGER NOT NULL,
  tingkat_lama TEXT,
  tingkat_baru TEXT NOT NULL,
  alasan      TEXT NOT NULL,
  waktu       TEXT NOT NULL
);
CREATE INDEX moderasi_koreksi_laporan ON moderasi_koreksi (laporan_id);
