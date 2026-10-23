"use client";

import { useEffect, useState } from "react";
import { ShieldAlert } from "lucide-react";

import { usePatientId } from "@/components/dashboard/shell";
import { api, type Patient } from "@/lib/api";

type LabDef = {
  key: keyof NonNullable<Patient["clinical"]>;
  label: string;
  unit: string;
  good: string;
  normalMax: number;
  elevatedMin?: number;
  desc: string;
};

const LABS: LabDef[] = [
  {
    key: "fasting_glucose",
    label: "Fasting Blood Glucose",
    unit: "mg/dL",
    good: "70–99 mg/dL",
    normalMax: 99,
    elevatedMin: 126,
    desc: "Key indicator of fasting glycemic control. Values 100–125 mg/dL indicate prediabetes under ADA and ICMR guidelines.",
  },
  {
    key: "hba1c",
    label: "Hemoglobin A1c (HbA1c)",
    unit: "%",
    good: "< 5.7%",
    normalMax: 5.6,
    elevatedMin: 6.5,
    desc: "Reflects average blood glucose over the preceding 2–3 months. Values 5.7–6.4% represent high risk for diabetes progression.",
  },
  {
    key: "sys_bp",
    label: "Systolic Blood Pressure",
    unit: "mmHg",
    good: "< 120 mmHg",
    normalMax: 120,
    elevatedMin: 140,
    desc: "Maximum arterial pressure during cardiac contraction. Persistent systolic elevations correlate with vascular wall stiffness.",
  },
  {
    key: "dia_bp",
    label: "Diastolic Blood Pressure",
    unit: "mmHg",
    good: "< 80 mmHg",
    normalMax: 80,
    elevatedMin: 90,
    desc: "Arterial pressure when heart rests between beats. >80 mmHg indicates elevated diastolic tone according to AHA 2017.",
  },
  {
    key: "total_chol",
    label: "Total Serum Cholesterol",
    unit: "mg/dL",
    good: "< 200 mg/dL",
    normalMax: 200,
    elevatedMin: 240,
    desc: "Sum of circulating cholesterol fractions. Higher levels promote atherosclerotic plaque formation.",
  },
  {
    key: "ldl",
    label: "Low-Density Lipoprotein (LDL)",
    unit: "mg/dL",
    good: "< 100 mg/dL",
    normalMax: 100,
    elevatedMin: 160,
    desc: "Primary atherogenic lipoprotein. High-yield target for cardiovascular risk reduction and dietary intervention.",
  },
  {
    key: "hdl",
    label: "High-Density Lipoprotein (HDL)",
    unit: "mg/dL",
    good: "> 40 (M), > 50 (F) mg/dL",
    normalMax: 60,
    desc: "Protective lipoprotein facilitating reverse cholesterol transport. Aerobic activity and healthy fats help raise HDL.",
  },
  {
    key: "triglycerides",
    label: "Serum Triglycerides",
    unit: "mg/dL",
    good: "< 150 mg/dL",
    normalMax: 150,
    elevatedMin: 200,
    desc: "Circulating fat molecules sensitive to refined carbohydrate consumption and sedentary lifestyle.",
  },
];

function getLabStatus(val: number | null | undefined, lab: LabDef): { status: string; color: string; badgeColor: string } {
  if (val === null || val === undefined) {
    return { status: "Missing", color: "bg-muted", badgeColor: "text-muted-foreground bg-muted" };
  }
  if (lab.key === "hdl") {
    if (val >= 50) return { status: "Optimal", color: "bg-emerald-500", badgeColor: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20" };
    if (val >= 40) return { status: "Borderline", color: "bg-amber-500", badgeColor: "text-amber-500 bg-amber-500/10 border-amber-500/20" };
    return { status: "Low Protective", color: "bg-rose-500", badgeColor: "text-rose-500 bg-rose-500/10 border-rose-500/20" };
  }
  if (val <= lab.normalMax) {
    return { status: "Optimal", color: "bg-emerald-500", badgeColor: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20" };
  }
  if (lab.elevatedMin && val >= lab.elevatedMin) {
    return { status: "Elevated", color: "bg-rose-500", badgeColor: "text-rose-500 bg-rose-500/10 border-rose-500/20" };
  }
  return { status: "Borderline", color: "bg-amber-500", badgeColor: "text-amber-500 bg-amber-500/10 border-amber-500/20" };
}

export default function ClinicalPage() {
  const patientId = usePatientId();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api.patient(patientId).then(setPatient).catch((reason: Error) => setError(reason.message));
  }, [patientId]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display text-3xl font-extrabold tracking-tight">Clinical Laboratory Biomarkers</h1>
          <p className="text-sm text-muted-foreground">
            Venous laboratory profile used for Layer A clinical baseline scoring (Indian IDRS & Framingham 10-Year CHD).
          </p>
        </div>
        {patient ? (
          <span className="rounded-full border border-border bg-card px-3 py-1 text-xs font-semibold">
            Patient: {patient.name} ({patient.age} {patient.sex})
          </span>
        ) : null}
      </div>

      {error ? <p className="text-sm text-rose-500">{error}</p> : null}

      <div className="grid gap-4 sm:grid-cols-2">
        {LABS.map((lab) => {
          const value = patient?.clinical?.[lab.key];
          const numeric = typeof value === "number" ? value : null;
          const status = getLabStatus(numeric, lab);
          const maxScale = lab.key === "hba1c" ? 14 : lab.key.includes("bp") ? 220 : 320;
          const barWidth = numeric !== null ? Math.min(100, (numeric / maxScale) * 100) : 0;

          return (
            <article key={lab.key} className="flex flex-col justify-between rounded-3xl border border-border bg-card p-5 shadow-sm">
              <div>
                <div className="flex items-center justify-between gap-2 pb-1">
                  <span className="font-medium text-foreground">{lab.label}</span>
                  <span className={`rounded-full border px-2.5 py-0.5 text-xs font-semibold ${status.badgeColor}`}>
                    {status.status}
                  </span>
                </div>

                <div className="my-2 flex items-baseline gap-1.5">
                  <span className="font-mono text-2xl font-bold text-foreground">
                    {numeric !== null ? numeric : "—"}
                  </span>
                  <span className="text-xs text-muted-foreground">{lab.unit}</span>
                  <span className="ml-auto text-xs text-muted-foreground">Reference: {lab.good}</span>
                </div>

                {/* Progress bar */}
                <div className="relative my-3 h-2 w-full overflow-hidden rounded-full bg-muted/60">
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${status.color}`}
                    style={{ width: `${Math.max(4, barWidth)}%` }}
                  />
                </div>

                <p className="text-xs text-muted-foreground leading-relaxed">{lab.desc}</p>
              </div>
            </article>
          );
        })}
      </div>

      <div className="rounded-2xl border border-border bg-muted/20 p-4 text-xs text-muted-foreground">
        <p className="flex items-center gap-1.5 font-semibold text-foreground">
          <ShieldAlert className="h-4 w-4" />
          <span>Educational Reference Notice</span>
        </p>
        <p className="mt-1">
          Reference bands are drawn from ADA Standards of Medical Care in Diabetes and ICMR Guidelines for Management of Type 2 Diabetes in India.
          Clinical diagnosis requires repeat confirmatory lab testing supervised by a licensed medical practitioner.
        </p>
      </div>
    </div>
  );
}
