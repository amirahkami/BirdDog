import type { NextAuthOptions } from "next-auth";
import type { JWT } from "next-auth/jwt";
import KeycloakProvider from "next-auth/providers/keycloak";

type KeycloakAccessToken = {
  preferred_username?: string;
  realm_access?: { roles?: string[] };
};

const issuer =
  process.env.KEYCLOAK_ISSUER ?? "http://auth.localhost:22080/realms/birddog";
const clientId = process.env.KEYCLOAK_CLIENT_ID ?? "birddog-web";
const clientSecret = process.env.KEYCLOAK_CLIENT_SECRET ?? "";

export const authOptions: NextAuthOptions = {
  secret: process.env.AUTH_SECRET,
  session: {
    strategy: "jwt",
    // Keep the user signed in for a full work session; rolls forward on activity.
    maxAge: 8 * 60 * 60,
    updateAge: 30 * 60,
  },
  pages: {
    signIn: "/login",
  },
  providers: [
    KeycloakProvider({ clientId, clientSecret, issuer }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      // Initial sign-in: capture the tokens from Keycloak.
      if (account?.access_token) {
        const decoded = decodeAccessToken(account.access_token);
        token.accessToken = account.access_token;
        token.refreshToken = account.refresh_token;
        token.idToken = account.id_token;
        token.expiresAt = account.expires_at;
        token.username = decoded.preferred_username ?? token.email ?? "user";
        token.roles = decoded.realm_access?.roles ?? [];
        token.error = undefined;
        return token;
      }

      // Access token still valid (with a 60s safety buffer): reuse it.
      if (token.expiresAt && Date.now() < token.expiresAt * 1000 - 60_000) {
        return token;
      }

      // Expired: refresh using the Keycloak refresh token.
      return refreshAccessToken(token);
    },
    async session({ session, token }) {
      session.user.id = token.sub ?? "";
      session.user.username = token.username ?? session.user.email ?? "user";
      session.user.roles = token.roles ?? [];
      return session;
    },
  },
};

async function refreshAccessToken(token: JWT): Promise<JWT> {
  if (!token.refreshToken) {
    return { ...token, error: "NoRefreshToken" };
  }
  try {
    const response = await fetch(`${issuer}/protocol/openid-connect/token`, {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      cache: "no-store",
      body: new URLSearchParams({
        grant_type: "refresh_token",
        client_id: clientId,
        client_secret: clientSecret,
        refresh_token: token.refreshToken,
      }),
    });
    const data = (await response.json()) as {
      access_token?: string;
      refresh_token?: string;
      id_token?: string;
      expires_in?: number;
      error?: string;
    };
    if (!response.ok || !data.access_token) {
      throw new Error(data.error ?? "refresh_failed");
    }
    const decoded = decodeAccessToken(data.access_token);
    return {
      ...token,
      accessToken: data.access_token,
      refreshToken: data.refresh_token ?? token.refreshToken,
      idToken: data.id_token ?? token.idToken,
      expiresAt: Math.floor(Date.now() / 1000) + (data.expires_in ?? 300),
      roles: decoded.realm_access?.roles ?? token.roles,
      username: decoded.preferred_username ?? token.username,
      error: undefined,
    };
  } catch {
    // Refresh failed (e.g. Keycloak session ended) — surface it; user re-logs in.
    return { ...token, error: "RefreshAccessTokenError" };
  }
}

function decodeAccessToken(value: string): KeycloakAccessToken {
  try {
    const payload = value.split(".")[1];
    return JSON.parse(
      Buffer.from(payload, "base64url").toString("utf8")
    ) as KeycloakAccessToken;
  } catch {
    return {};
  }
}
