// Frontend modul wilayah. Pemilik: M2. Kontrak data: app/kontrak/openapi.json (/api/docs)
// STUB: halaman penanda. Ganti isi tampil() tanpa mengubah `jalur` (jalur dipakai modul lain sebagai tautan).
import { belumDibuat } from "/shared/ui.js";

export const rute = [
  {
    jalur: "#/admin/instansi",
    judul: "Instansi",
    menu: true,
    peran: ["admin"],
    tampil(wadah, param) {
      wadah.append(belumDibuat("Kanal resmi instansi", "US-26", "M2", "Data: GET /api/instansi, PATCH /api/admin/instansi/{id}."));
    },
  },
];
