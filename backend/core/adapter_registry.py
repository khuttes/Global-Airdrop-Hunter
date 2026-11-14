from typing import Dict, List, Optional, Type
from backend.core.models import Source, SourceType
from backend.core.adapters import SourceAdapter, SourceMetadata
from backend.core.adapters_impl import (
    CoinGeckoAdapter, DefiLlamaAdapter, GitHubAdapter, RSSAdapter
)
from backend.core.adapters_galxe_layer3 import GalxeAdapter, Layer3Adapter


class AdapterRegistry:
    """Registry for source adapters."""

    def __init__(self):
        self._adapters: Dict[SourceType, List[Type[SourceAdapter]]] = {
            SourceType.API: [CoinGeckoAdapter, DefiLlamaAdapter, GitHubAdapter, GalxeAdapter, Layer3Adapter],
            SourceType.RSS: [RSSAdapter],
            SourceType.HTML: [RSSAdapter],  # HTML scraping uses same base
        }
        self._adapter_by_id: Dict[str, Type[SourceAdapter]] = {
            "coingecko": CoinGeckoAdapter,
            "defillama": DefiLlamaAdapter,
            "github": GitHubAdapter,
            "rss": RSSAdapter,
            "galxe": GalxeAdapter,
            "layer3": Layer3Adapter,
        }

    def get_adapter_class(self, source: Source) -> Optional[Type[SourceAdapter]]:
        """Get the appropriate adapter class for a source."""
        # First try by source ID
        if source.id in self._adapter_by_id:
            return self._adapter_by_id[source.id]

        # Then try by type
        adapters = self._adapters.get(source.type, [])
        if adapters:
            # For API sources, try to match by base_url or name
            for adapter_cls in adapters:
                try:
                    metadata = adapter_cls(source).metadata
                    if source.id in metadata.id or source.name.lower() in metadata.name.lower():
                        return adapter_cls
                except Exception:
                    continue
            return adapters[0]  # Return first as fallback

        return None

    def create_adapter(self, source: Source) -> Optional[SourceAdapter]:
        """Create an adapter instance for a source."""
        adapter_cls = self.get_adapter_class(source)
        if adapter_cls:
            return adapter_cls(source)
        return None

    def list_adapter_metadata(self) -> List[SourceMetadata]:
        """List metadata for all registered adapters."""
        metadata = []
        for adapter_cls in self._adapter_by_id.values():
            # Create a dummy source to get metadata
            dummy_source = Source(
                id=adapter_cls.__name__.lower().replace("adapter", ""),
                name=adapter_cls.__name__,
                type=SourceType.API,
                base_url="https://example.com",  # Valid dummy URL for validation
                config={}
            )
            try:
                adapter = adapter_cls(dummy_source)
                metadata.append(adapter.metadata)
            except Exception:
                pass
        return metadata


adapter_registry = AdapterRegistry()