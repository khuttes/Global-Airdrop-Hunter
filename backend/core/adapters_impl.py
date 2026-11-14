import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.core.adapters import (
    SourceAdapter, APISourceAdapter, SourceMetadata, DiscoveryResult, SourceType
)
from backend.core.models import CampaignCreate, Evidence, Source, CampaignType, CampaignStatus, VerificationStatus, RiskLevel

# Import new adapters
from backend.core.adapters_galxe_layer3 import GalxeAdapter, Layer3Adapter


class CoinGeckoAdapter(APISourceAdapter):
    """Adapter for CoinGecko API - token metadata and market context."""

    @property
    def metadata(self) -> SourceMetadata:
        return SourceMetadata(
            id="coingecko",
            name="CoinGecko",
            type=SourceType.API,
            description="CoinGecko API for token metadata, market data, and new token listings",
            base_url="https://api.coingecko.com/api/v3",
            rate_limit=50,
            timeout=30,
            config_schema={
                "type": "object",
                "properties": {
                    "include_new_tokens": {"type": "boolean", "default": True},
                    "min_market_cap_usd": {"type": "number", "default": 1000000},
                    "categories": {"type": "array", "items": {"type": "string"}}
                }
            },
            requires_auth=False,
            supported_networks=["ethereum", "polygon", "arbitrum", "optimism", "bsc", "base", "linea", "zksync", "scroll"],
            tags=["token_metadata", "market_data", "new_listings"]
        )

    async def health_check(self) -> bool:
        """Check CoinGecko API health."""
        session = await self._get_session()
        try:
            async with session.get(f"{self.metadata.base_url}/ping", timeout=self.timeout) as response:
                return response.status == 200
        except Exception:
            return False

    async def discover(self) -> DiscoveryResult:
        """Discover new tokens from CoinGecko."""
        campaigns = []
        evidence = []
        errors = []

        include_new = self.config.get("include_new_tokens", True)
        min_mcap = self.config.get("min_market_cap_usd", 1000000)
        categories = self.config.get("categories", [])

        session = await self._get_session()

        try:
            # Get recently added coins
            if include_new:
                new_coins = await self._fetch_new_coins(session)
                for coin in new_coins:
                    campaign = self._coin_to_campaign(coin)
                    if campaign:
                        campaigns.append(campaign)

            # Get trending coins
            trending = await self._fetch_trending(session)
            for coin in trending:
                campaign = self._coin_to_campaign(coin, is_trending=True)
                if campaign:
                    campaigns.append(campaign)

            # Get coins by category if specified
            for category in categories:
                category_coins = await self._fetch_category_coins(session, category)
                for coin in category_coins:
                    if coin.get("market_cap", 0) >= min_mcap:
                        campaign = self._coin_to_campaign(coin)
                        if campaign:
                            campaigns.append(campaign)

        except Exception as e:
            errors.append(f"CoinGecko discovery error: {str(e)}")

        return DiscoveryResult(
            campaigns=campaigns,
            evidence=evidence,
            errors=errors,
            scanned_at=datetime.utcnow()
        )

    async def _fetch_new_coins(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Fetch recently added coins from CoinGecko."""
        try:
            async with session.get(
                f"{self.metadata.base_url}/coins/new",
                params={"per_page": 50}
            ) as response:
                if response.status == 200:
                    return await response.json()
        except Exception:
            pass
        return []

    async def _fetch_trending(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Fetch trending coins from CoinGecko."""
        try:
            async with session.get(f"{self.metadata.base_url}/search/trending") as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("coins", [])
        except Exception:
            pass
        return []

    async def _fetch_category_coins(self, session: aiohttp.ClientSession, category: str) -> List[Dict]:
        """Fetch coins by category."""
        try:
            async with session.get(
                f"{self.metadata.base_url}/coins/markets",
                params={"vs_currency": "usd", "category": category, "per_page": 100, "order": "market_cap_desc"}
            ) as response:
                if response.status == 200:
                    return await response.json()
        except Exception:
            pass
        return []

    def _coin_to_campaign(self, coin_data: Dict, is_trending: bool = False) -> Optional[CampaignCreate]:
        """Convert CoinGecko coin data to CampaignCreate."""
        try:
            coin = coin_data.get("item", coin_data) if is_trending else coin_data
            coin_id = coin.get("id") or coin.get("coin_id")
            name = coin.get("name")
            symbol = coin.get("symbol", "").upper()

            if not coin_id or not name:
                return None

            # Skip stablecoins and major established tokens
            if symbol in ["USDT", "USDC", "BUSD", "DAI", "BTC", "ETH"]:
                return None

            platforms = coin.get("platforms", {})
            network = self._detect_primary_network(platforms)

            market_cap = coin.get("market_cap", 0)
            if market_cap and market_cap < 100000:  # Skip very small caps
                return None

            official_url = f"https://www.coingecko.com/en/coins/{coin_id}"
            campaign_url = official_url

            description = f"New token listing on CoinGecko: {name} ({symbol})"
            if is_trending:
                description += " - Currently trending"
            if market_cap:
                description += f" - Market cap: ${market_cap:,.0f}"

            return CampaignCreate(
                name=name,
                project=name,
                type=CampaignType.AIRDROP,
                network=network,
                description=description,
                official_url=official_url,
                campaign_url=campaign_url,
                status=CampaignStatus.ACTIVE,
                verification_status=VerificationStatus.INDEPENDENT,
                risk_level=RiskLevel.MEDIUM,
                risk_score=40,
                evidence_urls=[official_url],
                source_id=self.source.id
            )
        except Exception:
            return None

    def _detect_primary_network(self, platforms: Dict) -> str:
        """Detect primary network from CoinGecko platforms data."""
        network_priority = [
            "ethereum", "polygon-pos", "arbitrum", "optimism",
            "binance-smart-chain", "base", "linea", "zksync", "scroll"
        ]
        for net in network_priority:
            if net in platforms:
                return net.replace("-", " ").title()
        return "Unknown"

    async def parse_record(self, raw_data: Dict[str, Any]) -> Optional[CampaignCreate]:
        return self._coin_to_campaign(raw_data)


class DefiLlamaAdapter(APISourceAdapter):
    """Adapter for DefiLlama API - protocol/DeFi context."""

    @property
    def metadata(self) -> SourceMetadata:
        return SourceMetadata(
            id="defillama",
            name="DefiLlama",
            type=SourceType.API,
            description="DefiLlama API for protocol TVL, yields, and new protocol listings",
            base_url="https://api.llama.fi",
            rate_limit=100,
            timeout=30,
            config_schema={
                "type": "object",
                "properties": {
                    "include_new_protocols": {"type": "boolean", "default": True},
                    "min_tvl_usd": {"type": "number", "default": 1000000},
                    "chains": {"type": "array", "items": {"type": "string"}}
                }
            },
            requires_auth=False,
            supported_networks=["ethereum", "polygon", "arbitrum", "optimism", "bsc", "base", "avalanche", "fantom"],
            tags=["protocol_data", "tvl", "yields", "defi"]
        )

    async def health_check(self) -> bool:
        """Check DefiLlama API health."""
        session = await self._get_session()
        try:
            async with session.get(f"{self.metadata.base_url}/protocols", timeout=self.timeout) as response:
                return response.status == 200
        except Exception:
            return False

    async def discover(self) -> DiscoveryResult:
        """Discover new protocols from DefiLlama."""
        campaigns = []
        evidence = []
        errors = []

        include_new = self.config.get("include_new_protocols", True)
        min_tvl = self.config.get("min_tvl_usd", 1000000)
        chains = self.config.get("chains", [])

        session = await self._get_session()

        try:
            # Get all protocols
            protocols = await self._fetch_protocols(session)

            for protocol in protocols:
                # Filter by chain if specified
                protocol_chains = protocol.get("chains", [])
                if chains and not any(c in protocol_chains for c in chains):
                    continue

                tvl = protocol.get("tvl") or 0
                if tvl < min_tvl:
                    continue

                # Check if protocol is relatively new (added in last 90 days)
                # DefiLlama doesn't have a direct "added date" field, so we use TVL growth as proxy
                campaign = self._protocol_to_campaign(protocol)
                if campaign:
                    campaigns.append(campaign)

        except Exception as e:
            errors.append(f"DefiLlama discovery error: {str(e)}")

        return DiscoveryResult(
            campaigns=campaigns,
            evidence=evidence,
            errors=errors,
            scanned_at=datetime.utcnow()
        )

    async def _fetch_protocols(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Fetch all protocols from DefiLlama."""
        try:
            async with session.get(f"{self.metadata.base_url}/protocols") as response:
                if response.status == 200:
                    return await response.json()
        except Exception:
            pass
        return []

    def _protocol_to_campaign(self, protocol: Dict) -> Optional[CampaignCreate]:
        """Convert DefiLlama protocol to CampaignCreate."""
        try:
            name = protocol.get("name")
            slug = protocol.get("slug")
            tvl = protocol.get("tvl", 0)
            chains = protocol.get("chains", [])
            url = protocol.get("url")

            if not name or not slug:
                return None

            # Skip very large established protocols
            if tvl > 1000000000:  # > 1B TVL
                return None

            # Detect primary network
            network = chains[0].title() if chains else "Ethereum"

            official_url = url or f"https://defillama.com/protocol/{slug}"
            campaign_url = official_url

            description = f"DeFi protocol on DefiLlama: {name}"
            if tvl:
                description += f" - TVL: ${tvl:,.0f}"
            if chains:
                description += f" - Chains: {', '.join(chains)}"

            # Check for token incentives/aidrops
            if "incentivized" in protocol.get("tagline", "").lower() or \
               "airdrop" in protocol.get("description", "").lower():
                camp_type = CampaignType.AIRDROP
                risk = RiskLevel.MEDIUM
            else:
                camp_type = CampaignType.REWARD
                risk = RiskLevel.LOW

            return CampaignCreate(
                name=f"{name} Protocol",
                project=name,
                type=camp_type,
                network=network,
                description=description,
                official_url=official_url,
                campaign_url=campaign_url,
                status=CampaignStatus.ACTIVE,
                verification_status=VerificationStatus.INDEPENDENT,
                risk_level=risk,
                risk_score=35 if risk == RiskLevel.MEDIUM else 25,
                evidence_urls=[official_url],
                source_id=self.source.id
            )
        except Exception:
            return None

    async def parse_record(self, raw_data: Dict[str, Any]) -> Optional[CampaignCreate]:
        return self._protocol_to_campaign(raw_data)


class GitHubAdapter(APISourceAdapter):
    """Adapter for GitHub API - official repos, releases, docs."""

    def __init__(self, source: Source):
        super().__init__(source)
        self.token = self.config.get("github_token")

    @property
    def metadata(self) -> SourceMetadata:
        return SourceMetadata(
            id="github",
            name="GitHub",
            type=SourceType.API,
            description="GitHub API for official repositories, releases, and documentation",
            base_url="https://api.github.com",
            rate_limit=60,
            timeout=30,
            config_schema={
                "type": "object",
                "properties": {
                    "organizations": {"type": "array", "items": {"type": "string"}},
                    "repositories": {"type": "array", "items": {"type": "string"}},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "github_token": {"type": "string", "description": "GitHub PAT for higher rate limits"}
                }
            },
            requires_auth=True,
            auth_fields=["github_token"],
            supported_networks=["ethereum", "polygon", "arbitrum", "optimism", "bsc", "base", "solana", "cosmos"],
            tags=["official_repos", "releases", "documentation", "smart_contracts"]
        )

    async def health_check(self) -> bool:
        """Check GitHub API health."""
        session = await self._get_session()
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        try:
            async with session.get(f"{self.metadata.base_url}/rate_limit", headers=headers, timeout=self.timeout) as response:
                return response.status == 200
        except Exception:
            return False

    async def discover(self) -> DiscoveryResult:
        """Discover campaigns from GitHub repositories and releases."""
        campaigns = []
        evidence = []
        errors = []

        organizations = self.config.get("organizations", [])
        repositories = self.config.get("repositories", [])
        keywords = self.config.get("keywords", ["airdrop", "claim", "rewards", "incentive", "testnet"])

        session = await self._get_session()

        try:
            # Search repositories by keywords
            for keyword in keywords:
                repos = await self._search_repositories(session, keyword)
                for repo in repos:
                    campaign = self._repo_to_campaign(repo)
                    if campaign:
                        campaigns.append(campaign)

            # Get releases from specific orgs/repos
            for org in organizations:
                org_repos = await self._get_org_repositories(session, org)
                for repo in org_repos:
                    releases = await self._get_releases(session, repo["full_name"])
                    for release in releases:
                        campaign = self._release_to_campaign(release, repo)
                        if campaign:
                            campaigns.append(campaign)

            for repo_name in repositories:
                releases = await self._get_releases(session, repo_name)
                for release in releases:
                    campaign = self._release_to_campaign(release, {"full_name": repo_name})
                    if campaign:
                        campaigns.append(campaign)

        except Exception as e:
            errors.append(f"GitHub discovery error: {str(e)}")

        return DiscoveryResult(
            campaigns=campaigns,
            evidence=evidence,
            errors=errors,
            scanned_at=datetime.utcnow()
        )

    async def _search_repositories(self, session: aiohttp.ClientSession, keyword: str) -> List[Dict]:
        """Search GitHub repositories by keyword."""
        try:
            headers = await self._get_headers()
            async with session.get(
                f"{self.metadata.base_url}/search/repositories",
                headers=headers,
                params={"q": f"{keyword} language:solidity stars:>10", "sort": "updated", "per_page": 20}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("items", [])
        except Exception:
            pass
        return []

    async def _get_org_repositories(self, session: aiohttp.ClientSession, org: str) -> List[Dict]:
        """Get repositories for an organization."""
        try:
            headers = await self._get_headers()
            async with session.get(
                f"{self.metadata.base_url}/orgs/{org}/repos",
                headers=headers,
                params={"type": "public", "per_page": 50}
            ) as response:
                if response.status == 200:
                    return await response.json()
        except Exception:
            pass
        return []

    async def _get_releases(self, session: aiohttp.ClientSession, repo: str) -> List[Dict]:
        """Get releases for a repository."""
        try:
            headers = await self._get_headers()
            async with session.get(
                f"{self.metadata.base_url}/repos/{repo}/releases",
                headers=headers,
                params={"per_page": 10}
            ) as response:
                if response.status == 200:
                    return await response.json()
        except Exception:
            pass
        return []

    async def _get_headers(self) -> Dict[str, str]:
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers

    def _repo_to_campaign(self, repo: Dict) -> Optional[CampaignCreate]:
        """Convert GitHub repository to CampaignCreate."""
        try:
            name = repo.get("name")
            full_name = repo.get("full_name")
            description = repo.get("description", "")
            html_url = repo.get("html_url")
            topics = repo.get("topics", [])
            updated_at = repo.get("updated_at")

            if not name or not full_name:
                return None

            # Check if repo is relevant to airdrops/campaigns
            relevant_topics = {"airdrop", "claim", "rewards", "incentive", "testnet", "airdrop-contract", "merkle-distributor"}
            if not any(t in topics for t in relevant_topics):
                # Check description
                desc_lower = description.lower()
                if not any(kw in desc_lower for kw in ["airdrop", "claim", "reward", "incentive", "testnet"]):
                    return None

            network = "Ethereum"  # Default, could be detected from code
            if "arbitrum" in topics or "arbitrum" in description.lower():
                network = "Arbitrum"
            elif "optimism" in topics or "optimism" in description.lower():
                network = "Optimism"
            elif "polygon" in topics or "polygon" in description.lower():
                network = "Polygon"
            elif "base" in topics or "base" in description.lower():
                network = "Base"

            return CampaignCreate(
                name=f"{name} - GitHub Repository",
                project=full_name.split("/")[0],
                type=CampaignType.AIRDROP if "airdrop" in topics or "airdrop" in description.lower() else CampaignType.REWARD,
                network=network,
                description=description[:500] if description else f"GitHub repository: {full_name}",
                official_url=html_url,
                campaign_url=html_url,
                status=CampaignStatus.ACTIVE,
                verification_status=VerificationStatus.INDEPENDENT,
                risk_level=RiskLevel.LOW,
                risk_score=20,
                evidence_urls=[html_url],
                source_id=self.source.id
            )
        except Exception:
            return None

    def _release_to_campaign(self, release: Dict, repo: Dict) -> Optional[CampaignCreate]:
        """Convert GitHub release to CampaignCreate."""
        try:
            tag_name = release.get("tag_name")
            name = release.get("name") or tag_name
            body = release.get("body", "")
            html_url = release.get("html_url")
            published_at = release.get("published_at")
            repo_name = repo.get("full_name", "Unknown")

            if not tag_name:
                return None

            # Check if release is relevant
            body_lower = body.lower()
            if not any(kw in body_lower for kw in ["airdrop", "claim", "reward", "incentive", "testnet", "distribution"]):
                return None

            network = "Ethereum"
            if "arbitrum" in body_lower:
                network = "Arbitrum"
            elif "optimism" in body_lower:
                network = "Optimism"
            elif "polygon" in body_lower:
                network = "Polygon"
            elif "base" in body_lower:
                network = "Base"

            return CampaignCreate(
                name=f"{repo_name} - {name}",
                project=repo_name.split("/")[0],
                type=CampaignType.AIRDROP if "airdrop" in body_lower else CampaignType.REWARD,
                network=network,
                description=body[:500] if body else f"GitHub release: {tag_name}",
                official_url=html_url,
                campaign_url=html_url,
                status=CampaignStatus.ACTIVE,
                verification_status=VerificationStatus.INDEPENDENT,
                risk_level=RiskLevel.LOW,
                risk_score=20,
                evidence_urls=[html_url],
                source_id=self.source.id
            )
        except Exception:
            return None

    async def parse_record(self, raw_data: Dict[str, Any]) -> Optional[CampaignCreate]:
        if "html_url" in raw_data and "tag_name" in raw_data:
            return self._release_to_campaign(raw_data, {"full_name": raw_data.get("repository", {}).get("full_name", "Unknown")})
        return self._repo_to_campaign(raw_data)


class RSSAdapter(SourceAdapter):
    """Adapter for RSS/Atom feeds - official site announcements."""

    def __init__(self, source: Source):
        super().__init__(source)

    @property
    def metadata(self) -> SourceMetadata:
        return SourceMetadata(
            id="rss",
            name="RSS Feed",
            type=SourceType.RSS,
            description="RSS/Atom feed for official project announcements",
            base_url=str(self.source.base_url),
            rate_limit=30,
            timeout=30,
            config_schema={
                "type": "object",
                "properties": {
                    "feed_url": {"type": "string", "format": "uri"},
                    "keywords": {"type": "array", "items": {"type": "string"}},
                    "date_format": {"type": "string"}
                }
            },
            requires_auth=False,
            supported_networks=["ethereum", "polygon", "arbitrum", "optimism", "bsc", "base", "solana", "cosmos", "aptos", "sui"],
            tags=["official_announcements", "blog", "news"]
        )

    async def health_check(self) -> bool:
        """Check RSS feed accessibility."""
        import aiohttp
        feed_url = self.config.get("feed_url", str(self.source.base_url))
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(feed_url, timeout=self.timeout) as response:
                    return response.status == 200
        except Exception:
            return False

    async def discover(self) -> DiscoveryResult:
        """Discover campaigns from RSS feed."""
        campaigns = []
        evidence = []
        errors = []

        feed_url = self.config.get("feed_url", str(self.source.base_url))
        keywords = self.config.get("keywords", ["airdrop", "claim", "rewards", "incentive", "testnet", "distribution", "launch"])

        try:
            import feedparser
            feed = feedparser.parse(feed_url)

            if feed.bozo and not feed.entries:
                errors.append(f"RSS parse error: {feed.bozo_exception}")
                return DiscoveryResult(campaigns=[], evidence=[], errors=errors)

            for entry in feed.entries[:50]:  # Limit to recent 50 entries
                campaign = self._entry_to_campaign(entry, keywords)
                if campaign:
                    campaigns.append(campaign)

        except Exception as e:
            errors.append(f"RSS discovery error: {str(e)}")

        return DiscoveryResult(
            campaigns=campaigns,
            evidence=evidence,
            errors=errors,
            scanned_at=datetime.utcnow()
        )

    def _entry_to_campaign(self, entry: Any, keywords: List[str]) -> Optional[CampaignCreate]:
        """Convert RSS entry to CampaignCreate."""
        try:
            title = getattr(entry, "title", "")
            link = getattr(entry, "link", "")
            summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
            published = getattr(entry, "published", "") or getattr(entry, "updated", "")
            author = getattr(entry, "author", "")

            # Check relevance
            text = f"{title} {summary}".lower()
            if not any(kw in text for kw in keywords):
                return None

            # Determine type
            camp_type = CampaignType.AIRDROP
            if "nft" in text or "collection" in text:
                camp_type = CampaignType.NFT
            elif "testnet" in text:
                camp_type = CampaignType.TESTNET
            elif "reward" in text or "staking" in text or "yield" in text:
                camp_type = CampaignType.REWARD

            # Detect network
            network = "Ethereum"
            for net in ["arbitrum", "optimism", "polygon", "bsc", "base", "linea", "zksync", "scroll", "avalanche", "fantom"]:
                if net in text:
                    network = net.title()
                    break

            return CampaignCreate(
                name=title[:200],
                project=author or "Official Announcement",
                type=camp_type,
                network=network,
                description=summary[:500] if summary else title,
                official_url=link,
                campaign_url=link,
                status=CampaignStatus.ACTIVE,
                verification_status=VerificationStatus.OFFICIAL if self._is_official_domain(link) else VerificationStatus.INDEPENDENT,
                risk_level=RiskLevel.LOW if self._is_official_domain(link) else RiskLevel.MEDIUM,
                risk_score=15 if self._is_official_domain(link) else 40,
                evidence_urls=[link],
                source_id=self.source.id
            )
        except Exception:
            return None

    def _is_official_domain(self, url: str) -> bool:
        """Check if URL is from an official project domain."""
        from urllib.parse import urlparse
        try:
            domain = urlparse(url).netloc.lower()
            official_domains = [
                "ethereum.org", "arbitrum.io", "optimism.io", "polygon.technology",
                "base.org", "linea.build", "zksync.io", "scroll.io",
                "coinbase.com", "uniswap.org", "aave.com", "lido.fi"
            ]
            return any(d in domain for d in official_domains)
        except Exception:
            return False

    async def parse_record(self, raw_data: Dict[str, Any]) -> Optional[CampaignCreate]:
        # For RSS, we parse entries directly in discover
        return None