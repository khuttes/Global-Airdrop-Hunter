# Global Airdrop Hunter — Next Update Roadmap

**Date:** 2026-11-13  
**Based on:** `docs/audit/next_update_baseline.md`  
**Status:** Ready for Phase A approval

---

## Phase Overview

| Phase | Focus | Prerequisites | Est. Effort |
|-------|-------|---------------|-------------|
| **A** | Stabilization | None | 1-2 hrs |
| **B** | Core Runtime Verification | Phase A complete | 4-8 hrs |
| **C** | Automated Testing | Phase B complete | 8-16 hrs |
| **D** | Discovery Integrations | Phase B complete | 8-16 hrs |
| **E** | Campaign Intelligence | Phase D partial | 8-16 hrs |
| **F** | Tracking Features | Phase E partial | 4-8 hrs |
| **G** | Security & Reliability | Phase A complete | 4-8 hrs |
| **H** | Packaging & Release | Phase G complete | 4-8 hrs |

---

## Phase A — Stabilization (P0 Critical Defects)

**Goal:** Electron app launches and communicates with backend reliably.

### Tasks

| Task ID | Priority | Description | Current State | Dependencies | Files Affected | Proposed Solution | Risk | Backup | Acceptance Criteria | Verification |
|---------|----------|-------------|---------------|--------------|----------------|-------------------|------|--------|---------------------|--------------|
| A-E1 | P0 | Fix `crypto.getRandomValues()` in main.js | Crashes on startup | None | `desktop/main.js:5,12-16` | Replace with `crypto.randomBytes(32).toString('hex')` | Low | Full project backup | `generateToken()` returns 64-char hex string | Node REPL test |
| A-E2 | P0 | Fix `require('electron')` returns path string | `app` undefined | None | `desktop/main.js:1` | Use `require('electron/main')` or patch via `-r patch-electron.js` | Medium | Full project backup | `const {app,...} = require('electron')` works | `npm run dev` starts |
| A-E3 | P0 | Merge duplicate `campaigns` in preload.js | `list()`/`get()` lost | None | `desktop/preload.js:50-75` | Single `campaigns` object with `list`, `get`, `save` methods | Low | Full project backup | `window.api.campaigns.list()` works | Browser console test |
| A-E4 | P0 | Resolve token mismatch Electron ↔ Backend | All API calls 401 | A-E1, A-E2 | `desktop/main.js:46-50`, `backend/main.py:28-38` | Backend reads `LOCAL_API_TOKEN` from env, only generates if missing | Low | Full project backup | `GET /api/v1/health` returns 200 from Electron | `npm run dev` → dashboard loads |

### Phase A Exit Criteria
- [ ] `npm run dev` launches Electron window without crash
- [ ] Backend health check passes (green status indicator)
- [ ] Dashboard shows stats (even if zero)
- [ ] Campaigns tab loads table (empty state OK)
- [ ] No console errors in DevTools
- [ ] Settings tab accessible

---

## Phase B — Core Runtime Verification

**Goal:** All existing API routes tested, SQLite operations validated, frontend/backend integration verified.

### Tasks

| Task ID | Priority | Description | Current State | Dependencies | Files Affected | Proposed Solution | Risk | Backup | Acceptance Criteria | Verification |
|---------|----------|-------------|---------------|--------------|----------------|-------------------|------|--------|---------------------|--------------|
| B-T1 | P1 | Manual API endpoint smoke test | All untested | Phase A | All route files | Test each endpoint via `Invoke-RestMethod` or Postman | Low | DB backup | All 22 endpoints return expected status/schema | Test log |
| B-T2 | P1 | Database CRUD verification | Migrations run, untested | Phase A | `backend/database/` | Insert/select/update/delete campaigns, sources, evidence | Low | DB backup | All repository methods work | Script output |
| B-T3 | P1 | Migration runner test | `run_migrations()` exists | Phase A | `backend/database/connection.py:79` | Fresh DB → run migrations → verify all tables | Medium | Fresh DB | 7 migrations apply cleanly | `check_tables.py` |
| B-T4 | P1 | Discovery adapter test | 4 adapters implemented | Phase A | `backend/core/adapters_impl.py` | Run each adapter's `health_check()` and `discover()` | Medium | N/A | All 4 adapters return results/errors | Scan results |
| B-T5 | P1 | Frontend-backend integration | Blocked by Phase A | Phase A | `frontend/js/app.js` | Navigate all 5 tabs, verify data loads | Low | N/A | All modules render without JS errors | Manual test |
| B-T6 | P1 | Application restart test | Not tested | Phase A | All | Kill/restart app 3x, verify state persistence | Low | DB backup | App recovers cleanly each time | Manual test |

### Phase B Exit Criteria
- [ ] All 22 API endpoints return 200/201/204 with valid JSON
- [ ] Database migrations apply cleanly on fresh DB
- [ ] All 4 discovery adapters execute without unhandled exceptions
- [ ] All 5 frontend modules load and display data
- [ ] Application survives 3 cold restarts

---

## Phase C — Automated Testing

**Goal:** Critical workflows have repeatable automated tests.

### Tasks

| Task ID | Priority | Description | Current State | Dependencies | Files Affected | Proposed Solution | Risk | Backup | Acceptance Criteria | Verification |
|---------|----------|-------------|---------------|--------------|----------------|-------------------|------|--------|---------------------|--------------|
| C-T1 | P1 | Python test framework setup | None | Phase B | `backend/requirements.txt`, `pytest.ini`, `conftest.py` | Add pytest, pytest-asyncio, httpx; configure fixtures | Low | N/A | `pytest --collect-only` finds tests | CI log |
| C-T2 | P1 | Backend unit tests | None | C-T1 | `tests/unit/test_*.py` | Test security, models, repositories, deduplication | Low | N/A | >80% coverage on core modules | `pytest --cov` |
| C-T3 | P1 | API integration tests | None | C-T1 | `tests/integration/test_api.py` | Test all 22 endpoints with test DB | Medium | Test DB | All endpoints pass | `pytest tests/integration` |
| C-T4 | P1 | Database migration tests | None | C-T1 | `tests/unit/test_migrations.py` | Test up/down migrations, conflict detection | Medium | Test DB | Migrations apply/rollback cleanly | `pytest` |
| C-T5 | P1 | Discovery adapter unit tests | None | C-T1 | `tests/unit/test_adapters.py` | Mock HTTP, test adapter logic | Low | N/A | All 4 adapters tested | `pytest` |
| C-T6 | P1 | Electron/JS tests | None | C-T1 | `tests/unit/test_frontend.js`, `package.json` | Add Vitest + Playwright for Electron | Medium | N/A | Preload API, app.js functions tested | `npm test` |
| C-T7 | P1 | Security regression tests | None | C-T1 | `tests/security/` | Test auth bypass, CSP, origin validation | Low | N/A | Auth rejects invalid tokens | `pytest tests/security` |
| C-T8 | P1 | E2E test (critical path) | None | C-T3, C-T6 | `tests/end_to_end/` | Playwright: launch → scan → browse campaign | High | Test DB | Full user flow works | Playwright report |
| C-T9 | P1 | CI/CD pipeline | None | C-T1 | `.github/workflows/ci.yml` | GitHub Actions: lint, typecheck, test, build | Medium | N/A | Pipeline passes on PR | GitHub Actions |

### Phase C Exit Criteria
- [ ] `pytest` passes (backend unit + integration)
- [ ] `npm test` passes (frontend unit)
- [ ] Playwright E2E passes critical path
- [ ] GitHub Actions CI runs on push/PR
- [ ] Coverage >70% on backend core modules

---

## Phase D — Discovery Integrations

**Goal:** Integrate spec-required airdrop platforms (Galxe, Layer3) and harden discovery.

### Tasks

| Task ID | Priority | Description | Current State | Dependencies | Files Affected | Proposed Solution | Risk | Backup | Acceptance Criteria | Verification |
|---------|----------|-------------|---------------|--------------|----------------|-------------------|------|--------|---------------------|--------------|
| D-A1 | P2 | Galxe adapter | Not implemented | Phase B | `backend/core/adapters_impl.py`, `adapter_registry.py` | Implement GraphQL API adapter for Galxe campaigns | Medium | N/A | Adapter discovers Galxe campaigns | Scan result |
| D-A2 | P2 | Layer3 adapter | Not implemented | Phase B | `backend/core/adapters_impl.py`, `adapter_registry.py` | Implement Layer3 API/GraphQL adapter | Medium | N/A | Adapter discovers Layer3 campaigns | Scan result |
| D-A3 | P2 | Official site RSS/HTML adapter | RSS exists, needs config | Phase B | `backend/core/adapters_impl.py` | Add pre-configured sources for major projects | Low | N/A | Official announcements discovered | Scan result |
| D-A4 | P1 | Source health monitoring | Basic health check | Phase B | `backend/core/discovery.py`, `source_repository.py` | Track consecutive failures, auto-disable | Low | N/A | Unhealthy sources auto-paused | Scan history |
| D-A5 | P1 | Rate limiting per source | Config exists, not enforced | Phase B | `backend/core/adapters.py`, `adapters_impl.py` | Token bucket / sliding window per source | Medium | N/A | Respects `rate_limit` config | Load test |
| D-A6 | P1 | Request timeouts | 30s default, not per-source | Phase B | `backend/core/adapters.py` | Per-source timeout from config | Low | N/A | Slow sources timeout correctly | Scan result |
| D-A7 | P2 | Record normalization | Partial | Phase B | `backend/core/adapters_impl.py` | Unified CampaignCreate output, stable IDs | Low | N/A | All adapters produce valid CampaignCreate | Unit test |
| D-A8 | P1 | Source evidence capture | Evidence URLs only | Phase B | `backend/core/discovery.py`, `campaign_repository.py` | Store full response snippets, content hashes | Low | N/A | Evidence table populated per campaign | DB check |
| D-A9 | P1 | Scan history tracking | Basic implementation | Phase B | `backend/core/discovery.py` | Include partial failures, per-source stats | Low | N/A | Scan history shows per-source results | API response |

### Phase D Exit Criteria
- [ ] Galxe adapter discovers campaigns from live API
- [ ] Layer3 adapter discovers campaigns from live API
- [ ] All sources respect rate limits and timeouts
- [ ] Scan history shows per-source success/failure
- [ ] Evidence captured for all discovered campaigns

---

## Phase E — Campaign Intelligence

**Goal:** URL normalization, duplicate detection, lifecycle tracking, evidence collection, official verification, risk rules.

### Tasks

| Task ID | Priority | Description | Current State | Dependencies | Files Affected | Proposed Solution | Risk | Backup | Acceptance Criteria | Verification |
|---------|----------|-------------|---------------|--------------|----------------|-------------------|------|--------|---------------------|--------------|
| E-I1 | P2 | URL normalization | Basic in deduplication | Phase D | `backend/core/deduplication.py` | Canonicalize URLs (trailing slash, params, case) | Low | N/A | Same campaign from diff URLs = duplicate | Unit test |
| E-I2 | P2 | Duplicate detection | Stable ID + fuzzy (0.85) | Phase D | `backend/core/deduplication.py`, `campaign_repository.py` | Enhance matching: title similarity, network, deadline | Medium | N/A | >95% duplicate detection on test set | Unit test |
| E-I3 | P2 | Campaign lifecycle | Created/updated/merged/expired | Phase D | `backend/core/discovery.py`, `campaign_repository.py` | Auto-expire past deadline, revive on extension | Low | N/A | Status changes logged in lifecycle_events | DB check |
| E-I4 | P2 | First-seen/last-seen | `discovered_at`, `last_seen_at` | Phase D | `campaign_repository.py:387-424` | Update `last_seen_at` on rediscovery | Low | N/A | `last_seen_at` updates on re-scan | DB check |
| E-I5 | P2 | Expiration detection | Manual via `detect_lifecycle_changes` | Phase D | `campaign_repository.py:570-614` | Scheduled job (APScheduler) daily | Low | N/A | Expired campaigns marked automatically | Scheduler log |
| E-I6 | P2 | Campaign change history | `campaign_field_history` table | Phase D | `campaign_repository.py:452-464` | Record all field changes with source | Low | N/A | Field history queryable per campaign | API test |
| E-I7 | P2 | Evidence collection | URLs stored, not content | Phase D | `backend/core/discovery.py`, `adapters_impl.py` | Fetch and store content hash, snippet, title | Medium | N/A | Evidence has content_hash, snippet | DB check |
| E-I8 | P2 | Official domain verification | Basic in RSS adapter | Phase D | `backend/core/verification.py`, `verification_assessment.py` | Expand official domain list, require primary source | Medium | N/A | Only primary sources = "officially_corroborated" | Unit test |
| E-I9 | P2 | Risk rules engine | 10+ rules implemented | Phase D | `backend/core/risk.py`, `verification_assessment.py` | Add rule versioning, severity calibration | Low | N/A | Rules produce consistent scores | Unit test |
| E-I10 | P3 | False-positive review | Not implemented | E-I8, E-I9 | New UI + API | Manual review queue for suspicious campaigns | Medium | N/A | Reviewer can mark FP, adjust risk | Manual test |

### Phase E Exit Criteria
- [ ] Duplicate detection catches >95% of test duplicates
- [ ] Lifecycle events auto-recorded (create, update, expire, revive)
- [ ] Evidence includes content hash and snippet
- [ ] Official status requires primary source evidence
- [ ] Risk scores consistent across re-scans

---

## Phase F — Tracking Features

**Goal:** Eligibility, geographic restrictions, snapshots, manual progress, NFT/testnet/reward tracking.

### Tasks

| Task ID | Priority | Description | Current State | Dependencies | Files Affected | Proposed Solution | Risk | Backup | Acceptance Criteria | Verification |
|---------|----------|-------------|---------------|--------------|----------------|-------------------|------|--------|---------------------|--------------|
| F-T1 | P2 | Eligibility requirements UI | API ready, no UI | Phase E | `frontend/js/app.js`, `index.html` | Add eligibility section to campaign detail modal | Low | N/A | Requirements display with status badges | Manual test |
| F-T2 | P2 | Geographic restrictions | Model field exists | Phase E | `backend/core/models.py`, `campaign_repository.py` | Add `geo_restrictions` JSON field, UI filter | Low | N/A | Campaigns show restricted regions | Manual test |
| F-T3 | P2 | Snapshot information | `snapshot_date` field | Phase E | `backend/core/models.py`, `campaign_repository.py` | Display snapshot date in detail view | Low | N/A | Snapshot date visible when set | Manual test |
| F-T4 | P2 | Manual progress tracking | `user_tracked` + `user_progress` tables | Phase E | `frontend/js/app.js`, new eligibility routes | Checklist UI for requirements, persist per user | Medium | N/A | User can tick requirements, saved to DB | Manual test |
| F-T5 | P2 | NFT campaign records | Model fields complete | Phase E | `backend/core/models.py`, `campaign_repository.py` | NFT-specific detail view (collection, mint, supply) | Low | N/A | NFT fields display when type=nft | Manual test |
| F-T6 | P2 | Testnet classification | Model fields complete | Phase E | `backend/core/models.py`, `campaign_repository.py` | Testnet badge, chain info, faucet/docs links | Low | N/A | Testnet fields display when type=testnet | Manual test |
| F-T7 | P3 | Reward confirmation status | `reward_*` fields, `CampaignClaim` model | Phase E | New claim routes + UI | Track claim announcements, user confirmation | Medium | N/A | User can mark claim submitted/confirmed | Manual test |
| F-T8 | P3 | Claim announcement tracking | `CampaignEvent` model | Phase E | New event routes + UI | Calendar view for deadlines, claims, distributions | Medium | N/A | Events show in tracking module | Manual test |
| F-T9 | P3 | Deadline notifications | `UserNotificationPrefs` model | Phase E | APScheduler + in-app toast | Notify 1 day before deadline/mint/claim | Medium | N/A | Toast appears at configured interval | Manual test |

### Phase F Exit Criteria
- [ ] Eligibility requirements visible and trackable per campaign
- [ ] NFT/Testnet/Reward detail views show specialized fields
- [ ] User progress persists across app restarts
- [ ] Deadline notifications fire correctly

---

## Phase G — Security & Reliability

**Goal:** Harden Electron, API, URL safety, input validation, DB integrity, verified backups.

### Tasks

| Task ID | Priority | Description | Current State | Dependencies | Files Affected | Proposed Solution | Risk | Backup | Acceptance Criteria | Verification |
|---------|----------|-------------|---------------|--------------|----------------|-------------------|------|--------|---------------------|--------------|
| G-S1 | P1 | Electron security audit | Configured, untested | Phase A | `desktop/main.js`, `preload.js` | Verify CSP, sandbox, context isolation at runtime | Low | N/A | DevTools shows no security violations | Manual test |
| G-S2 | P1 | API access controls | Token auth, origin check | Phase A | `backend/api/middleware/auth.py` | Add rate limiting per token, audit log | Low | N/A | Brute force blocked, auth logged | Load test |
| G-S3 | P1 | URL safety validation | Basic in adapters | Phase E | `backend/core/verification.py` | SSRF protection: block private IPs, localhost in fetched URLs | Medium | N/A | Malicious URLs rejected | Unit test |
| G-S4 | P1 | Input validation hardening | Pydantic models | Phase B | All route files | Add string length limits, regex for known fields | Low | N/A | Oversized/malformed input rejected | Unit test |
| G-S5 | P1 | Database integrity | WAL, FK, no checksums | Phase B | `backend/database/connection.py` | Add PRAGMA integrity_check on startup, backup verify | Low | N/A | Corruption detected on startup | Test corrupt DB |
| G-S6 | P2 | Verified backups | API creates backup file | Phase B | `backend/api/routes/backup.py`, `scripts/backup.ps1` | Add SHA256 manifest, test restore procedure | Medium | Backup files | Restore from backup produces identical DB | Restore test |
| G-S7 | P2 | Restore testing | Not implemented | G-S6 | `scripts/backup.ps1`, new restore script | Automated restore test in CI | Medium | Test DB | CI includes restore verification | CI log |
| G-S8 | P2 | Offline operation | Requires backend | Phase A | `frontend/js/api.js`, `app.js` | Cache last-known data, show stale indicator | Medium | N/A | App shows cached data when backend down | Manual test |
| G-S9 | P2 | Source failure isolation | Partial in discovery | Phase D | `backend/core/discovery.py` | One source failure never blocks others | Low | N/A | Scan completes with partial results | Scan test |
| G-S10 | P2 | Structured logging | Basic `logging.basicConfig` | Phase B | All Python files | JSON logs, correlation IDs, log levels | Low | N/A | Logs parseable, include request IDs | Log check |
| G-S11 | P2 | Secret redaction | No secrets in code | Phase A | All files, CI | Redact tokens in logs, CI masks secrets | Low | N/A | No tokens in logs or artifacts | Log check |

### Phase G Exit Criteria
- [ ] Electron security flags clean in DevTools
- [ ] SSRF protection blocks private IP fetches
- [ ] Backup + restore verified in CI
- [ ] App degrades gracefully when backend offline
- [ ] Structured JSON logs with correlation IDs

---

## Phase H — Packaging & Release

**Goal:** Clean Windows build, installer, upgrade, uninstall tested.

### Tasks

| Task ID | Priority | Description | Current State | Dependencies | Files Affected | Proposed Solution | Risk | Backup | Acceptance Criteria | Verification |
|---------|----------|-------------|---------------|--------------|----------------|-------------------|------|--------|---------------------|--------------|
| H-P1 | P3 | Fix electron-builder file locking | Blocked | Phase G | `package.json`, `patch-electron.js` | Use `asar: false`, `--extra-resources`, pre-pack script | High | N/A | `npm run build` produces installer | Build output |
| H-P2 | P3 | Application startup after install | Not tested | H-P1 | `desktop/main.js` | Verify installed app finds backend, DB, resources | High | Fresh VM | Installed app launches on clean Windows | VM test |
| H-P3 | P3 | Application upgrade | Not tested | H-P1 | `package.json` (nsis config) | Test upgrade path preserves user data | Medium | VM with v1 | Upgrade keeps DB, settings | VM test |
| H-P4 | P3 | User data preservation | %LOCALAPPDATA% used | H-P1 | `desktop/main.js:53`, `backend/config.py:28` | Verify DB not overwritten on upgrade | Low | VM test | DB intact after upgrade | VM test |
| H-P5 | P3 | Uninstall behavior | NSIS default | H-P1 | `package.json` (nsis config) | Remove shortcuts, optional data cleanup | Low | VM test | Clean uninstall, no orphan files | VM test |
| H-P6 | P3 | Dependency packaging | `extraResources` configured | H-P1 | `package.json`, `backend/requirements.txt` | Verify Python + deps bundled correctly | Medium | VM test | Backend runs without system Python | VM test |
| H-P7 | P3 | Release documentation | Drafts exist | H-P1 | `RELEASE_NOTES.md`, `CHANGELOG.md` | Finalize release notes, checksums, sigs | Low | N/A | Release page complete | GitHub release |

### Phase H Exit Criteria
- [ ] `npm run build` succeeds, produces `.exe` and portable
- [ ] Installed app runs on clean Windows 10/11 VM
- [ ] Upgrade preserves user database and settings
- [ ] Uninstall removes all application files
- [ ] Release artifacts signed and documented

---

## Cross-Phase Dependencies

```
Phase A (Stabilization)
    │
    ├─→ Phase B (Core Runtime Verification)
    │       │
    │       ├─→ Phase C (Automated Testing)
    │       │
    │       ├─→ Phase D (Discovery Integrations)
    │       │       └─→ Phase E (Campaign Intelligence)
    │       │               └─→ Phase F (Tracking Features)
    │       │
    │       └─→ Phase G (Security & Reliability)
    │               └─→ Phase H (Packaging & Release)
    │
    └─→ Phase G (Security & Reliability) ──→ Phase H
```

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Electron packaging remains blocked | High | High | Commit to browser fallback (launch.ps1) as primary distribution |
| Galxe/Layer3 APIs change or require auth | Medium | Medium | Design adapters with configurable endpoints, graceful degradation |
| Database migration conflicts on user machines | Low | High | Add migration validation, backup before migrate |
| Security audit reveals fundamental flaw | Low | Critical | Phase G addresses systematically |
| Performance issues with large campaign sets | Medium | Medium | Add pagination, indexing, virtual scrolling |

---

## Resource Estimates

| Phase | Dev Hours | Test Hours | Total |
|-------|-----------|------------|-------|
| A | 2 | 1 | 3 |
| B | 8 | 4 | 12 |
| C | 16 | 8 | 24 |
| D | 16 | 8 | 24 |
| E | 16 | 8 | 24 |
| F | 8 | 4 | 12 |
| G | 8 | 4 | 12 |
| H | 8 | 8 | 16 |
| **Total** | **82** | **45** | **127** |

---

## Approval Gates

| Gate | Required Evidence | Approver |
|------|-------------------|----------|
| Phase A → B | Electron launches, dashboard loads, campaigns list works | User |
| Phase B → C | All 22 API endpoints tested, DB migrations verified | User |
| Phase C → D | CI pipeline passes, coverage >70% | User |
| Phase D → E | Galxe + Layer3 adapters return live data | User |
| Phase E → F | Lifecycle events auto-recorded, evidence has content | User |
| Phase F → G | Tracking features persist, notifications fire | User |
| Phase G → H | Backup/restore verified, SSRF blocked | User |
| Phase H → Release | Installer works on clean VM, upgrade preserves data | User |

---

**Next Action:** Approve Phase A to begin stabilization fixes.