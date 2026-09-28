import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  const accessToken =
    request.cookies.get("access_token")?.value ||
    request.cookies.get("agni_token")?.value;

  if (!accessToken) {
    const loginUrl = new URL("/login", request.url);
    const destination = pathname + search;
    if (destination && destination !== "/") {
      loginUrl.searchParams.set("redirect", destination);
    }
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/jarvis/:path*",
    "/admin/:path*",
    "/portal/agency/:path*",
    "/portal/industry/:path*",
    "/portal/research/:path*",
  ],
};
