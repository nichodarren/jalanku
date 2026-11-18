// Frontend modul akun. Pemilik: M2. Kontrak: /api/akun/* (app/kontrak/openapi.json, /api/docs)
// STUB: form daftar/masuk asli dikerjakan di US-01. Selama itu, di mode dev/test tersedia
// "masuk cepat" sebagai peran apa pun lewat POST /api/dev/masuk (endpoint ini tidak ada di produksi).
import { api } from "/shared/api.js";
import { belumDibuat, el, umumkan } from "/shared/ui.js";

function formMasukDev() {
  const email = el("input", { id: "dev-email", type: "email", value: "warga@contoh.test", required: true });
  const peran = el(
    "select",
    { id: "dev-peran" },
    el("option", { value: "pelapor" }, "Pelapor"),
    el("option", { value: "admin" }, "Admin"),
    el("option", { value: "petugas" }, "Petugas"),
  );
  const instansi = el("input", { id: "dev-instansi", value: "SUDIN_JP", placeholder: "mis. SUDIN_JP (wajib untuk petugas)" });
  const form = el(
    "form",
    { class: "kartu" },
    el("h2", {}, "Masuk cepat (khusus pengembangan)"),
    el("p", { class: "redup" }, "Tidak ada di produksi. Dipakai tim selama login asli (US-01) belum selesai."),
    el("label", { for: "dev-email" }, "Email"),
    email,
    el("label", { for: "dev-peran" }, "Peran"),
    peran,
    el("label", { for: "dev-instansi" }, "Instansi (petugas)"),
    instansi,
    el("p", {}, el("button", { type: "submit" }, "Masuk")),
  );
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    try {
      await api.post("/api/dev/masuk", {
        email: email.value,
        peran: peran.value,
        instansi_id: peran.value === "petugas" ? instansi.value : null,
      });
      umumkan("Berhasil masuk.");
      window.dispatchEvent(new Event("jalanku:akun-berubah"));
    } catch (galat) {
      umumkan(galat.kode === 404 ? "Masuk cepat tidak tersedia di server ini." : galat.message);
    }
  });
  return form;
}

async function keluar() {
  await api.post("/api/akun/keluar");
  window.dispatchEvent(new Event("jalanku:akun-berubah"));
}

export const rute = [
  {
    jalur: "#/masuk",
    judul: "Akun",
    menu: true,
    peran: null,
    tampil(wadah, _param, sesi) {
      if (sesi.pengguna) {
        wadah.append(
          el("section", { class: "kartu" }, el("h1", {}, `Halo, ${sesi.pengguna.nama}`),
            el("p", {}, `Peran: ${sesi.pengguna.peran}`), el("button", { onclick: keluar }, "Keluar")),
        );
        return;
      }
      wadah.append(belumDibuat("Masuk / Daftar", "US-01", "M2", "Email + password + verifikasi email; persetujuan privasi wajib."));
      wadah.append(formMasukDev());
    },
  },
];
