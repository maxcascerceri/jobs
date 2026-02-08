"""
Base adapter — all source scrapers extend this.
"""
import hashlib
import logging
import random
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import requests
from bs4 import BeautifulSoup

from config import (
    CATEGORY_MAP,
    EMPLOYMENT_TYPE_MAP,
    MAX_RETRIES,
    RATE_LIMIT_SECONDS,
    REQUEST_TIMEOUT,
    RETRY_BACKOFF,
    USER_AGENTS,
)

logger = logging.getLogger(__name__)


@dataclass
class JobListing:
    """Minimal metadata from the listings page."""
    source: str
    source_job_id: str
    url: str
    title: str = ""
    company: str = ""
    location: str = ""
    posted_date: str = ""
    employment_type: str = ""
    category: str = ""


@dataclass
class JobDetail:
    """Full job detail from the detail page."""
    source: str
    source_job_id: str
    title: str
    company_name: str = ""
    company_logo_url: str = ""
    company_domain: str = ""
    description_html: str = ""
    description_text: str = ""
    employment_type: str = "Full-time"
    remote_scope: str = "Anywhere"
    location_text: str = ""
    category: str = ""
    experience_level: str = ""
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "USD"
    salary_period: str = "yearly"
    salary_text: str = ""
    posted_at: str = ""
    apply_url_original: str = ""
    apply_url_final: str = ""
    canonical_url: str = ""
    status: str = "active"
    tags: str = ""


class BaseAdapter(ABC):
    """Base class for all source adapters."""

    SOURCE_NAME: str = ""
    BASE_URL: str = ""
    # Set to True for sources that block simple HTTP (403); uses Playwright headless browser
    USE_HEADLESS: bool = False

    def __init__(self):
        self.session = requests.Session()
        self._last_request_time = 0

    @property
    def name(self) -> str:
        return self.SOURCE_NAME

    def _get_headers(self) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

    def _rate_limit(self):
        elapsed = time.time() - self._last_request_time
        if elapsed < RATE_LIMIT_SECONDS:
            time.sleep(RATE_LIMIT_SECONDS - elapsed)
        self._last_request_time = time.time()

    def fetch(self, url: str, **kwargs) -> requests.Response | None:
        """Fetch a URL with retries and rate limiting. On 403, uses headless browser if USE_HEADLESS is True."""
        self._rate_limit()
        for attempt in range(MAX_RETRIES):
            try:
                resp = self.session.get(
                    url,
                    headers=self._get_headers(),
                    timeout=REQUEST_TIMEOUT,
                    **kwargs,
                )
                # If blocked (403) and this adapter uses headless, try Playwright once
                if resp.status_code == 403 and getattr(self, "USE_HEADLESS", False):
                    logger.info(f"[{self.SOURCE_NAME}] Got 403, trying headless browser for {url}")
                    from headless import fetch_html, HeadlessResponse
                    html = fetch_html(url, timeout_ms=REQUEST_TIMEOUT * 1000)
                    if html:
                        return HeadlessResponse(html, status_code=200, url=url)
                resp.raise_for_status()
                return resp
            except requests.RequestException as e:
                wait = RETRY_BACKOFF ** attempt
                logger.warning(
                    f"[{self.SOURCE_NAME}] Attempt {attempt+1}/{MAX_RETRIES} failed for {url}: {e}. "
                    f"Retrying in {wait}s..."
                )
                if attempt < MAX_RETRIES - 1:
                    time.sleep(wait)
        logger.error(f"[{self.SOURCE_NAME}] All retries exhausted for {url}")
        return None

    def fetch_json(self, url: str, **kwargs) -> dict | list | None:
        """Fetch JSON from a URL."""
        resp = self.fetch(url, **kwargs)
        if resp:
            try:
                return resp.json()
            except ValueError:
                logger.error(f"[{self.SOURCE_NAME}] Invalid JSON from {url}")
        return None

    def parse_html(self, html: str) -> BeautifulSoup:
        return BeautifulSoup(html, "html.parser")

    def normalize_category(self, raw) -> str:
        if not raw:
            return "Other"
        if isinstance(raw, list):
            raw = raw[0] if raw else "Other"
        raw = str(raw).strip()
        # Decode HTML entities
        raw = raw.replace("&amp;", "&")
        key = raw.lower()
        return CATEGORY_MAP.get(key, "Other")

    def normalize_employment_type(self, raw) -> str:
        if not raw:
            return "Full-time"
        if isinstance(raw, list):
            raw = raw[0] if raw else "Full-time"
        key = str(raw).strip().lower()
        return EMPLOYMENT_TYPE_MAP.get(key, "Full-time")

    def generate_fingerprint(self, title: str, company: str, description: str = "") -> str:
        """Generate a content fingerprint for deduplication."""
        normalized = f"{title.lower().strip()}|{company.lower().strip()}"
        if description:
            # Use first 500 chars of description for fingerprint
            desc_clean = re.sub(r'\s+', ' ', description[:500]).lower().strip()
            normalized += f"|{desc_clean}"
        return hashlib.sha256(normalized.encode()).hexdigest()[:32]

    def resolve_apply_url(self, url: str) -> str:
        """Follow redirects to get the final apply URL."""
        if not url:
            return ""
        try:
            resp = self.session.head(
                url,
                headers=self._get_headers(),
                timeout=10,
                allow_redirects=True,
            )
            return resp.url
        except Exception:
            return url

    def clean_text(self, text: str) -> str:
        """Clean up text content."""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def extract_salary(self, text: str) -> dict:
        """Try to extract salary info from text."""
        result = {
            "salary_min": None,
            "salary_max": None,
            "salary_currency": "USD",
            "salary_period": "yearly",
            "salary_text": "",
        }
        if not text:
            return result

        result["salary_text"] = text.strip()

        # Match patterns like "$100,000 - $150,000" or "$100k-$150k"
        money_pattern = r'\$\s*([\d,]+(?:\.\d+)?)\s*[kK]?\s*(?:[-–—to]+\s*\$?\s*([\d,]+(?:\.\d+)?)\s*[kK]?)?'
        match = re.search(money_pattern, text)
        if match:
            min_str = match.group(1).replace(",", "")
            min_val = float(min_str)
            if "k" in text[match.start():match.end()].lower() or min_val < 1000:
                min_val *= 1000
            result["salary_min"] = int(min_val)

            if match.group(2):
                max_str = match.group(2).replace(",", "")
                max_val = float(max_str)
                if "k" in text[match.start():match.end()].lower() or max_val < 1000:
                    max_val *= 1000
                result["salary_max"] = int(max_val)

        # Detect period
        lower = text.lower()
        if any(w in lower for w in ["month", "mo", "/mo", "per month", "monthly"]):
            result["salary_period"] = "monthly"
        elif any(w in lower for w in ["hour", "hr", "/hr", "per hour", "hourly"]):
            result["salary_period"] = "hourly"
        elif any(w in lower for w in ["week", "wk", "/wk", "per week", "weekly"]):
            result["salary_period"] = "weekly"

        # Detect currency
        if "€" in text or "EUR" in text:
            result["salary_currency"] = "EUR"
        elif "£" in text or "GBP" in text:
            result["salary_currency"] = "GBP"
        elif "CAD" in text:
            result["salary_currency"] = "CAD"

        return result

    @abstractmethod
    def crawl_listings(self) -> list[JobListing]:
        """Stage A: Discover job listing URLs."""
        ...

    @abstractmethod
    def crawl_detail(self, listing: JobListing) -> JobDetail | None:
        """Stage B: Extract full job details from a job page."""
        ...
