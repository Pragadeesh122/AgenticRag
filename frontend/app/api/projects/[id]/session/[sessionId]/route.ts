import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { prisma } from "@/lib/prisma";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

// DELETE /api/projects/[id]/session/[sessionId] — delete project chat session
export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string; sessionId: string }> }
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id: projectId, sessionId } = await params;

  const chatSession = await prisma.chatSession.findFirst({
    where: { id: sessionId, projectId, userId: session.user.id },
    select: { backendSessionId: true },
  });

  if (!chatSession) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  // Clean up Redis session
  if (chatSession.backendSessionId) {
    try {
      await fetch(
        `${BACKEND_URL}/projects/${projectId}/session/${chatSession.backendSessionId}`,
        { method: "DELETE" }
      );
    } catch (e) {
      // best-effort
    }
  }

  await prisma.chatSession.delete({ where: { id: sessionId } });

  return NextResponse.json({ ok: true });
}
