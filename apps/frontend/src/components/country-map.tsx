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
type Country = { a2: string; num: string; name: string };

// Normalize a geo id ("040" -> "40") to match our un-padded ISO numeric ids.
const norm = (raw: string | number) => String(Number(raw));

const EU: Country[] = [
  { a2: "AT", num: "40", name: "Austria" }, { a2: "BE", num: "56", name: "Belgium" },
  { a2: "BG", num: "100", name: "Bulgaria" }, { a2: "HR", num: "191", name: "Croatia" },
  { a2: "CY", num: "196", name: "Cyprus" }, { a2: "CZ", num: "203", name: "Czechia" },
  { a2: "DK", num: "208", name: "Denmark" }, { a2: "EE", num: "233", name: "Estonia" },
  { a2: "FI", num: "246", name: "Finland" }, { a2: "FR", num: "250", name: "France" },
  { a2: "DE", num: "276", name: "Germany" }, { a2: "GR", num: "300", name: "Greece" },
  { a2: "HU", num: "348", name: "Hungary" }, { a2: "IE", num: "372", name: "Ireland" },
  { a2: "IT", num: "380", name: "Italy" }, { a2: "LV", num: "428", name: "Latvia" },
  { a2: "LT", num: "440", name: "Lithuania" }, { a2: "LU", num: "442", name: "Luxembourg" },
  { a2: "MT", num: "470", name: "Malta" }, { a2: "NL", num: "528", name: "Netherlands" },
  { a2: "PL", num: "616", name: "Poland" }, { a2: "PT", num: "620", name: "Portugal" },
  { a2: "RO", num: "642", name: "Romania" }, { a2: "SK", num: "703", name: "Slovakia" },
  { a2: "SI", num: "705", name: "Slovenia" }, { a2: "ES", num: "724", name: "Spain" },
  { a2: "SE", num: "752", name: "Sweden" },
];
const EEA_EXTRA: Country[] = [
  { a2: "IS", num: "352", name: "Iceland" }, { a2: "NO", num: "578", name: "Norway" },
  { a2: "LI", num: "438", name: "Liechtenstein" },
];
const CH: Country = { a2: "CH", num: "756", name: "Switzerland" };
const OTHERS: Country[] = [{ a2: "GB", num: "826", name: "United Kingdom" }];

export const ALL_COUNTRIES: Country[] = [...EU, ...EEA_EXTRA, CH, ...OTHERS].sort(
  (a, b) => a.name.localeCompare(b.name)
);
const NAME_BY_A2 = new Map(ALL_COUNTRIES.map((c) => [c.a2, c.name]));
const A2_BY_NUM = new Map(ALL_COUNTRIES.map((c) => [c.num, c.a2]));

const codes = (list: Country[]) => list.map((c) => c.a2);
export type Preset = { label: string; codes: string[]; primary?: boolean };
export const REMOTE_PRESETS: Preset[] = [
  { label: "EU + EEA + CH", codes: codes([...EU, ...EEA_EXTRA, CH]), primary: true },
  { label: "EU", codes: codes(EU) },
  { label: "EEA", codes: codes([...EU, ...EEA_EXTRA]) },
  { label: "All", codes: codes(ALL_COUNTRIES) },
];

export function countryName(a2: string): string {
  return NAME_BY_A2.get(a2) ?? a2;
}

export function CountryPicker({
  value,
  onChange,
  showMap = true,
  presets = [],
}: {
  value: string[];
  onChange: (next: string[]) => void;
  showMap?: boolean;
  presets?: Preset[];
}) {
  const [query, setQuery] = React.useState("");
  const [canHover, setCanHover] = React.useState(false);
  React.useEffect(() => {
    setCanHover(window.matchMedia("(hover: hover)").matches);
  }, []);

  const selected = React.useMemo(() => new Set(value), [value]);
  const toggle = (a2: string) => {
    const next = new Set(selected);
    if (next.has(a2)) next.delete(a2);
    else next.add(a2);
    onChange([...next]);
  };
  const addAll = (list: string[]) => onChange([...new Set([...value, ...list])]);
  const clear = () => onChange([]);

  const q = query.trim().toLowerCase();
  const results = q
    ? ALL_COUNTRIES.filter((c) => c.name.toLowerCase().includes(q))
    : [];

  return (
    <div className="space-y-4">
      {presets.length > 0 ? (
        <div className="flex flex-wrap items-center gap-2">
          {presets.map((p) => (
            <Button
              key={p.label}
              type="button"
              size="sm"
              variant={p.primary ? "default" : "secondary"}
              onClick={() => addAll(p.codes)}
            >
              {p.label}
            </Button>
          ))}
          <Button type="button" size="sm" variant="ghost" onClick={clear} disabled={value.length === 0}>
            Clear all
          </Button>
        </div>
      ) : null}

      {showMap ? (
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
                  .filter((geo) => A2_BY_NUM.has(norm(geo.id)))
                  .map((geo) => {
                    const a2 = A2_BY_NUM.get(norm(geo.id)) as string;
                    const sel = selected.has(a2);
                    return (
                      <Geography
                        key={geo.rsmKey}
                        geography={geo}
                        onClick={() => toggle(a2)}
                        style={{
                          default: {
                            fill: sel ? "var(--ai)" : "var(--map-land)",
                            stroke: "var(--map-border)",
                            strokeWidth: 0.5,
                            outline: "none",
                            transition: "fill 150ms ease",
                          },
                          hover: canHover
                            ? {
                                fill: sel ? "var(--ai)" : "var(--map-hover)",
                                stroke: "var(--ai)",
                                strokeWidth: 1,
                                outline: "none",
                                cursor: "pointer",
                              }
                            : {
                                fill: sel ? "var(--ai)" : "var(--map-land)",
                                stroke: "var(--map-border)",
                                strokeWidth: 0.5,
                                outline: "none",
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
      ) : null}

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
                const sel = selected.has(c.a2);
                return (
                  <li key={c.a2}>
                    <button
                      type="button"
                      onClick={() => {
                        toggle(c.a2);
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

      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Selected ({value.length})
        </p>
        {value.length === 0 ? (
          <p className="mt-2 text-sm text-muted-foreground">None yet.</p>
        ) : (
          <div className="mt-2 flex flex-wrap gap-2">
            {[...value]
              .sort((a, b) => countryName(a).localeCompare(countryName(b)))
              .map((a2) => (
                <button
                  key={a2}
                  type="button"
                  onClick={() => toggle(a2)}
                  className="inline-flex items-center gap-1.5 rounded-md bg-ai-soft px-2.5 py-1 text-xs font-semibold text-ai transition-colors hover:bg-ai hover:text-ai-foreground"
                >
                  {countryName(a2)}
                  <X className="size-3" />
                </button>
              ))}
          </div>
        )}
      </div>
    </div>
  );
}
