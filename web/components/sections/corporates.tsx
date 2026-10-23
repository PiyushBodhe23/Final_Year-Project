import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Container } from "@/components/ui/container";
import { Section } from "@/components/ui/section";
import { SectionHeading } from "@/components/ui/section-heading";
import { corporateMetrics } from "@/data/home";

export function Corporates() {
  return (
    <Section id="corporates">
      <Container className="grid items-center gap-10 lg:grid-cols-2">
        <div>
          <SectionHeading
            id="corporates-title"
            eyebrow="For corporates"
            title="Workplace wellness without opening private health files."
            description="HR sees participation and program progress. Employees keep their scores. A pilot usually starts with one team, not the whole company."
          />
          <ul className="mt-8 space-y-4">
            {corporateMetrics.map((metric) => (
              <li key={metric.label}>
                <p className="font-display text-2xl text-brand-700">{metric.value}</p>
                <p className="text-sm text-muted-foreground">{metric.label}</p>
              </li>
            ))}
          </ul>
          <Button className="mt-8" asChild>
            <a href="#book">Request corporate demo</a>
          </Button>
        </div>
        <Card className="p-6" aria-hidden>
          <p className="text-sm font-semibold">Team wellness snapshot</p>
          <div className="mt-5 space-y-3">
            {[
              ["Check-ins this month", "68%"],
              ["Prevention program started", "41%"],
              ["People who shared a summary", "12%"],
            ].map(([label, value]) => (
              <div key={label}>
                <div className="flex justify-between text-sm">
                  <span>{label}</span>
                  <span className="font-semibold">{value}</span>
                </div>
                <div className="mt-1 h-2 rounded-full bg-muted">
                  <div className="h-2 rounded-full bg-brand-600" style={{ width: value }} />
                </div>
              </div>
            ))}
          </div>
          <p className="mt-5 text-xs text-muted-foreground">Sample view. Individual readings are not shown here.</p>
        </Card>
      </Container>
    </Section>
  );
}
