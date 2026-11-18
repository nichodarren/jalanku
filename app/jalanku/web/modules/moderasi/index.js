// Frontend modul moderasi. Pemilik: M5. Kontrak data: app/kontrak/openapi.json (/api/docs)
// STUB: halaman penanda. Ganti isi tampil() tanpa mengubah `jalur` (jalur dipakai modul lain sebagai tautan).
import { belumDibuat } from "/shared/ui.js";

export const rute = [
  {
    jalur: "#/admin",
    judul: "Antrean",
    menu: true,
    peran: ["admin"],
    tampil(wadah, param) {
      wadah.append(belumDibuat("Antrean Admin", "US-12, US-13, US-14", "M5", "Banding paling atas; tampilkan hasil AI per foto dan kandidat duplikat."));
    },
  },
];
