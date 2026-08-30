"use client";

import * as React from "react";
import {
  Briefcase,
  GraduationCap,
  Languages as LanguagesIcon,
  Loader2,
  Sparkles,
} from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

type Facts = {
  summary?: string | null;
  skills?: string[];
  languages?: { language: string; level?: string | null }[];
  experience?: {
    title: string;
    organization?: string | null;
    start?: string | null;
    end?: string | null;
    summary?: string | null;
  }[];
  education?: {
    degree?: string | null;
    field?: string | null;
    institution?: string | null;
    year?: string | null;
  }[];
  total_years_experience?: number | null;
  seniority?: string | null;
};

type FactsResponse = {
  facts_status: "pending" | "queued" | "ready" | "review" | "error" | null;
  facts: Facts;
};

const SKILL_CAP = 24;

export function CvFacts() {
  const [data, setData] = React.useState<FactsResponse | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [showAll, setShowAll] = React.useState(false);

  const status = data?.facts_status ?? null;
  const pending = status === "pending" || status === "queued";

  React.useEffect(() => {
    let active = true;
    fetch("/api/onboarding/facts", { cache: "no-store" })
      .then(async (res) => {
        if (res.ok && active) setData((await res.json()) as FactsResponse);
      })
      .catch(() => {})
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  React.useEffect(() => {
    if (!pending) return;
    const timer = setInterval(async () => {
      try {
        const res = await fetch("/api/onboarding/facts", { cache: "no-store" });
        if (res.ok) setData((await res.json()) as FactsResponse);
      } catch {
        // keep polling
      }
    }, 3000);
    return () => clearInterval(timer);
  }, [pending]);

  if (loading || !status) return null;

  const header = (
    <div className="flex items-center gap-2">
      <Sparkles className="size-4 text-ai" aria-hidden />
      <h2 className="text-sm font-semibold text-foreground">
        What we understood from your CV
      </h2>
      <Badge variant="ai" className="ml-auto">
        AI
      </Badge>
    </div>
  );

  if (pending) {
    return (
      <Card>
        <CardContent className="space-y-3 p-5">
          {header}
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin text-ai" /> Reading your CV…
          </p>
        </CardContent>
      </Card>
    );
  }

  if (status === "error") {
    return (
      <Card>
        <CardContent className="space-y-2 p-5">
          {header}
          <p className="text-sm text-muted-foreground">
            We couldn&apos;t read your CV this time. Try replacing it in Settings.
          </p>
        </CardContent>
      </Card>
    );
  }

  const facts = data?.facts ?? {};
  const skills = facts.skills ?? [];
  const shownSkills = showAll ? skills : skills.slice(0, SKILL_CAP);

  return (
    <Card>
      <CardContent className="space-y-5 p-5">
        {header}

        {facts.summary ? (
          <p className="text-sm leading-relaxed text-muted-foreground">
            {facts.summary}
          </p>
        ) : null}

        <div className="flex flex-wrap gap-2">
          {facts.seniority ? <Badge variant="match">{facts.seniority}</Badge> : null}
          {facts.total_years_experience != null ? (
            <Badge variant="default">
              {facts.total_years_experience} yrs experience
            </Badge>
          ) : null}
        </div>

        {skills.length > 0 ? (
          <Section title={`Skills (${skills.length})`}>
            <div className="flex flex-wrap gap-1.5">
              {shownSkills.map((s) => (
                <span
                  key={s}
                  className="rounded-md bg-secondary px-2 py-1 text-xs font-medium text-secondary-foreground"
                >
                  {s}
                </span>
              ))}
              {skills.length > SKILL_CAP ? (
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2 text-xs"
                  onClick={() => setShowAll((v) => !v)}
                >
                  {showAll ? "Show less" : `+${skills.length - SKILL_CAP} more`}
                </Button>
              ) : null}
            </div>
          </Section>
        ) : null}

        {facts.experience && facts.experience.length > 0 ? (
          <Section title="Experience" icon={<Briefcase className="size-3.5" />}>
            <ul className="space-y-2">
              {facts.experience.map((e, i) => (
                <li key={i} className="text-sm">
                  <span className="font-medium text-foreground">{e.title}</span>
                  {e.organization ? (
                    <span className="text-muted-foreground"> · {e.organization}</span>
                  ) : null}
                  {e.start || e.end ? (
                    <span className="text-muted-foreground">
                      {" "}
                      ({[e.start, e.end].filter(Boolean).join(" – ")})
                    </span>
                  ) : null}
                </li>
              ))}
            </ul>
          </Section>
        ) : null}

        {facts.education && facts.education.length > 0 ? (
          <Section title="Education" icon={<GraduationCap className="size-3.5" />}>
            <ul className="space-y-1.5">
              {facts.education.map((e, i) => (
                <li key={i} className="text-sm text-foreground">
                  {[e.degree, e.field].filter(Boolean).join(", ")}
                  {e.institution ? (
                    <span className="text-muted-foreground"> · {e.institution}</span>
                  ) : null}
                  {e.year ? <span className="text-muted-foreground"> ({e.year})</span> : null}
                </li>
              ))}
            </ul>
          </Section>
        ) : null}

        {facts.languages && facts.languages.length > 0 ? (
          <Section title="Languages" icon={<LanguagesIcon className="size-3.5" />}>
            <div className="flex flex-wrap gap-1.5">
              {facts.languages.map((l, i) => (
                <span
                  key={i}
                  className="rounded-md bg-secondary px-2 py-1 text-xs font-medium text-secondary-foreground"
                >
                  {l.language}
                  {l.level ? ` · ${l.level}` : ""}
                </span>
              ))}
            </div>
          </Section>
        ) : null}
      </CardContent>
    </Card>
  );
}

function Section({
  title,
  icon,
  children,
}: {
  title: string;
  icon?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div>
      <p className="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        {icon}
        {title}
      </p>
      {children}
    </div>
  );
}
