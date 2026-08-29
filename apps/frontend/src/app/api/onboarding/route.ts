import type { NextRequest } from "next/server";

import { authenticatedBackendRequest } from "@/lib/backend";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  return authenticatedBackendRequest(request, "/onboarding");
}
