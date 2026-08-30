"use client";

import * as React from "react";
import { CheckCircle2, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PreferencesStep } from "@/components/onboarding/preferences-step";
import type { OnboardingState } from "@/lib/onboarding-types";

export function SettingsClient({ initial }: { initial: OnboardingState }) {
  const [state, setState] = React.useState(initial);
  const [toast, setToast] = React.useState<string | null>(null);
  const timer = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  const saved = (label: string) => (next: OnboardingState) => {
    setState(next);
    setToast(label);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => setToast(null), 2500);
  };

  return (
    <main className="mx-auto w-full max-w-5xl px-4 pb-24 pt-8 sm:px-6">
      <h1 className="t-h1 text-foreground">Settings</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Update anything below — changes save on their own button.
      </p>

      <div className="mt-4 divide-y divide-border">
        <SettingsRow
          title="Desired role"
          description="The role your matches are anchored on."
        >
          <RoleFields role={state.desired_role ?? ""} onSaved={saved("Role saved")} />
        </SettingsRow>

        <SettingsRow
          title="Preferences"
          description="These shape which jobs you'll be matched with — work mode, location, and countries."
        >
          <PreferencesStep
            initial={state}
            onSaved={saved("Preferences saved")}
            submitLabel="Save preferences"
            hideHeader
          />
        </SettingsRow>
      </div>

      {toast ? (
        <div className="fixed inset-x-0 bottom-6 z-40 flex justify-center px-4">
          <div className="inline-flex items-center gap-2 rounded-full bg-match px-4 py-2 text-sm font-semibold text-match-foreground shadow-lg">
            <CheckCircle2 className="size-4" />
            {toast}
          </div>
        </div>
      ) : null}
    </main>
  );
}

function SettingsRow({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <section className="grid gap-x-10 gap-y-4 py-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
      <div>
        <h2 className="t-h2 text-foreground">{title}</h2>
        <p className="mt-1 text-sm leading-relaxed text-muted-foreground">
          {description}
        </p>
      </div>
      <div className="min-w-0">{children}</div>
    </section>
  );
}

function RoleFields({
  role,
  onSaved,
}: {
  role: string;
  onSaved: (state: OnboardingState) => void;
}) {
  const [value, setValue] = React.useState(role);
  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const valid = value.trim().length >= 2;

  async function save() {
    if (!valid || saving) return;
    setSaving(true);
    setError(null);
    try {
      const res = await fetch("/api/onboarding/role", {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ desired_role: value.trim() }),
      });
      if (!res.ok) throw new Error();
      const data = (await res.json()) as OnboardingState;
      setSaving(false);
      onSaved(data);
    } catch {
      setError("Couldn't save. Please try again.");
      setSaving(false);
    }
  }

  return (
    <div>
      <div className="flex gap-2">
        <Input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          maxLength={255}
          aria-label="Desired role"
          className="flex-1"
        />
        <Button
          type="button"
          onClick={save}
          disabled={!valid || saving || value.trim() === role}
        >
          {saving ? <Loader2 className="animate-spin" /> : "Save"}
        </Button>
      </div>
      {error ? <p className="mt-2 text-sm text-destructive">{error}</p> : null}
    </div>
  );
}
