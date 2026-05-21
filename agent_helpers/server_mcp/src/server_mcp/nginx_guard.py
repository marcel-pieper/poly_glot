from __future__ import annotations

import re

SITE_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]*$")
DOMAIN_RE = re.compile(
    r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$",
    re.IGNORECASE,
)

NGINX_SITES_AVAILABLE = "/etc/nginx/sites-available"
NGINX_SITES_ENABLED = "/etc/nginx/sites-enabled"


def validate_site_name(site_name: str) -> str:
    name = site_name.strip()
    if not SITE_NAME_RE.match(name):
        raise ValueError(
            f"Invalid site name '{site_name}'. Use lowercase letters, digits, hyphens, underscores; "
            "must start with a letter."
        )
    return name


def validate_domain(domain: str) -> str:
    d = domain.strip().lower()
    if not DOMAIN_RE.match(d):
        raise ValueError(f"Invalid domain name: {domain}")
    return d


def site_available_path(site_name: str) -> str:
    name = validate_site_name(site_name)
    return f"{NGINX_SITES_AVAILABLE}/{name}"


def site_enabled_path(site_name: str) -> str:
    name = validate_site_name(site_name)
    return f"{NGINX_SITES_ENABLED}/{name}"
