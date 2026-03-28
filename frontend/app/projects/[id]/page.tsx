import { auth } from "@/auth";
import { redirect } from "next/navigation";
import ProjectPage from "@/components/ProjectPage";

export default async function ProjectDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const session = await auth();
  if (!session?.user) {
    redirect("/auth/signin");
  }

  const { id } = await params;

  return (
    <ProjectPage
      projectId={id}
      user={{
        name: session.user.name,
        email: session.user.email,
        image: session.user.image,
      }}
    />
  );
}
