import Link from "next/link";
import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { ArrowLeft } from "lucide-react";

import { authOptions } from "@/lib/auth";
import { SiteHeader } from "@/components/site-header";
import { Button } from "@/components/ui/button";
import { SettingsClient } from "@/components/settings/settings-client";
import { fetchOnboarding } from "@/lib/onboarding";
import { EMPTY_ONBOARDING } from "@/lib/onboarding-types";

export const dynamic = "force-dynamic";

export default async function SettingsPage() {
  const session = await getServerSession(authOptions);
  if (!session) {
    redirect("/login");
  }
  if (!session.user.roles.includes("jobseeker")) {
    redirect("/");
  }

  const initial = (await fetchOnboarding()) ?? EMPTY_ONBOARDING;

  return (
    <>
      <SiteHeader>
        <Button asChild variant="ghost" size="sm">
          <Link href="/">
            <ArrowLeft aria-hidden /> Home
          </Link>
        </Button>
      </SiteHeader>
      <SettingsClient initial={initial} />
    </>
  );
}
