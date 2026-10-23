/** Empty in the browser so Next.js can proxy `/api` to the FastAPI process. */
export const API_URL = process.env.NEXT_PUBLIC_API_URL || "";

export type Patient = {
  id: number;
  name: string;
  age: number;
  sex: string;
  height_cm?: number;
  weight_kg?: number;
  waist_cm?: number;
  bmi?: number;
  smoking?: string;
  cigs_per_day?: number;
  alcohol?: string;
  activity_level?: string;
  diet_quality?: string;
  stress_level?: number;
  family_hx_diabetes?: string;
  family_hx_cvd?: boolean;
  bp_meds?: boolean;
  existing_hypertension?: boolean;
  existing_diabetes?: boolean;
  prior_stroke?: boolean;
  clinical?: {
    sys_bp: number | null;
    dia_bp: number | null;
    fasting_glucose: number | null;
    hba1c: number | null;
    total_chol: number | null;
    hdl: number | null;
    ldl: number | null;
    triglycerides: number | null;
  } | null;
  disclaimer?: string;
};

export type NewPatientInput = {
  name: string;
  age: number;
  sex: string;
  height_cm?: number;
  weight_kg?: number;
  waist_cm?: number;
  smoking?: string;
  cigs_per_day?: number;
  alcohol?: string;
  activity_level?: string;
  diet_quality?: string;
  stress_level?: number;
  family_hx_diabetes?: string;
  family_hx_cvd?: boolean;
  bp_meds?: boolean;
  existing_hypertension?: boolean;
  existing_diabetes?: boolean;
  prior_stroke?: boolean;
  sys_bp?: number;
  dia_bp?: number;
  fasting_glucose?: number;
  hba1c?: number;
  total_chol?: number;
  hdl?: number;
  ldl?: number;
  triglycerides?: number;
};

export type Factor = { name: string; detail: string; points: number };

export type Risk = {
  disease: string;
  baseline: number;
  wearable_score: number;
  subscores: Record<string, number>;
  composite: number;
  ci_low: number;
  ci_high: number;
  band: string;
  borderline: boolean;
  confidence: string;
  warnings: string[];
  factors: Factor[];
  disclaimer: string;
  ml_probability?: number | null;
  idrs?: number | null;
  point_score?: number | null;
};

export type SeriesPoint = Record<string, number | string | null> & { date: string };

export type Trend = {
  metric: string;
  mean_30: number;
  mean_7: number;
  slope_per_day: number;
  trend: string;
  anomaly_dates: string[];
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, { ...init, cache: "no-store" });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  return response.json() as Promise<T>;
}

export const api = {
  patients: () => request<Patient[]>("/api/patients"),
  patient: (id: number) => request<Patient>(`/api/patients/${id}`),
  createPatient: (body: NewPatientInput) =>
    request<Patient>("/api/patients", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  wearables: (id: number) => request<{ series: SeriesPoint[] }>(`/api/patients/${id}/wearables`),
  summary: (id: number) => request<Trend[]>(`/api/patients/${id}/wearables/summary`),
  latest: (id: number) => request<Risk[]>(`/api/patients/${id}/risk/latest`),
  calculate: (id: number) =>
    request<Risk[]>(`/api/patients/${id}/risk/calculate`, { method: "POST" }),
  whatIf: (id: number, body: { fasting_glucose?: number; steps?: number; sleep_hours?: number }) =>
    request<Risk[]>(`/api/patients/${id}/risk/what-if`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
  methodology: () => request<Record<string, unknown>>("/api/methodology"),
};

export function bandClass(band: string): string {
  if (band === "High") return "text-[#ef4444]";
  if (band === "Moderate") return "text-[#f59e0b]";
  return "text-[#10b981]";
}

export function bandHex(band: string): string {
  if (band === "High") return "#ef4444";
  if (band === "Moderate") return "#f59e0b";
  return "#10b981";
}
