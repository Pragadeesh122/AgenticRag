import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { prisma } from "@/lib/prisma";

// PATCH /api/chat/messages/[id] — update message metadata
export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = await params;
  const { metadata } = await req.json();

  if (!metadata || typeof metadata !== "object") {
    return NextResponse.json({ error: "metadata required" }, { status: 400 });
  }

  // Verify the message belongs to the user via the chat session
  const message = await prisma.chatMessage.findFirst({
    where: { id },
    select: {
      id: true,
      metadata: true,
      chatSession: { select: { userId: true } },
    },
  });

  if (!message || message.chatSession.userId !== session.user.id) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  // Merge new metadata with existing
  const existing = (message.metadata as Record<string, unknown>) ?? {};
  const updated = await prisma.chatMessage.update({
    where: { id },
    data: {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      metadata: { ...existing, ...metadata } as any,
    },
    select: { id: true, metadata: true },
  });

  return NextResponse.json(updated);
}
