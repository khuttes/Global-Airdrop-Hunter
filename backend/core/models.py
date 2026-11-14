from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, HttpUrl, validator
from uuid import UUID, uuid4


class CampaignType(str, Enum):
    AIRDROP = "airdrop"
    NFT = "nft"
    TESTNET = "testnet"
    REWARD = "reward"


class CampaignStatus(str, Enum):
    ACTIVE = "active"
    UPCOMING = "upcoming"
    ENDED = "ended"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class VerificationStatus(str, Enum):
    OFFICIAL = "officially_corroborated"
    INDEPENDENT = "independently_corroborated"
    UNVERIFIED = "unverified"
    SUSPICIOUS = "suspicious"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SourceType(str, Enum):
    API = "api"
    RSS = "rss"
    HTML = "html"
    GITHUB = "github"
    OFFICIAL = "official"
    MANUAL = "manual"


class SourceStatus(str, Enum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    PAUSED = "paused"
    ERROR = "error"


class EligibilityStatus(str, Enum):
    UNKNOWN = "unknown"
    CONFIRMED = "confirmed"
    NOT_MET = "not_met"
    USER_REPORTED_MET = "user_reported_met"
    NOT_APPLICABLE = "not_applicable"


class UserProgressStatus(str, Enum):
    UNKNOWN = "unknown"
    MET = "met"
    NOT_MET = "not_met"
    IN_PROGRESS = "in_progress"
    NOT_APPLICABLE = "not_applicable"


class ProgressStatus(str, Enum):
    POTENTIALLY_ELIGIBLE = "potentially_eligible"
    USER_REPORTED_MET = "user_reported_met"
    USER_REPORTED_NOT_MET = "user_reported_not_met"
    NOT_APPLICABLE = "not_applicable"
    CLAIM_AVAILABLE = "claim_available"
    CLAIMED = "claimed"


class ClaimStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RiskFinding(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    rule_id: str
    rule_version: int
    finding: str
    severity: RiskLevel
    description: str
    evidence_url: Optional[HttpUrl] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Evidence(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    url: HttpUrl
    source_type: SourceType
    content_hash: str
    title: Optional[str] = None
    snippet: Optional[str] = None
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    verified: bool = False


class EligibilityRequirement(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    category: str
    requirement: str
    status: EligibilityStatus = EligibilityStatus.UNKNOWN
    evidence_url: Optional[HttpUrl] = None
    source: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None
    progress_status: ProgressStatus = ProgressStatus.POTENTIALLY_ELIGIBLE
    user_notes: Optional[str] = None
    completed_at: Optional[datetime] = None


class CampaignBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    project: Optional[str] = None
    type: CampaignType = CampaignType.AIRDROP
    network: Optional[str] = None
    description: Optional[str] = None
    official_url: Optional[HttpUrl] = None
    campaign_url: Optional[HttpUrl] = None
    status: CampaignStatus = CampaignStatus.ACTIVE
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    risk_level: RiskLevel = RiskLevel.MEDIUM
    risk_score: int = Field(default=50, ge=0, le=100)
    deadline: Optional[datetime] = None
    snapshot_date: Optional[datetime] = None
    discovered_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)

    # NFT-specific fields
    nft_collection_name: Optional[str] = None
    nft_collection_slug: Optional[str] = None
    nft_mint_price: Optional[str] = None
    nft_mint_currency: Optional[str] = None
    nft_total_supply: Optional[int] = None
    nft_minted_supply: Optional[int] = None
    nft_mint_start: Optional[datetime] = None
    nft_mint_end: Optional[datetime] = None
    nft_whitelist_url: Optional[HttpUrl] = None
    nft_official_collection_url: Optional[HttpUrl] = None
    nft_marketplace_urls: List[HttpUrl] = []
    nft_royalty_percentage: Optional[float] = None
    nft_standard: Optional[str] = None

    # Testnet-specific fields
    testnet_network_name: Optional[str] = None
    testnet_chain_id: Optional[int] = None
    testnet_rpc_url: Optional[HttpUrl] = None
    testnet_explorer_url: Optional[HttpUrl] = None
    testnet_faucet_url: Optional[HttpUrl] = None
    testnet_docs_url: Optional[HttpUrl] = None
    testnet_github_url: Optional[HttpUrl] = None
    testnet_tasks: List[str] = []
    testnet_duration_days: Optional[int] = None
    testnet_reward_type: Optional[str] = None
    testnet_reward_amount: Optional[str] = None

    # Reward-specific fields
    reward_token_symbol: Optional[str] = None
    reward_token_address: Optional[str] = None
    reward_token_decimals: Optional[int] = None
    reward_amount_per_user: Optional[str] = None
    reward_total_pool: Optional[str] = None
    reward_distribution_method: Optional[str] = None
    reward_claim_start: Optional[datetime] = None
    reward_claim_end: Optional[datetime] = None
    reward_vesting_schedule: Optional[Dict[str, Any]] = None
    reward_apy: Optional[float] = None
    reward_lockup_period_days: Optional[int] = None


class CampaignCreate(CampaignBase):
    source_id: Optional[str] = None
    evidence_urls: List[HttpUrl] = []


class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    project: Optional[str] = None
    type: Optional[CampaignType] = None
    network: Optional[str] = None
    description: Optional[str] = None
    official_url: Optional[HttpUrl] = None
    campaign_url: Optional[HttpUrl] = None
    status: Optional[CampaignStatus] = None
    verification_status: Optional[VerificationStatus] = None
    risk_level: Optional[RiskLevel] = None
    risk_score: Optional[int] = Field(None, ge=0, le=100)
    deadline: Optional[datetime] = None
    snapshot_date: Optional[datetime] = None

    # NFT-specific fields
    nft_collection_name: Optional[str] = None
    nft_collection_slug: Optional[str] = None
    nft_mint_price: Optional[str] = None
    nft_mint_currency: Optional[str] = None
    nft_total_supply: Optional[int] = None
    nft_minted_supply: Optional[int] = None
    nft_mint_start: Optional[datetime] = None
    nft_mint_end: Optional[datetime] = None
    nft_whitelist_url: Optional[HttpUrl] = None
    nft_official_collection_url: Optional[HttpUrl] = None
    nft_marketplace_urls: Optional[List[HttpUrl]] = None
    nft_royalty_percentage: Optional[float] = None
    nft_standard: Optional[str] = None

    # Testnet-specific fields
    testnet_network_name: Optional[str] = None
    testnet_chain_id: Optional[int] = None
    testnet_rpc_url: Optional[HttpUrl] = None
    testnet_explorer_url: Optional[HttpUrl] = None
    testnet_faucet_url: Optional[HttpUrl] = None
    testnet_docs_url: Optional[HttpUrl] = None
    testnet_github_url: Optional[HttpUrl] = None
    testnet_tasks: Optional[List[str]] = None
    testnet_duration_days: Optional[int] = None
    testnet_reward_type: Optional[str] = None
    testnet_reward_amount: Optional[str] = None

    # Reward-specific fields
    reward_token_symbol: Optional[str] = None
    reward_token_address: Optional[str] = None
    reward_token_decimals: Optional[int] = None
    reward_amount_per_user: Optional[str] = None
    reward_total_pool: Optional[str] = None
    reward_distribution_method: Optional[str] = None
    reward_claim_start: Optional[datetime] = None
    reward_claim_end: Optional[datetime] = None
    reward_vesting_schedule: Optional[Dict[str, Any]] = None
    reward_apy: Optional[float] = None
    reward_lockup_period_days: Optional[int] = None


class Campaign(CampaignBase):
    id: UUID = Field(default_factory=uuid4)
    source_id: Optional[str] = None
    stable_id: str
    evidence: List[Evidence] = []
    risk_findings: List[RiskFinding] = []
    eligibility: List[EligibilityRequirement] = []
    field_history: Dict[str, List[Dict[str, Any]]] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class CampaignListItem(BaseModel):
    id: UUID
    stable_id: str
    name: str
    project: Optional[str]
    type: CampaignType
    network: Optional[str]
    status: CampaignStatus
    verification_status: VerificationStatus
    risk_level: RiskLevel
    deadline: Optional[datetime]
    discovered_at: datetime

    class Config:
        from_attributes = True


class CampaignsResponse(BaseModel):
    items: List[CampaignListItem]
    total: int
    page: int
    page_size: int
    total_pages: int


class SourceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: SourceType
    base_url: HttpUrl
    config: Dict[str, Any] = {}
    rate_limit: int = 60
    timeout: int = 30


class SourceCreate(SourceBase):
    pass


class SourceUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    base_url: Optional[HttpUrl] = None
    config: Optional[Dict[str, Any]] = None
    rate_limit: Optional[int] = None
    timeout: Optional[int] = None
    status: Optional[SourceStatus] = None
    enabled: Optional[bool] = None


class Source(SourceBase):
    id: str
    status: SourceStatus = SourceStatus.ENABLED
    enabled: bool = True
    last_health_check: Optional[datetime] = None
    last_scan: Optional[datetime] = None
    consecutive_failures: int = 0
    total_scans: int = 0
    total_records: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class ScanRequest(BaseModel):
    sources: List[str] = []


class ScanResult(BaseModel):
    scan_id: UUID = Field(default_factory=uuid4)
    sources_scanned: List[str]
    campaigns_found: int
    campaigns_new: int
    campaigns_updated: int
    errors: List[str] = []
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    database: str = "connected"
    uptime_seconds: float


class DashboardResponse(BaseModel):
    total_campaigns: int = 0
    tracked_campaigns: int = 0
    verified_campaigns: int = 0
    high_risk_campaigns: int = 0
    recent_campaigns: List[CampaignListItem] = []
    upcoming_deadlines: List[Dict[str, Any]] = []


class BackupResponse(BaseModel):
    backup_path: str
    size_bytes: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    integrity_verified: bool = True


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class CampaignFilters(BaseModel):
    type: Optional[CampaignType] = None
    network: Optional[str] = None
    status: Optional[CampaignStatus] = None
    verification_status: Optional[VerificationStatus] = None
    risk_level: Optional[RiskLevel] = None
    search: Optional[str] = None
    sort_by: Optional[str] = "discovered_at"
    sort_order: Optional[str] = "desc"


class UserEligibilityProgress(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    campaign_id: UUID
    requirement_id: UUID
    user_status: UserProgressStatus = UserProgressStatus.UNKNOWN
    user_notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class CampaignClaim(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    campaign_id: UUID
    claim_type: str
    claim_url: Optional[HttpUrl] = None
    transaction_hash: Optional[str] = None
    block_number: Optional[int] = None
    network: Optional[str] = None
    status: ClaimStatus = ClaimStatus.PENDING
    claimed_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    user_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class CampaignEvent(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    campaign_id: UUID
    event_type: str
    event_title: str
    event_description: Optional[str] = None
    event_date: datetime
    is_all_day: bool = False
    reminder_days_before: int = 1
    is_notified: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class UserNotificationPrefs(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    campaign_id: UUID
    notify_deadline: bool = True
    notify_mint_start: bool = True
    notify_mint_end: bool = True
    notify_claim_start: bool = True
    notify_claim_end: bool = True
    notify_distribution: bool = True
    reminder_days_before: int = 1
    in_app_enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True