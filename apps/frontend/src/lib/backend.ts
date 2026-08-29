import type { NextRequest } from "next/server";
import { getToken } from "next-auth/jwt";

/**
 * Proxy a frontend API route to the backend, attaching the user's access token.
 * Forwards the incoming method and body (JSON or multipart) for non-GET requests,
 * so the same helper serves reads, PUT steps and CV upload.
 */
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
  const method = request.method.toUpperCase();
  const headers: Record<string, string> = {
    authorization: `Bearer ${token.accessToken}`,
  };

  let body: ArrayBuffer | undefined;
  if (method !== "GET" && method !== "HEAD") {
    const contentType = request.headers.get("content-type");
    if (contentType) {
      headers["content-type"] = contentType;
    }
    body = await request.arrayBuffer();
  }

  try {
    const response = await fetch(`${apiBaseUrl}${path}`, {
      method,
      cache: "no-store",
      headers,
      body,
    });
    const responseBody = await response.text();
    return new Response(responseBody, {
      status: response.status,
      headers: {
        "content-type": response.headers.get("content-type") ?? "application/json",
      },
    });
  } catch {
    return Response.json({ detail: "API unavailable" }, { status: 503 });
  }
}
