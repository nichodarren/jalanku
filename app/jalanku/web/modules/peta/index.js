// Frontend modul peta: #/peta (US-15 laporan aktif) dan #/riwayat (US-16 laporan selesai). Pemilik: M6.
// Kontrak data: GET /api/peta?mode=aktif|riwayat&kota=&tingkat= (list TitikPetaKeluaran), GET /api/wilayah.
// Diport dari jalanku-v0 app/jalanku/web/js/views/peta.js (karya Yosua), disesuaikan ke router & kontrak repo ini.

import { api } from "/shared/api.js";
import { LABEL_TINGKAT } from "/shared/konstanta.js";
import { buatPeta } from "/shared/peta-dasar.js";
import { el, umumkan } from "/shared/ui.js";
import { aturSkalaBubble, buatCluster, markerLaporan, popupLaporan } from "./bubble.js";

// Lima kota administrasi daratan, sama dengan wilayah.KOTA di backend.
const KOTA = ["Jakarta Pusat", "Jakarta Utara", "Jakarta Barat", "Jakarta Selatan", "Jakarta Timur"];
const CSS_MODUL = "/modules/peta/peta.css";

function muatCss() {
  if (!document.querySelector(`link[href="${CSS_MODUL}"]`)) {
    document.head.append(el("link", { rel: "stylesheet", href: CSS_MODUL }));
  }
}

function tabMode(mode) {
  const tab = (jalur, label, aktif) =>
    el("a", { href: jalur, class: aktif ? "tab-mode aktif" : "tab-mode", "aria-current": aktif ? "page" : null }, label);
  return el(
    "nav",
    { class: "pilih-mode", "aria-label": "Jenis peta" },
    tab("#/peta", "Laporan aktif", mode === "aktif"),
    tab("#/riwayat", "Riwayat selesai", mode === "riwayat"),
  );
}

function grupChip(judul, opsi, terpilih, berubah) {
  return el(
    "fieldset",
    { class: "grup-chip" },
    el("legend", {}, judul),
    opsi.map(([nilai, label]) =>
      el(
        "button",
        {
          type: "button",
          class: "chip",
          "aria-pressed": "false",
          onclick: (e) => {
            const tombol = e.currentTarget;
            const nyala = tombol.getAttribute("aria-pressed") !== "true";
            tombol.setAttribute("aria-pressed", String(nyala));
            if (nyala) terpilih.add(nilai);
            else terpilih.delete(nilai);
            berubah();
          },
        },
        label,
      ),
    ),
  );
}

function legenda(mode) {
  const item = (kelas, label) => el("li", {}, el("span", { class: `tanda ${kelas}`, "aria-hidden": "true" }), label);
  const isi =
    mode === "aktif"
      ? [item("rusak", "Rusak"), item("kurang-baik", "Kurang Baik"), item("sedang", "Sedang Dikerjakan (garis putus biru)")]
      : [item("selesai", "Selesai diperbaiki")];
  return el("ul", { class: "legenda-peta", "aria-label": "Legenda" }, isi, item("simulasi", "Data SIMULASI (garis putus abu)"));
}

async function tambahBatasKecamatan(peta) {
  try {
    const geojson = await api.get("/api/wilayah");
    window.L.geoJSON(geojson, { className: "batas-kecamatan", interactive: false, fill: false, weight: 1 }).addTo(peta);
  } catch {
    // Data batas belum tersedia (mis. 503): peta tetap dipakai tanpa garis batas.
  }
}

function halamanPeta(mode) {
  return async (wadah) => {
    muatCss();
    const filter = { kota: new Set(), tingkat: new Set() };
    const ringkasan = el("p", { class: "ringkasan-peta", "aria-live": "polite" }, "Memuat laporan...");
    const catatanSimulasi = el(
      "p",
      { class: "catatan-simulasi", hidden: true },
      "Sebagian titik adalah data SIMULASI untuk pengembangan, bukan laporan warga nyata.",
    );
    const kanvas = el("div", {
      class: "peta peta-laporan",
      id: "peta-utama",
      role: "region",
      "aria-label": mode === "aktif" ? "Peta laporan jalan rusak yang aktif" : "Peta laporan yang sudah diperbaiki",
    });

    let muat = () => {};
    const panelFilter = el(
      "details",
      { class: "panel-filter" },
      el("summary", {}, "Filter"),
      grupChip("Wilayah", KOTA.map((k) => [k, k]), filter.kota, () => muat()),
      grupChip("Tingkat kerusakan", Object.entries(LABEL_TINGKAT), filter.tingkat, () => muat()),
      el("p", { class: "redup" }, "Hanya laporan yang sudah terverifikasi (oleh AI atau Admin) yang tampil."),
    );

    wadah.append(
      el("h1", {}, mode === "aktif" ? "Peta laporan aktif" : "Peta riwayat perbaikan"),
      tabMode(mode),
      panelFilter,
      ringkasan,
      catatanSimulasi,
      kanvas,
      legenda(mode),
    );

    const peta = buatPeta(kanvas);
    aturSkalaBubble(peta, kanvas);
    window.addEventListener(
      "hashchange",
      () => {
        peta.stop();
        peta.remove();
      },
      { once: true },
    );
    const cluster = buatCluster().addTo(peta);
    tambahBatasKecamatan(peta);

    let permintaan = 0;
    muat = async () => {
      const ke = ++permintaan;
      const q = new URLSearchParams({ mode });
      if (filter.kota.size) q.set("kota", [...filter.kota].join(","));
      if (filter.tingkat.size) q.set("tingkat", [...filter.tingkat].join(","));
      let data;
      try {
        data = await api.get(`/api/peta?${q}`);
      } catch (galat) {
        if (ke !== permintaan) return;
        // Kosongkan titik lama supaya peta tidak menampilkan hasil filter sebelumnya (review PR #20).
        cluster.clearLayers();
        catatanSimulasi.hidden = true;
        ringkasan.textContent = `Peta gagal dimuat: ${galat.message}. Coba ubah filter atau muat ulang halaman.`;
        umumkan(galat.message);
        return;
      }
      if (ke !== permintaan) return; // abaikan jawaban lama bila filter sudah berubah lagi
      cluster.clearLayers();
      cluster.addLayers(data.map((lap) => markerLaporan(lap).bindPopup(() => popupLaporan(lap), { maxWidth: 260 })));
      const nRusak = data.filter((l) => l.tingkat === "rusak").length;
      ringkasan.textContent =
        mode === "aktif"
          ? `${data.length} laporan aktif${data.length ? `, ${nRusak} rusak` : ""}`
          : `${data.length} laporan sudah diperbaiki`;
      catatanSimulasi.hidden = !data.some((l) => l.simulasi);
    };
    await muat();
  };
}

export const rute = [
  { jalur: "#/peta", judul: "Peta", menu: true, peran: null, tampil: halamanPeta("aktif") },
  { jalur: "#/riwayat", judul: "Riwayat", menu: true, peran: null, tampil: halamanPeta("riwayat") },
];
