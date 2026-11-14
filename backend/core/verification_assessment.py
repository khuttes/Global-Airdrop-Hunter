"""
Verification assessment service for Global Airdrop Hunter.
Determines verification status based on evidence quality and source authority.
"""

import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from backend.database.connection import get_db
from backend.database.repositories import campaign_repository
from backend.core.verification import domain_verification_service
from backend.core.risk import risk_engine


class VerificationService:
    """Service for assessing campaign verification status."""

    VERIFICATION_STATES = [
        "officially_corroborated",
        "independently_corroborated",
        "unverified",
        "suspicious",
        "expired",
        "withdrawn"
    ]

    # Minimum evidence requirements per state
    EVIDENCE_REQUIREMENTS = {
        "officially_corroborated": {
            "min_primary_sources": 1,
            "min_secondary_sources": 0,
            "requires_official_domain": True,
            "max_risk_level": "medium"
        },
        "independently_corroborated": {
            "min_primary_sources": 0,
            "min_secondary_sources": 2,
            "requires_official_domain": False,
            "max_risk_level": "high"
        },
        "unverified": {
            "min_primary_sources": 0,
            "min_secondary_sources": 0,
            "requires_official_domain": False,
            "max_risk_level": "critical"
        },
        "suspicious": {
            "min_primary_sources": 0,
            "min_secondary_sources": 0,
            "requires_official_domain": False,
            "max_risk_level": "critical"
        },
        "expired": {
            "min_primary_sources": 0,
            "min_secondary_sources": 0,
            "requires_official_domain": False,
            "max_risk_level": "critical"
        },
        "withdrawn": {
            "min_primary_sources": 0,
            "min_secondary_sources": 0,
            "requires_official_domain": False,
            "max_risk_level": "critical"
        }
    }

    def __init__(self):
        pass

    async def assess_verification(self, campaign_id: str) -> Dict[str, Any]:
        """
        Assess and update verification status for a campaign.
        """
        campaign = campaign_repository.get_by_id(campaign_id)
        if not campaign:
            return {"error": "Campaign not found"}

        # Get risk assessment
        risk_assessment = risk_engine.assess_campaign(campaign_id)
        
        # Analyze evidence
        evidence_analysis = await self._analyze_evidence(campaign)
        
        # Check domain verification for official URLs
        domain_results = await self._check_domains(campaign)

        # Determine verification status
        status, confidence = self._determine_status(
            campaign, risk_assessment, evidence_analysis, domain_results
        )

        # Create verification record
        verification = {
            "campaign_id": campaign_id,
            "verification_status": status,
            "confidence": confidence,
            "primary_evidence_urls": json.dumps(evidence_analysis["primary"]),
            "secondary_evidence_urls": json.dumps(evidence_analysis["secondary"]),
            "assessed_by": "system",
            "assessed_at": datetime.utcnow().isoformat(),
            "notes": self._generate_notes(evidence_analysis, domain_results, risk_assessment)
        }

        # Store verification
        self._store_verification(verification)

        # Update campaign verification status
        self._update_campaign_verification(campaign_id, status)

        return verification

    async def _analyze_evidence(self, campaign) -> Dict[str, Any]:
        """Analyze campaign evidence and categorize sources."""
        primary = []
        secondary = []

        for evidence in campaign.evidence:
            url = str(evidence.url)  # Convert HttpUrl to string
            source_type = evidence.source_type
            is_verified = evidence.verified

            # Classify source
            if self._is_official_source(url):
                primary.append({
                    "url": url,
                    "source_type": source_type,
                    "title": evidence.title,
                    "verified": is_verified,
                    "reason": "official_domain"
                })
            elif source_type == "api" and evidence.verified:
                primary.append({
                    "url": url,
                    "source_type": source_type,
                    "title": evidence.title,
                    "verified": is_verified,
                    "reason": "verified_api"
                })
            elif source_type == "github" and self._is_official_github(url):
                primary.append({
                    "url": url,
                    "source_type": source_type,
                    "title": evidence.title,
                    "verified": is_verified,
                    "reason": "official_github"
                })
            else:
                secondary.append({
                    "url": url,
                    "source_type": source_type,
                    "title": evidence.title,
                    "verified": is_verified,
                    "reason": "third_party"
                })

        return {"primary": primary, "secondary": secondary}

    def _is_official_source(self, url: str) -> bool:
        """Check if URL is from an official project domain."""
        from urllib.parse import urlparse
        try:
            domain = urlparse(url).netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]

            official_domains = {
                "ethereum.org", "arbitrum.io", "optimism.io", "polygon.technology",
                "base.org", "linea.build", "zksync.io", "scroll.io",
                "coinbase.com", "uniswap.org", "aave.com", "lido.fi"
            }

            return any(domain == d or domain.endswith("." + d) for d in official_domains)
        except Exception:
            return False

    def _is_official_github(self, url: str) -> bool:
        """Check if GitHub URL is from an official organization."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if "github.com" not in parsed.netloc:
                return False

            path_parts = parsed.path.strip("/").split("/")
            if len(path_parts) >= 1:
                org = path_parts[0].lower()
                official_orgs = {
                    "ethereum", "arbitrum", "optimism", "polygon", "base",
                    "linea", "zksync", "scroll", "coinbase", "uniswap",
                    "aave", "lidofinance"
                }
                return org in official_orgs
        except Exception:
            pass
        return False

    async def _check_domains(self, campaign) -> Dict[str, Any]:
        """Check domain verification for campaign URLs."""
        results = {}
        urls_to_check = []

        if campaign.official_url:
            urls_to_check.append(("official", campaign.official_url))
        if campaign.campaign_url:
            urls_to_check.append(("campaign", campaign.campaign_url))

        for label, url in urls_to_check:
            result = await domain_verification_service.verify_domain(url)
            results[label] = result

        return results

    def _determine_status(
        self,
        campaign,
        risk_assessment: Dict[str, Any],
        evidence_analysis: Dict[str, Any],
        domain_results: Dict[str, Any]
    ) -> Tuple[str, float]:
        """Determine verification status based on all factors."""
        
        # Check for critical risk override
        if risk_assessment.get("critical_override"):
            return "suspicious", 0.9

        # Count evidence
        primary_count = len(evidence_analysis["primary"])
        secondary_count = len(evidence_analysis["secondary"])

        # Check domain verification
        has_official_domain = any(
            r.get("is_official", False) for r in domain_results.values()
        )

        # Check risk level
        risk_level = risk_assessment.get("risk_level", "medium")

        # Determine status
        if primary_count >= 1 and has_official_domain and risk_level in ["low", "medium"]:
            return "officially_corroborated", 0.9
        
        elif primary_count >= 1 and risk_level in ["low", "medium"]:
            return "independently_corroborated", 0.75
        
        elif secondary_count >= 2 and risk_level != "critical":
            return "independently_corroborated", 0.65
        
        elif secondary_count >= 1 and risk_level == "low":
            return "independently_corroborated", 0.55
        
        elif risk_level == "critical" or risk_assessment.get("critical_override"):
            return "suspicious", 0.85
        
        elif risk_level == "high":
            return "suspicious", 0.6
        
        else:
            return "unverified", 0.3

    def _generate_notes(
        self,
        evidence_analysis: Dict[str, Any],
        domain_results: Dict[str, Any],
        risk_assessment: Dict[str, Any]
    ) -> str:
        """Generate human-readable assessment notes."""
        notes = []

        primary_count = len(evidence_analysis["primary"])
        secondary_count = len(evidence_analysis["secondary"])

        if primary_count > 0:
            notes.append(f"{primary_count} primary source(s) found")
        if secondary_count > 0:
            notes.append(f"{secondary_count} secondary source(s) found")

        for label, result in domain_results.items():
            if result.get("is_official"):
                notes.append(f"{label} URL verified as official")
            elif result.get("confidence", 0) > 0.5:
                notes.append(f"{label} URL partially verified (confidence: {result['confidence']:.0%})")

        if risk_assessment.get("critical_override"):
            notes.append("CRITICAL: Risk override triggered")

        risk_level = risk_assessment.get("risk_level", "unknown")
        notes.append(f"Risk level: {risk_level}")

        return "; ".join(notes)

    def _store_verification(self, verification: Dict[str, Any]) -> None:
        """Store verification assessment in database."""
        import uuid
        with get_db() as db:
            db.execute("""
                INSERT OR REPLACE INTO campaign_verification
                (id, campaign_id, verification_status, confidence, primary_evidence_urls, secondary_evidence_urls, assessed_by, assessed_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                verification["campaign_id"],
                verification["verification_status"],
                verification["confidence"],
                verification["primary_evidence_urls"],
                verification["secondary_evidence_urls"],
                verification["assessed_by"],
                verification["assessed_at"],
                verification["notes"]
            ))

    def _update_campaign_verification(self, campaign_id: str, status: str) -> None:
        """Update campaign's verification status."""
        from backend.core.models import CampaignUpdate, VerificationStatus
        update = CampaignUpdate(verification_status=VerificationStatus(status))
        campaign_repository.update(campaign_id, update)


verification_service = VerificationService()