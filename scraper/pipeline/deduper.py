"""
Deduplication engine — layered approach.
"""
import logging

from db import check_duplicate_fingerprint

logger = logging.getLogger(__name__)


def check_duplicate(conn, job_data: dict) -> dict | None:
    """
    Check for duplicates using layered approach.
    Returns the existing duplicate info dict or None.
    """
    # Level 1: Source + source_job_id (handled by UNIQUE constraint in upsert)

    # Level 2: Content fingerprint (same title+company → same job)
    fingerprint = job_data.get("fingerprint_hash")
    if fingerprint:
        dup = check_duplicate_fingerprint(conn, fingerprint)
        if dup:
            logger.info(
                f"Duplicate (fingerprint): '{job_data.get('title')}' matches job {dup['id']} from {dup['source']}"
            )
            return dup

    # Apply URL is NOT used for dedup: many different jobs share the same company careers page.
    return None
