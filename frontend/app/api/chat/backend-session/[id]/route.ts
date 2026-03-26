import { auth } from "@/auth";
import { NextResponse } from "next/server";

// DELETE /api/chat/backend-session/[id] — delete a backend (Redis) session
export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = await params;
  const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

  await fetch(`${backendUrl}/session/${id}`, { method: "DELETE" });

  return new Response(null, { status: 204 });
}
