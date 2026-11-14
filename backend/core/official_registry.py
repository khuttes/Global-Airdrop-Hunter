"""
Official domain registry for Global Airdrop Hunter.
Contains verified official domains for major projects and platforms.
This registry should be maintained and updated regularly.
"""

# Official domains for major blockchain ecosystems and platforms
# These domains are considered "officially corroborated" sources
OFFICIAL_DOMAINS = {
    # Ethereum ecosystem
    "ethereum.org",
    "ethereumfoundation.org",
    "consensys.net",
    "openzeppelin.com",
    "gnosis.io",
    "safe.global",
    
    # Layer 2 / Scaling solutions
    "arbitrum.io",
    "optimism.io",
    "polygon.technology",
    "polygon.io",
    "base.org",
    "linea.build",
    "zksync.io",
    "scroll.io",
    "mantle.xyz",
    "blast.io",
    "mode.network",
    "metis.io",
    
    # DeFi protocols
    "uniswap.org",
    "aave.com",
    "lido.fi",
    "curve.fi",
    "compound.finance",
    "makerdao.com",
    "synthetix.io",
    "balancer.fi",
    "dydx.exchange",
    "gmx.io",
    "perp.fi",
    "traderjoexyz.com",
    "camelot.exchange",
    "ramses.exchange",
    
    # Infrastructure
    "chainlink.com",
    "thegraph.com",
    "alchemy.com",
    "infura.io",
    "quicknode.com",
    "ankr.com",
    "getblock.io",
    "blastapi.io",
    
    # Wallets
    "metamask.io",
    "walletconnect.com",
    "rainbow.me",
    "trustwallet.com",
    "phantom.app",
    "xdefi.io",
    "frame.sh",
    "zerion.io",
    "zerion.xyz",
    "zapper.xyz",
    "debank.com",
    
    # Analytics
    "coingecko.com",
    "coingecko.io",
    "defillama.com",
    "token.terminal",
    "dune.com",
    "dune.xyz",
    "nansen.ai",
    "arkhamintelligence.com",
    "bubblemaps.io",
    
    # Launchpads / Platforms
    "coinlist.co",
    "republic.co",
    "seedify.fund",
    "polkastarter.com",
    "bounce.finance",
    "daomaker.com",
    "poolz.finance",
    "gamefi.org",
    "coinxpad.io",
    
    # Galxe / Layer3
    "galxe.com",
    "galxe.io",
    "layer3.xyz",
    "layer3.xyz",
    
    # Quest / Campaign platforms
    "crew3.xyz",
    "zealy.io",
    "guild.xyz",
    "dework.xyz",
    "layer3.xyz",
    "gitcoin.co",
    "gitcoin.io",
    
    # NFT / Marketplace
    "opensea.io",
    "blur.io",
    "looksrare.org",
    "x2y2.io",
    "element.market",
    "magiceden.io",
    "tensor.trade",
    "tensor.hx",
    
    # Cross-chain
    "wormhole.com",
    "layerzero.network",
    "celer.network",
    "synapseprotocol.com",
    "multichain.org",
    "anyswap.exchange",
    
    # Gaming / Metaverse
    "axieinfinity.com",
    "the sandbox.game",
    "decentraland.org",
    "illuvium.io",
    "staratlas.com",
    "bigtime.gg",
    "pixels.xyz",
    
    # Identity / Social
    "ens.domains",
    "lens.xyz",
    "farcaster.xyz",
    "cyberconnect.me",
    "mask.io",
    "worldcoin.org",
    "proof-of-humanity.id",
    
    # Security / Audit
    "trailofbits.com",
    "openzeppelin.com",
    "peckshield.com",
    "certik.com",
    "slowmist.com",
    "quantstamp.com",
    "halborn.com",
    "immunefi.com",
    
    # Grants / Funding
    "ethereum.foundation",
    "esp.ethereum.foundation",
    "grants.ethereum.org",
    "retroPGF.org",
    "optimism.io",
    "arbitrum.foundation",
    "polygon.technology",
    
    # News / Media (official project blogs only)
    "blog.ethereum.org",
    "blog.arbitrum.io",
    "blog.optimism.io",
    "blog.polygon.technology",
    "blog.base.org",
    "medium.com/ethereum-foundation",
    "medium.com/arbitrum",
    "medium.com/optimismfnd",
    
    # GitHub (for official repos)
    "github.com",
    "gitlab.com",
}

# Known suspicious/phishing TLDs and patterns
SUSPICIOUS_PATTERNS = [
    # Typosquatting common patterns
    "ethereum.",
    "uniswap.",
    "aave.",
    "lido.",
    "opensea.",
    "metamask.",
    "coinbase.",
    "binance.",
    "bybit.",
    "okx.",
    "kucoin.",
    "gate.io",
    "htx.",
    "mexc.",
    "kraken.",
    "gemini.",
    "crypto.",
    "blockchain.",
    "wallet.",
    "claim.",
    "airdrop.",
    "reward.",
    "token.",
    "nft.",
    "mint.",
    "stake.",
    "farm.",
    "yield.",
    "swap.",
    "bridge.",
    "dex.",
    "defi.",
    "web3.",
    "dapp.",
    "protocol.",
    "finance.",
    "capital.",
    "ventures.",
    "labs.",
    "dao.",
    "foundation.",
    "labs.",
    "inc.",
    "tech.",
    "xyz.",
    "io.",
    "app.",
    "ai.",
    "org.",
    "com.",
]

# Known phishing/fake domains (user-reported or detected)
KNOWN_PHISHING_DOMAINS = {
    # Add known phishing domains here as they are discovered
    # "fake-ethereum.org",
    # "uniswap-airdrop.com",
}

# Project-specific official domains (for subdomain verification)
PROJECT_OFFICIAL_DOMAINS = {
    "ethereum": ["ethereum.org", "ethereumfoundation.org"],
    "arbitrum": ["arbitrum.io", "arbitrum.foundation"],
    "optimism": ["optimism.io", "optimismfoundation.org"],
    "polygon": ["polygon.technology", "polygon.io"],
    "base": ["base.org", "base.foundation"],
    "uniswap": ["uniswap.org", "app.uniswap.org"],
    "aave": ["aave.com", "app.aave.com"],
    "lido": ["lido.fi", "stake.lido.fi"],
    "metamask": ["metamask.io", "portfolio.metamask.io"],
    "coinbase": ["coinbase.com", "wallet.coinbase.com"],
    "opensea": ["opensea.io", "api.opensea.io"],
    "galxe": ["galxe.com", "app.galxe.com"],
    "layer3": ["layer3.xyz", "app.layer3.xyz"],
    "chainlink": ["chainlink.com", "data.chainlink.com"],
    "thegraph": ["thegraph.com", "api.thegraph.com"],
}


def is_official_domain(domain: str) -> bool:
    """Check if a domain is in the official registry."""
    domain = domain.lower()
    if domain in OFFICIAL_DOMAINS:
        return True
    # Check subdomains
    for official in OFFICIAL_DOMAINS:
        if domain.endswith("." + official):
            return True
    return False


def is_suspicious_domain(domain: str) -> bool:
    """Check if a domain matches suspicious patterns."""
    domain = domain.lower()
    for pattern in SUSPICIOUS_PATTERNS:
        if domain.startswith(pattern):
            return True
    return False


def is_known_phishing(domain: str) -> bool:
    """Check if a domain is a known phishing domain."""
    return domain.lower() in KNOWN_PHISHING_DOMAINS


def get_project_from_domain(domain: str) -> Optional[str]:
    """Get the project name associated with an official domain."""
    domain = domain.lower()
    for project, domains in PROJECT_OFFICIAL_DOMAINS.items():
        if domain in domains or any(domain.endswith("." + d) for d in domains):
            return project
    return None


def add_official_domain(domain: str) -> None:
    """Add a domain to the official registry (for runtime updates)."""
    OFFICIAL_DOMAINS.add(domain.lower())


def remove_official_domain(domain: str) -> None:
    """Remove a domain from the official registry (for runtime updates)."""
    OFFICIAL_DOMAINS.discard(domain.lower())