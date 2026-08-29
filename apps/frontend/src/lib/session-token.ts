import { cookies } from "next/headers";
import { getToken } from "next-auth/jwt";
import type { NextRequest } from "next/server";

/**
 * Read the user's Keycloak access token from the next-auth JWT cookie in a
 * server component. Kept server-only so the token is never exposed to the client.
 */
export async function getAccessToken(): Promise<string | null> {
  const cookie = (await cookies()).toString();
  const token = await getToken({
    req: { headers: { cookie } } as unknown as NextRequest,
    secret: process.env.AUTH_SECRET,
  });
  return token?.accessToken ?? null;
}
