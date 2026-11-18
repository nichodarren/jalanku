// Frontend modul statistik. Pemilik: M5. Kontrak data: app/kontrak/openapi.json (/api/docs)
// STUB: halaman penanda. Ganti isi tampil() tanpa mengubah `jalur` (jalur dipakai modul lain sebagai tautan).
import { belumDibuat } from "/shared/ui.js";

export const rute = [
  {
    jalur: "#/statistik",
    judul: "Statistik",
    menu: true,
    peran: null,
    tampil(wadah, param) {
      wadah.append(belumDibuat("Statistik per Sudin", "US-23", "M5", "Wajib label 'data uji/simulasi' (BR-04)."));
    },
  },
];
