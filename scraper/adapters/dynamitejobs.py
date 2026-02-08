"""
Dynamite Jobs adapter.
Site: https://dynamitejobs.com
Note: Uses their public job listings page.
"""
import logging
import re
from urllib.parse import urljoin

from adapters.base import BaseAdapter, JobDetail, JobListing

logger = logging.getLogger(__name__)


class DynamiteJobsAdapter(BaseAdapter):
    SOURCE_NAME = "dynamitejobs"
    BASE_URL = "https://dynamitejobs.com"
    USE_HEADLESS = True  # May block simple HTTP

    def crawl_listings(self) -> list[JobListing]:
        listings = []
        # Dynamite Jobs has a jobs listing page
        urls_to_crawl = [
            f"{self.BASE_URL}/remote-jobs",
            f"{self.BASE_URL}/remote-developer-jobs",
            f"{self.BASE_URL}/remote-marketing-jobs",
            f"{self.BASE_URL}/remote-design-jobs",
            f"{self.BASE_URL}/remote-sales-jobs",
            f"{self.BASE_URL}/remote-customer-service-jobs",
            f"{self.BASE_URL}/remote-operations-jobs",
            f"{self.BASE_URL}/remote-finance-accounting-jobs",
        ]

        for page_url in urls_to_crawl:
            resp = self.fetch(page_url)
            if not resp:
                continue

            soup = self.parse_html(resp.text)

            # Find job cards
            job_cards = soup.select("a[href*='/job/']")
            for card in job_cards:
                href = card.get("href", "")
                if not href or "/job/" not in href:
                    continue

                job_url = urljoin(self.BASE_URL, href)
                source_job_id = href.rstrip("/").split("/")[-1]

                # Title
                title_el = card.select_one("h3, h4, .job-title, [class*='title']")
                title = title_el.get_text(strip=True) if title_el else card.get_text(strip=True)[:100]

                # Company
                company = ""
                company_el = card.select_one(".company-name, [class*='company']")
                if company_el:
                    company = company_el.get_text(strip=True)

                if not title or len(title) < 3:
                    continue

                listings.append(JobListing(
                    source=self.SOURCE_NAME,
                    source_job_id=source_job_id,
                    url=job_url,
                    title=self.clean_text(title),
                    company=company,
                ))

            logger.info(f"[{self.SOURCE_NAME}] Found {len(listings)} from {page_url}")

        seen = set()
        unique = []
        for l in listings:
            if l.url not in seen:
                seen.add(l.url)
                unique.append(l)
        return unique

    def crawl_detail(self, listing: JobListing) -> JobDetail | None:
        resp = self.fetch(listing.url)
        if not resp:
            return None

        soup = self.parse_html(resp.text)

        # Title
        title = listing.title
        title_el = soup.select_one("h1")
        if title_el:
            title = title_el.get_text(strip=True) or title

        # Company
        company = listing.company
        company_el = soup.select_one("a[href*='/company/'], [class*='company'] a, h2 a")
        if company_el:
            company = company_el.get_text(strip=True) or company

        # Logo
        logo_url = ""
        logo_el = soup.select_one("img[src*='logo'], img[class*='logo'], img[alt*='logo']")
        if logo_el:
            logo_url = logo_el.get("src", "")
            if logo_url and not logo_url.startswith("http"):
                logo_url = urljoin(self.BASE_URL, logo_url)

        # Description
        desc_el = soup.select_one("div.job-description, div[class*='description'], article, div.prose")
        description_html = str(desc_el) if desc_el else ""
        description_text = desc_el.get_text(separator="\n", strip=True) if desc_el else ""

        # Apply URL
        apply_url = ""
        apply_el = soup.select_one("a[href*='apply'], a.apply-button, a[class*='apply'], a[data-action*='apply']")
        if apply_el:
            apply_url = apply_el.get("href", "")
            if apply_url and not apply_url.startswith("http"):
                apply_url = urljoin(self.BASE_URL, apply_url)

        # Salary
        salary_info = {"salary_min": None, "salary_max": None, "salary_currency": "USD", "salary_period": "yearly", "salary_text": ""}
        salary_el = soup.select_one("[class*='salary'], [class*='compensation']")
        if salary_el:
            salary_info = self.extract_salary(salary_el.get_text(strip=True))

        # Employment type
        emp_type = "Full-time"
        type_el = soup.select_one("[class*='type'], [class*='employment']")
        if type_el:
            emp_type = self.normalize_employment_type(type_el.get_text(strip=True))

        # Location
        location = ""
        loc_el = soup.select_one("[class*='location']")
        if loc_el:
            location = loc_el.get_text(strip=True)

        fingerprint = self.generate_fingerprint(title, company, description_text)

        return JobDetail(
            source=self.SOURCE_NAME,
            source_job_id=listing.source_job_id,
            title=title,
            company_name=company,
            company_logo_url=logo_url,
            description_html=description_html,
            description_text=description_text,
            employment_type=emp_type,
            remote_scope="Anywhere",
            location_text=location,
            category=listing.category or "Other",
            salary_min=salary_info["salary_min"],
            salary_max=salary_info["salary_max"],
            salary_currency=salary_info["salary_currency"],
            salary_period=salary_info["salary_period"],
            salary_text=salary_info["salary_text"],
            apply_url_original=apply_url,
            apply_url_final=apply_url,
            canonical_url=listing.url,
        )
