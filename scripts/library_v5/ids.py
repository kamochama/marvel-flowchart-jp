from __future__ import annotations

import hashlib
import re
import unicodedata


_NON_ALNUM = re.compile(r"[^a-z0-9]+")
_MULTI_DASH = re.compile(r"-+")


def _ascii_slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).casefold()
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = _NON_ALNUM.sub("-", ascii_text).strip("-")
    return _MULTI_DASH.sub("-", slug)


def slug_id(prefix: str, *parts: str) -> str:
    """Return a deterministic stable ID for canonical v5 rows.

    Human-readable ASCII slugs are preferred. When the source text has no
    meaningful ASCII representation, a SHA-256 suffix keeps the ID stable
    without pretending to transliterate names.
    """
    prefix_slug = _ascii_slug(prefix)
    if not prefix_slug:
        raise ValueError("prefix must contain at least one ASCII letter or digit")

    source = " | ".join(str(part).strip() for part in parts if str(part).strip())
    if not source:
        raise ValueError("at least one non-empty ID part is required")

    body = _ascii_slug(source)
    if not body:
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()[:10]
        body = f"x-{digest}"

    return f"{prefix_slug}-{body}"
