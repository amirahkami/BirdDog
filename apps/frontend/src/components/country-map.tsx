"use client";

import * as React from "react";
import { ComposableMap, Geographies, Geography } from "react-simple-maps";
import worldData from "world-atlas/countries-50m.json";
import { Check, X } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Geo = any;
type Country = { id: string; name: string };

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
  { label: "EU + EEA + CH", ids: ids([...EU, ...EEA_EXTRA, CH]), primary: true, hint: "where an EU citizen works without a permit" },
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
  const filtered = q ? ALL.filter((c) => c.name.toLowerCase().includes(q)) : ALL;

  return (
    <div className="space-y-5">
      {/* Presets */}
      <div>
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
        <p className="mt-2 text-xs text-muted-foreground">
          Tip: <span className="font-medium text-foreground">EU + EEA + CH</span> is where an EU
          citizen can work without a permit.
        </p>
      </div>

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
                .filter((geo) => NAME.has(String(geo.id)))
                .map((geo) => {
                  const id = String(geo.id);
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

      {/* Searchable list — reliable selection incl. tiny countries */}
      <div className="rounded-xl border border-border bg-card p-3">
        <Input
          placeholder="Search a country…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <ul className="mt-3 grid max-h-56 grid-cols-1 gap-1 overflow-y-auto sm:grid-cols-2">
          {filtered.map((c) => {
            const sel = selected.has(c.id);
            return (
              <li key={c.id}>
                <button
                  type="button"
                  onClick={() => toggle(c.id)}
                  className={cn(
                    "flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-sm transition-colors",
                    sel
                      ? "bg-ai-soft font-semibold text-ai"
                      : "text-foreground hover:bg-accent"
                  )}
                >
                  <span
                    className={cn(
                      "grid size-4 shrink-0 place-items-center rounded border",
                      sel ? "border-ai bg-ai text-ai-foreground" : "border-border"
                    )}
                  >
                    {sel ? <Check className="size-3" /> : null}
                  </span>
                  {c.name}
                </button>
              </li>
            );
          })}
          {filtered.length === 0 ? (
            <li className="px-2.5 py-2 text-sm text-muted-foreground">No match.</li>
          ) : null}
        </ul>
      </div>

      {/* Selected chips */}
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Selected ({selected.size})
        </p>
        {selected.size === 0 ? (
          <p className="mt-2 text-sm text-muted-foreground">
            None yet — use Quick pick, the map, or the list.
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
