"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import {
  ArrowRight,
  CheckCircle2,
  FileText,
  Loader2,
  Upload,
  X,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { OnboardingState } from "@/lib/onboarding-types";

const MAX_BYTES = 25 * 1024 * 1024;

export function CvStep() {
  const router = useRouter();
  const [file, setFile] = React.useState<File | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [uploading, setUploading] = React.useState(false);
  const [state, setState] = React.useState<OnboardingState | null>(null);

  const extraction = state?.cv?.extraction_status;
  const done = extraction === "ready";
  const failed = extraction === "error";
  const processing = state != null && !done && !failed;

  React.useEffect(() => {
    if (!processing) return;
    const timer = setInterval(async () => {
      try {
        const res = await fetch("/api/onboarding", { cache: "no-store" });
        if (res.ok) setState((await res.json()) as OnboardingState);
      } catch {
        // keep polling
      }
    }, 2500);
    return () => clearInterval(timer);
  }, [processing]);

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
      setState((await res.json()) as OnboardingState);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Upload failed.");
      setUploading(false);
    }
  }

  if (state) {
    return (
      <div className="space-y-6">
        <h1 className="t-h1 text-foreground">
          {done
            ? "We've read your CV"
            : failed
              ? "We couldn't read that CV"
              : "Reading your CV…"}
        </h1>

        <Card>
          <CardContent className="flex items-center gap-3 p-4">
            {done ? (
              <CheckCircle2 className="size-6 shrink-0 text-match" />
            ) : failed ? (
              <X className="size-6 shrink-0 text-destructive" />
            ) : (
              <Loader2 className="size-6 shrink-0 animate-spin text-ai" />
            )}
            <div className="min-w-0">
              <p className="truncate text-sm font-semibold text-foreground">
                {state.cv?.original_filename}
              </p>
              <p className="text-sm text-muted-foreground">
                {done
                  ? "Extracted. Your matches will be ready soon."
                  : failed
                    ? "The file couldn't be processed. Try another PDF."
                    : "Extracting the text — this takes a moment."}
              </p>
            </div>
          </CardContent>
        </Card>

        {failed ? (
          <Button
            type="button"
            variant="outline"
            onClick={() => {
              setState(null);
              setFile(null);
            }}
          >
            Try another file
          </Button>
        ) : (
          <Button
            type="button"
            size="lg"
            className="w-full"
            onClick={() => router.push("/")}
          >
            Go to your dashboard <ArrowRight />
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="t-h1 text-foreground">
          Upload your CV
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
          A PDF, up to 25 MB. We read it to match you — it&apos;s never shared.
        </p>
      </div>

      <label
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          pick(event.dataTransfer.files?.[0] ?? null);
        }}
        className="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border bg-card px-4 py-10 text-center transition-colors hover:border-ai"
      >
        <input
          type="file"
          accept="application/pdf"
          className="sr-only"
          onChange={(event) => pick(event.target.files?.[0] ?? null)}
        />
        {file ? (
          <FileText className="size-6 text-ai" />
        ) : (
          <Upload className="size-6 text-muted-foreground" />
        )}
        <span className="text-sm font-medium text-foreground">
          {file ? file.name : "Choose a PDF or drop it here"}
        </span>
        {file ? (
          <span className="text-xs text-muted-foreground">
            {(file.size / 1024 / 1024).toFixed(1)} MB
          </span>
        ) : null}
      </label>

      {error ? <p className="text-sm text-destructive">{error}</p> : null}

      <Button
        type="button"
        size="lg"
        className="w-full"
        disabled={!file || uploading}
        onClick={upload}
      >
        {uploading ? (
          <>
            <Loader2 className="animate-spin" /> Uploading…
          </>
        ) : (
          <>
            Upload CV <ArrowRight />
          </>
        )}
      </Button>
    </div>
  );
}
