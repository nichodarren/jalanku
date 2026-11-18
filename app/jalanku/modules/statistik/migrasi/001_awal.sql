-- Modul statistik: kejadian anonim untuk metrik hipotesis A3 (FR-STAT-02). Pemilik: M5.
-- TIDAK menyimpan identitas pengguna: hanya penanda apakah pembuka adalah pelapornya sendiri.

CREATE TABLE statistik_kejadian (
  id           INTEGER PRIMARY KEY,
  jenis        TEXT NOT NULL CHECK (jenis IN ('buka_status', 'laporan_dibuat')),
  laporan_id   INTEGER NOT NULL,
  oleh_pelapor INTEGER NOT NULL DEFAULT 0,
  waktu        TEXT NOT NULL
);
CREATE INDEX statistik_kejadian_jenis ON statistik_kejadian (jenis, waktu);
