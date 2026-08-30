import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { getToken } from "next-auth/jwt";

export default async function proxy(request: NextRequest) {
  const token = await getToken({ req: request, secret: process.env.AUTH_SECRET });
  if (token) {
    return NextResponse.next();
  }

  if (request.nextUrl.pathname.startsWith("/api/")) {
    return NextResponse.json({ detail: "Authentication required" }, { status: 401 });
  }

  return NextResponse.redirect(new URL("/login", request.url));
}

export const config = {
  matcher: [
    "/((?!api/auth|login|_next/static|_next/image|favicon.ico|pdf.worker.min.mjs).*)",
  ],
};
