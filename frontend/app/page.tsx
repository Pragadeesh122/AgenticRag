import { auth } from "@/auth";
import ChatPage from "@/components/ChatPage";
import LandingPage from "@/components/LandingPage";

export default async function Home() {
  const session = await auth();

  if (session?.user) {
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

  return <LandingPage />;
}
