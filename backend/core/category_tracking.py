"""
Category-specific tracking service for Global Airdrop Hunter.
Handles NFT, Testnet, and Reward specific campaign data.
"""

import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

from backend.database.connection import get_db
from backend.database.repositories import campaign_repository
from backend.core.models import (
    Campaign, CampaignEvent, UserNotificationPrefs,
    CampaignType, CampaignEvent as CampaignEventModel,
    UserNotificationPrefs as UserNotificationPrefsModel
)


class CategoryTrackingService:
    """Service for managing NFT, Testnet, and Reward specific campaign data."""

    def __init__(self):
        pass

    # ===== NFT Methods =====

    def get_nft_data(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get NFT-specific data for a campaign."""
        campaign = campaign_repository.get_by_id(campaign_id)
        if not campaign or campaign.type.value != 'nft':
            return None

        return {
            "collection_name": campaign.nft_collection_name,
            "collection_slug": campaign.nft_collection_slug,
            "mint_price": campaign.nft_mint_price,
            "mint_currency": campaign.nft_mint_currency,
            "total_supply": campaign.nft_total_supply,
            "minted_supply": campaign.nft_minted_supply,
            "mint_start": campaign.nft_mint_start.isoformat() if campaign.nft_mint_start else None,
            "mint_end": campaign.nft_mint_end.isoformat() if campaign.nft_mint_end else None,
            "whitelist_url": str(campaign.nft_whitelist_url) if campaign.nft_whitelist_url else None,
            "official_collection_url": str(campaign.nft_official_collection_url) if campaign.nft_official_collection_url else None,
            "marketplace_urls": [str(u) for u in campaign.nft_marketplace_urls] if campaign.nft_marketplace_urls else [],
            "royalty_percentage": campaign.nft_royalty_percentage,
            "standard": campaign.nft_standard,
        }

    def update_nft_data(self, campaign_id: str, nft_data: Dict[str, Any]) -> Optional[Campaign]:
        """Update NFT-specific data for a campaign."""
        from backend.core.models import CampaignUpdate
        update = CampaignUpdate(**nft_data)
        return campaign_repository.update(campaign_id, update)

    # ===== Testnet Methods =====

    def get_testnet_data(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get Testnet-specific data for a campaign."""
        campaign = campaign_repository.get_by_id(campaign_id)
        if not campaign or campaign.type.value != 'testnet':
            return None

        return {
            "network_name": campaign.testnet_network_name,
            "chain_id": campaign.testnet_chain_id,
            "rpc_url": str(campaign.testnet_rpc_url) if campaign.testnet_rpc_url else None,
            "explorer_url": str(campaign.testnet_explorer_url) if campaign.testnet_explorer_url else None,
            "faucet_url": str(campaign.testnet_faucet_url) if campaign.testnet_faucet_url else None,
            "docs_url": str(campaign.testnet_docs_url) if campaign.testnet_docs_url else None,
            "github_url": str(campaign.testnet_github_url) if campaign.testnet_github_url else None,
            "tasks": campaign.testnet_tasks or [],
            "duration_days": campaign.testnet_duration_days,
            "reward_type": campaign.testnet_reward_type,
            "reward_amount": campaign.testnet_reward_amount,
        }

    def update_testnet_data(self, campaign_id: str, testnet_data: Dict[str, Any]) -> Optional[Campaign]:
        """Update Testnet-specific data for a campaign."""
        from backend.core.models import CampaignUpdate
        update = CampaignUpdate(**testnet_data)
        return campaign_repository.update(campaign_id, update)

    # ===== Reward Methods =====

    def get_reward_data(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get Reward-specific data for a campaign."""
        campaign = campaign_repository.get_by_id(campaign_id)
        if not campaign or campaign.type.value != 'reward':
            return None

        return {
            "token_symbol": campaign.reward_token_symbol,
            "token_address": campaign.reward_token_address,
            "token_decimals": campaign.reward_token_decimals,
            "amount_per_user": campaign.reward_amount_per_user,
            "total_pool": campaign.reward_total_pool,
            "distribution_method": campaign.reward_distribution_method,
            "claim_start": campaign.reward_claim_start.isoformat() if campaign.reward_claim_start else None,
            "claim_end": campaign.reward_claim_end.isoformat() if campaign.reward_claim_end else None,
            "vesting_schedule": campaign.reward_vesting_schedule,
            "apy": campaign.reward_apy,
            "lockup_period_days": campaign.reward_lockup_period_days,
        }

    def update_reward_data(self, campaign_id: str, reward_data: Dict[str, Any]) -> Optional[Campaign]:
        """Update Reward-specific data for a campaign."""
        from backend.core.models import CampaignUpdate
        update = CampaignUpdate(**reward_data)
        return campaign_repository.update(campaign_id, update)

    # ===== Category-agnostic Methods =====

    def get_category_data(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get category-specific data based on campaign type."""
        campaign = campaign_repository.get_by_id(campaign_id)
        if not campaign:
            return None

        if campaign.type == CampaignType.NFT:
            return self.get_nft_data(campaign_id)
        elif campaign.type == CampaignType.TESTNET:
            return self.get_testnet_data(campaign_id)
        elif campaign.type == CampaignType.REWARD:
            return self.get_reward_data(campaign_id)
        return {}

    def update_category_data(self, campaign_id: str, data: Dict[str, Any]) -> Optional[Campaign]:
        """Update category-specific data based on campaign type."""
        campaign = campaign_repository.get_by_id(campaign_id)
        if not campaign:
            return None

        from backend.core.models import CampaignUpdate
        update = CampaignUpdate(**data)
        return campaign_repository.update(campaign_id, update)

    # ===== Event/Calendar Methods =====

    def create_event(self, event: CampaignEventModel) -> CampaignEventModel:
        """Create a campaign event."""
        with get_db() as db:
            event_id = str(UUID(int=0))  # placeholder
            now = datetime.utcnow().isoformat()
            db.execute("""
                INSERT INTO campaign_events (
                    id, campaign_id, event_type, event_title, event_description,
                    event_date, is_all_day, reminder_days_before, is_notified,
                    created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                str(event.id),
                str(event.campaign_id),
                event.event_type,
                event.event_title,
                event.event_description,
                event.event_date.isoformat() if event.event_date else None,
                int(event.is_all_day),
                event.reminder_days_before,
                int(event.is_notified),
                now, now
            ))
            return self.get_event(str(event.id))

    def get_event(self, event_id: str) -> Optional[CampaignEventModel]:
        """Get a campaign event by ID."""
        with get_db() as db:
            row = db.execute("SELECT * FROM campaign_events WHERE id = ?", (event_id,)).fetchone()
            if not row:
                return None
            return CampaignEventModel(
                id=UUID(row["id"]),
                campaign_id=UUID(row["campaign_id"]),
                event_type=row["event_type"],
                event_title=row["event_title"],
                event_description=row["event_description"],
                event_date=datetime.fromisoformat(row["event_date"]),
                is_all_day=bool(row["is_all_day"]),
                reminder_days_before=row["reminder_days_before"],
                is_notified=bool(row["is_notified"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

    def get_campaign_events(self, campaign_id: str) -> List[CampaignEventModel]:
        """Get all events for a campaign."""
        with get_db() as db:
            rows = db.execute("SELECT * FROM campaign_events WHERE campaign_id = ? ORDER BY event_date", (campaign_id,)).fetchall()
            return [
                CampaignEventModel(
                    id=UUID(row["id"]),
                    campaign_id=UUID(row["campaign_id"]),
                    event_type=row["event_type"],
                    event_title=row["event_title"],
                    event_description=row["event_description"],
                    event_date=datetime.fromisoformat(row["event_date"]),
                    is_all_day=bool(row["is_all_day"]),
                    reminder_days_before=row["reminder_days_before"],
                    is_notified=bool(row["is_notified"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                )
                for row in rows
            ]

    def update_event(self, event_id: str, update_data: Dict[str, Any]) -> Optional[CampaignEventModel]:
        """Update a campaign event."""
        with get_db() as db:
            existing = db.execute("SELECT * FROM campaign_events WHERE id = ?", (event_id,)).fetchone()
            if not existing:
                return None

            updates = []
            params = []

            field_mapping = {
                "event_type": "event_type",
                "event_title": "event_title",
                "event_description": "event_description",
                "event_date": "event_date",
                "is_all_day": "is_all_day",
                "reminder_days_before": "reminder_days_before",
                "is_notified": "is_notified",
            }

            for field, db_field in field_mapping.items():
                if field in update_data and update_data[field] is not None:
                    value = update_data[field]
                    if isinstance(value, datetime):
                        value = value.isoformat()
                    elif isinstance(value, bool):
                        value = int(value)
                    updates.append(f"{db_field} = ?")
                    params.append(value)

            if updates:
                updates.append("updated_at = ?")
                params.append(datetime.utcnow().isoformat())
                params.append(event_id)
                db.execute(f"UPDATE campaign_events SET {', '.join(updates)} WHERE id = ?", params)

            return self.get_event(event_id)

    def delete_event(self, event_id: str) -> bool:
        """Delete a campaign event."""
        with get_db() as db:
            cursor = db.execute("DELETE FROM campaign_events WHERE id = ?", (event_id,))
            return cursor.rowcount > 0

    # ===== Notification Preferences =====

    def get_notification_prefs(self, campaign_id: str) -> Optional[UserNotificationPrefsModel]:
        """Get user notification preferences for a campaign."""
        with get_db() as db:
            row = db.execute("SELECT * FROM user_notification_prefs WHERE campaign_id = ?", (campaign_id,)).fetchone()
            if not row:
                return None
            return UserNotificationPrefsModel(
                id=UUID(row["id"]),
                campaign_id=UUID(row["campaign_id"]),
                notify_deadline=bool(row["notify_deadline"]),
                notify_mint_start=bool(row["notify_mint_start"]),
                notify_mint_end=bool(row["notify_mint_end"]),
                notify_claim_start=bool(row["notify_claim_start"]),
                notify_claim_end=bool(row["notify_claim_end"]),
                notify_distribution=bool(row["notify_distribution"]),
                reminder_days_before=row["reminder_days_before"],
                in_app_enabled=bool(row["in_app_enabled"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
            )

    def upsert_notification_prefs(self, prefs: UserNotificationPrefsModel) -> UserNotificationPrefsModel:
        """Create or update user notification preferences."""
        with get_db() as db:
            existing = db.execute("SELECT * FROM user_notification_prefs WHERE campaign_id = ?", (str(prefs.campaign_id),)).fetchone()
            now = datetime.utcnow().isoformat()

            if existing:
                db.execute("""
                    UPDATE user_notification_prefs SET
                        notify_deadline = ?, notify_mint_start = ?, notify_mint_end = ?,
                        notify_claim_start = ?, notify_claim_end = ?, notify_distribution = ?,
                        reminder_days_before = ?, in_app_enabled = ?, updated_at = ?
                    WHERE campaign_id = ?
                """, (
                    int(prefs.notify_deadline),
                    int(prefs.notify_mint_start),
                    int(prefs.notify_mint_end),
                    int(prefs.notify_claim_start),
                    int(prefs.notify_claim_end),
                    int(prefs.notify_distribution),
                    prefs.reminder_days_before,
                    int(prefs.in_app_enabled),
                    datetime.utcnow().isoformat(),
                    str(prefs.campaign_id)
                ))
            else:
                db.execute("""
                    INSERT INTO user_notification_prefs (
                        id, campaign_id, notify_deadline, notify_mint_start,
                        notify_mint_end, notify_claim_start, notify_claim_end,
                        notify_distribution, reminder_days_before, in_app_enabled,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(prefs.id),
                    str(prefs.campaign_id),
                    int(prefs.notify_deadline),
                    int(prefs.notify_mint_start),
                    int(prefs.notify_mint_end),
                    int(prefs.notify_claim_start),
                    int(prefs.notify_claim_end),
                    int(prefs.notify_distribution),
                    prefs.reminder_days_before,
                    int(prefs.in_app_enabled),
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                ))
            return self.get_notification_prefs(str(prefs.campaign_id))


category_tracking_service = CategoryTrackingService()