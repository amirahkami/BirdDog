import type { NextAuthOptions } from "next-auth";
import KeycloakProvider from "next-auth/providers/keycloak";

type KeycloakAccessToken = {
  preferred_username?: string;
  realm_access?: { roles?: string[] };
};

const issuer = process.env.KEYCLOAK_ISSUER ?? "http://auth.localhost:22080/realms/birddog";

export const authOptions: NextAuthOptions = {
  secret: process.env.AUTH_SECRET,
  session: {
    strategy: "jwt",
    maxAge: 60 * 60,
  },
  pages: {
    signIn: "/login",
  },
  providers: [
    KeycloakProvider({
      clientId: process.env.KEYCLOAK_CLIENT_ID ?? "birddog-web",
      clientSecret: process.env.KEYCLOAK_CLIENT_SECRET ?? "",
      issuer,
    }),
  ],
  callbacks: {
    async jwt({ token, account }) {
      if (account?.access_token) {
        const accessToken = decodeAccessToken(account.access_token);
        token.accessToken = account.access_token;
        token.idToken = account.id_token;
        token.expiresAt = account.expires_at;
        token.username = accessToken.preferred_username ?? token.email ?? "user";
        token.roles = accessToken.realm_access?.roles ?? [];
      }
      return token;
    },
    async session({ session, token }) {
      session.user.id = token.sub ?? "";
      session.user.username = token.username ?? session.user.email ?? "user";
      session.user.roles = token.roles ?? [];
      return session;
    },
  },
};

function decodeAccessToken(value: string): KeycloakAccessToken {
  try {
    const payload = value.split(".")[1];
    return JSON.parse(Buffer.from(payload, "base64url").toString("utf8")) as KeycloakAccessToken;
  } catch {
    return {};
  }
}
