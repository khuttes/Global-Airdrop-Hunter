"""
Domain verification service for Global Airdrop Hunter.
Performs WHOIS, SSL, DNS, and project-controlled source verification.
"""

import asyncio
import json
import re
import ssl
import socket
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse

import aiohttp

from backend.database.connection import get_db
from backend.database.repositories import campaign_repository


class DomainVerificationService:
    """Service for verifying domain ownership and authenticity."""

    def __init__(self):
        self.cache_ttl = timedelta(hours=24)
        self.timeout = 10

    async def verify_domain(self, url: str) -> Dict[str, Any]:
        """
        Verify a domain's authenticity.
        Returns verification result with confidence score.
        """
        if not url:
            return {"is_official": False, "confidence": 0.0, "reason": "No URL provided"}

        domain = self._extract_domain(url)
        if not domain:
            return {"is_official": False, "confidence": 0.0, "reason": "Invalid URL"}

        # Check cache first
        cached = self._get_cached_verification(domain)
        if cached:
            return cached

        # Perform verification checks
        results = {
            "domain": domain,
            "is_official": False,
            "confidence": 0.0,
            "checks": {}
        }

        # Run checks in parallel
        whois_task = self._check_whois(domain)
        ssl_task = self._check_ssl(domain)
        dns_task = self._check_dns(domain)
        project_task = self._check_project_confirmation(domain)

        whois_result, ssl_result, dns_result, project_result = await asyncio.gather(
            whois_task, ssl_task, dns_task, project_task, return_exceptions=True
        )

        results["checks"]["whois"] = whois_result if not isinstance(whois_result, Exception) else {"error": str(whois_result)}
        results["checks"]["ssl"] = ssl_result if not isinstance(ssl_result, Exception) else {"error": str(ssl_result)}
        results["checks"]["dns"] = dns_result if not isinstance(dns_result, Exception) else {"error": str(dns_result)}
        results["checks"]["project_confirmation"] = project_result if not isinstance(project_result, Exception) else {"error": str(project_result)}

        # Calculate overall confidence
        results["confidence"] = self._calculate_confidence(results["checks"])
        results["is_official"] = results["confidence"] >= 0.7
        results["verified_at"] = datetime.utcnow().isoformat()

        # Cache result
        self._cache_verification(domain, results)

        return results

    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return None

    def _get_cached_verification(self, domain: str) -> Optional[Dict[str, Any]]:
        """Get cached verification result."""
        with get_db() as db:
            row = db.execute(
                "SELECT * FROM domain_verification WHERE domain = ? AND verified_at > ?",
                (domain, (datetime.utcnow() - self.cache_ttl).isoformat())
            ).fetchone()
            if row:
                return dict(row)
        return None

    def _cache_verification(self, domain: str, result: Dict[str, Any]) -> None:
        """Cache verification result."""
        with get_db() as db:
            ssl_issuer = result["checks"].get("ssl", {}).get("issuer")
            if isinstance(ssl_issuer, dict):
                ssl_issuer = json.dumps(ssl_issuer)
            
            db.execute("""
                INSERT OR REPLACE INTO domain_verification 
                (domain, is_official, registrar, creation_date, expiry_date, ssl_valid, ssl_issuer, ssl_expiry, dns_records, whois_data, verified_at, verification_source, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                domain,
                int(result["is_official"]),
                result["checks"].get("whois", {}).get("registrar"),
                result["checks"].get("whois", {}).get("creation_date"),
                result["checks"].get("whois", {}).get("expiry_date"),
                int(result["checks"].get("ssl", {}).get("valid", False)),
                ssl_issuer,
                result["checks"].get("ssl", {}).get("expiry"),
                json.dumps(result["checks"].get("dns", {})),
                json.dumps(result["checks"].get("whois", {})),
                result["verified_at"],
                "auto",
                result["confidence"]
            ))

    async def _check_whois(self, domain: str) -> Dict[str, Any]:
        """Check WHOIS information for domain."""
        # This is a simplified check - in production you'd use a WHOIS API
        # For now, we check against known official domains
        official_domains = {
            "ethereum.org", "arbitrum.io", "optimism.io", "polygon.technology",
            "base.org", "linea.build", "zksync.io", "scroll.io",
            "coinbase.com", "uniswap.org", "aave.com", "lido.fi",
            "defillama.com", "coingecko.com", "github.com"
        }

        is_known = domain in official_domains or any(domain.endswith("." + d) for d in official_domains)

        return {
            "is_known_official": is_known,
            "registrar": "known" if is_known else "unknown",
            "creation_date": None,
            "expiry_date": None
        }

    async def _check_ssl(self, domain: str) -> Dict[str, Any]:
        """Check SSL certificate validity."""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    return {
                        "valid": True,
                        "issuer": dict(x[0] for x in cert.get("issuer", [])),
                        "subject": dict(x[0] for x in cert.get("subject", [])),
                        "expiry": cert.get("notAfter"),
                        "san": [x[1] for x in cert.get("subjectAltName", [])]
                    }
        except Exception as e:
            return {"valid": False, "error": str(e)}

    async def _check_dns(self, domain: str) -> Dict[str, Any]:
        """Check DNS records."""
        try:
            # Check A record
            a_records = socket.gethostbyname_ex(domain)[2]
            
            # Check for common subdomains
            subdomains = ["www", "api", "app", "blog", "docs", "claim", "airdrop"]
            found_subdomains = []
            for sub in subdomains:
                try:
                    socket.gethostbyname(f"{sub}.{domain}")
                    found_subdomains.append(sub)
                except Exception:
                    pass

            return {
                "a_records": a_records,
                "subdomains": found_subdomains,
                "has_www": "www" in found_subdomains
            }
        except Exception as e:
            return {"error": str(e)}

    async def _check_project_confirmation(self, domain: str) -> Dict[str, Any]:
        """Check if project confirms this domain via official channels."""
        # This would check GitHub repos, official docs, etc.
        # For now, return a basic check against official registry
        from backend.core.official_registry import OFFICIAL_DOMAINS
        
        is_official = domain in OFFICIAL_DOMAINS or any(domain.endswith("." + d) for d in OFFICIAL_DOMAINS)
        
        return {
            "checked": True,
            "confirmed": is_official,
            "sources": ["official_registry"] if is_official else []
        }

    def _calculate_confidence(self, checks: Dict[str, Any]) -> float:
        """Calculate overall confidence score from individual checks."""
        weights = {
            "whois": 0.3,
            "ssl": 0.25,
            "dns": 0.2,
            "project_confirmation": 0.25
        }

        scores = {}
        
        # WHOIS score
        whois = checks.get("whois", {})
        if isinstance(whois, dict) and whois.get("is_known_official"):
            scores["whois"] = 1.0
        else:
            scores["whois"] = 0.0

        # SSL score
        ssl = checks.get("ssl", {})
        if isinstance(ssl, dict) and ssl.get("valid"):
            scores["ssl"] = 1.0
        else:
            scores["ssl"] = 0.0

        # DNS score
        dns = checks.get("dns", {})
        if isinstance(dns, dict) and dns.get("a_records"):
            scores["dns"] = 0.8 if dns.get("has_www") else 0.5
        else:
            scores["dns"] = 0.0

        # Project confirmation score
        project = checks.get("project_confirmation", {})
        if isinstance(project, dict) and project.get("confirmed"):
            scores["project_confirmation"] = 1.0
        else:
            scores["project_confirmation"] = 0.0

        # Weighted average
        total = sum(scores[k] * weights[k] for k in weights if k in scores)
        return min(1.0, total)


domain_verification_service = DomainVerificationService()