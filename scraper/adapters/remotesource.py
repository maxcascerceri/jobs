"""
Remote Source adapter.
Site: https://www.remotesource.com/
"See more" to load more jobs requires login. With REMOTESOURCE_EMAIL/PASSWORD we log in
and click "See more" repeatedly; without credentials we only get the first ~5 public listings.
"""
import logging
import os
from urllib.parse import urljoin

from adapters.base import BaseAdapter, JobDetail, JobListing
from bs4 import BeautifulSoup
from headless import fetch_html, with_logged_in_session

logger = logging.getLogger(__name__)


class RemoteSourceAdapter(BaseAdapter):
    SOURCE_NAME = "remotesource"
    BASE_URL = "https://www.remotesource.com"
    USE_HEADLESS = True  # Next.js SPA — need browser to render

    def crawl_listings(self) -> list[JobListing]:
        email = os.environ.get("REMOTESOURCE_EMAIL", "").strip()
        password = os.environ.get("REMOTESOURCE_PASSWORD", "").strip()

        if email and password:
            # Log in so we can click "See more" and load many more jobs
            async def get_listings_page(page):
                await page.goto(self.BASE_URL, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(2000)
                see_more_texts = ["See more", "See more jobs", "Load more"]
                for _ in range(25):
                    clicked = False
                    for text in see_more_texts:
                        try:
                            for loc in [
                                page.get_by_role("button", name=text),
                                page.locator(f'button:has-text("{text}")'),
                                page.locator(f'a:has-text("{text}")'),
                            ]:
                                if await loc.count() > 0 and await loc.first.is_visible():
                                    await loc.first.click()
                                    await page.wait_for_timeout(2000)
                                    clicked = True
                                    break
                            if clicked:
                                break
                        except Exception:
                            pass
                    if not clicked:
                        break
                return await page.content()

            html = with_logged_in_session(
                self.BASE_URL, email, password, get_listings_page, timeout_ms=90000
            )
        else:
            html = fetch_html(self.BASE_URL, timeout_ms=45000)

        if not html:
            logger.warning("[remotesource] Failed to load homepage")
            return []

        soup = self.parse_html(html)
        seen_urls: set[str] = set()
        listings = []

        # Job links: <a class="w-full block" href="/jobs/SLUG-job-title-at-company">
        for a in soup.select('a[href^="/jobs/"]'):
            href = a.get("href", "")
            if not href or href == "/jobs" or len(href) <= 7:
                continue
            # Skip "Access All Jobs" or signup cards
            if "sign up" in a.get_text().lower() or "access all" in a.get_text().lower():
                continue

            job_url = urljoin(self.BASE_URL, href)
            slug = href.replace("/jobs/", "").strip()
            source_id = slug[:100] if slug else href

            title_el = a.select_one("h3")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title or len(title) < 3:
                continue

            # Company: <p class="text-black break-words">Circle K Stores</p> (first such p after the title area)
            company_el = a.select_one("p.text-black, .break-words p, p.break-words")
            company = company_el.get_text(strip=True) if company_el else ""

            # Category from badges: e.g. "Customer Success & Support", "Full-Time"
            badges = a.select("[class*='rounded-full'][class*='border']")
            category = ""
            employment_type = ""
            for span in badges:
                text = span.get_text(strip=True)
                if "full-time" in text.lower() or "part-time" in text.lower() or "contract" in text.lower():
                    employment_type = text
                elif not category and len(text) > 2 and "employees" not in text.lower() and "hq:" not in text.lower():
                    category = text

            if job_url in seen_urls:
                continue
            seen_urls.add(job_url)

            listings.append(JobListing(
                source=self.SOURCE_NAME,
                source_job_id=source_id[:100],
                url=job_url,
                title=title[:200],
                company=company,
                location="",
                category=self.normalize_category(category) if category else "Other",
                employment_type=self.normalize_employment_type(employment_type) if employment_type else "Full-time",
            ))

        logger.info(
            "[remotesource] Found %d listings (%s)",
            len(listings),
            "logged in + See more" if (email and password) else "public only",
        )
        return listings

    def crawl_detail(self, listing: JobListing) -> JobDetail | None:
        # Job detail pages are likely public too
        html = fetch_html(listing.url, timeout_ms=30000)
        if not html:
            return None

        soup = self.parse_html(html)
        title = listing.title
        company = listing.company

        h1 = soup.select_one("h1")
        if h1:
            title = h1.get_text(strip=True) or title

        company_el = soup.select_one("p.text-black, [class*='company'], .break-words p")
        if company_el:
            company = company_el.get_text(strip=True) or company

        desc_el = soup.select_one(
            "[class*='description'], .job-description, [class*='content'], .prose, article"
        )
        description_html = str(desc_el) if desc_el else ""
        description_text = desc_el.get_text(separator="\n", strip=True) if desc_el else ""

        apply_url = ""
        apply_el = soup.select_one("a[href*='apply'], a.apply, button.apply, a[href*='http']")
        if apply_el and apply_el.name == "a" and apply_el.get("href"):
            apply_url = apply_el.get("href", "")
        if apply_url and not apply_url.startswith("http"):
            apply_url = urljoin(self.BASE_URL, apply_url)

        salary_info = {"salary_min": None, "salary_max": None, "salary_currency": "USD", "salary_period": "yearly", "salary_text": ""}
        salary_el = soup.select_one("[class*='salary'], [class*='compensation']")
        if salary_el:
            salary_info = self.extract_salary(salary_el.get_text(strip=True))

        emp_type = listing.employment_type or "Full-time"
        type_el = soup.select_one("[class*='type'], [class*='employment']")
        if type_el:
            emp_type = self.normalize_employment_type(type_el.get_text(strip=True))

        return JobDetail(
            source=self.SOURCE_NAME,
            source_job_id=listing.source_job_id,
            title=title,
            company_name=company,
            description_html=description_html,
            description_text=description_text,
            employment_type=emp_type,
            remote_scope="Anywhere",
            location_text=listing.location,
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
