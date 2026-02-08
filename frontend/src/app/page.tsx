"use client";

import { useCallback, useEffect, useState } from "react";
import Header from "@/components/Header";
import SearchBar from "@/components/SearchBar";
import FilterBar from "@/components/FilterBar";
import JobList from "@/components/JobList";
import { Job, JobsResponse } from "@/lib/types";

export default function Home() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("All");
  const [employmentType, setEmploymentType] = useState("All");
  const [experienceLevel, setExperienceLevel] = useState("All");
  const [categories, setCategories] = useState<string[]>([]);
  const [employmentTypes, setEmploymentTypes] = useState<string[]>([]);
  const perPage = 30;

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      if (category !== "All") params.set("category", category);
      if (employmentType !== "All") params.set("employment_type", employmentType);
      if (experienceLevel !== "All") params.set("experience_level", experienceLevel);
      params.set("page", String(page));
      params.set("per_page", String(perPage));

      const res = await fetch(`/api/jobs?${params.toString()}`);
      const data: JobsResponse = await res.json();

      setJobs(data.jobs);
      setTotal(data.total);
      if (data.categories.length > 0) setCategories(data.categories);
      if (data.employment_types.length > 0) setEmploymentTypes(data.employment_types);
    } catch (err) {
      console.error("Failed to fetch jobs:", err);
    } finally {
      setLoading(false);
    }
  }, [search, category, employmentType, experienceLevel, page]);

  useEffect(() => {
    const debounce = setTimeout(fetchJobs, search ? 300 : 0);
    return () => clearTimeout(debounce);
  }, [fetchJobs, search]);

  // Reset page when filters change
  useEffect(() => {
    setPage(1);
  }, [search, category, employmentType, experienceLevel]);

  return (
    <div className="min-h-screen bg-background">
      <Header />

      <main className="mx-auto max-w-6xl px-4 sm:px-6">
        {/* Hero / Search section */}
        <section className="pb-6 pt-8 sm:pt-10">
          <div className="mb-1">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-foreground">
              Remote jobs that don&apos;t suck
            </h1>
            <p className="mt-1.5 text-sm sm:text-base text-muted-foreground">
              Curated from the best remote-first job boards. Updated daily.
            </p>
          </div>

          <div className="mt-5">
            <SearchBar value={search} onChange={setSearch} totalJobs={total} />
          </div>

          <div className="mt-4">
            <FilterBar
              categories={categories}
              employmentTypes={employmentTypes}
              selectedCategory={category}
              selectedType={employmentType}
              selectedExperience={experienceLevel}
              onCategoryChange={setCategory}
              onTypeChange={setEmploymentType}
              onExperienceChange={setExperienceLevel}
            />
          </div>
        </section>

        {/* Job listings */}
        <section className="pb-16">
          <JobList
            jobs={jobs}
            total={total}
            page={page}
            perPage={perPage}
            onPageChange={setPage}
            loading={loading}
          />
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-border py-8">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-muted-foreground">
            <p>
              RemoteHQ &mdash; Aggregated from WeWorkRemotely, Dynamite Jobs,
              Jobicy, Working Nomads, Jobspresso &amp; Himalayas
            </p>
            <p>Jobs are scraped &amp; deduplicated daily</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
