import { SiteHeader } from "@/components/site-header";
import { CountryPicker } from "@/components/country-map";

// Temporary preview route — remove once the map graduates into the B3 preferences step.
export const dynamic = "force-dynamic";

export default function CountriesPreviewPage() {
  return (
    <>
      <SiteHeader />
      <main className="mx-auto w-full max-w-2xl px-4 pb-24 pt-10">
        <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-ai">
          Preview
        </p>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          Where would you work remotely?
        </h1>
        <div className="mt-6">
          <CountryPicker />
        </div>
      </main>
    </>
  );
}
