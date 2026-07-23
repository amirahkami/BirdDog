import Link from "next/link";
import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";

import { authOptions } from "@/lib/auth";

import { AdminStatus } from "./status";

export const dynamic = "force-dynamic";

export default async function AdminPage() {
  const session = await getServerSession(authOptions);
  if (!session) {
    redirect("/login");
  }
  if (!session.user.roles.includes("admin")) {
    redirect("/");
  }

  return (
    <main>
      <nav className="topbar" aria-label="Admin navigation">
        <Link href="/">← BirdDog</Link>
        <strong>Admin dashboard</strong>
      </nav>
      <AdminStatus />
    </main>
  );
}
