import Link from "next/link";
import { meta } from "@/lib/data";

const LINKS = [
  { href: "/insights", label: "Insights" },
  { href: "/players", label: "Players" },
];

export function NavBar() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-bg/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="group flex items-center gap-2.5">
          <span className="h-6 w-1.5 rounded-full bg-accent transition-transform group-hover:scale-y-110" />
          <span className="font-display text-xl font-bold tracking-tight text-text-primary">
            TD REGRESSION
          </span>
        </Link>
        <nav className="flex items-center gap-6">
          {LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-text-secondary transition-colors hover:text-text-primary"
            >
              {link.label}
            </Link>
          ))}
          <span className="tabular hidden rounded-full border border-border-strong bg-surface px-3 py-1 text-xs font-semibold text-text-secondary sm:inline-block">
            {meta.seasonPrior} &rarr; {meta.seasonNext}
          </span>
        </nav>
      </div>
      <div className="yard-rule" />
    </header>
  );
}
