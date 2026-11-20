// Bubble dan cluster laporan di peta (US-15 aktif, US-16 riwayat). Pemilik: M6.
// Diport dari jalanku-v0 app/jalanku/web/js/peta.js (karya Yosua), disesuaikan:
// - warna lewat kelas CSS di peta.css, karena CSP style-src 'self' memblokir atribut style;
// - ikon dan popup dibangun dengan el() / createElementNS, tanpa string HTML;
// - hanya memakai field kontrak TitikPetaKeluaran.

import { LABEL_STATUS, LABEL_TINGKAT } from "/shared/konstanta.js";
import { el } from "/shared/ui.js";

const SVG_NS = "http://www.w3.org/2000/svg";

function svg(tag, atribut = {}, ...anak) {
  const node = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(atribut)) node.setAttribute(k, String(v));
  node.append(...anak);
  return node;
}

// Ikon jalan berlubang (laporan aktif) dan centang (selesai). Garis putih di atas warna bubble.
function ikonLaporan(selesai) {
  const garis = { fill: "none", stroke: "#fff", "stroke-width": 2, "stroke-linecap": "round" };
  const isi = selesai
    ? [svg("path", { ...garis, d: "M6 12.5l4 4 8-9", "stroke-width": 2.6, "stroke-linejoin": "round" })]
    : [
        svg("path", { ...garis, d: "M5 15c2-1 3-4 7-4s5 3 7 4" }),
        svg("path", { ...garis, d: "M12 4v4M8 6l1.5 3M16 6l-1.5 3" }),
        svg("ellipse", { cx: 12, cy: 16, rx: 4.5, ry: 2, fill: "#fff" }),
      ];
  return svg("svg", { viewBox: "0 0 24 24", width: 22, height: 22, "aria-hidden": "true", focusable: "false" }, ...isi);
}

/** Kelas warna satu laporan: selesai = hijau; selain itu menurut tingkat. */
export function kelasWarna(lap) {
  if (lap.status === "selesai") return "selesai";
  return lap.tingkat === "rusak" ? "rusak" : "kurang-baik";
}

export function labelLaporan(lap) {
  const tingkat = LABEL_TINGKAT[lap.tingkat];
  const status = LABEL_STATUS[lap.status] || lap.status;
  return tingkat && lap.status !== "selesai" ? `${tingkat}, ${status}` : status;
}

function ikonBubble(lap) {
  const kelas = ["bubble", kelasWarna(lap)];
  if (lap.status === "sedang_dikerjakan") kelas.push("sedang");
  if (lap.simulasi) kelas.push("simulasi");
  const isi = el("div", { class: kelas.join(" ") }, ikonLaporan(lap.status === "selesai"));
  return window.L.divIcon({ className: "bubble-wrap", html: isi, iconSize: [40, 48], iconAnchor: [20, 46], popupAnchor: [0, -40] });
}

export function markerLaporan(lap) {
  const marker = window.L.marker([lap.lat, lap.lon], {
    icon: ikonBubble(lap),
    keyboard: true,
    title: `${lap.nomor}: ${labelLaporan(lap)}`,
    alt: `${lap.nomor}: ${labelLaporan(lap)}`,
    riseOnHover: true,
  });
  marker.options.jalankuWarna = kelasWarna(lap);
  return marker;
}

/** Isi popup: nomor, tingkat & status, lokasi, dukungan, penanda SIMULASI, tautan detail. */
export function popupLaporan(lap) {
  const selesai = lap.status === "selesai";
  return el(
    "div",
    { class: "popup-laporan" },
    el("p", { class: "popup-nomor" }, lap.nomor, lap.simulasi ? el("span", { class: "lencana-simulasi" }, "SIMULASI") : null),
    el("p", {}, el("span", { class: `lencana ${kelasWarna(lap)}` }, labelLaporan(lap))),
    el("p", { class: "redup" }, [lap.kecamatan ? `Kec. ${lap.kecamatan}` : null, lap.kota].filter(Boolean).join(", ")),
    selesai
      ? null
      : el("p", { class: "redup" }, lap.jumlah_dukungan ? `${lap.jumlah_dukungan} warga mendukung` : "Belum ada dukungan"),
    el("a", { href: `#/laporan/${encodeURIComponent(lap.nomor)}` }, `Lihat detail ${lap.nomor}`),
  );
}

// Cluster berangka; warnanya mengikuti laporan terparah di dalamnya (rusak > kurang baik > selesai).
const URUTAN_PARAH = ["rusak", "kurang-baik", "selesai"];

function ukuranCluster(n) {
  if (n < 10) return ["kecil", 36];
  if (n < 50) return ["menengah", 44];
  return ["besar", 56];
}

export function buatCluster() {
  return window.L.markerClusterGroup({
    showCoverageOnHover: false,
    spiderfyOnMaxZoom: true,
    maxClusterRadius: 56,
    iconCreateFunction(cluster) {
      const anak = cluster.getAllChildMarkers();
      const warna = anak.map((m) => URUTAN_PARAH.indexOf(m.options.jalankuWarna)).reduce((a, b) => Math.min(a, b), 2);
      const [ukuran, d] = ukuranCluster(anak.length);
      const isi = el(
        "div",
        { class: `bubble-cluster ${URUTAN_PARAH[warna]} ${ukuran}`, "aria-label": `${anak.length} laporan` },
        el("span", {}, String(anak.length)),
      );
      return window.L.divIcon({ className: "bubble-wrap", html: isi, iconSize: [d, d] });
    },
  });
}

/** Bubble membesar saat zoom in (seperti pin peta). Lewat CSSOM, bukan atribut style. */
export function aturSkalaBubble(peta, wadah) {
  const atur = () => {
    const z = peta.getZoom();
    const skala = z <= 11 ? 0.7 : z <= 13 ? 0.85 : z <= 15 ? 1 : 1.2;
    wadah.style.setProperty("--skala-bubble", String(skala));
  };
  peta.on("zoomend", atur);
  atur();
}
