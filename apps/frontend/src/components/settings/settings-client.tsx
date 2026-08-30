"use client";

import * as React from "react";
import { CheckCircle2, FileText, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent } from "@/components/ui/card";
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
    <main className="mx-auto w-full max-w-md px-4 pb-24 pt-8">
      <h1 className="text-2xl font-bold tracking-tight text-foreground">Settings</h1>
      <p className="mt-2 text-sm text-muted-foreground">
        Update anything below — changes save on their own button.
      </p>

      <div className="mt-8 space-y-12">
        <RoleSection role={state.desired_role ?? ""} onSaved={saved("Role saved")} />

        <section>
          <h2 className="mb-4 text-lg font-semibold text-foreground">Preferences</h2>
          <PreferencesStep
            initial={state}
            onSaved={saved("Preferences saved")}
            submitLabel="Save preferences"
          />
        </section>

        <CvSection state={state} onSaved={saved("CV replaced")} />
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

function RoleSection({
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
    <section>
      <h2 className="mb-4 text-lg font-semibold text-foreground">Desired role</h2>
      <Label htmlFor="settings-role" className="mb-2 block">
        The role your matches are anchored on
      </Label>
      <div className="flex gap-2">
        <Input
          id="settings-role"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          maxLength={255}
          className="flex-1"
        />
        <Button type="button" onClick={save} disabled={!valid || saving || value.trim() === role}>
          {saving ? <Loader2 className="animate-spin" /> : "Save"}
        </Button>
      </div>
      {error ? <p className="mt-2 text-sm text-destructive">{error}</p> : null}
    </section>
  );
}

const MAX_BYTES = 25 * 1024 * 1024;

function CvSection({
  state,
  onSaved,
}: {
  state: OnboardingState;
  onSaved: (state: OnboardingState) => void;
}) {
  const [file, setFile] = React.useState<File | null>(null);
  const [uploading, setUploading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  function pick(candidate: File | null) {
    setError(null);
    if (!candidate) {
      setFile(null);
      return;
    }
    const isPdf =
      candidate.type === "application/pdf" ||
      candidate.name.toLowerCase().endsWith(".pdf");
    if (!isPdf) {
      setError("Please choose a PDF file.");
      return;
    }
    if (candidate.size > MAX_BYTES) {
      setError("That file is larger than 25 MB.");
      return;
    }
    setFile(candidate);
  }

  async function upload() {
    if (!file || uploading) return;
    setUploading(true);
    setError(null);
    try {
      const body = new FormData();
      body.append("file", file);
      const res = await fetch("/api/onboarding/cv", { method: "POST", body });
      if (!res.ok) {
        let message = "Upload failed. Please try again.";
        try {
          const detail = (await res.json())?.detail;
          if (detail?.message) message = detail.message;
        } catch {
          // ignore
        }
        throw new Error(message);
      }
      const data = (await res.json()) as OnboardingState;
      setFile(null);
      setUploading(false);
      onSaved(data);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Upload failed.");
      setUploading(false);
    }
  }

  return (
    <section>
      <h2 className="mb-4 text-lg font-semibold text-foreground">CV</h2>
      {state.cv ? (
        <Card className="mb-3">
          <CardContent className="flex items-center gap-3 p-4">
            <FileText className="size-5 shrink-0 text-ai" />
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-foreground">
                {state.cv.original_filename}
              </p>
              <p className="text-sm text-muted-foreground">
                {state.cv.extraction_status === "ready"
                  ? "Processed"
                  : state.cv.extraction_status === "error"
                    ? "Couldn't be read"
                    : "Processing…"}
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <p className="mb-3 text-sm text-muted-foreground">No CV uploaded yet.</p>
      )}

      <div className="flex gap-2">
        <label className="flex flex-1 cursor-pointer items-center gap-2 rounded-lg border border-dashed border-border bg-card px-3 py-2 text-sm text-muted-foreground transition-colors hover:border-ai">
          <input
            type="file"
            accept="application/pdf"
            className="sr-only"
            onChange={(e) => pick(e.target.files?.[0] ?? null)}
          />
          <span className="truncate">
            {file ? file.name : "Choose a PDF to replace it"}
          </span>
        </label>
        <Button type="button" onClick={upload} disabled={!file || uploading}>
          {uploading ? <Loader2 className="animate-spin" /> : "Replace"}
        </Button>
      </div>
      {error ? <p className="mt-2 text-sm text-destructive">{error}</p> : null}
    </section>
  );
}
