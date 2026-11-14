"""
Unit tests for repository layer.
"""
import pytest
from backend.database.repositories.campaign import CampaignRepository
from backend.database.repositories.source import SourceRepository
from backend.database.repositories.eligibility import EligibilityRepository, UserProgressRepository, ClaimRepository
from backend.core.models import (
    CampaignCreate, CampaignUpdate, CampaignFilters, PaginationParams,
    SourceCreate, SourceUpdate, SourceType,
    CampaignType, CampaignStatus, VerificationStatus, RiskLevel,
    EligibilityRequirement, EligibilityStatus, ProgressStatus,
    UserProgressStatus, UserEligibilityProgress,
)


class TestCampaignRepository:
    """Test CampaignRepository."""
    
    def test_create_campaign(self, db_connection):
        """Test creating a campaign."""
        repo = CampaignRepository()
        campaign = CampaignCreate(
            name="Repo Test Campaign",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
            description="Test description",
            official_url="https://example.com",
            campaign_url="https://example.com/campaign",
        )
        created = repo.create(campaign, source_id="test-source")
        
        assert created.id is not None
        assert created.stable_id is not None
        assert created.name == "Repo Test Campaign"
        assert created.project == "Test Project"
        assert created.type == CampaignType.AIRDROP
        assert created.status == CampaignStatus.ACTIVE
        assert created.verification_status == VerificationStatus.UNVERIFIED
        assert created.risk_level == RiskLevel.MEDIUM  # default
        assert created.risk_score == 50  # default
    
    def test_get_by_id(self, db_connection):
        """Test getting campaign by ID."""
        repo = CampaignRepository()
        campaign = CampaignCreate(
            name="Get By ID Test",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created = repo.create(campaign)
        
        found = repo.get_by_id(str(created.id))
        assert found is not None
        assert found.id == created.id
        assert found.name == "Get By ID Test"
    
    def test_get_by_id_not_found(self, db_connection):
        """Test getting non-existent campaign returns None."""
        repo = CampaignRepository()
        found = repo.get_by_id("non-existent-id")
        assert found is None
    
    def test_get_by_stable_id(self, db_connection):
        """Test getting campaign by stable ID."""
        repo = CampaignRepository()
        campaign = CampaignCreate(
            name="Stable ID Test",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created = repo.create(campaign)
        
        found = repo.get_by_stable_id(created.stable_id)
        assert found is not None
        assert found.stable_id == created.stable_id
    
    def test_update_campaign(self, db_connection):
        """Test updating a campaign."""
        repo = CampaignRepository()
        campaign = CampaignCreate(
            name="Update Test",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created = repo.create(campaign)
        
        update = CampaignUpdate(
            description="Updated description",
            risk_score=75,
        )
        updated = repo.update(str(created.id), update)
        
        assert updated is not None
        assert updated.description == "Updated description"
        assert updated.risk_score == 75
        assert updated.name == "Update Test"  # unchanged
    
    def test_update_not_found(self, db_connection):
        """Test updating non-existent campaign returns None."""
        repo = CampaignRepository()
        update = CampaignUpdate(description="Won't work")
        result = repo.update("non-existent-id", update)
        assert result is None
    
    def test_delete_campaign(self, db_connection):
        """Test deleting a campaign."""
        repo = CampaignRepository()
        campaign = CampaignCreate(
            name="Delete Test",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created = repo.create(campaign)
        
        deleted = repo.delete(str(created.id))
        assert deleted is True
        
        # Verify deleted
        found = repo.get_by_id(str(created.id))
        assert found is None
    
    def test_delete_not_found(self, db_connection):
        """Test deleting non-existent campaign returns False."""
        repo = CampaignRepository()
        deleted = repo.delete("non-existent-id")
        assert deleted is False
    
    def test_list_campaigns(self, db_connection):
        """Test listing campaigns with filters."""
        repo = CampaignRepository()
        
        # Create multiple campaigns
        for i in range(5):
            campaign = CampaignCreate(
                name=f"List Test {i}",
                project="Test Project",
                type=CampaignType.AIRDROP if i % 2 == 0 else CampaignType.NFT,
                network="Ethereum" if i % 2 == 0 else "Polygon",
            )
            repo.create(campaign)
        
        # List all
        filters = CampaignFilters()
        pagination = PaginationParams(page=1, page_size=10)
        result = repo.list(filters, pagination)
        
        assert result.total >= 5
        assert len(result.items) >= 5
        
        # Filter by type
        filters = CampaignFilters(type=CampaignType.AIRDROP)
        result = repo.list(filters, pagination)
        assert all(c.type == CampaignType.AIRDROP for c in result.items)
        
        # Filter by network
        filters = CampaignFilters(network="Polygon")
        result = repo.list(filters, pagination)
        assert all(c.network == "Polygon" for c in result.items)
    
    def test_list_with_search(self, db_connection):
        """Test listing with search query."""
        repo = CampaignRepository()
        campaign = CampaignCreate(
            name="Unique Searchable Name",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        repo.create(campaign)
        
        filters = CampaignFilters(search="Unique Searchable")
        pagination = PaginationParams(page=1, page_size=10)
        result = repo.list(filters, pagination)
        
        assert result.total >= 1
        assert any("Unique Searchable" in c.name for c in result.items)
    
    def test_get_stats(self, db_connection):
        """Test getting campaign statistics."""
        repo = CampaignRepository()
        stats = repo.get_stats()
        
        assert "total_campaigns" in stats
        assert "tracked_campaigns" in stats
        assert "verified_campaigns" in stats
        assert "high_risk_campaigns" in stats
    
    def test_get_recent(self, db_connection):
        """Test getting recent campaigns."""
        repo = CampaignRepository()
        recent = repo.get_recent(5)
        assert isinstance(recent, list)
        assert len(recent) <= 5
    
    def test_get_upcoming_deadlines(self, db_connection):
        """Test getting upcoming deadlines."""
        repo = CampaignRepository()
        deadlines = repo.get_upcoming_deadlines(5)
        assert isinstance(deadlines, list)
        assert len(deadlines) <= 5


class TestSourceRepository:
    """Test SourceRepository."""
    
    def test_create_source(self, db_connection):
        """Test creating a source."""
        repo = SourceRepository()
        source = SourceCreate(
            name="Repo Test Source",
            type=SourceType.API,
            base_url="https://api.example.com",
            config={"key": "value"},
            rate_limit=60,
            timeout=30,
        )
        created = repo.create(source)
        
        assert created.id is not None
        assert created.name == "Repo Test Source"
        assert created.type == SourceType.API
        assert created.rate_limit == 60
        assert created.enabled is True
    
    def test_get_by_id(self, db_connection):
        """Test getting source by ID."""
        repo = SourceRepository()
        source = SourceCreate(
            name="Get By ID Source",
            type=SourceType.RSS,
            base_url="https://example.com/feed.xml",
        )
        created = repo.create(source)
        
        found = repo.get_by_id(created.id)
        assert found is not None
        assert found.id == created.id
    
    def test_get_by_name(self, db_connection):
        """Test getting source by name."""
        repo = SourceRepository()
        source = SourceCreate(
            name="Unique Source Name",
            type=SourceType.API,
            base_url="https://api.example.com",
        )
        created = repo.create(source)
        
        found = repo.get_by_name("Unique Source Name")
        assert found is not None
        assert found.name == "Unique Source Name"
    
    def test_list_sources(self, db_connection):
        """Test listing sources."""
        repo = SourceRepository()
        
        for i in range(3):
            source = SourceCreate(
                name=f"List Source {i}",
                type=SourceType.API,
                base_url=f"https://api{i}.example.com",
            )
            repo.create(source)
        
        sources = repo.list()
        assert len(sources) >= 3
        
        enabled_only = repo.list(enabled_only=True)
        assert len(enabled_only) >= 3
    
    def test_update_source(self, db_connection):
        """Test updating a source."""
        repo = SourceRepository()
        source = SourceCreate(
            name="Update Source",
            type=SourceType.API,
            base_url="https://api.example.com",
        )
        created = repo.create(source)
        
        update = SourceUpdate(rate_limit=120, enabled=False)
        updated = repo.update(created.id, update)
        
        assert updated is not None
        assert updated.rate_limit == 120
        assert updated.enabled is False
    
    def test_update_health_check(self, db_connection):
        """Test updating health check status."""
        repo = SourceRepository()
        source = SourceCreate(
            name="Health Check Source",
            type=SourceType.API,
            base_url="https://api.example.com",
        )
        created = repo.create(source)
        
        repo.update_health_check(created.id, True)
        found = repo.get_by_id(created.id)
        assert found.consecutive_failures == 0
        assert found.last_health_check is not None
        
        repo.update_health_check(created.id, False)
        found = repo.get_by_id(created.id)
        assert found.consecutive_failures == 1
    
    def test_update_scan_stats(self, db_connection):
        """Test updating scan statistics."""
        repo = SourceRepository()
        source = SourceCreate(
            name="Scan Stats Source",
            type=SourceType.API,
            base_url="https://api.example.com",
        )
        created = repo.create(source)
        
        repo.update_scan_stats(created.id, 5)
        found = repo.get_by_id(created.id)
        assert found.total_records == 5
        assert found.last_scan is not None
    
    def test_get_enabled_sources(self, db_connection):
        """Test getting enabled sources."""
        repo = SourceRepository()
        
        source1 = SourceCreate(name="Enabled Source", type=SourceType.API, base_url="https://a.com")
        source2 = SourceCreate(name="Disabled Source", type=SourceType.API, base_url="https://b.com")
        
        created1 = repo.create(source1)
        created2 = repo.create(source2)
        
        repo.update(created2.id, SourceUpdate(enabled=False))
        
        enabled = repo.get_enabled_sources()
        enabled_names = [s.name for s in enabled]
        assert "Enabled Source" in enabled_names
        assert "Disabled Source" not in enabled_names
    
    def test_delete_source(self, db_connection):
        """Test deleting a source."""
        repo = SourceRepository()
        source = SourceCreate(
            name="Delete Source",
            type=SourceType.API,
            base_url="https://api.example.com",
        )
        created = repo.create(source)
        
        deleted = repo.delete(created.id)
        assert deleted is True
        
        found = repo.get_by_id(created.id)
        assert found is None


class TestEligibilityRepository:
    """Test EligibilityRepository."""
    
    def test_create_requirement(self, db_connection):
        """Test creating an eligibility requirement."""
        repo = EligibilityRepository()
        
        # First create a campaign
        from backend.database.repositories.campaign import CampaignRepository
        camp_repo = CampaignRepository()
        campaign = CampaignCreate(
            name="Eligibility Test Campaign",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created_campaign = camp_repo.create(campaign)
        
        # Create requirement
        req = EligibilityRequirement(
            campaign_id=str(created_campaign.id),
            category="social",
            requirement="Follow Twitter",
            status=EligibilityStatus.UNKNOWN,
            progress_status=ProgressStatus.POTENTIALLY_ELIGIBLE,
        )
        created = repo.create_for_campaign(str(created_campaign.id), req)
        
        assert created.id is not None
        assert created.category == "social"
        assert created.requirement == "Follow Twitter"
    
    def test_get_by_campaign(self, db_connection):
        """Test getting requirements by campaign."""
        repo = EligibilityRepository()
        camp_repo = CampaignRepository()
        
        campaign = CampaignCreate(
            name="Requirements Campaign",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created_campaign = camp_repo.create(campaign)
        
        for i in range(3):
            req = EligibilityRequirement(
                campaign_id=str(created_campaign.id),
                category="social",
                requirement=f"Requirement {i}",
                status=EligibilityStatus.UNKNOWN,
            )
            repo.create_for_campaign(str(created_campaign.id), req)
        
        requirements = repo.get_by_campaign(str(created_campaign.id))
        assert len(requirements) == 3


class TestUserProgressRepository:
    """Test UserProgressRepository."""
    
    def test_upsert_progress(self, db_connection):
        """Test upserting user progress."""
        repo = UserProgressRepository()
        camp_repo = CampaignRepository()
        elig_repo = EligibilityRepository()
        
        campaign = CampaignCreate(
            name="Progress Campaign",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created_campaign = camp_repo.create(campaign)
        
        req = EligibilityRequirement(
            campaign_id=str(created_campaign.id),
            category="social",
            requirement="Follow Twitter",
            status=EligibilityStatus.UNKNOWN,
        )
        created_req = elig_repo.create_for_campaign(str(created_campaign.id), req)
        
        progress = UserEligibilityProgress(
            campaign_id=str(created_campaign.id),
            requirement_id=str(created_req.id),
            user_status=UserProgressStatus.IN_PROGRESS,
            user_notes="Started following",
        )
        upserted = repo.upsert(progress)
        
        assert upserted.id is not None
        assert upserted.user_status == UserProgressStatus.IN_PROGRESS
        
        # Update progress
        progress.user_status = UserProgressStatus.MET
        upserted2 = repo.upsert(progress)
        assert upserted2.user_status == UserProgressStatus.MET
    
    def test_get_by_campaign(self, db_connection):
        """Test getting user progress by campaign."""
        repo = UserProgressRepository()
        camp_repo = CampaignRepository()
        elig_repo = EligibilityRepository()
        
        campaign = CampaignCreate(
            name="Progress Get Campaign",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created_campaign = camp_repo.create(campaign)
        
        req = EligibilityRequirement(
            campaign_id=str(created_campaign.id),
            category="social",
            requirement="Follow Twitter",
            status=EligibilityStatus.UNKNOWN,
        )
        created_req = elig_repo.create_for_campaign(str(created_campaign.id), req)
        
        progress = UserEligibilityProgress(
            campaign_id=str(created_campaign.id),
            requirement_id=str(created_req.id),
            user_status=UserProgressStatus.MET,
        )
        repo.upsert(progress)
        
        progress_list = repo.get_by_campaign(str(created_campaign.id))
        assert len(progress_list) == 1
        assert progress_list[0].user_status == UserProgressStatus.MET


class TestClaimRepository:
    """Test ClaimRepository."""
    
    def test_create_claim(self, db_connection):
        """Test creating a claim."""
        repo = ClaimRepository()
        camp_repo = CampaignRepository()
        
        campaign = CampaignCreate(
            name="Claim Campaign",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created_campaign = camp_repo.create(campaign)
        
        from backend.core.models import CampaignClaim, ClaimStatus
        claim = CampaignClaim(
            campaign_id=str(created_campaign.id),
            claim_type="airdrop",
            claim_url="https://example.com/claim",
            transaction_hash="0x123...",
            network="Ethereum",
            status=ClaimStatus.SUBMITTED,
        )
        created = repo.create(claim)
        
        assert created.id is not None
        assert created.claim_type == "airdrop"
        assert created.status == ClaimStatus.SUBMITTED
    
    def test_get_by_campaign(self, db_connection):
        """Test getting claims by campaign."""
        repo = ClaimRepository()
        camp_repo = CampaignRepository()
        
        campaign = CampaignCreate(
            name="Claims Campaign",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created_campaign = camp_repo.create(campaign)
        
        from backend.core.models import CampaignClaim, ClaimStatus
        for i in range(2):
            claim = CampaignClaim(
                campaign_id=str(created_campaign.id),
                claim_type="airdrop",
                status=ClaimStatus.SUBMITTED,
            )
            repo.create(claim)
        
        claims = repo.get_by_campaign(str(created_campaign.id))
        assert len(claims) == 2