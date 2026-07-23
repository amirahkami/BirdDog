import type { NextRequest } from "next/server";
import { getToken } from "next-auth/jwt";

export async function authenticatedBackendRequest(
  request: NextRequest,
  path: string,
  requiredRole?: string,
) {
  const token = await getToken({ req: request, secret: process.env.AUTH_SECRET });

  if (!token?.accessToken) {
    return Response.json({ detail: "Authentication required" }, { status: 401 });
  }

  if (requiredRole && !token.roles?.includes(requiredRole)) {
    return Response.json({ detail: "Insufficient permissions" }, { status: 403 });
  }

  const apiBaseUrl = process.env.API_INTERNAL_URL ?? "http://api:8000";
  try {
    const response = await fetch(`${apiBaseUrl}${path}`, {
      cache: "no-store",
      headers: { authorization: `Bearer ${token.accessToken}` },
    });
    const body = await response.text();
    return new Response(body, {
      status: response.status,
      headers: { "content-type": "application/json" },
    });
  } catch {
    return Response.json({ detail: "API unavailable" }, { status: 503 });
  }
}
