"""
Configuration for the job board scraper.
"""
import os

# Database
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "jobs.db")

# Scraper settings
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # exponential backoff multiplier
RATE_LIMIT_SECONDS = 2  # seconds between requests per domain

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
]

# Sources
SOURCES = [
    "weworkremotely",
    "dynamitejobs",
    "jobicy",
    "workingnomads",
    "jobspresso",
    "himalayas",
    "remotesource",
]

# Category mapping — normalize categories across sources
CATEGORY_MAP = {
    # Programming
    "programming": "Engineering",
    "software development": "Engineering",
    "software engineering": "Engineering",
    "development": "Engineering",
    "developer": "Engineering",
    "developer / engineer": "Engineering",
    "engineering": "Engineering",
    "full-stack programming": "Engineering",
    "front-end programming": "Engineering",
    "back-end programming": "Engineering",
    "full stack": "Engineering",
    "frontend": "Engineering",
    "backend": "Engineering",
    "web development": "Engineering",
    # Design
    "design": "Design",
    "creative & design": "Design",
    "design & ux": "Design",
    "ui/ux": "Design",
    # Marketing
    "marketing": "Marketing",
    "sales and marketing": "Marketing",
    "marketing & sales": "Marketing",
    "sales": "Sales",
    "business development": "Sales",
    "business development & sales": "Sales",
    # Customer Support
    "customer support": "Support",
    "customer success": "Support",
    "customer service": "Support",
    # DevOps
    "devops and sysadmin": "DevOps",
    "devops & infrastructure": "DevOps",
    "devops": "DevOps",
    "sysadmin": "DevOps",
    "system administration": "DevOps",
    # Management
    "management and finance": "Management",
    "management": "Management",
    "management / operations": "Management",
    "product & operations": "Management",
    "product": "Product",
    "operations": "Management",
    # Data
    "data science & analytics": "Data",
    "data science": "Data",
    "data": "Data",
    "ai & data": "Data",
    # Writing
    "writing": "Writing",
    "content & editorial": "Writing",
    "writing & editing": "Writing",
    "content": "Writing",
    "copywriting": "Writing",
    # Finance
    "finance": "Finance",
    "finance & accounting": "Finance",
    "finance and accounting": "Finance",
    "accounting": "Finance",
    # HR
    "hr & recruiting": "HR",
    "human resources": "HR",
    "recruiting": "HR",
    # Other
    "all other remote": "Other",
    "other": "Other",
    "various": "Other",
    "consulting": "Other",
    "legal": "Other",
    "education": "Other",
    "healthcare": "Other",
    "admin": "Other",
    "admin / virtual assistant": "Other",
    "virtual assistant": "Other",
}

# Employment type normalization
EMPLOYMENT_TYPE_MAP = {
    "full-time": "Full-time",
    "full time": "Full-time",
    "fulltime": "Full-time",
    "ft": "Full-time",
    "part-time": "Part-time",
    "part time": "Part-time",
    "parttime": "Part-time",
    "pt": "Part-time",
    "contract": "Contract",
    "contractor": "Contract",
    "freelance": "Contract",
    "internship": "Internship",
    "intern": "Internship",
}
