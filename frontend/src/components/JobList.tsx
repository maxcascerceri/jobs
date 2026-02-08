"use client";

import { Job } from "@/lib/types";
import JobCard from "./JobCard";

interface JobListProps {
  jobs: Job[];
  total: number;
  page: number;
  perPage: number;
  onPageChange: (page: number) => void;
  loading: boolean;
}

export default function JobList({
  jobs,
  total,
  page,
  perPage,
  onPageChange,
  loading,
}: JobListProps) {
  const totalPages = Math.ceil(total / perPage);

  if (loading) {
    return (
      <div className="flex flex-col gap-3">
        {Array.from({ length: 8 }).map((_, i) => (
          <div
            key={i}
            className="animate-pulse rounded-xl border border-border bg-card p-5"
          >
            <div className="flex items-start gap-4">
              <div className="hidden sm:block h-11 w-11 rounded-lg bg-muted" />
              <div className="flex-1 space-y-2.5">
                <div className="h-4 w-3/4 rounded bg-muted" />
                <div className="h-3 w-1/2 rounded bg-muted" />
                <div className="flex gap-2">
                  <div className="h-5 w-16 rounded-md bg-muted" />
                  <div className="h-5 w-20 rounded-md bg-muted" />
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border bg-card py-16 text-center">
        <div className="mb-3 text-4xl">&#x1F50D;</div>
        <h3 className="text-lg font-semibold text-foreground">No jobs found</h3>
        <p className="mt-1 max-w-sm text-sm text-muted-foreground">
          Try adjusting your search or filters. New jobs are scraped daily from
          top remote job boards.
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* Results count */}
      <div className="mb-3 flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          Showing {(page - 1) * perPage + 1}&ndash;{Math.min(page * perPage, total)} of{" "}
          {total.toLocaleString()} jobs
        </p>
      </div>

      {/* Job cards */}
      <div className="flex flex-col gap-2">
        {jobs.map((job) => (
          <JobCard key={job.id} job={job} />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-6 flex items-center justify-center gap-1">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={page <= 1}
            className="rounded-lg border border-border bg-card px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Previous
          </button>

          {generatePageNumbers(page, totalPages).map((p, i) =>
            p === "..." ? (
              <span key={`dots-${i}`} className="px-2 text-xs text-muted-foreground">
                &hellip;
              </span>
            ) : (
              <button
                key={p}
                onClick={() => onPageChange(p as number)}
                className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-colors ${
                  p === page
                    ? "bg-foreground text-card"
                    : "border border-border bg-card text-foreground hover:bg-muted"
                }`}
              >
                {p}
              </button>
            )
          )}

          <button
            onClick={() => onPageChange(page + 1)}
            disabled={page >= totalPages}
            className="rounded-lg border border-border bg-card px-3 py-1.5 text-xs font-medium text-foreground transition-colors hover:bg-muted disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

function generatePageNumbers(current: number, total: number): (number | string)[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);

  const pages: (number | string)[] = [];

  if (current <= 3) {
    pages.push(1, 2, 3, 4, "...", total);
  } else if (current >= total - 2) {
    pages.push(1, "...", total - 3, total - 2, total - 1, total);
  } else {
    pages.push(1, "...", current - 1, current, current + 1, "...", total);
  }

  return pages;
}
