// Pembantu DOM bersama. Pemilik: M1 (reviewer UX: M6).
// Selalu bangun DOM dengan textContent / el(), JANGAN innerHTML dengan data dari server (OWASP A05).

export function el(tag, atribut = {}, ...anak) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(atribut)) {
    if (v === null || v === undefined || v === false) continue;
    if (k.startsWith("on") && typeof v === "function") node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v === true ? "" : String(v));
  }
  for (const a of anak.flat()) {
    if (a === null || a === undefined || a === false) continue;
    node.append(a instanceof Node ? a : document.createTextNode(String(a)));
  }
  return node;
}

export function kosongkan(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

/** Kartu penanda halaman yang belum dibuat (stub). */
export function belumDibuat(judul, story, pemilik, catatan = "") {
  return el(
    "section",
    { class: "kartu stub" },
    el("h1", {}, judul),
    el("p", {}, `Halaman ini belum dibuat (${story}, pemilik ${pemilik}).`),
    catatan ? el("p", { class: "redup" }, catatan) : null,
  );
}

export function umumkan(pesan) {
  const kotak = el("div", { class: "toast", role: "status" }, pesan);
  document.body.append(kotak);
  setTimeout(() => kotak.remove(), 4000);
}
