"use client";

import * as React from "react";
import { ComposableMap, Geographies, Geography } from "react-simple-maps";
import worldData from "world-atlas/countries-50m.json";
import { Check, Search, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Geo = any;
type Country = { id: string; name: string };

// Normalize a geo id ("040" -> "40") so it matches our un-padded ISO numeric ids.
const norm = (raw: string | number) => String(Number(raw));

const EU: Country[] = [
  { id: "40", name: "Austria" }, { id: "56", name: "Belgium" }, { id: "100", name: "Bulgaria" },
  { id: "191", name: "Croatia" }, { id: "196", name: "Cyprus" }, { id: "203", name: "Czechia" },
  { id: "208", name: "Denmark" }, { id: "233", name: "Estonia" }, { id: "246", name: "Finland" },
  { id: "250", name: "France" }, { id: "276", name: "Germany" }, { id: "300", name: "Greece" },
  { id: "348", name: "Hungary" }, { id: "372", name: "Ireland" }, { id: "380", name: "Italy" },
  { id: "428", name: "Latvia" }, { id: "440", name: "Lithuania" }, { id: "442", name: "Luxembourg" },
  { id: "470", name: "Malta" }, { id: "528", name: "Netherlands" }, { id: "616", name: "Poland" },
  { id: "620", name: "Portugal" }, { id: "642", name: "Romania" }, { id: "703", name: "Slovakia" },
  { id: "705", name: "Slovenia" }, { id: "724", name: "Spain" }, { id: "752", name: "Sweden" },
];
const EEA_EXTRA: Country[] = [
  { id: "352", name: "Iceland" }, { id: "578", name: "Norway" }, { id: "438", name: "Liechtenstein" },
];
const CH: Country = { id: "756", name: "Switzerland" };
const OTHERS: Country[] = [{ id: "826", name: "United Kingdom" }];

const ALL: Country[] = [...EU, ...EEA_EXTRA, CH, ...OTHERS].sort((a, b) =>
  a.name.localeCompare(b.name)
);
const NAME = new Map(ALL.map((c) => [c.id, c.name]));

const ids = (list: Country[]) => list.map((c) => c.id);
const PRESETS = [
  { label: "EU + EEA + CH", ids: ids([...EU, ...EEA_EXTRA, CH]), primary: true },
  { label: "EU", ids: ids(EU) },
  { label: "EEA", ids: ids([...EU, ...EEA_EXTRA]) },
  { label: "All", ids: ids(ALL) },
];

export function CountryPicker() {
  const [selected, setSelected] = React.useState<Set<string>>(new Set());
  const [query, setQuery] = React.useState("");

  const toggle = (id: string) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  const addAll = (list: string[]) =>
    setSelected((prev) => new Set([...prev, ...list]));
  const clear = () => setSelected(new Set());

  const q = query.trim().toLowerCase();
  const results = q ? ALL.filter((c) => c.name.toLowerCase().includes(q)) : [];

  return (
    <div className="space-y-4">
      {/* Presets */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Quick pick
        </span>
        {PRESETS.map((p) => (
          <Button
            key={p.label}
            type="button"
            size="sm"
            variant={p.primary ? "default" : "secondary"}
            onClick={() => addAll(p.ids)}
          >
            {p.label}
          </Button>
        ))}
        <Button type="button" size="sm" variant="ghost" onClick={clear} disabled={selected.size === 0}>
          Clear all
        </Button>
      </div>
      <p className="-mt-1 text-xs text-muted-foreground">
        Tip: <span className="font-medium text-foreground">EU + EEA + CH</span> is where an EU
        citizen can work without a permit.
      </p>

      {/* Map */}
      <div className="overflow-hidden rounded-xl border border-border bg-card">
        <ComposableMap
          projection="geoAzimuthalEqualArea"
          projectionConfig={{ rotate: [-10, -52, 0], scale: 1150 }}
          width={800}
          height={760}
          style={{ width: "100%", height: "auto" }}
        >
          <Geographies geography={worldData as Geo}>
            {({ geographies }: { geographies: Geo[] }) =>
              geographies
                .filter((geo) => NAME.has(norm(geo.id)))
                .map((geo) => {
                  const id = norm(geo.id);
                  const sel = selected.has(id);
                  return (
                    <Geography
                      key={geo.rsmKey}
                      geography={geo}
                      onClick={() => toggle(id)}
                      style={{
                        default: {
                          fill: sel ? "var(--ai)" : "var(--secondary)",
                          stroke: "var(--background)",
                          strokeWidth: 0.6,
                          outline: "none",
                          transition: "fill 150ms ease",
                        },
                        hover: {
                          fill: sel ? "var(--ai)" : "var(--accent)",
                          stroke: "var(--ai)",
                          strokeWidth: 1,
                          outline: "none",
                          cursor: "pointer",
                        },
                        pressed: { fill: "var(--ai)", outline: "none" },
                      }}
                    />
                  );
                })
            }
          </Geographies>
        </ComposableMap>
      </div>

      {/* Compact search (results only while typing) */}
      <div>
        <div className="relative">
          <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            className="px-9"
            placeholder="Search to add a country…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {query ? (
            <button
              type="button"
              onClick={() => setQuery("")}
              aria-label="Clear search"
              className="absolute right-2 top-1/2 grid size-7 -translate-y-1/2 place-items-center rounded-md text-muted-foreground hover:bg-accent hover:text-foreground"
            >
              <X className="size-4" />
            </button>
          ) : null}
        </div>

        {q ? (
          <ul className="mt-2 max-h-52 overflow-y-auto rounded-lg border border-border bg-card">
            {results.length > 0 ? (
              results.map((c) => {
                const sel = selected.has(c.id);
                return (
                  <li key={c.id}>
                    <button
                      type="button"
                      onClick={() => {
                        toggle(c.id);
                        setQuery("");
                      }}
                      className={cn(
                        "flex w-full items-center justify-between px-3 py-2 text-sm transition-colors",
                        sel ? "bg-ai-soft font-semibold text-ai" : "hover:bg-accent"
                      )}
                    >
                      {c.name}
                      {sel ? <Check className="size-4" /> : null}
                    </button>
                  </li>
                );
              })
            ) : (
              <li className="px-3 py-2 text-sm text-muted-foreground">No match.</li>
            )}
          </ul>
        ) : null}
      </div>

      {/* Selected chips (click to remove) */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Selected ({selected.size})
        </p>
        {selected.size === 0 ? (
          <p className="mt-2 text-sm text-muted-foreground">
            None yet — use Quick pick, tap the map, or search.
          </p>
        ) : (
          <div className="mt-2 flex flex-wrap gap-2">
            {[...selected]
              .sort((a, b) => (NAME.get(a) ?? "").localeCompare(NAME.get(b) ?? ""))
              .map((id) => (
                <button
                  key={id}
                  type="button"
                  onClick={() => toggle(id)}
                  className="inline-flex items-center gap-1.5 rounded-md bg-ai-soft px-2.5 py-1 text-xs font-semibold text-ai transition-colors hover:bg-ai hover:text-ai-foreground"
                >
                  {NAME.get(id) ?? id}
                  <X className="size-3" />
                </button>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
