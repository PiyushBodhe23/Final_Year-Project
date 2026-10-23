"use client";

import { motion, useReducedMotion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";

import { Container } from "@/components/ui/container";
import { Section } from "@/components/ui/section";
import { SectionHeading } from "@/components/ui/section-heading";
import { steps } from "@/data/home";

export function HowItWorks() {
  const ref = useRef<HTMLDivElement>(null);
  const reduce = useReducedMotion();
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start 70%", "end 50%"] });
  const scaleY = useTransform(scrollYProgress, [0, 1], [0.08, 1]);

  return (
    <Section id="how" className="bg-muted/40">
      <Container>
        <SectionHeading
          id="how-title"
          eyebrow="How it works"
          title="From the watch on your wrist to a plan you can follow."
          description="Four steps. No new device required, and no diagnosis hiding inside a score."
        />
        <div ref={ref} className="relative mt-12 grid gap-8 md:grid-cols-[auto_1fr]">
          <div className="relative hidden w-8 justify-center md:flex" aria-hidden>
            <div className="absolute inset-y-0 w-px bg-border" />
            <motion.div
              className="absolute inset-y-0 left-1/2 w-px origin-top -translate-x-1/2 bg-brand-600"
              style={{ scaleY: reduce ? 1 : scaleY }}
            />
          </div>
          <ol className="space-y-4">
            {steps.map((step, index) => (
              <li key={step.title} className="rounded-3xl border border-border bg-card p-6 shadow-soft">
                <p className="text-sm font-bold text-brand-600">0{index + 1}</p>
                <h3 className="mt-2 text-xl">{step.title}</h3>
                <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">{step.body}</p>
              </li>
            ))}
          </ol>
        </div>
      </Container>
    </Section>
  );
}
