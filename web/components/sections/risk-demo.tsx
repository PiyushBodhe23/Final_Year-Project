"use client";

import { useMemo, useState } from "react";
import { ArrowRight, RotateCcw, Sparkles, Zap, Heart } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Container } from "@/components/ui/container";
import { Section } from "@/components/ui/section";
import { SectionHeading } from "@/components/ui/section-heading";

export function RiskDemo() {
  const [age, setAge] = useState(42);
  const [bmi, setBmi] = useState(26);
  const [steps, setSteps] = useState(6500);
  const [sleep, setSleep] = useState(6.5);
  const [glucose, setGlucose] = useState(105);

  // Simplified Indian Diabetes Risk Score (IDRS) + Framingham approximation for interactive visual feedback
  const { diabetesRisk, cardiacRisk, compositeRisk, band, bandColor } = useMemo(() => {
    // Age factor: <35: 0, 35-49: 20, >=50: 30
    const agePts = age < 35 ? 0 : age < 50 ? 20 : 30;
    // Activity factor based on steps
    const stepPts = steps >= 9000 ? 0 : steps >= 6000 ? 15 : 30;
    // BMI / metabolic factor
    const bmiPts = bmi < 23 ? 0 : bmi < 25 ? 10 : 25;
    // Glucose impact
    const glucPts = glucose < 100 ? 0 : glucose < 126 ? 20 : 35;

    const dScore = Math.min(100, Math.max(10, Math.round(agePts * 0.7 + stepPts * 0.8 + bmiPts * 0.9 + glucPts * 0.9)));
    const cScore = Math.min(100, Math.max(8, Math.round((age - 20) * 0.8 + (bmi - 20) * 1.8 + (10000 - steps) * 0.003 + (8 - sleep) * 4)));
    const comp = Math.round(dScore * 0.55 + cScore * 0.45);

    let b = "Low";
    let color = "#10b981";
    if (comp >= 60) {
      b = "High";
      color = "#ef4444";
    } else if (comp >= 35) {
      b = "Moderate";
      color = "#f59e0b";
    }

    return {
      diabetesRisk: dScore,
      cardiacRisk: cScore,
      compositeRisk: comp,
      band: b,
      bandColor: color,
    };
  }, [age, bmi, steps, sleep, glucose]);

  const resetValues = () => {
    setAge(42);
    setBmi(26);
    setSteps(6500);
    setSleep(6.5);
    setGlucose(105);
  };

  const radius = 56;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - compositeRisk / 100);

  return (
    <Section id="assess" className="bg-muted/40">
      <Container className="grid items-center gap-10 lg:grid-cols-2">
        <div>
          <SectionHeading
            id="assess-title"
            eyebrow="Interactive Screening Tool"
            title="See how lifestyle signals dynamically move the risk needle."
            description="Adjust age, metabolic parameters, daily activity, and sleep below to see how our hybrid multi-factor model recomputes screening bands in real time."
          />

          <div className="mt-6 space-y-3 text-xs text-muted-foreground">
            <div className="flex items-start gap-2">
              <span className="font-bold text-foreground">1. Clinical Baseline (IDRS): </span>
              <span>Indian Diabetes Risk Score incorporating South Asian BMI thresholds (Normal &lt;23, Overweight &gt;25).</span>
            </div>
            <div className="flex items-start gap-2">
              <span className="font-bold text-foreground">2. Continuous Telemetry: </span>
              <span>Daily step volume and sleep regularity act as positive levers to lower composite risk.</span>
            </div>
          </div>

          <div className="mt-8 flex items-center gap-3">
            <Button asChild className="gap-2 bg-[#2563eb] text-white hover:bg-blue-700">
              <a href="/dashboard">
                <span>Open Full Patient Dashboard</span>
                <ArrowRight className="h-4 w-4" />
              </a>
            </Button>
            <Button variant="ghost" onClick={resetValues} className="gap-1.5 text-xs text-muted-foreground">
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Reset Sliders</span>
            </Button>
          </div>
        </div>

        <Card className="rounded-[2rem] border border-border bg-card p-6 shadow-xl">
          <div className="flex items-center justify-between border-b border-border/60 pb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              <span className="text-xs font-bold uppercase tracking-wider text-foreground">
                Live Simulation Output
              </span>
            </div>
            <span
              className="rounded-full px-2.5 py-0.5 text-xs font-bold uppercase tracking-wider"
              style={{ backgroundColor: `${bandColor}18`, color: bandColor }}
            >
              {band} Risk Range
            </span>
          </div>

          {/* Semicircular / Circular Score Indicator */}
          <div className="my-5 flex items-center gap-6">
            <svg width="130" height="130" viewBox="0 0 130 130" role="img" aria-label={`Composite Risk ${compositeRisk}`}>
              <circle cx="65" cy="65" r={radius} fill="none" className="text-muted/30" stroke="currentColor" strokeWidth="10" />
              <circle
                cx="65"
                cy="65"
                r={radius}
                fill="none"
                stroke={bandColor}
                strokeWidth="10"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={offset}
                transform="rotate(-90 65 65)"
                className="transition-all duration-500"
              />
              <text x="65" y="69" textAnchor="middle" className="fill-foreground font-display font-bold" fontSize="28">
                {compositeRisk}
              </text>
              <text x="65" y="86" textAnchor="middle" className="fill-muted-foreground font-mono" fontSize="10">
                / 100 PTS
              </text>
            </svg>

            <div className="space-y-2 flex-1">
              <div className="rounded-xl border border-border bg-muted/30 p-2.5 text-xs">
                <div className="flex justify-between font-semibold">
                  <span className="flex items-center gap-1 text-amber-500">
                    <Zap className="h-3.5 w-3.5" />
                    <span>Diabetes Risk</span>
                  </span>
                  <span className="font-mono">{diabetesRisk} / 100</span>
                </div>
              </div>

              <div className="rounded-xl border border-border bg-muted/30 p-2.5 text-xs">
                <div className="flex justify-between font-semibold">
                  <span className="flex items-center gap-1 text-rose-500">
                    <Heart className="h-3.5 w-3.5" />
                    <span>Cardiac Risk</span>
                  </span>
                  <span className="font-mono">{cardiacRisk} / 100</span>
                </div>
              </div>
            </div>
          </div>

          {/* Interactive Sliders */}
          <div className="space-y-4 pt-2">
            <Slider label="Age" min={20} max={75} value={age} suffix=" yrs" onChange={setAge} />
            <Slider label="Body Mass Index (BMI)" min={17} max={38} value={bmi} suffix={` (${bmi < 23 ? "Normal" : bmi < 25 ? "Overweight" : "Obese"})`} onChange={setBmi} />
            <Slider label="Fasting Blood Glucose" min={70} max={160} value={glucose} suffix=" mg/dL" onChange={setGlucose} />
            <Slider label="Daily Step Volume" min={2000} max={14000} step={250} value={steps} suffix=" steps" onChange={setSteps} />
            <Slider label="Nightly Sleep" min={4.0} max={9.5} step={0.1} value={sleep} suffix=" hrs" onChange={setSleep} />
          </div>
        </Card>
      </Container>
    </Section>
  );
}

function Slider({
  label,
  min,
  max,
  value,
  step = 1,
  suffix = "",
  onChange,
}: {
  label: string;
  min: number;
  max: number;
  value: number;
  step?: number;
  suffix?: string;
  onChange: (value: number) => void;
}) {
  const id = label.toLowerCase().replace(/[^a-z0-9]/g, "-");
  return (
    <label htmlFor={id} className="block text-xs font-semibold">
      <div className="flex justify-between">
        <span className="text-foreground">{label}</span>
        <span className="font-mono text-primary font-bold">
          {value}
          {suffix}
        </span>
      </div>
      <input
        id={id}
        className="mt-1.5 w-full accent-[#2563eb] cursor-pointer"
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </label>
  );
}
