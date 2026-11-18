// Frontend modul notifikasi. Pemilik: M1. Kontrak data: app/kontrak/openapi.json (/api/docs)
// STUB: halaman penanda. Ganti isi tampil() tanpa mengubah `jalur` (jalur dipakai modul lain sebagai tautan).
import { belumDibuat } from "/shared/ui.js";

export const rute = [
  {
    jalur: "#/kabar",
    judul: "Kabar",
    menu: true,
    peran: ["pelapor", "petugas", "admin"],
    tampil(wadah, param) {
      wadah.append(belumDibuat("Kabar laporanku", "US-25", "M1", ""));
    },
  },
];
