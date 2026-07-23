"use client";

import { useEffect, useState } from "react";

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
          services: { api: "unavailable", postgresql: "unavailable", keycloak: "unavailable", mailpit: "unavailable" },
        }),
      );
  }, []);

  const services = status?.services ?? {};

  return (
    <section className="status-panel admin-status" aria-labelledby="status-title">
      <div>
        <p className="eyebrow">System status</p>
        <h1 id="status-title">Foundation services</h1>
        <p className="intro">Visible only to BirdDog administrators.</p>
      </div>
      <div className="status-list">
        <StatusRow label="Frontend" state="online" />
        {Object.entries(labels).map(([key, label]) => (
          <StatusRow key={key} label={label} state={services[key]} loading={!status} />
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
    <div className="status-row">
      <span>{label}</span>
      <span className={`badge ${ready ? "ready" : ""}`}>{text}</span>
    </div>
  );
}
