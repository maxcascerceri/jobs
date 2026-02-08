"""
Himalayas adapter.
Site: https://himalayas.app
Uses their public API.
"""
import logging
from urllib.parse import urljoin

from adapters.base import BaseAdapter, JobDetail, JobListing

logger = logging.getLogger(__name__)


class HimalayasAdapter(BaseAdapter):
    SOURCE_NAME = "himalayas"
    BASE_URL = "https://himalayas.app"
    API_URL = "https://himalayas.app/jobs/api"

    def crawl_listings(self) -> list[JobListing]:
        listings = []
        offset = 0
        limit = 50

        while True:
            params = {"limit": limit, "offset": offset}
            data = self.fetch_json(self.API_URL, params=params)

            if not data:
                break

            jobs = data.get("jobs", [])
            if not jobs:
                break

            for job in jobs:
                title = job.get("title", "")
                company = job.get("companyName", "")
                company_logo = job.get("companyLogo", "")
                guid = job.get("guid", "")
                application_link = job.get("applicationLink", "")

                # Derive source_job_id from guid URL
                source_job_id = guid.rstrip("/").split("/")[-1] if guid else title.lower().replace(" ", "-")[:50]

                # Location restrictions is a list
                location_restrictions = job.get("locationRestrictions", [])
                location = ", ".join(location_restrictions) if location_restrictions else "Anywhere"

                # Categories — use parentCategories first, then categories
                parent_cats = job.get("parentCategories", [])
                categories = job.get("categories", [])
                category_raw = parent_cats[0] if parent_cats else (categories[0].replace("-", " ") if categories else "Other")

                emp_type = job.get("employmentType", "Full Time")
                posted = job.get("pubDate", "")  # Unix timestamp as int
                description = job.get("description", "")
                excerpt = job.get("excerpt", "")

                salary_min = job.get("minSalary")
                salary_max = job.get("maxSalary")
                salary_currency = job.get("currency", "USD")

                seniority = job.get("seniority", [])
                experience_level = seniority[0] if seniority else ""

                canonical_url = guid or application_link

                if not title:
                    continue

                listing = JobListing(
                    source=self.SOURCE_NAME,
                    source_job_id=source_job_id,
                    url=canonical_url,
                    title=title,
                    company=company,
                    location=location,
                    category=self.normalize_category(category_raw),
                    employment_type=self.normalize_employment_type(emp_type),
                    posted_date=str(posted),
                )
                # Store extra metadata for detail phase
                listing._extra = {
                    "company_logo": company_logo,
                    "salary_min": salary_min,
                    "salary_max": salary_max,
                    "salary_currency": salary_currency,
                    "description": description,
                    "excerpt": excerpt,
                    "apply_url": application_link,
                    "experience_level": experience_level,
                }
                listings.append(listing)

            offset += limit
            if len(jobs) < limit:
                break
            if offset >= 500:
                break

        logger.info(f"[{self.SOURCE_NAME}] Found {len(listings)} listings from API")
        return listings

    def crawl_detail(self, listing: JobListing) -> JobDetail | None:
        extra = getattr(listing, "_extra", {})

        if extra.get("description"):
            description = str(extra["description"])
            description_text = self.parse_html(description).get_text(separator="\n", strip=True) if "<" in description else description

            salary_text = ""
            sal_min = extra.get("salary_min")
            sal_max = extra.get("salary_max")
            sal_cur = extra.get("salary_currency", "USD")
            if sal_min or sal_max:
                parts = []
                if sal_min:
                    parts.append(f"${int(sal_min):,}")
                if sal_max:
                    parts.append(f"${int(sal_max):,}")
                salary_text = f"{' - '.join(parts)}/yr ({sal_cur})"

            return JobDetail(
                source=self.SOURCE_NAME,
                source_job_id=str(listing.source_job_id),
                title=listing.title,
                company_name=listing.company,
                company_logo_url=str(extra.get("company_logo", "") or ""),
                description_html=description if "<" in description else f"<p>{description}</p>",
                description_text=description_text,
                employment_type=listing.employment_type,
                remote_scope="Anywhere",
                location_text=listing.location,
                category=listing.category,
                experience_level=str(extra.get("experience_level", "")),
                salary_min=int(sal_min) if sal_min else None,
                salary_max=int(sal_max) if sal_max else None,
                salary_currency=str(sal_cur),
                salary_text=salary_text,
                posted_at=str(listing.posted_date),
                apply_url_original=str(extra.get("apply_url", "") or ""),
                apply_url_final=str(extra.get("apply_url", "") or ""),
                canonical_url=listing.url,
            )

        # Fallback: scrape the detail page
        resp = self.fetch(listing.url)
        if not resp:
            return None

        soup = self.parse_html(resp.text)

        title = listing.title
        h1 = soup.select_one("h1")
        if h1:
            title = h1.get_text(strip=True) or title

        company = listing.company
        desc_el = soup.select_one("div[class*='description'], article, div.prose")
        description_html = str(desc_el) if desc_el else ""
        description_text = desc_el.get_text(separator="\n", strip=True) if desc_el else ""

        apply_url = ""
        apply_el = soup.select_one("a[href*='apply'], a[class*='apply']")
        if apply_el:
            apply_url = apply_el.get("href", "")

        return JobDetail(
            source=self.SOURCE_NAME,
            source_job_id=str(listing.source_job_id),
            title=title,
            company_name=company,
            description_html=description_html,
            description_text=description_text,
            employment_type=listing.employment_type or "Full-time",
            remote_scope="Anywhere",
            location_text=listing.location,
            category=listing.category or "Other",
            posted_at=str(listing.posted_date),
            apply_url_original=apply_url,
            apply_url_final=apply_url,
            canonical_url=listing.url,
        )
