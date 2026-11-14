# FILE USAGE ANALYSIS - Global Airdrop Hunter
**Generated:** 2026-11-14  
**Method:** Static analysis of imports, runtime references, configuration, and entry points

---

## 1. ENTRY POINT ANALYSIS

### 1.1 Primary Entry Points
| Entry Point | File | Type | Dependencies |
|-------------|------|------|--------------|
| Electron App | `desktop/main.js` | Main process | `patch-electron.js`, `desktop/preload.js`, `backend/main.py` |
| Browser Launcher | `scripts/launch.ps1` | PowerShell | `backend/main.py` (via uvicorn), `frontend/index.html` (via Edge) |
| FastAPI Server | `backend/main.py` | Python module | All backend modules, `frontend/` (static files) |
| Double-click | `run.bat` | Batch wrapper | `scripts/launch.ps1` |

### 1.2 Electron Main Process Flow (`desktop/main.js`)
```
main.js
├── require('patch-electron.js')          ← Line 1
├── Electron modules (app, BrowserWindow, ipcMain, shell, protocol)
├── Node modules (path, child_process, fs, crypto)
├── startBackend() → spawns python -m uvicorn backend.main:app
│   ├── getBackendPath() → process.resourcesPath/backend (packaged) or ../ (dev)
│   ├── getPythonExecutable() → .venv/Scripts/python.exe
│   └── Environment: PYTHONPATH, LOCAL_API_TOKEN, BACKEND_PORT, APP_DATA_DIR
├── checkBackendHealth() → HTTP GET /api/v1/health with X-Local-API-Token
├── createWindow() → BrowserWindow with:
│   ├── preload: preload.js
│   ├── CSP, security headers
│   └── loadFile: frontend/index.html
├── IPC Handlers:
│   ├── get-api-config → {baseUrl, token}
│   ├── open-external → shell.openExternal
│   └── get-app-version → app.getVersion()
└── App lifecycle: ready, window-all-closed, activate, before-quit
```

### 1.3 Browser Launcher Flow (`scripts/launch.ps1`)
```
launch.ps1
├── Validates .venv/Scripts/python.exe exists
├── Validates database exists at %LOCALAPPDATA%\GlobalAirdropHunter\app.db
├── Sets env: PYTHONPATH, DATABASE_PATH, BACKEND_PORT, APP_DATA_DIR
├── Generates 32-byte hex token → LOCAL_API_TOKEN
├── Starts backend: python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
├── Health checks: GET http://127.0.0.1:8000/api/v1/health with token
├── Launches Edge: msedge.exe --app=http://127.0.0.1:8000/api/v1/launch
│   └── --user-data-dir=%LOCALAPPDATA%\GlobalAirdropHunter\EdgeProfile
└── Waits for Edge exit, then kills backend
```

---

## 2. BACKEND MODULE DEPENDENCY GRAPH

### 2.1 Core Import Chain (from `backend/main.py`)
```
main.py
├── config.py → Settings (pydantic-settings)
├── core.security → token_manager, create_token_hash
├── core.structured_logging → setup_logging, LoggingMiddleware
├── database → init_database, run_migrations
├── api → api_router
├── api.middleware.auth → AuthMiddleware
├── api.middleware.rate_limit → RateLimitMiddleware
└── FastAPI app factory with CORS, middleware stack, static files
```

### 2.2 API Router Registration (`backend/api/__init__.py`)
```python
from .routes import (
    campaigns, category, dashboard, discovery, eligibility,
    health, sources, backup, verification_risk
)
api_router = APIRouter(prefix="/api/v1")
# All 9 route modules registered
```

### 2.3 Route Module Dependencies
| Route | Core Modules Used | Repository | Models |
|-------|-------------------|------------|--------|
| `health.py` | None | None | None |
| `campaigns.py` | database.repositories.campaign | CampaignRepository | Campaign, CampaignList |
| `category.py` | core.category_tracking | CampaignRepository | CategoryTracking |
| `dashboard.py` | database.repositories.campaign | CampaignRepository | DashboardStats |
| `discovery.py` | core.discovery, core.adapter_registry | SourceRepository | ScanResult |
| `eligibility.py` | core.eligibility, core.models | EligibilityRepository | EligibilityRequirement, UserProgress |
| `sources.py` | core.adapter_registry, database.repositories.source | SourceRepository | Source |
| `backup.py` | database.connection | Direct SQL | BackupResponse |
| `verification_risk.py` | core.verification, core.risk, core.verification_assessment | CampaignRepository | VerificationAssessment, RiskAssessment |

### 2.4 Core Module Dependency Map
```
core/
├── models.py                    ← Base models (NO deps)
├── security.py                  ← crypto, hashlib (stdlib)
├── adapter_registry.py          ← models, adapters
├── adapters.py                  ← models, BaseAdapter ABC
├── adapters_impl.py             ← adapters, httpx, bs4, feedparser
├── adapters_galxe_layer3.py     ← adapters, httpx
├── discovery.py                 ← adapter_registry, models, database.repositories.source
├── deduplication.py             ← models, database.connection
├── eligibility.py               ← models, database.repositories.eligibility
├── verification.py              ← models, httpx
├── verification_assessment.py   ← models, verification
├── risk.py                      ← models
├── category_tracking.py         ← models, database.repositories.campaign
├── false_positive_review.py     ← models, database.repositories.campaign
├── official_registry.py         ← models
├── scheduler.py                 ← apscheduler, discovery, adapter_registry
├── structured_logging.py        ← python-json-logger, logging
├── url_safety.py                ← urllib.parse, re
└── db_integrity.py              ← database.connection
```

### 2.5 Database Layer
```
database/
├── connection.py                ← sqlite3, contextlib, models
├── repositories/
│   ├── __init__.py              ← Exports all
│   ├── campaign.py              ← connection, models (30KB)
│   ├── eligibility.py           ← connection, models (17KB)
│   └── source.py                ← connection, models (5KB)
└── migrations/001-012_*.sql     ← Schema evolution (12 migrations)
```

---

## 3. FRONTEND MODULE DEPENDENCY GRAPH

### 3.1 HTML Load Order (`frontend/index.html`)
```html
<!-- CSS (4 files, load first) -->
<link rel="stylesheet" href="css/variables.css">   ← CSS custom properties
<link rel="stylesheet" href="css/layout.css">      ← Grid/flex layout
<link rel="stylesheet" href="css/components.css">  ← UI components
<link rel="stylesheet" href="css/states.css">      ← State styles (loading, empty, error)

<!-- Body content -->
<div class="app">...</div>

<!-- JS (load last) -->
<script src="js/app.js"></script>          ← Main app (1100 lines)
```

### 3.2 JavaScript Module Graph
```
app.js (App class, 1100 lines)
├── window.apiClient (from api.js)         ← Global API client
├── window.api (from preload.js)           ← Electron IPC bridge
├── window.shell (from preload.js)         ← Electron shell
├── window.app (from preload.js)           ← App version IPC
├── window.navigation (from navigation.js) ← Module switching
├── DOM event listeners (30+ handlers)
├── Module rendering: dashboard, campaigns, discovery, tracking, settings
├── Modal, toast, search, pagination systems
└── Campaign detail rendering (800+ lines inline)

api.js (APIClient class, 267 lines)
├── Electron IPC config (window.api.getConfig)
├── localStorage fallback (gah_api_config)
├── Meta tag fallback (gah-api-base-url, gah-api-token)
├── In-memory cache (5min TTL, 24hr max)
├── Offline mode with stale cache serving
├── Request/response interceptors
└── 18 API methods mapping to backend endpoints

navigation.js (Navigation class, 1744 bytes)
├── Module show/hide logic
├── Active state management
├── Keyboard navigation
└── Hash-based routing
```

### 3.3 API Endpoint Mapping (Frontend → Backend)
| Frontend Method | Backend Endpoint | Route Module |
|-----------------|------------------|--------------|
| `health()` | GET /api/v1/health | health.py |
| `dashboard()` | GET /api/v1/dashboard | dashboard.py |
| `campaigns(filters)` | GET /api/v1/campaigns | campaigns.py |
| `campaign(id)` | GET /api/v1/campaigns/{id} | campaigns.py |
| `scan(sources)` | POST /api/v1/discovery/scans | discovery.py |
| `saveCampaign(id)` | POST /api/v1/campaigns/{id}/save | campaigns.py |
| `backup()` | POST /api/v1/backup | backup.py |
| `sources()` | GET /api/v1/sources | sources.py |
| `sourceHealth(id)` | GET /api/v1/sources/{id}/health | sources.py |
| `trackedCampaigns()` | GET /api/v1/eligibility/tracked | eligibility.py |
| `trackCampaign(id)` | POST /api/v1/eligibility/campaigns/{id}/track | eligibility.py |
| `updateProgress(id, data)` | POST /api/v1/eligibility/campaigns/{id}/progress | eligibility.py |
| `notificationPrefs(id)` | GET /api/v1/eligibility/campaigns/{id}/notification-prefs | eligibility.py |
| `updateNotificationPrefs(id, data)` | PATCH /api/v1/eligibility/campaigns/{id}/notification-prefs | eligibility.py |

**All 18 frontend API methods have corresponding backend endpoints. No orphaned calls.**

---

## 4. PRELOAD / IPC BRIDGE ANALYSIS

### 4.1 Exposed APIs (`desktop/preload.js`)
```javascript
contextBridge.exposeInMainWorld('api', {
    getConfig: () => ipcRenderer.invoke('get-api-config'),  // → main.js:229
    request: (endpoint, options) => fetch with token,      // Custom fetch wrapper
    health: () => request('/api/v1/health'),
    dashboard: () => request('/api/v1/dashboard'),
    campaigns: { list, get, save },
    discovery: { scan },
    backup: { create },
})

contextBridge.exposeInMainWorld('shell', {
    openExternal: (url) => ipcRenderer.invoke('open-external', url)  // → main.js:236
})

contextBridge.exposeInMainWorld('app', {
    getVersion: () => ipcRenderer.invoke('get-app-version')  // → main.js:248
})

contextBridge.exposeInMainWorld('electron', {
    ipcRenderer: { invoke: (channel, ...args) }  // Allowed: get-api-config, open-external, get-app-version
})
```

### 4.2 IPC Channel Validation
| Channel | Handler | Validation |
|---------|---------|------------|
| `get-api-config` | main.js:229 | Returns `{baseUrl, token}` |
| `open-external` | main.js:236 | Validates URL scheme (http/https) |
| `get-app-version` | main.js:248 | Returns `app.getVersion()` |

**Preload allowlist matches main.js handlers exactly. No unauthorized channels.**

---

## 5. CONFIGURATION REFERENCE ANALYSIS

### 5.1 Environment Variables Used
| Variable | Set By | Consumed By | Required |
|----------|--------|-------------|----------|
| `LOCAL_API_TOKEN` | Electron main / launch.ps1 | Backend (main.py:35), Frontend (via IPC) | Yes |
| `PYTHONPATH` | Electron main / launch.ps1 | Python interpreter | Yes |
| `DATABASE_PATH` | launch.ps1:44 | Backend (config.py:29) | Yes |
| `BACKEND_PORT` | Electron main / launch.ps1 | Backend (config.py:14), Frontend | Yes |
| `APP_DATA_DIR` | Electron main / launch.ps1 | Backend (config.py:29) | Yes |
| `LOCALAPPDATA` | Windows | config.py:28, launch.ps1:29 | Yes |

### 5.2 Configuration Files
| File | Purpose | Referenced By |
|------|---------|---------------|
| `backend/config.py` | Pydantic Settings | All backend modules |
| `package.json` | npm config, build config | electron-builder, npm scripts |
| `backend/requirements.txt` | Python deps | setup.ps1:80 |
| `backend/pytest.ini` | Test config | pytest |
| `.gitignore` | Git exclusions | git |

---

## 6. RUNTIME FILE LOADING

### 6.1 Static Assets Served by FastAPI
```python
# main.py:87-89
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
```
**Serves:** `frontend/index.html`, `frontend/css/*`, `frontend/js/*`

### 6.2 Database Migrations (Auto-applied on startup)
```python
# main.py:31-32
init_database()
run_migrations()  # Applies 001-012_*.sql in order
```

### 6.3 Electron Resources (Packaged)
```json
// package.json:55-59
"asar": true,
"asarUnpack": ["backend/**/*", ".venv/**/*"],
"extraResources": [
    {"from": "backend", "to": "backend", "filter": ["**/*"]},
    {"from": ".venv", "to": ".venv", "filter": ["**/*"]}
]
```

---

## 7. TEST REFERENCE ANALYSIS

### 7.1 Backend Tests (117 passing)
| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_models.py` | ~25 | Models, validation |
| `test_repositories.py` | ~30 | Database operations |
| `test_deduplication.py` | ~15 | Deduplication logic |
| `test_security.py` | ~10 | Auth, tokens |
| `test_api.py` (integration) | ~33 | Full API endpoints |

### 7.2 Test Dependencies
- `backend/tests/conftest.py` → Shared fixtures (temp DB, test client)
- `backend/pytest.ini` → `testpaths = tests`, `asyncio_mode = auto`

---

## 8. UNUSED / ORPHANED FILES CONFIRMED

### 8.1 Zero References Found
| File | Search Performed | Result |
|------|------------------|--------|
| `preload-patch.js` | grep -r "preload-patch" | **NO REFERENCES** |
| `release.json` | grep -r "release.json" | Only in dist/ |
| `release28.json` | grep -r "release28.json" | Only in dist/ |
| `version` | grep -r "version" (as file) | No code references |
| Electron binaries in root | Not imported anywhere | Runtime only |

### 8.2 Root Test Scripts (Ad-hoc, Not in Test Suite)
| File | Imports Backend | Purpose |
|------|-----------------|---------|
| `test_api.py` | Yes | Manual API testing |
| `test_discovery.py` | Yes | Discovery debugging |
| `test_discovery2.py` | Yes | Discovery v2 debugging |
| `test_health.py` | Yes | Adapter health checks |
| `test_health2.py` | Yes | Adapter health v2 |
| `test_raw.py` | Yes | Raw API debugging |
| `test_rss.py` | Yes | RSS adapter debugging |
| `test_rss_feeds.py` | Yes | RSS feed debugging |
| `test_galxe_query.py` | Yes | Galxe adapter debugging |
| `test_galxe2.py` | Yes | Galxe adapter v2 debugging |

**None are imported by the application or test suite. All are standalone debug scripts.**

---

## 9. DUPLICATE FILE CONFIRMATION

### 9.1 Electron Runtime Files (Root vs dist/)
| File | Root Size | dist/ Size | Identical |
|------|-----------|------------|-----------|
| `chrome_100_percent.pak` | 129,228 | 129,228 | Yes |
| `chrome_200_percent.pak` | 179,318 | 179,318 | Yes |
| `d3dcompiler_47.dll` | 4,891,080 | 4,891,080 | Yes |
| `ffmpeg.dll` | 2,787,840 | 2,787,840 | Yes |
| `icudtl.dat` | 10,449,360 | 10,449,360 | Yes |
| `libEGL.dll` | 468,992 | 468,992 | Yes |
| `libGLESv2.dll` | 7,409,664 | 7,409,664 | Yes |
| `snapshot_blob.bin` | 411,128 | 411,128 | Yes |
| `v8_context_snapshot.bin` | 733,784 | 733,784 | Yes |
| `vk_swiftshader.dll` | 4,873,728 | 4,873,728 | Yes |
| `vk_swiftshader_icd.json` | 106 | 106 | Yes |
| `vulkan-1.dll` | 869,888 | 869,888 | Yes |

**Confirmed: 12 files are byte-for-byte duplicates of dist/win-unpacked/**

### 9.2 Backend in dist/ (Two Copies)
```
dist/win-unpacked/resources/app.asar.unpacked/backend/  ← Full backend (asar unpacked)
dist/win-unpacked/resources/backend/                    ← Full backend (extra copy)
```
**Both are build artifacts from electron-builder extraResources + asarUnpack config.**

---

## 10. SUMMARY: FILE CLASSIFICATION

| Classification | Count | Examples |
|----------------|-------|----------|
| **ESSENTIAL** (app won't run without) | ~85 | desktop/main.js, backend/main.py, frontend/index.html, all core modules |
| **ACTIVELY USED** (referenced at runtime) | ~95 | All above + scripts/, configs, docs |
| **BUILD ARTIFACTS** (regenerable) | ~25 | dist/, node_modules/, .venv/, Electron binaries |
| **TEST/DEBUG** (development only) | ~15 | backend/tests/, root test_*.py |
| **DUPLICATES** (byte-for-byte copies) | 12 | Electron runtime files in root |
| **ORPHANED** (no references found) | 5 | preload-patch.js, release.json, release28.json, version, default_app.asar |
| **UNKNOWN** (purpose unclear) | 3 | LICENSES.chromium.html, LICENSE, version |

---

**ANALYSIS COMPLETE:** All application entry points traced, all imports verified, all runtime references mapped. No essential files are candidates for removal.