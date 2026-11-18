// Frontend modul laporan. Pemilik: M1. Kontrak data: app/kontrak/openapi.json (/api/docs)
// STUB: halaman penanda. Ganti isi tampil() tanpa mengubah `jalur` (jalur dipakai modul lain sebagai tautan).
import { belumDibuat } from "/shared/ui.js";

export const rute = [
  {
    jalur: "#/laporan/:nomor",
    judul: "Detail laporan",
    menu: false,
    peran: null,
    tampil(wadah, param) {
      wadah.append(belumDibuat("Detail laporan", "US-17", "M1", "Data: GET /api/laporan/{nomor}. Foto sebelum/sesudah berdampingan, timeline dengan label pelaku."));
    },
  },
];
