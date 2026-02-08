"""
Database layer — SQLite with the canonical job schema.
"""
import sqlite3
import uuid
from contextlib import contextmanager
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@contextmanager
def get_db():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Create tables if they don't exist."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                source_job_id TEXT,
                title TEXT NOT NULL,
                company_name TEXT,
                company_logo_url TEXT,
                company_domain TEXT,
                description_html TEXT,
                description_text TEXT,
                employment_type TEXT DEFAULT 'Full-time',
                remote_scope TEXT DEFAULT 'Anywhere',
                location_text TEXT,
                category TEXT,
                experience_level TEXT,
                salary_min INTEGER,
                salary_max INTEGER,
                salary_currency TEXT DEFAULT 'USD',
                salary_period TEXT DEFAULT 'yearly',
                salary_text TEXT,
                posted_at TEXT,
                apply_url_original TEXT,
                apply_url_final TEXT,
                canonical_url TEXT,
                status TEXT DEFAULT 'active',
                fingerprint_hash TEXT,
                tags TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                last_checked_at TEXT DEFAULT (datetime('now')),
                UNIQUE(source, source_job_id)
            );

            CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
            CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);
            CREATE INDEX IF NOT EXISTS idx_jobs_fingerprint ON jobs(fingerprint_hash);
            CREATE INDEX IF NOT EXISTS idx_jobs_posted_at ON jobs(posted_at DESC);
            CREATE INDEX IF NOT EXISTS idx_jobs_category ON jobs(category);
            CREATE INDEX IF NOT EXISTS idx_jobs_employment_type ON jobs(employment_type);

            CREATE TABLE IF NOT EXISTS job_groups (
                id TEXT PRIMARY KEY,
                primary_job_id TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (primary_job_id) REFERENCES jobs(id)
            );

            CREATE TABLE IF NOT EXISTS job_group_members (
                group_id TEXT NOT NULL,
                job_id TEXT NOT NULL,
                PRIMARY KEY (group_id, job_id),
                FOREIGN KEY (group_id) REFERENCES job_groups(id),
                FOREIGN KEY (job_id) REFERENCES jobs(id)
            );

            CREATE TABLE IF NOT EXISTS crawl_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                stage TEXT NOT NULL,
                jobs_found INTEGER DEFAULT 0,
                jobs_new INTEGER DEFAULT 0,
                jobs_updated INTEGER DEFAULT 0,
                errors INTEGER DEFAULT 0,
                started_at TEXT DEFAULT (datetime('now')),
                finished_at TEXT,
                status TEXT DEFAULT 'running',
                error_message TEXT
            );
        """)


def gen_id():
    return str(uuid.uuid4())


def upsert_job(conn, job_data: dict) -> str:
    """Insert or update a job. Returns the job ID."""
    job_id = job_data.get("id") or gen_id()

    # Check if job exists by source + source_job_id
    existing = conn.execute(
        "SELECT id FROM jobs WHERE source = ? AND source_job_id = ?",
        (job_data.get("source"), job_data.get("source_job_id")),
    ).fetchone()

    if existing:
        job_id = existing["id"]
        fields = []
        values = []
        for key in [
            "title", "company_name", "company_logo_url", "company_domain",
            "description_html", "description_text", "employment_type",
            "remote_scope", "location_text", "category", "experience_level",
            "salary_min", "salary_max", "salary_currency", "salary_period",
            "salary_text", "posted_at", "apply_url_original", "apply_url_final",
            "canonical_url", "status", "fingerprint_hash", "tags",
        ]:
            if key in job_data and job_data[key] is not None:
                fields.append(f"{key} = ?")
                values.append(job_data[key])

        if fields:
            fields.append("updated_at = datetime('now')")
            fields.append("last_checked_at = datetime('now')")
            values.append(job_id)
            conn.execute(
                f"UPDATE jobs SET {', '.join(fields)} WHERE id = ?",
                values,
            )
        return job_id

    # Insert new
    job_data["id"] = job_id
    columns = []
    placeholders = []
    values = []
    for key, val in job_data.items():
        if val is not None:
            columns.append(key)
            placeholders.append("?")
            values.append(val)

    conn.execute(
        f"INSERT INTO jobs ({', '.join(columns)}) VALUES ({', '.join(placeholders)})",
        values,
    )
    return job_id


def check_duplicate_fingerprint(conn, fingerprint: str, exclude_id: str = None) -> dict | None:
    """Check if a job with this fingerprint already exists."""
    if exclude_id:
        row = conn.execute(
            "SELECT id, source FROM jobs WHERE fingerprint_hash = ? AND id != ? AND status = 'active'",
            (fingerprint, exclude_id),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT id, source FROM jobs WHERE fingerprint_hash = ? AND status = 'active'",
            (fingerprint,),
        ).fetchone()
    return dict(row) if row else None


def check_duplicate_apply_url(conn, apply_url: str, exclude_id: str = None) -> dict | None:
    """Check if a job with this apply URL already exists."""
    if not apply_url:
        return None
    if exclude_id:
        row = conn.execute(
            "SELECT id, source FROM jobs WHERE apply_url_final = ? AND id != ? AND status = 'active'",
            (apply_url, exclude_id),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT id, source FROM jobs WHERE apply_url_final = ? AND status = 'active'",
            (apply_url,),
        ).fetchone()
    return dict(row) if row else None


def log_crawl(conn, source: str, stage: str) -> int:
    """Start a crawl log entry. Returns the log ID."""
    cursor = conn.execute(
        "INSERT INTO crawl_log (source, stage) VALUES (?, ?)",
        (source, stage),
    )
    return cursor.lastrowid


def finish_crawl(conn, log_id: int, jobs_found=0, jobs_new=0, jobs_updated=0, errors=0, error_message=None):
    """Finish a crawl log entry."""
    status = "error" if error_message else "completed"
    conn.execute(
        """UPDATE crawl_log
           SET jobs_found=?, jobs_new=?, jobs_updated=?, errors=?,
               finished_at=datetime('now'), status=?, error_message=?
           WHERE id=?""",
        (jobs_found, jobs_new, jobs_updated, errors, status, error_message, log_id),
    )


if __name__ == "__main__":
    init_db()
    print(f"Database initialized at {DB_PATH}")
