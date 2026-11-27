// Frontend modul moderasi: #/admin (US-12 antrean + verifikasi/tolak/gabung, US-13 banding di atas,
// US-14 paket penerusan, US-21 koreksi tingkat). Pemilik: M5. Kontrak: GET /api/admin/antrean,
// POST /api/admin/laporan/{nomor}/verifikasi|tolak|gabung|tingkat, GET /api/admin/laporan/{nomor}/paket.
// Diport dari jalanku-v0 app/jalanku/web/js/views/admin.js (tab Antrean, karya Yosua), disesuaikan:
// field skema ItemAntreanKeluaran, form tolak langsung di kartu (bukan pindah ke detail), paket
// penerusan tampil setelah verifikasi + bisa diambil per nomor, warna lewat moderasi.css (CSP),
// dan hanya impor dari /shared/. Tab Kinerja AI (M4) & Instansi (Should) tidak ikut diport.

import { api } from "/shared/api.js";
import { LABEL_TINGKAT } from "/shared/konstanta.js";
import { el, kosongkan, umumkan } from "/shared/ui.js";

const CSS_MODUL = "/modules/moderasi/moderasi.css";
const MIN_ALASAN = 5; // BR-03: sama dengan laporan.ubah_status
const LABEL_KELAS = { baik: "Baik", kurang_baik: "Kurang Baik", rusak: "Rusak" };
const LABEL_KEPUTUSAN = { terima: "diterima", tolak: "ditolak", admin: "perlu Admin" };

function muatCss() {
  if (!document.querySelector(`link[href="${CSS_MODUL}"]`)) {
    document.head.append(el("link", { rel: "stylesheet", href: CSS_MODUL }));
  }
}

function tanggal(iso) {
  if (!iso) return "-";
  const d = new Date(iso.endsWith("Z") || iso.includes("+") ? iso : `${iso}Z`);
  return Number.isNaN(d.getTime())
    ? iso
    : d.toLocaleString("id-ID", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
}

function persen(nilai) {
  return typeof nilai === "number" ? `${Math.round(nilai * 100)}%` : "-";
}

function ringkasAi(hasil) {
  if (!hasil) return "AI tidak menilai foto ini.";
  if (!hasil.kelas) return hasil.alasan || "Model AI tidak aktif.";
  const kelas = LABEL_KELAS[hasil.kelas] || hasil.kelas;
  const keputusan = LABEL_KEPUTUSAN[hasil.keputusan] || hasil.keputusan || "-";
  return `AI: ${kelas} (yakin ${persen(hasil.confidence)}, mirip jalan ${persen(hasil.kemiripan)}), ${keputusan}.`;
}

/** Panel paket penerusan (US-14): teks siap salin + tautan kanal resmi, tanpa identitas pelapor. */
function panelPaket(paket) {
  const id = `paket-${paket.nomor}`;
  const teks = el("textarea", { id, class: "teks-paket", readonly: true, rows: "9" }, paket.teks);
  return el(
    "section",
    { class: "kartu paket", "aria-labelledby": `${id}-judul` },
    el("h2", { id: `${id}-judul` }, `Paket penerusan ${paket.nomor}`),
    el(
      "p",
      {},
      "Kirim ringkasan ini ke kanal resmi ",
      el("a", { href: paket.kanal_url, target: "_blank", rel: "noopener noreferrer" }, paket.kanal_nama),
      ` (${paket.instansi_id}). Identitas pelapor tidak disertakan.`,
    ),
    el("label", { for: id }, "Ringkasan"),
    teks,
    el(
      "div",
      { class: "baris-tombol" },
      el(
        "button",
        {
          type: "button",
          class: "tombol utama",
          onclick: async () => {
            try {
              await navigator.clipboard.writeText(paket.teks);
              umumkan("Paket disalin.");
            } catch {
              teks.select();
              umumkan("Salin manual: teks sudah dipilih.");
            }
          },
        },
        "Salin paket",
      ),
    ),
  );
}

async function tampilkanPaket(wadahPaket, nomor) {
  const paket = await api.get(`/api/admin/laporan/${encodeURIComponent(nomor)}/paket`);
  kosongkan(wadahPaket);
  wadahPaket.append(panelPaket(paket));
  wadahPaket.querySelector("h2")?.setAttribute("tabindex", "-1");
  wadahPaket.querySelector("h2")?.focus();
}

function formTolak(item, jalankan) {
  const id = `alasan-${item.nomor}`;
  const alasan = el("textarea", {
    id,
    name: "alasan",
    rows: "2",
    required: true,
    minlength: "5",
    maxlength: "200",
  });
  const label = el(
    "select",
    { id: `label-${item.nomor}`, name: "label" },
    el("option", { value: "" }, "Tidak perlu label"),
    el("option", { value: "bukan_jalan" }, "Bukan foto jalan"),
    el("option", { value: "baik" }, "Jalan tampak baik"),
  );
  const tombol = el("button", { type: "submit", class: "tombol bahaya" }, "Tolak laporan");
  return el(
    "form",
    {
      class: "form-tolak",
      onsubmit: (e) => {
        e.preventDefault();
        const isi = alasan.value.trim();
        if (isi.length < MIN_ALASAN) {
          alasan.setCustomValidity(`Alasan minimal ${MIN_ALASAN} karakter.`);
          alasan.reportValidity();
          return;
        }
        alasan.setCustomValidity("");
        jalankan(tombol, () =>
          api.post(`/api/admin/laporan/${encodeURIComponent(item.nomor)}/tolak`, {
            alasan: isi,
            label: label.value || null,
          }),
        );
      },
    },
    el("label", { for: id }, `Alasan penolakan (wajib, ${MIN_ALASAN}–200 karakter, terlihat oleh pelapor)`),
    alasan,
    el("label", { for: `label-${item.nomor}` }, "Label untuk data latih AI (opsional)"),
    label,
    el("div", { class: "baris-tombol" }, tombol),
  );
}

function kartuAntrean(item, { muatUlang, wadahPaket }) {
  const pesan = el("p", { class: "galat", role: "alert", hidden: true });
  const tombolKartu = [];

  async function jalankan(tombol, aksi, setelah) {
    pesan.hidden = true;
    for (const b of tombolKartu) b.disabled = true;
    tombol.disabled = true;
    try {
      const hasil = await aksi();
      umumkan(`${item.nomor}: ${hasil.status.replaceAll("_", " ")}.`);
      if (setelah) await setelah(hasil);
      await muatUlang();
    } catch (galat) {
      pesan.textContent = galat.message;
      pesan.hidden = false;
      for (const b of tombolKartu) b.disabled = false;
      tombol.disabled = false;
    }
  }

  const verifikasi = (tingkat) => {
    const tombol = el(
      "button",
      {
        type: "button",
        class: "tombol utama",
        onclick: () =>
          jalankan(
            tombol,
            () => api.post(`/api/admin/laporan/${encodeURIComponent(item.nomor)}/verifikasi`, { tingkat: tingkat }),
            () => tampilkanPaket(wadahPaket, item.nomor),
          ),
      },
      `Verifikasi: ${LABEL_TINGKAT[tingkat]}`,
    );
    tombolKartu.push(tombol);
    return tombol;
  };

  const gabung = (dup) => {
    const tombol = el(
      "button",
      {
        type: "button",
        class: "tombol",
        onclick: () =>
          jalankan(tombol, () =>
            api.post(`/api/admin/laporan/${encodeURIComponent(item.nomor)}/gabung`, { induk_nomor: dup.nomor }),
          ),
      },
      `Gabung ke ${dup.nomor}`,
    );
    tombolKartu.push(tombol);
    return tombol;
  };

  const foto = item.foto.map((f, i) =>
    el(
      "figure",
      { class: "foto-mod" },
      el("img", { src: f.url, alt: `Foto ${i + 1} laporan ${item.nomor}`, loading: "lazy" }),
      el("figcaption", {}, ringkasAi(f.hasil_ai)),
    ),
  );

  return el(
    "article",
    { class: item.banding ? "kartu-mod banding" : "kartu-mod", "aria-labelledby": `judul-${item.nomor}` },
    el(
      "h2",
      { id: `judul-${item.nomor}` },
      item.banding ? el("span", { class: "lencana-banding" }, "Banding") : null,
      el("a", { href: `#/laporan/${item.nomor}` }, item.nomor),
      el("span", { class: "redup" }, `Kec. ${item.kecamatan || "-"}, ${item.kota || "-"}`),
    ),
    item.banding
      ? el("p", { class: "catatan-banding" }, "Pelapor meminta peninjauan: menurutnya penolakan otomatis AI keliru.")
      : null,
    el("p", { class: "redup" }, `Masuk ${tanggal(item.dibuat_pada)}`),
    foto.length ? el("div", { class: "grid-foto-mod" }, foto) : el("p", { class: "redup" }, "Tanpa foto bukti."),
    el("p", {}, el("strong", {}, "Keterangan pelapor: "), item.keterangan || "-"),
    item.duplikat.length
      ? el(
          "p",
          { class: "info-duplikat" },
          "Kemungkinan duplikat (≤ 25 m): ",
          item.duplikat.map((d, i) => [
            i ? ", " : "",
            el("a", { href: `#/laporan/${d.nomor}` }, d.nomor),
            ` (${d.jarak_m} m)`,
          ]),
        )
      : null,
    pesan,
    el(
      "div",
      { class: "baris-tombol" },
      verifikasi("rusak"),
      verifikasi("kurang_baik"),
      item.duplikat.map((d) => gabung(d)),
    ),
    el("details", { class: "tolak" }, el("summary", {}, "Tolak laporan"), formTolak(item, jalankan)),
  );
}

function formAmbilPaket(wadahPaket) {
  const input = el("input", {
    id: "nomor-paket",
    name: "nomor",
    required: true,
    placeholder: "JK-00001",
    pattern: "JK-\\d{5}",
    autocomplete: "off",
  });
  const pesan = el("p", { class: "galat", role: "alert", hidden: true });
  return el(
    "form",
    {
      class: "kartu form-paket",
      onsubmit: async (e) => {
        e.preventDefault();
        pesan.hidden = true;
        try {
          await tampilkanPaket(wadahPaket, input.value.trim().toUpperCase());
        } catch (galat) {
          pesan.textContent = galat.message;
          pesan.hidden = false;
        }
      },
    },
    el("label", { for: "nomor-paket" }, "Ambil paket penerusan untuk laporan terverifikasi"),
    el("div", { class: "baris-tombol" }, input, el("button", { type: "submit", class: "tombol" }, "Ambil paket")),
    pesan,
  );
}

/** US-21: koreksi tingkat laporan terverifikasi (sudah tidak ada di antrean, jadi lewat nomor). */
function formKoreksi() {
  const nomor = el("input", {
    id: "nomor-koreksi",
    name: "nomor",
    required: true,
    placeholder: "JK-00001",
    pattern: "JK-\\d{5}",
    autocomplete: "off",
  });
  const tingkat = el(
    "select",
    { id: "tingkat-koreksi", name: "tingkat", required: true },
    el("option", { value: "rusak" }, LABEL_TINGKAT.rusak),
    el("option", { value: "kurang_baik" }, LABEL_TINGKAT.kurang_baik),
  );
  const alasan = el("textarea", {
    id: "alasan-koreksi",
    name: "alasan",
    rows: "2",
    required: true,
    minlength: "5",
    maxlength: "200",
  });
  const pesan = el("p", { class: "galat", role: "alert", hidden: true });
  const tombol = el("button", { type: "submit", class: "tombol" }, "Simpan koreksi");
  const form = el(
    "form",
    {
      class: "form-koreksi",
      onsubmit: async (e) => {
        e.preventDefault();
        pesan.hidden = true;
        const isi = alasan.value.trim();
        if (isi.length < MIN_ALASAN) {
          alasan.setCustomValidity(`Alasan minimal ${MIN_ALASAN} karakter.`);
          alasan.reportValidity();
          return;
        }
        alasan.setCustomValidity("");
        tombol.disabled = true;
        try {
          const no = nomor.value.trim().toUpperCase();
          const hasil = await api.post(`/api/admin/laporan/${encodeURIComponent(no)}/tingkat`, {
            tingkat: tingkat.value,
            alasan: isi,
          });
          umumkan(`Tingkat ${hasil.nomor} kini ${LABEL_TINGKAT[hasil.tingkat] || hasil.tingkat}.`);
          form.reset();
        } catch (galat) {
          pesan.textContent = galat.message;
          pesan.hidden = false;
        } finally {
          tombol.disabled = false;
        }
      },
    },
    el("label", { for: "nomor-koreksi" }, "Nomor laporan terverifikasi"),
    nomor,
    el("label", { for: "tingkat-koreksi" }, "Tingkat yang benar"),
    tingkat,
    el("label", { for: "alasan-koreksi" }, `Alasan koreksi (wajib, ${MIN_ALASAN}–200 karakter)`),
    alasan,
    pesan,
    el("div", { class: "baris-tombol" }, tombol),
  );
  return el("details", { class: "kartu koreksi" }, el("summary", {}, "Koreksi tingkat kerusakan"), form);
}

async function halamanAdmin(wadah) {
  muatCss();
  const wadahPaket = el("div", { "aria-live": "polite" });
  const info = el("p", { class: "redup" });
  const daftar = el("div", { class: "daftar-mod" });

  wadah.append(
    el("h1", {}, "Antrean Admin"),
    el(
      "p",
      { class: "redup" },
      "Laporan yang AI ragu atau tidak dikenali, dan permintaan peninjauan dari pelapor (paling atas). Target ≤ 1 × 24 jam.",
    ),
    wadahPaket,
    formAmbilPaket(wadahPaket),
    formKoreksi(),
    info,
    daftar,
  );

  let permintaan = 0;
  async function muat() {
    const ke = ++permintaan;
    let antrean;
    try {
      antrean = await api.get("/api/admin/antrean");
    } catch (galat) {
      if (ke !== permintaan) return;
      kosongkan(daftar);
      info.textContent = "";
      daftar.append(el("p", { class: "galat", role: "alert" }, `Antrean gagal dimuat: ${galat.message}`));
      return;
    }
    if (ke !== permintaan) return;
    kosongkan(daftar);
    const banding = antrean.filter((i) => i.banding).length;
    info.textContent = antrean.length
      ? `${antrean.length} laporan menunggu verifikasi${banding ? `, ${banding} di antaranya banding` : ""}.`
      : "";
    if (!antrean.length) {
      daftar.append(
        el("p", { class: "kartu" }, "Tidak ada laporan yang menunggu verifikasi. Laporan yang diyakini AI sudah diproses otomatis."),
      );
      return;
    }
    for (const item of antrean) daftar.append(kartuAntrean(item, { muatUlang: muat, wadahPaket }));
  }
  await muat();
}

export const rute = [
  {
    jalur: "#/admin",
    judul: "Antrean",
    menu: true,
    peran: ["admin"],
    tampil: halamanAdmin,
  },
];
