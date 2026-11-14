#!/usr/bin/env python3
"""
Demo/Test Fixtures for Global Airdrop Hunter

This script creates clearly labelled demo/test data that is never mixed with real data.
All demo records are prefixed with "[DEMO]" and have source_id="demo".
"""

import sys
import uuid
from datetime import datetime, timedelta

sys.path.insert(0, r'E:\Global Airdrop Hunter\backend')

from backend.database import get_db
from backend.core.models import (
    CampaignType, CampaignStatus, VerificationStatus, RiskLevel,
    Evidence, RiskFinding, EligibilityRequirement
)
from backend.database.repositories import campaign_repository


def create_demo_campaigns():
    """Create demo campaigns with full data including evidence, risk findings, and eligibility."""
    
    demo_campaigns = [
        {
            "name": "[DEMO] Ethereum Mainnet Airdrop - Arbitrum Ecosystem",
            "project": "Arbitrum Foundation",
            "type": CampaignType.AIRDROP,
            "network": "Arbitrum",
            "description": "Official ARB token distribution to early Arbitrum users and contributors. Distribution based on on-chain activity, governance participation, and bridging volume.",
            "official_url": "https://arbitrum.foundation/airdrop",
            "campaign_url": "https://claim.arbitrum.foundation",
            "status": CampaignStatus.ACTIVE,
            "verification_status": VerificationStatus.OFFICIAL,
            "risk_level": RiskLevel.LOW,
            "risk_score": 15,
            "deadline": datetime.utcnow() + timedelta(days=90),
            "snapshot_date": datetime.utcnow() - timedelta(days=30),
            "evidence_urls": [
                "https://arbitrum.foundation/airdrop-announcement",
                "https://gov.arbitrum.foundation/t/arb-token-distribution/12345",
                "https://twitter.com/Arbitrum/status/1234567890"
            ],
            "risk_findings": [],
            "eligibility": [
                {"category": "on_chain_activity", "requirement": "Minimum 10 transactions on Arbitrum One before snapshot", "status": "confirmed", "evidence_url": "https://arbiscan.io/address/0x123...", "source": "Arbitrum Foundation"},
                {"category": "governance", "requirement": "Participated in at least 3 governance votes", "status": "confirmed", "evidence_url": "https://gov.arbitrum.foundation/votes", "source": "Arbitrum Foundation"},
                {"category": "bridging", "requirement": "Bridged assets from Ethereum to Arbitrum at least once", "status": "confirmed", "evidence_url": "https://bridge.arbitrum.io/history", "source": "Arbitrum Foundation"},
            ]
        },
        {
            "name": "[DEMO] Optimism OP Token Airdrop #2",
            "project": "Optimism Collective",
            "type": CampaignType.AIRDROP,
            "network": "Optimism",
            "description": "Second round of OP token distribution to Optimism users, builders, and community members. Rewards usage of OP Stack chains and governance participation.",
            "official_url": "https://optimism.io/airdrop-2",
            "campaign_url": "https://app.optimism.io/airdrop",
            "status": CampaignStatus.ACTIVE,
            "verification_status": VerificationStatus.OFFICIAL,
            "risk_level": RiskLevel.LOW,
            "risk_score": 10,
            "deadline": datetime.utcnow() + timedelta(days=60),
            "snapshot_date": datetime.utcnow() - timedelta(days=14),
            "evidence_urls": [
                "https://optimism.io/blog/airdrop-2-announcement",
                "https://gov.optimism.io/t/op-airdrop-2-details/67890"
            ],
            "risk_findings": [],
            "eligibility": [
                {"category": "usage", "requirement": "Used Optimism mainnet for at least 5 transactions", "status": "confirmed", "source": "Optimism Collective"},
                {"category": "governance", "requirement": "Delegated OP tokens or voted on proposals", "status": "confirmed", "source": "Optimism Collective"},
                {"category": "builder", "requirement": "Deployed contract or contributed to OP Stack repos", "status": "unknown", "source": "Optimism Collective"},
            ]
        },
        {
            "name": "[DEMO] Polygon NFT Collection - Polygon Punks",
            "project": "Polygon Studios",
            "type": CampaignType.NFT,
            "network": "Polygon",
            "description": "Official Polygon Punks NFT collection mint for early Polygon adopters. 10,000 unique generative art pieces with utility in Polygon ecosystem.",
            "official_url": "https://polygon.technology/nft/punks",
            "campaign_url": "https://mint.polygon.technology/punks",
            "status": CampaignStatus.ACTIVE,
            "verification_status": VerificationStatus.OFFICIAL,
            "risk_level": RiskLevel.LOW,
            "risk_score": 5,
            "deadline": datetime.utcnow() + timedelta(days=30),
            "snapshot_date": None,
            "evidence_urls": [
                "https://blog.polygon.technology/polygon-punks-launch",
                "https://opensea.io/collection/polygon-punks"
            ],
            "risk_findings": [],
            "eligibility": [
                {"category": "wallet", "requirement": "Holds at least 1 MATIC in wallet", "status": "confirmed", "source": "Polygon Studios"},
                {"category": "activity", "requirement": "Completed at least 1 transaction on Polygon in last 90 days", "status": "confirmed", "source": "Polygon Studios"},
            ]
        },
        {
            "name": "[DEMO] Linea Testnet Voyage - Week 3",
            "project": "ConsenSys Linea",
            "type": CampaignType.TESTNET,
            "network": "Linea Sepolia",
            "description": "Week 3 of Linea Voyage testnet campaign. Complete tasks to earn LXP points for future token distribution.",
            "official_url": "https://linea.build/voyage",
            "campaign_url": "https://voyage.linea.build",
            "status": CampaignStatus.ACTIVE,
            "verification_status": VerificationStatus.OFFICIAL,
            "risk_level": RiskLevel.MEDIUM,
            "risk_score": 35,
            "deadline": datetime.utcnow() + timedelta(days=7),
            "snapshot_date": None,
            "evidence_urls": [
                "https://linea.build/blog/voyage-week-3",
                "https://discord.gg/linea"
            ],
            "risk_findings": [
                {
                    "rule_id": "testnet_effort",
                    "rule_version": 1,
                    "finding": "Testnet campaigns require significant time investment with no guaranteed reward",
                    "severity": RiskLevel.MEDIUM,
                    "description": "Testnet participation requires real time and gas fees (on Sepolia) with no guarantee of future token allocation.",
                    "evidence_url": "https://linea.build/terms"
                }
            ],
            "eligibility": [
                {"category": "wallet", "requirement": "Has Sepolia ETH for gas fees", "status": "confirmed", "source": "Linea"},
                {"category": "tasks", "requirement": "Complete 3 transactions on Linea Sepolia", "status": "confirmed", "source": "Linea"},
                {"category": "social", "requirement": "Follow Linea on Twitter and join Discord", "status": "user_reported_met", "source": "Linea"},
            ]
        },
        {
            "name": "[DEMO] Suspicious Airdrop - Fake Arbitrum Claim",
            "project": "Arbitrum Foundation (IMPERSONATED)",
            "type": CampaignType.AIRDROP,
            "network": "Arbitrum",
            "description": "CLAIM YOUR ARB TOKENS NOW! Limited time offer. Connect wallet and approve unlimited spending to receive 5000 ARB.",
            "official_url": "https://arbitrum-fake-claim.xyz",
            "campaign_url": "https://arbitrum-fake-claim.xyz/claim",
            "status": CampaignStatus.ACTIVE,
            "verification_status": VerificationStatus.SUSPICIOUS,
            "risk_level": RiskLevel.CRITICAL,
            "risk_score": 95,
            "deadline": datetime.utcnow() + timedelta(days=1),
            "snapshot_date": None,
            "evidence_urls": [
                "https://arbitrum-fake-claim.xyz"
            ],
            "risk_findings": [
                {
                    "rule_id": "credential_request",
                    "rule_version": 1,
                    "finding": "Campaign requests unlimited token approval and wallet connection to unknown contract",
                    "severity": RiskLevel.CRITICAL,
                    "description": "The claim page requests infinite token approval (setApprovalForAll) which could drain all tokens from connected wallet.",
                    "evidence_url": "https://arbitrum-fake-claim.xyz/claim"
                },
                {
                    "rule_id": "domain_impersonation",
                    "rule_version": 1,
                    "finding": "Domain 'arbitrum-fake-claim.xyz' impersonates official Arbitrum Foundation",
                    "severity": RiskLevel.CRITICAL,
                    "description": "Domain uses 'arbitrum' name but is not owned by Arbitrum Foundation. Official domain is arbitrum.foundation.",
                    "evidence_url": "https://whois.domaintools.com/arbitrum-fake-claim.xyz"
                },
                {
                    "rule_id": "upfront_payment",
                    "rule_version": 1,
                    "finding": "Requires gas payment to claim 'free' tokens",
                    "severity": RiskLevel.HIGH,
                    "description": "Claims to be free but requires users to pay gas fees for malicious contract interaction.",
                    "evidence_url": "https://arbitrum-fake-claim.xyz/claim"
                },
                {
                    "rule_id": "unrealistic_guarantee",
                    "rule_version": 1,
                    "finding": "Promises guaranteed 5000 ARB tokens with no eligibility criteria",
                    "severity": RiskLevel.HIGH,
                    "description": "Legitimate airdrops have specific eligibility criteria. Guaranteed large amounts with no criteria is a hallmark of scams.",
                    "evidence_url": "https://arbitrum-fake-claim.xyz"
                }
            ],
            "eligibility": [
                {"category": "wallet", "requirement": "Any wallet with ETH for gas", "status": "not_applicable", "source": "Scam site"},
                {"category": "approval", "requirement": "Approve unlimited token spending", "status": "not_met", "source": "Scam site"},
            ]
        },
        {
            "name": "[DEMO] Unverified DeFi Protocol Reward Program",
            "project": "YieldMax Protocol",
            "type": CampaignType.REWARD,
            "network": "BSC",
            "description": "New DeFi protocol offering 500% APY on stablecoin deposits. Deposit USDT/BUSD to earn YIELD tokens. Limited spots available.",
            "official_url": "https://yieldmax-defi.com",
            "campaign_url": "https://app.yieldmax-defi.com/deposit",
            "status": CampaignStatus.ACTIVE,
            "verification_status": VerificationStatus.UNVERIFIED,
            "risk_level": RiskLevel.HIGH,
            "risk_score": 75,
            "deadline": datetime.utcnow() + timedelta(days=14),
            "snapshot_date": None,
            "evidence_urls": [
                "https://yieldmax-defi.com/whitepaper",
                "https://twitter.com/YieldMaxDeFi"
            ],
            "risk_findings": [
                {
                    "rule_id": "unrealistic_guarantee",
                    "rule_version": 1,
                    "finding": "Promises 500% APY which is unsustainable and likely a Ponzi scheme",
                    "severity": RiskLevel.HIGH,
                    "description": "Sustainable DeFi yields typically range 5-20%. 500% APY requires constant new deposits to pay existing users.",
                    "evidence_url": "https://yieldmax-defi.com/apy-calculator"
                },
                {
                    "rule_id": "anonymous_team",
                    "rule_version": 1,
                    "finding": "Team is completely anonymous with no verifiable identities",
                    "severity": RiskLevel.MEDIUM,
                    "description": "No team members listed on website, no LinkedIn profiles, no previous project history.",
                    "evidence_url": "https://yieldmax-defi.com/team"
                },
                {
                    "rule_id": "unverified_contract",
                    "rule_version": 1,
                    "finding": "Deposit contract not verified on BscScan",
                    "severity": RiskLevel.HIGH,
                    "description": "Main deposit contract at 0x123... has no verified source code on BscScan.",
                    "evidence_url": "https://bscscan.com/address/0x123..."
                },
                {
                    "rule_id": "no_primary_evidence",
                    "rule_version": 1,
                    "finding": "No audit reports or security reviews from reputable firms",
                    "severity": RiskLevel.MEDIUM,
                    "description": "Claims 'audited' but no audit report links or auditor names provided.",
                    "evidence_url": "https://yieldmax-defi.com/security"
                }
            ],
            "eligibility": [
                {"category": "deposit", "requirement": "Minimum 100 USDT/BUSD deposit", "status": "unknown", "source": "YieldMax"},
                {"category": "lockup", "requirement": "90-day lockup period for maximum APY", "status": "unknown", "source": "YieldMax"},
            ]
        }
    ]

    created = 0
    for campaign_data in demo_campaigns:
        # Extract special fields
        evidence_urls = campaign_data.pop("evidence_urls", [])
        risk_findings_data = campaign_data.pop("risk_findings", [])
        eligibility_data = campaign_data.pop("eligibility", [])

        # Create campaign
        from backend.core.models import CampaignCreate
        campaign_create = CampaignCreate(**campaign_data, source_id="demo", evidence_urls=evidence_urls)
        campaign = campaign_repository.create(campaign_create, source_id="demo")

        # Add risk findings
        for rf_data in risk_findings_data:
            finding = RiskFinding(
                id=uuid.uuid4(),
                campaign_id=campaign.id,
                **rf_data
            )
            campaign_repository.add_risk_finding(str(campaign.id), finding)

        # Add eligibility requirements
        for e_data in eligibility_data:
            eligibility = EligibilityRequirement(
                id=uuid.uuid4(),
                campaign_id=campaign.id,
                **e_data
            )
            campaign_repository.add_eligibility(str(campaign.id), eligibility)

        created += 1
        print(f"Created: {campaign.name}")

    print(f"\nTotal demo campaigns created: {created}")


if __name__ == "__main__":
    create_demo_campaigns()