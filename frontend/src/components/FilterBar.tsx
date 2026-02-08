"use client";

interface FilterBarProps {
  categories: string[];
  employmentTypes: string[];
  selectedCategory: string;
  selectedType: string;
  selectedExperience: string;
  onCategoryChange: (cat: string) => void;
  onTypeChange: (type: string) => void;
  onExperienceChange: (exp: string) => void;
}

const EXPERIENCE_LEVELS = ["All", "Junior", "Mid", "Senior", "Manager", "Executive"];

export default function FilterBar({
  categories,
  employmentTypes,
  selectedCategory,
  selectedType,
  selectedExperience,
  onCategoryChange,
  onTypeChange,
  onExperienceChange,
}: FilterBarProps) {
  const allCategories = ["All", ...categories.filter(Boolean)];
  const allTypes = ["All", ...employmentTypes.filter(Boolean)];

  const hasActiveFilters =
    selectedCategory !== "All" || selectedType !== "All" || selectedExperience !== "All";

  return (
    <div className="flex flex-col gap-3">
      {/* Category pills */}
      <div className="flex flex-wrap items-center gap-1.5">
        {allCategories.map((cat) => (
          <button
            key={cat}
            onClick={() => onCategoryChange(cat)}
            className={`rounded-lg px-3 py-1.5 text-xs font-medium transition-all duration-150 ${
              selectedCategory === cat
                ? "bg-foreground text-card shadow-sm"
                : "bg-muted text-muted-foreground hover:bg-zinc-200 hover:text-foreground"
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Secondary filters */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-muted-foreground">Type:</span>
          <select
            value={selectedType}
            onChange={(e) => onTypeChange(e.target.value)}
            className="rounded-lg border border-border bg-card px-2.5 py-1 text-xs text-foreground outline-none focus:border-accent cursor-pointer"
          >
            {allTypes.map((t) => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-xs text-muted-foreground">Level:</span>
          <select
            value={selectedExperience}
            onChange={(e) => onExperienceChange(e.target.value)}
            className="rounded-lg border border-border bg-card px-2.5 py-1 text-xs text-foreground outline-none focus:border-accent cursor-pointer"
          >
            {EXPERIENCE_LEVELS.map((l) => (
              <option key={l} value={l}>{l}</option>
            ))}
          </select>
        </div>

        {hasActiveFilters && (
          <button
            onClick={() => {
              onCategoryChange("All");
              onTypeChange("All");
              onExperienceChange("All");
            }}
            className="ml-1 rounded-lg px-2.5 py-1 text-xs text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
          >
            Clear filters
          </button>
        )}
      </div>
    </div>
  );
}
