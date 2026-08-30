import type { NextRequest } from "next/server";
import { getToken } from "next-auth/jwt";

export const dynamic = "force-dynamic";

// Streams the user's current CV PDF (binary) — the shared JSON proxy would
// corrupt it, so this route handles the bytes directly.
export async function GET(request: NextRequest) {
  const token = await getToken({ req: request, secret: process.env.AUTH_SECRET });
  if (!token?.accessToken) {
    return new Response("Authentication required", { status: 401 });
  }

  const apiBaseUrl = process.env.API_INTERNAL_URL ?? "http://api:8000";
  try {
    const response = await fetch(`${apiBaseUrl}/onboarding/cv/file`, {
      cache: "no-store",
      headers: { authorization: `Bearer ${token.accessToken}` },
    });
    if (!response.ok) {
      return new Response("CV not available", { status: response.status });
    }
    const body = await response.arrayBuffer();
    return new Response(body, {
      status: 200,
      headers: {
        "content-type": response.headers.get("content-type") ?? "application/pdf",
        "content-disposition":
          response.headers.get("content-disposition") ?? "inline",
      },
    });
  } catch {
    return new Response("API unavailable", { status: 503 });
  }
}
