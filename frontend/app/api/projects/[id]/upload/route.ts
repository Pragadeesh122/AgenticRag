import {NextResponse} from "next/server";
import {auth} from "@/auth";
import {prisma} from "@/lib/prisma";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

// POST /api/projects/[id]/upload — create document record + get presigned URL
export async function POST(
  req: Request,
  {params}: {params: Promise<{id: string}>}
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({error: "Unauthorized"}, {status: 401});
  }

  const {id: projectId} = await params;

  const project = await prisma.project.findFirst({
    where: {id: projectId, userId: session.user.id},
    select: {id: true},
  });

  if (!project) {
    return NextResponse.json({error: "Project not found"}, {status: 404});
  }

  const body = await req.json();
  const {filename, fileSize} = body as {filename: string; fileSize: number};

  if (!filename) {
    return NextResponse.json({error: "No filename provided"}, {status: 400});
  }

  const ext = filename.split(".").pop()?.toLowerCase() || "";
  const supportedTypes = ["pdf", "txt", "md", "csv", "docx"];

  if (!supportedTypes.includes(ext)) {
    return NextResponse.json(
      {error: `Unsupported file type: ${ext}`},
      {status: 400}
    );
  }

  const document = await prisma.document.create({
    data: {
      projectId,
      filename,
      fileType: ext,
      fileSize: fileSize || 0,
      status: "uploading",
    },
  });

  try {
    const presignRes = await fetch(
      `${BACKEND_URL}/projects/${projectId}/presign`,
      {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({document_id: document.id, filename}),
      }
    );

    if (!presignRes.ok) {
      const err = await presignRes.text();
      await prisma.document.update({
        where: {id: document.id},
        data: {status: "failed", errorMessage: err},
      });
      return NextResponse.json(
        {error: "Failed to get upload URL", detail: err},
        {status: 502}
      );
    }

    const {url} = await presignRes.json();

    return NextResponse.json({...document, uploadUrl: url}, {status: 201});
  } catch {
    await prisma.document.update({
      where: {id: document.id},
      data: {status: "failed", errorMessage: "Backend unreachable"},
    });
    return NextResponse.json({error: "Backend unreachable"}, {status: 502});
  }
}

// PUT /api/projects/[id]/upload — confirm upload complete, trigger ingestion
export async function PUT(
  req: Request,
  {params}: {params: Promise<{id: string}>}
) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({error: "Unauthorized"}, {status: 401});
  }

  const {id: projectId} = await params;

  const body = await req.json();
  const {documentId, filename} = body as {documentId: string; filename: string};

  if (!documentId || !filename) {
    return NextResponse.json(
      {error: "documentId and filename are required"},
      {status: 400}
    );
  }

  await prisma.document.update({
    where: {id: documentId},
    data: {status: "processing"},
  });

  try {
    const res = await fetch(`${BACKEND_URL}/projects/${projectId}/ingest`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({document_id: documentId, filename}),
    });

    if (!res.ok) {
      const err = await res.text();
      await prisma.document.update({
        where: {id: documentId},
        data: {status: "failed", errorMessage: err},
      });
      return NextResponse.json({error: "Ingestion failed", detail: err}, {status: 502});
    }

    return NextResponse.json({status: "processing"});
  } catch {
    await prisma.document.update({
      where: {id: documentId},
      data: {status: "failed", errorMessage: "Backend unreachable"},
    });
    return NextResponse.json({error: "Backend unreachable"}, {status: 502});
  }
}
