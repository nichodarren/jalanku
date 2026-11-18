// Frontend modul peta. Pemilik: M6. Kontrak data: GET /api/peta?mode=aktif|riwayat (app/kontrak/openapi.json, /api/docs)
// STUB: peta dasar tampil (memastikan Leaflet & tile jalan); bubble + cluster dikerjakan di US-15/US-16.
import { buatPeta } from "/shared/peta-dasar.js";
import { belumDibuat, el } from "/shared/ui.js";

function halamanPeta(mode) {
  return (wadah) => {
    wadah.append(
      belumDibuat(
        mode === "aktif" ? "Peta laporan aktif" : "Peta riwayat",
        mode === "aktif" ? "US-15" : "US-16",
        "M6",
        "Bubble berkelompok (Leaflet.markercluster), warna per tingkat, ukuran mengikuti zoom.",
      ),
    );
    const kanvas = el("div", { class: "peta", id: "peta-utama", role: "region", "aria-label": "Peta Jakarta" });
    wadah.append(kanvas);
    buatPeta(kanvas);
  };
}

export const rute = [
  { jalur: "#/peta", judul: "Peta", menu: true, peran: null, tampil: halamanPeta("aktif") },
  { jalur: "#/riwayat", judul: "Riwayat", menu: true, peran: null, tampil: halamanPeta("riwayat") },
];
