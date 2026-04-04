"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { redirect } from "next/navigation";
import ChatPage from "@/components/ChatPage";
import { fetchProjects, fetchSessions } from "@/lib/api";
import { Session, Project } from "@/lib/types";

export default function ChatDashboard() {
  const { user, isLoading } = useAuth();
  
  const [sessions, setSessions] = useState<Session[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [dataLoaded, setDataLoaded] = useState(false);

  useEffect(() => {
    if (user && !isLoading) {
      Promise.all([fetchSessions(), fetchProjects()])
        .then(([fetchedSessions, fetchedProjects]) => {
          setSessions(fetchedSessions);
          setProjects(fetchedProjects);
          setDataLoaded(true);
        })
        .catch(console.error);
    } else if (!user && !isLoading) {
      redirect("/auth/signin");
    }
  }, [user, isLoading]);

  if (isLoading || !dataLoaded || !user) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-[#1a1a1a]">
        <div className="w-8 h-8 rounded-full border-2 border-zinc-700 border-t-violet-500 animate-spin" />
      </div>
    );
  }

  return (
    <ChatPage
      initialSessions={sessions}
      initialProjects={projects}
      user={{
        name: user.name || "",
        email: user.email || "",
        image: user.image || "",
      }}
    />
  );
}
