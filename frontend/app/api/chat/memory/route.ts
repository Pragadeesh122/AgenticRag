import { auth } from "@/auth";
import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

const VALID_CATEGORIES = [
  "work_context",
  "personal_context",
  "top_of_mind",
  "preferences",
];

/** Push the full memory state to Redis cache via the Python backend. */
async function syncToRedis(
  memories: { category: string; content: string }[]
): Promise<void> {
  try {
    await fetch(`${backendUrl}/memory/sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ memories }),
    });
  } catch {
    // Redis sync failure is non-fatal — DB is the source of truth
  }
}

// GET /api/chat/memory — fetch all memory categories from DB
export async function GET() {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const rows = await prisma.userMemory.findMany({
    where: { userId: session.user.id },
  });

  const memory: Record<string, string> = {};
  for (const cat of VALID_CATEGORIES) {
    memory[cat] = rows.find((r) => r.category === cat)?.content ?? "";
  }

  return NextResponse.json(memory);
}

// PUT /api/chat/memory — upsert a single category to DB + sync Redis
export async function PUT(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { category, content } = await req.json();
  if (!VALID_CATEGORIES.includes(category)) {
    return NextResponse.json(
      { error: `Invalid category: ${category}` },
      { status: 400 }
    );
  }

  const trimmed = (content ?? "").trim();

  if (trimmed) {
    await prisma.userMemory.upsert({
      where: {
        userId_category: { userId: session.user.id, category },
      },
      create: { userId: session.user.id, category, content: trimmed },
      update: { content: trimmed },
    });
  } else {
    // Empty content = delete the category
    await prisma.userMemory.deleteMany({
      where: { userId: session.user.id, category },
    });
  }

  // Sync full memory to Redis cache
  const allMemories = await prisma.userMemory.findMany({
    where: { userId: session.user.id },
  });
  await syncToRedis(
    allMemories.map((m) => ({ category: m.category, content: m.content }))
  );

  return NextResponse.json({ status: "updated", category });
}

// DELETE /api/chat/memory — delete a category from DB + sync Redis
export async function DELETE(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { searchParams } = new URL(req.url);
  const category = searchParams.get("category");
  if (!category || !VALID_CATEGORIES.includes(category)) {
    return NextResponse.json(
      { error: "Invalid or missing category" },
      { status: 400 }
    );
  }

  await prisma.userMemory.deleteMany({
    where: { userId: session.user.id, category },
  });

  // Sync remaining memory to Redis
  const remaining = await prisma.userMemory.findMany({
    where: { userId: session.user.id },
  });
  await syncToRedis(
    remaining.map((m) => ({ category: m.category, content: m.content }))
  );

  return NextResponse.json({ status: "deleted", category });
}
