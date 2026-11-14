# Global Airdrop Hunter

A Windows desktop application for discovering, tracking, and analyzing cryptocurrency airdrop campaigns.

## Features

- **Campaign Discovery**: Automated discovery from multiple sources (CoinGecko, DefiLlama, GitHub, RSS feeds)
- **Campaign Management**: Full CRUD operations with pagination, search, filtering, and sorting
- **Verification Intelligence**: Official/Independent/Unverified/Suspicious classification with evidence tracking
- **Risk Assessment**: 15-rule risk engine with critical overrides (credential requests, upfront payments)
- **Eligibility Tracking**: Structured requirements with user progress tracking (met/not_met/in_progress)
- **Claim Tracking**: Airdrop/NFT mint/reward claim/testnet reward tracking with transaction hashes
- **Calendar & Notifications**: Campaign events with reminder system and per-campaign notification preferences
- **Security Hardened**: Electron context isolation, sandbox, CSP, token-based API auth, localhost-only binding

## Quick Start

### Prerequisites
- Windows 10/11 64-bit
- Python 3.12 (included in installer)
- Node.js 18+ (for development)

### Installation
1. Download the latest `GlobalAirdropHunter-1.0.0-setup.exe` from releases
2. Run the installer
3. Launch "Global Airdrop Hunter" from Start Menu or Desktop

### Development Setup
```powershell
# Clone repository
git clone <repository-url>
cd GlobalAirdropHunter

# Run setup
.\scripts\setup.ps1

# Start development
.\scripts\launch.ps1
```

## Usage

1. **Dashboard**: Overview of campaigns, statistics, and upcoming deadlines
2. **Campaigns**: Browse, search, filter, and sort all discovered campaigns
3. **Discovery**: Configure sources and run scans
4. **Tracking**: Monitor your progress on campaigns
5. **Settings**: Configure notifications, theme, and preferences

## Architecture

- **Frontend**: HTML5/CSS3/Vanilla JS (Electron renderer)
- **Backend**: FastAPI (Python 3.12) on localhost:8000
- **Database**: SQLite at `%LOCALAPPDATA%\GlobalAirdropHunter\app.db`
- **IPC**: Secure context bridge with allowlisted channels

## Security

- Electron context isolation + sandbox enabled
- Content Security Policy enforced
- Token-based API authentication
- Localhost-only API binding
- Request size limits (1MB)
- Input validation and sanitization

## License

MIT License - see LICENSE file for details.