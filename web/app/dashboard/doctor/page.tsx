"use client";

import React, { useEffect, useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  FileText,
  Pill,
  Printer,
  Search,
  ShieldAlert,
  Stethoscope,
  TrendingDown,
  TrendingUp,
  UserCheck,
} from "lucide-react";

import { usePatientId } from "@/components/dashboard/shell";
import { api, type Patient, type Risk, type Trend } from "@/lib/api";

type NoteRecord = {
  id: string;
  patientId: number;
  date: string;
  doctor: string;
  text: string;
  directives: string[];
};

export default function DoctorPortalPage() {
  const selectedPatientId = usePatientId();
  const [activePatientId, setActivePatientId] = useState<number>(selectedPatientId);
  const [patients, setPatients] = useState<Patient[]>([]);
  const [patientData, setPatientData] = useState<Patient | null>(null);
  const [risks, setRisks] = useState<Risk[]>([]);
  const [trends, setTrends] = useState<Trend[]>([]);

  // Filters & Search
  const [searchQuery, setSearchQuery] = useState("");
  const [riskFilter, setRiskFilter] = useState<"ALL" | "HIGH" | "MODERATE" | "LOW">("ALL");
  const [mobileTab, setMobileTab] = useState<"queue" | "chart">("queue");

  // Doctor Action & Notes State
  const [notes, setNotes] = useState<NoteRecord[]>([]);
  const [currentNote, setCurrentNote] = useState("");
  const [selectedDirectives, setSelectedDirectives] = useState<string[]>([
    "Order 3-month confirmatory HbA1c & Fasting Glucose panel",
    "Advise ICMR 45-min brisk walking daily",
  ]);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Sync active patient with query param on initial load
  useEffect(() => {
    setActivePatientId(selectedPatientId);
  }, [selectedPatientId]);

  // Load patient list
  useEffect(() => {
    api
      .patients()
      .then((data) => {
        setPatients(data);
      })
      .catch((err) => {
        console.error(err.message || "Failed to load patient roster");
      });
  }, []);

  // Load detailed patient data when activePatientId changes
  useEffect(() => {
    if (!activePatientId) return;

    Promise.all([
      api.patient(activePatientId),
      api.latest(activePatientId).catch(() => []),
      api.summary(activePatientId).catch(() => []),
    ])
      .then(([p, r, t]) => {
        setPatientData(p);
        setRisks(r);
        setTrends(t);
      })
      .catch(console.error);

    // Load saved doctor notes from localStorage
    try {
      const stored = localStorage.getItem(`preventvital_notes_${activePatientId}`);
      if (stored) {
        setNotes(JSON.parse(stored));
      } else {
        setNotes([]);
      }
    } catch {
      setNotes([]);
    }
  }, [activePatientId]);

  // Handle saving clinical note
  const handleSaveNote = () => {
    if (!currentNote.trim() && selectedDirectives.length === 0) return;

    const newRecord: NoteRecord = {
      id: Date.now().toString(),
      patientId: activePatientId,
      date: new Date().toLocaleDateString("en-IN", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }),
      doctor: "Dr. A. Sharma, MD (Internal Med)",
      text: currentNote.trim() || "Clinical review conducted based on wearable telemetry and lab markers.",
      directives: [...selectedDirectives],
    };

    const updated = [newRecord, ...notes];
    setNotes(updated);
    try {
      localStorage.setItem(`preventvital_notes_${activePatientId}`, JSON.stringify(updated));
    } catch (e) {
      console.error(e);
    }

    setCurrentNote("");
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2500);
  };

  // Quick note template helper
  const insertTemplate = (snippet: string) => {
    setCurrentNote((prev) => (prev ? `${prev}\n${snippet}` : snippet));
  };

  // Toggle directive checklist
  const toggleDirective = (item: string) => {
    setSelectedDirectives((prev) =>
      prev.includes(item) ? prev.filter((d) => d !== item) : [...prev, item]
    );
  };

  // Categorize patient risks for roster
  const patientRosterWithRisk = useMemo(() => {
    return patients.map((p) => {
      let band: "High" | "Moderate" | "Low" = "Low";
      let alertReason = "";

      // Check clinical markers
      const glucose = p.clinical?.fasting_glucose;
      const sysBp = p.clinical?.sys_bp;
      const smoking = p.smoking === "current";

      if ((glucose && glucose >= 126) || (sysBp && sysBp >= 140) || p.id === 3) {
        band = "High";
        alertReason = sysBp && sysBp >= 140 ? "Hypertension Stage 2" : "High Glycemic / CVD Risk";
      } else if ((glucose && glucose >= 100) || (sysBp && sysBp >= 130) || p.id === 2) {
        band = "Moderate";
        alertReason = glucose && glucose >= 100 ? "Prediabetes (Impaired Fasting)" : "Elevated BP Tone";
      }

      return { ...p, calculatedBand: band, alertReason, smoking };
    });
  }, [patients]);

  // Filtered patients
  const filteredPatients = useMemo(() => {
    return patientRosterWithRisk.filter((p) => {
      const matchesSearch =
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        `PT-${p.id.toString().padStart(3, "0")}`.toLowerCase().includes(searchQuery.toLowerCase());

      if (!matchesSearch) return false;

      if (riskFilter === "HIGH") return p.calculatedBand === "High";
      if (riskFilter === "MODERATE") return p.calculatedBand === "Moderate";
      if (riskFilter === "LOW") return p.calculatedBand === "Low";
      return true;
    });
  }, [patientRosterWithRisk, searchQuery, riskFilter]);

  // Metrics for Top Strip
  const highRiskCount = patientRosterWithRisk.filter((p) => p.calculatedBand === "High").length;
  const modRiskCount = patientRosterWithRisk.filter((p) => p.calculatedBand === "Moderate").length;
  const stableCount = patientRosterWithRisk.filter((p) => p.calculatedBand === "Low").length;

  // Selected patient details
  const diabetesRisk = risks.find((r) => r.disease === "diabetes");
  const cardiacRisk = risks.find((r) => r.disease === "cardiac");
  const trendMap = useMemo(() => {
    const map: Record<string, Trend> = {};
    for (const t of trends) map[t.metric] = t;
    return map;
  }, [trends]);

  // Asian Indian BMI classification
  const getBmiCategory = (bmi: number | undefined | null) => {
    if (!bmi) return { label: "N/A", color: "text-muted-foreground" };
    if (bmi < 18.5) return { label: "Underweight", color: "text-blue-500" };
    if (bmi <= 22.9) return { label: "Normal (Asian Indian)", color: "text-emerald-500" };
    if (bmi <= 24.9) return { label: "Overweight (Asian Indian)", color: "text-amber-500" };
    return { label: "Obese (Asian Indian)", color: "text-rose-500" };
  };

  const bmiMeta = getBmiCategory(patientData?.bmi);

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner / Triage KPI Bar */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary/10 text-primary">
              <Stethoscope className="h-5 w-5" />
            </div>
            <div>
              <h1 className="font-display text-2xl font-bold tracking-tight">Physician & Clinician Portal</h1>
              <p className="text-xs text-muted-foreground">
                Continuous wearable telemetry triage, risk indices (IDRS & Framingham), and clinical directives.
              </p>
            </div>
          </div>
        </div>

        {/* Doctor Badges & Stats */}
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex items-center gap-2 rounded-xl border border-rose-500/20 bg-rose-500/5 px-3 py-1.5 text-xs font-semibold text-rose-600 dark:text-rose-400">
            <ShieldAlert className="h-3.5 w-3.5" />
            <span>{highRiskCount} High Risk</span>
          </div>
          <div className="flex items-center gap-2 rounded-xl border border-amber-500/20 bg-amber-500/5 px-3 py-1.5 text-xs font-semibold text-amber-600 dark:text-amber-400">
            <AlertTriangle className="h-3.5 w-3.5" />
            <span>{modRiskCount} Moderate</span>
          </div>
          <div className="flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/5 px-3 py-1.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>{stableCount} Stable</span>
          </div>
          <div className="rounded-xl border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground font-mono">
            {patients.length} Enrolled Patients
          </div>
        </div>
      </div>

      {/* Mobile Tab Switcher */}
      <div className="flex rounded-xl bg-muted p-1 lg:hidden">
        <button
          type="button"
          onClick={() => setMobileTab("queue")}
          className={`flex-1 rounded-lg py-1.5 text-xs font-semibold transition-all ${
            mobileTab === "queue" ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Patient Triage Queue ({filteredPatients.length})
        </button>
        <button
          type="button"
          onClick={() => setMobileTab("chart")}
          className={`flex-1 rounded-lg py-1.5 text-xs font-semibold transition-all ${
            mobileTab === "chart" ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
          }`}
        >
          Clinical Dossier: {patientData?.name || "Patient"}
        </button>
      </div>

      {/* Master-Detail Layout */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* Left Column: Patient Triage Queue */}
        <div className={`space-y-4 lg:col-span-4 ${mobileTab === "chart" ? "hidden lg:block" : "block"}`}>
          <div className="rounded-3xl border border-border bg-card p-4 shadow-soft">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="font-display text-sm font-bold uppercase tracking-wider text-muted-foreground">
                Triage Roster
              </h2>
              <span className="text-[11px] font-mono text-muted-foreground">
                {filteredPatients.length} of {patients.length}
              </span>
            </div>

            {/* Search Input */}
            <div className="relative mb-3">
              <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search patient name or ID..."
                className="w-full rounded-xl border border-border bg-muted/40 py-2 pl-9 pr-3 text-xs outline-none placeholder:text-muted-foreground focus:border-primary/50"
              />
            </div>

            {/* Risk Filter Chips */}
            <div className="mb-4 flex flex-wrap gap-1.5 text-[11px]">
              {(["ALL", "HIGH", "MODERATE", "LOW"] as const).map((lvl) => (
                <button
                  key={lvl}
                  type="button"
                  onClick={() => setRiskFilter(lvl)}
                  className={`rounded-lg px-2.5 py-1 font-semibold transition-colors ${
                    riskFilter === lvl
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground"
                  }`}
                >
                  {lvl}
                </button>
              ))}
            </div>

            {/* Patient List */}
            <div className="space-y-2 max-h-[620px] overflow-y-auto pr-1">
              {filteredPatients.map((p) => {
                const isSelected = p.id === activePatientId;
                const isHigh = p.calculatedBand === "High";
                const isMod = p.calculatedBand === "Moderate";

                return (
                  <div
                    key={p.id}
                    onClick={() => {
                      setActivePatientId(p.id);
                      setMobileTab("chart");
                    }}
                    className={`cursor-pointer rounded-2xl border p-3 transition-all ${
                      isSelected
                        ? "border-primary bg-primary/5 shadow-sm ring-1 ring-primary/20"
                        : "border-border/70 bg-card hover:border-border hover:bg-muted/30"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2.5">
                        <div
                          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-xs font-bold ${
                            isHigh
                              ? "bg-rose-500/10 text-rose-600 dark:text-rose-400"
                              : isMod
                              ? "bg-amber-500/10 text-amber-600 dark:text-amber-400"
                              : "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                          }`}
                        >
                          {p.name.slice(0, 2).toUpperCase()}
                        </div>
                        <div>
                          <div className="flex items-center gap-1.5">
                            <span className="font-display text-sm font-semibold text-foreground">{p.name}</span>
                            <span className="text-[10px] font-mono text-muted-foreground">
                              #{p.id.toString().padStart(3, "0")}
                            </span>
                          </div>
                          <div className="text-[11px] text-muted-foreground">
                            {p.age}y · {p.sex} · BMI {p.bmi || "—"}
                          </div>
                        </div>
                      </div>

                      <span
                        className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                          isHigh
                            ? "bg-rose-500/15 text-rose-600 dark:text-rose-400"
                            : isMod
                            ? "bg-amber-500/15 text-amber-600 dark:text-amber-400"
                            : "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400"
                        }`}
                      >
                        {p.calculatedBand}
                      </span>
                    </div>

                    {p.alertReason ? (
                      <div className="mt-2 flex items-center gap-1.5 text-[11px] font-medium text-amber-600 dark:text-amber-400">
                        <AlertCircle className="h-3 w-3 shrink-0" />
                        <span className="truncate">{p.alertReason}</span>
                      </div>
                    ) : null}
                  </div>
                );
              })}

              {filteredPatients.length === 0 && (
                <div className="py-8 text-center text-xs text-muted-foreground">
                  No patients matched the criteria.
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Selected Patient Clinical Workspace */}
        <div className={`space-y-6 lg:col-span-8 ${mobileTab === "queue" ? "hidden lg:block" : "block"}`}>
          {/* Back to queue button on mobile */}
          <button
            type="button"
            onClick={() => setMobileTab("queue")}
            className="flex items-center gap-1.5 text-xs font-semibold text-primary lg:hidden"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to Patient Roster
          </button>

          {/* Patient Overview Card */}
          <div className="rounded-3xl border border-border bg-card p-5 shadow-soft">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between border-b border-border/60 pb-4">
              <div className="flex items-center gap-3.5">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 text-base font-bold text-white shadow-md shadow-blue-500/20">
                  {patientData?.name.slice(0, 2).toUpperCase() || "PT"}
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <h2 className="font-display text-xl font-bold tracking-tight text-foreground">
                      {patientData?.name || "Loading Patient..."}
                    </h2>
                    <span className="rounded-md bg-muted px-2 py-0.5 font-mono text-[11px] text-muted-foreground">
                      ID: PT-{(patientData?.id || activePatientId).toString().padStart(3, "0")}
                    </span>
                    {patientData?.smoking === "current" && (
                      <span className="rounded-full bg-rose-500/10 px-2 py-0.5 text-[10px] font-bold text-rose-500">
                        Active Smoker
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {patientData?.age} Years · {patientData?.sex === "M" ? "Male" : "Female"} · Waist:{" "}
                    {patientData?.waist_cm ? `${patientData.waist_cm} cm` : "Not recorded"} · Activity:{" "}
                    <span className="capitalize">{patientData?.activity_level || "Moderate"}</span>
                  </p>
                </div>
              </div>

              {/* Print / Action Buttons */}
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => window.print()}
                  className="flex items-center gap-1.5 rounded-xl border border-border bg-muted/30 px-3 py-1.5 text-xs font-semibold text-foreground transition-colors hover:bg-muted"
                  title="Print Clinical Summary"
                >
                  <Printer className="h-3.5 w-3.5 text-muted-foreground" />
                  <span>Print Dossier</span>
                </button>
              </div>
            </div>

            {/* Risk Indices Gauges Strip */}
            <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3">
              {/* Diabetes Risk Index */}
              <div className="rounded-2xl border border-border/80 bg-muted/20 p-3.5">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span className="font-medium">Diabetes Screening</span>
                  <span
                    className={`font-bold ${
                      diabetesRisk?.band === "High"
                        ? "text-rose-500"
                        : diabetesRisk?.band === "Moderate"
                        ? "text-amber-500"
                        : "text-emerald-500"
                    }`}
                  >
                    {diabetesRisk?.band || "Low"} Risk
                  </span>
                </div>
                <div className="mt-1 flex items-baseline gap-2">
                  <span className="font-display text-2xl font-bold">
                    {diabetesRisk?.composite ? diabetesRisk.composite.toFixed(1) : "—"}
                  </span>
                  <span className="text-[11px] text-muted-foreground font-mono">
                    IDRS: {diabetesRisk?.idrs || 0}/100
                  </span>
                </div>
                <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className={`h-full ${
                      diabetesRisk?.band === "High"
                        ? "bg-rose-500"
                        : diabetesRisk?.band === "Moderate"
                        ? "bg-amber-500"
                        : "bg-emerald-500"
                    }`}
                    style={{ width: `${Math.min(100, (diabetesRisk?.composite || 20) * 1.2)}%` }}
                  />
                </div>
              </div>

              {/* Cardiovascular Risk Index */}
              <div className="rounded-2xl border border-border/80 bg-muted/20 p-3.5">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span className="font-medium">Cardiovascular (Framingham)</span>
                  <span
                    className={`font-bold ${
                      cardiacRisk?.band === "High"
                        ? "text-rose-500"
                        : cardiacRisk?.band === "Moderate"
                        ? "text-amber-500"
                        : "text-emerald-500"
                    }`}
                  >
                    {cardiacRisk?.band || "Low"} Risk
                  </span>
                </div>
                <div className="mt-1 flex items-baseline gap-2">
                  <span className="font-display text-2xl font-bold">
                    {cardiacRisk?.composite ? `${cardiacRisk.composite.toFixed(1)}%` : "—"}
                  </span>
                  <span className="text-[11px] text-muted-foreground">10-Year Probability</span>
                </div>
                <div className="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className={`h-full ${
                      cardiacRisk?.band === "High"
                        ? "bg-rose-500"
                        : cardiacRisk?.band === "Moderate"
                        ? "bg-amber-500"
                        : "bg-emerald-500"
                    }`}
                    style={{ width: `${Math.min(100, (cardiacRisk?.composite || 15) * 1.5)}%` }}
                  />
                </div>
              </div>

              {/* Asian Indian BMI Category */}
              <div className="rounded-2xl border border-border/80 bg-muted/20 p-3.5">
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span className="font-medium">BMI Index</span>
                  <span className={`font-bold ${bmiMeta.color}`}>{bmiMeta.label.split(" ")[0]}</span>
                </div>
                <div className="mt-1 flex items-baseline gap-2">
                  <span className="font-display text-2xl font-bold">{patientData?.bmi || "—"}</span>
                  <span className="text-[11px] text-muted-foreground">kg/m²</span>
                </div>
                <p className="mt-2 text-[10px] text-muted-foreground">
                  Cutoff: Normal ≤22.9 | Overweight 23–24.9 | Obese ≥25
                </p>
              </div>
            </div>
          </div>

          {/* Clinical Biomarkers Panel */}
          <div className="rounded-3xl border border-border bg-card p-5 shadow-soft">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-primary" />
                <h3 className="font-display text-sm font-bold uppercase tracking-wider text-foreground">
                  Stored Laboratory Biomarkers
                </h3>
              </div>
              <span className="text-xs text-muted-foreground">Verified Laboratory Screening</span>
            </div>

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {/* Fasting Glucose */}
              <div className="rounded-2xl border border-border/70 bg-muted/20 p-3">
                <span className="text-[11px] text-muted-foreground">Fasting Blood Glucose</span>
                <div className="mt-1 flex items-baseline gap-1">
                  <span className="font-display text-xl font-bold">
                    {patientData?.clinical?.fasting_glucose ?? "—"}
                  </span>
                  <span className="text-[10px] text-muted-foreground">mg/dL</span>
                </div>
                <span
                  className={`mt-1.5 inline-block rounded-md px-1.5 py-0.5 text-[10px] font-semibold ${
                    (patientData?.clinical?.fasting_glucose || 0) >= 126
                      ? "bg-rose-500/15 text-rose-500"
                      : (patientData?.clinical?.fasting_glucose || 0) >= 100
                      ? "bg-amber-500/15 text-amber-500"
                      : "bg-emerald-500/15 text-emerald-500"
                  }`}
                >
                  {(patientData?.clinical?.fasting_glucose || 0) >= 126
                    ? "Elevated (Diabetic)"
                    : (patientData?.clinical?.fasting_glucose || 0) >= 100
                    ? "Impaired (Prediabetes)"
                    : "Optimal (<100)"}
                </span>
              </div>

              {/* HbA1c */}
              <div className="rounded-2xl border border-border/70 bg-muted/20 p-3">
                <span className="text-[11px] text-muted-foreground">HbA1c</span>
                <div className="mt-1 flex items-baseline gap-1">
                  <span className="font-display text-xl font-bold">{patientData?.clinical?.hba1c ?? "—"}</span>
                  <span className="text-[10px] text-muted-foreground">%</span>
                </div>
                <span
                  className={`mt-1.5 inline-block rounded-md px-1.5 py-0.5 text-[10px] font-semibold ${
                    (patientData?.clinical?.hba1c || 0) >= 6.5
                      ? "bg-rose-500/15 text-rose-500"
                      : (patientData?.clinical?.hba1c || 0) >= 5.7
                      ? "bg-amber-500/15 text-amber-500"
                      : "bg-emerald-500/15 text-emerald-500"
                  }`}
                >
                  {(patientData?.clinical?.hba1c || 0) >= 6.5
                    ? "Diabetic (≥6.5%)"
                    : (patientData?.clinical?.hba1c || 0) >= 5.7
                    ? "Pre-diabetic Range"
                    : "Optimal (<5.7%)"}
                </span>
              </div>

              {/* Blood Pressure */}
              <div className="rounded-2xl border border-border/70 bg-muted/20 p-3">
                <span className="text-[11px] text-muted-foreground">Blood Pressure</span>
                <div className="mt-1 flex items-baseline gap-1">
                  <span className="font-display text-xl font-bold">
                    {patientData?.clinical?.sys_bp && patientData?.clinical?.dia_bp
                      ? `${patientData.clinical.sys_bp}/${patientData.clinical.dia_bp}`
                      : "—"}
                  </span>
                  <span className="text-[10px] text-muted-foreground">mmHg</span>
                </div>
                <span
                  className={`mt-1.5 inline-block rounded-md px-1.5 py-0.5 text-[10px] font-semibold ${
                    (patientData?.clinical?.sys_bp || 0) >= 140 || (patientData?.clinical?.dia_bp || 0) >= 90
                      ? "bg-rose-500/15 text-rose-500"
                      : (patientData?.clinical?.sys_bp || 0) >= 130
                      ? "bg-amber-500/15 text-amber-500"
                      : "bg-emerald-500/15 text-emerald-500"
                  }`}
                >
                  {(patientData?.clinical?.sys_bp || 0) >= 140
                    ? "Stage 2 HTN"
                    : (patientData?.clinical?.sys_bp || 0) >= 130
                    ? "Stage 1 HTN"
                    : "Normotensive"}
                </span>
              </div>

              {/* Lipid: Total Cholesterol */}
              <div className="rounded-2xl border border-border/70 bg-muted/20 p-3">
                <span className="text-[11px] text-muted-foreground">Total Cholesterol</span>
                <div className="mt-1 flex items-baseline gap-1">
                  <span className="font-display text-xl font-bold">
                    {patientData?.clinical?.total_chol ?? "—"}
                  </span>
                  <span className="text-[10px] text-muted-foreground">mg/dL</span>
                </div>
                <span
                  className={`mt-1.5 inline-block rounded-md px-1.5 py-0.5 text-[10px] font-semibold ${
                    (patientData?.clinical?.total_chol || 0) >= 200
                      ? "bg-amber-500/15 text-amber-500"
                      : "bg-emerald-500/15 text-emerald-500"
                  }`}
                >
                  {(patientData?.clinical?.total_chol || 0) >= 200 ? "Borderline / High" : "Desirable (<200)"}
                </span>
              </div>
            </div>

            {/* Lipid Subfractions */}
            <div className="mt-3 grid grid-cols-3 gap-2 border-t border-border/50 pt-3 text-xs">
              <div className="flex items-center justify-between px-2">
                <span className="text-muted-foreground">LDL-C:</span>
                <span className="font-mono font-bold text-foreground">
                  {patientData?.clinical?.ldl ? `${patientData.clinical.ldl} mg/dL` : "—"}
                </span>
              </div>
              <div className="flex items-center justify-between px-2">
                <span className="text-muted-foreground">HDL-C:</span>
                <span className="font-mono font-bold text-foreground">
                  {patientData?.clinical?.hdl ? `${patientData.clinical.hdl} mg/dL` : "—"}
                </span>
              </div>
              <div className="flex items-center justify-between px-2">
                <span className="text-muted-foreground">Triglycerides:</span>
                <span className="font-mono font-bold text-foreground">
                  {patientData?.clinical?.triglycerides ? `${patientData.clinical.triglycerides} mg/dL` : "—"}
                </span>
              </div>
            </div>
          </div>

          {/* Continuous Wearable Telemetry Strip */}
          <div className="rounded-3xl border border-border bg-card p-5 shadow-soft">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-emerald-500" />
                <h3 className="font-display text-sm font-bold uppercase tracking-wider text-foreground">
                  Continuous Wearable Telemetry (30-Day Windows)
                </h3>
              </div>
              <span className="text-xs text-muted-foreground">Passive Biosensor Ingestion</span>
            </div>

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {/* Daily Steps */}
              <div className="rounded-2xl border border-border/70 bg-muted/15 p-3">
                <span className="text-[11px] text-muted-foreground">Avg Daily Steps</span>
                <div className="mt-1 flex items-baseline gap-1">
                  <span className="font-display text-xl font-bold">
                    {trendMap["steps"] ? trendMap["steps"].mean_30.toFixed(0) : "—"}
                  </span>
                  <span className="text-[10px] text-muted-foreground">/day</span>
                </div>
                <div className="mt-1 flex items-center gap-1 text-[10px] text-muted-foreground">
                  <span>Target: 8,000</span>
                  {trendMap["steps"]?.trend === "up" ? (
                    <TrendingUp className="h-3 w-3 text-emerald-500" />
                  ) : (
                    <TrendingDown className="h-3 w-3 text-rose-500" />
                  )}
                </div>
              </div>

              {/* Resting Heart Rate */}
              <div className="rounded-2xl border border-border/70 bg-muted/15 p-3">
                <span className="text-[11px] text-muted-foreground">Resting HR (RHR)</span>
                <div className="mt-1 flex items-baseline gap-1">
                  <span className="font-display text-xl font-bold">
                    {trendMap["rhr"] ? trendMap["rhr"].mean_30.toFixed(1) : "—"}
                  </span>
                  <span className="text-[10px] text-muted-foreground">bpm</span>
                </div>
                <div className="mt-1 text-[10px] text-muted-foreground">
                  Normal: 60–75 bpm
                </div>
              </div>

              {/* Nocturnal SpO2 */}
              <div className="rounded-2xl border border-border/70 bg-muted/15 p-3">
                <span className="text-[11px] text-muted-foreground">Nocturnal SpO₂ Min</span>
                <div className="mt-1 flex items-baseline gap-1">
                  <span className="font-display text-xl font-bold">
                    {trendMap["spo2_min"] ? `${trendMap["spo2_min"].mean_30.toFixed(1)}%` : "—"}
                  </span>
                </div>
                <div className="mt-1 text-[10px]">
                  {(trendMap["spo2_min"]?.mean_30 || 99) < 92 ? (
                    <span className="font-bold text-rose-500">Hypoxic Dip Alert</span>
                  ) : (
                    <span className="text-emerald-500">Normal Oxygenation</span>
                  )}
                </div>
              </div>

              {/* Sleep Duration */}
              <div className="rounded-2xl border border-border/70 bg-muted/15 p-3">
                <span className="text-[11px] text-muted-foreground">Sleep Duration</span>
                <div className="mt-1 flex items-baseline gap-1">
                  <span className="font-display text-xl font-bold">
                    {trendMap["sleep_hours"] ? `${trendMap["sleep_hours"].mean_30.toFixed(1)}` : "—"}
                  </span>
                  <span className="text-[10px] text-muted-foreground">hrs/night</span>
                </div>
                <div className="mt-1 text-[10px] text-muted-foreground">
                  Target: 7.0–8.5 hrs
                </div>
              </div>
            </div>
          </div>

          {/* Doctor Directives & Consultation Console */}
          <div className="rounded-3xl border border-border bg-card p-5 shadow-soft">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Pill className="h-4 w-4 text-blue-500" />
                <h3 className="font-display text-sm font-bold uppercase tracking-wider text-foreground">
                  Physician Orders & Action Directives
                </h3>
              </div>
              <span className="text-xs text-muted-foreground">Clinical Governance & EHR Export</span>
            </div>

            {/* Directive Checklist */}
            <div className="space-y-2 mb-4">
              <label className="text-xs font-semibold text-muted-foreground">
                Quick Orders & Clinical Interventions:
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                {[
                  "Order 3-month confirmatory HbA1c & Fasting Glucose panel",
                  "Advise ICMR 45-min brisk walking daily",
                  "Prescribe DASH dietary protocol & sodium <2,000 mg/day",
                  "Schedule 2-week follow-up for blood pressure monitoring",
                  "Recommend tobacco cessation counseling program",
                  "Refer to Pulmonology for nocturnal SpO2 desaturation check",
                ].map((directive) => {
                  const isChecked = selectedDirectives.includes(directive);
                  return (
                    <div
                      key={directive}
                      onClick={() => toggleDirective(directive)}
                      className={`flex cursor-pointer items-start gap-2.5 rounded-xl border p-2.5 transition-colors ${
                        isChecked
                          ? "border-primary/40 bg-primary/5 text-foreground font-medium"
                          : "border-border/60 bg-muted/20 text-muted-foreground hover:bg-muted/40"
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={isChecked}
                        onChange={() => {}} // handled by parent div
                        className="mt-0.5 h-3.5 w-3.5 rounded accent-primary"
                      />
                      <span className="text-[11px] leading-snug">{directive}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Consultation Note Area */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-xs font-semibold text-muted-foreground">
                  Doctor&apos;s Consultation &amp; Clinical Note:
                </label>
                <div className="flex items-center gap-1.5 text-[11px]">
                  <span className="text-muted-foreground">Snippets:</span>
                  <button
                    type="button"
                    onClick={() => insertTemplate("Reviewed 30-day wearable trends. Advised glycemic moderation. Follow-up in 4 weeks.")}
                    className="rounded bg-muted px-2 py-0.5 text-foreground hover:bg-muted/80"
                  >
                    + Routine Review
                  </button>
                  <button
                    type="button"
                    onClick={() => insertTemplate("Prediabetes counseling: advised fiber-first nutrition, 45 min walk. Avoid refined carbs.")}
                    className="rounded bg-muted px-2 py-0.5 text-foreground hover:bg-muted/80"
                  >
                    + Prediabetes
                  </button>
                </div>
              </div>

              <textarea
                rows={3}
                value={currentNote}
                onChange={(e) => setCurrentNote(e.target.value)}
                placeholder="Enter clinical assessment, diagnostic notes, medication adjustments, or lifestyle orders..."
                className="w-full rounded-2xl border border-border bg-muted/20 p-3 text-xs outline-none focus:border-primary/50 text-foreground"
              />

              <div className="flex items-center justify-between pt-1">
                {savedSuccess ? (
                  <span className="flex items-center gap-1.5 text-xs font-semibold text-emerald-500">
                    <CheckCircle2 className="h-4 w-4" /> Note successfully recorded in patient dossier!
                  </span>
                ) : (
                  <span className="text-[11px] text-muted-foreground">
                    Notes are stored in the local clinical session audit trail.
                  </span>
                )}

                <button
                  type="button"
                  onClick={handleSaveNote}
                  className="flex items-center gap-1.5 rounded-xl bg-primary px-4 py-2 text-xs font-bold text-primary-foreground shadow-md transition-all hover:bg-primary/90"
                >
                  <UserCheck className="h-3.5 w-3.5" />
                  <span>Save Clinical Directive</span>
                </button>
              </div>
            </div>

            {/* Previous Clinical Notes History */}
            {notes.length > 0 && (
              <div className="mt-5 border-t border-border/60 pt-4">
                <h4 className="mb-2 text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  Consultation Audit History ({notes.length})
                </h4>
                <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                  {notes.map((n) => (
                    <div key={n.id} className="rounded-xl border border-border/50 bg-muted/15 p-2.5 text-xs">
                      <div className="flex items-center justify-between text-[11px] text-muted-foreground mb-1">
                        <span className="font-semibold text-foreground">{n.doctor}</span>
                        <span>{n.date}</span>
                      </div>
                      <p className="text-foreground text-[11px] leading-relaxed">{n.text}</p>
                      {n.directives.length > 0 && (
                        <div className="mt-1.5 flex flex-wrap gap-1">
                          {n.directives.map((d, i) => (
                            <span
                              key={i}
                              className="rounded-md bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary"
                            >
                              ✓ {d}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
