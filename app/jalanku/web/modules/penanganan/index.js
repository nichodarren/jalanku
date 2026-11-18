// Frontend modul penanganan. Pemilik: M6. Kontrak data: app/kontrak/openapi.json (/api/docs)
// STUB: halaman penanda. Ganti isi tampil() tanpa mengubah `jalur` (jalur dipakai modul lain sebagai tautan).
import { belumDibuat } from "/shared/ui.js";

export const rute = [
  {
    jalur: "#/petugas",
    judul: "Dashboard petugas",
    menu: true,
    peran: ["petugas"],
    tampil(wadah, param) {
      wadah.append(belumDibuat("Laporan wilayahku", "US-18, US-19, US-20", "M6", "Peta + daftar; Selesai wajib foto (BR-08)."));
    },
  },
];
