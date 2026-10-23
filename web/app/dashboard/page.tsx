"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Brain,
  CheckCircle2,
  Heart,
  Info,
  Moon,
  RotateCcw,
  ShieldAlert,
  Sliders,
  Sparkles,
  Stethoscope,
  Zap,
} from "lucide-react";

import { patientHref, usePatientId } from "@/components/dashboard/shell";
import { Bars, Gauge, Radar } from "@/components/dashboard/viz";
import { api, bandClass, type Patient, type Risk } from "@/lib/api";

function bmiCategory(bmi?: number): { label: string; color: string } {
  if (!bmi) return { label: "Unknown", color: "text-muted-foreground bg-muted" };
  if (bmi < 18.5) return { label: "Underweight", color: "text-blue-500 bg-blue-500/10 border-blue-500/20" };
  if (bmi < 25) return { label: "Normal weight", color: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20" };
  if (bmi < 30) return { label: "Overweight", color: "text-amber-500 bg-amber-500/10 border-amber-500/20" };
  return { label: "Obese (Class I+)", color: "text-rose-500 bg-rose-500/10 border-rose-500/20" };
}

export default function OverviewPage() {
  const patientId = usePatientId();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [scores, setScores] = useState<Risk[]>([]);
  const [error, setError] = useState("");

  // What-If Simulation State
  const [showSim, setShowSim] = useState(false);
  const [simGlucose, setSimGlucose] = useState<number>(100);
  const [simSteps, setSimSteps] = useState<number>(7500);
  const [simSleep, setSimSleep] = useState<number>(7.2);
  const [simScores, setSimScores] = useState<Risk[] | null>(null);

  useEffect(() => {
    let cancel = false;
    setError("");
    setSimScores(null);

    Promise.all([api.patient(patientId), api.latest(patientId)])
      .then(async ([profile, latest]) => {
        const ready = latest.length ? latest : await api.calculate(patientId);
        if (!cancel) {
          setPatient(profile);
          setScores(ready);

          // Initialize simulation sliders from current values
          const fastG = profile?.clinical?.fasting_glucose;
          setSimGlucose(fastG ? Number(fastG) : 100);
          setSimSteps(profile?.activity_level === "high" ? 10000 : profile?.activity_level === "moderate" ? 7500 : 4500);
          setSimSleep(7.0);
        }
      })
      .catch((reason: Error) => {
        if (!cancel) {
          setError(reason.message);
        }
      });

    return () => {
      cancel = true;
    };
  }, [patientId]);

  // Run What-If simulation when sliders change
  const runSimulation = (glucose: number, steps: number, sleep: number) => {
    api
      .whatIf(patientId, { fasting_glucose: glucose, steps, sleep_hours: sleep })
      .then((res) => {
        setSimScores(res);
      })
      .catch((err) => {
        console.error(err);
      });
  };

  const resetSimulation = () => {
    const fastG = patient?.clinical?.fasting_glucose;
    const defaultG = fastG ? Number(fastG) : 100;
    const defaultSteps = patient?.activity_level === "high" ? 10000 : patient?.activity_level === "moderate" ? 7500 : 4500;
    const defaultSleep = 7.0;

    setSimGlucose(defaultG);
    setSimSteps(defaultSteps);
    setSimSleep(defaultSleep);
    setSimScores(null);
  };

  const diabetes = scores.find((s) => s.disease === "diabetes");
  const cardiac = scores.find((s) => s.disease === "cardiac");

  const simDiabetes = simScores?.find((s) => s.disease === "diabetes");
  const simCardiac = simScores?.find((s) => s.disease === "cardiac");

  const bmiMeta = bmiCategory(patient?.bmi);

  return (
    <div className="space-y-6">
      {/* Patient Profile Header */}
      <section className="relative overflow-hidden rounded-3xl border border-border bg-card p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 className="font-display text-3xl font-extrabold tracking-tight">
                {patient ? patient.name : "Loading Patient Profile…"}
              </h1>
              {patient ? (
                <span className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${bmiMeta.color}`}>
                  BMI {patient.bmi ?? "—"} · {bmiMeta.label}
                </span>
              ) : null}
              {patient?.smoking === "current" ? (
                <span className="rounded-full border border-rose-500/20 bg-rose-500/10 px-2.5 py-0.5 text-xs font-semibold text-rose-500">
                  Current Smoker
                </span>
              ) : (
                <span className="rounded-full border border-emerald-500/20 bg-emerald-500/10 px-2.5 py-0.5 text-xs font-semibold text-emerald-500">
                  Non-Smoker
                </span>
              )}
            </div>
            <p className="text-sm text-muted-foreground">
              {patient
                ? `${patient.age} years old · Biological ${patient.sex} · Waist ${patient.waist_cm ?? "—"} cm · Activity: ${patient.activity_level ?? "moderate"}`
                : "Synchronizing continuous wearable telemetry and clinical records"}
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowSim(!showSim)}
              className={`flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-medium transition-all ${
                showSim
                  ? "bg-[#2563eb] text-white shadow-md shadow-blue-500/20"
                  : "border border-border bg-muted/60 text-foreground hover:bg-muted"
              }`}
            >
              <Sliders className="h-4 w-4" />
              <span>{showSim ? "Hide What-If Simulator" : "Interactive What-If Simulator"}</span>
            </button>
            <Link
              href={patientHref("/dashboard/chat", patientId)}
              className="flex items-center gap-1.5 rounded-full bg-primary/10 px-4 py-2 text-sm font-medium text-primary transition-colors hover:bg-primary/20"
            >
              <Brain className="h-4 w-4" />
              <span>Ask AI Assistant</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </div>

        {/* Clinical Parameters Strip */}
        {patient?.clinical ? (
          <div className="mt-5 grid grid-cols-2 gap-3 border-t border-border/60 pt-4 sm:grid-cols-3 md:grid-cols-6">
            <div className="space-y-0.5">
              <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Fasting Glucose</span>
              <div className="flex items-baseline gap-1">
                <span className="font-mono text-lg font-bold text-foreground">
                  {patient.clinical.fasting_glucose ?? "—"}
                </span>
                <span className="text-[10px] text-muted-foreground">mg/dL</span>
              </div>
            </div>
            <div className="space-y-0.5">
              <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">HbA1c</span>
              <div className="flex items-baseline gap-1">
                <span className="font-mono text-lg font-bold text-foreground">
                  {patient.clinical.hba1c ? `${patient.clinical.hba1c}%` : "—"}
                </span>
              </div>
            </div>
            <div className="space-y-0.5">
              <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Blood Pressure</span>
              <div className="flex items-baseline gap-1">
                <span className="font-mono text-lg font-bold text-foreground">
                  {patient.clinical.sys_bp && patient.clinical.dia_bp
                    ? `${patient.clinical.sys_bp}/${patient.clinical.dia_bp}`
                    : "—"}
                </span>
                <span className="text-[10px] text-muted-foreground">mmHg</span>
              </div>
            </div>
            <div className="space-y-0.5">
              <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Total Cholesterol</span>
              <div className="flex items-baseline gap-1">
                <span className="font-mono text-lg font-bold text-foreground">
                  {patient.clinical.total_chol ?? "—"}
                </span>
                <span className="text-[10px] text-muted-foreground">mg/dL</span>
              </div>
            </div>
            <div className="space-y-0.5">
              <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">LDL / HDL</span>
              <div className="flex items-baseline gap-1">
                <span className="font-mono text-lg font-bold text-foreground">
                  {patient.clinical.ldl ?? "—"} / {patient.clinical.hdl ?? "—"}
                </span>
                <span className="text-[10px] text-muted-foreground">mg/dL</span>
              </div>
            </div>
            <div className="space-y-0.5">
              <span className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Family Hx Diabetes</span>
              <div className="flex items-baseline gap-1">
                <span className="text-sm font-semibold capitalize text-foreground">
                  {patient.family_hx_diabetes ?? "None"}
                </span>
              </div>
            </div>
          </div>
        ) : null}
      </section>

      {error ? (
        <div className="flex items-center gap-3 rounded-2xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-500">
          <AlertTriangle className="h-5 w-5 shrink-0" />
          <span>{error}. Ensure the FastAPI backend is running on port 8000.</span>
        </div>
      ) : null}

      {/* Interactive What-If Scenario Simulator Panel */}
      {showSim ? (
        <section className="relative overflow-hidden rounded-3xl border-2 border-blue-500/30 bg-gradient-to-br from-blue-500/5 via-card to-card p-6 shadow-lg">
          <div className="flex flex-wrap items-center justify-between gap-3 pb-4">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-blue-500" />
              <h2 className="font-display text-xl font-bold">Interactive Lifestyle & Biomarker Simulator</h2>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={resetSimulation}
                className="flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-xs font-medium text-muted-foreground hover:bg-muted hover:text-foreground"
              >
                <RotateCcw className="h-3.5 w-3.5" />
                <span>Reset to Baseline</span>
              </button>
            </div>
          </div>
          <p className="text-xs text-muted-foreground">
            Adjust the sliders below to simulate the physiological impact of lifestyle interventions (increased daily activity,
            sleep regularity, glycemic regulation). The composite risk engine recomputes instantly without overwriting clinical records.
          </p>

          <div className="mt-5 grid gap-6 md:grid-cols-3">
            <div className="space-y-2 rounded-2xl border border-border bg-card/60 p-4">
              <div className="flex justify-between text-xs font-semibold">
                <span className="flex items-center gap-1 text-foreground">
                  <Activity className="h-3.5 w-3.5 text-emerald-500" />
                  <span>Daily Steps</span>
                </span>
                <span className="font-mono text-emerald-600 dark:text-emerald-400 font-bold">{simSteps.toLocaleString()} steps</span>
              </div>
              <input
                type="range"
                min={2000}
                max={15000}
                step={250}
                value={simSteps}
                onChange={(e) => {
                  const val = Number(e.target.value);
                  setSimSteps(val);
                  runSimulation(simGlucose, val, simSleep);
                }}
                className="w-full accent-emerald-500"
              />
              <div className="flex justify-between text-[10px] text-muted-foreground">
                <span>2k (Sedentary)</span>
                <span>8k (Display Goal)</span>
                <span>15k (Athlete)</span>
              </div>
            </div>

            <div className="space-y-2 rounded-2xl border border-border bg-card/60 p-4">
              <div className="flex justify-between text-xs font-semibold">
                <span className="flex items-center gap-1 text-foreground">
                  <Moon className="h-3.5 w-3.5 text-blue-500" />
                  <span>Nightly Sleep</span>
                </span>
                <span className="font-mono text-blue-600 dark:text-blue-400 font-bold">{simSleep.toFixed(1)} hrs</span>
              </div>
              <input
                type="range"
                min={4.0}
                max={10.0}
                step={0.2}
                value={simSleep}
                onChange={(e) => {
                  const val = Number(e.target.value);
                  setSimSleep(val);
                  runSimulation(simGlucose, simSteps, val);
                }}
                className="w-full accent-blue-500"
              />
              <div className="flex justify-between text-[10px] text-muted-foreground">
                <span>4.0h (Deprived)</span>
                <span>7.5h (Target)</span>
                <span>10.0h</span>
              </div>
            </div>

            <div className="space-y-2 rounded-2xl border border-border bg-card/60 p-4">
              <div className="flex justify-between text-xs font-semibold">
                <span className="flex items-center gap-1 text-foreground">
                  <Zap className="h-3.5 w-3.5 text-amber-500" />
                  <span>Fasting Glucose</span>
                </span>
                <span className="font-mono text-amber-600 dark:text-amber-400 font-bold">{simGlucose} mg/dL</span>
              </div>
              <input
                type="range"
                min={70}
                max={180}
                step={1}
                value={simGlucose}
                onChange={(e) => {
                  const val = Number(e.target.value);
                  setSimGlucose(val);
                  runSimulation(val, simSteps, simSleep);
                }}
                className="w-full accent-amber-500"
              />
              <div className="flex justify-between text-[10px] text-muted-foreground">
                <span>70 (Optimal)</span>
                <span>99 (Normal Upper)</span>
                <span>180 (Elevated)</span>
              </div>
            </div>
          </div>

          {/* Simulation Outcome Comparison */}
          {simDiabetes && simCardiac && diabetes && cardiac ? (
            <div className="mt-5 grid gap-4 rounded-2xl border border-border bg-card p-4 sm:grid-cols-2">
              <div className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold uppercase text-muted-foreground">Simulated Diabetes Risk</span>
                  <div className="flex items-center gap-1 font-mono font-bold">
                    <span>{simDiabetes.composite.toFixed(0)} pts</span>
                    <span
                      className={`text-xs ${
                        simDiabetes.composite < diabetes.composite ? "text-emerald-500" : "text-rose-500"
                      }`}
                    >
                      ({simDiabetes.composite - diabetes.composite > 0 ? "+" : ""}
                      {(simDiabetes.composite - diabetes.composite).toFixed(0)})
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-bold ${bandClass(simDiabetes.band)}`}>{simDiabetes.band} Band</span>
                  <span className="text-xs text-muted-foreground">
                    (Baseline was {diabetes.composite.toFixed(0)} · {diabetes.band})
                  </span>
                </div>
              </div>

              <div className="space-y-1">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold uppercase text-muted-foreground">Simulated Cardiac Risk</span>
                  <div className="flex items-center gap-1 font-mono font-bold">
                    <span>{simCardiac.composite.toFixed(0)} pts</span>
                    <span
                      className={`text-xs ${
                        simCardiac.composite < cardiac.composite ? "text-emerald-500" : "text-rose-500"
                      }`}
                    >
                      ({simCardiac.composite - cardiac.composite > 0 ? "+" : ""}
                      {(simCardiac.composite - cardiac.composite).toFixed(0)})
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-bold ${bandClass(simCardiac.band)}`}>{simCardiac.band} Band</span>
                  <span className="text-xs text-muted-foreground">
                    (Baseline was {cardiac.composite.toFixed(0)} · {cardiac.band})
                  </span>
                </div>
              </div>
            </div>
          ) : null}
        </section>
      ) : null}

      {/* Primary Risk Ranges (Diabetes & Cardiovascular) */}
      <section className="grid gap-6 md:grid-cols-2">
        {[diabetes, cardiac].map((score) => {
          if (!score) return null;
          const isDiabetes = score.disease === "diabetes";
          return (
            <article
              key={score.disease}
              className="flex flex-col justify-between rounded-3xl border border-border bg-card p-6 shadow-sm transition-shadow hover:shadow-md"
            >
              <div>
                <div className="flex items-center justify-between gap-2 pb-1">
                  <div className="flex items-center gap-2">
                    {isDiabetes ? (
                      <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-amber-500/10 text-amber-500">
                        <Zap className="h-4 w-4" />
                      </div>
                    ) : (
                      <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-rose-500/10 text-rose-500">
                        <Heart className="h-4 w-4" />
                      </div>
                    )}
                    <div>
                      <h2 className="font-display text-lg font-bold capitalize">{score.disease} Risk Range</h2>
                      <span className="text-xs text-muted-foreground">
                        {isDiabetes ? "Indian IDRS + Calibrated Pima ML Model" : "Framingham 10-Yr CHD + Calibrated Ensemble"}
                      </span>
                    </div>
                  </div>
                  <span
                    className={`rounded-full border px-3 py-1 text-xs font-bold uppercase tracking-wider ${
                      score.band === "High"
                        ? "border-rose-500/20 bg-rose-500/10 text-rose-500"
                        : score.band === "Moderate"
                        ? "border-amber-500/20 bg-amber-500/10 text-amber-500"
                        : "border-emerald-500/20 bg-emerald-500/10 text-emerald-500"
                    }`}
                  >
                    {score.band} Risk
                  </span>
                </div>

                <div className="my-2">
                  <Gauge score={score.composite} low={score.ci_low} high={score.ci_high} band={score.band} />
                </div>

                {/* Explainable Decomposition: Layer A, B, C */}
                <div className="my-3 grid grid-cols-3 gap-2 rounded-2xl bg-muted/40 p-3 text-center text-xs">
                  <div>
                    <span className="block text-[10px] uppercase tracking-wider text-muted-foreground">Layer A (Clinical)</span>
                    <span className="font-mono text-sm font-bold text-foreground">{score.baseline.toFixed(0)} / 100</span>
                    <span className="block text-[9px] text-muted-foreground">Weight: 70%</span>
                  </div>
                  <div>
                    <span className="block text-[10px] uppercase tracking-wider text-muted-foreground">Layer B (Wearables)</span>
                    <span className="font-mono text-sm font-bold text-foreground">{score.wearable_score.toFixed(0)} / 100</span>
                    <span className="block text-[9px] text-muted-foreground">Weight: 30%</span>
                  </div>
                  <div>
                    <span className="block text-[10px] uppercase tracking-wider text-muted-foreground">Confidence</span>
                    <span className="font-mono text-sm font-bold capitalize text-foreground">{score.confidence}</span>
                    <span className="block text-[9px] text-muted-foreground">{score.borderline ? "Borderline band" : "Stable band"}</span>
                  </div>
                </div>

                {/* Factor Contribution Waterfall */}
                <div className="mt-4 space-y-1">
                  <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Top Contributing Factors</h3>
                  <Bars rows={score.factors.map((f) => ({ label: f.name, value: f.points }))} />
                </div>
              </div>

              {score.warnings && score.warnings.length > 0 ? (
                <div className="mt-4 rounded-xl border border-amber-500/20 bg-amber-500/5 p-2.5 text-xs text-amber-600 dark:text-amber-400">
                  <div className="flex items-center gap-1.5 font-semibold">
                    <Info className="h-3.5 w-3.5" />
                    <span>Clinical Screening Note:</span>
                  </div>
                  <ul className="mt-1 list-disc space-y-0.5 pl-4 text-[11px]">
                    {score.warnings.map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
            </article>
          );
        })}
      </section>

      {/* 5-Dimensional Wearable Concern Radar vs Healthy Target */}
      {diabetes?.subscores ? (
        <section className="grid gap-6 lg:grid-cols-[1.2fr_1fr]">
          <article className="rounded-3xl border border-border bg-card p-6 shadow-sm">
            <div className="flex items-center justify-between pb-2">
              <div>
                <h2 className="font-display text-lg font-bold">Wearable Concern Radar vs Healthy Benchmark</h2>
                <p className="text-xs text-muted-foreground">
                  Evaluates 30-day continuous sensor telemetry across 5 physiological domains. The center indicates optimal health;
                  proximity to the outer rim indicates elevated risk.
                </p>
              </div>
            </div>
            <Radar scores={diabetes.subscores} />
          </article>

          {/* Actionable Clinical Guidance */}
          <article className="flex flex-col justify-between rounded-3xl border border-border bg-card p-6 shadow-sm">
            <div className="space-y-4">
              <div className="flex items-center gap-2 pb-1">
                <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-500/10 text-blue-500">
                  <Stethoscope className="h-4 w-4" />
                </div>
                <div>
                  <h2 className="font-display text-lg font-bold">Personalized Preventive Action Plan</h2>
                  <span className="text-xs text-muted-foreground">Evidence-based guidelines (ICMR, WHO, ADA, AHA)</span>
                </div>
              </div>

              <ul className="space-y-3 text-xs">
                <li className="flex gap-2.5 rounded-2xl border border-border bg-muted/30 p-3">
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500" />
                  <div>
                    <span className="font-semibold text-foreground">Physical Activity Lever: </span>
                    <span className="text-muted-foreground">
                      Target 8,000–10,000 brisk steps daily (or 150 min/wk moderate activity). Consistent daily movement improves insulin
                      sensitivity and endothelial function.
                    </span>
                  </div>
                </li>

                <li className="flex gap-2.5 rounded-2xl border border-border bg-muted/30 p-3">
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-blue-500" />
                  <div>
                    <span className="font-semibold text-foreground">Sleep & Autonomic Recovery: </span>
                    <span className="text-muted-foreground">
                      Maintain 7.0–8.5 hours of uninterrupted nightly sleep. Irregular sleep cycles correlate with nocturnal sympathetic
                      overactivity and elevated morning cortisol.
                    </span>
                  </div>
                </li>

                <li className="flex gap-2.5 rounded-2xl border border-border bg-muted/30 p-3">
                  <CheckCircle2 className="h-4 w-4 shrink-0 text-amber-500" />
                  <div>
                    <span className="font-semibold text-foreground">Glycemic & Metabolic Monitoring: </span>
                    <span className="text-muted-foreground">
                      Schedule a confirmatory venous fasting blood glucose and HbA1c panel with your clinician. Emphasize complex whole
                      grains and dietary fiber.
                    </span>
                  </div>
                </li>
              </ul>
            </div>

            <div className="mt-5 border-t border-border pt-4">
              <Link
                href={patientHref("/dashboard/chat", patientId)}
                className="flex w-full items-center justify-center gap-2 rounded-2xl bg-[#2563eb] py-2.5 text-xs font-semibold text-white shadow-md shadow-blue-500/20 transition-all hover:bg-blue-700"
              >
                <Brain className="h-4 w-4" />
                <span>Discuss This Record with PreventVital AI Assistant</span>
              </Link>
            </div>
          </article>
        </section>
      ) : null}

      {/* Academic Disclaimer Footer */}
      {diabetes?.disclaimer ? (
        <div className="rounded-2xl border border-border/80 bg-muted/20 p-4 text-xs text-muted-foreground">
          <p className="flex items-center gap-1.5 font-semibold text-foreground">
            <ShieldAlert className="h-4 w-4 text-muted-foreground" />
            <span>Academic Methodology Notice</span>
          </p>
          <p className="mt-1">{diabetes.disclaimer}</p>
        </div>
      ) : null}
    </div>
  );
}
