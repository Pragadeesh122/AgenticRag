import { redirect } from "next/navigation";
import ChatPage from "@/components/ChatPage";
import {
  fetchCurrentUserServer,
  fetchProjectsServer,
  fetchSessionsServer,
} from "@/lib/server-api";

export default async function ChatDashboard() {
  const user = await fetchCurrentUserServer();

  if (!user) {
    redirect("/auth/signin");
  }

  const [sessionsResult, projectsResult] = await Promise.allSettled([
    fetchSessionsServer(),
    fetchProjectsServer(),
  ]);

  const sessions =
    sessionsResult.status === "fulfilled" ? sessionsResult.value : [];
  const projects =
    projectsResult.status === "fulfilled" ? projectsResult.value : [];

  return (
    <ChatPage
      initialSessions={sessions}
      initialProjects={projects}
      renderedAt={new Date().toISOString()}
      user={{
        name: user.name || "",
        email: user.email || "",
        image: user.image || "",
      }}
    />
  );
}
