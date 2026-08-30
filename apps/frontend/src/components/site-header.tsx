import Link from "next/link";
import type { ReactNode } from "react";

import { ThemeToggle } from "@/components/theme-toggle";
import { cn } from "@/lib/utils";

function BirdMark() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden>
      <path
        d="M3 13c4.5 0 6-4 9-4s3.5 3 6.5 3c1.2 0 2-.4 2.5-1-.2 4.2-3.4 7-7.8 7C6.9 18 3 16.2 3 13Z"
        fill="currentColor"
      />
    </svg>
  );
}

export function SiteHeader({
  children,
  className,
}: {
  children?: ReactNode;
  className?: string;
}) {
  return (
    <header
      className={cn(
        "sticky top-0 z-20 border-b border-border bg-background/85 backdrop-blur",
        className
      )}
    >
      <div className="mx-auto flex h-14 w-full max-w-5xl items-center justify-between gap-3 px-4 sm:px-6">
        <Link
          href="/"
          className="flex items-center gap-2 font-semibold tracking-tight text-foreground"
        >
          <span className="grid size-7 place-items-center rounded-lg bg-primary text-primary-foreground">
            <BirdMark />
          </span>
          <span className="hidden sm:inline">
            Bird<span className="text-ai">Dog</span>
          </span>
        </Link>
        <div className="flex items-center gap-2">
          {children}
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
