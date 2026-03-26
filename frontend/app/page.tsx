import { auth } from "@/auth";
import { redirect } from "next/navigation";
import ChatPage from "@/components/ChatPage";

export default async function Home() {
  const session = await auth();

  if (!session?.user) {
    redirect("/auth/signin");
  }

  return (
    <ChatPage
      user={{
        name: session.user.name,
        email: session.user.email,
        image: session.user.image,
      }}
    />
  );
}
