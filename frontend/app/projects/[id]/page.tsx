import { auth } from "@/auth";
import { redirect, notFound } from "next/navigation";
import ProjectPage from "@/components/ProjectPage";
import { prisma } from "@/lib/prisma";

export default async function ProjectDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const session = await auth();
  if (!session?.user?.id) {
    redirect("/auth/signin");
  }

  const { id } = await params;

  // Server-side fetch to utilize loading.tsx and SSR
  const [project, chatSessions] = await Promise.all([
    prisma.project.findFirst({
      where: { id, userId: session.user.id },
      include: { documents: { orderBy: { createdAt: "desc" } } },
    }),
    prisma.chatSession.findMany({
      where: { userId: session.user.id, projectId: id },
      orderBy: { updatedAt: "desc" },
      select: {
        id: true,
        backendSessionId: true,
        title: true,
        createdAt: true,
        updatedAt: true,
      },
    })
  ]);

  if (!project) notFound();

  // Convert Prisma Date objects to ISO strings for the Client Component prop boundary
  const serializedProject = {
    ...project,
    createdAt: project.createdAt.toISOString(),
    updatedAt: project.updatedAt.toISOString(),
    documents: project.documents.map((d) => ({
      ...d,
      createdAt: d.createdAt.toISOString(),
    })),
  };

  const serializedSessions = chatSessions.map((s) => ({
    ...s,
    createdAt: s.createdAt.toISOString(),
    updatedAt: s.updatedAt.toISOString(),
  }));

  return (
    <ProjectPage
      initialProject={serializedProject as any}
      initialSessions={serializedSessions as any}
      projectId={id}
      user={{
        name: session.user.name,
        email: session.user.email,
        image: session.user.image,
      }}
    />
  );
}
