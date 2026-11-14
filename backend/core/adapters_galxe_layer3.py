import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.core.adapters import (
    APISourceAdapter, SourceMetadata, DiscoveryResult, SourceType
)
from backend.core.models import CampaignCreate, Source, CampaignType, CampaignStatus, VerificationStatus, RiskLevel


class GalxeAdapter(APISourceAdapter):
    """Adapter for Galxe API - campaign and credential discovery."""

    @property
    def metadata(self) -> SourceMetadata:
        return SourceMetadata(
            id="galxe",
            name="Galxe",
            type=SourceType.API,
            description="Galxe GraphQL API for credential campaigns, NFTs, and community rewards",
            base_url="https://graphigo.prd.galaxy.eco/query",
            rate_limit=30,
            timeout=30,
            config_schema={
                "type": "object",
                "properties": {
                    "space_ids": {"type": "array", "items": {"type": "string"}, "description": "Specific Galxe Space IDs to monitor"},
                    "include_ended": {"type": "boolean", "default": False},
                    "min_rewards": {"type": "integer", "default": 1},
                    "campaign_types": {"type": "array", "items": {"type": "string"}}
                }
            },
            requires_auth=False,
            supported_networks=["ethereum", "polygon", "arbitrum", "optimism", "bsc", "base", "linea", "zksync", "scroll", "avalanche", "fantom"],
            tags=["credentials", "nft", "community_rewards", "galxe"]
        )

    async def health_check(self) -> bool:
        """Check Galxe GraphQL API health."""
        session = await self._get_session()
        try:
            # Simple introspection query
            query = """
            query {
                __typename
            }
            """
            async with session.post(
                self.metadata.base_url,
                json={"query": query},
                timeout=self.timeout
            ) as response:
                return response.status == 200
        except Exception:
            return False

    async def discover(self) -> DiscoveryResult:
        """Discover campaigns from Galxe."""
        campaigns = []
        evidence = []
        errors = []

        space_ids = self.config.get("space_ids", [])
        include_ended = self.config.get("include_ended", False)
        min_rewards = self.config.get("min_rewards", 1)

        session = await self._get_session()

        try:
            # Query for credential campaigns
            if not space_ids:
                # Get popular/recent spaces first
                space_ids = await self._fetch_popular_spaces(session)

            for space_id in space_ids:
                space_campaigns = await self._fetch_space_campaigns(session, space_id, include_ended)
                for campaign_data in space_campaigns:
                    # Filter by minimum rewards
                    rewards = campaign_data.get("rewards", [])
                    if len(rewards) < min_rewards:
                        continue

                    campaign = self._campaign_data_to_campaign(campaign_data, space_id)
                    if campaign:
                        campaigns.append(campaign)

        except Exception as e:
            errors.append(f"Galxe discovery error: {str(e)}")

        return DiscoveryResult(
            campaigns=campaigns,
            evidence=evidence,
            errors=errors,
            scanned_at=datetime.utcnow()
        )

    async def _fetch_popular_spaces(self, session: aiohttp.ClientSession) -> List[str]:
        """Fetch popular/active Galxe Space IDs."""
        query = """
        query GetPopularSpaces($first: Int) {
            popularSpaces(first: $first) {
                id
            }
        }
        """
        try:
            async with session.post(
                self.metadata.base_url,
                json={"query": query, "variables": {"first": 20}},
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    spaces = data.get("data", {}).get("popularSpaces", [])
                    return [s["id"] for s in spaces]
        except Exception:
            pass
        return []

    async def _fetch_space_campaigns(self, session: aiohttp.ClientSession, space_id: str, include_ended: bool) -> List[Dict]:
        """Fetch campaigns for a specific Galxe Space."""
        query = """
        query GetSpaceCampaigns($spaceId: ID!, $includeEnded: Boolean!) {
            space(id: $spaceId) {
                id
                name
                campaigns(first: 50, includeEnded: $includeEnded) {
                    edges {
                        node {
                            id
                            name
                            description
                            status
                            startAt
                            endAt
                            updatedAt
                            rewards {
                                id
                                name
                                type
                                network
                                contractAddress
                                image
                                amount
                                chainId
                                claimable
                            }
                            credential {
                                id
                                name
                                description
                                network
                                chainId
                            }
                            nft {
                                id
                                name
                                description
                                network
                                chainId
                                contractAddress
                            }
                            space {
                                id
                                name
                            }
                        }
                    }
                }
            }
        }
        """
        try:
            async with session.post(
                self.metadata.base_url,
                json={
                    "query": query,
                    "variables": {"spaceId": space_id, "includeEnded": include_ended}
                },
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    edges = data.get("data", {}).get("space", {}).get("campaigns", {}).get("edges", [])
                    return [edge["node"] for edge in edges]
        except Exception:
            pass
        return []

    def _campaign_data_to_campaign(self, campaign_data: Dict, space_id: str) -> Optional[CampaignCreate]:
        """Convert Galxe campaign data to CampaignCreate."""
        try:
            campaign_id = campaign_data.get("id")
            name = campaign_data.get("name")
            description = campaign_data.get("description", "")
            status = campaign_data.get("status", "ACTIVE")
            end_at = campaign_data.get("endAt")
            rewards = campaign_data.get("rewards", [])
            credential = campaign_data.get("credential")
            nft = campaign_data.get("nft")
            space = campaign_data.get("space", {})

            if not campaign_id or not name:
                return None

            # Determine campaign type and network
            camp_type = CampaignType.AIRDROP
            network = "Ethereum"

            if nft:
                camp_type = CampaignType.NFT
                network = self._chain_id_to_network(nft.get("chainId", 1))
            elif credential:
                camp_type = CampaignType.REWARD
                network = self._chain_id_to_network(credential.get("chainId", 1))
            elif rewards:
                # Use first reward's network
                first_reward = rewards[0]
                network = self._chain_id_to_network(first_reward.get("chainId", 1))

            # Build official URL
            official_url = f"https://galxe.com/{space.get('name', space_id)}/campaign/{campaign_id}"
            campaign_url = official_url

            # Build description
            desc_parts = [description] if description else []
            if rewards:
                reward_names = [r.get("name", "Reward") for r in rewards[:3]]
                desc_parts.append(f"Rewards: {', '.join(reward_names)}")
            if nft:
                desc_parts.append(f"NFT: {nft.get('name', 'NFT')}")
            if credential:
                desc_parts.append(f"Credential: {credential.get('name', 'Credential')}")

            full_description = " | ".join(desc_parts) if desc_parts else f"Galxe campaign: {name}"

            # Determine status
            camp_status = CampaignStatus.ACTIVE
            if status == "ENDED" or (end_at and datetime.fromisoformat(end_at.replace("Z", "+00:00")) < datetime.utcnow()):
                camp_status = CampaignStatus.ENDED

            # Risk level - Galxe is a known platform but campaigns vary
            risk = RiskLevel.MEDIUM
            if space.get("name") in ["ethereum", "arbitrum", "optimism", "polygon", "base"]:
                risk = RiskLevel.LOW

            return CampaignCreate(
                name=f"Galxe: {name}",
                project=space.get("name", "Galxe"),
                type=camp_type,
                network=network,
                description=full_description[:1000],
                official_url=official_url,
                campaign_url=campaign_url,
                status=camp_status,
                verification_status=VerificationStatus.INDEPENDENT,
                risk_level=risk,
                risk_score=40 if risk == RiskLevel.MEDIUM else 25,
                evidence_urls=[official_url],
                source_id=self.source.id
            )
        except Exception:
            return None

    def _chain_id_to_network(self, chain_id: int) -> str:
        """Convert chain ID to network name."""
        chain_map = {
            1: "Ethereum",
            137: "Polygon",
            42161: "Arbitrum",
            10: "Optimism",
            56: "BSC",
            8453: "Base",
            59144: "Linea",
            324: "zkSync",
            534352: "Scroll",
            43114: "Avalanche",
            250: "Fantom",
        }
        return chain_map.get(chain_id, "Ethereum")

    async def parse_record(self, raw_data: Dict[str, Any]) -> Optional[CampaignCreate]:
        return self._campaign_data_to_campaign(raw_data, raw_data.get("space", {}).get("id", ""))


class Layer3Adapter(APISourceAdapter):
    """Adapter for Layer3 API - quest and campaign discovery."""

    @property
    def metadata(self) -> SourceMetadata:
        return SourceMetadata(
            id="layer3",
            name="Layer3",
            type=SourceType.API,
            description="Layer3 GraphQL API for quests, campaigns, and user rewards",
            base_url="https://api.layer3.xyz/graphql",
            rate_limit=30,
            timeout=30,
            config_schema={
                "type": "object",
                "properties": {
                    "campaign_ids": {"type": "array", "items": {"type": "string"}, "description": "Specific campaign IDs to monitor"},
                    "include_completed": {"type": "boolean", "default": False},
                    "min_xp": {"type": "integer", "default": 0},
                    "networks": {"type": "array", "items": {"type": "string"}}
                }
            },
            requires_auth=False,
            supported_networks=["ethereum", "polygon", "arbitrum", "optimism", "bsc", "base", "linea", "zksync", "scroll", "avalanche", "fantom", "solana"],
            tags=["quests", "xp", "campaigns", "layer3"]
        )

    async def health_check(self) -> bool:
        """Check Layer3 GraphQL API health."""
        session = await self._get_session()
        try:
            query = """
            query {
                __typename
            }
            """
            async with session.post(
                self.metadata.base_url,
                json={"query": query},
                timeout=self.timeout
            ) as response:
                return response.status == 200
        except Exception:
            return False

    async def discover(self) -> DiscoveryResult:
        """Discover campaigns from Layer3."""
        campaigns = []
        evidence = []
        errors = []

        campaign_ids = self.config.get("campaign_ids", [])
        include_completed = self.config.get("include_completed", False)
        min_xp = self.config.get("min_xp", 0)
        networks = self.config.get("networks", [])

        session = await self._get_session()

        try:
            if campaign_ids:
                for campaign_id in campaign_ids:
                    campaign_data = await self._fetch_campaign(session, campaign_id)
                    if campaign_data:
                        campaign = self._campaign_data_to_campaign(campaign_data)
                        if campaign:
                            campaigns.append(campaign)
            else:
                # Fetch recent/active campaigns
                campaign_list = await self._fetch_campaign_list(session, include_completed)
                for campaign_data in campaign_list:
                    if networks:
                        campaign_network = self._chain_id_to_network(campaign_data.get("chainId", 1))
                        if campaign_network not in networks:
                            continue
                    
                    xp = campaign_data.get("xpReward", 0)
                    if xp < min_xp:
                        continue
                    
                    campaign = self._campaign_data_to_campaign(campaign_data)
                    if campaign:
                        campaigns.append(campaign)

        except Exception as e:
            errors.append(f"Layer3 discovery error: {str(e)}")

        return DiscoveryResult(
            campaigns=campaigns,
            evidence=evidence,
            errors=errors,
            scanned_at=datetime.utcnow()
        )

    async def _fetch_campaign_list(self, session: aiohttp.ClientSession, include_completed: bool) -> List[Dict]:
        """Fetch list of campaigns from Layer3."""
        query = """
        query GetCampaigns($first: Int, $includeCompleted: Boolean!) {
            campaigns(first: $first, includeCompleted: $includeCompleted) {
                edges {
                    node {
                        id
                        name
                        description
                        status
                        xpReward
                        chainId
                        startAt
                        endAt
                        updatedAt
                        quests {
                            id
                            name
                            type
                            xpReward
                        }
                        rewards {
                            id
                            name
                            type
                            network
                            contractAddress
                            amount
                        }
                    }
                }
            }
        }
        """
        try:
            async with session.post(
                self.metadata.base_url,
                json={
                    "query": query,
                    "variables": {"first": 50, "includeCompleted": include_completed}
                },
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    edges = data.get("data", {}).get("campaigns", {}).get("edges", [])
                    return [edge["node"] for edge in edges]
        except Exception:
            pass
        return []

    async def _fetch_campaign(self, session: aiohttp.ClientSession, campaign_id: str) -> Optional[Dict]:
        """Fetch a specific campaign by ID."""
        query = """
        query GetCampaign($id: ID!) {
            campaign(id: $id) {
                id
                name
                description
                status
                xpReward
                chainId
                startAt
                endAt
                updatedAt
                quests {
                    id
                    name
                    type
                    xpReward
                }
                rewards {
                    id
                    name
                    type
                    network
                    contractAddress
                    amount
                }
            }
        }
        """
        try:
            async with session.post(
                self.metadata.base_url,
                json={"query": query, "variables": {"id": campaign_id}},
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("data", {}).get("campaign")
        except Exception:
            pass
        return None

    def _campaign_data_to_campaign(self, campaign_data: Dict) -> Optional[CampaignCreate]:
        """Convert Layer3 campaign data to CampaignCreate."""
        try:
            campaign_id = campaign_data.get("id")
            name = campaign_data.get("name")
            description = campaign_data.get("description", "")
            status = campaign_data.get("status", "ACTIVE")
            xp_reward = campaign_data.get("xpReward", 0)
            chain_id = campaign_data.get("chainId", 1)
            end_at = campaign_data.get("endAt")
            quests = campaign_data.get("quests", [])
            rewards = campaign_data.get("rewards", [])

            if not campaign_id or not name:
                return None

            # Determine campaign type and network
            camp_type = CampaignType.AIRDROP
            network = self._chain_id_to_network(chain_id)

            # Build official URL
            official_url = f"https://layer3.xyz/campaigns/{campaign_id}"
            campaign_url = official_url

            # Build description
            desc_parts = [description] if description else []
            if xp_reward:
                desc_parts.append(f"XP Reward: {xp_reward}")
            if quests:
                desc_parts.append(f"Quests: {len(quests)}")
            if rewards:
                reward_names = [r.get("name", "Reward") for r in rewards[:3]]
                desc_parts.append(f"Rewards: {', '.join(reward_names)}")

            full_description = " | ".join(desc_parts) if desc_parts else f"Layer3 campaign: {name}"

            # Determine status
            camp_status = CampaignStatus.ACTIVE
            if status == "COMPLETED" or (end_at and datetime.fromisoformat(end_at.replace("Z", "+00:00")) < datetime.utcnow()):
                camp_status = CampaignStatus.ENDED

            # Risk level
            risk = RiskLevel.MEDIUM
            if xp_reward > 1000:
                risk = RiskLevel.LOW

            return CampaignCreate(
                name=f"Layer3: {name}",
                project="Layer3",
                type=camp_type,
                network=network,
                description=full_description[:1000],
                official_url=official_url,
                campaign_url=campaign_url,
                status=camp_status,
                verification_status=VerificationStatus.INDEPENDENT,
                risk_level=risk,
                risk_score=40 if risk == RiskLevel.MEDIUM else 25,
                evidence_urls=[official_url],
                source_id=self.source.id
            )
        except Exception:
            return None

    def _chain_id_to_network(self, chain_id: int) -> str:
        """Convert chain ID to network name."""
        chain_map = {
            1: "Ethereum",
            137: "Polygon",
            42161: "Arbitrum",
            10: "Optimism",
            56: "BSC",
            8453: "Base",
            59144: "Linea",
            324: "zkSync",
            534352: "Scroll",
            43114: "Avalanche",
            250: "Fantom",
            101: "Solana",  # Not EVM but Layer3 supports it
        }
        return chain_map.get(chain_id, "Ethereum")

    async def parse_record(self, raw_data: Dict[str, Any]) -> Optional[CampaignCreate]:
        return self._campaign_data_to_campaign(raw_data)