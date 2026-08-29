import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";

import { authOptions } from "@/lib/auth";
import { SiteHeader } from "@/components/site-header";
import { OnboardingWizard } from "@/components/onboarding/onboarding-wizard";
import { fetchOnboarding } from "@/lib/onboarding";
import { EMPTY_ONBOARDING, isOnboardingComplete } from "@/lib/onboarding-types";

export const dynamic = "force-dynamic";

export default async function OnboardingPage() {
  const session = await getServerSession(authOptions);
  if (!session) {
    redirect("/login");
  }

  const initial = (await fetchOnboarding()) ?? EMPTY_ONBOARDING;
  if (isOnboardingComplete(initial)) {
    redirect("/");
  }

  return (
    <>
      <SiteHeader />
      <main>
        <OnboardingWizard initial={initial} />
      </main>
    </>
  );
}
