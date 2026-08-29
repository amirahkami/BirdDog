import type { NextRequest } from "next/server";

import { authenticatedBackendRequest } from "@/lib/backend";

export const dynamic = "force-dynamic";

export async function POST(request: NextRequest) {
  return authenticatedBackendRequest(request, "/onboarding/cv");
}
