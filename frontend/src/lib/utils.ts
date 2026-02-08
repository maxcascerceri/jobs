import { Job } from "./types";

export function formatSalary(job: Job): string {
  if (job.salary_text) return job.salary_text;
  if (!job.salary_min && !job.salary_max) return "";

  const currency = job.salary_currency || "USD";
  const symbol = currency === "USD" ? "$" : currency === "EUR" ? "\u20AC" : currency === "GBP" ? "\u00A3" : currency;

  const fmt = (n: number) => {
    if (n >= 1000) return `${symbol}${Math.round(n / 1000)}k`;
    return `${symbol}${n}`;
  };

  const period = job.salary_period === "yearly" ? "/yr" : job.salary_period === "monthly" ? "/mo" : job.salary_period === "hourly" ? "/hr" : "";

  if (job.salary_min && job.salary_max) {
    return `${fmt(job.salary_min)} - ${fmt(job.salary_max)}${period}`;
  }
  if (job.salary_min) return `${fmt(job.salary_min)}+${period}`;
  if (job.salary_max) return `Up to ${fmt(job.salary_max)}${period}`;
  return "";
}

export function timeAgo(dateStr: string): string {
  if (!dateStr) return "";
  try {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    const diffWeeks = Math.floor(diffDays / 7);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays}d ago`;
    if (diffWeeks < 4) return `${diffWeeks}w ago`;
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  } catch {
    return "";
  }
}

export function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    Engineering: "bg-blue-50 text-blue-700 border-blue-200",
    Design: "bg-purple-50 text-purple-700 border-purple-200",
    Marketing: "bg-orange-50 text-orange-700 border-orange-200",
    Sales: "bg-green-50 text-green-700 border-green-200",
    Support: "bg-yellow-50 text-yellow-700 border-yellow-200",
    DevOps: "bg-cyan-50 text-cyan-700 border-cyan-200",
    Data: "bg-indigo-50 text-indigo-700 border-indigo-200",
    Product: "bg-pink-50 text-pink-700 border-pink-200",
    Management: "bg-slate-100 text-slate-700 border-slate-200",
    Writing: "bg-emerald-50 text-emerald-700 border-emerald-200",
    Finance: "bg-amber-50 text-amber-700 border-amber-200",
    HR: "bg-rose-50 text-rose-700 border-rose-200",
    Other: "bg-gray-50 text-gray-700 border-gray-200",
  };
  return colors[category] || colors.Other;
}

export function getCategoryIcon(category: string): string {
  const icons: Record<string, string> = {
    Engineering: "\u2728",
    Design: "\uD83C\uDFA8",
    Marketing: "\uD83D\uDCE3",
    Sales: "\uD83D\uDCC8",
    Support: "\uD83D\uDCAC",
    DevOps: "\u2699\uFE0F",
    Data: "\uD83D\uDCCA",
    Product: "\uD83D\uDCE6",
    Management: "\uD83D\uDCBC",
    Writing: "\u270D\uFE0F",
    Finance: "\uD83D\uDCB0",
    HR: "\uD83D\uDC65",
    Other: "\uD83D\uDD17",
  };
  return icons[category] || icons.Other;
}

export function getSourceLabel(source: string): string {
  const labels: Record<string, string> = {
    weworkremotely: "WWR",
    dynamitejobs: "Dynamite",
    jobicy: "Jobicy",
    workingnomads: "Nomads",
    jobspresso: "Jobspresso",
    himalayas: "Himalayas",
    remotesource: "Remote Source",
  };
  return labels[source] || source;
}
