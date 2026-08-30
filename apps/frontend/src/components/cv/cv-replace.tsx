"use client";

import * as React from "react";
import { FileText, Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { CvViewer } from "@/components/cv/cv-viewer";

const MAX_BYTES = 25 * 1024 * 1024;

type Cv = {
  original_filename: string;
  extraction_status: "pending" | "processing" | "ready" | "error";
} | null;

export function CvReplace() {
  const [cv, setCv] = React.useState<Cv | undefined>(undefined);
  const [file, setFile] = React.useState<File | null>(null);
  const [uploading, setUploading] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    let active = true;
    fetch("/api/onboarding", { cache: "no-store" })
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (active) setCv((data?.cv as Cv) ?? null);
      })
      .catch(() => {
        if (active) setCv(null);
      });
    return () => {
      active = false;
    };
  }, []);

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
      // Reload so the facts card re-reads the new CV.
      window.location.reload();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Upload failed.");
      setUploading(false);
    }
  }

  return (
    <Card>
      <CardContent className="space-y-3 p-5">
        <h2 className="t-h3 text-foreground">Your CV</h2>

        {cv === undefined ? (
          <p className="text-sm text-muted-foreground">Loading…</p>
        ) : cv ? (
          <div className="flex items-center gap-3">
            <FileText className="size-5 shrink-0 text-ai" />
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-foreground">
                {cv.original_filename}
              </p>
              <p className="text-sm text-muted-foreground">
                {cv.extraction_status === "ready"
                  ? "Processed"
                  : cv.extraction_status === "error"
                    ? "Couldn't be read"
                    : "Processing…"}
              </p>
            </div>
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">No CV uploaded yet.</p>
        )}

        {cv ? <CvViewer /> : null}

        <div className="flex gap-2 pt-1">
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
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
      </CardContent>
    </Card>
  );
}
