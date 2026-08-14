import { meta } from "@/lib/data";

export function Footer() {
  const generated = new Date(meta.generatedAt);

  return (
    <footer className="mt-auto border-t border-border">
      <div className="mx-auto max-w-6xl px-6 py-8 text-xs text-text-muted">
        <p>
          Data from nflverse via nflreadpy, {meta.histSeasons[0]}&ndash;{meta.histSeasons[1]}.
          Generated{" "}
          {generated.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}.
        </p>
        <p className="mt-1">
          Only same-team {meta.minOpportunities}+ opportunity players are scored. Not betting advice.
        </p>
      </div>
    </footer>
  );
}
