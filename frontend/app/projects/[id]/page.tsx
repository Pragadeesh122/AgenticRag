"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { redirect, notFound } from "next/navigation";
import { useParams } from "next/navigation";
import ProjectPage from "@/components/ProjectPage";
import { fetchProject, fetchProjectSessions } from "@/lib/api";
import { Session, Project } from "@/lib/types";

export default function ProjectDetailPage() {
  const { user, isLoading } = useAuth();
  const { id } = useParams<{ id: string }>();

  const [project, setProject] = useState<Project | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [dataLoaded, setDataLoaded] = useState(false);
  const [errorStatus, setErrorStatus] = useState<number | null>(null);

  useEffect(() => {
    if (user && !isLoading) {
      Promise.all([fetchProject(id), fetchProjectSessions(id)])
        .then(([fetchedProject, fetchedSessions]) => {
          setProject(fetchedProject);
          setSessions(fetchedSessions);
          setDataLoaded(true);
        })
        .catch(() => {
          setErrorStatus(404);
        });
    } else if (!user && !isLoading) {
      redirect("/auth/signin"); // Or standard landing
    }
  }, [user, isLoading, id]);

  if (errorStatus === 404) {
    notFound();
  }

  if (isLoading || !dataLoaded || !project || !user) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-[#1a1a1a]">
        <div className="w-8 h-8 rounded-full border-2 border-zinc-700 border-t-violet-500 animate-spin" />
      </div>
    );
  }

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
