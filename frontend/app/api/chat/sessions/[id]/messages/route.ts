import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { prisma } from "@/lib/prisma";

// GET /api/chat/sessions/[id]/messages — fetch messages for a session
export async function GET(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = await params;

  // Verify session belongs to user
  const chatSession = await prisma.chatSession.findFirst({
    where: { id, userId: session.user.id },
    select: { id: true },
  });

  if (!chatSession) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  const messages = await prisma.chatMessage.findMany({
    where: { chatSessionId: id },
    orderBy: { createdAt: "asc" },
    select: {
      id: true,
      role: true,
      content: true,
      toolCalls: true,
      createdAt: true,
    },
  });

  return NextResponse.json(messages);
}

// POST /api/chat/sessions/[id]/messages — save one or more messages
export async function POST(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = await params;

  // Verify session belongs to user
  const chatSession = await prisma.chatSession.findFirst({
    where: { id, userId: session.user.id },
    select: { id: true },
  });

  if (!chatSession) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  const body = await req.json();
  const messages: Array<{
    role: string;
    content: string;
    toolCalls?: Record<string, unknown>[];
  }> = Array.isArray(body) ? body : [body];

  // Validate each message's role and content
  for (const msg of messages) {
    if (msg.role !== "user" && msg.role !== "assistant") {
      return NextResponse.json(
        { error: `Invalid role: "${msg.role}". Must be "user" or "assistant".` },
        { status: 400 }
      );
    }
    if (typeof msg.content !== "string") {
      return NextResponse.json(
        { error: "Each message content must be a string." },
        { status: 400 }
      );
    }
  }

  const created = await prisma.chatMessage.createMany({
    data: messages.map((m) => ({
      chatSessionId: id,
      role: m.role,
      content: m.content,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      toolCalls: (m.toolCalls ?? []) as any,
    })),
  });

  // Touch session updatedAt
  await prisma.chatSession.update({
    where: { id },
    data: { updatedAt: new Date() },
  });

  return NextResponse.json({ count: created.count }, { status: 201 });
}
