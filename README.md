# RemoteHQ — Remote Jobs That Don't Suck

A sleek, modern remote job board that aggregates listings from the best remote-first job boards. Built with a robust scraping pipeline and a clean Next.js frontend.

## Architecture

```
Jobs/
├── scraper/           # Python scraping engine
│   ├── adapters/      # One adapter per source (6 sources)
│   │   ├── base.py             # Base adapter with shared logic
│   │   ├── himalayas.py        # himalayas.app (API)
│   │   ├── jobicy.py           # jobicy.com (API)
│   │   ├── workingnomads.py    # workingnomads.com (API)
│   │   ├── weworkremotely.py   # weworkremotely.com (HTML)
│   │   ├── dynamitejobs.py     # dynamitejobs.com (HTML)
│   │   └── jobspresso.py       # jobspresso.co (HTML)
│   ├── pipeline/      # Processing pipeline
│   │   ├── normalizer.py       # Normalize data to canonical schema
│   │   ├── deduper.py          # 3-layer deduplication
│   │   └── quality.py          # Quality gates
│   ├── config.py      # Configuration
│   ├── db.py          # SQLite database layer
│   ├── main.py        # CLI runner
│   └── requirements.txt
├── frontend/          # Next.js 16 + Tailwind CSS
│   └── src/
│       ├── app/
│       │   ├── page.tsx                 # Main job board page
│       │   ├── jobs/[id]/page.tsx       # Job detail page
│       │   └── api/jobs/route.ts        # API route
│       ├── components/
│       │   ├── Header.tsx
│       │   ├── SearchBar.tsx
│       │   ├── FilterBar.tsx
│       │   ├── JobCard.tsx
│       │   └── JobList.tsx
│       └── lib/
│           ├── db.ts          # SQLite reader
│           ├── types.ts       # TypeScript types
│           └── utils.ts       # Formatting helpers
└── jobs.db            # Shared SQLite database
```

## Scraper Design

### Two-Stage Crawl Pipeline

**Stage A — Listings Crawl**: Discovers job URLs + minimal metadata from each source.

**Stage B — Detail Crawl**: Fetches full job data from each listing page.

### Source Adapters

Each source has its own adapter that handles the unique structure of that site:

| Source | Method | Status |
|--------|--------|--------|
| Himalayas | JSON API | Working |
| Jobicy | JSON API | Working |
| Working Nomads | JSON API | Working |
| We Work Remotely | HTML + Playwright | Working (with headless) |
| Dynamite Jobs | HTML + Playwright | Working (with headless) |
| Jobspresso | HTML + Playwright | Working (with headless) |
| **Remote Source** | HTML + Playwright + login | Requires env credentials |

API-based sources work with plain `requests`. WWR, Dynamite Jobs, and Jobspresso block simple HTTP (403); for those, the scraper automatically uses a **Playwright** headless browser when you install it (see below). **Remote Source** (24k+ jobs) requires login; set `REMOTESOURCE_EMAIL` and `REMOTESOURCE_PASSWORD` (see below).

### Deduplication (3 Layers)

1. **URL + source_job_id** — Exact duplicates within a source
2. **Content fingerprint** — Hash of normalized title + company + description
3. **Apply URL matching** — Same ATS/apply page = same job

### Quality Gates

Jobs are rejected if they have:
- Missing or too-short title (< 5 chars)
- Missing company name
- Description shorter than 50 characters
- No apply URL or canonical URL
- Spam-like title content

## Headless browser (Playwright) — optional

Sources that block simple HTTP (WeWorkRemotely, Dynamite Jobs, Jobspresso) use **Playwright** so the scraper runs a real headless Chromium browser. You only need this if you want to scrape those three sites.

### Setup (one-time)

```bash
cd scraper
pip3 install playwright
# Important: use Python’s Playwright to install the browser (not Node’s)
python3 -m playwright install chromium
```

That’s it. No API keys. The adapters for WWR, Dynamite Jobs, and Jobspresso have `USE_HEADLESS = True`; when a request gets **403**, the scraper automatically retries that URL with the headless browser and returns the page HTML.

**Troubleshooting:** If you see `Executable doesn't exist at .../chrome-headless-shell`, the browser wasn’t installed for this Python. Run `python3 -m playwright install chromium` in your terminal (same Python you use for the scraper). Don’t use `playwright install` from Node — that installs to a different path.

### Remote Source (login required)

[Remote Source](https://www.remotesource.com/) has 24k+ jobs but requires an account. The scraper logs in via the headless browser using env vars — **never put your password in code**.

1. Copy the example env file and add your credentials:
   ```bash
   cd scraper
   cp .env.example .env
   # Edit .env and set:
   # REMOTESOURCE_EMAIL=your@email.com
   # REMOTESOURCE_PASSWORD=your_password
   ```
2. `.env` is in `.gitignore` — don’t commit it.
3. Run the scraper (Remote Source is included when you run all sources):
   ```bash
   python3 main.py --source remotesource --max-details 50
   ```

If the site’s HTML structure changes, the adapter may need selector updates (job list links, login form fields).

### Cost

| Item | Cost |
|------|------|
| **Playwright** | Free (open source) |
| **Chromium** | Free (`playwright install chromium`) |
| **Running on your machine** | Free |
| **Running on a VPS** (e.g. cron every hour) | ~$5–12/mo (e.g. DigitalOcean $6 droplet) |
| **Managed “browser in the cloud”** (optional) | Paid per page, e.g. [Browserless](https://www.browserless.io/) or [ScrapingBee](https://www.scrapingbee.com/) — only if you don’t want to run Chromium yourself |

**Summary:** $0 for the stack. If you run the scraper on your own laptop or a small VPS, the only cost is the VPS (optional). No per-request or per-page fees unless you choose a managed browser service.

---

## Quick Start

### 1. Install Dependencies

```bash
# Scraper
cd scraper
pip3 install -r requirements.txt

# Optional: for WeWorkRemotely, Dynamite Jobs, Jobspresso (headless browser)
playwright install chromium

# Frontend
cd ../frontend
npm install
```

### 2. Initialize Database & Scrape Jobs

```bash
cd scraper

# Initialize the database
python3 main.py --init-db

# Scrape all sources
python3 main.py

# Or scrape a specific source
python3 main.py --source himalayas --max-details 100
python3 main.py --source jobicy --max-details 100
```

### 3. Run the Frontend

```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Scraper CLI

```bash
# Scrape all sources (default 50 details per source)
python3 main.py

# Scrape specific source
python3 main.py --source himalayas

# Control detail limit
python3 main.py --max-details 100

# Just initialize database
python3 main.py --init-db
```

Available sources: `weworkremotely`, `dynamitejobs`, `jobicy`, `workingnomads`, `jobspresso`, `himalayas`, `remotesource` (remotesource requires `REMOTESOURCE_EMAIL` and `REMOTESOURCE_PASSWORD` in `.env`)

## Tech Stack

- **Frontend**: Next.js 16, TypeScript, Tailwind CSS
- **Backend**: Python 3, BeautifulSoup, Requests
- **Database**: SQLite (shared between scraper and frontend)
- **Fonts**: Geist Sans + Geist Mono

## Scheduled scraping (no local runs)

The scraper can run **in the cloud on a schedule** so you never have to run it on your own terminal.

### GitHub Actions (recommended)

1. **Push this repo to GitHub** (if it’s not already):
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

2. **Add secrets** for Remote Source login (so “See more” can load 1000+ jobs):
   - Repo → **Settings** → **Secrets and variables** → **Actions**
   - **New repository secret** → name: `REMOTESOURCE_EMAIL`, value: your Remote Source email
   - **New repository secret** → name: `REMOTESOURCE_PASSWORD`, value: your Remote Source password

3. **Automatic runs**
   - The workflow [`.github/workflows/scrape.yml`](.github/workflows/scrape.yml) runs **daily at 12:00 UTC** (e.g. 7:00 AM Eastern).
   - It installs Python, Playwright, Chromium, runs the Remote Source scraper, then **commits and pushes** the updated `jobs.db` to the repo.
   - You don’t run anything locally; the scraper runs on GitHub’s servers.

4. **Manual run**
   - Repo → **Actions** → **Scrape jobs** → **Run workflow**.

5. **Using the updated data**
   - After each run, `jobs.db` in the repo is updated. If your frontend is deployed (e.g. Vercel) and reads `jobs.db` from the repo at build time, redeploy or trigger a rebuild to get the latest jobs. For “live” updates without redeploy, you’d add an API that serves the DB or switch to a hosted DB (e.g. Supabase).

---

## Next Steps for Production

1. ~~Set up cron jobs~~ → Use the GitHub Actions workflow above.
2. **Add expired job detection** — mark jobs as expired when detail pages 404
3. **Add email alerts** for new jobs matching user preferences
4. **Deploy** — Vercel for frontend; `jobs.db` is updated in the repo by the workflow
