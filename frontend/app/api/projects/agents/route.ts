import { NextResponse } from "next/server";
import { auth } from "@/auth";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

// GET /api/projects/agents — list available agents
export async function GET() {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const res = await fetch(`${BACKEND_URL}/projects/agents`);
    if (!res.ok) {
      return NextResponse.json([], { status: 200 });
    }
    const agents = await res.json();
    return NextResponse.json(agents);
  } catch {
    return NextResponse.json([], { status: 200 });
  }
}
