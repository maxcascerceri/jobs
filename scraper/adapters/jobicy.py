"""
Jobicy adapter.
Site: https://jobicy.com
Uses their public REST API for listings.
"""
import logging
from urllib.parse import urljoin

from adapters.base import BaseAdapter, JobDetail, JobListing

logger = logging.getLogger(__name__)


class JobicyAdapter(BaseAdapter):
    SOURCE_NAME = "jobicy"
    BASE_URL = "https://jobicy.com"
    API_URL = "https://jobicy.com/api/v2/remote-jobs"

    def crawl_listings(self) -> list[JobListing]:
        listings = []

        # Jobicy has a public API (max count per request)
        params = {"count": 50}
        data = self.fetch_json(self.API_URL, params=params)

        if data and "jobs" in data:
            for job in data["jobs"]:
                source_job_id = str(job.get("id", ""))
                job_url = job.get("url", "")
                title = job.get("jobTitle", "")
                company = job.get("companyName", "")
                location = job.get("jobGeo", "Anywhere")
                category = job.get("jobIndustry", ["Other"])
                emp_type = job.get("jobType", "Full-time")
                posted = job.get("pubDate", "")
                job_level = job.get("jobLevel", "")

                if isinstance(category, list):
                    category = category[0] if category else "Other"

                if not title or not job_url:
                    continue

                listing = JobListing(
                    source=self.SOURCE_NAME,
                    source_job_id=source_job_id,
                    url=job_url,
                    title=title,
                    company=company,
                    location=location if isinstance(location, str) else "Anywhere",
                    category=self.normalize_category(category),
                    employment_type=self.normalize_employment_type(emp_type),
                    posted_date=posted,
                )
                # Store full API data for detail phase
                listing._extra = {
                    "description": job.get("jobDescription", ""),
                    "companyLogo": job.get("companyLogo", ""),
                    "url": job_url,
                    "job_level": job_level,
                    "salary_min": job.get("salaryMin"),
                    "salary_max": job.get("salaryMax"),
                    "salary_currency": job.get("salaryCurrency", "USD"),
                    "salary_period": job.get("salaryPeriod", "yearly"),
                }
                listings.append(listing)

        logger.info(f"[{self.SOURCE_NAME}] Found {len(listings)} listings from API")

        # Also try HTML fallback for more jobs
        for page in range(1, 4):
            resp = self.fetch(f"{self.BASE_URL}/jobs?page={page}")
            if not resp:
                break

            soup = self.parse_html(resp.text)
            job_cards = soup.select("article a[href*='/jobs/'], div.job-card a[href*='/jobs/']")

            for card in job_cards:
                href = card.get("href", "")
                if not href or "/jobs/" not in href:
                    continue
                job_url = urljoin(self.BASE_URL, href)
                source_id = href.rstrip("/").split("/")[-1]

                title_el = card.select_one("h2, h3, .job-title")
                title = title_el.get_text(strip=True) if title_el else ""

                if not title:
                    continue

                listings.append(JobListing(
                    source=self.SOURCE_NAME,
                    source_job_id=source_id,
                    url=job_url,
                    title=title,
                ))

        # Deduplicate
        seen = set()
        unique = []
        for l in listings:
            key = l.source_job_id or l.url
            if key not in seen:
                seen.add(key)
                unique.append(l)
        return unique

    def crawl_detail(self, listing: JobListing) -> JobDetail | None:
        extra = getattr(listing, "_extra", {})

        # If we have API data, use it directly
        if extra.get("description"):
            description = str(extra["description"])
            description_text = self.parse_html(description).get_text(separator="\n", strip=True) if "<" in description else description
            apply_url = str(extra.get("url", listing.url))
            logo = str(extra.get("companyLogo", ""))

            salary_min = extra.get("salary_min")
            salary_max = extra.get("salary_max")
            salary_currency = str(extra.get("salary_currency", "USD"))
            salary_period = str(extra.get("salary_period", "yearly"))
            salary_text = ""
            if salary_min or salary_max:
                parts = []
                if salary_min:
                    parts.append(f"${int(salary_min):,}")
                if salary_max:
                    parts.append(f"${int(salary_max):,}")
                salary_text = f"{' - '.join(parts)}/{salary_period} ({salary_currency})"

            return JobDetail(
                source=self.SOURCE_NAME,
                source_job_id=str(listing.source_job_id),
                title=listing.title,
                company_name=listing.company,
                company_logo_url=logo,
                description_html=description,
                description_text=description_text,
                employment_type=listing.employment_type or "Full-time",
                remote_scope="Anywhere",
                location_text=listing.location,
                category=listing.category or "Other",
                experience_level=str(extra.get("job_level", "")),
                salary_min=int(salary_min) if salary_min else None,
                salary_max=int(salary_max) if salary_max else None,
                salary_currency=salary_currency,
                salary_period=salary_period,
                salary_text=salary_text,
                posted_at=str(listing.posted_date),
                apply_url_original=apply_url,
                apply_url_final=apply_url,
                canonical_url=listing.url,
            )

        # Fallback: scrape detail page
        resp = self.fetch(listing.url)
        if not resp:
            return None

        soup = self.parse_html(resp.text)

        title = listing.title
        h1 = soup.select_one("h1")
        if h1:
            title = h1.get_text(strip=True) or title

        company = listing.company
        company_el = soup.select_one("a[href*='/company/'], .company-name")
        if company_el:
            company = company_el.get_text(strip=True) or company

        logo_url = ""
        logo_el = soup.select_one("img[class*='logo'], img[src*='logo']")
        if logo_el:
            logo_url = logo_el.get("src", "")

        desc_el = soup.select_one("div.job-description, div.job-content, article")
        description_html = str(desc_el) if desc_el else ""
        description_text = desc_el.get_text(separator="\n", strip=True) if desc_el else ""

        apply_url = ""
        apply_el = soup.select_one("a[href*='apply'], a.apply-btn, a[class*='apply']")
        if apply_el:
            apply_url = apply_el.get("href", "")
            if apply_url and not apply_url.startswith("http"):
                apply_url = urljoin(self.BASE_URL, apply_url)

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
