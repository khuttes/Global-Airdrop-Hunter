import asyncio
import uuid
import json
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict
from backend.database.connection import get_db
from backend.core.models import (
    Source, ScanRequest, ScanResult, CampaignCreate, CampaignStatus,
    SourceUpdate, SourceStatus, Evidence
)
from backend.core.adapter_registry import adapter_registry


async def fetch_evidence_content(url: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """
    Fetch content from an evidence URL and extract snippet, title, and content hash.
    """
    import aiohttp
    import hashlib
    from bs4 import BeautifulSoup
    
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.get(url, headers={'User-Agent': 'GlobalAirdropHunter/1.0'}) as response:
                if response.status != 200:
                    return None
                
                content_type = response.headers.get('content-type', '')
                if 'text/html' not in content_type and 'application/json' not in content_type:
                    return None
                
                text = await response.text()
                
                # Extract title and snippet
                title = ""
                snippet = ""
                
                if 'text/html' in content_type:
                    soup = BeautifulSoup(text, 'html.parser')
                    # Get title
                    if soup.title:
                        title = soup.title.string.strip()[:200]
                    # Get meta description or first paragraph
                    meta_desc = soup.find('meta', attrs={'name': 'description'})
                    if meta_desc and meta_desc.get('content'):
                        snippet = meta_desc['content'][:300]
                    else:
                        first_p = soup.find('p')
                        if first_p:
                            snippet = first_p.get_text()[:300]
                elif 'application/json' in content_type:
                    import json
                    try:
                        data = json.loads(text)
                        snippet = str(data)[:300]
                    except:
                        snippet = text[:300]
                
                # Compute content hash
                content_hash = hashlib.sha256(text.encode()).hexdigest()[:32]
                
                return {
                    'url': url,
                    'title': title,
                    'snippet': snippet,
                    'content_hash': content_hash,
                    'fetched_at': datetime.utcnow().isoformat(),
                    'source_type': 'auto_fetch',
                    'status_code': response.status
                }
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.debug(f"Failed to fetch evidence from {url}: {e}")
        return None


import logging
logger = logging.getLogger(__name__)


def _get_repositories():
    """Lazy import to avoid circular imports."""
    from backend.database.repositories.source import source_repository
    from backend.database.repositories.campaign import campaign_repository
    return source_repository, campaign_repository


class TokenBucketRateLimiter:
    """Token bucket rate limiter for per-source request limiting."""

    def __init__(self, rate_limit: int, period: float = 60.0):
        self.rate_limit = rate_limit
        self.period = period
        self.tokens = rate_limit
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1):
        """Acquire tokens, blocking until available."""
        async with self._lock:
            while True:
                self._refill()
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return
                # Calculate wait time
                wait_time = (tokens - self.tokens) * self.period / self.rate_limit
                if wait_time > 30:
                    wait_time = 30  # Cap wait time
                await asyncio.sleep(wait_time)

    def _refill(self):
        now = time.monotonic()
        elapsed = now - self.last_refill
        if elapsed >= self.period:
            self.tokens = self.rate_limit
            self.last_refill = now
        else:
            self.tokens = min(self.rate_limit, self.tokens + int(elapsed * self.rate_limit / self.period))


class DiscoveryService:
    """Service for orchestrating discovery scans across all sources."""

    def __init__(self):
        self.max_concurrent_scans = 3
        self.scan_timeout = 300  # 5 minutes
        self._rate_limiters: Dict[str, TokenBucketRateLimiter] = {}
        self.max_consecutive_failures = 5  # Auto-disable after this many failures

    def _get_rate_limiter(self, source_id: str, rate_limit: int) -> TokenBucketRateLimiter:
        """Get or create rate limiter for a source."""
        if source_id not in self._rate_limiters:
            self._rate_limiters[source_id] = TokenBucketRateLimiter(rate_limit)
        return self._rate_limiters[source_id]

    async def run_scan(self, request: ScanRequest) -> ScanResult:
        """Run a discovery scan on specified sources."""
        scan_id = uuid.uuid4()
        sources_to_scan = request.sources if request.sources else None

        # Get repositories lazily
        source_repo, campaign_repo = _get_repositories()

        # Get sources to scan
        if sources_to_scan:
            sources = []
            for source_id in sources_to_scan:
                source = source_repo.get_by_id(source_id)
                if source and source.enabled:
                    sources.append(source)
        else:
            sources = source_repo.get_enabled_sources()

        if not sources:
            return ScanResult(
                scan_id=scan_id,
                sources_scanned=[],
                campaigns_found=0,
                campaigns_new=0,
                campaigns_updated=0,
                errors=["No enabled sources to scan"],
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )

        # Create scan history record
        scan_history_id = self._create_scan_history(scan_id, [s.id for s in sources])

        all_campaigns = []
        all_errors = []
        total_new = 0
        total_updated = 0
        per_source_details = []

        # Run scans with concurrency limit
        semaphore = asyncio.Semaphore(self.max_concurrent_scans)

        async def scan_source(source: Source):
            async with semaphore:
                return await self._scan_source(source)

        tasks = [scan_source(source) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        sources_scanned = []
        all_evidence = []
        for source, result in zip(sources, results):
            sources_scanned.append(source.id)
            if isinstance(result, Exception):
                all_errors.append(f"{source.name}: {str(result)}")
                source_repo.update_health_check(source.id, False)
            elif isinstance(result, tuple) and len(result) == 3:
                campaigns, errors, evidence = result
                all_errors.extend(errors)
                all_evidence.extend(evidence)
                source_repo.update_health_check(source.id, len(errors) == 0)

                for campaign in campaigns:
                    # Use deduplication-aware creation/update
                    created_campaign, is_new, duplicate_info = campaign_repo.get_or_create_deduplicated(
                        campaign, source_id=source.id
                    )
                    
                    if duplicate_info:
                        total_updated += 1
                    elif is_new:
                        total_new += 1
                    
                    all_campaigns.append(created_campaign)

                source_repo.update_scan_stats(source.id, len(campaigns))

                # Collect per-source details for scan history
                source_detail = {
                    "source_id": source.id,
                    "source_name": source.name,
                    "campaigns_found": len(campaigns),
                    "errors": errors,
                    "evidence_count": len(evidence),
                    "status": "success" if len(errors) == 0 else "partial_failure"
                }
                per_source_details.append(source_detail)

        # Update scan history with per-source details
        self._update_scan_history(
            scan_history_id,
            sources_scanned,
            len(all_campaigns),
            total_new,
            total_updated,
            all_errors,
            per_source_details
        )

        return ScanResult(
            scan_id=scan_id,
            sources_scanned=sources_scanned,
            campaigns_found=len(all_campaigns),
            campaigns_new=total_new,
            campaigns_updated=total_updated,
            errors=all_errors,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow()
        )

    async def _scan_source(self, source: Source) -> tuple:
        """Scan a single source with rate limiting and health monitoring."""
        adapter = adapter_registry.create_adapter(source)
        if not adapter:
            return [], [f"No adapter available for source: {source.name}"], []

        source_repo, _ = _get_repositories()

        # Check consecutive failures - auto-disable if too many
        fresh_source = source_repo.get_by_id(source.id)
        if fresh_source and fresh_source.consecutive_failures >= self.max_consecutive_failures:
            source_repo.update(fresh_source.id, SourceUpdate(enabled=False, status=SourceStatus.DISABLED))
            return [], [f"Source {source.name} auto-disabled after {fresh_source.consecutive_failures} consecutive failures"], []

        try:
            # Apply rate limiting
            rate_limiter = self._get_rate_limiter(source.id, source.rate_limit)
            await rate_limiter.acquire()

            # Health check first
            healthy = await adapter.health_check()
            if not healthy:
                source_repo.update_health_check(source.id, False)
                return [], [f"Source {source.name} health check failed"], []

            # Run discovery with timeout
            try:
                result = await asyncio.wait_for(adapter.discover(), timeout=source.timeout)
            except asyncio.TimeoutError:
                source_repo.update_health_check(source.id, False)
                return [], [f"Source {source.name} scan timed out after {source.timeout}s"], []

            # Close adapter if it has a close method
            if hasattr(adapter, 'close'):
                await adapter.close()

            # Capture evidence from raw response
            evidence_list = []
            if result.raw_response:
                from backend.core.models import Evidence
                evidence = Evidence(
                    source_type="api",
                    content_hash=str(hash(str(result.raw_response)))[:32],
                    raw_data=result.raw_response,
                    url=getattr(adapter.metadata, 'base_url', ''),
                )
                evidence_list.append(evidence)

            source_repo.update_health_check(source.id, True)
            return result.campaigns, result.errors, evidence_list

        except Exception as e:
            source_repo.update_health_check(source.id, False)
            return [], [f"Source {source.name} scan failed: {str(e)}"], []

    def _create_scan_history(self, scan_id: uuid.UUID, source_ids: List[str]) -> str:
        """Create a scan history record."""
        history_id = str(uuid.uuid4())
        with get_db() as db:
            db.execute("""
                INSERT INTO scan_history (id, sources_scanned, campaigns_found, campaigns_new, campaigns_updated, errors, started_at)
                VALUES (?, ?, 0, 0, 0, '[]', ?)
            """, (history_id, json.dumps(source_ids), datetime.utcnow().isoformat()))
        return history_id

    def _update_scan_history(self, history_id: str, sources_scanned: List[str],
                            campaigns_found: int, campaigns_new: int, campaigns_updated: int,
                            errors: List[str], per_source: Optional[List[Dict]] = None) -> None:
        """Update scan history record with per-source details."""
        with get_db() as db:
            db.execute("""
                UPDATE scan_history
                SET sources_scanned = ?, campaigns_found = ?, campaigns_new = ?,
                    campaigns_updated = ?, errors = ?, completed_at = ?, per_source_details = ?
                WHERE id = ?
            """, (
                json.dumps(sources_scanned),
                campaigns_found,
                campaigns_new,
                campaigns_updated,
                json.dumps(errors),
                datetime.utcnow().isoformat(),
                json.dumps(per_source or []),
                history_id
            ))

    def get_scan_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent scan history."""
        with get_db() as db:
            rows = db.execute("""
                SELECT * FROM scan_history
                ORDER BY started_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
            return [dict(row) for row in rows]

    def get_scan_history_detail(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed scan history for a specific scan."""
        with get_db() as db:
            row = db.execute("SELECT * FROM scan_history WHERE id = ?", (scan_id,)).fetchone()
            if not row:
                return None
            return dict(row)

    async def enrich_campaign_evidence(self, campaign_id: str) -> int:
        """
        Fetch content for evidence URLs of a campaign and store snippets/content hashes.
        Returns the number of evidence items enriched.
        """
        from backend.database.repositories.campaign import campaign_repository
        
        campaign = campaign_repository.get_by_id(campaign_id)
        if not campaign:
            return 0
        
        enriched = 0
        for evidence in campaign.evidence:
            if not evidence.content_hash and evidence.url:
                # Try to fetch content
                content = await fetch_evidence_content(evidence.url)
                if content:
                    # Update evidence with fetched content
                    with get_db() as db:
                        db.execute("""
                            UPDATE campaign_evidence 
                            SET title = ?, snippet = ?, content_hash = ?, fetched_at = ?, source_type = ?
                            WHERE id = ?
                        """, (
                            content['title'][:200] if content['title'] else None,
                            content['snippet'][:300] if content['snippet'] else None,
                            content['content_hash'],
                            content['fetched_at'],
                            'auto_fetch',
                            str(evidence.id)
                        ))
                    enriched += 1
        
        return enriched


discovery_service = DiscoveryService()