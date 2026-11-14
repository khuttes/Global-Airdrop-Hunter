# SECURITY_AUDIT.md

**Project:** Global Airdrop Hunter
**Audit Date:** 2026-11-13
**Auditor:** Kilo AI Assistant
**Phase:** 0 - Environment Audit (Pre-Implementation Baseline)
**Scope:** Threat model, security requirements, and security architecture from implementation plan (PDF Sections 8, 9, 12, 15)

---

## 1. Security Objectives (from PDF)

### Core Security Principles
1. **Discovery-first, read-only V1** - No wallet connection, signing, auto-claiming
2. **All external input is untrusted** - Campaign text, URLs, metadata, API responses
3. **Evidence-based trust** - Every verification label requires stored evidence + timestamp
4. **Local-first architecture** - No data transmitted to external services except discovery sources
5. **Defense in depth** - Multiple trust boundaries with validation at each

### Non-Goals for V1 Security
- ❌ No wallet secret storage (seed phrases, private keys, passwords)
- ❌ No transaction signing or token approvals
- ❌ No automated claiming or financial activity
- ❌ No paid AI API dependencies (Ollama optional, local-only)

---

## 2. Trust Boundaries (from PDF Section 8.1)

| Boundary | Required Treatment | Implementation Status |
|----------|-------------------|----------------------|
| **Renderer → Electron Main** | Narrow preload API; validate every IPC channel/payload | 🔄 Phase 1 |
| **Electron → Python API** | Loopback only (127.0.0.1); per-launch token; strict request schema | 🔄 Phase 1 |
| **External Source → Backend** | Untrusted input; timeouts, size limits, schema validation, redirect limits | 🔄 Phase 3 |
| **Backend → SQLite** | Parameterized queries, transactions, constraints, migrations | 🔄 Phase 1 |
| **Campaign URL → Browser** | Allow HTTP/HTTPS only; show destination host; block dangerous schemes | 🔄 Phase 2 |
| **Campaign Content → UI** | Render as text; sanitize allowed markup; never execute scripts | 🔄 Phase 2 |

---

## 3. Electron Hardening Requirements (from PDF Section 8.2)

| Requirement | Specification | Verification Method |
|-------------|---------------|---------------------|
| **contextIsolation** | `true` | Code review + runtime check |
| **nodeIntegration** | `false` | Code review + runtime check |
| **sandbox** | Enabled where compatible | Code review + runtime check |
| **Content Security Policy** | Strict; no `unsafe-eval`, no broad remote script origins | CSP header inspection |
| **Remote Content** | No remote content in privileged BrowserWindows/webviews | Code review |
| **IPC Validation** | Validate sender + payload; explicit preload methods only | Code review + fuzz testing |
| **Navigation Control** | Control navigation and new windows | Code review + navigation tests |
| **Dependency Updates** | Keep Electron dependencies updated | `npm audit` + scheduled updates |

---

## 4. Network & URL Handling (from PDF Section 8.3)

| Control | Specification | Implementation |
|---------|---------------|----------------|
| **Allowed Schemes** | `http:` `https:` only | URL validation allowlist |
| **Blocked Schemes** | `file:` `javascript:` `data:` wallet schemes (`ethereum:`, `bitcoin:`, etc.) | URL validation denylist |
| **Redirect Limits** | Max 5 hops; record final hostname | HTTPX config |
| **SSRF Protection** | Block localhost, loopback (127.0.0.0/8), link-local (169.254.0.0/16), private ranges (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16) | DNS/IP validation at connection time |
| **DNS Rebinding Protection** | Validate resolved IP against private ranges before request | Custom HTTPX transport |
| **Timeouts** | Connect: 10s, Read: 30s, Total: 60s | HTTPX timeout config |
| **Response Size Cap** | 10 MB max (configurable) | HTTPX response streaming with limit |
| **Content-Type Check** | Reject non-text/non-JSON for parsing endpoints | Header validation |

---

## 5. Wallet Boundary (from PDF Section 8.4)

| Rule | Enforcement |
|------|-------------|
| **No wallet connection** | No Web3 provider injection, no `window.ethereum` exposure |
| **No signing** | No transaction creation, signing, or broadcasting code |
| **No approvals** | No `eth_approve`, `permit`, or similar RPC calls |
| **No seed phrases** | Never request, store, transmit, or log mnemonics |
| **No private keys** | Never request, store, transmit, or log private keys |
| **Public address monitoring (future)** | If added later: public blockchain data only, separate security review |

---

## 6. Threat Cases & Defenses (from PDF Section 8.5)

| Threat | Expected Defense | Test Case |
|--------|------------------|-----------|
| **Recovery phrase requested** | Critical flag; never collect/transmit | Inject seed phrase request in campaign description |
| **Lookalike domain** | Domain mismatch warning; require primary evidence | Typosquatting domain in campaign URL |
| **Malicious HTML title** | Escape as text; no script execution | `<script>alert(1)</script>` in title field |
| **Redirect to local admin** | Block private/loopback destination | Campaign URL redirects to `http://127.0.0.1:8080/admin` |
| **Oversized response** | Reject using response-size cap | Source returns 100MB response |
| **Source outage/malformed JSON** | Isolate adapter; preserve last record as stale | Source returns invalid JSON / 5xx / timeout |
| **Forged local API request** | Reject missing/invalid token and invalid origin | POST to `/api/v1/campaigns` without token |
| **Database corruption** | Integrity check and verified restore | `PRAGMA integrity_check` + backup restore test |

---

## 7. API Security (from PDF Section 9)

### Authentication & Authorization
- **Per-launch token** generated at startup, passed via header `X-Local-API-Token`
- **Origin validation** - Reject requests with `Origin`/`Referer` not matching `http://127.0.0.1:*` or `file://`
- **Request schema validation** - Pydantic models for all endpoints
- **Rate limiting** - Per-endpoint limits (e.g., 60 req/min for scan triggers)

### Endpoint Security Checklist
| Endpoint | Auth | Validation | Rate Limit |
|----------|------|------------|------------|
| `GET /api/v1/health` | Token | None | 120/min |
| `GET /api/v1/dashboard` | Token | Query params | 60/min |
| `GET /api/v1/campaigns` | Token | Pagination, filters | 60/min |
| `GET /api/v1/campaigns/{id}` | Token | UUID format | 120/min |
| `POST /api/v1/discovery/scans` | Token | Source selection | 10/min |
| `POST /api/v1/campaigns/{id}/save` | Token | Campaign exists | 60/min |
| `POST /api/v1/backup` | Token | None | 5/min |

### API Conventions
- All errors: `{ "error": { "code": "...", "message": "...", "details": {} } }` with appropriate HTTP status
- Pagination: `page`, `page_size` (max 100)
- Timestamps: UTC ISO-8601 (`2026-11-13T12:00:00Z`)
- No arbitrary filesystem paths or command execution exposed

---

## 8. Data Protection & Privacy (from PDF Sections 6.4, 8.4)

| Data Type | Handling |
|-----------|----------|
| **Campaign data** | Stored locally in SQLite; user-controlled export/delete |
| **User notes/progress** | Stored locally; export/delete controls in UI |
| **Wallet addresses** | Not collected in V1; if added later: optional, public only |
| **API keys (optional)** | Windows Credential Manager (DPAPI); never in code/logs/env |
| **Logs** | Structured; redact tokens, credentials, sensitive paths |
| **Backups** | User-controlled location; integrity verified; retention policy |
| **Telemetry** | None in V1 |

---

## 9. Secure Development Practices (from PDF Section 10.1)

| Practice | Enforcement |
|----------|-------------|
| **Project-specific venv** | `.venv/` in project root (gitignored) |
| **Pinned dependencies** | `package-lock.json`, `requirements.txt` with exact versions |
| **Type hints** | Python: full typing; JS: JSDoc or TypeScript (future) |
| **Pydantic models** | All API request/response validation |
| **Structured logging** | JSON logs with timestamp, severity, component, scan_id |
| **Small modules** | Single responsibility; explicit dependencies |
| **Tests with features** | Unit + integration per feature |
| **Migrations for schema changes** | Alembic or custom; never delete/recreate DB |
| **Secrets out of Git** | `.gitignore` covers `.env`, `.venv/`, `*.db`, `backups/`, `logs/`, `dist/` |
| **No secrets in logs** | Redaction middleware |
| **Meaningful commits** | Conventional commits; CHANGELOG maintained |

---

## 10. Security Testing Requirements (from PDF Section 12)

### Test Layers
| Layer | Security Focus |
|-------|----------------|
| **Unit** | URL validation, scoring logic, deduplication, date parsing |
| **Integration** | API + SQLite, mocked adapters, migrations, backup/restore |
| **Security** | XSS payloads, IPC misuse, SSRF/redirect, malformed input, secret leakage |
| **End-to-end** | Launch, scan, view, filter, save, notify, restart |
| **Operational** | Offline start, source timeout, partial scan, restore, log rotation |
| **Packaging** | Clean install, upgrade, uninstall, user-data preservation |

### Specific Security Test Cases
1. **XSS in campaign title/description** - Inject `<img src=x onerror=alert(1)>` → verify escaped in UI
2. **IPC prototype pollution** - Send `__proto__` payload → verify rejected
3. **SSRF via campaign URL** - `http://169.254.169.254/latest/meta-data/` → verify blocked
4. **Redirect chain to localhost** - Campaign URL → 302 → `http://127.0.0.1:8080` → verify blocked
5. **Oversized API response** - Source returns 50MB → verify truncated/rejected
6. **Malformed JSON from source** - Invalid UTF-8, truncated JSON → verify adapter isolation
7. **Forged scan request** - POST to `/api/v1/discovery/scans` without token → verify 401
8. **Path traversal in export** - `../../etc/passwd` in export filename → verify sanitized
9. **SQL injection in filters** - `' OR 1=1--` in search → verify parameterized query
10. **CSP bypass attempt** - Inline script in campaign data → verify CSP blocks

---

## 11. Dependency Security

### Required Auditing Tools
| Ecosystem | Tool | Frequency |
|-----------|------|-----------|
| **npm** | `npm audit` / `npm audit signatures` | Each release + weekly |
| **Python** | `pip-audit` / `safety` | Each release + weekly |
| **Electron** | `electron-builder` security checks | Each release |

### Supply Chain Protections
- Use `npm ci` / `pip install --require-hashes` in CI
- Verify package signatures where available
- Pin exact versions; no floating ranges (`^`, `~`)
- Review new dependencies before adding
- Document justification for each dependency

---

## 12. Current Security Posture (Phase 0 Baseline)

| Control | Status | Evidence |
|---------|--------|----------|
| **Code exists** | ❌ No code yet | Greenfield project |
| **Electron hardening** | 🔄 Planned Phase 1 | PDF spec Section 8.2 |
| **API authentication** | 🔄 Planned Phase 1 | PDF spec Section 9 |
| **URL validation** | 🔄 Planned Phase 2 | PDF spec Section 8.3 |
| **Input sanitization** | 🔄 Planned Phase 2 | PDF spec Section 8.1 |
| **Database security** | 🔄 Planned Phase 1 | PDF spec Section 6.2 |
| **Backup/restore** | 🔄 Planned Phase 8 | PDF spec Section 13.2 |
| **Dependency auditing** | 🔄 Planned Phase 8 | PDF spec Section 12 |
| **Security testing** | 🔄 Planned Phase 8, 10 | PDF spec Section 12 |
| **Threat model documented** | ✅ This document | Derived from PDF Section 8 |

---

## 13. Security Gate Criteria (from PDF Section 12.4)

**No release with unresolved critical security findings.**

| Gate | Criteria |
|------|----------|
| **Phase 1** | Electron hardened; API bound to 127.0.0.1 with token auth |
| **Phase 3** | Source adapters isolated; timeouts/size limits enforced |
| **Phase 5** | Critical risk overrides implemented (seed phrase = critical) |
| **Phase 8** | All security tests pass; backup/restore verified; dependency audit clean |
| **Phase 9** | Installer signed (optional); upgrade preserves data; no debug code |
| **Phase 10** | Full regression suite green; no critical/open high findings |

---

## 14. Residual Risks & Acceptance (from PDF Section 15)

| Risk | Likelihood | Impact | Acceptance |
|------|------------|--------|------------|
| **Zero-day in Electron/Node/Python** | Low | High | Monitor advisories; patch within 72h |
| **Source becomes malicious** | Low | Medium | Source health monitoring; disable switch |
| **User ignores critical warning** | Medium | High | Clear UI; cannot auto-claim; manual browser only |
| **Local API token stolen** | Very Low | Medium | Per-launch token; loopback only; short lifetime |
| **SQLite corruption** | Low | High | WAL mode; verified backups; integrity checks |

---

## 15. Compliance & Standards Alignment

| Standard | Applicability | Approach |
|----------|---------------|----------|
| **OWASP Top 10 (2021)** | Web/API security | Address A01-A10 in API + renderer |
| **OWASP Electron Security** | Desktop app | Follow Electron security checklist |
| **CWE Top 25** | Code weaknesses | Static analysis + secure coding |
| **NIST SSDF** | Development lifecycle | Secure practices per PDF Section 10 |

---

## 16. Next Steps for Phase 1

1. **Implement Electron main process** with all hardening flags
2. **Create preload.js** with explicit, validated IPC methods only
3. **Configure CSP** in `BrowserWindow` webPreferences
4. **Build FastAPI** with token middleware + origin validation
5. **Set up SQLite** with WAL mode, foreign keys, parameterized queries
6. **Create first migration** with secure schema (no dynamic SQL)
7. **Add structured logging** with redaction
8. **Write security unit tests** for URL validation, token auth, CSP

---

**Audit Complete.** This baseline establishes the security requirements that all subsequent phases must satisfy. Each phase will update this document with implementation evidence and test results.

**No security controls implemented yet** - this is the pre-implementation threat model and requirements specification.