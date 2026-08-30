"use client";

import * as React from "react";
import { ComposableMap, Geographies, Geography } from "react-simple-maps";
import worldData from "world-atlas/countries-110m.json";

// Numeric ISO 3166-1 ids for the European countries we let users pick.
const EUROPE_IDS = new Set([
  "8", "40", "56", "70", "100", "112", "191", "196", "203", "208", "233",
  "246", "250", "276", "300", "348", "352", "372", "380", "428", "440",
  "442", "470", "498", "499", "528", "578", "616", "620", "642", "688",
  "703", "705", "724", "752", "756", "804", "807", "826",
]);

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type Geo = any;

export function CountryPicker() {
  const [selected, setSelected] = React.useState<Map<string, string>>(
    new Map()
  );

  function toggle(id: string, name: string) {
    setSelected((prev) => {
      const next = new Map(prev);
      if (next.has(id)) next.delete(id);
      else next.set(id, name);
      return next;
    });
  }

  return (
    <div>
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">
          Tap countries to select where you&apos;d work remotely.
        </p>
        <span className="rounded-md bg-ai-soft px-2.5 py-1 text-xs font-semibold text-ai tabular-nums">
          {selected.size} selected
        </span>
      </div>

      <div className="mt-4 overflow-hidden rounded-xl border border-border bg-card">
        <ComposableMap
          projection="geoAzimuthalEqualArea"
          projectionConfig={{ rotate: [-10, -52, 0], scale: 760 }}
          width={800}
          height={620}
          style={{ width: "100%", height: "auto" }}
        >
          <Geographies geography={worldData as Geo}>
            {({ geographies }: { geographies: Geo[] }) =>
              geographies
                .filter((geo) => EUROPE_IDS.has(String(geo.id)))
                .map((geo) => {
                  const id = String(geo.id);
                  const isSelected = selected.has(id);
                  return (
                    <Geography
                      key={geo.rsmKey}
                      geography={geo}
                      onClick={() => toggle(id, geo.properties.name)}
                      style={{
                        default: {
                          fill: isSelected ? "var(--ai)" : "var(--secondary)",
                          stroke: "var(--background)",
                          strokeWidth: 0.75,
                          outline: "none",
                          transition: "fill 150ms ease",
                        },
                        hover: {
                          fill: isSelected ? "var(--ai)" : "var(--accent)",
                          stroke: "var(--ai)",
                          strokeWidth: 1,
                          outline: "none",
                          cursor: "pointer",
                        },
                        pressed: {
                          fill: "var(--ai)",
                          stroke: "var(--ai)",
                          strokeWidth: 1,
                          outline: "none",
                        },
                      }}
                    />
                  );
                })
            }
          </Geographies>
        </ComposableMap>
      </div>

      {selected.size > 0 ? (
        <div className="mt-4 flex flex-wrap gap-2">
          {[...selected.values()].sort().map((name) => (
            <span
              key={name}
              className="rounded-md bg-ai-soft px-2.5 py-1 text-xs font-semibold text-ai"
            >
              {name}
            </span>
          ))}
        </div>
      ) : null}
    </div>
  );
}
