// Frontend modul pelaporan. Pemilik: M3. Kontrak data: app/kontrak/openapi.json (/api/docs)
// STUB: halaman penanda. Ganti isi tampil() tanpa mengubah `jalur` (jalur dipakai modul lain sebagai tautan).
import { belumDibuat } from "/shared/ui.js";

export const rute = [
  {
    jalur: "#/lapor",
    judul: "Laporkan",
    menu: true,
    peran: null,
    tampil(wadah, param) {
      wadah.append(belumDibuat("Laporkan jalan rusak", "US-03, US-04, US-09", "M3", "Tiga langkah: foto + hasil AI, lokasi (pin), kirim. Pakai /shared/peta-dasar.js untuk pin."));
    },
  },
  {
    jalur: "#/saya",
    judul: "Laporan saya",
    menu: true,
    peran: ["pelapor", "petugas", "admin"],
    tampil(wadah, param) {
      wadah.append(belumDibuat("Laporan saya", "US-11", "M3", ""));
    },
  },
];
