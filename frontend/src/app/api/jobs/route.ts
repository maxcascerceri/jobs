import { NextRequest, NextResponse } from "next/server";
import { getJobs } from "@/lib/db";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);

    const search = searchParams.get("search") || "";
    const category = searchParams.get("category") || "";
    const employment_type = searchParams.get("employment_type") || "";
    const experience_level = searchParams.get("experience_level") || "";
    const page = parseInt(searchParams.get("page") || "1", 10);
    const per_page = parseInt(searchParams.get("per_page") || "30", 10);

    const result = getJobs({
      search,
      category,
      employment_type,
      experience_level,
      page,
      per_page: Math.min(per_page, 100),
    });

    return NextResponse.json(result);
  } catch (error) {
    console.error("Error fetching jobs:", error);

    // Return empty results if DB doesn't exist yet
    return NextResponse.json({
      jobs: [],
      total: 0,
      page: 1,
      per_page: 30,
      categories: [],
      employment_types: [],
    });
  }
}
