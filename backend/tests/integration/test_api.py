"""
API integration tests for all endpoints.
"""
import pytest
from uuid import uuid4
from datetime import datetime, UTC
from backend.core.models import (
    CampaignType, CampaignStatus, VerificationStatus, RiskLevel,
    SourceType, ScanRequest,
)


class TestHealthEndpoints:
    """Test health and launch endpoints."""
    
    def test_health_endpoint(self, client, auth_headers):
        """Test GET /api/v1/health"""
        response = client.get("/api/v1/health", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "database" in data
        assert "uptime_seconds" in data
    
    def test_launch_endpoint(self, client, auth_headers):
        """Test GET /api/v1/launch"""
        response = client.get("/api/v1/launch", headers=auth_headers)
        assert response.status_code == 200
        # /launch endpoint returns HTML page for browser mode
        assert "text/html" in response.headers.get("content-type", "")


class TestDashboardEndpoints:
    """Test dashboard endpoints."""
    
    def test_dashboard(self, client, auth_headers):
        """Test GET /api/v1/dashboard"""
        response = client.get("/api/v1/dashboard", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_campaigns" in data
        assert "tracked_campaigns" in data
        assert "verified_campaigns" in data
        assert "high_risk_campaigns" in data
        assert "recent_campaigns" in data
        assert "upcoming_deadlines" in data


class TestCampaignEndpoints:
    """Test campaign CRUD endpoints."""
    
    def test_list_campaigns(self, client, auth_headers):
        """Test GET /api/v1/campaigns"""
        response = client.get("/api/v1/campaigns", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "total_pages" in data
    
    def test_list_campaigns_with_filters(self, client, auth_headers):
        """Test GET /api/v1/campaigns with query parameters"""
        response = client.get(
            "/api/v1/campaigns?page=1&page_size=5&type=airdrop",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5
    
    def test_get_campaign(self, client, auth_headers, db_connection):
        """Test GET /api/v1/campaigns/{id}"""
        # Create a test campaign
        from backend.database.repositories.campaign import CampaignRepository
        from backend.core.models import CampaignCreate
        
        repo = CampaignRepository()
        campaign = CampaignCreate(
            name="Test Get Campaign",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created = repo.create(campaign)
        
        response = client.get(f"/api/v1/campaigns/{created.id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Get Campaign"
        assert data["id"] == str(created.id)
    
    def test_get_campaign_not_found(self, client, auth_headers):
        """Test GET /api/v1/campaigns/{id} returns 404 for non-existent"""
        response = client.get(f"/api/v1/campaigns/{uuid4()}", headers=auth_headers)
        assert response.status_code == 404
    
    def test_save_campaign(self, client, auth_headers, db_connection):
        """Test POST /api/v1/campaigns/{id}/save"""
        from backend.database.repositories.campaign import CampaignRepository
        from backend.core.models import CampaignCreate
        
        repo = CampaignRepository()
        campaign = CampaignCreate(
            name="Test Save Campaign",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created = repo.create(campaign)
        
        response = client.post(
            f"/api/v1/campaigns/{created.id}/save",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(created.id)


class TestSourceEndpoints:
    """Test source endpoints."""
    
    def test_list_sources(self, client, auth_headers):
        """Test GET /api/v1/sources"""
        response = client.get("/api/v1/sources", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_list_adapters(self, client, auth_headers):
        """Test GET /api/v1/adapters"""
        response = client.get("/api/v1/adapters", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 4  # CoinGecko, DefiLlama, GitHub, RSS
    
    def test_source_health(self, client, auth_headers, db_connection):
        """Test POST /api/v1/sources/{id}/health"""
        from backend.database.repositories.source import SourceRepository
        from backend.core.models import SourceCreate
        
        repo = SourceRepository()
        source = SourceCreate(
            name="Health Test Source",
            type=SourceType.API,
            base_url="https://api.example.com",
        )
        created = repo.create(source)
        
        response = client.post(
            f"/api/v1/sources/{created.id}/health",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "healthy" in data
        assert "checked_at" in data


class TestDiscoveryEndpoints:
    """Test discovery/scan endpoints."""
    
    def test_start_scan(self, client, auth_headers):
        """Test POST /api/v1/discovery/scans"""
        # Test with empty sources list (uses all enabled)
        response = client.post(
            "/api/v1/discovery/scans",
            headers=auth_headers,
            json={"sources": []}
        )
        # Scan may take time, accept 202 or 200
        assert response.status_code in (200, 202)
        data = response.json()
        assert "scan_id" in data
        assert "sources_scanned" in data
        assert "campaigns_found" in data
        assert "campaigns_new" in data
        assert "campaigns_updated" in data
        assert "errors" in data
    
    def test_get_scan_history(self, client, auth_headers):
        """Test GET /api/v1/discovery/scans"""
        response = client.get("/api/v1/discovery/scans", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestVerificationRiskEndpoints:
    """Test verification and risk endpoints."""
    
    def test_verification_get(self, client, auth_headers, db_connection):
        """Test GET /api/v1/campaigns/{id}/verification"""
        from backend.database.repositories.campaign import CampaignRepository
        from backend.core.models import CampaignCreate
        
        repo = CampaignRepository()
        campaign = CampaignCreate(
            name="Verification Test",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created = repo.create(campaign)
        
        response = client.get(
            f"/api/v1/campaigns/{created.id}/verification",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "verification_status" in data
        assert "confidence" in data
    
    def test_verification_trigger(self, client, auth_headers, db_connection):
        """Test POST /api/v1/campaigns/{id}/verify"""
        from backend.database.repositories.campaign import CampaignRepository
        from backend.core.models import CampaignCreate
        
        repo = CampaignRepository()
        campaign = CampaignCreate(
            name="Verify Trigger Test",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created = repo.create(campaign)
        
        response = client.post(
            f"/api/v1/campaigns/{created.id}/verify",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_risk_get(self, client, auth_headers, db_connection):
        """Test GET /api/v1/campaigns/{id}/risk"""
        from backend.database.repositories.campaign import CampaignRepository
        from backend.core.models import CampaignCreate
        
        repo = CampaignRepository()
        campaign = CampaignCreate(
            name="Risk Test",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created = repo.create(campaign)
        
        response = client.get(
            f"/api/v1/campaigns/{created.id}/risk",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "risk_score" in data
        assert "risk_level" in data
    
    def test_risk_trigger(self, client, auth_headers, db_connection):
        """Test POST /api/v1/campaigns/{id}/assess-risk"""
        from backend.database.repositories.campaign import CampaignRepository
        from backend.core.models import CampaignCreate
        
        repo = CampaignRepository()
        campaign = CampaignCreate(
            name="Risk Trigger Test",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created = repo.create(campaign)
        
        response = client.post(
            f"/api/v1/campaigns/{created.id}/assess-risk",
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_list_risk_rules(self, client, auth_headers):
        """Test GET /api/v1/risk/rules"""
        response = client.get("/api/v1/risk/rules", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 15  # Default risk rules
    
    def test_domain_verify(self, client, auth_headers):
        """Test GET /api/v1/domain/verify"""
        response = client.get(
            "/api/v1/domain/verify?url=https://example.com",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "domain" in data
        assert "is_official" in data


class TestEligibilityEndpoints:
    """Test eligibility endpoints."""
    
    def test_eligibility_list(self, client, auth_headers, db_connection):
        """Test GET /api/v1/campaigns/{id}/eligibility"""
        from backend.database.repositories.campaign import CampaignRepository
        from backend.core.models import CampaignCreate
        
        repo = CampaignRepository()
        campaign = CampaignCreate(
            name="Eligibility Test",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created = repo.create(campaign)
        
        response = client.get(
            f"/api/v1/campaigns/{created.id}/eligibility",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_progress_list(self, client, auth_headers, db_connection):
        """Test GET /api/v1/campaigns/{id}/progress"""
        from backend.database.repositories.campaign import CampaignRepository
        from backend.core.models import CampaignCreate
        
        repo = CampaignRepository()
        campaign = CampaignCreate(
            name="Progress Test",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created = repo.create(campaign)
        
        response = client.get(
            f"/api/v1/campaigns/{created.id}/progress",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_claims_list(self, client, auth_headers, db_connection):
        """Test GET /api/v1/campaigns/{id}/claims"""
        from backend.database.repositories.campaign import CampaignRepository
        from backend.core.models import CampaignCreate
        
        repo = CampaignRepository()
        campaign = CampaignCreate(
            name="Claims Test",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created = repo.create(campaign)
        
        response = client.get(
            f"/api/v1/campaigns/{created.id}/claims",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_events_list(self, client, auth_headers, db_connection):
        """Test GET /api/v1/campaigns/{id}/events"""
        from backend.database.repositories.campaign import CampaignRepository
        from backend.core.models import CampaignCreate
        
        repo = CampaignRepository()
        campaign = CampaignCreate(
            name="Events Test",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created = repo.create(campaign)
        
        response = client.get(
            f"/api/v1/campaigns/{created.id}/events",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_notification_prefs(self, client, auth_headers, db_connection):
        """Test GET /api/v1/campaigns/{id}/notification-prefs"""
        from backend.database.repositories.campaign import CampaignRepository
        from backend.core.models import CampaignCreate
        
        repo = CampaignRepository()
        campaign = CampaignCreate(
            name="Prefs Test",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created = repo.create(campaign)
        
        response = client.get(
            f"/api/v1/campaigns/{created.id}/notification-prefs",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "notify_deadline" in data


class TestCategoryEndpoints:
    """Test category-specific endpoints (NFT, Testnet, Reward)."""
    
    def test_nft_detail_wrong_type(self, client, auth_headers, db_connection):
        """Test GET /api/v1/campaigns/{id}/nft for non-NFT campaign returns 400"""
        from backend.database.repositories.campaign import CampaignRepository
        from backend.core.models import CampaignCreate
        
        repo = CampaignRepository()
        campaign = CampaignCreate(
            name="NFT Wrong Type",
            project="Test Project",
            type=CampaignType.AIRDROP,  # Not NFT
            network="Ethereum",
        )
        created = repo.create(campaign)
        
        response = client.get(
            f"/api/v1/campaigns/{created.id}/nft",
            headers=auth_headers
        )
        assert response.status_code == 400
    
    def test_testnet_detail_wrong_type(self, client, auth_headers, db_connection):
        """Test GET /api/v1/campaigns/{id}/testnet for non-testnet campaign returns 400"""
        from backend.database.repositories.campaign import CampaignRepository
        from backend.core.models import CampaignCreate
        
        repo = CampaignRepository()
        campaign = CampaignCreate(
            name="Testnet Wrong Type",
            project="Test Project",
            type=CampaignType.AIRDROP,  # Not testnet
            network="Ethereum",
        )
        created = repo.create(campaign)
        
        response = client.get(
            f"/api/v1/campaigns/{created.id}/testnet",
            headers=auth_headers
        )
        assert response.status_code == 400
    
    def test_reward_detail(self, client, auth_headers, db_connection):
        """Test GET /api/v1/campaigns/{id}/reward for reward campaign"""
        from backend.database.repositories.campaign import CampaignRepository
        from backend.core.models import CampaignCreate
        
        repo = CampaignRepository()
        campaign = CampaignCreate(
            name="Reward Test",
            project="Test Project",
            type=CampaignType.REWARD,
            network="Ethereum",
        )
        created = repo.create(campaign)
        
        response = client.get(
            f"/api/v1/campaigns/{created.id}/reward",
            headers=auth_headers
        )
        # Reward campaign should return 200 with data (even if empty)
        assert response.status_code == 200
        data = response.json()
        assert "token_symbol" in data
    
    def test_category_data(self, client, auth_headers, db_connection):
        """Test GET /api/v1/campaigns/{id}/category-data"""
        from backend.database.repositories.campaign import CampaignRepository
        from backend.core.models import CampaignCreate
        
        repo = CampaignRepository()
        
        # Test with airdrop campaign (no category data) - should return 404
        campaign = CampaignCreate(
            name="Category Data Test",
            project="Test Project",
            type=CampaignType.AIRDROP,
            network="Ethereum",
        )
        created = repo.create(campaign)
        
        response = client.get(
            f"/api/v1/campaigns/{created.id}/category-data",
            headers=auth_headers
        )
        assert response.status_code == 404
        
        # Test with NFT campaign (should have category data)
        nft_campaign = CampaignCreate(
            name="NFT Category Test",
            project="Test Project",
            type=CampaignType.NFT,
            network="Ethereum",
        )
        created_nft = repo.create(nft_campaign)
        
        response = client.get(
            f"/api/v1/campaigns/{created_nft.id}/category-data",
            headers=auth_headers
        )
        # NFT campaign should have category data
        assert response.status_code == 200
        data = response.json()
        # NFT category data has collection_name, collection_slug, etc.
        assert "collection_name" in data


class TestBackupEndpoints:
    """Test backup endpoints."""
    
    def test_create_backup(self, client, auth_headers):
        """Test POST /api/v1/backup"""
        response = client.post("/api/v1/backup", headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert "backup_path" in data
        assert "size_bytes" in data
        assert "created_at" in data
        assert "integrity_verified" in data
    
    def test_list_backups(self, client, auth_headers):
        """Test GET /api/v1/backups"""
        response = client.get("/api/v1/backups", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestAuthValidation:
    """Test authentication validation."""
    
    def test_missing_token(self, client):
        """Test endpoints reject requests without token"""
        response = client.get("/api/v1/dashboard")
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "MISSING_TOKEN"
    
    def test_invalid_token(self, client):
        """Test endpoints reject invalid token"""
        response = client.get(
            "/api/v1/dashboard",
            headers={"X-Local-API-Token": "invalid-token"}
        )
        assert response.status_code == 401
        data = response.json()
        assert data["error"]["code"] == "INVALID_TOKEN"
    
    def test_valid_token(self, client, auth_headers):
        """Test endpoints accept valid token"""
        response = client.get("/api/v1/dashboard", headers=auth_headers)
        assert response.status_code == 200