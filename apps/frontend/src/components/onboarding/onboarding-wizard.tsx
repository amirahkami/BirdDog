"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Check, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import { PreferencesStep } from "@/components/onboarding/preferences-step";
import { CvStep } from "@/components/onboarding/cv-step";
import type { OnboardingState, OnboardingSteps } from "@/lib/onboarding-types";

const STEPS = [
  { key: "role", label: "Role" },
  { key: "preferences", label: "Preferences" },
  { key: "cv", label: "CV" },
] as const;

type StepKey = (typeof STEPS)[number]["key"] | "done";

export function OnboardingWizard({ initial }: { initial: OnboardingState }) {
  const [state, setState] = React.useState(initial);
  const router = useRouter();

  const current: StepKey = !state.steps.role
    ? "role"
    : !state.steps.preferences
      ? "preferences"
      : !state.steps.cv
        ? "cv"
        : "done";

  React.useEffect(() => {
    if (current === "done") {
      router.replace("/");
    }
  }, [current, router]);

  return (
    <div className="mx-auto w-full max-w-2xl px-4 pb-24 pt-8 sm:px-6">
      <Stepper current={current} steps={state.steps} />

      <div className="mt-8">
        {current === "role" && (
          <RoleStep value={state.desired_role ?? ""} onSaved={setState} />
        )}
        {current === "preferences" && (
          <PreferencesStep initial={state} onSaved={setState} />
        )}
        {current === "cv" && <CvStep />}
        {current === "done" && (
          <p className="text-sm text-muted-foreground">Finishing up…</p>
        )}
      </div>
    </div>
  );
}

function Stepper({
  current,
  steps,
}: {
  current: StepKey;
  steps: OnboardingSteps;
}) {
  return (
    <ol className="flex items-center gap-2">
      {STEPS.map((step, index) => {
        const done = steps[step.key];
        const active = current === step.key;
        return (
          <li key={step.key} className="flex flex-1 items-center gap-2">
            <span
              className={cn(
                "grid size-7 shrink-0 place-items-center rounded-full text-xs font-semibold",
                done
                  ? "bg-match text-match-foreground"
                  : active
                    ? "bg-ai text-ai-foreground"
                    : "bg-secondary text-muted-foreground"
              )}
            >
              {done ? <Check className="size-4" /> : index + 1}
            </span>
            <span
              className={cn(
                "hidden text-xs font-medium sm:inline",
                active || done ? "text-foreground" : "text-muted-foreground"
              )}
            >
              {step.label}
            </span>
            {index < STEPS.length - 1 && (
              <span className="ml-1 h-px flex-1 bg-border" />
            )}
          </li>
        );
      })}
    </ol>
  );
}

function RoleStep({
  value,
  onSaved,
}: {
  value: string;
  onSaved: (state: OnboardingState) => void;
}) {
  const [role, setRole] = React.useState(value);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const valid = role.trim().length >= 2;

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!valid || saving) return;
    setSaving(true);
    setError(null);
    try {
      const response = await fetch("/api/onboarding/role", {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ desired_role: role.trim() }),
      });
      if (!response.ok) throw new Error("save failed");
      onSaved((await response.json()) as OnboardingState);
    } catch {
      setError("Couldn't save that. Please try again.");
      setSaving(false);
    }
  }

  return (
    <form onSubmit={submit} noValidate>
      <h1 className="text-2xl font-bold tracking-tight text-foreground">
        What role are you after?
      </h1>
      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
        In your own words. This is the anchor for your matches — you can refine
        it later.
      </p>

      <div className="mt-6 space-y-2">
        <Label htmlFor="role">Desired role</Label>
        <Input
          id="role"
          value={role}
          onChange={(event) => setRole(event.target.value)}
          placeholder="e.g. Senior Frontend Engineer"
          maxLength={255}
          autoFocus
        />
      </div>

      {error ? (
        <p className="mt-3 text-sm text-destructive">{error}</p>
      ) : null}

      <Button
        type="submit"
        size="lg"
        className="mt-6 w-full"
        disabled={!valid || saving}
      >
        {saving ? (
          <>
            <Loader2 className="animate-spin" /> Saving…
          </>
        ) : (
          <>
            Continue <ArrowRight />
          </>
        )}
      </Button>
    </form>
  );
}

