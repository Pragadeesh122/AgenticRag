import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { prisma } from "@/lib/prisma";

// GET /api/chat/sessions — list all sessions for the authenticated user
export async function GET() {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const chatSessions = await prisma.chatSession.findMany({
    where: { userId: session.user.id, projectId: null },
    orderBy: { updatedAt: "desc" },
    select: {
      id: true,
      backendSessionId: true,
      title: true,
      createdAt: true,
      updatedAt: true,
    },
  });

  return NextResponse.json(chatSessions);
}

// POST /api/chat/sessions — create a new chat session
export async function POST(req: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body = await req.json().catch(() => ({}));
  const title = body.title || "New chat";

  const chatSession = await prisma.chatSession.create({
    data: {
      userId: session.user.id,
      title,
    },
    select: {
      id: true,
      backendSessionId: true,
      title: true,
      createdAt: true,
      updatedAt: true,
    },
  });

  return NextResponse.json(chatSession, { status: 201 });
}
