"""
Jobspresso adapter.
Site: https://jobspresso.co
"""
import logging
from urllib.parse import urljoin

from adapters.base import BaseAdapter, JobDetail, JobListing

logger = logging.getLogger(__name__)

CATEGORY_PAGES = [
    "/remote-work/",
    "/remote-work-ai-data/",
    "/remote-work-developer/",
    "/remote-work-design/",
    "/remote-work-customer-support/",
    "/remote-work-marketing/",
    "/remote-work-sales/",
    "/remote-work-writing/",
    "/remote-work-product-management/",
]


class JobspressoAdapter(BaseAdapter):
    SOURCE_NAME = "jobspresso"
    BASE_URL = "https://jobspresso.co"
    USE_HEADLESS = True  # May block simple HTTP

    def crawl_listings(self) -> list[JobListing]:
        listings = []

        for page_path in CATEGORY_PAGES:
            url = f"{self.BASE_URL}{page_path}"
            resp = self.fetch(url)
            if not resp:
                continue

            soup = self.parse_html(resp.text)

            # Jobspresso uses a job listing format
            job_cards = soup.select("div.job_listing, article.job_listing, li.job_listing")
            if not job_cards:
                # Broader selectors
                job_cards = soup.select("a[href*='jobspresso.co/job/']")

            for card in job_cards:
                # Get the link
                if card.name == "a":
                    link = card
                else:
                    link = card.select_one("a[href*='/job/']")

                if not link:
                    continue

                href = link.get("href", "")
                if not href or "/job/" not in href:
                    continue

                job_url = href if href.startswith("http") else urljoin(self.BASE_URL, href)
                source_job_id = href.rstrip("/").split("/")[-1]

                # Title
                title_el = card.select_one("h3, h4, .position, .job-title") if card.name != "a" else None
                title = title_el.get_text(strip=True) if title_el else link.get_text(strip=True)

                # Company
                company = ""
                company_el = card.select_one(".company, .job-company") if card.name != "a" else None
                if company_el:
                    company = company_el.get_text(strip=True)

                # Location
                location = ""
                loc_el = card.select_one(".location, .job-location") if card.name != "a" else None
                if loc_el:
                    location = loc_el.get_text(strip=True)

                if not title or len(title) < 3:
                    continue

                # Derive category from page path
                cat_map = {
                    "ai-data": "Data",
                    "developer": "Engineering",
                    "design": "Design",
                    "customer-support": "Support",
                    "marketing": "Marketing",
                    "sales": "Sales",
                    "writing": "Writing",
                    "product-management": "Product",
                }
                category = "Other"
                for key, val in cat_map.items():
                    if key in page_path:
                        category = val
                        break

                listings.append(JobListing(
                    source=self.SOURCE_NAME,
                    source_job_id=source_job_id,
                    url=job_url,
                    title=self.clean_text(title),
                    company=company,
                    location=location,
                    category=category,
                ))

            logger.info(f"[{self.SOURCE_NAME}] Crawled {page_path}")

        # Deduplicate
        seen = set()
        unique = []
        for l in listings:
            if l.url not in seen:
                seen.add(l.url)
                unique.append(l)

        logger.info(f"[{self.SOURCE_NAME}] Total unique listings: {len(unique)}")
        return unique

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
        company_el = soup.select_one(".company-name, .job-company, h2 a")
        if company_el:
            company = company_el.get_text(strip=True) or company

        logo_url = ""
        logo_el = soup.select_one("img.company_logo, img[class*='logo']")
        if logo_el:
            src = logo_el.get("src", "")
            logo_url = src if src.startswith("http") else urljoin(self.BASE_URL, src)

        desc_el = soup.select_one("div.job_description, div.job-description, div.entry-content")
        description_html = str(desc_el) if desc_el else ""
        description_text = desc_el.get_text(separator="\n", strip=True) if desc_el else ""

        apply_url = ""
        apply_el = soup.select_one("a.apply_button, a[href*='apply'], a[class*='apply']")
        if apply_el:
            apply_url = apply_el.get("href", "")
            if apply_url and not apply_url.startswith("http"):
                apply_url = urljoin(self.BASE_URL, apply_url)

        # Salary
        salary_info = {"salary_min": None, "salary_max": None, "salary_currency": "USD", "salary_period": "yearly", "salary_text": ""}
        salary_el = soup.select_one(".salary, .job-salary, [class*='salary']")
        if salary_el:
            salary_info = self.extract_salary(salary_el.get_text(strip=True))

        emp_type = listing.employment_type or "Full-time"
        type_el = soup.select_one(".job-type, .employment-type")
        if type_el:
            emp_type = self.normalize_employment_type(type_el.get_text(strip=True))

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
            location_text=listing.location,
            category=listing.category,
            salary_min=salary_info["salary_min"],
            salary_max=salary_info["salary_max"],
            salary_currency=salary_info["salary_currency"],
            salary_period=salary_info["salary_period"],
            salary_text=salary_info["salary_text"],
            apply_url_original=apply_url,
            apply_url_final=apply_url,
            canonical_url=listing.url,
        )
