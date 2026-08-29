import { getAccessToken } from "@/lib/session-token";
import type { OnboardingState } from "@/lib/onboarding-types";

/** Server-side fetch of the current user's onboarding state from the backend. */
export async function fetchOnboarding(): Promise<OnboardingState | null> {
  const token = await getAccessToken();
  if (!token) {
    return null;
  }

  const apiBaseUrl = process.env.API_INTERNAL_URL ?? "http://api:8000";
  try {
    const response = await fetch(`${apiBaseUrl}/onboarding`, {
      cache: "no-store",
      headers: { authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      return null;
    }
    return (await response.json()) as OnboardingState;
  } catch {
    return null;
  }
}
