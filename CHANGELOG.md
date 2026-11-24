# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html) (`0.x` until the first stable release).

Each release PR moves entries from **Unreleased** into a new version section; categories: *Added, Changed, Deprecated, Removed, Fixed, Security*.

## [Unreleased]

### Added
- Modular-monolith foundation: `core` (config, SQLite with per-module migrations, in-process events, errors, security headers, CSRF guard, rate limiting, file storage) and ten feature modules with contract-complete stubs.
- Locked contracts: OpenAPI and module public-interface snapshots in `app/kontrak/`, enforced by architecture tests.
- Report domain (`laporan`): numbering, status machine, timeline, supports, visibility rules, public detail endpoint.
- Build-free PWA shell with hash router, shared UI helpers, Leaflet base map, and per-module pages.
- CI (lint, format, architecture, tests with coverage, dependency audit, JavaScript syntax), Dependabot, issue/PR templates, CODEOWNERS.
- Community files: README (EN/ID), CONTRIBUTING, SECURITY, CODE_OF_CONDUCT.
- Status transition preconditions (BR-03): Admin verification requires a damage level, rejection requires a reason (≥ 5 chars), merging requires an active parent report, appeals are allowed once and only against AI rejections, and closing as done requires an after-repair photo when configured (TS-02).
- Region data preparation: normalises district names and builds a local GeoJSON of the 42 districts in the five Jakarta administrative cities (TS-04, #16); `python -m jalanku.modules.wilayah.data.setup_wilayah` downloads the source boundaries with a pinned SHA-256 and runs it (#17).
- District, city and Sudin Bina Marga lookup from coordinates using an STRtree spatial index; points on shared borders resolve deterministically, and missing or corrupt region data returns 503 (US-07, #17).
- Map data endpoint `GET /api/peta` with `aktif` and `riwayat` modes and multi-value city/level filters (US-15, US-16, #18).
- Clustered bubble map pages `#/peta` and `#/riwayat`: colour by damage level, worst-level cluster colour, filters, live summary, legend, district boundaries and a SIMULATION badge (US-15, US-16, #20).
- Officer dashboard API `GET /api/petugas/laporan` scoped to the officer's region, and status updates to in progress / done with an after-repair photo (US-18, US-19, #37).
- Officer page `#/petugas`: per-status summary, filter, map, "start work" action, and a "mark done" form with camera photo and note (US-18, US-19, #40).
- Report detail page `#/laporan/:nomor`: before/after photos, timeline labelled by actor, responsible agency with its official channel, a small map, a SIMULATION badge and a friendly 404 (US-17, #35).
- Tamper-evident audit trail: each timeline entry stores a SHA-256 hash chained to the previous entry; `GET /api/laporan/{nomor}/jejak` recomputes the chain and also checks that its last entry matches the current status; the detail page shows a "verified history" badge (US-32, BR-09, #36).
- In-app notifications: reporters and supporters receive a message when a report's status changes (excluding the reporter's own actions and users who opted out), with list, mark-as-read, and `GET`/`PUT /api/notifikasi/pengaturan` endpoints and a `#/kabar` page; notifications are deleted with the account (US-25, #38).
- When a report is merged, its supporters and reporter become supporters of the parent report in the same transaction, keeping the original support time and never making the parent's reporter a supporter of their own report; new public function `laporan.jumlah_dukungan_massal` counts supports for many reports in one query (CR #23, #34).
- OpenStreetMap tile proxy `GET /api/tile/{z}/{x}/{y}.png` limited to zoom 10–19 inside the Jakarta bounding box, with PNG validation, a 7-day disk cache and per-client then global rate limits (#22, #31, #39).
- `JALANKU_PROXY_TEPERCAYA` setting so the server reads the real client IP behind a trusted reverse proxy (default `127.0.0.1`) (#39).

### Changed
- Report descriptions longer than 280 characters are now rejected instead of silently truncated (TS-02).
- On screens narrower than 720 px the main menu becomes a fixed bottom bar; the active item is marked with `aria-current` and scrolled into view (#32, #39).
- `python -m jalanku contoh-data` stops with a clear message and exit code 1 when region data has not been set up (#33).
- CI prepares the region GeoJSON before running tests (TS-03, #19).
- Setup docs (README, CONTRIBUTING, PR template) now include the region data step and use the `Closes #N` keyword so issues close automatically (#42).

### Fixed
- Bug and change-request issue templates did not appear because comma-containing labels were unquoted (#30).
- Base map tiles were blocked by OpenStreetMap ("Access blocked") in Codespaces; tiles are now served through the proxy and the CSP allows images only from the app itself (#22, #31).

### Security
- Report photos are validated by content (JPEG/PNG/WebP only, max 10 MB), re-encoded as JPEG ≤ 1 MB, and stripped of all EXIF metadata including GPS before storage (TS-02).
- Photos of non-public reports (awaiting verification, rejected) are served with `Cache-Control: private, no-store`; photos of public reports with `public, max-age=86400` (BR-06, TS-02).
- Report visibility (BR-06) is covered by a full status × viewer test matrix for details, photos and AI results; a report whose reporter account was deleted is visible only to Admin (TS-02).
