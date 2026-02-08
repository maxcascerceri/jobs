import Database from "better-sqlite3";
import path from "path";

const DB_PATH = path.join(process.cwd(), "..", "jobs.db");

let db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!db) {
    db = new Database(DB_PATH, { readonly: true });
    db.pragma("journal_mode = WAL");
  }
  return db;
}

export function getJobs({
  search = "",
  category = "",
  employment_type = "",
  experience_level = "",
  page = 1,
  per_page = 30,
}: {
  search?: string;
  category?: string;
  employment_type?: string;
  experience_level?: string;
  page?: number;
  per_page?: number;
}) {
  const db = getDb();
  const conditions: string[] = ["status = 'active'"];
  const params: (string | number)[] = [];

  if (search) {
    conditions.push("(title LIKE ? OR company_name LIKE ? OR description_text LIKE ?)");
    const term = `%${search}%`;
    params.push(term, term, term);
  }

  if (category && category !== "All") {
    conditions.push("category = ?");
    params.push(category);
  }

  if (employment_type && employment_type !== "All") {
    conditions.push("employment_type = ?");
    params.push(employment_type);
  }

  if (experience_level && experience_level !== "All") {
    conditions.push("experience_level = ?");
    params.push(experience_level);
  }

  const where = conditions.length > 0 ? `WHERE ${conditions.join(" AND ")}` : "";
  const offset = (page - 1) * per_page;

  const total = db
    .prepare(`SELECT COUNT(*) as count FROM jobs ${where}`)
    .get(...params) as { count: number };

  const jobs = db
    .prepare(
      `SELECT * FROM jobs ${where} ORDER BY posted_at DESC, created_at DESC LIMIT ? OFFSET ?`
    )
    .all(...params, per_page, offset);

  // Get unique categories and types for filters
  const categories = db
    .prepare("SELECT DISTINCT category FROM jobs WHERE status = 'active' AND category IS NOT NULL AND category != '' ORDER BY category")
    .all()
    .map((r) => (r as { category: string }).category);

  const employment_types = db
    .prepare("SELECT DISTINCT employment_type FROM jobs WHERE status = 'active' AND employment_type IS NOT NULL AND employment_type != '' ORDER BY employment_type")
    .all()
    .map((r) => (r as { employment_type: string }).employment_type);

  return {
    jobs,
    total: total.count,
    page,
    per_page,
    categories,
    employment_types,
  };
}

export function getJobById(id: string) {
  const db = getDb();
  return db.prepare("SELECT * FROM jobs WHERE id = ?").get(id);
}
