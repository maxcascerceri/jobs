"use client";

import Link from "next/link";
import { Job } from "@/lib/types";
import { formatSalary, getCategoryColor, getSourceLabel, timeAgo } from "@/lib/utils";

interface JobDetailClientProps {
  job: Job;
}

export default function JobDetailClient({ job }: JobDetailClientProps) {
  const salary = formatSalary(job);
  const posted = timeAgo(job.posted_at);
  const categoryStyle = getCategoryColor(job.category);
  const applyUrl = job.apply_url_final || job.apply_url_original || job.canonical_url;

  return (
    <main className="mx-auto max-w-4xl px-4 sm:px-6 pb-20">
      {/* Back link */}
      <div className="pt-6 pb-4">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M19 12H5" />
            <path d="M12 19l-7-7 7-7" />
          </svg>
          All jobs
        </Link>
      </div>

      {/* Job header */}
      <div className="rounded-2xl border border-border bg-card p-6 sm:p-8">
        <div className="flex items-start gap-5">
          {/* Company logo */}
          <div className="hidden sm:flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-muted border border-border overflow-hidden">
            {job.company_logo_url ? (
              <img
                src={job.company_logo_url}
                alt={job.company_name}
                className="h-full w-full object-contain p-1.5"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = "none";
                  (e.target as HTMLImageElement).parentElement!.innerHTML = `<span class="text-lg font-bold text-muted-foreground">${(job.company_name || "?")[0].toUpperCase()}</span>`;
                }}
              />
            ) : (
              <span className="text-lg font-bold text-muted-foreground">
                {(job.company_name || "?")[0].toUpperCase()}
              </span>
            )}
          </div>

          <div className="flex-1 min-w-0">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-foreground leading-tight">
              {job.title}
            </h1>
            <p className="mt-1.5 text-base text-muted-foreground">
              {job.company_name}
            </p>

            {/* Meta row */}
            <div className="mt-4 flex flex-wrap items-center gap-2">
              {job.category && (
                <span className={`inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-medium ${categoryStyle}`}>
                  {job.category}
                </span>
              )}
              {job.employment_type && (
                <span className="inline-flex items-center rounded-md border border-border bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
                  {job.employment_type}
                </span>
              )}
              {job.experience_level && (
                <span className="inline-flex items-center rounded-md border border-border bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground">
                  {job.experience_level}
                </span>
              )}
              {salary && (
                <span className="inline-flex items-center rounded-md border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-medium text-emerald-700">
                  {salary}
                </span>
              )}
            </div>

            {/* Info grid */}
            <div className="mt-4 flex flex-wrap gap-x-6 gap-y-2 text-sm text-muted-foreground">
              {job.location_text && (
                <div className="flex items-center gap-1.5">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z" />
                    <circle cx="12" cy="10" r="3" />
                  </svg>
                  {job.location_text}
                </div>
              )}
              {job.remote_scope && (
                <div className="flex items-center gap-1.5">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <path d="M2 12h20" />
                    <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                  </svg>
                  Remote &mdash; {job.remote_scope}
                </div>
              )}
              {posted && (
                <div className="flex items-center gap-1.5">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <circle cx="12" cy="12" r="10" />
                    <polyline points="12 6 12 12 16 14" />
                  </svg>
                  Posted {posted}
                </div>
              )}
              <div className="flex items-center gap-1.5">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
                  <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
                </svg>
                via {getSourceLabel(job.source)}
              </div>
            </div>
          </div>
        </div>

        {/* Apply CTA */}
        {applyUrl && (
          <div className="mt-6 flex flex-col sm:flex-row gap-3">
            <a
              href={applyUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 rounded-xl bg-accent px-6 py-2.5 text-sm font-semibold text-accent-foreground shadow-sm transition-all hover:opacity-90 hover:shadow-md active:scale-[0.98]"
            >
              Apply Now
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M7 17L17 7" />
                <path d="M7 7h10v10" />
              </svg>
            </a>
            {job.canonical_url && job.canonical_url !== applyUrl && (
              <a
                href={job.canonical_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-border bg-card px-6 py-2.5 text-sm font-medium text-foreground transition-all hover:bg-muted"
              >
                View Original
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                  <polyline points="15 3 21 3 21 9" />
                  <line x1="10" y1="14" x2="21" y2="3" />
                </svg>
              </a>
            )}
          </div>
        )}
      </div>

      {/* Job description */}
      {(job.description_html || job.description_text) && (
        <div className="mt-4 rounded-2xl border border-border bg-card p-6 sm:p-8">
          <h2 className="mb-4 text-lg font-semibold text-foreground">
            About This Role
          </h2>
          {job.description_html ? (
            <div
              className="job-description text-[15px] leading-relaxed text-card-foreground"
              dangerouslySetInnerHTML={{ __html: job.description_html }}
            />
          ) : (
            <div className="job-description text-[15px] leading-relaxed text-card-foreground whitespace-pre-line">
              {job.description_text}
            </div>
          )}
        </div>
      )}

      {/* Tags */}
      {job.tags && (
        <div className="mt-4 rounded-2xl border border-border bg-card p-6 sm:p-8">
          <h2 className="mb-3 text-sm font-semibold text-foreground">Tags</h2>
          <div className="flex flex-wrap gap-2">
            {job.tags.split(",").filter(Boolean).map((tag) => (
              <span
                key={tag}
                className="rounded-md bg-muted px-2.5 py-1 text-xs text-muted-foreground"
              >
                {tag.trim()}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Sticky bottom apply bar */}
      {applyUrl && (
        <div className="fixed bottom-0 left-0 right-0 z-40 border-t border-border bg-card/95 backdrop-blur-lg sm:hidden">
          <div className="mx-auto flex max-w-4xl items-center justify-between gap-3 px-4 py-3">
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-foreground">{job.title}</p>
              <p className="truncate text-xs text-muted-foreground">{job.company_name}</p>
            </div>
            <a
              href={applyUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="shrink-0 rounded-lg bg-accent px-5 py-2 text-sm font-semibold text-accent-foreground shadow-sm"
            >
              Apply
            </a>
          </div>
        </div>
      )}
    </main>
  );
}
