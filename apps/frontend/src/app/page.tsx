import Link from "next/link";
import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { Radar } from "lucide-react";

import { authOptions } from "@/lib/auth";
import { SiteHeader } from "@/components/site-header";
import { Button } from "@/components/ui/button";
import { fetchOnboarding } from "@/lib/onboarding";
import { isOnboardingComplete } from "@/lib/onboarding-types";

import { SignOutButton } from "./sign-out-button";

export const dynamic = "force-dynamic";

export default async function Home() {
  const session = await getServerSession(authOptions);
  if (!session) {
    redirect("/login");
  }

  const isAdmin = session.user.roles.includes("admin");
  const isJobseeker = session.user.roles.includes("jobseeker");

  // Gate: send jobseekers who haven't finished onboarding into the wizard.
  if (isJobseeker) {
    const onboarding = await fetchOnboarding();
    if (onboarding && !isOnboardingComplete(onboarding)) {
      redirect("/onboarding");
    }
  }

  return (
    <>
      <SiteHeader>
        {isAdmin ? (
          <Button asChild variant="ghost" size="sm">
            <Link href="/admin">Admin</Link>
          </Button>
        ) : null}
        {isJobseeker ? (
          <Button asChild variant="ghost" size="sm">
            <Link href="/cv">CV</Link>
          </Button>
        ) : null}
        {isJobseeker ? (
          <Button asChild variant="ghost" size="sm">
            <Link href="/settings">Settings</Link>
          </Button>
        ) : null}
        <SignOutButton />
      </SiteHeader>

      <main className="mx-auto flex min-h-[calc(100dvh-3.5rem)] w-full max-w-2xl items-center justify-center px-4 pb-16 sm:px-6">
        <div className="w-full text-center">
          <div className="mx-auto grid size-14 place-items-center rounded-2xl bg-ai-soft text-ai">
            <Radar className="size-7" aria-hidden />
          </div>

          <p className="mt-6 t-eyebrow text-ai">Private workspace</p>
          <h1 className="mt-2 t-h1 text-foreground">
            Your matches are on the way
          </h1>
          <p className="mx-auto mt-3 max-w-md t-lead text-muted-foreground">
            Signed in as{" "}
            <span className="font-semibold text-foreground">
              {session.user.username}
            </span>
            . BirdDog collects focused roles and explains which ones fit your CV —
            each match with a clear reason. They&apos;ll appear here.
          </p>

          {isJobseeker ? (
            <div className="mt-7 flex flex-wrap justify-center gap-2">
              <Button asChild variant="secondary">
                <Link href="/cv">View your CV</Link>
              </Button>
              <Button asChild variant="ghost">
                <Link href="/settings">Edit preferences</Link>
              </Button>
            </div>
          ) : null}
        </div>
      </main>
    </>
  );
}
