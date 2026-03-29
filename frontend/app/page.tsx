import { auth } from "@/auth";
import ChatPage from "@/components/ChatPage";
import LandingPage from "@/components/LandingPage";
import { prisma } from "@/lib/prisma";

export default async function Home() {
  const session = await auth();

  if (session?.user?.id) {
    const [chatSessions, projects] = await Promise.all([
      prisma.chatSession.findMany({
        where: { userId: session.user.id, projectId: null },
        orderBy: { updatedAt: "desc" },
        select: {
          id: true,
          backendSessionId: true,
          title: true,
          createdAt: true,
          updatedAt: true,
        },
      }),
      prisma.project.findMany({
        where: { userId: session.user.id },
        orderBy: { updatedAt: "desc" },
        include: { documents: { orderBy: { createdAt: "desc" } } },
      }),
    ]);

    const serializedSessions = chatSessions.map((s) => ({
      ...s,
      createdAt: s.createdAt.toISOString(),
      updatedAt: s.updatedAt.toISOString(),
    }));

    const serializedProjects = projects.map((p) => ({
      ...p,
      createdAt: p.createdAt.toISOString(),
      updatedAt: p.updatedAt.toISOString(),
      documents: p.documents.map((d) => ({
        ...d,
        createdAt: d.createdAt.toISOString(),
      })),
    }));

    return (
      <ChatPage
        initialSessions={serializedSessions as any}
        initialProjects={serializedProjects as any}
        user={{
          name: session.user.name,
          email: session.user.email,
          image: session.user.image,
        }}
      />
    );
  }

  return <LandingPage />;
}
