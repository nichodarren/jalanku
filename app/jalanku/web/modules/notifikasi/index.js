// Frontend modul notifikasi: halaman #/kabar (US-25). Pemilik: M1.
// Kontrak data: GET /api/notifikasi, POST /api/notifikasi/{id}/dibaca, GET/PUT /api/notifikasi/pengaturan.
// Jalur rute dipakai modul lain sebagai tautan: jangan diubah.

import { api } from "/shared/api.js";
import { el, umumkan } from "/shared/ui.js";

const CSS_MODUL = "/modules/notifikasi/notifikasi.css";
const FORMAT_WAKTU = new Intl.DateTimeFormat("id-ID", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Jakarta" });

function muatCss() {
  if (!document.querySelector(`link[href="${CSS_MODUL}"]`)) {
    document.head.append(el("link", { rel: "stylesheet", href: CSS_MODUL }));
  }
}

function waktu(iso) {
  const t = new Date(iso);
  return Number.isNaN(t.getTime()) ? "" : FORMAT_WAKTU.format(t);
}

function itemKabar(k) {
  const tandai = () => {
    if (k.dibaca) return;
    // Tandai dibaca sambil pindah ke detail; kegagalan tidak menghalangi navigasi.
    api.post(`/api/notifikasi/${k.id}/dibaca`).catch(() => {});
  };
  return el(
    "li",
    { class: k.dibaca ? "kabar" : "kabar baru" },
    el(
      "a",
      { href: `#/laporan/${encodeURIComponent(k.nomor)}`, onclick: tandai },
      k.dibaca ? null : el("span", { class: "kabar-titik", "aria-hidden": "true" }),
      el("span", { class: "kabar-pesan" }, k.pesan),
      el("span", { class: "redup" }, `${k.dibaca ? "" : "Belum dibaca · "}${waktu(k.waktu)}`),
    ),
  );
}

function sakelar(awal) {
  const kotak = el("input", { type: "checkbox", id: "kabar-aktif", checked: awal });
  kotak.addEventListener("change", async () => {
    kotak.disabled = true;
    try {
      const r = await api.put("/api/notifikasi/pengaturan", { aktif: kotak.checked });
      kotak.checked = r.aktif;
      umumkan(r.aktif ? "Notifikasi dinyalakan." : "Notifikasi dimatikan.");
    } catch (galat) {
      kotak.checked = !kotak.checked;
      umumkan(galat.message);
    } finally {
      kotak.disabled = false;
    }
  });
  return el("label", { class: "kabar-sakelar", for: "kabar-aktif" }, kotak, " Kabari aku saat status laporanku berubah");
}

async function tampilKabar(wadah) {
  muatCss();
  let kabar;
  let aktif;
  try {
    [kabar, { aktif }] = await Promise.all([api.get("/api/notifikasi"), api.get("/api/notifikasi/pengaturan")]);
  } catch (galat) {
    wadah.append(el("h1", {}, "Kabar laporanku"), el("p", { class: "galat", role: "alert" }, galat.message));
    return;
  }
  const belum = kabar.filter((k) => !k.dibaca).length;
  wadah.append(
    el("h1", {}, "Kabar laporanku"),
    el("section", { class: "kartu" }, sakelar(aktif)),
    el("p", { class: "redup", "aria-live": "polite" }, kabar.length ? `${belum} kabar belum dibaca` : ""),
    kabar.length
      ? el("ul", { class: "daftar-kabar" }, kabar.map(itemKabar))
      : el(
          "section",
          { class: "kartu" },
          el("p", {}, "Belum ada kabar."),
          el("p", { class: "redup" }, "Kabar muncul saat laporan yang kamu buat atau dukung berubah status."),
        ),
  );
}

export const rute = [
  {
    jalur: "#/kabar",
    judul: "Kabar",
    menu: true,
    peran: ["pelapor", "petugas", "admin"],
    tampil: tampilKabar,
  },
];
