import Link from "next/link";
import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { Sparkles } from "lucide-react";

import { authOptions } from "@/lib/auth";
import { SiteHeader } from "@/components/site-header";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

import { SignOutButton } from "./sign-out-button";

export const dynamic = "force-dynamic";

export default async function Home() {
  const session = await getServerSession(authOptions);
  if (!session) {
    redirect("/login");
  }

  const isAdmin = session.user.roles.includes("admin");

  return (
    <>
      <SiteHeader>
        {isAdmin ? (
          <Button asChild variant="ghost" size="sm">
            <Link href="/admin">Admin</Link>
          </Button>
        ) : null}
        <SignOutButton />
      </SiteHeader>

      <main className="mx-auto w-full max-w-3xl px-4 pb-24 pt-10">
        <p className="mb-3 inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-ai">
          <Sparkles className="size-3.5" aria-hidden /> Private workspace
        </p>
        <h1 className="text-balance text-4xl font-bold leading-[1.1] tracking-tight text-foreground sm:text-5xl">
          The job search that reads before you apply.
        </h1>
        <p className="mt-5 max-w-prose text-base leading-relaxed text-muted-foreground">
          Signed in as{" "}
          <span className="font-semibold text-foreground">
            {session.user.username}
          </span>
          . BirdDog collects focused roles, removes the noise, and explains which
          ones fit your CV — so you can move with confidence.
        </p>

        <Card className="mt-8">
          <CardContent className="p-5">
            <p className="text-sm font-semibold text-foreground">
              Your matches aren&apos;t ready yet
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              Once onboarding and pool building are complete, your personalized
              matches will appear here — each one with a clear reason it fits.
            </p>
          </CardContent>
        </Card>
      </main>
    </>
  );
}
