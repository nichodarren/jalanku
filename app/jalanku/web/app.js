// Kerangka aplikasi: router hash + navigasi. Pemilik: M1.
// Setiap modul frontend ada di /modules/<modul>/index.js dan mengekspor `rute`:
//   export const rute = [{ jalur: "#/peta", judul: "Peta", menu: true, peran: null, tampil(wadah, param) {...} }]
// `peran`: null = semua orang; ["admin"] = hanya peran itu (pengecekan sesungguhnya tetap di server).
// Menambah modul frontend = tambahkan import di DAFTAR_MODUL (perubahan file milik M1, lewat PR).

import { api } from "/shared/api.js";
import { el, kosongkan } from "/shared/ui.js";

import * as akun from "/modules/akun/index.js";
import * as pelaporan from "/modules/pelaporan/index.js";
import * as laporan from "/modules/laporan/index.js";
import * as peta from "/modules/peta/index.js";
import * as moderasi from "/modules/moderasi/index.js";
import * as penanganan from "/modules/penanganan/index.js";
import * as statistik from "/modules/statistik/index.js";
import * as notifikasi from "/modules/notifikasi/index.js";
import * as ai from "/modules/ai/index.js";
import * as wilayah from "/modules/wilayah/index.js";

const DAFTAR_MODUL = [peta, pelaporan, laporan, statistik, notifikasi, moderasi, ai, wilayah, penanganan, akun];
const SEMUA_RUTE = DAFTAR_MODUL.flatMap((m) => m.rute);
const RUTE_AWAL = "#/peta";

export const sesi = { pengguna: null };

async function muatPengguna() {
  try {
    sesi.pengguna = await api.get("/api/akun/saya");
  } catch {
    sesi.pengguna = null;
  }
  const status = document.getElementById("status-akun");
  status.textContent = sesi.pengguna ? `${sesi.pengguna.nama} (${sesi.pengguna.peran})` : "Belum masuk";
}

function bolehLihat(r) {
  return !r.peran || (sesi.pengguna && r.peran.includes(sesi.pengguna.peran));
}

function gambarNavigasi() {
  const nav = document.getElementById("navigasi");
  kosongkan(nav);
  const hash = location.hash || RUTE_AWAL;
  for (const r of SEMUA_RUTE.filter((r) => r.menu && bolehLihat(r))) {
    const aktif = hash.startsWith(r.jalur);
    nav.append(el("a", { href: r.jalur, class: aktif ? "aktif" : "", "aria-current": aktif ? "page" : null }, r.judul));
  }
  // Di layar sempit menu menjadi bar bawah yang bisa digeser: pastikan menu aktif kelihatan.
  nav.querySelector("a.aktif")?.scrollIntoView({ block: "nearest", inline: "nearest" });
}

function cocokkan(hash) {
  // "#/laporan/JK-00001" cocok dengan jalur "#/laporan/:nomor"
  for (const r of SEMUA_RUTE) {
    const pola = r.jalur.split("/");
    const bagian = hash.split("/");
    if (pola.length !== bagian.length) continue;
    const param = {};
    if (pola.every((p, i) => (p.startsWith(":") ? ((param[p.slice(1)] = decodeURIComponent(bagian[i])), true) : p === bagian[i]))) {
      return { r, param };
    }
  }
  return null;
}

async function tampilkan() {
  const hash = location.hash || RUTE_AWAL;
  const wadah = document.getElementById("isi");
  kosongkan(wadah);
  gambarNavigasi();
  const hasil = cocokkan(hash);
  if (!hasil) {
    wadah.append(el("h1", {}, "Halaman tidak ditemukan"), el("p", {}, el("a", { href: RUTE_AWAL }, "Kembali ke peta")));
    return;
  }
  if (!bolehLihat(hasil.r)) {
    wadah.append(el("h1", {}, "Perlu masuk"), el("p", {}, el("a", { href: "#/masuk" }, "Masuk dulu")));
    return;
  }
  document.title = `${hasil.r.judul} · JalanKu`;
  try {
    await hasil.r.tampil(wadah, hasil.param, sesi);
  } catch (galat) {
    wadah.append(el("p", { class: "galat", role: "alert" }, galat.message || String(galat)));
  }
  wadah.focus();
}

window.addEventListener("hashchange", tampilkan);
window.addEventListener("jalanku:akun-berubah", async () => {
  await muatPengguna();
  tampilkan();
});

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("/sw.js").catch(() => {});
}

await muatPengguna();
tampilkan();
