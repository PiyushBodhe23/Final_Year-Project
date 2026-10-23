"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";
import { useState } from "react";

import { Card } from "@/components/ui/card";
import { Container } from "@/components/ui/container";
import { Section } from "@/components/ui/section";
import { SectionHeading } from "@/components/ui/section-heading";
import { testimonials } from "@/data/home";

export function Testimonials() {
  const [index, setIndex] = useState(0);
  const current = testimonials[index];
  const initials = current.name
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("");

  function shift(direction: number) {
    setIndex((value) => (value + direction + testimonials.length) % testimonials.length);
  }

  return (
    <Section id="stories" className="bg-muted/40">
      <Container>
        <SectionHeading id="stories-title" eyebrow="Stories" title="People use it to start a calmer conversation." align="center" />
        <Card className="mx-auto mt-8 max-w-3xl p-8" aria-live="polite">
          <div className="flex items-center gap-3">
            <span className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-brand-600 text-sm font-bold text-white" aria-hidden>
              {initials}
            </span>
            <div>
              <p className="font-semibold">{current.name}</p>
              <p className="text-sm text-muted-foreground">{current.role}</p>
            </div>
          </div>
          <blockquote className="mt-6 text-lg leading-relaxed">“{current.quote}”</blockquote>
          <div className="mt-6 flex gap-2">
            <button type="button" className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-border" aria-label="Previous story" onClick={() => shift(-1)}>
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button type="button" className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-border" aria-label="Next story" onClick={() => shift(1)}>
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </Card>
      </Container>
    </Section>
  );
}
