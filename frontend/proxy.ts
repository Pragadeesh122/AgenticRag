import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { getToken } from "next-auth/jwt";

export async function proxy(req: NextRequest) {
  const token = await getToken({ req, secret: process.env.AUTH_SECRET });

  if (!token) {
    const signInUrl = new URL("/auth/signin", req.url);
    return NextResponse.redirect(signInUrl);
  }

  return NextResponse.next();
}

export const config = {
  // Exclude the homepage (/), auth routes, static assets, and API routes
  // so the landing page is publicly accessible
  matcher: ["/((?!$|api|auth|_next/static|_next/image|favicon.ico).+)"],
};
