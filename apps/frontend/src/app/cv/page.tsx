import Link from "next/link";
import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { authOptions } from "@/lib/auth";
import { SiteHeader } from "@/components/site-header";
import { Button } from "@/components/ui/button";
import { CvReplace } from "@/components/cv/cv-replace";
import { CvFacts } from "@/components/cv-facts";

export const dynamic = "force-dynamic";

export default async function CvPage() {
  const session = await getServerSession(authOptions);
  if (!session) {
    redirect("/login");
  }
  if (!session.user.roles.includes("jobseeker")) {
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
      <main className="mx-auto w-full max-w-5xl px-4 pb-24 pt-8 sm:px-6">
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          Your CV
        </h1>
        <div className="mt-6 grid gap-4 lg:grid-cols-[320px_minmax(0,1fr)] lg:items-start">
          <CvReplace />
          <CvFacts />
        </div>
      </main>
    </>
  );
}
