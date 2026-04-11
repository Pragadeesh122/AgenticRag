import { redirect } from "next/navigation";

import SettingsPage from "@/components/SettingsPage";
import { fetchCurrentUserServer } from "@/lib/server-api";

export default async function SettingsRoute() {
  const user = await fetchCurrentUserServer();

  if (!user) {
    redirect("/auth/signin");
  }

  return <SettingsPage user={user} />;
}
