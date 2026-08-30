import Link from "next/link";
import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { authOptions } from "@/lib/auth";
import { SiteHeader } from "@/components/site-header";
import { Button } from "@/components/ui/button";

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
    <>
      <SiteHeader>
        <Button asChild variant="ghost" size="sm">
          <Link href="/">
            <ArrowLeft aria-hidden /> Home
          </Link>
        </Button>
      </SiteHeader>

      <main className="mx-auto w-full max-w-5xl px-4 pb-24 pt-10 sm:px-6">
        <AdminStatus />
      </main>
    </>
  );
}
