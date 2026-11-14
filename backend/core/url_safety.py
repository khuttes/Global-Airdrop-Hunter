"""
URL safety validation and SSRF protection.
"""
import ipaddress
import re
from typing import Optional, Set
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

# Private/reserved IP ranges that should not be accessible
PRIVATE_IP_RANGES = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),  # Link-local
    ipaddress.ip_network("::1/128"),  # IPv6 loopback
    ipaddress.ip_network("fe80::/10"),  # IPv6 link-local
    ipaddress.ip_network("fc00::/7"),  # IPv6 unique local
]

# Reserved/special use ranges
RESERVED_IP_RANGES = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("224.0.0.0/4"),  # Multicast
    ipaddress.ip_network("240.0.0.0/4"),  # Reserved
]

BLOCKED_IP_RANGES = PRIVATE_IP_RANGES + RESERVED_IP_RANGES

# Allowed schemes for external fetches
ALLOWED_SCHEMES = {"http", "https"}

# Maximum redirect hops to prevent redirect loops
MAX_REDIRECTS = 5

# Suspicious patterns in URLs
SUSPICIOUS_PATTERNS = [
    r"127\.0\.0\.1",
    r"localhost",
    r"0\.0\.0\.0",
    r"\[::1\]",
    r"169\.254\.",  # Link-local
    r"10\.\d+\.\d+\.\d+",  # 10.x.x.x
    r"172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+",  # 172.16-31.x.x
    r"192\.168\.\d+\.\d+",  # 192.168.x.x
    r"file://",
    r"ftp://",
    r"gopher://",
    r"dict://",
    r"ldap://",
]


class URLValidator:
    """Validates URLs for safety against SSRF and other attacks."""

    def __init__(
        self,
        allow_private_ips: bool = False,
        allowed_domains: Optional[Set[str]] = None,
        blocked_domains: Optional[Set[str]] = None,
        max_redirects: int = MAX_REDIRECTS,
    ):
        self.allow_private_ips = allow_private_ips
        self.allowed_domains = allowed_domains or set()
        self.blocked_domains = blocked_domains or set()
        self.max_redirects = max_redirects

    def validate(self, url: str) -> tuple[bool, Optional[str]]:
        """
        Validate a URL for safety.
        Returns (is_valid, error_message).
        """
        # Basic URL format check
        if not url or not isinstance(url, str):
            return False, "Invalid URL: empty or not a string"

        # Check for suspicious patterns
        for pattern in SUSPICIOUS_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                logger.warning(f"Suspicious URL pattern detected: {url}")
                return False, f"URL contains suspicious pattern: {pattern}"

        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            return False, f"Invalid URL format: {e}"

        # Check scheme
        if parsed.scheme.lower() not in ALLOWED_SCHEMES:
            return False, f"Scheme '{parsed.scheme}' not allowed. Only HTTP/HTTPS allowed."

        # Check hostname
        hostname = parsed.hostname
        if not hostname:
            return False, "URL missing hostname"

        # Check against allowed/blocked domains
        if self.allowed_domains and hostname not in self.allowed_domains:
            return False, f"Domain '{hostname}' not in allowed list"

        if hostname in self.blocked_domains:
            return False, f"Domain '{hostname}' is blocked"

        # Check for IP address in hostname
        try:
            ip = ipaddress.ip_address(hostname)
            if not self._is_ip_allowed(ip):
                return False, f"IP address '{ip}' is not allowed (private/reserved range)"
        except ValueError:
            # Not an IP address, it's a hostname - that's fine
            pass

        # Check port
        if parsed.port:
            # Block well-known privileged ports except 80, 443
            if parsed.port < 1024 and parsed.port not in (80, 443):
                return False, f"Port {parsed.port} is not allowed"

        return True, None

    def _is_ip_allowed(self, ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
        """Check if an IP address is allowed (not private/reserved)."""
        if self.allow_private_ips:
            return True

        for network in BLOCKED_IP_RANGES:
            if ip in network:
                return False
        return True

    async def check_redirects(self, session, url: str) -> tuple[bool, Optional[str], str]:
        """
        Follow redirects and validate each hop.
        Returns (is_valid, error_message, final_url).
        """
        current_url = url
        redirect_count = 0
        visited = set()

        while redirect_count < self.max_redirects:
            if current_url in visited:
                return False, "Redirect loop detected", current_url
            visited.add(current_url)

            is_valid, error = self.validate(current_url)
            if not is_valid:
                return False, error, current_url

            try:
                # Use HEAD request to check redirect
                async with session.head(current_url, allow_redirects=False, timeout=10) as resp:
                    if 300 <= resp.status < 400:
                        location = resp.headers.get("Location")
                        if not location:
                            return False, "Redirect without Location header", current_url
                        
                        # Resolve relative redirects
                        from urllib.parse import urljoin
                        current_url = urljoin(current_url, location)
                        redirect_count += 1
                        continue
                    else:
                        # No redirect, we're at final URL
                        return True, None, current_url
            except Exception as e:
                logger.warning(f"Error checking redirect for {current_url}: {e}")
                return False, f"Failed to follow redirect: {e}", current_url

        return False, f"Too many redirects (max {self.max_redirects})", current_url


def validate_url(url: str, allow_private: bool = False) -> tuple[bool, Optional[str]]:
    """Convenience function for quick URL validation."""
    validator = URLValidator(allow_private_ips=allow_private)
    return validator.validate(url)


def is_safe_url(url: str) -> bool:
    """Quick check if URL is safe (boolean only)."""
    valid, _ = validate_url(url)
    return valid