from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from backend.core.models import SourceType, CampaignCreate, Evidence, Source


@dataclass
class SourceMetadata:
    """Metadata about a source for display and configuration."""
    id: str
    name: str
    type: SourceType
    description: str
    base_url: str
    rate_limit: int
    timeout: int
    config_schema: Dict[str, Any]
    requires_auth: bool = False
    auth_fields: List[str] = None
    supported_networks: List[str] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.auth_fields is None:
            self.auth_fields = []
        if self.supported_networks is None:
            self.supported_networks = []
        if self.tags is None:
            self.tags = []


@dataclass
class DiscoveryResult:
    """Result of a discovery scan from a source."""
    campaigns: List[CampaignCreate]
    evidence: List[Evidence]
    errors: List[str]
    raw_response: Optional[Dict[str, Any]] = None
    scanned_at: datetime = None

    def __post_init__(self):
        if self.scanned_at is None:
            self.scanned_at = datetime.utcnow()


class SourceAdapter(ABC):
    """Abstract base class for all source adapters."""

    def __init__(self, source: Source):
        self.source = source
        self.config = source.config or {}
        self.rate_limit = source.rate_limit
        self.timeout = source.timeout

    @property
    @abstractmethod
    def metadata(self) -> SourceMetadata:
        """Return metadata about this adapter type."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the source is reachable and responding.
        Returns True if healthy, False otherwise.
        """
        pass

    @abstractmethod
    async def discover(self) -> DiscoveryResult:
        """
        Perform a discovery scan and return discovered campaigns.
        Should respect rate limits and timeouts.
        """
        pass

    @abstractmethod
    async def parse_record(self, raw_data: Dict[str, Any]) -> Optional[CampaignCreate]:
        """
        Parse a single raw record from the source into a CampaignCreate.
        Returns None if the record should be skipped.
        """
        pass

    def get_source_type(self) -> SourceType:
        return self.source.type

    def get_source_id(self) -> str:
        return self.source.id

    def normalize_url(self, url: str) -> str:
        """Normalize URL for deduplication."""
        if not url:
            return url
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        parsed = urlparse(url)
        # Remove tracking parameters
        tracking_params = {'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
                          'ref', 'source', 'campaign', 'medium', 'affiliate', 'aff_id'}
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        filtered = {k: v for k, v in query_params.items() if k.lower() not in tracking_params}
        new_query = urlencode(filtered, doseq=True)
        return urlunparse(parsed._replace(query=new_query))

    def generate_stable_id(self, project: str, name: str, network: str, deadline: Optional[str] = None) -> str:
        """Generate a stable ID for deduplication."""
        import hashlib
        parts = [project or "", name, network or "", deadline or ""]
        content = "|".join(parts)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class APISourceAdapter(SourceAdapter):
    """Base class for REST API based sources."""

    def __init__(self, source: Source):
        super().__init__(source)
        self.session = None

    async def _get_session(self):
        """Get or create aiohttp session."""
        if self.session is None or self.session.closed:
            import aiohttp
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def close(self):
        """Close the aiohttp session."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _make_request(self, method: str, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make an HTTP request with error handling."""
        import aiohttp
        session = await self._get_session()
        try:
            async with session.request(method, url, **kwargs) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    return None
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            return None


class RSSSourceAdapter(SourceAdapter):
    """Base class for RSS/Atom feed sources."""

    async def health_check(self) -> bool:
        """Check if RSS feed is accessible."""
        import aiohttp
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(str(self.source.base_url), timeout=self.timeout) as response:
                    return response.status == 200
        except Exception:
            return False


class GitHubSourceAdapter(SourceAdapter):
    """Base class for GitHub API sources."""

    def __init__(self, source: Source):
        super().__init__(source)
        self.token = self.config.get("github_token")

    async def _get_headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    async def _make_request(self, method: str, url: str, **kwargs) -> Optional[Dict[str, Any]]:
        """Make a GitHub API request."""
        import aiohttp
        headers = await self._get_headers()
        kwargs.setdefault("headers", {}).update(headers)
        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, timeout=self.timeout, **kwargs) as response:
                    if response.status == 200:
                        return await response.json()
                    elif response.status == 403:
                        # Rate limited
                        return None
                    else:
                        return None
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return None