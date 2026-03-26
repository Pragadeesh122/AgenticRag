import { NextResponse } from "next/server";
import { auth } from "@/auth";
import { prisma } from "@/lib/prisma";

// PATCH /api/chat/sessions/[id] — update session (title, backendSessionId)
export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = await params;
  const body = await req.json();

  const chatSession = await prisma.chatSession.updateMany({
    where: { id, userId: session.user.id },
    data: {
      ...(body.title !== undefined && { title: body.title }),
      ...(body.backendSessionId !== undefined && {
        backendSessionId: body.backendSessionId,
      }),
    },
  });

  if (chatSession.count === 0) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  return NextResponse.json({ ok: true });
}

// DELETE /api/chat/sessions/[id] — delete session and its messages
export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = await params;

  // Fetch backendSessionId before deleting so we can clean up Redis
  const chatSession = await prisma.chatSession.findFirst({
    where: { id, userId: session.user.id },
    select: { backendSessionId: true },
  });

  if (!chatSession) {
    return NextResponse.json({ error: "Not found" }, { status: 404 });
  }

  // Cascade deletes messages too
  await prisma.chatSession.delete({ where: { id } });

  return NextResponse.json({
    ok: true,
    backendSessionId: chatSession.backendSessionId,
  });
}
