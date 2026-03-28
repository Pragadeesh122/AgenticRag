import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { prisma } from "@/lib/prisma";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

// GET /api/projects/[id]/documents/[docId]/status — poll processing status
export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string; docId: string }> }
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id: projectId, docId } = await params;

  // Verify ownership
  const document = await prisma.document.findFirst({
    where: {
      id: docId,
      projectId,
      project: { userId: session.user.id },
    },
  });

  if (!document) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  // If already ready or failed in DB, return that
  if (document.status === "ready" || document.status === "failed") {
    return NextResponse.json({
      status: document.status,
      chunkCount: document.chunkCount,
      chunkStrategy: document.chunkStrategy,
      errorMessage: document.errorMessage,
    });
  }

  // Otherwise poll the backend for live processing status
  try {
    const backendRes = await fetch(
      `${BACKEND_URL}/projects/${projectId}/documents/${docId}/status`
    );

    if (backendRes.ok) {
      const data = await backendRes.json();

      // If backend says ready/failed, update our DB record
      if (data.status === "ready" || data.status === "failed") {
        await prisma.document.update({
          where: { id: docId },
          data: {
            status: data.status,
            chunkCount: data.chunk_count || 0,
            chunkStrategy: data.chunk_strategy || null,
            errorMessage: data.error || null,
          },
        });
      }

      return NextResponse.json({
        status: data.status,
        chunkCount: data.chunk_count || 0,
        chunkStrategy: data.chunk_strategy || null,
        errorMessage: data.error || null,
      });
    }
  } catch (e) {
    // Backend unreachable — return DB state
  }

  return NextResponse.json({
    status: document.status,
    chunkCount: document.chunkCount,
    chunkStrategy: document.chunkStrategy,
    errorMessage: document.errorMessage,
  });
}
