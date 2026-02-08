import { NextRequest, NextResponse } from "next/server";
import { getJobs } from "@/lib/db";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const q = searchParams.get("q") || "";

    if (!q || q.length < 2) {
      return NextResponse.json({ jobs: [], total: 0 });
    }

    const result = getJobs({
      search: q,
      page: 1,
      per_page: 10,
    });

    return NextResponse.json(result);
  } catch (error) {
    console.error("Error searching jobs:", error);
    return NextResponse.json({ jobs: [], total: 0 });
  }
}
