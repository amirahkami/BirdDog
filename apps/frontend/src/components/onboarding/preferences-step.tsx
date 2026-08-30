"use client";

import * as React from "react";
import { ArrowRight, Check, Loader2, MapPin } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";
import {
  ALL_COUNTRIES,
  CountryPicker,
  REMOTE_PRESETS,
} from "@/components/country-map";
import type { OnboardingState } from "@/lib/onboarding-types";

type Home = {
  home_label: string;
  home_city: string | null;
  home_country_code: string;
  home_latitude: number;
  home_longitude: number;
};

export function PreferencesStep({
  initial,
  onSaved,
  submitLabel,
  hideHeader,
}: {
  initial: OnboardingState;
  onSaved: (state: OnboardingState) => void;
  submitLabel?: string;
  hideHeader?: boolean;
}) {
  const [onsite, setOnsite] = React.useState(initial.accepts_onsite);
  const [hybrid, setHybrid] = React.useState(initial.accepts_hybrid);
  const [remote, setRemote] = React.useState(initial.accepts_remote);
  const [fullTime, setFullTime] = React.useState(initial.accepts_full_time);
  const [partTime, setPartTime] = React.useState(initial.accepts_part_time);
  const [radius, setRadius] = React.useState<number>(
    initial.travel_radius_km ?? 50
  );
  const [onsiteCountries, setOnsiteCountries] = React.useState<string[]>(
    initial.onsite_countries.length
      ? initial.onsite_countries
      : initial.home_country_code
        ? [initial.home_country_code]
        : []
  );
  const [remoteCountries, setRemoteCountries] = React.useState<string[]>(
    initial.remote_countries
  );

  const [home, setHome] = React.useState<Home | null>(
    initial.home_country_code &&
      initial.home_latitude != null &&
      initial.home_longitude != null
      ? {
          home_label: initial.home_label ?? "",
          home_city: initial.home_city,
          home_country_code: initial.home_country_code,
          home_latitude: initial.home_latitude,
          home_longitude: initial.home_longitude,
        }
      : null
  );
  const [country, setCountry] = React.useState(initial.home_country_code ?? "DE");
  const [postal, setPostal] = React.useState("");
  const [geoLoading, setGeoLoading] = React.useState(false);
  const [geoError, setGeoError] = React.useState<string | null>(null);

  const [saving, setSaving] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const needHome = onsite || hybrid;
  const anyMode = onsite || hybrid || remote;
  const anyEmployment = fullTime || partTime;

  async function findLocation() {
    const code = postal.trim();
    if (!code) return;
    setGeoLoading(true);
    setGeoError(null);
    try {
      const res = await fetch(
        `/api/onboarding/geocode?country_code=${encodeURIComponent(
          country
        )}&postal_code=${encodeURIComponent(code)}`
      );
      if (!res.ok) throw new Error();
      const d = (await res.json()) as {
        country_code: string;
        postal_code: string;
        city: string | null;
        latitude: number;
        longitude: number;
      };
      const label = `${[d.postal_code, d.city].filter(Boolean).join(" ")}, ${d.country_code}`;
      setHome({
        home_label: label,
        home_city: d.city,
        home_country_code: d.country_code,
        home_latitude: d.latitude,
        home_longitude: d.longitude,
      });
      setOnsiteCountries((prev) => (prev.length ? prev : [d.country_code]));
    } catch {
      setGeoError("Couldn't find that postal code. Check it and try again.");
      setHome(null);
    } finally {
      setGeoLoading(false);
    }
  }

  const valid =
    anyMode &&
    anyEmployment &&
    (!needHome || (home !== null && radius > 0 && onsiteCountries.length > 0)) &&
    (!remote || remoteCountries.length > 0);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!valid || saving) return;
    setSaving(true);
    setError(null);
    const payload = {
      home_label: needHome && home ? home.home_label : null,
      home_city: needHome && home ? home.home_city : null,
      home_country_code: needHome && home ? home.home_country_code : null,
      home_latitude: needHome && home ? home.home_latitude : null,
      home_longitude: needHome && home ? home.home_longitude : null,
      travel_radius_km: needHome ? radius : null,
      accepts_onsite: onsite,
      accepts_hybrid: hybrid,
      accepts_remote: remote,
      accepts_full_time: fullTime,
      accepts_part_time: partTime,
      onsite_countries: needHome ? onsiteCountries : [],
      remote_countries: remote ? remoteCountries : [],
    };
    try {
      const res = await fetch("/api/onboarding/preferences", {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error();
      const data = (await res.json()) as OnboardingState;
      setSaving(false);
      onSaved(data);
    } catch {
      setError("Couldn't save. Please check your entries and try again.");
      setSaving(false);
    }
  }

  return (
    <form onSubmit={submit} className="space-y-8">
      {hideHeader ? null : (
        <div>
          <h1 className="t-h1 text-foreground">Your preferences</h1>
          <p className="mt-2 text-sm leading-relaxed text-muted-foreground">
            These shape which jobs you&apos;ll be matched with.
          </p>
        </div>
      )}

      <Section label="Work mode">
        <div className="flex flex-wrap gap-2">
          <Choice active={onsite} onClick={() => setOnsite((v) => !v)}>On-site</Choice>
          <Choice active={hybrid} onClick={() => setHybrid((v) => !v)}>Hybrid</Choice>
          <Choice active={remote} onClick={() => setRemote((v) => !v)}>Remote</Choice>
        </div>
      </Section>

      <Section label="Employment">
        <div className="flex flex-wrap gap-2">
          <Choice active={fullTime} onClick={() => setFullTime((v) => !v)}>Full-time</Choice>
          <Choice active={partTime} onClick={() => setPartTime((v) => !v)}>Part-time</Choice>
        </div>
      </Section>

      {needHome ? (
        <>
          <Section label="Where do you live?">
            <div className="flex flex-col gap-2 sm:flex-row">
              <select
                value={country}
                onChange={(e) => setCountry(e.target.value)}
                aria-label="Home country"
                className="h-11 rounded-lg border border-input bg-card px-3 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background sm:w-40"
              >
                {ALL_COUNTRIES.map((c) => (
                  <option key={c.a2} value={c.a2}>
                    {c.name}
                  </option>
                ))}
              </select>
              <Input
                placeholder="Postal code (e.g. 80331)"
                value={postal}
                onChange={(e) => setPostal(e.target.value)}
                className="flex-1"
              />
              <Button
                type="button"
                variant="secondary"
                onClick={findLocation}
                disabled={!postal.trim() || geoLoading}
              >
                {geoLoading ? <Loader2 className="animate-spin" /> : "Find"}
              </Button>
            </div>
            {home ? (
              <p className="mt-2 inline-flex items-center gap-1.5 text-sm font-medium text-match">
                <MapPin className="size-4" /> {home.home_label}
              </p>
            ) : null}
            {geoError ? (
              <p className="mt-2 text-sm text-destructive">{geoError}</p>
            ) : null}
          </Section>

          <Section label="Travel radius">
            <div className="flex items-center gap-2">
              <Input
                type="number"
                min={1}
                max={500}
                value={radius}
                onChange={(e) => setRadius(Number(e.target.value) || 0)}
                className="w-28"
              />
              <span className="text-sm text-muted-foreground">km from home</span>
            </div>
          </Section>

          <Section label="Countries you'd commute to">
            <CountryPicker
              value={onsiteCountries}
              onChange={setOnsiteCountries}
              showMap={false}
            />
          </Section>
        </>
      ) : null}

      {remote ? (
        <Section label="Where would you work remotely?">
          <CountryPicker
            value={remoteCountries}
            onChange={setRemoteCountries}
            presets={REMOTE_PRESETS}
          />
        </Section>
      ) : null}

      {error ? <p className="text-sm text-destructive">{error}</p> : null}

      <Button type="submit" size="lg" className="w-full" disabled={!valid || saving}>
        {saving ? (
          <>
            <Loader2 className="animate-spin" /> Saving…
          </>
        ) : submitLabel ? (
          submitLabel
        ) : (
          <>
            Continue <ArrowRight />
          </>
        )}
      </Button>
    </form>
  );
}

function Section({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <Label className="mb-3 block text-sm font-semibold text-foreground">
        {label}
      </Label>
      {children}
    </div>
  );
}

function Choice({
  active,
  onClick,
  children,
}: {
  active: boolean;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <Button
      type="button"
      size="sm"
      variant={active ? "default" : "outline"}
      onClick={onClick}
      className={cn(active && "pl-2.5")}
    >
      {active ? <Check /> : null}
      {children}
    </Button>
  );
}
