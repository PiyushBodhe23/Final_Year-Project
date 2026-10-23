"use client";

import { useEffect, useState } from "react";

import { usePatientId } from "@/components/dashboard/shell";
import { Gauge } from "@/components/dashboard/viz";
import { api, type Risk } from "@/lib/api";

export default function HowItWorksPage() {
  const patientId = usePatientId();
  const [method, setMethod] = useState<Record<string, unknown> | null>(null);
  const [glucose, setGlucose] = useState(110);
  const [steps, setSteps] = useState(6000);
  const [sleep, setSleep] = useState(7);
  const [scores, setScores] = useState<Risk[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.methodology().then(setMethod).catch((reason: Error) => setError(reason.message));
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      api
        .whatIf(patientId, { fasting_glucose: glucose, steps, sleep_hours: sleep })
        .then(setScores)
        .catch((reason: Error) => setError(reason.message));
    }, 350);
    return () => clearTimeout(timer);
  }, [patientId, glucose, steps, sleep]);

  const idrs = (method?.idrs ?? {}) as { activity?: Record<string, number>; family_history?: Record<string, number> };

  return (
    <div className="space-y-6">
      <h1 className="font-display text-3xl font-bold">How the risk range is calculated</h1>
      {error ? <p className="text-sm text-[#ef4444]">{error}</p> : null}
      <section className="grid gap-4 md:grid-cols-3">
        <Card title="Diabetes baseline" body={String(method?.diabetes_baseline ?? "")} />
        <Card title="Cardiac baseline" body={String(method?.cardiac_baseline ?? "")} />
        <Card title="Composite" body={String(method?.composite ?? "")} />
      </section>
      <section className="rounded-3xl border border-border bg-card p-5">
        <h2 className="font-semibold">IDRS activity and family points</h2>
        <p className="mt-1 text-sm text-muted-foreground">{String(method?.idrs_citation ?? "")}</p>
        <pre className="mt-3 overflow-auto text-sm">{JSON.stringify({ activity: idrs.activity, family: idrs.family_history, wearable: method?.wearable_weights, bands: method?.bands }, null, 2)}</pre>
        <p className="mt-3 text-sm text-muted-foreground">{String(method?.uncertainty ?? "")}</p>
      </section>
      <section className="rounded-3xl border border-border bg-card p-5">
        <h2 className="mb-3 font-semibold">What-if for this patient</h2>
        <p className="mb-4 text-sm text-muted-foreground">These sliders recompute the score and do not replace the saved report.</p>
        <Slider label="Fasting glucose" min={70} max={180} step={1} value={glucose} unit="mg/dL" onChange={setGlucose} />
        <Slider label="Daily steps" min={2000} max={12000} step={100} value={steps} unit="steps" onChange={setSteps} />
        <Slider label="Sleep" min={4} max={9} step={0.1} value={sleep} unit="hours" onChange={setSleep} />
        <div className="mt-4 grid gap-4 md:grid-cols-2">
          {scores.map((score) => (
            <div key={score.disease}>
              <h3 className="text-sm font-semibold uppercase text-muted-foreground">{score.disease}</h3>
              <Gauge score={score.composite} low={score.ci_low} high={score.ci_high} band={score.band} />
            </div>
          ))}
        </div>
      </section>
      <section>
        <h2 className="font-semibold">Limitations</h2>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted-foreground">
          <li>Pima is a small, demographically narrow teaching set. Framingham here is a public teaching extract.</li>
          <li>Wearable days are simulated and linked synthetically. Weights are heuristics, not a validated clinical model.</li>
          <li>The tool does not diagnose. Future work is an Indian cohort reviewed with clinicians.</li>
        </ul>
      </section>
    </div>
  );
}

function Card({ title, body }: { title: string; body: string }) {
  return (
    <article className="rounded-3xl border border-border bg-card p-4">
      <h2 className="text-sm font-semibold text-muted-foreground">{title}</h2>
      <p className="mt-2 font-mono text-sm">{body}</p>
    </article>
  );
}

function Slider({
  label,
  min,
  max,
  step,
  value,
  unit,
  onChange,
}: {
  label: string;
  min: number;
  max: number;
  step: number;
  value: number;
  unit: string;
  onChange: (value: number) => void;
}) {
  return (
    <label className="mb-3 block text-sm">
      <span className="mb-1 flex justify-between">
        <span>{label}</span>
        <span>
          {value} {unit}
        </span>
      </span>
      <input className="w-full" type="range" min={min} max={max} step={step} value={value} onChange={(event) => onChange(Number(event.target.value))} />
    </label>
  );
}
