import { cookies } from "next/headers";
import { getToken } from "next-auth/jwt";

/**
 * Read the user's Keycloak access token from the next-auth JWT cookie in a
 * server component. getToken reads `req.cookies` (a name->value map), so we
 * pass all cookies; SessionStore reassembles any chunked session cookie.
 * Kept server-only so the token is never exposed to the client.
 */
export async function getAccessToken(): Promise<string | null> {
  const store = await cookies();
  const cookieMap: Record<string, string> = {};
  for (const cookie of store.getAll()) {
    cookieMap[cookie.name] = cookie.value;
  }

  const token = await getToken({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    req: { cookies: cookieMap } as any,
    secret: process.env.AUTH_SECRET,
  });
  return token?.accessToken ?? null;
}
