// Frontend modul statistik: #/statistik (US-23 statistik per Sudin, publik). Pemilik: M5.
// Kontrak: GET /api/statistik?hari=  → label_simulasi, periode_hari, persen_diputuskan_ai, instansi[].
// Diport dari jalanku-v0 app/jalanku/web/js/views/statistik.js (karya Yosua), disesuaikan: field skema
// StatistikKeluaran, kartu per Sudin (bukan tabel) agar nyaman di 360 px, pilihan periode 7/30/90 hari,
// label "data uji/simulasi" wajib (BR-04), warna lewat statistik.css (CSP), hanya impor dari /shared/.

import { api } from "/shared/api.js";
import { LABEL_STATUS } from "/shared/konstanta.js";
import { el, kosongkan } from "/shared/ui.js";

const CSS_MODUL = "/modules/statistik/statistik.css";
const PERIODE = [7, 30, 90];
const N_MINIMUM = 5; // BR-04, sama dengan server

function muatCss() {
  if (!document.querySelector(`link[href="${CSS_MODUL}"]`)) {
    document.head.append(el("link", { rel: "stylesheet", href: CSS_MODUL }));
  }
}

function formatJam(jam) {
  if (jam === null || jam === undefined) return null;
  if (jam < 24) return `${jam.toLocaleString("id-ID")} jam`;
  return `${(jam / 24).toLocaleString("id-ID", { maximumFractionDigits: 1 })} hari`;
}

function median(label, jam, n) {
  const teks = formatJam(jam);
  return el(
    "div",
    { class: "median" },
    el("dt", {}, label),
    el("dd", {}, teks ?? "–"),
    el(
      "dd",
      { class: "redup" },
      teks ? `dari ${n} laporan` : `butuh minimal 5 laporan (baru ${n})`,
    ),
  );
}

function kartuInstansi(item) {
  const status = Object.entries(item.jumlah_per_status);
  const total = status.reduce((a, [, n]) => a + n, 0);
  return el(
    "article",
    { class: "kartu-stat", "aria-labelledby": `stat-${item.instansi_id}` },
    el("h2", { id: `stat-${item.instansi_id}` }, item.nama_pendek, el("span", { class: "redup" }, ` · ${total} laporan`)),
    el(
      "dl",
      { class: "angka-status" },
      status.map(([s, n]) =>
        el("div", { class: `status-${s.replaceAll("_", "-")}` }, el("dt", {}, LABEL_STATUS[s] || s), el("dd", {}, String(n))),
      ),
    ),
    el(
      "dl",
      { class: "angka-median" },
      median("Median sampai dikerjakan", item.median_jam_dikerjakan, item.n_dikerjakan),
      median("Median sampai selesai", item.median_jam_selesai, item.n_selesai),
    ),
  );
}

async function halamanStatistik(wadah) {
  muatCss();
  let hari = 30;
  const label = el("p", { class: "label-simulasi", role: "note" });
  const ringkas = el("p", { class: "redup" });
  const daftar = el("div", { class: "daftar-stat", "aria-live": "polite" });

  const chip = (nilai) =>
    el(
      "button",
      {
        type: "button",
        class: "chip",
        "aria-pressed": String(nilai === hari),
        onclick: (e) => {
          hari = nilai;
          for (const b of e.currentTarget.parentElement.querySelectorAll(".chip")) {
            b.setAttribute("aria-pressed", String(b === e.currentTarget));
          }
          muat();
        },
      },
      `${nilai} hari`,
    );

  wadah.append(
    el("h1", {}, "Statistik per Sudin"),
    label,
    el(
      "p",
      { class: "redup" },
      `Waktu dihitung sejak laporan terverifikasi. Median hanya ditampilkan bila ada minimal ${N_MINIMUM} laporan.`,
    ),
    el("fieldset", { class: "grup-chip" }, el("legend", {}, "Periode"), PERIODE.map(chip)),
    ringkas,
    daftar,
  );

  let permintaan = 0;
  async function muat() {
    const ke = ++permintaan;
    let data;
    try {
      data = await api.get(`/api/statistik?hari=${hari}`);
    } catch (galat) {
      if (ke !== permintaan) return;
      kosongkan(daftar);
      ringkas.textContent = "";
      daftar.append(el("p", { class: "galat", role: "alert" }, `Statistik gagal dimuat: ${galat.message}`));
      return;
    }
    if (ke !== permintaan) return;
    label.textContent = data.label_simulasi
      ? "Data uji/simulasi: petugas pemerintah diperankan tim proyek, bukan kinerja nyata instansi."
      : "";
    label.hidden = !data.label_simulasi;
    const ai = data.persen_diputuskan_ai;
    ringkas.textContent =
      `Periode ${data.periode_hari} hari terakhir. ` +
      (ai === null ? "Belum ada laporan baru." : `${ai.toLocaleString("id-ID")}% laporan diputuskan otomatis oleh AI.`);
    kosongkan(daftar);
    for (const item of data.instansi) daftar.append(kartuInstansi(item));
  }
  await muat();
}

export const rute = [
  {
    jalur: "#/statistik",
    judul: "Statistik",
    menu: true,
    peran: null,
    tampil: halamanStatistik,
  },
];
