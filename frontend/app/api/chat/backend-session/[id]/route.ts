import { auth } from "@/auth";
import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

const VALID_CATEGORIES = [
  "work_context",
  "personal_context",
  "top_of_mind",
  "preferences",
];

// DELETE /api/chat/backend-session/[id] — delete a backend (Redis) session
// After the backend extracts memories into Redis, we persist them to DB.
export async function DELETE(
  _req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { id } = await params;

  // This triggers memory extraction + saves to Redis, then deletes the session
  await fetch(`${backendUrl}/session/${id}`, { method: "DELETE" });

  // Pull the updated memory from Redis and persist to DB
  try {
    const memRes = await fetch(`${backendUrl}/memory`);
    if (memRes.ok) {
      const memory = (await memRes.json()) as Record<string, string>;
      for (const category of VALID_CATEGORIES) {
        const content = (memory[category] ?? "").trim();
        if (content) {
          await prisma.userMemory.upsert({
            where: {
              userId_category: { userId: session.user.id, category },
            },
            create: { userId: session.user.id, category, content },
            update: { content },
          });
        }
      }
    }
  } catch {
    // Non-fatal — memory will be captured on next sync
  }

  return new Response(null, { status: 204 });
}
