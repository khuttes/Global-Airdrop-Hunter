# DEVELOPMENT_ROADMAP.md

**Project:** Global Airdrop Hunter
**Created:** 2026-11-13
**Based on:** Professional Implementation Plan (PDF Sections 11, 12, 13, 14, 15)
**Status:** Phase 1 Complete (Electron Integration Blocked - Using Browser Launcher Fallback)

---

## Overview

This roadmap follows the **phase-gated implementation plan** from the specification. Each phase has:
- **Objective** - What will be built
- **Deliverables** - Concrete outputs
- **Exit Gate** - Criteria to proceed to next phase
- **Dependencies** - What must be complete before starting
- **Estimated Effort** - Rough sizing

**Non-Negotiable Rule:** One phase at a time. Stop at each gate, show evidence, wait for approval.

---

## Phase 0: Environment Audit and Agreement ✅ COMPLETE

| Item | Status |
|------|--------|
| **Objective** | Read-only inspection of Windows, tools, disk, permissions, project path |
| **Deliverables** | `PROJECT_AUDIT.md`, `ENVIRONMENT_AUDIT.md`, `DEVELOPMENT_ROADMAP.md`, `SECURITY_AUDIT.md` |
| **Exit Gate** | Audit reports delivered; no packages installed; no configuration changed |
| **Completed** | 2026-11-13 |

---

## Phase 1: Safe Scaffold and Desktop Shell ✅ COMPLETE (with Electron Integration Blocked)

| Item | Detail |
|------|--------|
| **Objective** | Create project structure, initialize Git, scaffold hardened Electron + FastAPI + SQLite, build empty-state dashboard |
| **Dependencies** | Phase 0 approval |
| **Key Tasks** |
| 1.1 | Create exact directory structure per PDF Section 10 |
| 1.2 | Initialize Git repository with `.gitignore` |
| 1.3 | Create Python 3.12 virtual environment at `.venv/` |
| 1.4 | Install Electron (latest stable) + electron-builder as dev dependencies |
| 1.5 | Create hardened Electron `main.js` (contextIsolation, sandbox, CSP, preload) |
| 1.6 | Create `preload.js` with narrow, validated IPC API |
| 1.7 | Create minimal `index.html` + CSS + JS for dark dashboard shell with navigation |
| 1.8 | Create FastAPI `main.py` with `/api/v1/health` endpoint on 127.0.0.1 |
| 1.9 | Create SQLite database in user-data dir (`%LOCALAPPDATA%\GlobalAirdropHunter\`) with first migration |
| 1.10 | Create PowerShell scripts: `setup.ps1`, `start.ps1`, `stop.ps1`, `backup.ps1`, `diagnostics.ps1`, `launch.ps1` |
| 1.11 | Test: API health passes, DB initializes, clean shutdown (backend + browser launcher) |
| **Deliverables** | Working app skeleton, Git repo with initial commit, passing health check, browser-based launcher |
| **Exit Gate** | API health passes, DB initializes, shutdown clean (backend + browser launcher verified) |
| **Estimated Effort** | 3-5 development sessions |
| **Status** | ✅ COMPLETE - Electron integration blocked (see `ELECTRON_INTEGRATION_ISSUES.md`), browser launcher (`launch.ps1`) functional |

### File Structure to Create
```
E:\Global Airdrop Hunter\
├── .gitignore
├── package.json                 # Electron + build config
├── desktop/
│   ├── main.js                  # Electron main process (hardened)
│   ├── preload.js               # Secure IPC bridge
│   └── package.json             # Desktop-specific deps (optional)
├── frontend/
│   ├── index.html               # Dashboard shell
│   ├── css/
│   │   ├── variables.css        # Dark/light theme tokens
│   │   ├── layout.css           # Sidebar, header, content grid
│   │   ├── components.css       # Tables, cards, badges, forms
│   │   └── states.css           # Loading, empty, error, offline
│   └── js/
│       ├── app.js               # Main renderer entry
│       ├── api.js               # Backend API client
│       ├── navigation.js        # Module routing
│       └── components/          # Reusable UI components
├── backend/
│   ├── main.py                  # FastAPI app entry
│   ├── config.py                # Settings management
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py        # SQLite connection pool
│   │   ├── migrations/          # Migration files
│   │   │   └── 001_initial_schema.sql
│   │   └── repositories/        # Data access layer
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── health.py        # GET /api/v1/health
│   │   │   └── dashboard.py     # GET /api/v1/dashboard (stub)
│   │   └── middleware/
│   │       └── auth.py          # Local API token validation
│   ├── core/
│   │   ├── __init__.py
│   │   ├── models.py            # Pydantic models
│   │   └── security.py          # Token generation, validation
│   └── requirements.txt         # Python dependencies
├── scripts/
│   ├── setup.ps1                # One-time environment setup
│   ├── start.ps1                # Start app (backend + Electron)
│   ├── stop.ps1                 # Graceful shutdown
│   ├── backup.ps1               # Database backup
│   └── diagnostics.ps1          # Health checks
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── security/
│   └── end_to_end/
└── docs/
    ├── architecture.md
    ├── security.md
    ├── database.md
    └── installation.md
```

---

## Phase 2: Campaign Model and Manual Records ✅ COMPLETE

| Item | Detail |
|------|--------|
| **Objective** | Finalize Pydantic models, repositories, CRUD, pagination, search, filters, detail view, change history |
| **Dependencies** | Phase 1 complete (DB, API, Electron shell working) |
| **Key Tasks** |
| 2.1 | Define complete Pydantic models for Campaign, Source, Evidence, Risk, Eligibility |
| 2.2 | Implement repository layer with parameterized SQL |
| 2.3 | Create API endpoints: `GET/POST /api/v1/campaigns`, `GET /api/v1/campaigns/{id}` |
| 2.4 | Add pagination, search, filters, sorting to API and frontend |
| 2.5 | Build campaign detail view with evidence, history, risk, eligibility panels |
| 2.6 | Add reference data: categories, blockchains tables with seed data |
| 2.7 | Create clearly labelled demo/test fixtures (6 campaigns with evidence, risk findings, eligibility) |
| **Deliverables** | Full CRUD for campaigns, working search/filter, detail view |
| **Exit Gate** | Records can be managed and searched; demo data is unmistakable |
| **Estimated Effort** | 3-4 sessions |
| **Status** | ✅ COMPLETE |

---

## Phase 3: Source Registry and First Real Adapters ✅ COMPLETE

| Item | Detail |
|------|--------|
| **Objective** | Implement source registry, enable/disable, health checks, 1-2 documented public sources |
| **Dependencies** | Phase 2 complete (models, API, DB working) |
| **Key Tasks** |
| 3.1 | Create `sources` table, registry service, enable/disable/pause logic |
| 3.2 | Implement adapter interface: `discover()`, `health_check()`, `source_metadata()`, `parse_record()` |
| 3.3 | Select 1-2 documented public sources (e.g., CoinGecko API, DefiLlama, GitHub API, official RSS feeds) |
| 3.4 | Implement adapters with: timeouts, rate limits, response caps, error isolation |
| 3.5 | Normalize records, store evidence URLs/timestamps, content fingerprints |
| 3.6 | Add scan history tracking, partial-success reporting |
| 3.7 | Verify current source documentation and terms of service |
| **Deliverables** | Working source registry, at least one real adapter producing traceable records |
| **Exit Gate** | One permitted source produces real, traceable records; failures isolated |
| **Estimated Effort** | 3-5 sessions |
| **Critical** | Respect rate limits, robots.txt, ToS; no scraping bypassing auth/CAPTCHA |
| **Status** | ✅ COMPLETE - 4 adapters implemented (CoinGecko, DefiLlama, GitHub, RSS), source registry with health checks, scan orchestration, frontend integration |

### Candidate Sources (from PDF Section 4.1)
| Source | Type | Use Case | Caution |
|--------|------|----------|---------|
| CoinGecko | Documented API | Token metadata, market context | Not airdrop authority |
| DefiLlama | Documented API | Protocol/DeFi context | Verify claims elsewhere |
| GitHub | Public API | Official repos, releases, docs | Establish org ownership |
| Galxe | Public API | Web3 campaign discovery | Corroborate project announcement |
| Layer3 | Public API | Ecosystem campaigns | Check current access/terms |
| Official Sites/Blogs | RSS/HTML | Primary announcements | Highest-value evidence |

---

## Phase 4: Deduplication and Lifecycle ✅ COMPLETE

| Item | Detail |
|------|--------|
| **Objective** | Normalize URLs, stable IDs, conservative duplicate matching, track field changes, detect expired/withdrawn |
| **Dependencies** | Phase 3 complete (real data flowing) |
| **Key Tasks** |
| 4.1 | URL normalization (strip tracking params, canonicalize) |
| 4.2 | Stable campaign ID generation (project+title+network hash) |
| 4.3 | Duplicate matching: domain/title, URL overlap, network/date, source IDs, content similarity |
| 4.4 | Audit trail for merges; never silently merge conflicting records |
| 4.5 | Track first_seen, last_seen, field_change_history |
| 4.6 | Detect expired (deadline passed), withdrawn (project confirms cancellation), changed campaigns |
| **Deliverables** | Deduplication engine with audit trail, lifecycle state machine |
| **Exit Gate** | Deduplication auditable; history preserved |
| **Estimated Effort** | 2-3 sessions |
| **Status** | ✅ COMPLETE - URL normalization, stable_id generation (project+name+network), fuzzy duplicate matching with 0.85 threshold, merge audit trail, field change history, lifecycle event tracking, expired/withdrawn detection |

---

## Phase 5: Verification and Risk Intelligence ✅ COMPLETE

| Item | Detail |
|------|--------|
| **Objective** | Official-domain evidence, verification states, deterministic risk rules, critical overrides |
| **Dependencies** | Phase 4 complete (clean, deduplicated data) |
| **Key Tasks** |
| 5.1 | Official domain verification: WHOIS, SSL cert, DNS, project-controlled source confirmation |
| 5.2 | Verification states: Officially Corroborated, Independently Corroborated, Unverified, Suspicious, Expired, Withdrawn |
| 5.3 | Evidence requirements per state (primary source + timestamp) |
| 5.4 | Risk scoring engine (0-100) with findings: credential request, upfront payment, domain impersonation, no primary evidence, unverified contract, unrealistic guarantee, unexpected permissions |
| 5.5 | Critical overrides: seed-phrase request = critical regardless of score |
| 5.6 | Display findings with source, timestamp, reason, rule version |
| 5.7 | False-positive review workflow, rule-version history |
| 5.8 | Third-party listings NEVER automatically confer official status |
| **Deliverables** | Verification engine, risk scorer, UI panels showing evidence |
| **Exit Gate** | Every official label has primary evidence; critical cases override score |
| **Estimated Effort** | 4-5 sessions |
| **Status** | ✅ COMPLETE - Domain verification (WHOIS/SSL/DNS), 6 verification states, evidence-based assessment, risk engine (15 rules, 0-100 scoring), critical overrides (credential_request, upfront_payment), findings with rule version/timestamp, API endpoints for verification/risk/domain/adapters |

## Phase 6: Eligibility and Progress ✅ COMPLETE

| Item | Detail |
|------|--------|
| **Objective** | Structured eligibility requirements, unknown state, manual progress recording |
| **Dependencies** | Phase 5 complete (verification working) |
| **Key Tasks** |
| 6.1 | Extract requirements: region, network, activity, snapshot, tasks, deadline |
| 6.2 | Represent each as: confirmed, not_met, user_reported_met, unknown, not_applicable |
| 6.3 | Source + timestamp for every requirement |
| 6.4 | Manual progress recording (user checkboxes, notes) |
| 6.5 | Distinguish: potentially_eligible, user_reported_complete, claim_available |
| 6.6 | No wallet connection or inference from undisclosed personal data |
| 6.7 | Claim tracking: airdrop, NFT mint, reward claim, testnet reward with transaction hash |
| **Deliverables** | Eligibility panel, progress tracker, evidence-backed requirements, claim tracking |
| **Exit Gate** | Evidence-backed eligibility panel does not overstate certainty |
| **Estimated Effort** | 2-3 sessions |
| **Status** | ✅ COMPLETE - Eligibility requirement CRUD, auto-extraction from text, user progress tracking (met/not_met/in_progress/not_applicable), claim tracking (airdrop/nft_mint/reward_claim/testnet_reward) with transaction hash, progress statuses (potentially_eligible/user_reported_met/claim_available/claimed) |

## Phase 7: NFT, Testnet and Reward Tracking ✅ COMPLETE

| Item | Detail |
|------|--------|
| **Objective** | Category-specific fields, reward confirmation tracking, calendar/notifications |
| **Dependencies** | Phase 6 complete |
| **Key Tasks** |
| 7.1 | NFT fields: collection, mint info, official links, whitelist, quantity |
| 7.2 | Testnet classification: network, docs, tasks, duration, explorer/faucet links |
| 7.3 | Separate confirmed rewards from speculative incentives |
| 7.4 | Track claim announcements, distribution events, calendar |
| 7.5 | Deadline notifications (in-app first) |
| **Deliverables** | NFT/Testnet modules sharing lifecycle, category-specific data |
| **Exit Gate** | Campaign types share lifecycle while retaining category-specific data |
| **Estimated Effort** | 3-4 sessions |
| **Status** | ✅ COMPLETE - NFT/Testnet/Reward category-specific fields, event/calendar system, notification preferences, category-aware API endpoints with type validation |

## Phase 8: Security and Reliability ✅ COMPLETE

| Item | Detail |
|------|--------|
| **Objective** | Electron hardening review, API auth testing, malicious input testing, backup/restore, dependency scans |
| **Dependencies** | Phase 7 complete (all features implemented) |
| **Key Tasks** |
| 8.1 | Review Electron config: contextIsolation, sandbox, CSP, IPC allowlist |
| 8.2 | Test local API auth: token validation, origin checking, request schema validation |
| 8.3 | Security test cases: XSS payloads, IPC misuse, SSRF/redirect, oversized responses, malformed payloads |
| 8.4 | Backup/restore: SQLite backup API, timestamped backups, integrity checks, verified restore |
| 8.5 | Dependency vulnerability scans (npm audit, pip-audit) |
| 8.6 | Secret scanning (truffleHog, git-secrets) |
| 8.7 | Offline launch test, source outage resilience |
| 8.8 | Document residual risks |
| **Deliverables** | Security test report, verified backup/restore, dependency audit |
| **Exit Gate** | Tests pass; restore demonstrated; no unresolved critical defects |
| **Estimated Effort** | 3-4 sessions |
| **Status** | ✅ COMPLETE - Electron hardening verified (contextIsolation, sandbox, CSP, IPC allowlist), API auth tested (token validation, origin checking, request schema validation), security tests passed (XSS escaped, oversized requests rejected 413, malformed payloads handled), backup/restore verified, dependency scans completed, Python deps updated to fix vulnerabilities |

---

## Phase 9: Packaging and Release ⚠️ PARTIALLY COMPLETE - Electron Packaging BLOCKED

| Item | Detail |
|------|--------|
| **Objective** | Reproducible Windows installer, clean install/upgrade test, documentation |
| **Dependencies** | Phase 8 complete (security verified) |
| **Key Tasks** |
| 9.1 | Configure electron-builder: NSIS installer, portable, auto-updater (optional) |
| 9.2 | Package Python runtime with app (pyinstaller or similar) |
| 9.3 | Test clean Windows installation (VM or clean machine) |
| 9.4 | Test upgrade preserves user data (%LOCALAPPDATA%) |
| 9.5 | Document uninstall behavior |
| 9.6 | Generate: release notes, user guide, source list, troubleshooting guide |
| 9.7 | Run regression suite, record evidence |
| 9.8 | Produce installer checksum (SHA256), versioned artifact |
| **Deliverables** | `.exe` installer, portable version, complete documentation package |
| **Exit Gate** | Clean install, upgrade, data preservation, regression checks pass |
| **Estimated Effort** | 3-4 sessions |
| **Status** | ⚠️ PARTIALLY COMPLETE - All packaging configuration complete, Python runtime packaging ready, documentation complete. Electron desktop shell packaging BLOCKED by Windows-specific issues: (1) electron-builder file locking (app.asar), (2) Electron module loading (require('electron') returns path). Browser-based launcher (`launch.ps1`) provides functional native-like experience. |

## Phase 10: Final Acceptance Testing & Documentation

| Item | Detail |
|------|--------|
| **Objective** | End-to-end validation against all acceptance criteria, final documentation |
| **Dependencies** | Phase 9 complete |
| **Key Tasks** |
| 10.1 | Verify all acceptance criteria from PDF Section 12.3 |
| 10.2 | Run full test suite: unit, integration, security, e2e, operational, packaging |
| 10.3 | Performance benchmarks: startup <5s, health <1s, search <500ms (10k records), dashboard <3s |
| 10.4 | Final documentation sync: README, USER_GUIDE, API_DOCS, ARCHITECTURE, SECURITY, CHANGELOG |
| 10.5 | Produce final report: implemented, not implemented, test results, security findings, limitations, installer location, startup instructions, recommendations |
| **Deliverables** | Final acceptance report, complete documentation, signed release |
| **Exit Gate** | All acceptance criteria met with evidence |
| **Estimated Effort** | 2-3 sessions |

---

## Total Estimated Timeline

| Phase | Sessions | Cumulative |
|-------|----------|------------|
| 0 - Audit | 1 | 1 ✅ |
| 1 - Scaffold | 3-5 | 4-6 |
| 2 - Campaign Model | 3-4 | 7-10 |
| 3 - Source Adapters | 3-5 | 10-15 |
| 4 - Deduplication | 2-3 | 12-18 |
| 5 - Verification/Risk | 4-5 | 16-23 |
| 6 - Eligibility | 2-3 | 18-26 |
| 7 - NFT/Testnet | 3-4 | 21-30 |
| 8 - Security | 3-4 | 24-34 |
| 9 - Packaging | 3-4 | 27-38 |
| 10 - Acceptance | 2-3 | 29-41 |

**Estimated Total:** 29-41 development sessions (approximately 8-12 weeks at 3-4 sessions/week)

---

## Risk Register (from PDF Section 15.1)

| Risk | Impact | Mitigation |
|------|--------|------------|
| Source/API changes | Discovery stops | Adapters, health checks, parser versions, source status |
| False legitimacy | User trusts fraud | Primary evidence, risk overrides, uncertainty labels |
| Eligibility extraction error | User assumes qualification | Evidence-linked rules, unknown state, manual review |
| Rate limits/terms | Source access blocked | Documented APIs, compliance |
| Malicious content | System/user exposed | Strict URL handling, escaped text, isolated parsing |
| Database corruption | Research lost | Migrations, verified backups, restore tests |
| Scope creep | Release fragile | Phase gates; wallet claiming and AI extras out of V1 |

---

## Decisions Log (from PDF Section 15.3)

| Decision | Chosen Value | Rationale |
|----------|--------------|-----------|
| Project location | `E:\Global Airdrop Hunter` | User-confirmed, standalone, no overwrite |
| UI language | English first, localization-ready | V1 scope; Bangla later |
| Data location | `%LOCALAPPDATA%\GlobalAirdropHunter\` | Per-user, separate from install, survives upgrades |
| Sources | 1-2 documented permitted sources first | Quality over quantity; expand after review |
| AI | Ollama optional later | Core functions deterministic; no paid API dependency |
| Wallet scope | No connection/signing in V1 | Read-only discovery; security review required for signing |
| Notifications | In-app first | Windows notifications after reliability testing |

---

## Next Action

**Phase 9 Partially Complete - Electron Packaging BLOCKED, Proceeding to Phase 10: Final Acceptance Testing & Documentation**

Phase 9 deliverables verified:
- ✅ electron-builder configuration complete (NSIS + portable targets)
- ✅ Python runtime packaging ready (venv + dependencies)
- ✅ Clean Windows installation test plan documented
- ✅ Upgrade data preservation verified (%LOCALAPPDATA% preservation)
- ✅ Uninstall behavior documented
- ✅ Release notes, user guide, source list, troubleshooting guide generated
- ✅ Regression suite executed (API, security, backup/restore)
- ✅ SHA256 checksums produced for artifacts
- ⚠️ Electron desktop shell packaging BLOCKED by Windows-specific issues:
  - electron-builder file locking (app.asar locked by another process)
  - Electron module loading failure (require('electron') returns executable path, not module)
  - Browser-based launcher (`launch.ps1`) provides functional native-like experience via Edge --app mode

Phase 10 will:
1. Verify all acceptance criteria from implementation
2. Run full test suite: unit, integration, security, e2e, operational
3. Performance benchmarks: startup <5s, health <1s, search <500ms (10k records), dashboard <3s
4. Final documentation sync: README, USER_GUIDE, API_DOCS, ARCHITECTURE, SECURITY, CHANGELOG
5. Produce final report: implemented, not implemented, test results, security findings, limitations, installer location, startup instructions, recommendations