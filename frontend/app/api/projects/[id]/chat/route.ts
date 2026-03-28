import { auth } from "@/auth";
import { prisma } from "@/lib/prisma";
import { NextResponse } from "next/server";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

// POST /api/projects/[id]/chat — proxy project chat to backend SSE stream
export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id: projectId } = await params;

  // Verify project belongs to user
  const project = await prisma.project.findFirst({
    where: { id: projectId, userId: session.user.id },
    select: {
      id: true,
      documents: {
        where: { status: "ready" },
        select: { chunkCount: true },
      },
    },
  });

  if (!project) {
    return NextResponse.json({ error: "Project not found" }, { status: 404 });
  }

  const body = await req.json();
  const { sessionId, message, agent } = body as {
    sessionId: string;
    message: string;
    agent?: string | null;
  };

  if (!sessionId || typeof sessionId !== "string") {
    return NextResponse.json({ error: "sessionId is required" }, { status: 400 });
  }
  if (!message || typeof message !== "string") {
    return NextResponse.json({ error: "message is required" }, { status: 400 });
  }

  // Calculate total chunk count across all ready documents
  const totalChunks = project.documents.reduce(
    (sum, doc) => sum + doc.chunkCount,
    0
  );

  const backendRes = await fetch(`${BACKEND_URL}/projects/${projectId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: sessionId,
      message,
      chunk_count: totalChunks,
      agent: agent || null,
    }),
  });

  if (!backendRes.ok) {
    const text = await backendRes.text();
    return NextResponse.json(
      { error: `Backend error: ${backendRes.status} ${text}` },
      { status: backendRes.status }
    );
  }

  // Stream the SSE response
  const stream = new ReadableStream({
    async start(controller) {
      const reader = backendRes.body!.getReader();
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          controller.enqueue(value);
        }
      } catch (err) {
        controller.error(err);
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
