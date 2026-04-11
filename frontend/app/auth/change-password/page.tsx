import { redirect } from "next/navigation";

export default function ChangePasswordPage() {
  redirect("/settings#security");
}
