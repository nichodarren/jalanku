-- Modul wilayah: data instansi (Dinas + 5 Sudin Bina Marga). Pemilik: M2.
-- Kanal resmi bisa diubah Admin (FR-WIL-03); nilai awal dari jalanku-v0 (instansi.json, 18 Nov 2026).

CREATE TABLE wilayah_instansi (
  id           TEXT PRIMARY KEY,
  nama         TEXT NOT NULL,
  nama_pendek  TEXT NOT NULL,
  kota         TEXT,              -- NULL = Dinas provinsi (semua wilayah, BR-01 d)
  kanal_nama   TEXT NOT NULL,
  kanal_url    TEXT NOT NULL CHECK (kanal_url LIKE 'http://%' OR kanal_url LIKE 'https://%'),
  diubah_pada  TEXT
);

INSERT INTO wilayah_instansi (id, nama, nama_pendek, kota, kanal_nama, kanal_url) VALUES
  ('DINAS_BM', 'Dinas Bina Marga Provinsi DKI Jakarta', 'Dinas Bina Marga DKI', NULL,
   'JAKI (Jakarta Kini) atau Posko Bina Marga 021-3844444', 'https://jaki.jakarta.go.id/'),
  ('SUDIN_JP', 'Suku Dinas Bina Marga Kota Administrasi Jakarta Pusat', 'Sudin Bina Marga Jakarta Pusat',
   'Jakarta Pusat', 'JAKI (Jakarta Kini)', 'https://jaki.jakarta.go.id/'),
  ('SUDIN_JU', 'Suku Dinas Bina Marga Kota Administrasi Jakarta Utara', 'Sudin Bina Marga Jakarta Utara',
   'Jakarta Utara', 'JAKI (Jakarta Kini)', 'https://jaki.jakarta.go.id/'),
  ('SUDIN_JB', 'Suku Dinas Bina Marga Kota Administrasi Jakarta Barat', 'Sudin Bina Marga Jakarta Barat',
   'Jakarta Barat', 'JAKI (Jakarta Kini)', 'https://jaki.jakarta.go.id/'),
  ('SUDIN_JS', 'Suku Dinas Bina Marga Kota Administrasi Jakarta Selatan', 'Sudin Bina Marga Jakarta Selatan',
   'Jakarta Selatan', 'JAKI (Jakarta Kini)', 'https://jaki.jakarta.go.id/'),
  ('SUDIN_JT', 'Suku Dinas Bina Marga Kota Administrasi Jakarta Timur', 'Sudin Bina Marga Jakarta Timur',
   'Jakarta Timur', 'JAKI (Jakarta Kini)', 'https://jaki.jakarta.go.id/');
