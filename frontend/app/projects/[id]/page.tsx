import { notFound, redirect } from "next/navigation";
import ProjectPage from "@/components/ProjectPage";
import {
  fetchCurrentUserServer,
  fetchProjectServer,
  fetchProjectSessionsServer,
} from "@/lib/server-api";

interface ProjectDetailPageProps {
  params: Promise<{ id: string }>;
}

export default async function ProjectDetailPage({
  params,
}: ProjectDetailPageProps) {
  const { id } = await params;
  const user = await fetchCurrentUserServer();

  if (!user) {
    redirect("/auth/signin");
  }

  const project = await fetchProjectServer(id);
  if (!project) {
    notFound();
  }

  const sessions = await fetchProjectSessionsServer(id);

  return (
    <ProjectPage
      initialProject={project}
      initialSessions={sessions}
      projectId={id}
      user={{
        name: user.name || "",
        email: user.email || "",
        image: user.image || "",
      }}
    />
  );
}
