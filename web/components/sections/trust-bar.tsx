import { Container } from "@/components/ui/container";
import { partners } from "@/data/home";

export function TrustBar() {
  const loop = [...partners, ...partners];
  return (
    <section aria-label="Organizations exploring PreventVital" className="border-y border-border bg-card/40 py-8">
      <Container>
        <p className="text-center text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
          Designed with hospitals, labs, and workplaces in mind
        </p>
      </Container>
      <div className="marquee mt-5 overflow-hidden">
        <div className="marquee-track flex w-max gap-4 px-4">
          {loop.map((name, index) => (
            <span
              key={`${name}-${index}`}
              className="inline-flex h-12 items-center rounded-2xl border border-dashed border-border bg-background px-5 text-sm font-semibold text-slate-500"
            >
              {name}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
