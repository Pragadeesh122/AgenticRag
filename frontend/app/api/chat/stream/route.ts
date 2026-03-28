import { auth } from "@/auth";
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body = await req.json();
  const { sessionId, message } = body as { sessionId: string; message: string };

  if (!sessionId || typeof sessionId !== "string") {
    return NextResponse.json({ error: "sessionId is required" }, { status: 400 });
  }
  if (!message || typeof message !== "string") {
    return NextResponse.json({ error: "message is required" }, { status: 400 });
  }

  // Ensure the Redis session exists — restore from DB if expired
  await ensureSession(sessionId, session.user.id);

  const backendRes = await fetch(`${BACKEND_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  });

  if (!backendRes.ok) {
    const text = await backendRes.text();
    return NextResponse.json(
      { error: `Backend error: ${backendRes.status} ${text}` },
      { status: backendRes.status }
    );
  }

  // Stream the SSE response from the backend directly to the client
  const stream = new ReadableStream({
    async start(controller) {
      const reader = backendRes.body!.getReader();
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          controller.enqueue(value);
        }
      } catch {
        // client disconnected
      } finally {
        controller.close();
      }
    },
    cancel() {
      backendRes.body?.cancel();
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
      Connection: "keep-alive",
    },
  });
}

/**
 * Check if the backend Redis session exists.
 * If not, fetch messages from DB and restore it.
 */
async function ensureSession(backendSessionId: string, userId: string) {
  const check = await fetch(`${BACKEND_URL}/session/${backendSessionId}/exists`);
  const { exists } = await check.json();
  if (exists) return;

  // Find the DB session that owns this backend session ID
  const chatSession = await prisma.chatSession.findFirst({
    where: { backendSessionId, userId },
    select: { id: true },
  });
  if (!chatSession) return;

  // Fetch messages from DB
  const messages = await prisma.chatMessage.findMany({
    where: { chatSessionId: chatSession.id },
    orderBy: { createdAt: "asc" },
    select: { role: true, content: true },
  });

  // Restore the Redis session
  await fetch(`${BACKEND_URL}/session/restore`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: backendSessionId, messages }),
  });
}
