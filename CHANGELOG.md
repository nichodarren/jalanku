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

### Changed
- Report descriptions longer than 280 characters are now rejected instead of silently truncated (TS-02).

### Security
- Report photos are validated by content (JPEG/PNG/WebP only, max 10 MB), re-encoded as JPEG ≤ 1 MB, and stripped of all EXIF metadata including GPS before storage (TS-02).
- Photos of non-public reports (awaiting verification, rejected) are served with `Cache-Control: private, no-store`; photos of public reports with `public, max-age=86400` (BR-06, TS-02).
- Report visibility (BR-06) is covered by a full status × viewer test matrix for details, photos and AI results; a report whose reporter account was deleted is visible only to Admin (TS-02).
