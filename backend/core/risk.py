"""
Risk scoring engine for Global Airdrop Hunter.
Evaluates campaigns against risk rules and produces risk assessments.
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse

from backend.database.connection import get_db
from backend.database.repositories import campaign_repository


class RiskEngine:
    """Engine for evaluating campaign risk."""

    def __init__(self):
        self._rules_cache = None
        self._cache_time = None

    def _get_rules(self) -> List[Dict[str, Any]]:
        """Get active risk rules from database with caching."""
        now = datetime.utcnow()
        if self._rules_cache is None or self._cache_time is None or \
           (now - self._cache_time).total_seconds() > 300:  # 5 min cache
            with get_db() as db:
                rows = db.execute(
                    "SELECT * FROM risk_rules WHERE is_active = 1 ORDER BY weight DESC"
                ).fetchall()
                self._rules_cache = [dict(row) for row in rows]
                self._cache_time = now
        return self._rules_cache

    def assess_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Perform full risk assessment for a campaign.
        Returns risk assessment with findings.
        """
        campaign = campaign_repository.get_by_id(campaign_id)
        if not campaign:
            return {"error": "Campaign not found"}

        # Prepare campaign data for evaluation
        campaign_data = self._prepare_campaign_data(campaign)

        # Evaluate all rules
        findings = []
        total_score = 0
        critical_override = False
        high_count = 0
        critical_count = 0

        rules = self._get_rules()
        for rule in rules:
            triggered, match_details = self._evaluate_rule(rule, campaign_data)
            if triggered:
                finding = self._create_finding(campaign_id, rule, match_details)
                findings.append(finding)

                weight = rule["weight"]
                total_score += weight

                severity = rule["severity"]
                if severity == "high":
                    high_count += 1
                elif severity == "critical":
                    critical_count += 1

                if rule.get("is_critical_override", False):
                    critical_override = True

        # Calculate final risk level
        if critical_override:
            risk_level = "critical"
            risk_score = 100
        else:
            # Cap at 100
            risk_score = min(100, total_score)
            if risk_score >= 75:
                risk_level = "critical"
            elif risk_score >= 50:
                risk_level = "high"
            elif risk_score >= 25:
                risk_level = "medium"
            else:
                risk_level = "low"

        # Create assessment
        assessment = {
            "campaign_id": campaign_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "critical_override": critical_override,
            "total_findings": len(findings),
            "high_findings": high_count,
            "critical_findings": critical_count,
            "findings": findings,
            "assessed_at": datetime.utcnow().isoformat(),
            "assessed_by": "system"
        }

        # Store assessment
        self._store_assessment(assessment)
        self._store_findings(campaign_id, findings)

        # Auto-enqueue high-risk campaigns for false positive review
        from backend.core.false_positive_review import false_positive_review_queue
        trigger_rules = [f.get("rule_id", "") for f in findings if f.get("rule_id")]
        false_positive_review_queue.auto_enqueue_high_risk(
            campaign_id, risk_score, risk_level, trigger_rules
        )

        return assessment

    def _prepare_campaign_data(self, campaign) -> Dict[str, Any]:
        """Prepare campaign data for rule evaluation."""
        # Get evidence URLs
        evidence_urls = [str(e.url) for e in campaign.evidence]
        
        # Convert URL fields to strings
        official_url = str(campaign.official_url) if campaign.official_url else ""
        campaign_url = str(campaign.campaign_url) if campaign.campaign_url else ""
        
        # Combine all text content for content-based rules
        text_content = " ".join(filter(None, [
            campaign.name or "",
            campaign.project or "",
            campaign.description or "",
            official_url,
            campaign_url,
        ] + evidence_urls))

        return {
            "id": str(campaign.id),
            "name": campaign.name or "",
            "project": campaign.project or "",
            "type": campaign.type.value if hasattr(campaign.type, 'value') else str(campaign.type),
            "network": campaign.network or "",
            "description": campaign.description or "",
            "official_url": official_url,
            "campaign_url": campaign_url,
            "status": campaign.status.value if hasattr(campaign.status, 'value') else str(campaign.status),
            "verification_status": campaign.verification_status.value if hasattr(campaign.verification_status, 'value') else str(campaign.verification_status),
            "risk_level": campaign.risk_level.value if hasattr(campaign.risk_level, 'value') else str(campaign.risk_level),
            "evidence_urls": evidence_urls,
            "text_content": text_content.lower(),
            "deadline": campaign.deadline.isoformat() if campaign.deadline else None,
        }

    def _evaluate_rule(self, rule: Dict[str, Any], campaign_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Evaluate a single rule against campaign data."""
        logic_type = rule.get("logic_type", "custom")
        logic_config = rule.get("logic_config")
        
        if isinstance(logic_config, str):
            try:
                config = json.loads(logic_config)
            except json.JSONDecodeError:
                config = {}
        else:
            config = logic_config or {}

        if logic_type == "keyword":
            return self._evaluate_keyword_rule(config, campaign_data)
        elif logic_type == "domain_check":
            return self._evaluate_domain_check_rule(config, campaign_data)
        elif logic_type == "contract_check":
            return self._evaluate_contract_check_rule(config, campaign_data)
        elif logic_type == "content_similarity":
            return self._evaluate_content_similarity_rule(config, campaign_data)
        elif logic_type == "custom":
            return self._evaluate_custom_rule(rule, campaign_data)
        else:
            return False, {}

    def _evaluate_keyword_rule(self, config: Dict[str, Any], campaign_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Evaluate keyword-based rule."""
        keywords = config.get("keywords", [])
        text = campaign_data.get("text_content", "")
        
        matches = []
        for keyword in keywords:
            if keyword.lower() in text:
                matches.append(keyword)
        
        return len(matches) > 0, {"matched_keywords": matches}

    def _evaluate_domain_check_rule(self, config: Dict[str, Any], campaign_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Evaluate domain-based rules (typosquatting, etc.)."""
        official_url = campaign_data.get("official_url", "")
        campaign_url = campaign_data.get("campaign_url", "")
        project = campaign_data.get("project", "").lower()
        
        urls_to_check = [u for u in [official_url, campaign_url] if u]
        
        # Known official domains
        official_domains = {
            "ethereum.org", "arbitrum.io", "optimism.io", "polygon.technology",
            "base.org", "linea.build", "zksync.io", "scroll.io",
            "coinbase.com", "uniswap.org", "aave.com", "lido.fi"
        }

        for url in urls_to_check:
            try:
                domain = urlparse(url).netloc.lower()
                if domain.startswith("www."):
                    domain = domain[4:]
                
                # Check if domain mimics official domain
                for official in official_domains:
                    if self._is_typosquatting(domain, official):
                        return True, {"type": "typosquatting", "domain": domain, "target": official}
                    
                    # Check subdomain spoofing
                    if domain.endswith("." + official) and domain != official:
                        return True, {"type": "subdomain_spoofing", "domain": domain, "target": official}
            except Exception:
                pass
        
        return False, {}

    def _is_typosquatting(self, domain: str, official: str) -> bool:
        """Check if domain is a typosquat of official domain."""
        # Remove TLD for comparison
        domain_base = domain.split(".")[0]
        official_base = official.split(".")[0]
        
        # Levenshtein distance check (simplified)
        if len(domain_base) == len(official_base):
            diff = sum(c1 != c2 for c1, c2 in zip(domain_base, official_base))
            if diff == 1:  # Single character difference
                return True
        
        # Check common typosquatting patterns
        patterns = [
            official_base.replace("i", "1"),
            official_base.replace("o", "0"),
            official_base.replace("a", "@"),
            official_base + "app",
            official_base + "claim",
            official_base + "airdrop",
            "app-" + official_base,
            "claim-" + official_base,
        ]
        
        return domain_base in patterns

    def _evaluate_contract_check_rule(self, config: Dict[str, Any], campaign_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Evaluate contract-related rules."""
        # This would check contract verification status on block explorers
        # For now, return False - would need integration with explorer APIs
        return False, {}

    def _evaluate_content_similarity_rule(self, config: Dict[str, Any], campaign_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Evaluate content similarity (copy-paste detection)."""
        # This would compare against other campaigns
        # For now, return False - would need cross-campaign comparison
        return False, {}

    def _evaluate_custom_rule(self, rule: Dict[str, Any], campaign_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """Evaluate custom rules."""
        rule_id = rule.get("rule_id", "")
        
        if rule_id == "no_primary_evidence":
            # Check if campaign has official source evidence
            evidence = campaign_data.get("evidence_urls", [])
            has_official = any(self._is_official_source(url) for url in evidence)
            return not has_official, {"has_official_source": has_official}
        
        elif rule_id == "no_social_presence":
            # Check for social media presence
            # Simplified check
            return False, {}
        
        elif rule_id == "anonymous_team":
            # Check for team info
            return False, {}
        
        elif rule_id == "single_source":
            # Check if only one source
            evidence_count = len(campaign_data.get("evidence_urls", []))
            return evidence_count <= 1, {"evidence_count": evidence_count}
        
        elif rule_id == "unrealistic_guarantee":
            # Check for unrealistic claims in description
            text = campaign_data.get("text_content", "")
            unrealistic_phrases = [
                "guaranteed", "100% return", "risk free", "cannot lose",
                "guaranteed profit", "fixed return", "no risk"
            ]
            matches = [p for p in unrealistic_phrases if p in text]
            return len(matches) > 0, {"matched_phrases": matches}
        
        return False, {}

    def _is_official_source(self, url: str) -> bool:
        """Check if URL is from an official project domain."""
        try:
            domain = urlparse(url).netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            
            official_domains = {
                "ethereum.org", "arbitrum.io", "optimism.io", "polygon.technology",
                "base.org", "linea.build", "zksync.io", "scroll.io",
                "coinbase.com", "uniswap.org", "aave.com", "lido.fi",
                "defillama.com", "coingecko.com"
            }
            
            return any(domain == d or domain.endswith("." + d) for d in official_domains)
        except Exception:
            return False

    def _create_finding(self, campaign_id: str, rule: Dict[str, Any], match_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create a risk finding from a triggered rule."""
        import uuid
        return {
            "id": str(uuid.uuid4()),
            "campaign_id": campaign_id,
            "rule_id": rule["rule_id"],
            "rule_version": rule["version"],
            "finding": f"{rule['name']}: {rule['description']}",
            "severity": rule["severity"],
            "description": rule["description"],
            "evidence_url": None,
            "matched_content": json.dumps(match_details),
        }

    def _store_assessment(self, assessment: Dict[str, Any]) -> None:
        """Store risk assessment in database."""
        import uuid
        with get_db() as db:
            db.execute("""
                INSERT OR REPLACE INTO campaign_risk_assessment
                (id, campaign_id, risk_score, risk_level, critical_override, total_findings, high_findings, critical_findings, assessed_at, assessed_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(uuid.uuid4()),
                assessment["campaign_id"],
                assessment["risk_score"],
                assessment["risk_level"],
                int(assessment["critical_override"]),
                assessment["total_findings"],
                assessment["high_findings"],
                assessment["critical_findings"],
                assessment["assessed_at"],
                assessment["assessed_by"]
            ))

    def _store_findings(self, campaign_id: str, findings: List[Dict[str, Any]]) -> None:
        """Store risk findings in database."""
        with get_db() as db:
            # Clear existing findings
            db.execute("DELETE FROM risk_findings WHERE campaign_id = ?", (campaign_id,))
            
            for finding in findings:
                db.execute("""
                    INSERT INTO risk_findings
                    (id, campaign_id, rule_id, rule_version, finding, severity, description, evidence_url, matched_content, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    finding["id"],
                    finding["campaign_id"],
                    finding["rule_id"],
                    finding["rule_version"],
                    finding["finding"],
                    finding["severity"],
                    finding["description"],
                    finding["evidence_url"],
                    finding["matched_content"],
                    datetime.utcnow().isoformat()
                ))


risk_engine = RiskEngine()