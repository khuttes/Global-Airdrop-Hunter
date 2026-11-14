# ELECTRON_INTEGRATION_ISSUES.md

## Electron Integration Issues - Global Airdrop Hunter

**Date:** 2026-11-13
**Status:** BLOCKED - Requires environment resolution

---

## Summary

The Electron desktop shell integration is currently blocked due to fundamental issues with Electron binary distributions on Windows. The backend API, frontend UI, and database are fully functional and tested.

---

## Root Cause

**Electron binaries from GitHub releases and npm package postinstall do not include the internal module system (electron.asar).**

### Details

1. **GitHub Release Binaries**: The official Electron release zips (v20, v22, v28, v30, v45) contain only the minimal binary (`electron.exe`) and supporting DLLs. The `electron.asar` file containing the internal module system (`require('electron')` → `{app, BrowserWindow, ...}`) is **not included**.

2. **npm Package Postinstall**: The `electron` npm package's `install.js` script downloads the same minimal binary from GitHub releases. It does not download a complete distribution with `electron.asar`.

3. **Module System Failure**: When running inside Electron, `require('electron')` returns the path string (`E:\...\electron.exe`) instead of the module object (`{app, BrowserWindow, ...}`). This is because:
   - The npm package's `index.js` intercepts `require('electron')` and returns the executable path
   - The built-in Electron module system (which should be exposed via `electron.asar`) is missing
   - Patching attempts fail because the built-in module is not accessible via `require('electron')` or `Module._load('electron')`

### Tested Versions

| Version | electron.asar in release zip | Postinstall downloads complete dist | Works |
|---------|------------------------------|-------------------------------------|-------|
| 20.3.12 | No | No | No |
| 22.3.27 | No | No | No |
| 28.3.3 | No | No | No |
| 30.5.1 | No | No | No |
| 45.3.1 | No | No | No |

### Attempted Fixes

1. **Multiple Electron versions** (20, 22, 28, 30, 45) - All fail identically
2. **Manual binary extraction** from `@electron/get` cache - Same minimal binary
3. **Patching `node_modules/electron/index.js`** - Cannot access built-in module
2. **Preload patches with `-r` flag** - Built-in module not accessible
3. **Cache clearing and `Module._load`** - Built-in module not registered
4. **electron-builder** - Fails extracting code signing tools (Windows privilege issue with symlinks in macOS binaries)
5. **Chocolatey** - Requires admin rights, package version issues

---

## Working Components (Verified)

✅ **Backend API** (FastAPI on 127.0.0.1:8000)
- Health endpoint: `GET /api/v1/health` → 200 OK
- Dashboard endpoint: `GET /api/v1/dashboard` → 200 OK
- Token authentication working
- CORS configured for localhost

✅ **Database** (SQLite at `%LOCALAPPDATA%\GlobalAirdropHunter\app.db`)
- Schema initialized with 10 tables
- Integrity check: OK
- Migrations applied

✅ **Frontend UI** (HTML/CSS/JS)
- Dashboard shell with navigation
- CSS variables, layout, components, states
- API client, navigation, main app logic

✅ **PowerShell Scripts**
- `setup.ps1` - Environment setup
- `start.ps1` - Start backend + frontend
- `stop.ps1` - Graceful shutdown
- `backup.ps1` - Database backup
- `diagnostics.ps1` - Health checks

---

## Fallback Solution: Browser-Based Launcher

Since Electron is blocked, a functional browser-based launcher has been created that provides a native app-like experience:

### `launch.ps1` - Browser App Mode Launcher

```powershell
# Starts FastAPI backend
# Opens frontend in Microsoft Edge --app mode (chromeless window)
# Provides native app experience without Electron
```

### Usage

```powershell
# From project root
.\scripts\launch.ps1
```

This launches:
1. FastAPI backend on http://127.0.0.1:8000
2. Frontend in Edge `--app=http://127.0.0.1:8000` (chromeless, taskbar icon, native feel)
3. Graceful shutdown on window close

---

## Path Forward

### Option 1: Resolve Electron (Recommended for Production)
- Build Electron from source with full distribution
- Use Electron Forge instead of electron-builder
- Use a pre-built Electron distribution from a trusted source that includes electron.asar
- Run postinstall in a clean environment with proper permissions

### Option 2: Continue with Browser Launcher (Current)
- Develop all backend/frontend features (Phases 2-7) using browser launcher
- Package as Windows app using Edge WebView2 or Tauri later
- Electron packaging deferred to Phase 9

### Option 3: Switch Framework
- Tauri (Rust backend, WebView2 frontend) - smaller, more secure
- WebView2 direct wrapper (C#/PowerShell)
- Neutralino.js (lightweight)

---

## Recommendation

**Proceed with Option 2** - Continue development using the browser-based launcher. All core functionality (Phases 2-7) works independently of Electron. The backend API is the contract; the frontend works in any modern browser. Electron packaging can be resolved in Phase 9 when the application is feature-complete.

This unblocks immediate development progress while maintaining the architectural integrity of the Electron-based design.

---

## Files Created/Modified

- `scripts/launch.ps1` - Browser app mode launcher (fallback)
- `ELECTRON_INTEGRATION_ISSUES.md` - This document
- `desktop/main.js` - Electron main process (blocked)
- `desktop/preload.js` - Secure IPC bridge (ready)
- `backend/main.py` - FastAPI app (working)
- `frontend/index.html` + CSS/JS - Dashboard UI (working)