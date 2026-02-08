"""
Working Nomads adapter.
Site: https://www.workingnomads.com
Uses their public API.
"""
import logging
from urllib.parse import urljoin

from adapters.base import BaseAdapter, JobDetail, JobListing

logger = logging.getLogger(__name__)


class WorkingNomadsAdapter(BaseAdapter):
    SOURCE_NAME = "workingnomads"
    BASE_URL = "https://www.workingnomads.com"
    API_URL = "https://www.workingnomads.com/api/exposed_jobs/"

    def crawl_listings(self) -> list[JobListing]:
        listings = []

        data = self.fetch_json(self.API_URL)
        if not data:
            # Fallback to HTML
            return self._crawl_listings_html()

        if isinstance(data, list):
            jobs = data
        elif isinstance(data, dict):
            jobs = data.get("results", data.get("jobs", []))
        else:
            return self._crawl_listings_html()

        for job in jobs:
            source_job_id = str(job.get("id", job.get("slug", "")))
            title = job.get("title", "")
            company = job.get("company_name", "")
            url = job.get("url", "")
            location = job.get("location", "Remote")
            category = job.get("category_name", "Other")
            emp_type = job.get("job_type", "Full-time")
            posted = job.get("pub_date", "")

            if not title or not url:
                continue

            if not url.startswith("http"):
                url = urljoin(self.BASE_URL, url)

            listings.append(JobListing(
                source=self.SOURCE_NAME,
                source_job_id=source_job_id,
                url=url,
                title=title,
                company=company,
                location=location,
                category=self.normalize_category(category),
                employment_type=self.normalize_employment_type(emp_type),
                posted_date=posted,
            ))

        logger.info(f"[{self.SOURCE_NAME}] Found {len(listings)} listings from API")
        return listings

    def _crawl_listings_html(self) -> list[JobListing]:
        """Fallback HTML scraping."""
        listings = []
        resp = self.fetch(f"{self.BASE_URL}/jobs")
        if not resp:
            return listings

        soup = self.parse_html(resp.text)
        job_links = soup.select("a[href*='/job/'], a[href*='/jobs/']")

        for link in job_links:
            href = link.get("href", "")
            if not href:
                continue

            url = urljoin(self.BASE_URL, href)
            source_id = href.rstrip("/").split("/")[-1]
            title = link.get_text(strip=True)

            if not title or len(title) < 5:
                continue

            listings.append(JobListing(
                source=self.SOURCE_NAME,
                source_job_id=source_id,
                url=url,
                title=title,
            ))

        logger.info(f"[{self.SOURCE_NAME}] Found {len(listings)} listings from HTML")
        return listings

    def crawl_detail(self, listing: JobListing) -> JobDetail | None:
        resp = self.fetch(listing.url)
        if not resp:
            return None

        soup = self.parse_html(resp.text)

        title = listing.title
        h1 = soup.select_one("h1")
        if h1:
            title = h1.get_text(strip=True) or title

        company = listing.company
        company_el = soup.select_one(".company-name, a[href*='/company/'], h2")
        if company_el:
            txt = company_el.get_text(strip=True)
            if txt and len(txt) < 100:
                company = txt or company

        logo_url = ""
        logo_el = soup.select_one("img[class*='logo'], img[alt*='logo']")
        if logo_el:
            src = logo_el.get("src", "")
            logo_url = urljoin(self.BASE_URL, src) if src else ""

        desc_el = soup.select_one("div.description, div.job-description, article, div.content")
        description_html = str(desc_el) if desc_el else ""
        description_text = desc_el.get_text(separator="\n", strip=True) if desc_el else ""

        apply_url = ""
        apply_el = soup.select_one("a.apply-btn, a[href*='apply'], a[class*='apply']")
        if apply_el:
            apply_url = apply_el.get("href", "")
            if apply_url and not apply_url.startswith("http"):
                apply_url = urljoin(self.BASE_URL, apply_url)

        # If no explicit apply, use the job URL itself
        if not apply_url:
            apply_url = listing.url

        fingerprint = self.generate_fingerprint(title, company, description_text)

        return JobDetail(
            source=self.SOURCE_NAME,
            source_job_id=listing.source_job_id,
            title=title,
            company_name=company,
            company_logo_url=logo_url,
            description_html=description_html,
            description_text=description_text,
            employment_type=listing.employment_type or "Full-time",
            remote_scope="Anywhere",
            location_text=listing.location,
            category=listing.category or "Other",
            posted_at=listing.posted_date,
            apply_url_original=apply_url,
            apply_url_final=apply_url,
            canonical_url=listing.url,
        )
