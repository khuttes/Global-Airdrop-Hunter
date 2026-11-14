# Global Airdrop Hunter - User Guide

## Table of Contents
1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Campaigns Module](#campaigns-module)
5. [Discovery Module](#discovery-module)
6. [Tracking Module](#tracking-module)
7. [Settings](#settings)
8. [Keyboard Shortcuts](#keyboard-shortcuts)
9. [Troubleshooting](#troubleshooting)

## Getting Started

### First Launch
1. Launch Global Airdrop Hunter from Start Menu or Desktop shortcut
2. The application will start the backend API (may take 5-10 seconds on first run)
3. The dashboard will load with an empty state

### Running Your First Scan
1. Click the **Scan** button in the top bar
2. Wait for the scan to complete (progress shown in toast notifications)
3. Results will appear in the Campaigns module

## Dashboard Overview

The dashboard provides a high-level overview:

### Statistics Cards
- **Total Campaigns**: All discovered campaigns
- **Tracking**: Campaigns you're actively monitoring
- **Verified**: Officially or independently corroborated campaigns
- **High Risk**: Campaigns with high or critical risk ratings

### Recent Campaigns
Shows the 5 most recently discovered campaigns with:
- Name and project
- Type (Airdrop/NFT/Testnet/Reward)
- Network
- Status
- Risk level
- Discovery date

### Upcoming Deadlines
Shows campaigns with approaching deadlines:
- Color-coded urgency (red ≤3 days, yellow ≤7 days)
- Days remaining
- Risk level indicator

## Campaigns Module

### Campaign List
Full-featured campaign browser with:

#### Filters
- **Type**: Airdrop, NFT, Testnet, Reward
- **Network**: Ethereum, Arbitrum, Optimism, Polygon, BSC, etc.
- **Status**: Active, Upcoming, Ended, Expired
- **Risk**: Low, Medium, High, Critical

#### Search
Global search across name, project, and description

#### Sorting
Click column headers to sort by:
- Name, Project, Type, Network, Status, Verification, Risk, Deadline, Discovered

#### Pagination
Navigate through pages (20 campaigns per page)

### Campaign Detail View
Click any campaign row to open the detail modal:

#### Basic Information
- Name, project, type, network
- Status badge (Active/Upcoming/Ended/Expired)
- Verification status badge
- Risk level badge with score (0-100)
- Discovery date, last seen, deadline, snapshot date

#### Links
- Official URL (project website)
- Campaign URL (claim/participation page)

#### Description
Full campaign description

#### Evidence
All supporting evidence with:
- Source type and URL
- Title and snippet
- Verification status
- Fetch timestamp

#### Risk Findings
All risk rule triggers with:
- Rule ID and version
- Finding description
- Severity badge
- Matched content
- Evidence URL

#### Eligibility Requirements
Structured requirements with:
- Category (region, network, activity, snapshot, tasks, deadline, holding, NFT)
- Requirement description
- Status (confirmed, not_met, user_reported_met, unknown, not_applicable)
- Source and evidence URL

## Discovery Module

### Sources
Configured discovery sources with:
- Name, type, status
- Last health check
- Scan history
- Enable/disable toggle

### Running a Scan
1. Select sources to scan (checkboxes)
2. Click **Scan** button
3. Results show:
   - Campaigns found
   - New campaigns added
   - Existing campaigns updated
   - Any errors

### Scan History
Previous scans with:
- Timestamp
- Sources scanned
- Results summary
- Error details

## Tracking Module

### Tracked Campaigns
Campaigns you're actively monitoring with:
- Personal progress status
- Custom notes
- Eligibility checklist

### Progress Tracking
For each tracked campaign:
- Mark requirements as: Met / Not Met / In Progress / Not Applicable
- Add personal notes per requirement
- Automatic completion timestamp

### Claim Tracking
Record claim attempts:
- Claim type (Airdrop / NFT Mint / Reward Claim / Testnet Reward)
- Claim URL
- Transaction hash
- Block number
- Network
- Status (Pending / Submitted / Confirmed / Failed / Cancelled)
- Personal notes

## Settings

### General
- **Theme**: Dark / Light / System
- **Auto-refresh interval**: 5-1440 minutes (default 30)
- **Notifications**: Enable/disable desktop notifications

### Backend
- API Base URL (read-only)
- Database location (read-only)

### Data Management
- **Create Backup**: Timestamped SQLite backup with integrity verification
- **Run Diagnostics**: Health check of API, database, and connectivity

### About
- Application version
- Electron version
- Node.js version

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+R` | Refresh current view |
| `Ctrl+F` | Focus global search |
| `Ctrl+S` | Start discovery scan |
| `Esc` | Close modal / dismiss toast |
| `Ctrl+1` | Dashboard |
| `Ctrl+2` | Campaigns |
| `Ctrl+3` | Discovery |
| `Ctrl+4` | Tracking |
| `Ctrl+5` | Settings |

## Troubleshooting

### Application Won't Start
1. Check if backend is running: `http://127.0.0.1:8000/api/v1/health`
2. Run diagnostics from Settings
3. Check `%LOCALAPPDATA%\GlobalAirdropHunter\logs\` for error logs
4. Restart application

### Backend Connection Failed
1. Verify port 8000 is not in use
2. Check Windows Firewall allows localhost connections
3. Run `.\scripts\diagnostics.ps1` for detailed checks

### Scan Returns No Results
1. Check source health in Discovery module
2. Verify internet connectivity
3. Check source rate limits (some APIs have strict limits)

### Database Issues
1. Run backup from Settings
2. If corrupted, restore from backup
3. Check `%LOCALAPPDATA%\GlobalAirdropHunter\app.db` exists

### Performance Issues
1. Reduce auto-refresh interval
2. Clear browser cache (if using browser launcher)
3. Restart application to clear memory

### Data Location
- Database: `%LOCALAPPDATA%\GlobalAirdropHunter\app.db`
- Backups: `%LOCALAPPDATA%\GlobalAirdropHunter\backups\`
- Logs: `%LOCALAPPDATA%\GlobalAirdropHunter\logs\`

## Support

For issues not covered here:
1. Run diagnostics from Settings
2. Check logs in `%LOCALAPPDATA%\GlobalAirdropHunter\logs\`
3. Report issues with: error message, steps to reproduce, logs