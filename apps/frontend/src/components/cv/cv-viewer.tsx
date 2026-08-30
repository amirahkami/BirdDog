"use client";

import * as React from "react";
import { Document, Page, pdfjs } from "react-pdf";
import { Eye, Loader2, X } from "lucide-react";

import { Button } from "@/components/ui/button";

// Self-hosted pdf.js worker (no CDN). The file is copied into /public and pinned
// to pdfjs-dist's version, so it always matches react-pdf's API.
pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.mjs";

const FILE_URL = "/api/onboarding/cv/file";

export function CvViewer() {
  const [open, setOpen] = React.useState(false);
  const [numPages, setNumPages] = React.useState(0);
  const [width, setWidth] = React.useState(360);
  const frameRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    if (!open) return;
    document.body.style.overflow = "hidden";

    function measure() {
      const w = frameRef.current?.clientWidth;
      if (w) setWidth(Math.min(w - 24, 900));
    }
    measure();
    window.addEventListener("resize", measure);

    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    window.addEventListener("keydown", onKey);

    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("resize", measure);
      window.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <>
      <Button
        type="button"
        variant="outline"
        size="sm"
        className="w-full"
        onClick={() => setOpen(true)}
      >
        <Eye className="size-4" /> View CV
      </Button>

      {open ? (
        <div className="fixed inset-0 z-50 flex flex-col bg-background/97 backdrop-blur">
          <div className="flex h-14 shrink-0 items-center justify-between border-b border-border px-4">
            <span className="text-sm font-semibold text-foreground">Your CV</span>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              aria-label="Close"
              onClick={() => setOpen(false)}
            >
              <X />
            </Button>
          </div>

          <div ref={frameRef} className="flex-1 overflow-y-auto px-3 py-4">
            <div className="mx-auto w-full max-w-3xl">
              <Document
                file={FILE_URL}
                onLoadSuccess={(pdf) => setNumPages(pdf.numPages)}
                loading={
                  <div className="flex justify-center py-16 text-muted-foreground">
                    <Loader2 className="size-6 animate-spin" />
                  </div>
                }
                error={
                  <p className="py-16 text-center text-sm text-destructive">
                    Couldn&apos;t load the CV. Please try again.
                  </p>
                }
                className="flex flex-col items-center gap-4"
              >
                {Array.from({ length: numPages }, (_, index) => (
                  <Page
                    key={index}
                    pageNumber={index + 1}
                    width={width}
                    renderTextLayer={false}
                    renderAnnotationLayer={false}
                    className="overflow-hidden rounded-lg border border-border shadow-card"
                  />
                ))}
              </Document>
            </div>
          </div>
        </div>
      ) : null}
    </>
  );
}
