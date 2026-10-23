"use client";

import { useMemo, useState } from "react";
import {
  Activity,
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Heart,
  Loader2,
  Scale,
  Sparkles,
  User,
  UserPlus,
  X,
  Zap,
} from "lucide-react";

import { api, type NewPatientInput, type Patient } from "@/lib/api";

interface AddPatientDialogProps {
  open: boolean;
  onClose: () => void;
  onPatientCreated: (patient: Patient) => void;
}

export function AddPatientDialog({
  open,
  onClose,
  onPatientCreated,
}: AddPatientDialogProps) {
  // Personal Info
  const [name, setName] = useState("");
  const [age, setAge] = useState<number>(35);
  const [sex, setSex] = useState<"M" | "F" | "Other">("M");

  // Biometrics
  const [heightCm, setHeightCm] = useState<number>(170);
  const [weightKg, setWeightKg] = useState<number>(70);
  const [waistCm, setWaistCm] = useState<number>(84);

  // Lifestyle
  const [activityLevel, setActivityLevel] = useState<string>("moderate");
  const [smoking, setSmoking] = useState<string>("never");
  const [cigsPerDay, setCigsPerDay] = useState<number>(0);
  const [alcohol, setAlcohol] = useState<string>("none");
  const [dietQuality, setDietQuality] = useState<string>("average");
  const [stressLevel, setStressLevel] = useState<number>(4);

  // History & Diagnosis
  const [familyHxDiabetes, setFamilyHxDiabetes] = useState<string>("none");
  const [familyHxCvd, setFamilyHxCvd] = useState<boolean>(false);
  const [bpMeds, setBpMeds] = useState<boolean>(false);
  const [existingHypertension, setExistingHypertension] = useState<boolean>(false);
  const [existingDiabetes, setExistingDiabetes] = useState<boolean>(false);
  const [priorStroke, setPriorStroke] = useState<boolean>(false);

  // Clinical Labs (Advanced Section)
  const [showAdvancedLabs, setShowAdvancedLabs] = useState(false);
  const [sysBp, setSysBp] = useState<number>(120);
  const [diaBp, setDiaBp] = useState<number>(80);
  const [fastingGlucose, setFastingGlucose] = useState<number>(95);
  const [hba1c, setHba1c] = useState<number>(5.4);
  const [totalChol, setTotalChol] = useState<number>(190);
  const [hdl, setHdl] = useState<number>(50);
  const [ldl, setLdl] = useState<number>(115);
  const [triglycerides, setTriglycerides] = useState<number>(140);

  // State
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Live BMI calculation
  const bmi = useMemo(() => {
    if (!heightCm || !weightKg || heightCm <= 0) return 0;
    const heightM = heightCm / 100;
    return parseFloat((weightKg / (heightM * heightM)).toFixed(1));
  }, [heightCm, weightKg]);

  const bmiCategory = useMemo(() => {
    if (bmi < 18.5) return { label: "Underweight", color: "text-amber-500" };
    if (bmi < 23) return { label: "Normal (Asian Indian)", color: "text-emerald-500" };
    if (bmi < 27.5) return { label: "Overweight", color: "text-amber-500" };
    return { label: "Obese (Higher Risk)", color: "text-rose-500" };
  }, [bmi]);

  if (!open) return null;

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) {
      setError("Please enter the patient's full name.");
      return;
    }
    if (age < 18 || age > 105) {
      setError("Please enter a valid adult age between 18 and 105.");
      return;
    }

    setLoading(true);
    setError(null);

    const payload: NewPatientInput = {
      name: name.trim(),
      age: Number(age),
      sex,
      height_cm: Number(heightCm),
      weight_kg: Number(weightKg),
      waist_cm: Number(waistCm),
      smoking,
      cigs_per_day: smoking === "current" ? Number(cigsPerDay) : 0,
      alcohol,
      activity_level: activityLevel,
      diet_quality: dietQuality,
      stress_level: Number(stressLevel),
      family_hx_diabetes: familyHxDiabetes,
      family_hx_cvd: familyHxCvd,
      bp_meds: bpMeds,
      existing_hypertension: existingHypertension,
      existing_diabetes: existingDiabetes,
      prior_stroke: priorStroke,
      sys_bp: Number(sysBp),
      dia_bp: Number(diaBp),
      fasting_glucose: Number(fastingGlucose),
      hba1c: Number(hba1c),
      total_chol: Number(totalChol),
      hdl: Number(hdl),
      ldl: Number(ldl),
      triglycerides: Number(triglycerides),
    };

    try {
      const created = await api.createPatient(payload);
      setLoading(false);
      onPatientCreated(created);
      onClose();
    } catch (err: unknown) {
      setLoading(false);
      const msg = err instanceof Error ? err.message : "Failed to register patient";
      setError(msg);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/60 backdrop-blur-sm animate-in fade-in-50 duration-200"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="add-patient-title"
    >
      <div
        className="relative w-full max-w-2xl max-h-[92vh] flex flex-col rounded-3xl border border-border bg-card shadow-2xl text-foreground overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border/80 px-6 py-4 bg-muted/30">
          <div className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-2xl bg-blue-600/10 text-blue-600 dark:text-blue-400">
              <UserPlus className="h-5 w-5" />
            </span>
            <div>
              <h2 id="add-patient-title" className="text-base font-bold text-foreground">
                Register New Patient
              </h2>
              <p className="text-xs text-muted-foreground">
                Enter demographic and clinical parameters to initialize continuous risk screening
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close dialog"
            className="flex h-8 w-8 items-center justify-center rounded-full text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Scrollable Form Body */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6 space-y-6">
          {error && (
            <div className="flex items-center gap-2 rounded-xl border border-rose-500/30 bg-rose-500/10 p-3 text-xs text-rose-600 dark:text-rose-400">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* 1. Basic Demographics */}
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5 mb-3">
              <User className="h-3.5 w-3.5 text-primary" />
              <span>Personal Demographics</span>
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="sm:col-span-2">
                <label className="block text-xs font-medium text-foreground mb-1">
                  Full Name <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Ananya Sharma"
                  className="w-full rounded-xl border border-border bg-muted/40 px-3 py-2 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:border-primary/60"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-foreground mb-1">
                  Age (Years) <span className="text-rose-500">*</span>
                </label>
                <input
                  type="number"
                  min="18"
                  max="105"
                  required
                  value={age}
                  onChange={(e) => setAge(Number(e.target.value))}
                  className="w-full rounded-xl border border-border bg-muted/40 px-3 py-2 text-xs text-foreground focus:outline-none focus:border-primary/60"
                />
              </div>

              <div className="sm:col-span-3">
                <label className="block text-xs font-medium text-foreground mb-1.5">
                  Biological Sex <span className="text-rose-500">*</span>
                </label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { val: "M", label: "Male" },
                    { val: "F", label: "Female" },
                    { val: "Other", label: "Other" },
                  ].map((item) => (
                    <button
                      key={item.val}
                      type="button"
                      onClick={() => setSex(item.val as "M" | "F" | "Other")}
                      className={`rounded-xl border py-2 text-xs font-semibold transition-all ${
                        sex === item.val
                          ? "border-primary bg-primary/10 text-primary shadow-xs"
                          : "border-border bg-muted/30 text-muted-foreground hover:bg-muted"
                      }`}
                    >
                      {item.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* 2. Body Metrics & BMI */}
          <div className="border-t border-border/60 pt-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                <Scale className="h-3.5 w-3.5 text-primary" />
                <span>Body Metrics & BMI</span>
              </h3>
              <div className="inline-flex items-center gap-1.5 rounded-full border border-border bg-muted/50 px-2.5 py-0.5 text-xs">
                <span className="font-semibold">BMI: {bmi} kg/m²</span>
                <span>·</span>
                <span className={`font-bold ${bmiCategory.color}`}>{bmiCategory.label}</span>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs font-medium text-foreground mb-1">
                  Height (cm)
                </label>
                <input
                  type="number"
                  min="100"
                  max="230"
                  value={heightCm}
                  onChange={(e) => setHeightCm(Number(e.target.value))}
                  className="w-full rounded-xl border border-border bg-muted/40 px-3 py-2 text-xs text-foreground focus:outline-none focus:border-primary/60"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-foreground mb-1">
                  Weight (kg)
                </label>
                <input
                  type="number"
                  min="30"
                  max="220"
                  value={weightKg}
                  onChange={(e) => setWeightKg(Number(e.target.value))}
                  className="w-full rounded-xl border border-border bg-muted/40 px-3 py-2 text-xs text-foreground focus:outline-none focus:border-primary/60"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-foreground mb-1">
                  Waist (cm)
                </label>
                <input
                  type="number"
                  min="50"
                  max="160"
                  value={waistCm}
                  onChange={(e) => setWaistCm(Number(e.target.value))}
                  className="w-full rounded-xl border border-border bg-muted/40 px-3 py-2 text-xs text-foreground focus:outline-none focus:border-primary/60"
                />
              </div>
            </div>
          </div>

          {/* 3. Lifestyle & Habits */}
          <div className="border-t border-border/60 pt-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5 mb-3">
              <Activity className="h-3.5 w-3.5 text-primary" />
              <span>Lifestyle & Activity</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-foreground mb-1">
                  Physical Activity
                </label>
                <select
                  value={activityLevel}
                  onChange={(e) => setActivityLevel(e.target.value)}
                  className="w-full rounded-xl border border-border bg-muted/40 px-3 py-2 text-xs text-foreground focus:outline-none focus:border-primary/60"
                >
                  <option value="sedentary">Sedentary (&lt;5k steps/day)</option>
                  <option value="moderate">Moderate (5k–10k steps/day)</option>
                  <option value="regular">Regular Active (&gt;10k steps/day)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-foreground mb-1">
                  Smoking Status
                </label>
                <select
                  value={smoking}
                  onChange={(e) => setSmoking(e.target.value)}
                  className="w-full rounded-xl border border-border bg-muted/40 px-3 py-2 text-xs text-foreground focus:outline-none focus:border-primary/60"
                >
                  <option value="never">Never Smoked</option>
                  <option value="former">Former Smoker</option>
                  <option value="current">Current Smoker</option>
                </select>
              </div>

              {smoking === "current" && (
                <div>
                  <label className="block text-xs font-medium text-foreground mb-1">
                    Cigarettes / Day
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="60"
                    value={cigsPerDay}
                    onChange={(e) => setCigsPerDay(Number(e.target.value))}
                    className="w-full rounded-xl border border-border bg-muted/40 px-3 py-2 text-xs text-foreground focus:outline-none focus:border-primary/60"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-medium text-foreground mb-1">
                  Alcohol Intake
                </label>
                <select
                  value={alcohol}
                  onChange={(e) => setAlcohol(e.target.value)}
                  className="w-full rounded-xl border border-border bg-muted/40 px-3 py-2 text-xs text-foreground focus:outline-none focus:border-primary/60"
                >
                  <option value="none">None / Rare</option>
                  <option value="moderate">Moderate</option>
                  <option value="heavy">Frequent / Heavy</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-foreground mb-1">
                  Diet Quality
                </label>
                <select
                  value={dietQuality}
                  onChange={(e) => setDietQuality(e.target.value)}
                  className="w-full rounded-xl border border-border bg-muted/40 px-3 py-2 text-xs text-foreground focus:outline-none focus:border-primary/60"
                >
                  <option value="good">Balanced &amp; High Fiber</option>
                  <option value="average">Standard Average</option>
                  <option value="poor">High Sodium / Ultra-Processed</option>
                </select>
              </div>

              <div className="sm:col-span-2">
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="font-medium text-foreground">Stress Level (1-10)</span>
                  <span className="font-mono font-bold text-primary">{stressLevel} / 10</span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  value={stressLevel}
                  onChange={(e) => setStressLevel(Number(e.target.value))}
                  className="w-full accent-blue-600"
                />
              </div>
            </div>
          </div>

          {/* 4. Family & Medical History */}
          <div className="border-t border-border/60 pt-4">
            <h3 className="text-xs font-bold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5 mb-3">
              <Heart className="h-3.5 w-3.5 text-rose-500" />
              <span>Clinical &amp; Family History</span>
            </h3>

            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-foreground mb-1">
                  Family History of Diabetes (IDRS Weighted)
                </label>
                <select
                  value={familyHxDiabetes}
                  onChange={(e) => setFamilyHxDiabetes(e.target.value)}
                  className="w-full rounded-xl border border-border bg-muted/40 px-3 py-2 text-xs text-foreground focus:outline-none focus:border-primary/60"
                >
                  <option value="none">No immediate family history</option>
                  <option value="one parent">One parent diabetic (+10 IDRS)</option>
                  <option value="both parents">Both parents diabetic (+20 IDRS)</option>
                </select>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {[
                  {
                    id: "familyHxCvd",
                    label: "Family History of Heart Disease",
                    checked: familyHxCvd,
                    onChange: setFamilyHxCvd,
                  },
                  {
                    id: "existingHypertension",
                    label: "Diagnosed Hypertension",
                    checked: existingHypertension,
                    onChange: setExistingHypertension,
                  },
                  {
                    id: "bpMeds",
                    label: "Currently on BP Medication",
                    checked: bpMeds,
                    onChange: setBpMeds,
                  },
                  {
                    id: "existingDiabetes",
                    label: "Diagnosed Type 2 Diabetes",
                    checked: existingDiabetes,
                    onChange: setExistingDiabetes,
                  },
                  {
                    id: "priorStroke",
                    label: "Prior Stroke / TIA History",
                    checked: priorStroke,
                    onChange: setPriorStroke,
                  },
                ].map((item) => (
                  <label
                    key={item.id}
                    className="flex items-center gap-2.5 rounded-xl border border-border/80 bg-muted/30 p-2.5 text-xs text-foreground cursor-pointer hover:bg-muted/60 transition-colors"
                  >
                    <input
                      type="checkbox"
                      checked={item.checked}
                      onChange={(e) => item.onChange(e.target.checked)}
                      className="h-4 w-4 rounded accent-blue-600"
                    />
                    <span className="font-medium">{item.label}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* 5. Optional Lab Values & Baseline (Collapsible) */}
          <div className="border-t border-border/60 pt-4">
            <button
              type="button"
              onClick={() => setShowAdvancedLabs((prev) => !prev)}
              className="flex w-full items-center justify-between text-xs font-bold uppercase tracking-wider text-muted-foreground hover:text-foreground transition-colors"
            >
              <span className="flex items-center gap-1.5">
                <Zap className="h-3.5 w-3.5 text-amber-500" />
                <span>Initial Lab Vitals (Optional Clinical Baseline)</span>
              </span>
              {showAdvancedLabs ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
            </button>

            {showAdvancedLabs && (
              <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-3 bg-muted/20 rounded-2xl p-3 border border-border">
                <div>
                  <label className="block text-[11px] font-medium text-foreground mb-1">
                    Systolic BP (mmHg)
                  </label>
                  <input
                    type="number"
                    value={sysBp}
                    onChange={(e) => setSysBp(Number(e.target.value))}
                    className="w-full rounded-xl border border-border bg-background px-2.5 py-1.5 text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-foreground mb-1">
                    Diastolic BP (mmHg)
                  </label>
                  <input
                    type="number"
                    value={diaBp}
                    onChange={(e) => setDiaBp(Number(e.target.value))}
                    className="w-full rounded-xl border border-border bg-background px-2.5 py-1.5 text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-foreground mb-1">
                    Fasting Glucose (mg/dL)
                  </label>
                  <input
                    type="number"
                    value={fastingGlucose}
                    onChange={(e) => setFastingGlucose(Number(e.target.value))}
                    className="w-full rounded-xl border border-border bg-background px-2.5 py-1.5 text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-foreground mb-1">
                    HbA1c (%)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    value={hba1c}
                    onChange={(e) => setHba1c(Number(e.target.value))}
                    className="w-full rounded-xl border border-border bg-background px-2.5 py-1.5 text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-foreground mb-1">
                    Total Chol (mg/dL)
                  </label>
                  <input
                    type="number"
                    value={totalChol}
                    onChange={(e) => setTotalChol(Number(e.target.value))}
                    className="w-full rounded-xl border border-border bg-background px-2.5 py-1.5 text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-foreground mb-1">
                    HDL (mg/dL)
                  </label>
                  <input
                    type="number"
                    value={hdl}
                    onChange={(e) => setHdl(Number(e.target.value))}
                    className="w-full rounded-xl border border-border bg-background px-2.5 py-1.5 text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-foreground mb-1">
                    LDL (mg/dL)
                  </label>
                  <input
                    type="number"
                    value={ldl}
                    onChange={(e) => setLdl(Number(e.target.value))}
                    className="w-full rounded-xl border border-border bg-background px-2.5 py-1.5 text-xs focus:outline-none focus:border-primary"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-foreground mb-1">
                    Triglycerides (mg/dL)
                  </label>
                  <input
                    type="number"
                    value={triglycerides}
                    onChange={(e) => setTriglycerides(Number(e.target.value))}
                    className="w-full rounded-xl border border-border bg-background px-2.5 py-1.5 text-xs focus:outline-none focus:border-primary"
                  />
                </div>
              </div>
            )}
          </div>
        </form>

        {/* Footer Actions */}
        <div className="flex items-center justify-between border-t border-border/80 px-6 py-4 bg-muted/20">
          <div className="text-[11px] text-muted-foreground flex items-center gap-1.5">
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            <span>Generates 180-day baseline telemetry automatically</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              type="button"
              disabled={loading}
              onClick={onClose}
              className="rounded-xl border border-border px-4 py-2 text-xs font-semibold text-foreground hover:bg-muted transition-colors disabled:opacity-50"
            >
              Cancel
            </button>

            <button
              type="button"
              disabled={loading}
              onClick={handleSubmit}
              className="flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2 text-xs font-bold text-white shadow-sm hover:bg-blue-700 transition-all hover:scale-[1.02] disabled:opacity-50 disabled:hover:scale-100"
            >
              {loading ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>Computing Telemetry &amp; Risk...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>Save &amp; Open Dashboard</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
