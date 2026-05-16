import { NextResponse, type NextRequest } from "next/server";

const AUTH_COOKIE_NAME = "app_token";
const SIGN_IN_PATH = "/auth/signin";
const BLOG_HOST = "blog.runaxai.com";

function isProtectedPath(pathname: string): boolean {
  return (
    pathname === "/chat" ||
    pathname === "/settings" ||
    pathname.startsWith("/projects/")
  );
}

export function proxy(request: NextRequest) {
  const host = (request.headers.get("host") ?? "").toLowerCase();
  const { pathname, search } = request.nextUrl;

  if (host === BLOG_HOST && !pathname.startsWith("/blog")) {
    const target = pathname === "/" ? "/blog" : `/blog${pathname}`;
    return NextResponse.rewrite(new URL(`${target}${search}`, request.url));
  }

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
  matcher: ["/((?!_next/|api/|favicon\\.ico|icon\\.svg).*)"],
};
