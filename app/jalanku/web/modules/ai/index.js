// Frontend modul ai. Pemilik: M4. Kontrak data: app/kontrak/openapi.json (/api/docs)
// STUB: halaman penanda. Ganti isi tampil() tanpa mengubah `jalur` (jalur dipakai modul lain sebagai tautan).
import { belumDibuat } from "/shared/ui.js";

export const rute = [
  {
    jalur: "#/admin/ai",
    judul: "Kinerja AI",
    menu: true,
    peran: ["admin"],
    tampil(wadah, param) {
      wadah.append(belumDibuat("Kinerja AI", "US-22", "M4", "Data: GET /api/admin/ai/metrik."));
    },
  },
];
