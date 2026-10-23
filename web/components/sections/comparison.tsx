"use client";

import { Check, X, Shield, Activity, Sparkles, HeartPulse, Clock, FileText } from "lucide-react";
import { Container } from "@/components/ui/container";
import { Section } from "@/components/ui/section";
import { SectionHeading } from "@/components/ui/section-heading";

const COMPARISON_POINTS = [
  {
    feature: "Screening Frequency",
    traditional: "Once a year (single snapshot in time)",
    preventVital: "365-day continuous passive wearable monitoring",
    icon: Clock,
  },
  {
    feature: "Early Warning Window",
    traditional: "Detects disease after clinical threshold is crossed",
    preventVital: "Identifies prediabetic & metabolic drifts 3–5 years earlier",
    icon: Sparkles,
  },
  {
    feature: "Physiological Data Inputs",
    traditional: "Single clinic blood draw & seated BP cuff",
    preventVital: "Continuous RHR, HRV RMSSD, sleep stages, & nocturnal SpO₂",
    icon: Activity,
  },
  {
    feature: "Explainability & Method",
    traditional: "Opaque lab numbers with generic normal ranges",
    preventVital: "Transparent 70/30 hybrid scoring (ICMR IDRS + Framingham)",
    icon: Shield,
  },
  {
    feature: "Care Coordination",
    traditional: "Patient is left to decipher multi-page PDF reports",
    preventVital: "Simulated 3-way triage (Patient, Family Caregiver, Clinician)",
    icon: HeartPulse,
  },
  {
    feature: "Personal Guidance",
    traditional: "Brief 5-minute doctor consult once illness develops",
    preventVital: "Grounded RAG AI Assistant answering from patient's own vitals",
    icon: FileText,
  },
];

export function Comparison() {
  return (
    <Section id="comparison" className="bg-muted/30">
      <Container>
        <SectionHeading
          id="comparison-title"
          eyebrow="The Preventive Paradigm"
          title="Traditional Reactive Medicine vs. PreventVital Continuous Intelligence"
          description="Most chronic metabolic and cardiovascular conditions develop silently over years. See why continuous sensor telemetry combined with clinical baseline scoring creates an unprecedented early-detection advantage."
        />

        <div className="mt-12 overflow-hidden rounded-3xl border border-border bg-card shadow-sm">
          <div className="grid grid-cols-1 md:grid-cols-[1.2fr_1fr_1.2fr] border-b border-border bg-muted/40 p-4 font-semibold text-xs uppercase tracking-wider text-muted-foreground">
            <div>Physiological Capability</div>
            <div className="hidden md:block text-center text-rose-500/90">Standard Annual Checkup</div>
            <div className="hidden md:block text-center text-primary font-bold">PreventVital Platform</div>
          </div>

          <div className="divide-y divide-border">
            {COMPARISON_POINTS.map((item, idx) => {
              const Icon = item.icon;
              return (
                <div
                  key={idx}
                  className="grid grid-cols-1 md:grid-cols-[1.2fr_1fr_1.2fr] items-center p-4 text-sm transition-colors hover:bg-muted/20"
                >
                  <div className="flex items-center gap-3 font-semibold text-foreground">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                      <Icon className="h-4 w-4" />
                    </div>
                    <span>{item.feature}</span>
                  </div>

                  <div className="mt-2 md:mt-0 flex items-start md:justify-center gap-2 text-xs text-muted-foreground md:border-x md:border-border/60 md:px-4">
                    <X className="h-4 w-4 shrink-0 text-rose-500 mt-0.5" />
                    <span>{item.traditional}</span>
                  </div>

                  <div className="mt-2 md:mt-0 flex items-start md:justify-center gap-2 text-xs font-medium text-foreground md:px-4">
                    <Check className="h-4 w-4 shrink-0 text-emerald-500 mt-0.5" />
                    <span>{item.preventVital}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </Container>
    </Section>
  );
}
