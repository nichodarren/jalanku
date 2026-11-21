// Peta dasar Leaflet + tile OSM + atribusi (NFR-LEG-01). Pemilik: M1; dipakai peta, pelaporan, penanganan.
// Tile diambil lewat server sendiri (/api/tile, core/tile.py) karena di sebagian jaringan tile OSM yang
// diminta langsung dari browser dibalas "Access blocked" (issue #22). Server hanya melayani zoom 10–19
// di kotak DKI Jakarta; BATAS_TILE harus sama dengan BATAS di core/tile.py.

import { PUSAT_JAKARTA } from "/shared/konstanta.js";

const ZOOM_MIN = 10;
const ZOOM_MAKS = 19;
const BATAS_TILE = [
  [-6.5, 106.3],
  [-5.1, 107.2],
];

export function buatPeta(wadah, { zoom = 12, pusat = PUSAT_JAKARTA } = {}) {
  if (!window.L) throw new Error("Pustaka peta belum termuat.");
  const peta = window.L.map(wadah, { zoomControl: true, minZoom: ZOOM_MIN, maxZoom: ZOOM_MAKS }).setView(pusat, zoom);
  window.L.tileLayer("/api/tile/{z}/{x}/{y}.png", {
    minZoom: ZOOM_MIN,
    maxZoom: ZOOM_MAKS,
    bounds: BATAS_TILE, // jangan minta tile di luar wilayah yang dilayani server
    attribution: '&copy; kontributor <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>; batas wilayah &copy; GADM',
  }).addTo(peta);
  return peta;
}
