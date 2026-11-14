"""
Unit tests for core models.
"""
import pytest
from pydantic import ValidationError
from uuid import uuid4
from backend.core.models import (
    CampaignCreate, CampaignUpdate, CampaignFilters, PaginationParams,
    CampaignType, CampaignStatus, VerificationStatus, RiskLevel,
    SourceCreate, SourceUpdate, SourceType,
    EligibilityRequirement, EligibilityStatus, UserProgressStatus, ProgressStatus, ClaimStatus,
    CampaignEvent, UserNotificationPrefs,
    ScanRequest, ScanResult, HealthResponse, DashboardResponse,
)


class TestCampaignModels:
    """Test campaign-related models."""
    
    def test_campaign_create_valid(self):
        """Test valid campaign creation."""
        campaign = CampaignCreate(
            name="Test Campaign",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
            description="Test description",
            official_url="https://example.com",
            campaign_url="https://example.com/campaign",
            status=CampaignStatus.ACTIVE,
            verification_status=VerificationStatus.UNVERIFIED,
            risk_level=RiskLevel.LOW,
            risk_score=10,
        )
        assert campaign.name == "Test Campaign"
        assert campaign.type == CampaignType.AIRDROP
        assert campaign.risk_score == 10
    
    def test_campaign_create_minimal(self):
        """Test campaign creation with minimal required fields."""
        campaign = CampaignCreate(
            name="Minimal Campaign",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        assert campaign.name == "Minimal Campaign"
        assert campaign.status == CampaignStatus.ACTIVE  # default
        assert campaign.verification_status == VerificationStatus.UNVERIFIED  # default
        assert campaign.risk_level == RiskLevel.MEDIUM  # default
        assert campaign.risk_score == 50  # default
    
    def test_campaign_create_invalid_risk_score(self):
        """Test campaign creation rejects invalid risk score."""
        with pytest.raises(ValidationError):
            CampaignCreate(
                name="Test",
                project="Test",
                type=CampaignType.AIRDROP,
                network="Ethereum",
                risk_score=101,  # > 100
            )
        with pytest.raises(ValidationError):
            CampaignCreate(
                name="Test",
                project="Test",
                type=CampaignType.AIRDROP,
                network="Ethereum",
                risk_score=-1,  # < 0
            )
    
    def test_campaign_create_invalid_url(self):
        """Test campaign creation rejects invalid URLs."""
        with pytest.raises(ValidationError):
            CampaignCreate(
                name="Test",
                project="Test",
                type=CampaignType.AIRDROP,
                network="Ethereum",
                official_url="not-a-url",
            )
    
    def test_campaign_update_partial(self):
        """Test partial campaign update."""
        update = CampaignUpdate(
            description="Updated description",
            risk_score=50,
        )
        assert update.description == "Updated description"
        assert update.risk_score == 50
        assert update.name is None  # not provided
    
    def test_campaign_filters(self):
        """Test campaign filters model."""
        filters = CampaignFilters(
            type=CampaignType.AIRDROP,
            network="Ethereum",
            status=CampaignStatus.ACTIVE,
            verification_status=VerificationStatus.OFFICIAL,
            risk_level=RiskLevel.HIGH,
            search="test",
        )
        assert filters.type == CampaignType.AIRDROP
        assert filters.network == "Ethereum"
        assert filters.search == "test"
    
    def test_pagination_params(self):
        """Test pagination parameters."""
        pagination = PaginationParams(page=2, page_size=20)
        assert pagination.page == 2
        assert pagination.page_size == 20
        # offset is not a property, compute manually
        assert (pagination.page - 1) * pagination.page_size == 20
    
    def test_pagination_params_defaults(self):
        """Test pagination defaults."""
        pagination = PaginationParams()
        assert pagination.page == 1
        assert pagination.page_size == 20
        assert (pagination.page - 1) * pagination.page_size == 0
    
    def test_pagination_invalid_page(self):
        """Test pagination rejects invalid page."""
        with pytest.raises(ValidationError):
            PaginationParams(page=0)
        with pytest.raises(ValidationError):
            PaginationParams(page=-1)
    
    def test_pagination_invalid_page_size(self):
        """Test pagination rejects invalid page_size."""
        with pytest.raises(ValidationError):
            PaginationParams(page_size=0)
        with pytest.raises(ValidationError):
            PaginationParams(page_size=101)  # max 100


class TestSourceModels:
    """Test source-related models."""
    
    def test_source_create_valid(self):
        """Test valid source creation."""
        source = SourceCreate(
            name="Test Source",
            type=SourceType.API,
            base_url="https://api.example.com",
            config={"api_key": "secret"},
            rate_limit=60,
            timeout=30,
        )
        assert source.name == "Test Source"
        assert source.type == SourceType.API
        assert source.config == {"api_key": "secret"}
    
    def test_source_create_minimal(self):
        """Test source creation with minimal fields."""
        source = SourceCreate(
            name="Minimal Source",
            type=SourceType.RSS,
            base_url="https://example.com/feed.xml",
        )
        assert source.rate_limit == 60  # default
        assert source.timeout == 30  # default
        assert source.config == {}  # default
    
    def test_source_update(self):
        """Test source update model."""
        update = SourceUpdate(
            rate_limit=120,
            enabled=False,
        )
        assert update.rate_limit == 120
        assert update.enabled is False
        assert update.name is None


class TestEligibilityModels:
    """Test eligibility-related models."""
    
    def test_eligibility_requirement(self):
        """Test eligibility requirement model."""
        req = EligibilityRequirement(
            category="social",
            requirement="Follow Twitter",
            status=EligibilityStatus.CONFIRMED,
            progress_status=ProgressStatus.POTENTIALLY_ELIGIBLE,
            evidence_url="https://twitter.com/test",
            source="manual",
            notes="Must follow and retweet",
        )
        assert req.category == "social"
        assert req.status == EligibilityStatus.CONFIRMED
        assert req.progress_status == ProgressStatus.POTENTIALLY_ELIGIBLE
    
    def test_campaign_event(self):
        """Test campaign event model."""
        event = CampaignEvent(
            campaign_id=uuid4(),
            event_type="deadline",
            event_title="Campaign Ends",
            event_description="Last day to participate",
            event_date="2026-12-31T23:59:59",
            is_all_day=False,
            reminder_days_before=1,
        )
        assert event.event_type == "deadline"
        assert event.reminder_days_before == 1
    
    def test_notification_prefs(self):
        """Test notification preferences model."""
        prefs = UserNotificationPrefs(
            campaign_id=uuid4(),
            notify_deadline=True,
            notify_mint_start=True,
            reminder_days_before=2,
            in_app_enabled=True,
        )
        assert prefs.notify_deadline is True
        assert prefs.reminder_days_before == 2


class TestEnums:
    """Test enum values."""
    
    def test_campaign_type_values(self):
        assert CampaignType.AIRDROP.value == "airdrop"
        assert CampaignType.NFT.value == "nft"
        assert CampaignType.TESTNET.value == "testnet"
        assert CampaignType.REWARD.value == "reward"
    
    def test_campaign_status_values(self):
        assert CampaignStatus.ACTIVE.value == "active"
        assert CampaignStatus.UPCOMING.value == "upcoming"
        assert CampaignStatus.ENDED.value == "ended"
        assert CampaignStatus.EXPIRED.value == "expired"
        assert CampaignStatus.WITHDRAWN.value == "withdrawn"
    
    def test_verification_status_values(self):
        assert VerificationStatus.OFFICIAL.value == "officially_corroborated"
        assert VerificationStatus.INDEPENDENT.value == "independently_corroborated"
        assert VerificationStatus.UNVERIFIED.value == "unverified"
        assert VerificationStatus.SUSPICIOUS.value == "suspicious"
        assert VerificationStatus.EXPIRED.value == "expired"
        assert VerificationStatus.WITHDRAWN.value == "withdrawn"
    
    def test_risk_level_values(self):
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"
    
    def test_source_type_values(self):
        assert SourceType.API.value == "api"
        assert SourceType.RSS.value == "rss"
        assert SourceType.HTML.value == "html"
        assert SourceType.GITHUB.value == "github"
        assert SourceType.OFFICIAL.value == "official"
        assert SourceType.MANUAL.value == "manual"
    
    def test_eligibility_status_values(self):
        assert EligibilityStatus.UNKNOWN.value == "unknown"
        assert EligibilityStatus.CONFIRMED.value == "confirmed"
        assert EligibilityStatus.NOT_MET.value == "not_met"
        assert EligibilityStatus.USER_REPORTED_MET.value == "user_reported_met"
        assert EligibilityStatus.NOT_APPLICABLE.value == "not_applicable"
    
    def test_user_progress_status_values(self):
        assert UserProgressStatus.UNKNOWN.value == "unknown"
        assert UserProgressStatus.MET.value == "met"
        assert UserProgressStatus.NOT_MET.value == "not_met"
        assert UserProgressStatus.IN_PROGRESS.value == "in_progress"
        assert UserProgressStatus.NOT_APPLICABLE.value == "not_applicable"
    
    def test_progress_status_values(self):
        assert ProgressStatus.POTENTIALLY_ELIGIBLE.value == "potentially_eligible"
        assert ProgressStatus.USER_REPORTED_MET.value == "user_reported_met"
        assert ProgressStatus.USER_REPORTED_NOT_MET.value == "user_reported_not_met"
        assert ProgressStatus.NOT_APPLICABLE.value == "not_applicable"
        assert ProgressStatus.CLAIM_AVAILABLE.value == "claim_available"
        assert ProgressStatus.CLAIMED.value == "claimed"
    
    def test_claim_status_values(self):
        assert ClaimStatus.PENDING.value == "pending"
        assert ClaimStatus.SUBMITTED.value == "submitted"
        assert ClaimStatus.CONFIRMED.value == "confirmed"
        assert ClaimStatus.FAILED.value == "failed"
        assert ClaimStatus.CANCELLED.value == "cancelled"