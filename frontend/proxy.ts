import { NextResponse, type NextRequest } from "next/server";

const AUTH_COOKIE_NAME = "app_token";
const SIGN_IN_PATH = "/auth/signin";

function isProtectedPath(pathname: string): boolean {
  return (
    pathname === "/chat" ||
    pathname === "/settings" ||
    pathname.startsWith("/projects/")
  );
}

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (!isProtectedPath(pathname)) {
    return NextResponse.next();
  }

  const authCookie = request.cookies.get(AUTH_COOKIE_NAME)?.value;
  if (authCookie) {
    return NextResponse.next();
  }

  const signInUrl = new URL(SIGN_IN_PATH, request.url);
  signInUrl.searchParams.set("next", pathname);
  return NextResponse.redirect(signInUrl);
}

export const config = {
  matcher: ["/chat", "/settings", "/projects/:path*"],
};
