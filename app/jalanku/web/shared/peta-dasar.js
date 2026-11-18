// Peta dasar Leaflet + tile OSM + atribusi (NFR-LEG-01). Pemilik: M1; dipakai peta, pelaporan, penanganan.

import { PUSAT_JAKARTA } from "/shared/konstanta.js";

export function buatPeta(wadah, { zoom = 12, pusat = PUSAT_JAKARTA } = {}) {
  if (!window.L) throw new Error("Pustaka peta belum termuat.");
  const peta = window.L.map(wadah, { zoomControl: true }).setView(pusat, zoom);
  window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; kontributor <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>; batas wilayah &copy; GADM',
  }).addTo(peta);
  return peta;
}
