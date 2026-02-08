"""
Main scraper runner — orchestrates the two-stage crawl pipeline.
"""
import argparse
import logging
import os
import sys
import time
from dataclasses import asdict

# Load .env so REMOTESOURCE_EMAIL / REMOTESOURCE_PASSWORD are available (from scraper dir, any cwd)
try:
    from dotenv import load_dotenv
    _env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".env"))
    load_dotenv(_env_path)
except ImportError:
    pass

from adapters import ALL_ADAPTERS
from db import finish_crawl, get_db, init_db, log_crawl, upsert_job
from pipeline.deduper import check_duplicate
from pipeline.normalizer import normalize_job
from pipeline.quality import passes_quality

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def run_source(adapter_class, max_details: int = 100):
    """Run the full two-stage pipeline for a single source."""
    adapter = adapter_class()
    source = adapter.name
    logger.info(f"{'='*60}")
    logger.info(f"Starting crawl for: {source}")
    logger.info(f"{'='*60}")

    stats = {
        "listings_found": 0,
        "details_fetched": 0,
        "jobs_new": 0,
        "jobs_updated": 0,
        "duplicates": 0,
        "quality_rejected": 0,
        "errors": 0,
    }

    with get_db() as conn:
        crawl_id = log_crawl(conn, source, "full")

        try:
            # Stage A: Listings crawl
            logger.info(f"[{source}] Stage A: Discovering listings...")
            listings = adapter.crawl_listings()
            stats["listings_found"] = len(listings)
            logger.info(f"[{source}] Found {len(listings)} listings")

            if not listings:
                logger.warning(f"[{source}] No listings found! Possible site change.")
                finish_crawl(conn, crawl_id, error_message="No listings found")
                return stats

            # Stage B: Detail crawl (limit for sanity)
            detail_count = min(len(listings), max_details)
            logger.info(f"[{source}] Stage B: Fetching details for {detail_count} jobs...")

            for i, listing in enumerate(listings[:detail_count]):
                try:
                    detail = adapter.crawl_detail(listing)
                    if not detail:
                        stats["errors"] += 1
                        continue

                    stats["details_fetched"] += 1

                    # Normalize
                    job_data = normalize_job(detail)

                    # Quality check
                    passes, reason = passes_quality(job_data)
                    if not passes:
                        stats["quality_rejected"] += 1
                        logger.debug(f"[{source}] Quality rejected: {reason} — {listing.title}")
                        continue

                    # Dedupe check
                    dup = check_duplicate(conn, job_data)
                    if dup:
                        stats["duplicates"] += 1
                        continue

                    # Check if this is an update or new
                    existing = conn.execute(
                        "SELECT id FROM jobs WHERE source = ? AND source_job_id = ?",
                        (source, listing.source_job_id),
                    ).fetchone()

                    # Upsert
                    upsert_job(conn, job_data)

                    if existing:
                        stats["jobs_updated"] += 1
                    else:
                        stats["jobs_new"] += 1

                    if (i + 1) % 10 == 0:
                        logger.info(f"[{source}] Progress: {i+1}/{detail_count}")

                except Exception as e:
                    stats["errors"] += 1
                    logger.error(f"[{source}] Error processing {listing.url}: {e}")

            # Finish crawl log
            finish_crawl(
                conn, crawl_id,
                jobs_found=stats["listings_found"],
                jobs_new=stats["jobs_new"],
                jobs_updated=stats["jobs_updated"],
                errors=stats["errors"],
            )

        except Exception as e:
            logger.error(f"[{source}] Fatal error: {e}")
            finish_crawl(conn, crawl_id, error_message=str(e))
            stats["errors"] += 1

    logger.info(f"[{source}] Results: {stats}")
    return stats


def run_all(max_details: int = 50):
    """Run all source adapters."""
    logger.info("Starting full crawl of all sources...")
    start = time.time()
    all_stats = {}

    for adapter_class in ALL_ADAPTERS:
        try:
            stats = run_source(adapter_class, max_details=max_details)
            all_stats[adapter_class.SOURCE_NAME] = stats
        except Exception as e:
            logger.error(f"Failed to run {adapter_class.SOURCE_NAME}: {e}")
            all_stats[adapter_class.SOURCE_NAME] = {"error": str(e)}

    elapsed = time.time() - start
    logger.info(f"\n{'='*60}")
    logger.info(f"CRAWL COMPLETE in {elapsed:.1f}s")
    logger.info(f"{'='*60}")

    total_new = sum(s.get("jobs_new", 0) for s in all_stats.values())
    total_found = sum(s.get("listings_found", 0) for s in all_stats.values())
    logger.info(f"Total listings found: {total_found}")
    logger.info(f"Total new jobs: {total_new}")

    for source, stats in all_stats.items():
        logger.info(f"  {source}: {stats}")

    return all_stats


def main():
    parser = argparse.ArgumentParser(description="Remote Job Board Scraper")
    parser.add_argument(
        "--source",
        choices=[a.SOURCE_NAME for a in ALL_ADAPTERS],
        help="Run only a specific source adapter",
    )
    parser.add_argument(
        "--max-details",
        type=int,
        default=50,
        help="Max number of detail pages to fetch per source (default: 50)",
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize/reset the database",
    )
    args = parser.parse_args()

    # Always ensure DB exists
    init_db()

    if args.init_db:
        logger.info("Database initialized.")
        return

    if args.source:
        adapter_map = {a.SOURCE_NAME: a for a in ALL_ADAPTERS}
        run_source(adapter_map[args.source], max_details=args.max_details)
    else:
        run_all(max_details=args.max_details)


if __name__ == "__main__":
    main()
