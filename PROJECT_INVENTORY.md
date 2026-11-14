# PROJECT INVENTORY - Global Airdrop Hunter
**Generated:** 2026-11-14  
**Scope:** Complete forensic audit of all project files (excluding node_modules and .venv internals)

---

## 1. PROJECT STRUCTURE OVERVIEW

```
E:\Global Airdrop Hunter\
├── .git/                           # Git repository (21 commits)
├── .gitignore                      # Git ignore rules (76 lines)
├── .kilo/                          # Kilo configuration directory
├── .venv/                          # Python virtual environment (excluded from git)
├── backend/                        # Python FastAPI backend
│   ├── api/                        # API routes and middleware
│   ├── config.py                   # Settings configuration
│   ├── core/                       # Core business logic (20 modules)
│   ├── database/                   # Database connection, migrations, repositories
│   ├── main.py                     # FastAPI entry point
│   ├── requirements.txt            # Python dependencies (14 packages)
│   ├── tests/                      # Backend tests (unit + integration)
│   └── pytest.ini                  # Pytest configuration
├── build/                          # Build resources
│   └── icon.ico                    # Application icon
├── desktop/                        # Electron main process
│   ├── main.js                     # Electron main process (250 lines)
│   └── preload.js                  # Secure preload script (99 lines)
├── dist/                           # Electron build output (excluded from git)
│   ├── builder-debug.yml
│   └── win-unpacked/               # Full packaged application
├── docs/                           # Documentation
│   └── audit/                      # Audit reports (10 files)
├── electron.exe                    # Electron binary (151MB) - NOT IN GIT
├── electron.zip                    # Electron archive (94MB) - NOT IN GIT
├── electron_cache/                 # Electron cache (excluded)
├── electron_temp/                  # Electron temp (excluded)
├── frontend/                       # Vanilla JS frontend
│   ├── css/                        # Stylesheets (4 files, 60KB)
│   ├── index.html                  # Main HTML (436 lines)
│   └── js/                         # JavaScript modules
│       ├── api.js                  # API client with caching (267 lines)
│       ├── app.js                  # Main application (1100 lines)
│       └── navigation.js           # Navigation handler (1744 bytes)
├── locales/                        # Electron locales (excluded)
├── node_modules/                   # npm dependencies (excluded from git)
├── package.json                    # npm package config (90 lines)
├── package-lock.json               # npm lockfile (146KB)
├── patch-electron.js               # Electron module patcher (40 lines)
├── preload-patch.js                # Additional preload patch (1.6KB)
├── resources/                      # Electron resources
│   └── default_app.asar            # Default Electron app (109KB)
├── run.bat                         # Windows launcher (645 bytes)
├── scripts/                        # Build/launch scripts
│   ├── backup.ps1                  # Database backup script
│   ├── create_demo_fixtures.py     # Demo data generator
│   ├── diagnostics.ps1             # System diagnostics
│   ├── launch.ps1                  # Browser app mode launcher (122 lines)
│   ├── prepare-backend.js          # Backend preparation (JS)
│   ├── prepare-backend.ps1         # Backend preparation (PS1)
│   ├── setup.ps1                   # First-time setup (136 lines)
│   ├── start.ps1                   # Start application
│   └── stop.ps1                    # Stop application
├── SECURITY.md                     # Security documentation
├── SECURITY_AUDIT.md               # Security audit report
├── test_*.py                       # Root-level test scripts (11 files)
├── tests/                          # Frontend/E2E tests (empty directories)
├── USER_GUIDE.md                   # User guide
└── Various Electron binaries       # chrome_*.pak, d3dcompiler_47.dll, etc.
```

---

## 2. ESSENTIAL APPLICATION FILES (MUST KEEP)

### 2.1 Core Entry Points
| File | Purpose | Evidence |
|------|---------|----------|
| `desktop/main.js` | Electron main process, backend spawning, window creation | Referenced in package.json main field |
| `desktop/preload.js` | Secure IPC bridge for renderer | Loaded via webPreferences.preload in main.js |
| `backend/main.py` | FastAPI application factory | Spawned by desktop/main.js:35 |
| `scripts/launch.ps1` | Browser app mode launcher | Primary launch mechanism (run.bat calls this) |
| `run.bat` | Double-click launcher | Project root, user-facing entry point |

### 2.2 Backend Core Modules (All Referenced)
| Module | Used By | Evidence |
|--------|---------|----------|
| `backend/config.py` | All backend modules | Imported in main.py:10, security.py, structured_logging.py |
| `backend/core/security.py` | Auth middleware, token management | main.py:11, auth.py |
| `backend/core/structured_logging.py` | Logging middleware | main.py:12, 82 |
| `backend/database/connection.py` | Database access | Imported by repositories |
| `backend/database/migrations/001-012_*.sql` | Schema initialization | run_migrations() in main.py:32 |
| `backend/api/routes/*.py` (9 files) | API endpoints | Registered in api/__init__.py |
| `backend/core/*.py` (20 files) | Business logic | Imported by routes and services |

### 2.3 Frontend Assets
| File | Purpose | Evidence |
|------|---------|----------|
| `frontend/index.html` | Main HTML entry point | Loaded by main.js:191,194 and served by FastAPI static files |
| `frontend/js/app.js` | Main application controller | Loaded by index.html:434 |
| `frontend/js/api.js` | API client with caching | Imported by app.js (global window.apiClient) |
| `frontend/js/navigation.js` | Module navigation | Imported by app.js:66 |
| `frontend/css/*.css` (4 files) | Styling | Linked in index.html:8-11 |

### 2.4 Configuration & Build
| File | Purpose | Evidence |
|------|---------|----------|
| `package.json` | npm config, build config | Required for electron-builder |
| `package-lock.json` | Dependency lockfile | Required for reproducible builds |
| `backend/requirements.txt` | Python dependencies | Used by setup.ps1:80 |
| `backend/pytest.ini` | Test configuration | Required for test execution |
| `scripts/setup.ps1` | Environment setup | User-facing setup script |
| `build/icon.ico` | Application icon | Referenced in package.json:75 and main.js:144 |

---

## 3. FILES WITH EVIDENCE OF ACTIVE USE

### 3.1 Scripts (Referenced by package.json or launch flow)
| File | Referenced By |
|------|---------------|
| `scripts/prepare-backend.ps1` | package.json:12 ("prepare-backend" script) |
| `scripts/prepare-backend.js` | Alternative JS version |
| `scripts/start.ps1` | User workflow |
| `scripts/stop.ps1` | User workflow |
| `scripts/backup.ps1` | Called from frontend (settings backup button) |
| `scripts/diagnostics.ps1` | Called from frontend (diagnostics button) |

### 3.2 Test Files (Backend - 117 tests passing)
| File | Purpose |
|------|---------|
| `backend/tests/conftest.py` | Pytest fixtures |
| `backend/tests/unit/test_*.py` (4 files) | Unit tests |
| `backend/tests/integration/test_api.py` | Integration tests |

### 3.3 Documentation (Project Knowledge)
| File | Purpose |
|------|---------|
| `README.md` | Project overview |
| `USER_GUIDE.md` | User documentation |
| `SECURITY.md` | Security model |
| `CHANGELOG.md` | Release history |
| `docs/audit/*.md` (10 files) | Audit & validation reports |

---

## 4. DUPLICATE / REDUNDANT FILES

### 4.1 Electron Binaries in Project Root (NOT IN GIT)
| File | Size | Duplicate Of |
|------|------|--------------|
| `electron.exe` | 151.8 MB | `dist/win-unpacked/electron.exe` (not present, but in node_modules) |
| `electron.zip` | 94.2 MB | Downloaded artifact |
| `chrome_100_percent.pak` | 129 KB | `dist/win-unpacked/chrome_100_percent.pak` |
| `chrome_200_percent.pak` | 179 KB | `dist/win-unpacked/chrome_200_percent.pak` |
| `d3dcompiler_47.dll` | 4.9 MB | `dist/win-unpacked/d3dcompiler_47.dll` |
| `ffmpeg.dll` | 2.8 MB | `dist/win-unpacked/ffmpeg.dll` |
| `icudtl.dat` | 10.4 MB | `dist/win-unpacked/icudtl.dat` |
| `libEGL.dll` | 469 KB | `dist/win-unpacked/libEGL.dll` |
| `libGLESv2.dll` | 7.4 MB | `dist/win-unpacked/libGLESv2.dll` |
| `snapshot_blob.bin` | 411 KB | `dist/win-unpacked/snapshot_blob.bin` |
| `v8_context_snapshot.bin` | 734 KB | `dist/win-unpacked/v8_context_snapshot.bin` |
| `vk_swiftshader.dll` | 4.9 MB | `dist/win-unpacked/vk_swiftshader.dll` |
| `vk_swiftshader_icd.json` | 106 B | `dist/win-unpacked/vk_swiftshader_icd.json` |
| `vulkan-1.dll` | 870 KB | `dist/win-unpacked/vulkan-1.dll` |

**Total duplicate Electron runtime: ~184 MB**

### 4.2 Duplicate Backend in dist/
| Path | Status |
|------|--------|
| `dist/win-unpacked/resources/app.asar.unpacked/backend/` | Full copy of backend/ |
| `dist/win-unpacked/resources/backend/` | Another full copy of backend/ |

**These are build artifacts, not source files.**

### 4.3 Duplicate Test Scripts (Root Level)
| File | Duplicate Of | Notes |
|------|--------------|-------|
| `test_api.py` | Backend integration tests | Ad-hoc test script |
| `test_discovery.py` | Discovery testing | Ad-hoc test script |
| `test_discovery2.py` | Discovery testing v2 | Ad-hoc test script |
| `test_health.py` | Health check testing | Used for adapter health checks |
| `test_health2.py` | Health check testing v2 | Ad-hoc test script |
| `test_raw.py` | Raw API testing | Ad-hoc test script |
| `test_rss.py` | RSS adapter testing | Ad-hoc test script |
| `test_rss_feeds.py` | RSS feed testing | Ad-hoc test script |
| `test_galxe_query.py` | Galxe adapter testing | Ad-hoc test script |
| `test_galxe2.py` | Galxe adapter testing v2 | Ad-hoc test script |

**11 root-level test scripts, mostly ad-hoc/debugging scripts**

### 4.4 Database Test Files
| File | Size | Notes |
|------|------|-------|
| `test_fresh.db` | 311 KB | Test database artifact |
| `test_fresh3.db` | 401 KB | Test database artifact |

### 4.5 Patch Files (Potentially Redundant)
| File | Size | Notes |
|------|------|-------|
| `patch-electron.js` | 1.5 KB | Loaded by main.js:1 |
| `preload-patch.js` | 1.6 KB | Not referenced anywhere |

---

## 5. GENERATED / REPRODUCIBLE FILES (SAFE TO CLEAN)

### 5.1 Build Artifacts (Excluded by .gitignore)
| Path | Size | Regenerable |
|------|------|-------------|
| `dist/` | ~400 MB | `npm run build` |
| `node_modules/` | ~2 GB | `npm install` |
| `.venv/` | ~500 MB | `scripts/setup.ps1` |

### 5.2 Python Cache
| Path | Size | Regenerable |
|------|------|-------------|
| `backend/__pycache__/` | ~200 KB | Auto-generated |
| `backend/**/__pycache__/` | ~500 KB | Auto-generated |
| `backend/.pytest_cache/` | ~10 KB | Auto-generated |

### 5.3 Electron Cache/Temp
| Path | Size | Regenerable |
|------|------|-------------|
| `electron_cache/` | ~50 MB | Auto-generated |
| `electron_temp/` | ~10 MB | Auto-generated |
| `locales/` | ~20 MB | Bundled with Electron |

---

## 6. FILES OF UNKNOWN / UNCLEAR PURPOSE

| File | Size | Investigation Needed |
|------|------|---------------------|
| `preload-patch.js` | 1.6 KB | Not imported anywhere, may be orphaned |
| `release.json` | 115 KB | Electron-builder output? |
| `release28.json` | 115 KB | Electron-builder output? |
| `version` | 7 bytes | Unknown content |
| `LICENSE` | 1 KB | Standard MIT license |
| `LICENSES.chromium.html` | 6.6 MB | Chromium license (bundled with Electron) |
| `resources/default_app.asar` | 109 KB | Electron default app |

---

## 7. FILES THAT MUST NEVER BE DELETED

| Category | Files | Reason |
|----------|-------|--------|
| **User Data** | `%LOCALAPPDATA%\GlobalAirdropHunter\app.db` | User's campaign database |
| **Database Migrations** | `backend/database/migrations/001-012_*.sql` | Schema history, required for init |
| **Environment Config** | `.venv/pyvenv.cfg`, `.env` (if exists) | Runtime configuration |
| **Security** | `SECURITY.md`, `SECURITY_AUDIT.md` | Security documentation |
| **Git History** | `.git/` | Version control |
| **Lockfiles** | `package-lock.json` | Reproducible builds |

---

## 8. DEPENDENCY ANALYSIS

### 8.1 Python Dependencies (requirements.txt - 14 packages)
| Package | Version | Used By | Status |
|---------|---------|---------|--------|
| fastapi | 0.109.1 | main.py, all routes | **Essential** |
| uvicorn[standard] | 0.30.6 | main.py:108, launch.ps1 | **Essential** |
| pydantic | 2.11.3 | config.py, models.py | **Essential** |
| pydantic-settings | 2.9.1 | config.py | **Essential** |
| httpx | 0.27.2 | adapters_impl.py | **Essential** |
| beautifulsoup4 | 4.12.3 | adapters_impl.py (HTML parsing) | **Essential** |
| apscheduler | 3.11.0 | core/scheduler.py | **Essential** |
| python-dotenv | 1.2.2 | config.py (BaseSettings) | **Essential** |
| alembic | 1.14.1 | database migrations | **Essential** |
| pytest | 8.3.5 | Testing | **Dev only** |
| pytest-asyncio | 0.26.0 | Async tests | **Dev only** |
| aiohttp | 3.14.4 | test scripts, adapters | **Essential** |
| feedparser | 6.0.11 | RSS adapters | **Essential** |
| python-json-logger | 2.0.7 | structured_logging.py | **Essential** |

**All 14 packages are actively used. No unused dependencies.**

### 8.2 Node.js Dependencies (package.json - 2 devDependencies)
| Package | Version | Used By | Status |
|---------|---------|---------|--------|
| electron | ^28.3.3 | Runtime | **Essential** |
| electron-builder | ^24.0.0 | Packaging | **Build only** |

**Minimal, clean dependency tree. No unused packages.**

---

## 9. CLEANUP RECOMMENDATIONS

### 9.1 IMMEDIATE SAFE CLEANUP (High Confidence)

| # | File/Directory | Size | Reason | Recovery |
|---|----------------|------|--------|----------|
| 1 | `electron.exe` | 151.8 MB | Electron binary duplicate, not in git | `npm install` |
| 2 | `electron.zip` | 94.2 MB | Downloaded archive, not in git | Re-download |
| 3 | `chrome_100_percent.pak` | 129 KB | Runtime duplicate in dist/ | `npm run build` |
| 4 | `chrome_200_percent.pak` | 179 KB | Runtime duplicate in dist/ | `npm run build` |
| 5 | `d3dcompiler_47.dll` | 4.9 MB | Runtime duplicate in dist/ | `npm run build` |
| 6 | `ffmpeg.dll` | 2.8 MB | Runtime duplicate in dist/ | `npm run build` |
| 7 | `icudtl.dat` | 10.4 MB | Runtime duplicate in dist/ | `npm run build` |
| 8 | `libEGL.dll` | 469 KB | Runtime duplicate in dist/ | `npm run build` |
| 9 | `libGLESv2.dll` | 7.4 MB | Runtime duplicate in dist/ | `npm run build` |
| 10 | `snapshot_blob.bin` | 411 KB | Runtime duplicate in dist/ | `npm run build` |
| 11 | `v8_context_snapshot.bin` | 734 KB | Runtime duplicate in dist/ | `npm run build` |
| 12 | `vk_swiftshader.dll` | 4.9 MB | Runtime duplicate in dist/ | `npm run build` |
| 13 | `vk_swiftshader_icd.json` | 106 B | Runtime duplicate in dist/ | `npm run build` |
| 14 | `vulkan-1.dll` | 870 KB | Runtime duplicate in dist/ | `npm run build` |
| 15 | `electron_cache/` | ~50 MB | Electron cache, regenerated | Auto |
| 16 | `electron_temp/` | ~10 MB | Electron temp, regenerated | Auto |
| 17 | `locales/` | ~20 MB | Bundled with Electron | `npm install` |
| 18 | `test_fresh.db` | 311 KB | Test artifact | Re-run tests |
| 19 | `test_fresh3.db` | 401 KB | Test artifact | Re-run tests |
| 20 | `preload-patch.js` | 1.6 KB | Not referenced anywhere | Git history |
| 21 | `release.json` | 115 KB | Build artifact | `npm run build` |
| 22 | `release28.json` | 115 KB | Build artifact | `npm run build` |
| 23 | `version` | 7 B | Unknown, likely build artifact | Git history |

**Total recoverable space: ~184 MB**

### 9.2 REVIEW REQUIRED (Medium Confidence)

| # | File/Directory | Size | Reason | Notes |
|---|----------------|------|--------|-------|
| 1 | Root `test_*.py` (11 files) | ~15 KB | Ad-hoc test scripts | May be useful for debugging; consider moving to `scripts/` or `backend/tests/debug/` |
| 2 | `scripts/create_demo_fixtures.py` | 15 KB | Demo data generator | Useful for development; keep |
| 3 | `LICENSES.chromium.html` | 6.6 MB | Chromium license | Bundled in dist anyway; can remove from root |
| 4 | `resources/default_app.asar` | 109 KB | Electron default app | Not used (we have custom app) |
| 5 | `backend/.pytest_cache/` | 10 KB | Test cache | Auto-regenerated |

### 9.3 DO NOT DELETE (Zero Confidence for Removal)

| File/Directory | Reason |
|----------------|--------|
| `dist/` | Build output - user may need for distribution |
| `node_modules/` | Required for Electron runtime |
| `.venv/` | Required for Python backend |
| All backend source files | Core application |
| All frontend source files | Core application |
| All desktop source files | Core application |
| All scripts/ | Operational tooling |
| All documentation | Project knowledge |
| Database migrations | Schema integrity |
| Git repository | Version control |

---

## 10. SUMMARY STATISTICS

| Metric | Value |
|--------|-------|
| **Total project files (excl. node_modules/.venv)** | ~180 |
| **Essential source files** | ~85 |
| **Build artifacts / duplicates** | ~25 (184 MB) |
| **Test/debug scripts (root)** | 11 |
| **Documentation files** | ~15 |
| **Configuration files** | ~10 |
| **Python dependencies** | 14 (all used) |
| **Node.js dependencies** | 2 (both used) |
| **Backend tests** | 117 passing (84 unit + 33 integration) |

---

## 11. APPROVAL-READY CLEANUP PLAN

### Phase 1: Remove Electron Runtime Duplicates (Safe)
```powershell
# These are NOT in git, safe to remove
Remove-Item electron.exe, electron.zip, chrome_100_percent.pak, chrome_200_percent.pak,
           d3dcompiler_47.dll, ffmpeg.dll, icudtl.dat, libEGL.dll, libGLESv2.dll,
           snapshot_blob.bin, v8_context_snapshot.bin, vk_swiftshader.dll,
           vk_swiftshader_icd.json, vulkan-1.dll -Force
Remove-Item electron_cache, electron_temp, locales -Recurse -Force
```

### Phase 2: Remove Build Artifacts (Safe)
```powershell
Remove-Item release.json, release28.json, version -Force
Remove-Item test_fresh.db, test_fresh3.db -Force
```

### Phase 3: Remove Orphaned Files (Review First)
```powershell
# preload-patch.js - NOT REFERENCED ANYWHERE
Remove-Item preload-patch.js -Force

# resources/default_app.asar - NOT USED
Remove-Item resources/default_app.asar -Force

# LICENSES.chromium.html - BUNDLED IN DIST
Remove-Item LICENSES.chromium.html -Force
```

### Phase 4: Organize Root Test Scripts (Optional)
```powershell
# Move ad-hoc test scripts to scripts/debug/ or backend/tests/debug/
New-Item -ItemType Directory -Path scripts/debug -Force
Move-Item test_*.py scripts/debug/ -Force
```

### Phase 5: Clean Python Cache (Auto-regenerates)
```powershell
Remove-Item backend\**\__pycache__ -Recurse -Force
Remove-Item backend\.pytest_cache -Recurse -Force
```

---

**Total estimated cleanup: ~185 MB + organization**

**All removals are reversible via:** `npm install`, `scripts/setup.ps1`, or git history.