"use client";

import { useState } from "react";

import { Card } from "@/components/ui/card";
import { Container } from "@/components/ui/container";
import { Section } from "@/components/ui/section";
import { SectionHeading } from "@/components/ui/section-heading";
import { programs } from "@/data/home";
import { cn } from "@/lib/utils";

export function Programs() {
  const [active, setActive] = useState<(typeof programs)[number]["id"]>(programs[0].id);
  const current = programs.find((program) => program.id === active) ?? programs[0];

  return (
    <Section id="programs" className="bg-muted/40">
      <Container>
        <SectionHeading
          id="programs-title"
          eyebrow="Prevention programs"
          title="Small weekly actions, chosen for the risk you care about."
          description="Programs support prevention. They do not treat disease."
        />
        <div role="tablist" aria-label="Prevention programs" className="mt-8 flex flex-wrap gap-2">
          {programs.map((program) => (
            <button
              key={program.id}
              type="button"
              role="tab"
              aria-selected={program.id === active}
              className={cn(
                "rounded-full border px-4 py-2 text-sm font-semibold",
                program.id === active ? "border-brand-600 bg-brand-600 text-white" : "border-border bg-card",
              )}
              onClick={() => setActive(program.id)}
            >
              {program.label}
            </button>
          ))}
        </div>
        <Card className="mt-6 p-6" role="tabpanel">
          <h3 className="text-2xl">{current.label}</h3>
          <p className="mt-2 text-muted-foreground">{current.outcome}</p>
          <ul className="mt-5 space-y-2 text-sm">
            {current.points.map((point) => (
              <li key={point} className="rounded-2xl bg-muted px-4 py-3">
                {point}
              </li>
            ))}
          </ul>
        </Card>
      </Container>
    </Section>
  );
}
