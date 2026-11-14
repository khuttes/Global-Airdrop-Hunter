# Global Airdrop Hunter - API Documentation

## Base URL
```
http://127.0.0.1:8000/api/v1
```

## Authentication
All endpoints (except `/health`) require the `X-Local-API-Token` header:
```
X-Local-API-Token: <your-token>
```

The token is generated at startup and logged to console.

## Rate Limiting
- Maximum request size: 1 MB
- No explicit rate limits (local-only API)

## Endpoints

### Health Check
```
GET /api/v1/health
```
**Auth**: None required
**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-11-13T04:04:27.709613",
  "database": "connected",
  "uptime_seconds": 364.98
}
```

### Dashboard
```
GET /api/v1/dashboard
```
**Response**:
```json
{
  "total_campaigns": 1211,
  "tracked_campaigns": 0,
  "verified_campaigns": 0,
  "high_risk_campaigns": 0,
  "recent_campaigns": [...],
  "upcoming_deadlines": [...]
}
```

---

## Campaigns

### List Campaigns
```
GET /api/v1/campaigns
```
**Query Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| page | integer | 1 | Page number (≥1) |
| page_size | integer | 20 | Items per page (1-100) |
| type | string | - | Filter by type (airdrop/nft/testnet/reward) |
| network | string | - | Filter by network |
| status | string | - | Filter by status (active/upcoming/ended/expired/withdrawn) |
| verification_status | string | - | Filter by verification (officially_corroborated/independently_corroborated/unverified/suspicious/expired/withdrawn) |
| risk_level | string | - | Filter by risk (low/medium/high/critical) |
| search | string | - | Search in name/project/description |
| sort_by | string | discovered_at | Sort field |
| sort_order | string | desc | Sort order (asc/desc) |

**Response**:
```json
{
  "items": [...],
  "total": 1211,
  "page": 1,
  "page_size": 20,
  "total_pages": 61
}
```

### Create Campaign
```
POST /api/v1/campaigns
```
**Body**:
```json
{
  "name": "string",
  "project": "string",
  "type": "airdrop|nft|testnet|reward",
  "network": "string",
  "description": "string",
  "official_url": "https://...",
  "campaign_url": "https://...",
  "status": "active|upcoming|ended|expired|withdrawn",
  "verification_status": "officially_corroborated|independently_corroborated|unverified|suspicious|expired|withdrawn",
  "risk_level": "low|medium|high|critical",
  "risk_score": 50,
  "deadline": "2026-12-31T23:59:59Z",
  "snapshot_date": "2026-11-01T00:00:00Z",
  "evidence_urls": ["https://..."],
  "source_id": "string"
}
```

### Get Campaign
```
GET /api/v1/campaigns/{campaign_id}
```
**Response**: Full Campaign object with evidence, risk findings, eligibility

### Update Campaign
```
PATCH /api/v1/campaigns/{campaign_id}
```
**Body**: Partial CampaignUpdate object

### Delete Campaign
```
DELETE /api/v1/campaigns/{campaign_id}
```

### Save Campaign (Track)
```
POST /api/v1/campaigns/{campaign_id}/save
```

---

## Campaign Eligibility

### Get Eligibility Requirements
```
GET /api/v1/campaigns/{campaign_id}/eligibility
```

### Auto-extract Requirements
```
POST /api/v1/campaigns/{campaign_id}/eligibility/extract
```
Extracts requirements from campaign text using regex patterns.

### Get User Progress
```
GET /api/v1/campaigns/{campaign_id}/progress
```

### Update User Progress
```
POST /api/v1/campaigns/{campaign_id}/progress
```
**Body**:
```json
{
  "requirement_id": "uuid",
  "user_status": "unknown|met|not_met|in_progress|not_applicable",
  "user_notes": "string",
  "completed": true
}
```

---

## Campaign Claims

### List Claims
```
GET /api/v1/campaigns/{campaign_id}/claims
```

### Create Claim
```
POST /api/v1/campaigns/{campaign_id}/claims
```
**Body**:
```json
{
  "claim_type": "airdrop|nft_mint|reward_claim|testnet_reward",
  "claim_url": "https://...",
  "transaction_hash": "0x...",
  "block_number": 12345678,
  "network": "Ethereum",
  "user_notes": "string"
}
```

### Update Claim
```
PATCH /api/v1/campaigns/{campaign_id}/claims/{claim_id}
```
**Body**: Partial CampaignClaim update (status, transaction_hash, block_number, etc.)

---

## Sources

### List Sources
```
GET /api/v1/sources
```
**Query**: `enabled_only=true|false`

### Create Source
```
POST /api/v1/sources
```
**Body**:
```json
{
  "name": "string",
  "type": "api|rss|html|github|official",
  "base_url": "https://...",
  "config": {},
  "rate_limit": 60,
  "timeout": 30
}
```

### Get Source
```
GET /api/v1/sources/{source_id}
```

### Update Source
```
PATCH /api/v1/sources/{source_id}
```

### Delete Source
```
DELETE /api/v1/sources/{source_id}
```

### Health Check
```
POST /api/v1/sources/{source_id}/health
```

### List Adapters
```
GET /api/v1/adapters
```

---

## Discovery

### Start Scan
```
POST /api/v1/discovery/scans
```
**Body**:
```json
{
  "sources": ["source_id_1", "source_id_2"]
}
```
Empty sources = scan all enabled sources.

**Response**:
```json
{
  "scan_id": "uuid",
  "sources_scanned": ["source_id_1"],
  "campaigns_found": 1198,
  "campaigns_new": 0,
  "campaigns_updated": 1198,
  "errors": [],
  "started_at": "2026-11-13T04:04:07.663758",
  "completed_at": "2026-11-13T04:04:20.123456"
}
```

### Scan History
```
GET /api/v1/discovery/scans?limit=50
```

---

## Verification & Risk

### Campaign Verification
```
GET /api/v1/campaigns/{campaign_id}/verification
POST /api/v1/campaigns/{campaign_id}/verify
```

### Campaign Risk Assessment
```
GET /api/v1/campaigns/{campaign_id}/risk
POST /api/v1/campaigns/{campaign_id}/assess-risk
```

### Domain Verification
```
GET /api/v1/domain/verify?url=https://example.com
```

### Risk Rules
```
GET /api/v1/risk/rules?category=&severity=&active_only=true
GET /api/v1/risk/rules/{rule_id}
POST /api/v1/risk/rules
PATCH /api/v1/risk/rules/{rule_id}
```

---

## Category-Specific Data

### NFT Data
```
GET /api/v1/campaigns/{campaign_id}/nft
PATCH /api/v1/campaigns/{campaign_id}/nft
```

### Testnet Data
```
GET /api/v1/campaigns/{campaign_id}/testnet
PATCH /api/v1/campaigns/{campaign_id}/testnet
```

### Reward Data
```
GET /api/v1/campaigns/{campaign_id}/reward
PATCH /api/v1/campaigns/{campaign_id}/reward
```

---

## Events & Calendar

### List Events
```
GET /api/v1/campaigns/{campaign_id}/events
```

### Create Event
```
POST /api/v1/campaigns/{campaign_id}/events
```
**Body**:
```json
{
  "event_type": "deadline|mint_start|mint_end|claim_start|claim_end|distribution|announcement|snapshot",
  "event_title": "string",
  "event_description": "string",
  "event_date": "2026-12-01T12:00:00Z",
  "is_all_day": false,
  "reminder_days_before": 3
}
```

### Update Event
```
PATCH /api/v1/campaigns/{campaign_id}/events/{event_id}
```

### Delete Event
```
DELETE /api/v1/campaigns/{campaign_id}/events/{event_id}
```

---

## Notification Preferences

### Get Preferences
```
GET /api/v1/campaigns/{campaign_id}/notification-prefs
```

### Update Preferences
```
PATCH /api/v1/campaigns/{campaign_id}/notification-prefs
```
**Body**:
```json
{
  "notify_deadline": true,
  "notify_mint_start": true,
  "notify_mint_end": true,
  "notify_claim_start": true,
  "notify_claim_end": true,
  "notify_distribution": true,
  "reminder_days_before": 1,
  "in_app_enabled": true
}
```

---

## Backup & Restore

### Create Backup
```
POST /api/v1/backup?verify=true
```
**Response**:
```json
{
  "backup_path": "C:\\Users\\...\\backups\\app_20261113_040407.db",
  "size_bytes": 5201920,
  "created_at": "2026-11-13T04:04:07.663758",
  "integrity_verified": true
}
```

### List Backups
```
GET /api/v1/backups
```

### Restore Backup
```
POST /api/v1/restore?filename=app_20261113_040407.db
```

---

## Error Responses

All errors follow this format:
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description"
  }
}
```

### Common Error Codes
| Code | HTTP Status | Description |
|------|-------------|-------------|
| MISSING_TOKEN | 401 | Missing X-Local-API-Token header |
| INVALID_TOKEN | 401 | Invalid or expired API token |
| INVALID_ORIGIN | 403 | Request origin not allowed |
| NOT_FOUND | 404 | Resource not found |
| DUPLICATE_SOURCE | 409 | Source name already exists |
| PAYLOAD_TOO_LARGE | 413 | Request body exceeds 1MB |
| INVALID_TOKEN | 401 | Invalid or expired API token |
| WRONG_TYPE | 400 | Campaign type mismatch for category endpoint |
| BACKUP_CORRUPT | 400 | Backup integrity check failed |
| INTERNAL_ERROR | 500 | Unexpected server error |

---

## Data Models

### Campaign
```typescript
interface Campaign {
  id: string (UUID)
  stable_id: string
  name: string
  project?: string
  type: "airdrop" | "nft" | "testnet" | "reward"
  network?: string
  description?: string
  official_url?: string
  campaign_url?: string
  status: "active" | "upcoming" | "ended" | "expired" | "withdrawn"
  verification_status: "officially_corroborated" | "independently_corroborated" | "unverified" | "suspicious" | "expired" | "withdrawn"
  risk_level: "low" | "medium" | "high" | "critical"
  risk_score: number (0-100)
  deadline?: string (ISO 8601)
  snapshot_date?: string (ISO 8601)
  discovered_at: string (ISO 8601)
  last_seen_at: string (ISO 8601)
  // Category-specific fields (see below)
  evidence: Evidence[]
  risk_findings: RiskFinding[]
  eligibility: EligibilityRequirement[]
}
```

### Evidence
```typescript
interface Evidence {
  id: string (UUID)
  campaign_id: string (UUID)
  url: string
  source_type: "api" | "rss" | "html" | "github" | "official" | "manual"
  content_hash: string
  title?: string
  snippet?: string
  fetched_at: string (ISO 8601)
  verified: boolean
}
```

### RiskFinding
```typescript
interface RiskFinding {
  id: string (UUID)
  campaign_id: string (UUID)
  rule_id: string
  rule_version: number
  finding: string
  severity: "low" | "medium" | "high" | "critical"
  description: string
  evidence_url?: string
  matched_content?: string
  created_at: string (ISO 8601)
}
```

### EligibilityRequirement
```typescript
interface EligibilityRequirement {
  id: string (UUID)
  campaign_id: string (UUID)
  category: string
  requirement: string
  status: "unknown" | "confirmed" | "not_met" | "user_reported_met" | "not_applicable"
  evidence_url?: string
  source?: string
  timestamp: string (ISO 8601)
  notes?: string
  progress_status: "potentially_eligible" | "user_reported_met" | "user_reported_not_met" | "not_applicable" | "claim_available" | "claimed"
  user_notes?: string
  completed_at?: string (ISO 8601)
}
```

### CampaignClaim
```typescript
interface CampaignClaim {
  id: string (UUID)
  campaign_id: string (UUID)
  claim_type: "airdrop" | "nft_mint" | "reward_claim" | "testnet_reward"
  claim_url?: string
  transaction_hash?: string
  block_number?: number
  network?: string
  status: "pending" | "submitted" | "confirmed" | "failed" | "cancelled"
  claimed_at?: string (ISO 8601)
  confirmed_at?: string (ISO 8601)
  user_notes?: string
  created_at: string (ISO 8601)
  updated_at: string (ISO 8601)
}
```

### CampaignEvent
```typescript
interface CampaignEvent {
  id: string (UUID)
  campaign_id: string (UUID)
  event_type: "deadline" | "mint_start" | "mint_end" | "claim_start" | "claim_end" | "distribution" | "announcement" | "snapshot"
  event_title: string
  event_description?: string
  event_date: string (ISO 8601)
  is_all_day: boolean
  reminder_days_before: number
  is_notified: boolean
  created_at: string (ISO 8601)
  updated_at: string (ISO 8601)
}
```

### UserNotificationPrefs
```typescript
interface UserNotificationPrefs {
  id: string (UUID)
  campaign_id: string (UUID)
  notify_deadline: boolean
  notify_mint_start: boolean
  notify_mint_end: boolean
  notify_claim_start: boolean
  notify_claim_end: boolean
  notify_distribution: boolean
  reminder_days_before: number
  in_app_enabled: boolean
  created_at: string (ISO 8601)
  updated_at: string (ISO 8601)
}
```

---

## NFT-Specific Fields (Campaign)
```typescript
interface Campaign {
  // ... base fields
  nft_collection_name?: string
  nft_collection_slug?: string
  nft_mint_price?: string
  nft_mint_currency?: string
  nft_total_supply?: number
  nft_minted_supply?: number
  nft_mint_start?: string (ISO 8601)
  nft_mint_end?: string (ISO 8601)
  nft_whitelist_url?: string
  nft_official_collection_url?: string
  nft_marketplace_urls: string[]
  nft_royalty_percentage?: number
  nft_standard?: string
}
```

## Testnet-Specific Fields (Campaign)
```typescript
interface Campaign {
  // ... base fields
  testnet_network_name?: string
  testnet_chain_id?: number
  testnet_rpc_url?: string
  testnet_explorer_url?: string
  testnet_faucet_url?: string
  testnet_docs_url?: string
  testnet_github_url?: string
  testnet_tasks: string[]
  testnet_duration_days?: number
  testnet_reward_type?: string
  testnet_reward_amount?: string
}
```

## Reward-Specific Fields (Campaign)
```typescript
interface Campaign {
  // ... base fields
  reward_token_symbol?: string
  reward_token_address?: string
  reward_token_decimals?: number
  reward_amount_per_user?: string
  reward_total_pool?: string
  reward_distribution_method?: string
  reward_claim_start?: string (ISO 8601)
  reward_claim_end?: string (ISO 8601)
  reward_vesting_schedule?: object
  reward_apy?: number
  reward_lockup_period_days?: number
}
```