# Global Airdrop Hunter

<p align="center">
  <img src="assets/banner.png" alt="Global Airdrop Hunter Banner" width="800"/>
</p>

<p align="center">
  <a href="#features"><strong>Features</strong></a> •
  <a href="#screenshots"><strong>Screenshots</strong></a> •
  <a href="#installation"><strong>Installation</strong></a> •
  <a href="#quick-start"><strong>Quick Start</strong></a> •
  <a href="#architecture"><strong>Architecture</strong></a> •
  <a href="#development"><strong>Development</strong></a> •
  <a href="#security"><strong>Security</strong></a> •
  <a href="#contributing"><strong>Contributing</strong></a> •
  <a href="#license"><strong>License</strong></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows%2010%2F11-blue?style=flat-square&logo=windows" alt="Platform"/>
  <img src="https://img.shields.io/badge/Electron-28.x-47848F?style=flat-square&logo=electron" alt="Electron"/>
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python" alt="Python"/>
  <img src="https://img.shields.io/badge/FastAPI-0.110-009688?style=flat-square&logo=fastapi" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/SQLite-3.45-003B57?style=flat-square&logo=sqlite" alt="SQLite"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License"/>
  <img src="https://img.shields.io/badge/Version-1.0.0-orange?style=flat-square" alt="Version"/>
</p>

---

A **Windows desktop application** for discovering, tracking, and analyzing cryptocurrency airdrop campaigns. Built with security-first architecture using Electron + FastAPI.

## 📋 Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [System Requirements](#system-requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [User Guide](#user-guide)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Development](#development)
- [Security](#security)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Changelog](#changelog)
- [License](#license)

---

## ✨ Features

### 🔍 Campaign Discovery
| Source | Description | Status |
|--------|-------------|--------|
| **CoinGecko** | Top gainers, new listings, trending tokens | ✅ Active |
| **DeFiLlama** | Protocol launches, incentive programs | ✅ Active |
| **GitHub** | New repository monitoring for crypto projects | ✅ Active |
| **RSS Feeds** | Curated crypto news & announcement feeds | ✅ Active |
| **Custom APIs** | Extensible source plugin system | 🔧 Extensible |

### 📊 Campaign Management
- **Full CRUD** — Create, read, update, delete campaigns
- **Advanced Filtering** — By status, chain, category, risk level, verification
- **Smart Search** — Full-text search across name, description, tags
- **Pagination** — Efficient loading for large datasets
- **Bulk Operations** — Multi-select actions (export, tag, delete)

### 🛡️ Verification Intelligence
```
┌─────────────────┬────────────────────────────────────────────┐
│ Classification  │ Criteria                                   │
├─────────────────┼────────────────────────────────────────────┤
│ 🟢 Official     │ Verified team, audit reports, mainnet live │
│ 🔵 Independent  │ Community-verified, reputable backers      │
│ 🟡 Unverified   │ No public verification, proceed with care  │
│ 🔴 Suspicious   │ Red flags: anon team, copy-paste, honeypot │
└─────────────────┴────────────────────────────────────────────┘
```
- Evidence tracking with source URLs and timestamps
- Confidence scoring (0-100%)
- Manual override with audit trail

### ⚠️ Risk Assessment Engine
**15 automated rules** across 5 categories:

| Category | Rules | Critical Override |
|----------|-------|-------------------|
| **Financial** | Upfront payment, token purchase required, gas fees excessive | 🔴 Block |
| **Credential** | Private key request, seed phrase, wallet connect abuse | 🔴 Block |
| **Technical** | Unverified contract, proxy without admin, honeypot patterns | 🟠 Warn |
| **Operational** | Anonymous team, copied whitepaper, fake partnerships | 🟠 Warn |
| **Timeline** | Unrealistic deadlines, vague roadmap, no testnet | 🟡 Caution |

**Risk Score**: 0-100 (Lower = Safer)

### ✅ Eligibility Tracking
Structured requirement system:
```
Campaign: Arbitrum Odyssey
├── 📋 Bridge $100+ to Arbitrum          [MET ✅]
├── 📋 Complete 5 transactions           [IN_PROGRESS 🔄 3/5]
├── 📋 Use 3 different protocols         [NOT_MET ❌]
└── 📋 Hold ARB for 30 days              [NOT_MET ❌]
```
- Progress persistence across sessions
- Automatic validation where possible
- Custom requirement templates

### 🎁 Claim Tracking
| Claim Type | Fields | Verification |
|------------|--------|--------------|
| **Airdrop** | Amount, token, tx hash, block explorer | On-chain lookup |
| **NFT Mint** | Collection, token ID, tx hash, metadata | OpenSea/API |
| **Reward Claim** | Protocol, amount, tx hash, reward type | Protocol API |
| **Testnet Reward** | Faucet, tasks completed, testnet tx | Explorer |

### 📅 Calendar & Notifications
- **Event Types**: Snapshot, claim window, distribution, snapshot, deadline
- **Reminders**: 1h, 24h, 7d before event (configurable)
- **Channels**: In-app toast, system notification, email (optional)
- **Per-Campaign Preferences**: Granular opt-in/out

### 🎨 User Experience
- **Themes**: Light / Dark / System (auto)
- **Responsive Layout**: Adaptive sidebar, collapsible panels
- **Keyboard Shortcuts**: Power-user navigation
- **Data Export**: JSON, CSV, PDF reports
- **Offline Mode**: Cached data with sync queue

---

## 📸 Screenshots

<p align="center">
  <strong>Dashboard Overview</strong><br/>
  <img src="assets/screenshots/dashboard.png" alt="Dashboard" width="700"/><br/><br/>
  
  <strong>Campaign Discovery</strong><br/>
  <img src="assets/screenshots/discovery.png" alt="Discovery" width="700"/><br/><br/>
  
  <strong>Eligibility Tracking</strong><br/>
  <img src="assets/screenshots/eligibility.png" alt="Eligibility" width="700"/><br/><br/>
  
  <strong>Risk Analysis Detail</strong><br/>
  <img src="assets/screenshots/risk-analysis.png" alt="Risk Analysis" width="700"/>
</p>

> **Note**: Screenshots are placeholders. Run the app to see the actual UI.

---

## 💻 System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **OS** | Windows 10 64-bit (1909+) | Windows 11 64-bit |
| **RAM** | 4 GB | 8 GB+ |
| **Storage** | 500 MB free | 1 GB+ (for cache/db) |
| **CPU** | x64, 2 cores | x64, 4+ cores |
| **Network** | Broadband | Broadband (for discovery) |
| **Display** | 1366×768 | 1920×1080+ |

**Included in Installer**:
- Python 3.12 (embedded, isolated)
- Node.js runtime (Electron)
- SQLite database engine

---

## 📥 Installation

### Option 1: Installer (Recommended)
```powershell
# 1. Download from GitHub Releases
#    https://github.com/your-org/Global-Airdrop-Hunter/releases/latest

# 2. Run the installer
.\GlobalAirdropHunter-1.0.0-setup.exe

# 3. Launch from Start Menu or Desktop shortcut
```

**Installer Details**:
- Installs to `%LOCALAPPDATA%\Programs\GlobalAirdropHunter`
- Creates Start Menu entry & Desktop shortcut
- Registers uninstaller in Windows Apps & Features
- Auto-updates via GitHub Releases (optional)

### Option 2: Portable Version
```powershell
# Download portable zip, extract anywhere, run GlobalAirdropHunter.exe
# No admin rights required, no registry changes
```

### Option 3: Microsoft Store (Coming Soon)
```powershell
# Search "Global Airdrop Hunter" in Microsoft Store
# Automatic updates, sandboxed installation
```

---

## 🚀 Quick Start

### First Launch
```
┌─────────────────────────────────────────────────────────────┐
│  Welcome to Global Airdrop Hunter!                          │
│                                                              │
│  🔍 Run Initial Discovery Scan?  [Yes] [No, I'll configure] │
│                                                              │
│  ⚙️  Configure Sources & Settings    [Skip for now]         │
└─────────────────────────────────────────────────────────────┘
```

### 3-Minute Setup
1. **Run Discovery** — Click "Scan Now" on Dashboard or go to Discovery tab
2. **Review Campaigns** — Browse results, check verification badges
3. **Track Eligibility** — Click a campaign → "Track Progress" → mark requirements
4. **Set Reminders** — Enable notifications for claim windows/snapshots
5. **Export Data** — Settings → Export → Choose format (CSV/JSON/PDF)

---

## 📖 User Guide

### Dashboard
Central command center showing:
- **Stats Cards**: Total campaigns, tracking, upcoming claims, risk alerts
- **Upcoming Events**: Next 7 days of snapshots, claims, deadlines
- **Risk Heatmap**: Visual risk distribution across tracked campaigns
- **Quick Actions**: Scan now, add campaign, export report

### Campaigns Tab
```
┌────────────────────────────────────────────────────────────────┐
│ 🔍 Search...          │ Filter: ▼ Status ▼ Chain ▼ Risk ▼ Verif│
├────────────────────────────────────────────────────────────────┤
│ ☐ Arbitrum Odyssey    │ 🟢 Official │ 🟢 Low Risk  │ 5 reqs    │
│ ☐ zkSync Era          │ 🔵 Indep.   │ 🟡 Medium    │ 3 reqs    │
│ ☐ Linea Voyage        │ 🟡 Unver.   │ 🟠 High      │ 7 reqs    │
│ ☐ Suspicious Project  │ 🔴 Susp.    │ 🔴 CRITICAL  │ —         │
└────────────────────────────────────────────────────────────────┘
```
- **Sort**: Click column headers (multi-column with Shift)
- **Bulk**: Checkbox select → toolbar actions
- **Detail**: Double-click or "View" button

### Discovery Tab
- **Source Configuration**: Enable/disable, set API keys, rate limits
- **Scan History**: Previous runs with results summary
- **Scheduled Scans**: Cron-like scheduler (daily, weekly, custom)
- **Manual Trigger**: "Scan Now" with progress indicator

### Tracking Tab
- **My Campaigns**: Only campaigns you're actively tracking
- **Progress View**: Visual progress bars per requirement
- **Claim Log**: History of submitted claims with tx hashes
- **Calendar View**: Month view of all tracked events

### Settings
| Section | Options |
|---------|---------|
| **Appearance** | Theme, density, language, startup view |
| **Notifications** | Channels, timing, per-campaign defaults |
| **Discovery** | Sources, schedule, auto-scan on startup |
| **Security** | API token, auto-lock, data encryption |
| **Advanced** | Log level, cache size, proxy, debug mode |
| **Data** | Export, import, backup, reset |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ELECTRON MAIN PROCESS                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ Window Mgmt │  │ IPC Handler │  │ Auto-Updater│              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          │                │                │
    ┌─────▼─────┐    ┌─────▼─────┐    ┌─────▼─────┐
    │ Preload   │    │  Secure   │    │  Python   │
    │ Script    │───▶│  IPC Bridge│   │  Spawner  │
    └───────────┘    └─────┬─────┘    └─────┬─────┘
                           │                │
              ┌────────────┼────────────────┼────────────┐
              │            │                │            │
        ┌─────▼─────┐ ┌────▼────┐    ┌─────▼─────┐ ┌────▼────┐
        │ Renderer  │ │  SQLite │    │  FastAPI  │ │ Discovery│
        │  (UI)     │ │  (DB)   │    │  (API)    │ │ Workers  │
        └───────────┘ └─────────┘    └───────────┘ └──────────┘
```

### Technology Stack
| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Frontend** | HTML5 / CSS3 / Vanilla JS | — | Renderer process UI |
| **Desktop Shell** | Electron | 28.x | Cross-platform desktop |
| **Backend API** | FastAPI | 0.110 | REST API on localhost:8000 |
| **Database** | SQLite | 3.45 | Local data persistence |
| **Language** | Python | 3.12 | Backend & discovery workers |
| **Packaging** | electron-builder | 24.x | Installer & auto-update |

### Data Flow
```
User Action (UI)
      │
      ▼
Preload Script (contextBridge)
      │
      ▼
IPC Main Process (allowlisted channels)
      │
      ▼
FastAPI (localhost:8000, token auth)
      │
      ▼
SQLite / Discovery Workers / External APIs
      │
      ▼
Response → IPC → Preload → UI Update
```

### Database Schema (Key Tables)
```sql
campaigns           -- Core campaign data
campaign_sources    -- Discovery source tracking
verification_evidence -- Verification audit trail
risk_assessments    -- Risk rule evaluations
eligibility_requirements -- Structured requirements
user_progress       -- Per-user requirement status
claims              -- Claim tracking with tx hashes
events              -- Calendar events & reminders
notifications       -- Notification preferences & history
settings            -- User configuration
scan_history        -- Discovery run logs
```

---

## ⚙️ Configuration

### Config File Location
```
%LOCALAPPDATA%\GlobalAirdropHunter\config.json
```

### Example Configuration
```json
{
  "theme": "system",
  "language": "en",
  "api": {
    "port": 8000,
    "token": "auto-generated-on-first-run",
    "cors": ["http://localhost:3000"]
  },
  "discovery": {
    "sources": {
      "coingecko": { "enabled": true, "rate_limit": 30 },
      "defillama": { "enabled": true, "rate_limit": 60 },
      "github": { "enabled": true, "token": "ghp_xxx" },
      "rss": { "enabled": true, "feeds": ["..."] }
    },
    "schedule": "0 */6 * * *",
    "auto_scan_on_startup": true
  },
  "notifications": {
    "channels": ["toast", "system"],
    "reminders": ["1h", "24h", "7d"],
    "per_campaign": {}
  },
  "security": {
    "auto_lock_minutes": 30,
    "encrypt_database": false,
    "log_level": "INFO"
  },
  "advanced": {
    "cache_size_mb": 500,
    "proxy": null,
    "debug": false
  }
}
```

### Environment Variables (Development)
```powershell
$env:GAH_API_PORT=8000
$env:GAH_LOG_LEVEL=DEBUG
$env:GAH_DB_PATH="C:\custom\path\app.db"
$env:GAH_DISABLE_AUTO_UPDATE=1
```

---

## 🛠️ Development

### Prerequisites
```powershell
# Required
Node.js 18+          # https://nodejs.org
Python 3.12+         # https://python.org
Git                  # https://git-scm.com

# Optional but recommended
VS Code              # https://code.visualstudio.com
Docker Desktop       # For containerized testing
```

### Setup
```powershell
# 1. Clone
git clone https://github.com/your-org/Global-Airdrop-Hunter.git
cd Global-Airdrop-Hunter

# 2. Run automated setup (installs deps, builds, configures)
.\scripts\setup.ps1

# 3. Start development (hot reload)
.\scripts\launch.ps1
```

### Project Structure
```
Global-Airdrop-Hunter/
├── src/
│   ├── main/                 # Electron main process
│   │   ├── index.ts          # Entry point
│   │   ├── ipc/              # IPC handlers
│   │   ├── python/           # Python spawner & management
│   │   ├── security/         # CSP, token auth, validation
│   │   └── updater/          # Auto-update logic
│   ├── preload/              # Preload script (contextBridge)
│   └── renderer/             # Frontend (Vanilla JS)
│       ├── assets/           # CSS, icons, fonts
│       ├── components/       # Reusable UI components
│       ├── pages/            # Page modules (Dashboard, Campaigns, etc.)
│       ├── services/         # API client, storage, events
│       └── utils/            # Helpers, constants, types
├── python/                   # FastAPI backend
│   ├── app/
│   │   ├── api/              # Route handlers
│   │   ├── core/             # Config, security, database
│   │   ├── models/           # SQLAlchemy models
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   └── workers/          # Discovery, risk, verification
│   ├── requirements.txt
│   └── pyproject.toml
├── scripts/                  # Build & dev scripts
│   ├── setup.ps1
│   ├── launch.ps1
│   ├── build.ps1
│   └── test.ps1
├── assets/                   # Icons, installer assets
├── tests/                    # Unit & integration tests
├── docs/                     # Additional documentation
├── package.json
├── tsconfig.json
└── electron-builder.yml
```

### Common Commands
```powershell
# Development
.\scripts\launch.ps1              # Start dev (hot reload)
.\scripts\launch.ps1 --no-python  # Frontend only (mock API)

# Building
.\scripts\build.ps1               # Production build
.\scripts\build.ps1 --portable    # Portable zip
.\scripts\build.ps1 --store       # MSIX for Microsoft Store

# Testing
.\scripts\test.ps1                # All tests
.\scripts\test.ps1 --unit         # Unit only
.\scripts\test.ps1 --e2e          # E2E (Playwright)
.\scripts\test.ps1 --coverage     # With coverage report

# Python Backend Only
cd python
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Database
.\scripts\db.ps1 migrate          # Run migrations
.\scripts\db.ps1 seed             # Seed test data
.\scripts\db.ps1 reset            # Drop & recreate
```

### Code Style
```powershell
# Linting
npm run lint          # ESLint (frontend)
npm run lint:fix      # Auto-fix
cd python && ruff check .  # Python lint
cd python && ruff format . # Python format

# Type Checking
npm run typecheck     # TypeScript
cd python && mypy app/     # Python
```

---

## 🔒 Security

### Defense in Depth
```
┌────────────────────────────────────────────────────────────────┐
│                    SECURITY LAYERS                              │
├────────────────────────────────────────────────────────────────┤
│  1. ELECTRON HARDENING                                         │
│     ✓ Context Isolation          ✓ Sandbox Enabled             │
│     ✓ NodeIntegration: false     ✓ Preload Only                │
│     ✓ WebSecurity: true          ✓ AllowPopups: false          │
├────────────────────────────────────────────────────────────────┤
│  2. CONTENT SECURITY POLICY                                    │
│     default-src 'self'; script-src 'self';                      │
│     style-src 'self' 'unsafe-inline'; img-src 'self' data:;    │
│     connect-src http://localhost:8000; frame-ancestors 'none'; │
├────────────────────────────────────────────────────────────────┤
│  3. IPC SECURITY                                               │
│     ✓ Allowlisted Channels Only  ✓ Schema Validation (Zod)    │
│     ✓ No Remote Code Execution   ✓ Rate Limited                │
├────────────────────────────────────────────────────────────────┤
│  4. API SECURITY                                               │
│     ✓ Token Authentication       ✓ Localhost-Only Binding     │
│     ✓ Request Size Limit (1MB)   ✓ Input Sanitization         │
│     ✓ CORS Restricted            ✓ Helmet.js Headers          │
├────────────────────────────────────────────────────────────────┤
│  5. DATA PROTECTION                                            │
│     ✓ SQLite WAL Mode            ✓ Prepared Statements        │
│     ✓ Optional DB Encryption     ✓ No Telemetry/Tracking      │
│     ✓ Local-First (No Cloud)     ✓ User Controls Data         │
└────────────────────────────────────────────────────────────────┘
```

### Threat Model
| Threat | Mitigation |
|--------|------------|
| **XSS via Campaign Data** | CSP + sanitization + context isolation |
| **Malicious IPC Calls** | Allowlist + schema validation |
| **API Token Theft** | Auto-generated, localhost-only, short-lived |
| **Supply Chain** | Locked dependencies, SBOM, signed releases |
| **Data Exfiltration** | No network access from renderer, API localhost-only |

### Reporting Security Issues
**Do not open public issues.** Email: `security@your-domain.com`  
PGP Key: Available on [KEYBASE](https://keybase.io/your-handle)  
Response: Within 48 hours, patch within 7 days for critical issues.

---

## 🐛 Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| **"Python not found"** | Embedded Python failed to extract | Reinstall, run as admin once |
| **API connection refused** | Port 8000 in use / firewall | Check `netstat -ano \| findstr 8000`, allow in firewall |
| **Blank/white screen** | GPU acceleration issue | Launch with `--disable-gpu` flag |
| **Discovery not working** | Network / API keys / rate limit | Check logs, verify API keys, wait for rate limit reset |
| **Database locked** | Multiple instances running | Close all instances, check Task Manager |
| **Settings not saving** | Permissions on config folder | Run once as admin, or check `%LOCALAPPDATA%` permissions |

### Logs Location
```
%LOCALAPPDATA%\GlobalAirdropHunter\logs\
├── main-YYYY-MM-DD.log        # Electron main process
├── renderer-YYYY-MM-DD.log    # Frontend console
├── api-YYYY-MM-DD.log         # FastAPI backend
└── discovery-YYYY-MM-DD.log   # Discovery workers
```

### Debug Mode
```powershell
# Enable debug logging
$env:GAH_LOG_LEVEL=DEBUG
.\GlobalAirdropHunter.exe

# Or from Settings → Advanced → Debug Mode
```

### Reset Application
```powershell
# Warning: Deletes ALL data
Remove-Item "$env:LOCALAPPDATA\GlobalAirdropHunter" -Recurse -Force
# Then relaunch app
```

### Performance Tuning
```json
{
  "advanced": {
    "cache_size_mb": 1024,
    "discovery": { "concurrent_sources": 3 },
    "database": { "wal_mode": true, "page_size": 4096 }
  }
}
```

---

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) first.

### Quick Contribution Flow
```bash
# 1. Fork & clone
git clone https://github.com/YOUR-FORK/Global-Airdrop-Hunter.git

# 2. Create branch
git checkout -b feat/amazing-feature

# 3. Make changes
# ... code, test, lint ...

# 4. Commit (conventional commits)
git commit -m "feat: add amazing feature"

# 5. Push & PR
git push origin feat/amazing-feature
# Open PR on GitHub
```

### Development Guidelines
- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`)
- **Branching**: `main` (stable), `develop` (integration), `feat/*`, `fix/*`
- **Testing**: All PRs must pass CI (lint, typecheck, unit, e2e)
- **Code Review**: Minimum 1 approval, no self-merge

### Ways to Contribute
- 🐛 **Bug Reports** — Use issue templates
- 💡 **Feature Requests** — Discuss in issues first
- 📝 **Documentation** — Improve guides, add translations
- 🧪 **Testing** — Write tests, report regressions
- 🎨 **UI/UX** — Design improvements, accessibility
- 🔌 **Sources** — Add new discovery sources
- 🌐 **Localization** — Translate to your language

---

## 📜 Changelog

### v1.0.0 (2026-01-15) — Initial Release
- ✅ Campaign discovery from 4 sources
- ✅ Full campaign management (CRUD, search, filter)
- ✅ Verification intelligence (4-tier classification)
- ✅ 15-rule risk assessment engine
- ✅ Eligibility & claim tracking
- ✅ Calendar with notifications
- ✅ Security hardening (CSP, sandbox, token auth)
- ✅ Light/Dark/System themes
- ✅ Data export (JSON, CSV, PDF)
- ✅ Auto-updater via GitHub Releases

### Upcoming (v1.1.0)
- 🔄 Microsoft Store package
- 🔄 Mobile companion app (React Native)
- 🔄 Web dashboard (optional self-hosted)
- 🔄 Advanced analytics & reporting
- 🔄 Team collaboration features
- 🔄 Plugin system for custom sources

---

## 📄 License

**MIT License** — See [LICENSE](LICENSE) for details.

```
Copyright (c) 2026 Global Airdrop Hunter Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
```

---

## 🙏 Acknowledgments

- **Electron** — Desktop framework
- **FastAPI** — Modern Python API framework
- **SQLite** — Embedded database
- **CoinGecko, DeFiLlama** — Data sources
- **Open Source Community** — Inspiration & libraries

---

## 📞 Support & Links

| Resource | Link |
|----------|------|
| **Documentation** | [docs.your-domain.com](https://docs.your-domain.com) |
| **Issues & Bugs** | [GitHub Issues](https://github.com/your-org/Global-Airdrop-Hunter/issues) |
| **Discussions** | [GitHub Discussions](https://github.com/your-org/Global-Airdrop-Hunter/discussions) |
| **Discord Community** | [discord.gg/your-invite](https://discord.gg/your-invite) |
| **Twitter/X** | [@GlobalAirdropHQ](https://twitter.com/GlobalAirdropHQ) |
| **Email** | support@your-domain.com |

---

<p align="center">
  <strong>Made with ❤️ for the airdrop hunting community</strong><br/>
  <sub>Star ⭐ this repo if you find it useful!</sub>
</p>