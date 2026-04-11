import "server-only";

import { cookies } from "next/headers";
import type { Project, Session, User } from "./types";

const SERVER_API_BASE_URL =
  process.env.INTERNAL_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

function buildUrl(endpoint: string): string {
  return endpoint.startsWith("http")
    ? endpoint
    : `${SERVER_API_BASE_URL}${endpoint.replace(/^\/api/, "")}`;
}

async function serverApiFetch(
  endpoint: string,
  options: RequestInit = {}
): Promise<Response> {
  const cookieStore = await cookies();
  const requestHeaders = new Headers(options.headers);
  const cookieHeader = cookieStore.toString();

  if (cookieHeader) {
    requestHeaders.set("cookie", cookieHeader);
  }

  return fetch(buildUrl(endpoint), {
    ...options,
    headers: requestHeaders,
    cache: "no-store",
  });
}

export async function fetchCurrentUserServer(): Promise<User | null> {
  const res = await serverApiFetch("/users/me");
  if (!res.ok) return null;
  return res.json();
}

export async function fetchSessionsServer(): Promise<Session[]> {
  const res = await serverApiFetch("/chat/sessions");
  if (!res.ok) return [];
  return res.json();
}

export async function fetchProjectsServer(): Promise<Project[]> {
  const res = await serverApiFetch("/projects");
  if (!res.ok) return [];
  return res.json();
}

export async function fetchProjectServer(projectId: string): Promise<Project | null> {
  const res = await serverApiFetch(`/projects/${projectId}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Failed to fetch project ${projectId}`);
  return res.json();
}

export async function fetchProjectSessionsServer(
  projectId: string
): Promise<Session[]> {
  const res = await serverApiFetch(`/projects/${projectId}/sessions`);
  if (!res.ok) return [];
  return res.json();
}
