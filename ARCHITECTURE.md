# Global Airdrop Hunter - Architecture Documentation

## System Overview

Global Airdrop Hunter is a Windows desktop application for discovering, tracking, and analyzing cryptocurrency airdrop campaigns. It follows a local-first architecture with a clear separation between the Electron frontend and FastAPI backend.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Global Airdrop Hunter                     │
├─────────────────────────────────────────────────────────────────┤
│  Electron Frontend (Renderer Process)                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  HTML5/CSS3/Vanilla JS                                    │  │
│  │  • Dashboard, Campaigns, Discovery, Tracking, Settings    │  │
│  │  • Secure IPC via contextBridge                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                     │
│                            ▼ IPC (allowlisted channels)         │
│  Electron Main Process                                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Window management                                      │  │
│  │  • Backend process spawning                               │  │
│  │  • Security policies (CSP, sandbox, contextIsolation)     │  │
│  │  • IPC handlers (get-api-config, open-external, etc.)     │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                     │
│                            ▼ HTTP/REST (localhost:8000)         │
│  FastAPI Backend (Separate Process)                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  • Campaign CRUD & discovery                              │  │
│  │  • Verification & risk assessment                         │  │
│  │  • Eligibility & progress tracking                        │  │
│  │  • Source management & adapters                           │  │
│  │  • SQLite persistence                                     │  │
│  │  • Token-based authentication                             │  │
│  └───────────────────────────────────────────────────────────┘  │
│                            │                                     │
│                            ▼                                     │
│  SQLite Database (%LOCALAPPDATA%\GlobalAirdropHunter\app.db)   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Details

### Electron Frontend

#### Main Process (`desktop/main.js`)
- Creates BrowserWindow with hardened security settings
- Spawns FastAPI backend as child process
- Manages application lifecycle
- Handles IPC communication

#### Preload Script (`desktop/preload.js`)
- Exposes secure APIs via `contextBridge`
- Allowlisted IPC channels only
- Provides `api`, `shell`, `app` namespaces

#### Renderer (Frontend)
- **index.html**: Single-page application shell
- **CSS**: Modular architecture (variables, layout, components, states)
- **JavaScript**: Modular ES6 modules
  - `api.js`: API client with token auth
  - `navigation.js`: Module routing
  - `app.js`: Main application controller

### FastAPI Backend

#### Core Modules
```
backend/
├── main.py                 # FastAPI app, lifespan, middleware
├── config.py               # Pydantic Settings
├── core/
│   ├── models.py           # Pydantic models & enums
│   ├── security.py         # Token management
│   ├── adapters.py         # Source adapter interfaces
│   ├── adapter_registry.py # Adapter factory
│   ├── discovery.py        # Scan orchestration
│   ├── verification.py     # Domain verification
│   ├── verification_assessment.py # Verification logic
│   ├── risk.py             # Risk scoring engine
│   ├── eligibility.py      # Eligibility extraction & tracking
│   └── category_tracking.py # NFT/Testnet/Reward/Events/Notifications
├── api/
│   ├── middleware/auth.py  # Token auth + origin checking
│   └── routes/
│       ├── health.py
│       ├── dashboard.py
│       ├── campaigns.py
│       ├── sources.py
│       ├── discovery.py
│       ├── verification_risk.py
│       ├── eligibility.py
│       ├── category.py
│       └── backup.py
├── database/
│   ├── connection.py       # SQLite connection pool
│   ├── migrations/         # SQL migrations
│   └── repositories/
│       ├── campaign.py
│       ├── source.py
│       └── eligibility.py
└── scripts/                # PowerShell automation
```

#### Database Schema
Key tables:
- `campaigns` - Core campaign data + category-specific fields
- `campaign_evidence` - Supporting evidence with content hashes
- `campaign_risk_findings` - Risk rule triggers
- `campaign_eligibility` - Structured requirements
- `campaign_field_history` - Audit trail for field changes
- `user_tracked` - User's tracked campaigns
- `user_notes` - Personal notes
- `campaign_claims` - Claim tracking with tx hashes
- `campaign_events` - Calendar events with reminders
- `user_notification_prefs` - Per-campaign notification settings
- `campaign_merge_audit` - Deduplication audit trail
- `campaign_lifecycle_events` - Status change history
- `sources` - Discovery source registry
- `scan_history` - Scan execution history
- `campaign_categories` - Category reference data
- `blockchains` - Network reference data
- `risk_rules` - Configurable risk rules
- `schema_migrations` - Migration tracking

### Security Architecture

#### Electron Hardening
- `contextIsolation: true` - Isolates preload from renderer
- `nodeIntegration: false` - No Node.js in renderer
- `sandbox: true` - Chromium sandbox enabled
- `webSecurity: true` - Same-origin policy enforced
- CSP headers injected via `webRequest.onHeadersReceived`
- `webContents.setWindowOpenHandler` - Blocks unwanted navigation
- `will-navigate` handler - Prevents navigation away from localhost

#### IPC Security
- Preload script exposes only allowlisted channels
- `get-api-config`, `open-external`, `get-app-version`
- Renderer cannot access Node.js or Electron APIs directly
- All communication via `contextBridge.exposeInMainWorld`

#### API Security
- Token-based authentication (`X-Local-API-Token` header)
- Token generated at startup (32 bytes, hex-encoded)
- Origin validation (only `http://127.0.0.1:*`, `http://localhost:*`, `file://`)
- Request size limit: 1 MB (413 for oversized)
- Input validation via Pydantic models
- CORS restricted to localhost/file:// origins

#### Data Protection
- SQLite database in user-local `%LOCALAPPDATA%`
- No cloud sync, no telemetry
- Backup/restore with integrity checks (PRAGMA integrity_check)
- No wallet connections, no private keys, no signing

### Data Flow

#### Campaign Discovery
1. User clicks **Scan** in Discovery module
2. Frontend calls `POST /api/v1/discovery/scans`
3. DiscoveryService:
   - Gets enabled sources (or specified subset)
   - Creates adapter for each source
   - Runs health check
   - Executes `discover()` concurrently (max 3 parallel)
   - Normalizes results to CampaignCreate objects
   - Deduplicates via stable_id (project+name+network hash)
   - Updates existing or creates new campaigns
   - Records scan history
4. Frontend refreshes campaign list

#### Campaign Verification
1. User clicks **Verify** or auto-triggered
2. VerificationService:
   - Analyzes evidence (primary vs secondary sources)
   - Checks domain verification (WHOIS, SSL, DNS)
   - Applies verification state machine
   - Updates campaign.verification_status
3. RiskEngine:
   - Loads active risk rules
   - Evaluates each rule against campaign data
   - Calculates weighted risk score (0-100)
   - Applies critical overrides
   - Stores findings with rule references

#### Deduplication
- Stable ID: SHA256(project|name|network)[:16]
- Matching criteria (in priority order):
  1. Exact stable_id match
  2. Official URL or campaign URL match
  3. Title similarity > 0.85 + same network
  4. Project similarity > 0.85 + same network + deadline within 1 day
- On match: merge evidence, risk findings, eligibility; update last_seen_at
- Audit trail in `campaign_merge_audit` table

#### Eligibility Tracking
- Auto-extraction from campaign text (regex patterns)
- Categories: region, network, activity, snapshot, tasks, deadline, holding, NFT
- Statuses: unknown, confirmed, not_met, user_reported_met, not_applicable
- User progress: unknown, met, not_met, in_progress, not_applicable
- Progress statuses: potentially_eligible, user_reported_met, user_reported_not_met, not_applicable, claim_available, claimed

### Configuration

#### Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `LOCAL_API_TOKEN` | Auto-generated | API authentication token |
| `DATABASE_PATH` | `%LOCALAPPDATA%\GlobalAirdropHunter\app.db` | SQLite path |
| `BACKEND_PORT` | 8000 | Backend HTTP port |
| `APP_DATA_DIR` | `%LOCALAPPDATA%\GlobalAirdropHunter` | Data directory |
| `PYTHONPATH` | Project root | Python module resolution |

#### Settings (User-configurable)
Stored in database `settings` table:
| Key | Default | Description |
|-----|---------|-------------|
| theme | dark | dark/light/system |
| auto_refresh_minutes | 30 | Dashboard refresh interval |
| notifications_enabled | 1 | Global notification toggle |

### Deployment

#### Build Process
```bash
# Development
npm run dev          # Electron with DevTools
npm run start        # Electron production

# Build
npm run build        # NSIS installer + portable
npm run build:portable # Portable only
npm run build:dir    # Unpacked directory only
```

#### Installer Output
- `dist/GlobalAirdropHunter-1.0.0-setup.exe` (NSIS)
- `dist/GlobalAirdropHunter-1.0.0-portable.exe` (Portable)

#### Packaging Notes
- ASAR disabled (`"asar": false`) to avoid Windows file locking
- Python runtime bundled via `extraResources`
- Extra resources: backend/, scripts/, package.json
- NSIS: user-selectable install directory, desktop/Start Menu shortcuts
- Portable: self-contained, no installation required

### Known Limitations

1. **Electron Packaging on Windows**: 
   - electron-builder file locking issues with app.asar
   - Electron module loading issues (require('electron') returns path)
   - Workaround: Browser-based launcher (`launch.ps1`) using Edge `--app` mode

2. **Source Discovery**:
   - Limited to documented public APIs
   - Respects rate limits and ToS
   - No scraping bypassing auth/CAPTCHA

3. **Verification**:
   - Automated verification limited to publicly verifiable sources
   - Manual review required for edge cases
   - Third-party listings never confer official status automatically

4. **Eligibility**:
   - No wallet connection or on-chain verification
   - User-self-reported progress only
   - No inference from undisclosed personal data

### Future Extensibility

#### Adding New Sources
1. Create new adapter class extending `SourceAdapter`
2. Register in `adapter_registry.py`
3. Add source via API or database
4. Configure rate limits, timeouts, config schema

#### Adding Risk Rules
```sql
INSERT INTO risk_rules (id, rule_id, version, name, description, category, severity, weight, is_critical_override, logic_type, logic_config)
VALUES ('rr-new', 'new_rule', 1, 'Name', 'Description', 'security', 'high', 50, 0, 'keyword', '{"keywords": ["bad", "words"]}');
```

#### Adding Campaign Categories
1. Add fields to Campaign model
2. Add columns via migration
3. Update repository create/update
4. Add API endpoints in category router
4. Add frontend panel in category router

### Testing Strategy

#### Test Categories
- Unit: Repository methods, service logic, risk rules
- Integration: API endpoints, database operations
- Security: Auth middleware, CSP, IPC allowlist
- E2E: Critical user flows (scan, verify, track, claim)

#### Test Commands
```bash
# Backend
pytest backend/tests/

# Frontend (manual)
npm run dev

# Security
pip-audit -r backend/requirements.txt
npm audit
```

### Monitoring & Observability

#### Logging
- Backend: Python logging to console + rotating file
- Frontend: Console.log + Electron IPC logs
- Levels: DEBUG, INFO, WARNING, ERROR

#### Health Checks
- `GET /api/v1/health` - Backend + database
- Source health checks on each scan
- `POST /api/v1/sources/{id}/health` - Manual trigger

#### Metrics (Implicit)
- Scan duration, campaigns found/updated/errors
- API response times (via uvicorn access logs)
- Database size, backup success/failure

---

*Architecture version: 1.0.0*
*Last updated: 2026-11-13*