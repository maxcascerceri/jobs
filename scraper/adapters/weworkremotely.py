"""
We Work Remotely adapter.
Site: https://weworkremotely.com
"""
import logging
import re
from urllib.parse import urljoin

from adapters.base import BaseAdapter, JobDetail, JobListing

logger = logging.getLogger(__name__)

CATEGORIES = [
    "remote-jobs/programming",
    "remote-jobs/design",
    "remote-jobs/devops-and-sysadmin",
    "remote-jobs/management-and-finance",
    "remote-jobs/product",
    "remote-jobs/customer-support",
    "remote-jobs/sales-and-marketing",
    "remote-jobs/all-other-remote",
]


class WeWorkRemotelyAdapter(BaseAdapter):
    SOURCE_NAME = "weworkremotely"
    BASE_URL = "https://weworkremotely.com"
    USE_HEADLESS = True  # Site blocks simple HTTP with 403

    def crawl_listings(self) -> list[JobListing]:
        listings = []
        for category_path in CATEGORIES:
            url = f"{self.BASE_URL}/{category_path}"
            resp = self.fetch(url)
            if not resp:
                continue

            soup = self.parse_html(resp.text)
            job_sections = soup.select("section.jobs article ul li")

            for li in job_sections:
                link = li.select_one("a[href*='/remote-jobs/']")
                if not link:
                    continue

                href = link.get("href", "")
                if not href or href.startswith("#") or "/categories/" in href:
                    continue

                # Extract source_job_id from URL
                source_job_id = href.rstrip("/").split("/")[-1]
                job_url = urljoin(self.BASE_URL, href)

                # Get title
                title_el = link.select_one("span.title")
                title = title_el.get_text(strip=True) if title_el else ""

                # Get company
                company_el = link.select_one("span.company")
                company = company_el.get_text(strip=True) if company_el else ""

                # Get location/region
                region_el = link.select_one("span.region")
                region = region_el.get_text(strip=True) if region_el else "Anywhere"

                if not title:
                    continue

                # Determine category from URL path
                cat_name = category_path.split("/")[-1].replace("-", " ").title()

                listings.append(JobListing(
                    source=self.SOURCE_NAME,
                    source_job_id=source_job_id,
                    url=job_url,
                    title=title,
                    company=company,
                    location=region,
                    category=self.normalize_category(cat_name),
                ))

            logger.info(f"[{self.SOURCE_NAME}] Found {len(listings)} listings from {category_path}")

        # Deduplicate by URL
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

        # Job content
        content_el = soup.select_one("div.listing-container")
        if not content_el:
            content_el = soup.select_one("div#job-listing-show-container")

        description_html = ""
        description_text = ""
        if content_el:
            # Remove the header/apply sections to get just the description
            desc_el = content_el.select_one("div.listing-header-container")
            if desc_el:
                desc_el.decompose()
            description_html = str(content_el)
            description_text = content_el.get_text(separator="\n", strip=True)

        # Company name
        company = listing.company
        company_el = soup.select_one("div.company-card h2 a, div.listing-header-container h2")
        if company_el:
            company = company_el.get_text(strip=True) or company

        # Company logo
        logo_url = ""
        logo_el = soup.select_one("div.listing-logo img")
        if logo_el:
            logo_url = logo_el.get("src", "")
            if logo_url and not logo_url.startswith("http"):
                logo_url = urljoin(self.BASE_URL, logo_url)

        # Apply URL — look for apply button/link
        apply_url = ""
        apply_el = soup.select_one("div.apply-container a, a.apply-button, a[href*='apply']")
        if apply_el:
            apply_url = apply_el.get("href", "")
            if apply_url and not apply_url.startswith("http"):
                apply_url = urljoin(self.BASE_URL, apply_url)

        # Employment type
        employment_type = listing.employment_type or "Full-time"
        type_el = soup.select_one("span.listing-tag")
        if type_el:
            type_text = type_el.get_text(strip=True).lower()
            employment_type = self.normalize_employment_type(type_text)

        # Salary
        salary_info = {"salary_min": None, "salary_max": None, "salary_currency": "USD", "salary_period": "yearly", "salary_text": ""}
        salary_el = soup.select_one("span.listing-tag.salary, div.salary")
        if salary_el:
            salary_info = self.extract_salary(salary_el.get_text(strip=True))

        # Posted date
        posted_at = listing.posted_date
        date_el = soup.select_one("time")
        if date_el:
            posted_at = date_el.get("datetime", "") or date_el.get_text(strip=True)

        # Tags
        tags = []
        tag_els = soup.select("span.listing-tag")
        for t in tag_els:
            tags.append(t.get_text(strip=True))

        fingerprint = self.generate_fingerprint(listing.title, company, description_text)

        return JobDetail(
            source=self.SOURCE_NAME,
            source_job_id=listing.source_job_id,
            title=listing.title,
            company_name=company,
            company_logo_url=logo_url,
            description_html=description_html,
            description_text=description_text,
            employment_type=employment_type,
            remote_scope="Anywhere",
            location_text=listing.location,
            category=listing.category,
            salary_min=salary_info["salary_min"],
            salary_max=salary_info["salary_max"],
            salary_currency=salary_info["salary_currency"],
            salary_period=salary_info["salary_period"],
            salary_text=salary_info["salary_text"],
            posted_at=posted_at,
            apply_url_original=apply_url,
            apply_url_final=apply_url,
            canonical_url=listing.url,
            tags=",".join(tags) if tags else "",
        )
