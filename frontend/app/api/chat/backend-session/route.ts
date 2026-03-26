import { auth } from "@/auth";
import { NextResponse } from "next/server";

// POST /api/chat/backend-session — create a new backend (Redis) session
export async function POST() {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

  const backendRes = await fetch(`${backendUrl}/session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });

  if (!backendRes.ok) {
    return NextResponse.json(
      { error: `Failed to create backend session: ${backendRes.status}` },
      { status: backendRes.status }
    );
  }

  const data = (await backendRes.json()) as { session_id: string };
  return NextResponse.json({ session_id: data.session_id }, { status: 201 });
}
