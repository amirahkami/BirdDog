export type OnboardingStatus = "incomplete" | "processing" | "ready" | "error";

export type OnboardingSteps = {
  role: boolean;
  preferences: boolean;
  cv: boolean;
};

export type CvStatus = {
  id: string;
  original_filename: string;
  byte_size: number;
  page_count: number | null;
  detected_language: "de" | "en" | "other" | null;
  extraction_status: "pending" | "processing" | "ready" | "error";
  extraction_method: "native" | "ocr" | "mixed" | null;
  extraction_error_code: string | null;
  facts_status: "pending" | "queued" | "ready" | "review" | "error";
  created_at: string;
};

export type OnboardingState = {
  status: OnboardingStatus;
  desired_role: string | null;
  home_label: string | null;
  home_city: string | null;
  home_country_code: string | null;
  home_latitude: number | null;
  home_longitude: number | null;
  travel_radius_km: number | null;
  accepts_onsite: boolean;
  accepts_hybrid: boolean;
  accepts_remote: boolean;
  accepts_full_time: boolean;
  accepts_part_time: boolean;
  steps: OnboardingSteps;
  cv: CvStatus | null;
};

export const EMPTY_ONBOARDING: OnboardingState = {
  status: "incomplete",
  desired_role: null,
  home_label: null,
  home_city: null,
  home_country_code: null,
  home_latitude: null,
  home_longitude: null,
  travel_radius_km: null,
  accepts_onsite: false,
  accepts_hybrid: false,
  accepts_remote: false,
  accepts_full_time: true,
  accepts_part_time: false,
  steps: { role: false, preferences: false, cv: false },
  cv: null,
};

export function isOnboardingComplete(state: OnboardingState): boolean {
  return state.steps.role && state.steps.preferences && state.steps.cv;
}
