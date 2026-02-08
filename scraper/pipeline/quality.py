"""
Quality gates — filter out low-quality or broken job entries.
"""
import logging

logger = logging.getLogger(__name__)


def passes_quality(job_data: dict) -> tuple[bool, str]:
    """
    Check if a job passes quality gates.
    Returns (passes, reason).
    """
    title = job_data.get("title", "").strip()
    company = job_data.get("company_name", "").strip()
    description = job_data.get("description_text", "").strip()
    apply_url = job_data.get("apply_url_final", "") or job_data.get("apply_url_original", "")
    canonical_url = job_data.get("canonical_url", "")

    # Must have a title
    if not title or len(title) < 5:
        return False, "Missing or too-short title"

    # Must have a company
    if not company:
        return False, "Missing company name"

    # Must have some description
    if not description or len(description) < 50:
        return False, f"Description too short ({len(description)} chars)"

    # Must have some way to apply
    if not apply_url and not canonical_url:
        return False, "Missing apply URL and canonical URL"

    # Filter out obvious spam/junk titles
    spam_indicators = [
        "test job", "test posting", "do not apply",
        "placeholder", "lorem ipsum", "asdf",
    ]
    if any(s in title.lower() for s in spam_indicators):
        return False, f"Spam-like title: {title}"

    return True, "OK"
