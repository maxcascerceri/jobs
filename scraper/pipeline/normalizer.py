"""
Normalizer — ensures all job data conforms to the canonical schema.
"""
import hashlib
import re
from datetime import datetime, timezone
from adapters.base import JobDetail


def _generate_fingerprint(title: str, company: str, description: str = "") -> str:
    """Generate a content fingerprint for deduplication."""
    normalized = f"{str(title).lower().strip()}|{str(company).lower().strip()}"
    if description:
        desc_clean = re.sub(r'\s+', ' ', str(description)[:500]).lower().strip()
        normalized += f"|{desc_clean}"
    return hashlib.sha256(normalized.encode()).hexdigest()[:32]


def normalize_job(detail: JobDetail) -> dict:
    """Convert a JobDetail into a normalized dict for database storage."""
    data = {
        "source": str(detail.source or ""),
        "source_job_id": str(detail.source_job_id or ""),
        "title": _clean_title(str(detail.title or "")),
        "company_name": str(detail.company_name or "").strip(),
        "company_logo_url": str(detail.company_logo_url or ""),
        "company_domain": str(detail.company_domain or ""),
        "description_html": str(detail.description_html or ""),
        "description_text": str(detail.description_text or ""),
        "employment_type": str(detail.employment_type or "Full-time"),
        "remote_scope": str(detail.remote_scope or "Anywhere"),
        "location_text": str(detail.location_text or ""),
        "category": str(detail.category or "Other"),
        "experience_level": str(detail.experience_level or ""),
        "salary_min": detail.salary_min,
        "salary_max": detail.salary_max,
        "salary_currency": str(detail.salary_currency or "USD"),
        "salary_period": str(detail.salary_period or "yearly"),
        "salary_text": str(detail.salary_text or ""),
        "posted_at": _normalize_date(detail.posted_at),
        "apply_url_original": str(detail.apply_url_original or ""),
        "apply_url_final": str(detail.apply_url_final or ""),
        "canonical_url": str(detail.canonical_url or ""),
        "status": "active",
        "tags": str(detail.tags or ""),
    }

    # Generate fingerprint
    data["fingerprint_hash"] = _generate_fingerprint(
        data["title"], data["company_name"], data["description_text"]
    )

    # Infer experience level from title if not set
    if not data["experience_level"]:
        data["experience_level"] = _infer_experience(data["title"])

    return data


def _clean_title(title: str) -> str:
    """Clean up job title."""
    if not title:
        return ""
    # Remove extra whitespace
    title = re.sub(r'\s+', ' ', title).strip()
    # Remove common prefixes/suffixes
    title = re.sub(r'^\[.*?\]\s*', '', title)
    title = re.sub(r'\s*\[.*?\]$', '', title)
    return title


def _normalize_date(date_val) -> str:
    """Normalize date string to ISO format."""
    if not date_val:
        return datetime.now(timezone.utc).isoformat()

    # Handle integer timestamps
    if isinstance(date_val, (int, float)):
        try:
            # Could be seconds or milliseconds
            ts = date_val
            if ts > 1e12:
                ts = ts / 1000
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        except (ValueError, OSError):
            return datetime.now(timezone.utc).isoformat()

    date_str = str(date_val)

    # If already ISO-ish
    if re.match(r'\d{4}-\d{2}-\d{2}', date_str):
        return date_str

    # Try common formats
    formats = [
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d %H:%M:%S",
        "%B %d, %Y",
        "%b %d, %Y",
        "%d %B %Y",
        "%d %b %Y",
        "%m/%d/%Y",
        "%d/%m/%Y",
    ]

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            return dt.isoformat()
        except ValueError:
            continue

    # Fallback — return as-is or current date
    return datetime.now(timezone.utc).isoformat()


def _infer_experience(title: str) -> str:
    """Infer experience level from job title."""
    lower = title.lower()
    if any(w in lower for w in ["senior", "sr.", "sr ", "lead", "principal", "staff", "architect"]):
        return "Senior"
    if any(w in lower for w in ["junior", "jr.", "jr ", "entry", "associate", "trainee", "intern"]):
        return "Junior"
    if any(w in lower for w in ["mid-level", "mid level", "intermediate"]):
        return "Mid"
    if any(w in lower for w in ["director", "vp", "vice president", "head of", "chief", "cto", "ceo"]):
        return "Executive"
    if any(w in lower for w in ["manager", "mgr"]):
        return "Manager"
    return "Mid"
