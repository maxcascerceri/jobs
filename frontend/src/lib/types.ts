export interface Job {
  id: string;
  source: string;
  source_job_id: string;
  title: string;
  company_name: string;
  company_logo_url: string;
  company_domain: string;
  description_html: string;
  description_text: string;
  employment_type: string;
  remote_scope: string;
  location_text: string;
  category: string;
  experience_level: string;
  salary_min: number | null;
  salary_max: number | null;
  salary_currency: string;
  salary_period: string;
  salary_text: string;
  posted_at: string;
  apply_url_original: string;
  apply_url_final: string;
  canonical_url: string;
  status: string;
  tags: string;
  created_at: string;
  updated_at: string;
}

export interface JobsResponse {
  jobs: Job[];
  total: number;
  page: number;
  per_page: number;
  categories: string[];
  employment_types: string[];
}

export interface FilterState {
  search: string;
  category: string;
  employment_type: string;
  experience_level: string;
  page: number;
}
