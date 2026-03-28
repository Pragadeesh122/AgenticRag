import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { prisma } from "@/lib/prisma";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

// DELETE /api/projects/[id]/documents/[docId] — delete a document
export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string; docId: string }> }
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id: projectId, docId } = await params;

  // Verify project belongs to user and document exists
  const document = await prisma.document.findFirst({
    where: {
      id: docId,
      projectId,
      project: { userId: session.user.id },
    },
    select: { id: true },
  });

  if (!document) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  // Delete vectors from Pinecone via backend
  try {
    await fetch(
      `${BACKEND_URL}/projects/${projectId}/documents/${docId}`,
      { method: "DELETE" }
    );
  } catch (e) {
    // Best-effort cleanup
  }

  // Delete from DB
  await prisma.document.delete({ where: { id: docId } });

  return NextResponse.json({ ok: true });
}
