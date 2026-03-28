import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { prisma } from "@/lib/prisma";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

// POST /api/projects/[id]/session — create a project-scoped Redis + DB session
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
    select: { id: true, name: true },
  });

  if (!project) {
    return NextResponse.json({ error: "Project not found" }, { status: 404 });
  }

  // Create Redis session on backend
  const backendRes = await fetch(
    `${BACKEND_URL}/projects/${projectId}/session?project_name=${encodeURIComponent(project.name)}`,
    { method: "POST" }
  );

  if (!backendRes.ok) {
    return NextResponse.json({ error: "Failed to create backend session" }, { status: 502 });
  }

  const { session_id: backendSessionId } = await backendRes.json();

  // Create ChatSession in DB linked to project
  const chatSession = await prisma.chatSession.create({
    data: {
      userId: session.user.id,
      projectId,
      backendSessionId,
      title: "New chat",
    },
  });

  return NextResponse.json({
    id: chatSession.id,
    backendSessionId,
    title: chatSession.title,
    projectId,
    createdAt: chatSession.createdAt.toISOString(),
    updatedAt: chatSession.updatedAt.toISOString(),
  }, { status: 201 });
}
