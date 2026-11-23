// Frontend modul penanganan: #/petugas (US-18 laporan wilayahku, US-19 ubah status + foto). Pemilik: M6.
// Kontrak: GET /api/petugas/laporan?status=  dan  POST /api/petugas/laporan/{nomor}/status (multipart ke, catatan, foto).
// Diport dari jalanku-v0 app/jalanku/web/js/views/petugas.js (karya Yosua), disesuaikan: kartu (bukan tabel)
// agar nyaman di 360 px, form Selesai + foto langsung di kartu, tanpa skor prioritas (US-20 menyusul),
// warna lewat kelas di penanganan.css (CSP style-src 'self'), dan hanya impor dari /shared/.

import { api } from "/shared/api.js";
import { LABEL_STATUS, LABEL_TINGKAT } from "/shared/konstanta.js";
import { buatPeta } from "/shared/peta-dasar.js";
import { el, kosongkan, umumkan } from "/shared/ui.js";

const CSS_MODUL = "/modules/penanganan/penanganan.css";
const FILTER_STATUS = [
  ["", "Semua"],
  ["belum_dikerjakan", "Belum dikerjakan"],
  ["sedang_dikerjakan", "Sedang dikerjakan"],
  ["selesai", "Selesai"],
];

function muatCss() {
  if (!document.querySelector(`link[href="${CSS_MODUL}"]`)) {
    document.head.append(el("link", { rel: "stylesheet", href: CSS_MODUL }));
  }
}

function kelasTingkat(lap) {
  return lap.tingkat === "rusak" ? "rusak" : "kurang-baik";
}

function kelasStatus(status) {
  return { belum_dikerjakan: "belum", sedang_dikerjakan: "dikerjakan", selesai: "selesai" }[status] || "belum";
}

function tanggal(iso) {
  if (!iso) return "-";
  const d = new Date(iso.endsWith("Z") || iso.includes("+") ? iso : `${iso}Z`);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString("id-ID", { day: "numeric", month: "short", year: "numeric" });
}

function ringkasan(semua) {
  const n = (s) => semua.filter((l) => l.status === s).length;
  return el(
    "dl",
    { class: "ringkas-petugas" },
    [
      ["Belum dikerjakan", n("belum_dikerjakan")],
      ["Sedang dikerjakan", n("sedang_dikerjakan")],
      ["Selesai", n("selesai")],
    ].map(([label, nilai]) => el("div", {}, el("dt", {}, label), el("dd", {}, String(nilai)))),
  );
}

async function kirimStatus(nomor, ke, { catatan = "", foto = null } = {}) {
  const fd = new FormData();
  fd.append("ke", ke);
  fd.append("catatan", catatan);
  if (foto) fd.append("foto", foto);
  return api.post(`/api/petugas/laporan/${encodeURIComponent(nomor)}/status`, fd);
}

function formSelesai(lap, setelahBerhasil) {
  const id = `foto-${lap.nomor}`;
  const pesan = el("p", { class: "galat", role: "alert", hidden: true });
  const inputFoto = el("input", { id, type: "file", name: "foto", accept: "image/*", capture: "environment" });
  const inputCatatan = el("textarea", { id: `catatan-${lap.nomor}`, name: "catatan", rows: "2", maxlength: "200" });
  const tombol = el("button", { type: "submit", class: "tombol utama" }, "Kirim, tandai Selesai");
  const form = el(
    "form",
    {
      class: "form-selesai",
      onsubmit: async (e) => {
        e.preventDefault();
        pesan.hidden = true;
        tombol.disabled = true;
        try {
          await kirimStatus(lap.nomor, "selesai", { catatan: inputCatatan.value, foto: inputFoto.files[0] || null });
          umumkan(`${lap.nomor} ditandai Selesai dan pindah ke peta riwayat.`);
          setelahBerhasil();
        } catch (galat) {
          pesan.textContent = galat.message;
          pesan.hidden = false;
          tombol.disabled = false;
        }
      },
    },
    el("label", { for: id }, "Foto setelah perbaikan"),
    inputFoto,
    el("label", { for: `catatan-${lap.nomor}` }, "Catatan (opsional, maks. 200 karakter)"),
    inputCatatan,
    pesan,
    el(
      "div",
      { class: "baris-tombol" },
      tombol,
      el("button", { type: "button", class: "tombol", onclick: () => form.remove() }, "Batal"),
    ),
  );
  return form;
}

function kartuLaporan(lap, muatUlang) {
  const aksi = el("div", { class: "baris-tombol" });
  const kartu = el(
    "article",
    { class: "kartu-petugas", id: `kartu-${lap.nomor}`, tabindex: "-1", "aria-labelledby": `judul-${lap.nomor}` },
    el(
      "h2",
      { id: `judul-${lap.nomor}` },
      el("a", { href: `#/laporan/${encodeURIComponent(lap.nomor)}` }, lap.nomor),
      " ",
      el("span", { class: `lencana-p ${kelasTingkat(lap)}` }, LABEL_TINGKAT[lap.tingkat] || "-"),
      " ",
      el("span", { class: `lencana-p ${kelasStatus(lap.status)}` }, LABEL_STATUS[lap.status] || lap.status),
    ),
    el("p", { class: "redup" }, [lap.kecamatan ? `Kec. ${lap.kecamatan}` : null, lap.kota].filter(Boolean).join(", ")),
    el(
      "p",
      { class: "redup" },
      `${lap.jumlah_dukungan ? `${lap.jumlah_dukungan} warga mendukung` : "Belum ada dukungan"}, terverifikasi ${tanggal(lap.diverifikasi_pada)}`,
    ),
    aksi,
  );

  const bukaFormSelesai = () => {
    if (kartu.querySelector(".form-selesai")) return;
    const form = formSelesai(lap, muatUlang);
    kartu.append(form);
    form.querySelector("input")?.focus();
  };

  if (lap.status === "belum_dikerjakan") {
    aksi.append(
      el(
        "button",
        {
          type: "button",
          class: "tombol utama",
          onclick: async (e) => {
            e.currentTarget.disabled = true;
            try {
              await kirimStatus(lap.nomor, "sedang_dikerjakan");
              umumkan(`${lap.nomor} mulai dikerjakan.`);
              muatUlang();
            } catch (galat) {
              umumkan(galat.message);
              e.currentTarget.disabled = false;
            }
          },
        },
        "Mulai dikerjakan",
      ),
    );
  }
  if (lap.status !== "selesai") {
    aksi.append(el("button", { type: "button", class: "tombol", onclick: bukaFormSelesai }, "Tandai selesai"));
  }
  return kartu;
}

function titikLaporan(lap) {
  // circleMarker (SVG) + kelas CSS: tanpa atribut style, aman untuk CSP.
  return window.L.circleMarker([lap.lat, lap.lon], {
    radius: 9,
    className: `titik-petugas ${lap.status === "selesai" ? "selesai" : kelasTingkat(lap)} ${kelasStatus(lap.status)}`,
  });
}

async function halamanPetugas(wadah, _param, sesi) {
  muatCss();
  let filter = "";
  const instansi = sesi?.pengguna?.instansi_id;
  const wadahRingkas = el("div", { "aria-live": "polite" });
  const daftar = el("div", { class: "daftar-petugas" });
  const kanvas = el("div", { class: "peta peta-petugas", role: "region", "aria-label": "Peta laporan di wilayah instansimu" });

  const chip = ([nilai, label]) =>
    el(
      "button",
      {
        type: "button",
        class: "chip",
        "aria-pressed": String(nilai === filter),
        onclick: (e) => {
          filter = nilai;
          for (const b of e.currentTarget.parentElement.querySelectorAll(".chip")) {
            b.setAttribute("aria-pressed", String(b === e.currentTarget));
          }
          muat();
        },
      },
      label,
    );

  wadah.append(
    el("h1", {}, "Laporan wilayahku"),
    el("p", { class: "redup" }, instansi ? `Instansi: ${instansi}. ` : "", "Hanya laporan yang sudah terverifikasi di wilayahmu yang tampil."),
    wadahRingkas,
    el("fieldset", { class: "grup-chip" }, el("legend", {}, "Status"), FILTER_STATUS.map(chip)),
    kanvas,
    daftar,
  );

  const peta = buatPeta(kanvas);
  window.addEventListener(
    "hashchange",
    () => {
      peta.stop();
      peta.remove();
    },
    { once: true },
  );
  const lapisan = window.L.featureGroup().addTo(peta);

  let permintaan = 0;
  async function muat() {
    const ke = ++permintaan;
    let semua;
    try {
      semua = await api.get("/api/petugas/laporan");
    } catch (galat) {
      if (ke !== permintaan) return;
      // Jangan tampilkan daftar/titik lama yang mungkin sudah tidak benar (pelajaran review PR #20).
      lapisan.clearLayers();
      kosongkan(daftar);
      kosongkan(wadahRingkas);
      daftar.append(el("p", { class: "galat", role: "alert" }, `Daftar gagal dimuat: ${galat.message}`));
      umumkan(galat.message);
      return;
    }
    if (ke !== permintaan) return;
    const tampil = filter ? semua.filter((l) => l.status === filter) : semua;
    kosongkan(wadahRingkas);
    wadahRingkas.append(ringkasan(semua));
    lapisan.clearLayers();
    kosongkan(daftar);
    for (const lap of tampil) {
      titikLaporan(lap)
        .on("click", () => {
          const kartu = document.getElementById(`kartu-${lap.nomor}`);
          kartu?.scrollIntoView({ block: "center" });
          kartu?.focus({ preventScroll: true });
        })
        .bindTooltip(`${lap.nomor}: ${LABEL_STATUS[lap.status] || lap.status}`)
        .addTo(lapisan);
      daftar.append(kartuLaporan(lap, muat));
    }
    if (!tampil.length) {
      const kosong = filter ? "Tidak ada laporan untuk filter ini." : "Belum ada laporan terverifikasi di wilayahmu.";
      daftar.append(el("p", { class: "redup" }, kosong));
    }
    if (tampil.length) peta.fitBounds(lapisan.getBounds(), { maxZoom: 15, padding: [30, 30] });
  }
  await muat();
}

export const rute = [
  {
    jalur: "#/petugas",
    judul: "Dashboard petugas",
    menu: true,
    peran: ["petugas"],
    tampil: halamanPetugas,
  },
];
