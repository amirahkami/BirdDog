"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

type Status = {
  status: "ok" | "degraded";
  services: Record<string, "online" | "unavailable">;
};

const labels: Record<string, string> = {
  api: "API",
  postgresql: "PostgreSQL",
  keycloak: "Keycloak",
  mailpit: "Mailpit",
};

export function AdminStatus() {
  const [status, setStatus] = useState<Status | null>(null);

  useEffect(() => {
    fetch("/api/admin/status", { cache: "no-store" })
      .then(async (response) => {
        if (!response.ok) throw new Error("Status unavailable");
        setStatus((await response.json()) as Status);
      })
      .catch(() =>
        setStatus({
          status: "degraded",
          services: {
            api: "unavailable",
            postgresql: "unavailable",
            keycloak: "unavailable",
            mailpit: "unavailable",
          },
        })
      );
  }, []);

  const services = status?.services ?? {};

  return (
    <section aria-labelledby="status-title">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-ai">
        System status
      </p>
      <div className="flex flex-wrap items-center gap-3">
        <h1
          id="status-title"
          className="text-2xl font-bold tracking-tight text-foreground"
        >
          Foundation services
        </h1>
        {status ? (
          <Badge variant={status.status === "ok" ? "match" : "mid"}>
            {status.status === "ok" ? "All systems go" : "Degraded"}
          </Badge>
        ) : null}
      </div>
      <p className="mt-1 text-sm text-muted-foreground">
        Visible only to BirdDog administrators.
      </p>

      <div className="mt-6 grid gap-2.5 sm:grid-cols-2">
        <StatusRow label="Frontend" state="online" />
        {Object.entries(labels).map(([key, label]) => (
          <StatusRow
            key={key}
            label={label}
            state={services[key]}
            loading={!status}
          />
        ))}
      </div>
    </section>
  );
}

function StatusRow({
  label,
  state,
  loading = false,
}: {
  label: string;
  state?: "online" | "unavailable";
  loading?: boolean;
}) {
  const ready = state === "online";
  const text = loading ? "Checking" : ready ? "Online" : "Unavailable";

  return (
    <Card className="flex items-center justify-between gap-3 px-4 py-3.5">
      <span className="font-medium text-foreground">{label}</span>
      <Badge variant={loading ? "outline" : ready ? "match" : "destructive"}>
        <span className="size-1.5 rounded-full bg-current" aria-hidden />
        {text}
      </Badge>
    </Card>
  );
}
