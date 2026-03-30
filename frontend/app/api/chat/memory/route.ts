import { auth } from "@/auth";
import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8000";

// Maps frontend snake_case keys ↔ DB camelCase columns
const CATEGORY_TO_COLUMN: Record<string, string> = {
  work_context: "workContext",
  personal_context: "personalContext",
  top_of_mind: "topOfMind",
  preferences: "preferences",
};

const EMPTY_MEMORY: Record<string, string> = {
  work_context: "",
  personal_context: "",
  top_of_mind: "",
  preferences: "",
};

/** Push the full memory state to Redis cache via the Python backend. */
async function syncToRedis(
  userId: string,
  memory: Record<string, string>
): Promise<void> {
  const memories = Object.entries(memory)
    .filter(([, v]) => v.trim())
    .map(([category, content]) => ({ category, content }));
  try {
    await fetch(`${backendUrl}/memory/sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId, memories }),
    });
  } catch {
    // Non-fatal — DB is source of truth
  }
}

/** Read the single UserMemory row and return as snake_case record. */
async function readMemory(
  userId: string
): Promise<Record<string, string>> {
  const row = await prisma.userMemory.findUnique({
    where: { userId },
  });
  if (!row) return { ...EMPTY_MEMORY };
  return {
    work_context: row.workContext ?? "",
    personal_context: row.personalContext ?? "",
    top_of_mind: row.topOfMind ?? "",
    preferences: row.preferences ?? "",
  };
}

// GET /api/chat/memory
export async function GET() {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const memory = await readMemory(session.user.id);
    return NextResponse.json(memory);
  } catch {
    return NextResponse.json(EMPTY_MEMORY);
  }
}

// PUT /api/chat/memory — update a single category
export async function PUT(req: NextRequest) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const { category, content } = await req.json();
  const column = CATEGORY_TO_COLUMN[category];
  if (!column) {
    return NextResponse.json(
      { error: `Invalid category: ${category}` },
      { status: 400 }
    );
  }

  try {
    const userId = session.user.id;
    const trimmed = (content ?? "").trim() || null;

    await prisma.userMemory.upsert({
      where: { userId },
      create: { userId, [column]: trimmed },
      update: { [column]: trimmed },
    });

    const memory = await readMemory(userId);
    await syncToRedis(userId, memory);

    return NextResponse.json({ status: "updated", category });
  } catch (e) {
    return NextResponse.json(
      { error: e instanceof Error ? e.message : "Failed to update memory" },
      { status: 500 }
    );
  }
}
