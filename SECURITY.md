# Security Policy

## Supported versions

Only the latest release on `main` receives security fixes while the project is in the `0.x` series.

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Use GitHub's private reporting: **Security → Advisories → Report a vulnerability** on this repository. Include:

- what is affected (endpoint, module, file) and the impact;
- steps to reproduce or a proof of concept;
- any suggested fix.

We aim to acknowledge reports within **3 days** and to ship a fix or mitigation within **14 days** for high-severity issues. You will be credited in the release notes unless you prefer otherwise.

## Scope notes

- The app processes citizens' photos and locations. Issues that could expose a reporter's identity, EXIF/GPS data, or non-public reports (pending/rejected) are treated as **high severity**.
- `/api/dev/*` endpoints exist only when `JALANKU_MODE` is `dev` or `test`; their presence in production is itself a vulnerability.
- Never include real personal data in a report; use synthetic data.
