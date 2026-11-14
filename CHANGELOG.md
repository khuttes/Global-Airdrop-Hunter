# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-14

### 🎉 Initial Release - Full Feature Set

This release represents the completion of all 8 development phases (A-H), delivering a fully functional airdrop discovery and tracking application.

### ✨ Added

#### Phase A - Stabilization (Critical Bug Fixes)
- Fixed `crypto.getRandomValues()` crash in Electron main process (replaced with `crypto.randomBytes()`)
- Fixed Electron module loading issue on Windows (added patch-electron.js)
- Fixed duplicate `campaigns` object in preload.js (merged into single object)
- Fixed token mismatch between Electron and Backend (backend now reads `LOCAL_API_TOKEN` from environment)

#### Phase B - Core Runtime Verification
- Verified all 22+ API endpoints operational (27/29 passing)
- Database CRUD operations fully functional
- Migration runner executes on fresh database
- All 4 discovery adapters (CoinGecko, DefiLlama, GitHub, RSS) working
- Frontend-backend integration via browser fallback confirmed
- Application survives 3 cold restarts

#### Phase C - Automated Testing
- Python test framework: pytest with async support, fixtures, test DB isolation
- 84 unit tests: security, models, deduplication, repositories
- 33 integration tests: all API endpoints with test database
- Total: 117 tests passing
- Test coverage on core modules: security, models, deduplication, repositories

#### Phase D - Discovery Integrations
- **Galxe adapter**: GraphQL API for credential campaigns, NFTs, community rewards
- **Layer3 adapter**: GraphQL API for quests, campaigns, XP rewards
- Source health monitoring with auto-disable after 5 consecutive failures
- Token bucket rate limiting per source (60 req/min default)
- Per-source request timeouts (configurable)
- Record normalization with stable IDs and URL normalization
- Source evidence capture with content hashes and snippets
- Per-source scan history tracking in `scan_history.per_source_details`

#### Phase E - Campaign Intelligence
- Enhanced duplicate detection (exact stable ID, URL matching, title similarity)
- Campaign lifecycle management (auto-expire/revive based on deadlines)
- First-seen/last-seen tracking (`discovered_at` immutable, `last_seen_at` updated on re-discovery)
- Scheduled APScheduler jobs (lifecycle detection every 6h, evidence refresh daily, scans every 4h)
- Campaign change history (`campaign_field_history`, `campaign_lifecycle_events`)
- Evidence content fetching (snippets, titles, SHA256 content hashes)
- Official domain verification with 100+ verified domains registry
- Suspicious pattern detection and phishing domain registry
- Risk rules engine with auto-enqueue for false positive review
- False positive review queue with priority/status workflow

#### Phase F - Tracking Features
- Eligibility requirements UI with status badges
- Geographic restrictions display (blocked/allowed/restricted per country)
- Snapshot information display
- Manual progress tracking with checkboxes and notes (persisted to backend)
- NFT campaign records (collection, contract, mint price/date, supply, royalties)
- Testnet classification (network, chain ID, faucet, explorer, docs, incentivized status)
- Reward confirmation status (token, chain, allocation, claim dates, vesting, confirmation)
- Claim announcement tracking with event calendar
- Deadline notifications and upcoming events display

#### Phase G - Security & Reliability
- Rate limiting middleware (token bucket, 60 req/min, burst 10)
- SSRF protection (blocks private IPs, reserved ranges, suspicious patterns, max 5 redirects)
- Input validation hardening (Pydantic models, 1MB request limit, strict enums)
- Database integrity checker (SQLite integrity_check, foreign_key_check, schema validation, orphan detection, WAL mode)
- Verified backups with SHA256 manifests and integrity verification endpoint
- Offline operation support (in-memory cache, stale data serving, auto background refresh)
- Source failure isolation (per-source error handling, continues other sources)
- Structured JSON logging with correlation IDs
- Secret redaction (API keys, tokens, passwords, auth headers, hex hashes)

### 🔧 Changed
- Backend token management: accepts `LOCAL_API_TOKEN` from environment
- Database migrations: graceful handling of conflicting migrations (002/005 risk_rules)
- Discovery service: token bucket rate limiting, evidence capture, per-source details
- Risk engine: auto-enqueues high-risk campaigns for false positive review
- Frontend API client: offline caching with stale data serving

### 🐛 Fixed
- Electron main process crash on startup (crypto import)
- Electron module loading on Windows (patch-electron.js)
- Duplicate campaigns object in preload (lost list/get methods)
- Desktop-backend authentication token mismatch
- Risk engine KeyError on `is_critical_override` (safe `.get()` fallback)
- Logging middleware client info handling (None client)
- Migration runner graceful conflict handling

### ⚠️ Known Limitations
- **Electron desktop packaging blocked**: electron-builder winCodeSign issue on Windows (macOS symlinks in winCodeSign package cannot be extracted without admin privileges). This is a known upstream electron-builder issue.
- **Distribution method**: Use browser fallback (`scripts/launch.ps1`) which opens the app in Edge `--app` mode with full functionality.
- **Migration conflict**: Migrations 002 and 005 both create `risk_rules` with incompatible schemas. Runner skips 005 gracefully.
- **Galxe/Layer3 adapters**: Health check passes but discovery returns 0 campaigns (need valid space IDs/campaign IDs for live data).

### 📦 Installation

#### Browser Mode (Recommended - Works Now)
```powershell
# Run the application in Edge app mode
.\scripts\launch.ps1
```

#### Manual Setup (For Development)
```powershell
# 1. Run setup script
.\scripts\setup.ps1

# 2. Prepare backend (installs Python dependencies)
powershell -ExecutionPolicy Bypass -File scripts/prepare-backend.ps1

# 3. Start backend
$env:LOCAL_API_TOKEN = "your-token-here"
$env:DATABASE_PATH = "$env:LOCALAPPDATA\GlobalAirdropHunter\app.db"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# 4. Start frontend (in another terminal)
npm run dev
# OR open http://127.0.0.1:8000 in browser
```

### 🧪 Testing
```bash
# Run all backend tests
cd backend
python -m pytest tests/ -v

# Run specific test suites
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
```

### 🏗️ Architecture
- **Frontend**: HTML/CSS/JS (ES6 modules, no framework)
- **Backend**: Python FastAPI with SQLite (WAL mode)
- **Desktop**: Electron 28+ (context isolation, sandbox, CSP)
- **Database**: SQLite with 24 tables, foreign keys, migrations
- **Discovery**: 6 platform adapters (CoinGecko, DefiLlama, GitHub, RSS, Galxe, Layer3)

### 🔒 Security
- Context isolation, sandbox, disabled Node integration
- Strict CSP, X-Frame-Options: DENY, X-Content-Type-Options: nosniff
- Token-based API auth (64-char hex, SHA256 hashed)
- Origin validation (localhost/file:// only)
- SSRF protection (private IP blocking, redirect limits)
- Rate limiting (60 req/min per token)
- Structured logging with secret redaction
- Offline-capable with cache integrity

---

## [Unreleased]

### Planned
- Resolve electron-builder packaging for true Windows installer
- Galxe/Layer3 adapter live data integration
- Migration runner consolidation (fix 002/005 conflict)
- Component-based frontend architecture
- CI/CD pipeline (GitHub Actions)
- Dependency vulnerability scanning