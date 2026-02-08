"use client";

import Link from "next/link";
import { Job } from "@/lib/types";
import { formatSalary, getCategoryColor, getSourceLabel, timeAgo } from "@/lib/utils";

interface JobCardProps {
  job: Job;
}

export default function JobCard({ job }: JobCardProps) {
  const salary = formatSalary(job);
  const posted = timeAgo(job.posted_at);
  const categoryStyle = getCategoryColor(job.category);

  return (
    <Link
      href={`/jobs/${job.id}`}
      className="group block rounded-xl border border-border bg-card p-4 sm:p-5 transition-all duration-200 hover:border-zinc-300 hover:shadow-[0_2px_8px_rgba(0,0,0,0.04)]"
    >
      <div className="flex items-start gap-4">
        {/* Company logo / avatar */}
        <div className="hidden sm:flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-muted border border-border overflow-hidden">
          {job.company_logo_url ? (
            <img
              src={job.company_logo_url}
              alt={job.company_name}
              className="h-full w-full object-contain p-1"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = "none";
                (e.target as HTMLImageElement).parentElement!.innerHTML = `<span class="text-sm font-semibold text-muted-foreground">${(job.company_name || "?")[0].toUpperCase()}</span>`;
              }}
            />
          ) : (
            <span className="text-sm font-semibold text-muted-foreground">
              {(job.company_name || "?")[0].toUpperCase()}
            </span>
          )}
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-3">
            <div className="min-w-0">
              <h3 className="text-[15px] font-semibold leading-snug text-foreground group-hover:text-accent transition-colors line-clamp-1">
                {job.title}
              </h3>
              <p className="mt-0.5 text-sm text-muted-foreground line-clamp-1">
                {job.company_name}
                {job.location_text && job.location_text !== "Anywhere" && (
                  <span className="text-zinc-300 mx-1.5">&middot;</span>
                )}
                {job.location_text && job.location_text !== "Anywhere" && (
                  <span>{job.location_text}</span>
                )}
              </p>
            </div>

            {/* Time */}
            {posted && (
              <span className="shrink-0 text-xs text-muted-foreground whitespace-nowrap mt-0.5">
                {posted}
              </span>
            )}
          </div>

          {/* Tags row */}
          <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
            {job.category && (
              <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[11px] font-medium ${categoryStyle}`}>
                {job.category}
              </span>
            )}
            {job.employment_type && (
              <span className="inline-flex items-center rounded-md border border-border bg-muted px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
                {job.employment_type}
              </span>
            )}
            {salary && (
              <span className="inline-flex items-center rounded-md border border-emerald-200 bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700">
                {salary}
              </span>
            )}
            <span className="inline-flex items-center rounded-md bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground">
              {getSourceLabel(job.source)}
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}
