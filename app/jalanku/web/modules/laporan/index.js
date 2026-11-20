// Frontend modul laporan: halaman detail #/laporan/:nomor (US-17). Pemilik: M1.
// Kontrak data: GET /api/laporan/{nomor} (DetailLaporanKeluaran) + GET /api/instansi (nama & kanal resmi).
// Diport dari jalanku-v0 app/jalanku/web/js/views/laporan.js (karya Yosua), bagian tampilan publik saja:
// panel Admin ada di modul moderasi (M5) dan panel Petugas di modul penanganan (M6).
// Jalur rute dipakai modul lain sebagai tautan: jangan diubah.

import { api } from "/shared/api.js";
import { LABEL_PELAKU, LABEL_STATUS, LABEL_TINGKAT } from "/shared/konstanta.js";
import { buatPeta } from "/shared/peta-dasar.js";
import { el } from "/shared/ui.js";

const CSS_MODUL = "/modules/laporan/laporan.css";
const FORMAT_WAKTU = new Intl.DateTimeFormat("id-ID", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Jakarta" });
const POLA_NOMOR = /\bJK-\d{5}\b/g;

function muatCss() {
  if (!document.querySelector(`link[href="${CSS_MODUL}"]`)) {
    document.head.append(el("link", { rel: "stylesheet", href: CSS_MODUL }));
  }
}

function waktu(iso) {
  const t = iso ? new Date(iso) : null;
  return t && !Number.isNaN(t.getTime()) ? FORMAT_WAKTU.format(t) : "-";
}

/** Teks biasa, tetapi nomor laporan (mis. "Digabung ke JK-00012") menjadi tautan. Tanpa HTML mentah. */
function teksBertaut(teks) {
  const hasil = [];
  let akhir = 0;
  for (const m of teks.matchAll(POLA_NOMOR)) {
    hasil.push(teks.slice(akhir, m.index), el("a", { href: `#/laporan/${m[0]}` }, m[0]));
    akhir = m.index + m[0].length;
  }
  hasil.push(teks.slice(akhir));
  return hasil;
}

function lencanaStatus(status) {
  return el("span", { class: `detail-lencana status-${status}` }, LABEL_STATUS[status] || status);
}

function lencanaTingkat(tingkat) {
  return tingkat ? el("span", { class: `detail-lencana tingkat-${tingkat}` }, LABEL_TINGKAT[tingkat] || tingkat) : null;
}

function judul(d) {
  if (d.status === "selesai") return "Jalan sudah diperbaiki";
  if (d.tingkat) return `Jalan ${(LABEL_TINGKAT[d.tingkat] || d.tingkat).toLowerCase()}`;
  return "Laporan jalan";
}

function kartuFoto(d) {
  const sebelum = d.foto.filter((f) => f.jenis === "bukti");
  const sesudah = d.foto.filter((f) => f.jenis === "sesudah");
  const gambar = (f, alt) => el("img", { src: f.url, alt, loading: "lazy", decoding: "async" });
  const kolom = (label, isi) => el("figure", { class: "detail-kolom-foto" }, el("figcaption", {}, label), ...isi);
  if (!sebelum.length && !sesudah.length) return null;
  if (!sesudah.length) {
    return el("div", { class: "detail-foto" }, sebelum.map((f, i) => gambar(f, `Foto jalan ${i + 1} dari ${sebelum.length}`)));
  }
  // Selesai: sebelum & sesudah berdampingan supaya warga bisa membandingkan hasil perbaikan.
  return el(
    "div",
    { class: "detail-foto berdampingan" },
    kolom("Sebelum", sebelum.map((f, i) => gambar(f, `Foto sebelum perbaikan ${i + 1}`))),
    kolom("Sesudah", sesudah.map((f, i) => gambar(f, `Foto setelah perbaikan ${i + 1}`))),
  );
}

function catatanStatus(d) {
  const terakhir = d.timeline.at(-1);
  if (d.status === "menunggu_verifikasi") {
    return el("p", { class: "detail-info" }, "Menunggu pemeriksaan Admin JalanKu sebelum diteruskan ke instansi.");
  }
  if (d.status === "ditolak") {
    return el("p", { class: "detail-info penting" }, "Laporan ditolak. ", terakhir?.catatan ? teksBertaut(terakhir.catatan) : null);
  }
  if (d.status === "digabung") {
    return el(
      "p",
      { class: "detail-info" },
      "Laporan ini digabung ke laporan lain yang menunjuk kerusakan yang sama. ",
      terakhir?.catatan ? teksBertaut(terakhir.catatan) : null,
    );
  }
  return null;
}

function kartuUtama(d) {
  const pemeriksa = d.diperiksa_oleh ? `Diperiksa oleh ${LABEL_PELAKU[d.diperiksa_oleh] || d.diperiksa_oleh}` : null;
  return el(
    "section",
    { class: "kartu" },
    el("div", { class: "detail-kepala" }, el("h1", {}, judul(d)), lencanaStatus(d.status), lencanaTingkat(d.tingkat)),
    d.simulasi
      ? el("p", { class: "detail-simulasi" }, "SIMULASI: data contoh untuk pengembangan, bukan laporan warga nyata.")
      : null,
    el(
      "p",
      { class: "redup" },
      [d.nomor, d.kecamatan ? `Kec. ${d.kecamatan}` : null, d.kota].filter(Boolean).join(" · "),
      el("br"),
      `Dilaporkan ${waktu(d.dibuat_pada)}`,
    ),
    d.keterangan ? el("p", {}, d.keterangan) : null,
    kartuFoto(d),
    catatanStatus(d),
    el(
      "p",
      { class: "detail-ringkas" },
      el("strong", {}, String(d.jumlah_dukungan)),
      " warga ikut mendukung",
      pemeriksa ? ` · ${pemeriksa}` : null,
    ),
  );
}

function kartuInstansi(d, instansi) {
  const peta = el("div", { class: "peta detail-peta", role: "img", "aria-label": `Lokasi laporan ${d.nomor} di peta` });
  return {
    peta,
    kartu: el(
      "section",
      { class: "kartu" },
      el("h2", {}, "Ditangani oleh"),
      el("p", { class: "detail-instansi" }, instansi ? instansi.nama : d.instansi_id),
      instansi
        ? el(
            "p",
            { class: "redup" },
            "Kanal resmi: ",
            el("a", { href: instansi.kanal_url, target: "_blank", rel: "noopener noreferrer" }, instansi.kanal_nama),
          )
        : null,
      peta,
    ),
  };
}

/** US-32: lencana keutuhan riwayat (rantai hash). Diisi belakangan; disembunyikan bila jejak tidak tersedia. */
async function isiLencanaJejak(wadah, nomor) {
  let jejak;
  try {
    jejak = await api.get(`/api/laporan/${encodeURIComponent(nomor)}/jejak`);
  } catch {
    return; // mis. 501 sebelum US-32 aktif: tidak menampilkan apa pun
  }
  wadah.append(
    jejak.utuh
      ? el("p", { class: "detail-jejak utuh" }, "✓ Riwayat terverifikasi: tidak ada entri yang diubah sejak dicatat.")
      : el("p", { class: "detail-jejak", role: "status" }, "Riwayat ini tidak bisa dibuktikan utuh. Hubungi Admin JalanKu."),
  );
}

function kartuTimeline(d, jejak) {
  return el(
    "section",
    { class: "kartu" },
    el("h2", {}, "Riwayat status"),
    jejak,
    el(
      "ol",
      { class: "detail-timeline" },
      d.timeline.map((t) =>
        el(
          "li",
          { class: `status-${t.ke_status}` },
          el("span", { class: "detail-langkah" }, LABEL_STATUS[t.ke_status] || t.ke_status),
          el("span", { class: "redup" }, `${waktu(t.waktu)} · oleh ${LABEL_PELAKU[t.pelaku] || t.pelaku}`),
          t.catatan ? el("span", {}, teksBertaut(t.catatan)) : null,
        ),
      ),
    ),
  );
}

async function ambilInstansi(id) {
  try {
    return (await api.get("/api/instansi")).find((i) => i.id === id) || null;
  } catch {
    return null; // nama instansi pelengkap: halaman tetap tampil walau daftar instansi gagal dimuat
  }
}

async function tampilDetail(wadah, param) {
  muatCss();
  const nomor = String(param.nomor || "").toUpperCase();
  const kembali = el(
    "p",
    {},
    el("a", { href: "#/peta", onclick: (e) => history.length > 1 && (e.preventDefault(), history.back()) }, "‹ Kembali"),
  );
  let d;
  try {
    d = await api.get(`/api/laporan/${encodeURIComponent(nomor)}`);
  } catch (galat) {
    const tidakAda = galat.kode === 404;
    wadah.append(
      kembali,
      el(
        "section",
        { class: "kartu" },
        el("h1", {}, tidakAda ? "Laporan tidak ditemukan" : "Laporan gagal dimuat"),
        el("p", {}, tidakAda ? `Laporan ${nomor} tidak ada atau belum bisa dilihat publik.` : galat.message),
      ),
    );
    return;
  }
  document.title = `${d.nomor} · JalanKu`;
  const instansi = await ambilInstansi(d.instansi_id);
  const { kartu, peta } = kartuInstansi(d, instansi);
  const jejak = el("div", { "aria-live": "polite" });
  wadah.append(kembali, kartuUtama(d), kartu, kartuTimeline(d, jejak));
  isiLencanaJejak(jejak, d.nomor);

  const map = buatPeta(peta, { zoom: 17, pusat: [d.lat, d.lon] });
  window.L.circleMarker([d.lat, d.lon], { radius: 9, className: `detail-titik status-${d.status}` }).addTo(map);
  window.addEventListener("hashchange", () => map.remove(), { once: true });
}

export const rute = [
  {
    jalur: "#/laporan/:nomor",
    judul: "Detail laporan",
    menu: false,
    peran: null,
    tampil: tampilDetail,
  },
];
