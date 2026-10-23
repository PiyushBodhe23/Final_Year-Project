"use client";

import { useEffect, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import {
  Activity,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  Heart,
  MessageSquare,
  Moon,
  ShieldCheck,
  Sparkles,
  Zap,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import { Container } from "@/components/ui/container";
import { trustBadges } from "@/data/home";

const HERO_SLIDES = [
  {
    id: 1,
    image: "/images/hero/slide-1.jpg",
    badge: "Always Quietly Watching Out For You",
    titlePrefix: "You're Never",
    titleHighlight: "Doing This Alone",
    description:
      "Connect your wearable to turn everyday metrics like heart rate, HRV, and sleep into gentle, life-saving clinical insights.",
    label: "Core Wellness",
  },
  {
    id: 2,
    image: "/images/hero/slide-2.jpg",
    badge: "Continuous Autonomic & Cardiovascular Telemetry",
    titlePrefix: "Detect Cardiac Strain",
    titleHighlight: "Years In Advance",
    description:
      "Our ML models continuously analyze pulse drift and autonomic recovery markers during daily activity to preempt hypertensive spikes.",
    label: "Cardio Trends",
  },
  {
    id: 3,
    image: "/images/hero/slide-3.jpg",
    badge: "Nocturnal Hypoxia & Autonomic Recovery",
    titlePrefix: "Restorative Sleep With",
    titleHighlight: "Zero Clinic Hassle",
    description:
      "Continuous nocturnal SpO₂ monitoring flags sleep apnea and early insulin resistance patterns while you rest comfortably at home.",
    label: "Sleep & SpO₂",
  },
  {
    id: 4,
    image: "/images/hero/slide-4.jpg",
    badge: "Clinical RAG Intelligence & Indian Telemetry Baseline",
    titlePrefix: "Explainable Risk",
    titleHighlight: "At Your Fingertips",
    description:
      "Our clinical AI assistant synthesizes 180 days of wearable history with instant, medical-grade precautions and proactive lifestyle guidance.",
    label: "Metabolic AI",
  },
];

const PREVIEW_PERSONAS = [
  {
    id: 1,
    name: "Priya",
    age: 28,
    sex: "F",
    bmi: 22.0,
    healthScore: 84,
    diabetesBand: "Low",
    cardiacBand: "Low",
    rhr: 58,
    spo2: 98,
    sleep: 7.8,
    alertTitle: "Nominal Baseline",
    alertDesc: "Vitals within optimal range. Consistent 10k daily steps.",
    alertTone: "border-emerald-500/40 bg-emerald-500/20 text-emerald-300",
  },
  {
    id: 2,
    name: "Rahul",
    age: 45,
    sex: "M",
    bmi: 28.0,
    healthScore: 54,
    diabetesBand: "Moderate",
    cardiacBand: "Moderate",
    rhr: 76,
    spo2: 95,
    sleep: 6.1,
    alertTitle: "Moderate Risk Drift",
    alertDesc: "Fasting glucose 112 mg/dL with rising 30d resting heart rate.",
    alertTone: "border-amber-500/40 bg-amber-500/20 text-amber-300",
  },
  {
    id: 3,
    name: "Suresh",
    age: 58,
    sex: "M",
    bmi: 31.0,
    healthScore: 28,
    diabetesBand: "High",
    cardiacBand: "High",
    rhr: 88,
    spo2: 91,
    sleep: 5.2,
    alertTitle: "High Priority Alert",
    alertDesc: "Nocturnal SpO₂ dips <92% with hypertension & smoking history.",
    alertTone: "border-rose-500/40 bg-rose-500/20 text-rose-300",
  },
];

export function Hero() {
  const reduce = useReducedMotion();
  const float = reduce ? undefined : { y: [0, -8, 0] };

  const [currentSlide, setCurrentSlide] = useState(0);
  const [selectedPersona, setSelectedPersona] = useState(PREVIEW_PERSONAS[1]); // Rahul default
  const [isPaused, setIsPaused] = useState(false);

  // Auto-switch background slides every 5.5 seconds
  useEffect(() => {
    if (isPaused) return;
    const interval = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % HERO_SLIDES.length);
    }, 5500);
    return () => clearInterval(interval);
  }, [isPaused]);

  const activeSlide = HERO_SLIDES[currentSlide];

  const handlePrev = () => {
    setCurrentSlide((prev) => (prev - 1 + HERO_SLIDES.length) % HERO_SLIDES.length);
  };

  const handleNext = () => {
    setCurrentSlide((prev) => (prev + 1) % HERO_SLIDES.length);
  };

  return (
    <section
      id="top"
      aria-label="Hero Showcase"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
      className="relative min-h-[680px] lg:min-h-[760px] w-full overflow-hidden bg-slate-950 flex flex-col justify-between"
    >
      {/* 4 Switching Background Images with Ken-Burns and Crossfade */}
      <div className="absolute inset-0 z-0">
        {HERO_SLIDES.map((slide, index) => {
          const isActive = index === currentSlide;
          return (
            <div
              key={slide.id}
              className={`absolute inset-0 transition-opacity duration-1000 ease-in-out ${
                isActive ? "opacity-100 z-10" : "opacity-0 z-0 pointer-events-none"
              }`}
            >
              <div
                className={`h-full w-full bg-cover bg-center transition-transform duration-[7000ms] ease-out ${
                  isActive ? "scale-105" : "scale-100"
                }`}
                style={{
                  backgroundImage: `url(${slide.image})`,
                  backgroundPosition: "center 30%",
                }}
              />
            </div>
          );
        })}

        {/* Directional Cinematic Gradient Overlay matching reference image */}
        {/* Deep dark gradient on the left for maximum text contrast, fading out to reveal the fitness photo on the right */}
        <div className="absolute inset-0 z-20 bg-gradient-to-r from-slate-950 via-slate-950/85 via-45% to-slate-950/30 lg:to-transparent" />

        {/* Subtle top & bottom vignette to blend with navbar and trustbar */}
        <div className="absolute inset-0 z-20 bg-gradient-to-t from-slate-950 via-transparent to-slate-950/40" />

        {/* Ambient atmospheric glows */}
        <div className="pointer-events-none absolute -left-20 top-20 z-20 h-96 w-96 rounded-full bg-blue-600/15 blur-3xl" />
        <div className="pointer-events-none absolute right-10 top-32 z-20 h-80 w-80 rounded-full bg-cyan-500/10 blur-3xl" />
      </div>

      {/* Main Content Area */}
      <div className="relative z-30 pt-10 pb-12 sm:pt-16 sm:pb-16 lg:pt-20 lg:pb-20">
        <Container className="grid items-center gap-10 lg:grid-cols-[1.15fr_0.85fr]">
          {/* Left Column: Headlines, CTAs, App Badges, Device Compatibility */}
          <div className="max-w-2xl">
            {/* Top Pill Badge */}
            <AnimatePresence mode="wait">
              <motion.div
                key={activeSlide.id}
                initial={{ opacity: 0, y: -8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 8 }}
                transition={{ duration: 0.35 }}
                className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-4 py-1.5 text-xs font-semibold uppercase tracking-wider text-white shadow-sm backdrop-blur-md"
              >
                <Sparkles className="h-3.5 w-3.5 text-cyan-300 animate-pulse" />
                <span>{activeSlide.badge}</span>
              </motion.div>
            </AnimatePresence>

            {/* Dynamic Headline with Multi-stop Gradient */}
            <AnimatePresence mode="wait">
              <motion.div
                key={activeSlide.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.45 }}
              >
                <h1 className="mt-5 text-4xl leading-[1.08] font-black tracking-tight text-white sm:text-5xl lg:text-6xl drop-shadow-sm">
                  {activeSlide.titlePrefix}{" "}
                  <span className="block bg-gradient-to-r from-sky-400 via-indigo-300 to-fuchsia-400 bg-clip-text text-transparent">
                    {activeSlide.titleHighlight}
                  </span>
                </h1>

                <p className="mt-5 text-base sm:text-lg leading-relaxed text-slate-200 drop-shadow-sm">
                  {activeSlide.description}
                </p>
              </motion.div>
            </AnimatePresence>

            {/* Primary Action & Live Cohort Status */}
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <Button
                size="lg"
                className="h-12 rounded-xl bg-white px-8 text-sm font-bold text-slate-900 shadow-xl shadow-black/30 hover:bg-slate-100 hover:scale-[1.02] active:scale-[0.98] transition-all"
                asChild
              >
                <a href="/dashboard">
                  <span>Launch Live Dashboard</span>
                  <ArrowRight className="ml-2 h-4 w-4" />
                </a>
              </Button>

              <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3.5 py-2 text-xs font-medium text-slate-200 backdrop-blur-md">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400" />
                </span>
                <span>100 Patient Cohort Active</span>
              </div>
            </div>

            {/* Clinical Telemetry & Screening Highlights (Non-repeating, key platform stats) */}
            <div className="mt-8 grid grid-cols-3 gap-3 border-t border-white/15 pt-5 max-w-lg">
              <div className="rounded-xl border border-white/10 bg-white/5 p-3 backdrop-blur-xs">
                <div className="text-xl font-extrabold text-white sm:text-2xl">100</div>
                <div className="text-[11px] font-medium text-slate-300">Cohort Profiles</div>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-3 backdrop-blur-xs">
                <div className="text-xl font-extrabold text-cyan-400 sm:text-2xl">180d</div>
                <div className="text-[11px] font-medium text-slate-300">Continuous Data</div>
              </div>
              <div className="rounded-xl border border-white/10 bg-white/5 p-3 backdrop-blur-xs">
                <div className="text-xl font-extrabold text-emerald-400 sm:text-2xl">Dual ML</div>
                <div className="text-[11px] font-medium text-slate-300">Diabetes & CVD</div>
              </div>
            </div>

            {/* Trust Badges */}
            <div className="mt-5 flex flex-wrap gap-2">
              {trustBadges.map((item) => (
                <span
                  key={item}
                  className="inline-flex items-center gap-1.5 rounded-full border border-white/15 bg-slate-900/60 px-3 py-1 text-[11px] font-medium text-slate-200 backdrop-blur-sm"
                >
                  <ShieldCheck className="h-3.5 w-3.5 text-emerald-400" aria-hidden />
                  {item}
                </span>
              ))}
            </div>
          </div>

          {/* Right Column: Live Interactive Telemetry Card (Glassmorphism dark card) */}
          <div className="relative mx-auto w-full max-w-md lg:ml-auto">
            <motion.div
              animate={float}
              transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
              className="rounded-[2rem] border border-white/20 bg-slate-950/80 p-6 shadow-2xl backdrop-blur-2xl text-white"
            >
              {/* Persona Switcher Tabs */}
              <div className="mb-4 flex items-center justify-between border-b border-white/15 pb-3">
                <div>
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                    Live Telemetry Preview
                  </span>
                  <div className="flex items-center gap-1.5 font-bold text-white">
                    <span>{selectedPersona.name}</span>
                    <span className="text-xs text-slate-400">
                      ({selectedPersona.age}y {selectedPersona.sex} · BMI {selectedPersona.bmi})
                    </span>
                  </div>
                </div>

                <div className="flex gap-1 rounded-full border border-white/15 bg-white/10 p-1 backdrop-blur-sm">
                  {PREVIEW_PERSONAS.map((p) => (
                    <button
                      key={p.id}
                      type="button"
                      onClick={() => setSelectedPersona(p)}
                      className={`rounded-full px-2.5 py-0.5 text-xs font-semibold transition-all ${
                        selectedPersona.id === p.id
                          ? "bg-blue-600 text-white shadow-md shadow-blue-500/30"
                          : "text-slate-300 hover:text-white hover:bg-white/10"
                      }`}
                    >
                      {p.name}
                    </button>
                  ))}
                </div>
              </div>

              {/* Score Ring & Summary */}
              <div className="flex items-center gap-5 my-2">
                <ScoreRing score={selectedPersona.healthScore} />
                <div>
                  <div className="flex items-baseline gap-1">
                    <span className="font-display text-4xl font-extrabold text-white">
                      {selectedPersona.healthScore}
                    </span>
                    <span className="text-xs text-slate-400">/ 100</span>
                  </div>
                  <p className="text-xs font-semibold uppercase tracking-wide text-cyan-400">
                    Health Risk Index
                  </p>
                  <p className="mt-1 text-xs text-slate-300 leading-snug">
                    {selectedPersona.healthScore > 75
                      ? "Optimal autonomic & metabolic telemetry."
                      : selectedPersona.healthScore > 45
                      ? "Borderline elevated metabolic markers."
                      : "High risk profile requiring clinical attention."}
                  </p>
                </div>
              </div>

              {/* Vitals Telemetry Row */}
              <div className="my-4 grid grid-cols-3 gap-2 rounded-2xl border border-white/10 bg-white/5 p-3 text-center text-xs backdrop-blur-xs">
                <div>
                  <span className="flex items-center justify-center gap-1 text-[10px] uppercase text-slate-400">
                    <Heart className="h-3 w-3 text-rose-400" />
                    <span>Resting HR</span>
                  </span>
                  <span className="font-mono text-sm font-bold text-white">{selectedPersona.rhr} bpm</span>
                </div>
                <div>
                  <span className="flex items-center justify-center gap-1 text-[10px] uppercase text-slate-400">
                    <Activity className="h-3 w-3 text-cyan-400" />
                    <span>Min SpO₂</span>
                  </span>
                  <span className="font-mono text-sm font-bold text-white">{selectedPersona.spo2}%</span>
                </div>
                <div>
                  <span className="flex items-center justify-center gap-1 text-[10px] uppercase text-slate-400">
                    <Moon className="h-3 w-3 text-blue-400" />
                    <span>Sleep</span>
                  </span>
                  <span className="font-mono text-sm font-bold text-white">{selectedPersona.sleep}h</span>
                </div>
              </div>

              {/* Risk Bands Meter */}
              <div className="space-y-2">
                <div className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 p-2 text-xs">
                  <span className="flex items-center gap-1.5 font-medium text-slate-200">
                    <Zap className="h-3.5 w-3.5 text-amber-400" />
                    <span>Diabetes Screening</span>
                  </span>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${
                      selectedPersona.diabetesBand === "High"
                        ? "bg-rose-500/20 text-rose-400"
                        : selectedPersona.diabetesBand === "Moderate"
                        ? "bg-amber-500/20 text-amber-400"
                        : "bg-emerald-500/20 text-emerald-400"
                    }`}
                  >
                    {selectedPersona.diabetesBand} Risk
                  </span>
                </div>

                <div className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 p-2 text-xs">
                  <span className="flex items-center gap-1.5 font-medium text-slate-200">
                    <Heart className="h-3.5 w-3.5 text-rose-400" />
                    <span>Cardiovascular Screening</span>
                  </span>
                  <span
                    className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${
                      selectedPersona.cardiacBand === "High"
                        ? "bg-rose-500/20 text-rose-400"
                        : selectedPersona.cardiacBand === "Moderate"
                        ? "bg-amber-500/20 text-amber-400"
                        : "bg-emerald-500/20 text-emerald-400"
                    }`}
                  >
                    {selectedPersona.cardiacBand} Risk
                  </span>
                </div>
              </div>

              {/* Simulated Notification Notice */}
              <div className={`mt-3 rounded-2xl border p-2.5 text-xs ${selectedPersona.alertTone}`}>
                <div className="flex items-center justify-between font-semibold">
                  <span>{selectedPersona.alertTitle}</span>
                  <span className="text-[10px] opacity-80">Simulated Alert</span>
                </div>
                <p className="mt-0.5 text-[11px] opacity-90">{selectedPersona.alertDesc}</p>
              </div>

              <a
                href={`/dashboard?patient=${selectedPersona.id}`}
                className="mt-4 flex items-center justify-center gap-1.5 rounded-xl bg-blue-600/30 border border-blue-500/40 py-2.5 text-xs font-semibold text-blue-200 transition-all hover:bg-blue-600/50 hover:text-white"
              >
                <span>View {selectedPersona.name}&apos;s Complete 180-Day Telemetry →</span>
              </a>
            </motion.div>
          </div>
        </Container>
      </div>

      {/* Carousel Bottom Control Bar (4 Segmented Slide Indicators & Nav Arrows) */}
      <div className="relative z-30 border-t border-white/15 bg-black/60 backdrop-blur-xl py-3 px-4 sm:px-6">
        <Container className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          {/* Segmented 4-Slide Indicators */}
          <div className="grid grid-cols-4 gap-2 sm:gap-3 flex-1 max-w-2xl">
            {HERO_SLIDES.map((slide, index) => {
              const isActive = index === currentSlide;
              return (
                <button
                  key={slide.id}
                  type="button"
                  onClick={() => setCurrentSlide(index)}
                  className={`group relative text-left transition-all ${
                    isActive ? "opacity-100" : "opacity-60 hover:opacity-90"
                  }`}
                >
                  {/* Progress bar container */}
                  <div className="h-1 w-full overflow-hidden rounded-full bg-white/20">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        isActive
                          ? "bg-gradient-to-r from-cyan-400 to-blue-500 w-full"
                          : "w-0 group-hover:w-full group-hover:bg-white/40"
                      }`}
                    />
                  </div>
                  <div className="mt-1.5 flex items-center gap-1.5">
                    <span className="text-[10px] font-mono font-bold text-slate-400">
                      0{index + 1}
                    </span>
                    <span className="hidden sm:inline text-xs font-semibold text-white truncate">
                      {slide.label}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Slide Arrow Navigation & Status */}
          <div className="flex items-center justify-end gap-2 shrink-0">
            <span className="text-xs font-medium text-slate-400 mr-2">
              {currentSlide + 1} <span className="text-slate-600">/</span> {HERO_SLIDES.length}
            </span>
            <button
              type="button"
              onClick={handlePrev}
              aria-label="Previous background"
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/20 bg-white/10 text-white backdrop-blur-md transition-all hover:bg-white/25 active:scale-95"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              type="button"
              onClick={handleNext}
              aria-label="Next background"
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-white/20 bg-white/10 text-white backdrop-blur-md transition-all hover:bg-white/25 active:scale-95"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </Container>
      </div>

      {/* Floating Bottom-Right Quick Action Pill: "Chat with AI Assistant" (matches reference image "Chat with VITA") */}
      <a
        href="/dashboard/chat"
        className="fixed bottom-6 right-6 z-50 flex items-center gap-2.5 rounded-full bg-gradient-to-r from-sky-500 to-cyan-500 px-5 py-3 text-sm font-bold text-white shadow-xl shadow-cyan-500/35 transition-all hover:scale-105 hover:shadow-cyan-500/50 active:scale-95 group"
      >
        <span className="relative flex h-2.5 w-2.5">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75" />
          <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-white" />
        </span>
        <MessageSquare className="h-4 w-4 transition-transform group-hover:rotate-6" />
        <span>Chat with AI Assistant</span>
      </a>
    </section>
  );
}

function ScoreRing({ score }: { score: number }) {
  const radius = 36;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - score / 100);
  const color = score >= 75 ? "#34d399" : score >= 45 ? "#fbbf24" : "#f87171";

  return (
    <svg width="92" height="92" viewBox="0 0 92 92" aria-hidden className="shrink-0">
      <circle cx="46" cy="46" r={radius} fill="none" stroke="currentColor" className="text-white/15" strokeWidth="8" />
      <circle
        cx="46"
        cy="46"
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth="8"
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        transform="rotate(-90 46 46)"
        className="transition-all duration-700"
      />
    </svg>
  );
}
