import { Activity, HeartPulse, LineChart, Sparkles, Watch } from "lucide-react";
import type { LucideIcon } from "lucide-react";

import { Reveal } from "@/components/motion/reveal";
import { Card } from "@/components/ui/card";
import { Container } from "@/components/ui/container";
import { Section } from "@/components/ui/section";
import { SectionHeading } from "@/components/ui/section-heading";
import { features, type FeatureIcon } from "@/data/home";
import { cn } from "@/lib/utils";

const icons: Record<FeatureIcon, LucideIcon> = {
  spark: Sparkles,
  pulse: Activity,
  heart: HeartPulse,
  watch: Watch,
  chart: LineChart,
  users: Activity,
};

export function Features() {
  return (
    <Section id="platform">
      <Container>
        <SectionHeading
          id="platform-title"
          eyebrow="Platform"
          title="One place for the signals that matter."
          description="Assessment, monitoring, and prevention programs that stay readable on a phone."
        />
        <div className="mt-10 grid gap-4 md:grid-cols-3">
          {features.map((feature, index) => {
            const Icon = icons[feature.icon];
            return (
              <Reveal key={feature.title} delay={index * 0.05} className={cn(feature.span)}>
                <Card className="group h-full p-6 motion-safe:transition-transform motion-safe:hover:-translate-y-1">
                  <span className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-100">
                    <Icon className="h-5 w-5" aria-hidden />
                  </span>
                  <h3 className="mt-4 text-xl">{feature.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{feature.body}</p>
                  <FeatureVisual kind={feature.visual} />
                </Card>
              </Reveal>
            );
          })}
        </div>
      </Container>
    </Section>
  );
}

function FeatureVisual({ kind }: { kind: (typeof features)[number]["visual"] }) {
  if (kind === "score") {
    return (
      <div className="mt-6 flex items-end gap-2" aria-hidden>
        {[40, 64, 52, 78, 70].map((height) => (
          <span key={height} className="w-8 rounded-t-xl bg-brand-500/80 motion-safe:transition-all group-hover:bg-brand-600" style={{ height }} />
        ))}
      </div>
    );
  }
  if (kind === "trend") {
    return <p className="mt-6 text-sm font-semibold text-emerald-600">7-day trend · mostly steady</p>;
  }
  if (kind === "programs") {
    return <p className="mt-6 text-sm font-semibold text-brand-700">Diabetes · Cardiac</p>;
  }
  if (kind === "steps") {
    return <p className="mt-6 text-sm font-semibold text-muted-foreground">6,420 steps · 7h sleep</p>;
  }
  return <p className="mt-6 text-sm font-semibold text-muted-foreground">Month over month, in plain words</p>;
}
