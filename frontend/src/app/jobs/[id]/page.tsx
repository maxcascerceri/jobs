import { notFound } from "next/navigation";
import { getJobById } from "@/lib/db";
import { Job } from "@/lib/types";
import Header from "@/components/Header";
import JobDetailClient from "./JobDetailClient";

export const dynamic = "force-dynamic";

interface PageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: PageProps) {
  const { id } = await params;
  try {
    const job = getJobById(id) as Job | undefined;
    if (!job) return { title: "Job Not Found — RemoteHQ" };
    return {
      title: `${job.title} at ${job.company_name} — RemoteHQ`,
      description: job.description_text?.slice(0, 160) || `${job.title} - Remote position at ${job.company_name}`,
    };
  } catch {
    return { title: "Job — RemoteHQ" };
  }
}

export default async function JobPage({ params }: PageProps) {
  const { id } = await params;
  let job: Job | undefined;

  try {
    job = getJobById(id) as Job | undefined;
  } catch {
    // DB might not exist yet
  }

  if (!job) {
    notFound();
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <JobDetailClient job={job} />
    </div>
  );
}
