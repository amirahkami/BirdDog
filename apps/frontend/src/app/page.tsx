"use client";

import { useEffect, useState } from "react";

type Health = {
  status: "ok" | "unavailable";
  database: "ok" | "error";
};

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);

  useEffect(() => {
    fetch("/api/health", { cache: "no-store" })
      .then(async (response) => {
        const payload = (await response.json()) as Health;
        setHealth(payload);
      })
      .catch(() => setHealth({ status: "unavailable", database: "error" }));
  }, []);

  const apiReady = health?.status === "ok";
  const databaseReady = health?.database === "ok";

  return (
    <main>
      <section className="hero" aria-labelledby="page-title">
        <p className="eyebrow">BirdDog foundation</p>
        <h1 id="page-title">The job search that reads before you apply.</h1>
        <p className="intro">
          BirdDog will collect focused roles, remove the noise, and explain which
          opportunities fit your CV.
        </p>
      </section>

      <section className="status-panel" aria-labelledby="status-title">
        <div>
          <p className="eyebrow">System status</p>
          <h2 id="status-title">Foundation services</h2>
        </div>
        <div className="status-list">
          <StatusRow label="Frontend" ready />
          <StatusRow label="API" ready={apiReady} loading={health === null} />
          <StatusRow label="PostgreSQL" ready={databaseReady} loading={health === null} />
        </div>
      </section>
    </main>
  );
}

function StatusRow({
  label,
  ready,
  loading = false,
}: {
  label: string;
  ready: boolean;
  loading?: boolean;
}) {
  const status = loading ? "Checking" : ready ? "Online" : "Unavailable";

  return (
    <div className="status-row">
      <span>{label}</span>
      <span className={`badge ${ready ? "ready" : ""}`}>{status}</span>
    </div>
  );
}
