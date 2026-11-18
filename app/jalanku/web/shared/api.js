// Klien API bersama. Pemilik: M1.
// - Request yang mengubah data otomatis membawa header CSRF X-JalanKu: 1 (lihat core/keamanan.py).
// - Galat dari server ({"detail": "..."}) dilempar sebagai Error dengan pesan Bahasa Indonesia.

export class GalatApi extends Error {
  constructor(pesan, kode) {
    super(pesan);
    this.kode = kode;
  }
}

async function kirim(metode, jalur, isi) {
  const opsi = { method: metode, credentials: "same-origin", headers: {} };
  if (metode !== "GET") opsi.headers["X-JalanKu"] = "1";
  if (isi instanceof FormData) {
    opsi.body = isi;
  } else if (isi !== undefined) {
    opsi.headers["Content-Type"] = "application/json";
    opsi.body = JSON.stringify(isi);
  }
  const respons = await fetch(jalur, opsi);
  if (respons.status === 204) return null;
  const data = await respons.json().catch(() => null);
  if (!respons.ok) {
    const pesan = typeof data?.detail === "string" ? data.detail : "Permintaan tidak bisa diproses.";
    throw new GalatApi(pesan, respons.status);
  }
  return data;
}

export const api = {
  get: (jalur) => kirim("GET", jalur),
  post: (jalur, isi) => kirim("POST", jalur, isi),
  put: (jalur, isi) => kirim("PUT", jalur, isi),
  patch: (jalur, isi) => kirim("PATCH", jalur, isi),
  hapus: (jalur) => kirim("DELETE", jalur),
};
