"""
Deduplication utilities for Global Airdrop Hunter.
Handles URL normalization, stable ID generation, and duplicate detection.
"""

import re
import hashlib
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime


# Tracking parameters to strip from URLs
TRACKING_PARAMS = {
    'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
    'ref', 'source', 'campaign', 'medium', 'affiliate', 'aff_id',
    'fbclid', 'gclid', 'msclkid', 'twclid', 'li_fat_id',
    'igshid', 'igsh', 'mkt_tok', 'vero_id', 'vero_conv',
    'mc_cid', 'mc_eid', '_hsmi', '_hsenc', 'hsCtaTracking',
    'omnisend', 'klaviyo', 'mailchimp', 'sendgrid', 'sendinblue',
    'customer_id', 'user_id', 'session_id', 'tracking_id',
    'utm_id', 'utm_source_platform', 'utm_creative_format', 'utm_marketing_tactic'
}


def normalize_url(url: str) -> str:
    """
    Normalize a URL for deduplication by:
    1. Lowercasing the scheme and host
    2. Removing default ports (80 for HTTP, 443 for HTTPS)
    3. Removing tracking/query parameters
    4. Removing trailing slashes from path (except root)
    5. Sorting remaining query parameters
    """
    if not url:
        return url

    try:
        parsed = urlparse(url.strip())
        
        # Normalize scheme and netloc
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        
        # Remove default ports
        if (scheme == 'http' and netloc.endswith(':80')) or \
           (scheme == 'https' and netloc.endswith(':443')):
            netloc = netloc.rsplit(':', 1)[0]
        
        # Remove www. prefix for consistency
        if netloc.startswith('www.'):
            netloc = netloc[4:]
        
        # Parse and filter query parameters
        query_params = parse_qs(parsed.query, keep_blank_values=True)
        filtered_params = {
            k: v for k, v in query_params.items()
            if k.lower() not in TRACKING_PARAMS
        }
        
        # Sort parameters for consistent ordering
        sorted_params = sorted(filtered_params.items())
        new_query = urlencode(sorted_params, doseq=True)
        
        # Normalize path - remove trailing slash unless it's just "/"
        path = parsed.path.rstrip('/')
        if not path:
            path = '/'
        
        # Reconstruct URL
        normalized = urlunparse((
            scheme,
            netloc,
            path,
            parsed.params,
            new_query,
            ''  # Remove fragment
        ))
        
        return normalized
    except Exception:
        # If parsing fails, return original URL
        return url.strip()


def generate_stable_id(
    project: Optional[str],
    name: str,
    network: Optional[str],
    deadline: Optional[datetime] = None,
    official_url: Optional[str] = None
) -> str:
    """
    Generate a stable ID for a campaign based on its identifying attributes.
    This ID should remain consistent across re-discoveries of the same campaign.
    Uses only the core identifying fields: project, name, network.
    Excludes deadline and URLs which may vary between sources.
    """
    parts = [
        (project or "").strip().lower(),
        name.strip().lower(),
        (network or "").strip().lower(),
    ]
    
    # Filter out empty parts for the hash
    content = "|".join(p for p in parts if p)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def compute_content_hash(text: str) -> str:
    """Compute a content hash for deduplication of text content."""
    if not text:
        return ""
    # Normalize whitespace
    normalized = re.sub(r'\s+', ' ', text.strip().lower())
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate Jaccard similarity between two texts based on word shingles.
    Returns a value between 0 and 1.
    """
    if not text1 or not text2:
        return 0.0
    
    def get_shingles(text: str, k: int = 3) -> set:
        words = re.findall(r'\w+', text.lower())
        if len(words) < k:
            return set([' '.join(words)])
        return set(' '.join(words[i:i+k]) for i in range(len(words) - k + 1))
    
    shingles1 = get_shingles(text1)
    shingles2 = get_shingles(text2)
    
    if not shingles1 or not shingles2:
        return 0.0
    
    intersection = len(shingles1 & shingles2)
    union = len(shingles1 | shingles2)
    
    return intersection / union if union > 0 else 0.0


def find_potential_duplicates(
    campaign: Dict[str, Any],
    existing_campaigns: List[Dict[str, Any]],
    threshold: float = 0.85
) -> List[Tuple[Dict[str, Any], float, str]]:
    """
    Find potential duplicates among existing campaigns.
    Returns list of (campaign, similarity_score, match_reason).
    """
    duplicates = []
    
    new_name = campaign.get('name', '').lower()
    new_project = campaign.get('project', '').lower()
    new_network = campaign.get('network', '').lower()
    new_official_url = normalize_url(campaign.get('official_url', ''))
    new_campaign_url = normalize_url(campaign.get('campaign_url', ''))
    new_deadline = campaign.get('deadline')
    
    for existing in existing_campaigns:
        reasons = []
        scores = []
        
        # 1. Exact stable_id match (highest confidence)
        if campaign.get('stable_id') and campaign['stable_id'] == existing.get('stable_id'):
            return [(existing, 1.0, 'exact_stable_id')]
        
        # 2. URL overlap (official_url or campaign_url)
        existing_official = normalize_url(existing.get('official_url', ''))
        existing_campaign = normalize_url(existing.get('campaign_url', ''))
        
        if new_official_url and existing_official and new_official_url == existing_official:
            reasons.append('official_url_match')
            scores.append(0.95)
        
        if new_campaign_url and existing_campaign and new_campaign_url == existing_campaign:
            reasons.append('campaign_url_match')
            scores.append(0.95)
        
        # 3. Domain + title similarity
        existing_name = existing.get('name', '').lower()
        existing_project = existing.get('project', '').lower()
        existing_network = existing.get('network', '').lower()
        
        # Title similarity
        title_sim = calculate_similarity(new_name, existing_name)
        if title_sim > 0.7:
            reasons.append(f'title_similarity_{title_sim:.2f}')
            scores.append(title_sim * 0.8)
        
        # Project similarity
        project_sim = calculate_similarity(new_project, existing_project)
        if project_sim > 0.7:
            reasons.append(f'project_similarity_{project_sim:.2f}')
            scores.append(project_sim * 0.6)
        
        # 4. Network + deadline match
        if new_network and existing_network and new_network == existing_network:
            if new_deadline and existing.get('deadline'):
                try:
                    new_dl = datetime.fromisoformat(new_deadline.replace('Z', '+00:00'))
                    existing_dl = datetime.fromisoformat(existing['deadline'].replace('Z', '+00:00'))
                    if abs((new_dl - existing_dl).days) <= 1:
                        reasons.append('network_deadline_match')
                        scores.append(0.8)
                except Exception:
                    pass
            else:
                reasons.append('network_match')
                scores.append(0.3)
        
        # Calculate overall score
        if scores:
            overall_score = max(scores)
            if overall_score >= threshold:
                duplicates.append((existing, overall_score, '; '.join(reasons)))
    
    # Sort by score descending
    duplicates.sort(key=lambda x: x[1], reverse=True)
    return duplicates


class DuplicateMatch:
    """Represents a potential duplicate match with details."""
    
    def __init__(
        self,
        existing_id: str,
        existing_stable_id: str,
        similarity: float,
        reasons: List[str],
        field_comparison: Dict[str, Any]
    ):
        self.existing_id = existing_id
        self.existing_stable_id = existing_stable_id
        self.similarity = similarity
        self.reasons = reasons
        self.field_comparison = field_comparison
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'existing_id': self.existing_id,
            'existing_stable_id': self.existing_stable_id,
            'similarity': self.similarity,
            'reasons': self.reasons,
            'field_comparison': self.field_comparison,
            'timestamp': self.timestamp.isoformat()
        }