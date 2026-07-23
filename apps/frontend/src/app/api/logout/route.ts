import type { NextRequest } from "next/server";
import { getToken } from "next-auth/jwt";

export async function GET(request: NextRequest) {
  const token = await getToken({ req: request, secret: process.env.AUTH_SECRET });
  if (!token) {
    return Response.json({ detail: "Authentication required" }, { status: 401 });
  }

  const issuer = process.env.KEYCLOAK_ISSUER ?? "http://auth.localhost:22080/realms/birddog";
  const logoutUrl = new URL(`${issuer}/protocol/openid-connect/logout`);
  if (token.idToken) {
    logoutUrl.searchParams.set("id_token_hint", token.idToken);
  }
  logoutUrl.searchParams.set(
    "post_logout_redirect_uri",
    `${process.env.NEXTAUTH_URL ?? "http://localhost:22300"}/login`,
  );

  return Response.json({ logoutUrl: logoutUrl.toString() });
}
