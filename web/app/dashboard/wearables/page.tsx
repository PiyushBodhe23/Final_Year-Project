"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Activity,
  Bell,
  CheckCircle,
  Clock,
  Heart,
  Moon,
  Wind,
  Zap,
} from "lucide-react";

import { usePatientId } from "@/components/dashboard/shell";
import { LineChart, VitalGauge } from "@/components/dashboard/viz";
import { api, bandClass, type Risk, type SeriesPoint, type Trend } from "@/lib/api";

const RANGES = [7, 30, 90, 180];

type SimulatedAlert = {
  id: string;
  channel: "Patient" | "Caregiver" | "Clinician";
  severity: "info" | "warning" | "urgent";
  title: string;
  message: string;
};

export default function WearablesPage() {
  const patientId = usePatientId();
  const [days, setDays] = useState(30);
  const [series, setSeries] = useState<SeriesPoint[]>([]);
  const [trends, setTrends] = useState<Trend[]>([]);
  const [scores, setScores] = useState<Risk[]>([]);
  const [error, setError] = useState("");
  const [channel, setChannel] = useState<"All" | SimulatedAlert["channel"]>("All");
  const [acknowledgedAlerts, setAcknowledgedAlerts] = useState<Set<string>>(new Set());

  useEffect(() => {
    let cancel = false;
    setError("");
    Promise.all([api.wearables(patientId), api.summary(patientId), api.latest(patientId)])
      .then(async ([rows, summary, latest]) => {
        const ready = latest.length ? latest : await api.calculate(patientId);
        if (cancel) return;
        setSeries(rows.series);
        setTrends(summary);
        setScores(ready);
      })
      .catch((reason: Error) => {
        if (!cancel) setError(reason.message || "API not fetched");
      });
    return () => {
      cancel = true;
    };
  }, [patientId]);

  const slice = series.slice(-days);
  const latest = series.at(-1);
  const anomalies = trends.find((trend) => trend.metric === "rhr")?.anomaly_dates ?? [];
  const diabetes = scores.find((score) => score.disease === "diabetes");
  const cardiac = scores.find((score) => score.disease === "cardiac");

  const numeric = (key: string) =>
    slice
      .filter((row) => typeof row[key] === "number")
      .map((row) => ({ x: String(row.date), y: Number(row[key]) }));

  const alerts = useMemo(
    () => buildAlerts(latest, trends, diabetes, cardiac),
    [latest, trends, diabetes, cardiac],
  );

  const shownAlerts = useMemo(() => {
    const list = channel === "All" ? alerts : alerts.filter((a) => a.channel === channel);
    return list.filter((a) => !acknowledgedAlerts.has(a.id));
  }, [alerts, channel, acknowledgedAlerts]);

  const toggleAcknowledge = (id: string) => {
    setAcknowledgedAlerts((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const getMetricSummary = (metric: string) => {
    return trends.find((t) => t.metric === metric);
  };

  return (
    <div className="space-y-6">
      {/* Page Title & Time Range Switcher */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-3xl font-extrabold tracking-tight">Wearable Telemetry & Trends</h1>
          <p className="text-sm text-muted-foreground">
            Continuous multi-sensor time-series (180 days max). Automated anomaly detection, statistical baselines, and multi-channel triage.
          </p>
        </div>
        <div className="flex items-center gap-1.5 rounded-full border border-border bg-card p-1 shadow-sm">
          {RANGES.map((range) => (
            <button
              key={range}
              type="button"
              onClick={() => setDays(range)}
              className={`rounded-full px-3.5 py-1 text-xs font-semibold transition-all ${
                days === range ? "bg-[#2563eb] text-white shadow-sm" : "text-muted-foreground hover:bg-muted"
              }`}
            >
              {range} Days
            </button>
          ))}
        </div>
      </div>

      {error ? (
        <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 p-4 text-sm text-rose-500">{error}</div>
      ) : null}

      {/* KPI Overview Grid */}
      <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Diabetes Range"
          value={diabetes ? diabetes.composite.toFixed(0) : "—"}
          badge={diabetes?.band ?? "Calculating"}
          tone={diabetes?.band}
          detail={`90% CI: ${diabetes ? `${diabetes.ci_low.toFixed(0)}–${diabetes.ci_high.toFixed(0)}` : "—"}`}
          icon={<Zap className="h-4 w-4 text-amber-500" />}
        />
        <MetricCard
          label="Cardiac Range"
          value={cardiac ? cardiac.composite.toFixed(0) : "—"}
          badge={cardiac?.band ?? "Calculating"}
          tone={cardiac?.band}
          detail={`90% CI: ${cardiac ? `${cardiac.ci_low.toFixed(0)}–${cardiac.ci_high.toFixed(0)}` : "—"}`}
          icon={<Heart className="h-4 w-4 text-rose-500" />}
        />
        <MetricCard
          label="Resting Heart Rate"
          value={fmt(latest?.rhr)}
          badge={trendBadge(getMetricSummary("rhr")?.trend)}
          detail={`30d Mean: ${getMetricSummary("rhr")?.mean_30 ?? "—"} bpm`}
          unit="bpm"
          icon={<Activity className="h-4 w-4 text-blue-500" />}
        />
        <MetricCard
          label="Overnight Min SpO₂"
          value={fmt(latest?.spo2_min)}
          badge={num(latest?.spo2_min) >= 94 ? "Normal" : "Hypoxemic Dip"}
          tone={num(latest?.spo2_min) >= 94 ? "Low" : "High"}
          detail={`30d Mean: ${getMetricSummary("spo2_min")?.mean_30 ?? "—"}%`}
          unit="%"
          icon={<Wind className="h-4 w-4 text-cyan-500" />}
        />
      </section>

      {/* Live Vitals Gauges */}
      <section className="rounded-3xl border border-border bg-card p-6 shadow-sm">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <div>
            <h2 className="font-display text-lg font-bold">Latest Wearable Day Snapshot</h2>
            <p className="text-xs text-muted-foreground">
              Most recent normalized wearable reading from synthetic continuous sensor telemetry.
            </p>
          </div>
          <span className="rounded-full bg-emerald-500/10 px-2.5 py-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
            Telemetry Synced: {latest?.date ? String(latest.date) : "Today"}
          </span>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-2xl border border-border/60 bg-muted/20 p-3">
            <VitalGauge
              title="Resting Heart Rate"
              value={num(latest?.rhr)}
              min={40}
              max={140}
              suffix=" bpm"
              color="#f59e0b"
              status={num(latest?.rhr) < 70 ? "Optimal" : num(latest?.rhr) < 90 ? "Normal" : "Elevated"}
            />
          </div>
          <div className="rounded-2xl border border-border/60 bg-muted/20 p-3">
            <VitalGauge
              title="Blood Oxygen (SpO₂)"
              value={num(latest?.spo2_avg ?? latest?.spo2_min)}
              min={85}
              max={100}
              suffix="%"
              color="#0891b2"
              status={num(latest?.spo2_min) >= 95 ? "Excellent" : num(latest?.spo2_min) >= 92 ? "Borderline" : "Low"}
            />
          </div>
          <div className="rounded-2xl border border-border/60 bg-muted/20 p-3">
            <VitalGauge
              title="Respiratory Rate"
              value={num(latest?.resp_rate)}
              min={8}
              max={30}
              suffix=" /min"
              color="#10b981"
              status={num(latest?.resp_rate) <= 18 ? "Normal Resting" : "Elevated"}
            />
          </div>
          <div className="rounded-2xl border border-border/60 bg-muted/20 p-3">
            <VitalGauge
              title="Sleep Duration"
              value={num(latest?.sleep_hours)}
              min={0}
              max={12}
              suffix=" hrs"
              color="#2563eb"
              status={num(latest?.sleep_hours) >= 7.0 ? "Target Met (7-9h)" : "Sleep Deficit"}
            />
          </div>
        </div>
      </section>

      {/* 3-Channel Simulated Alerts & 30-Day Mean Comparisons */}
      <section className="grid gap-6 lg:grid-cols-[1.3fr_1fr]">
        {/* Alert Channel Panel */}
        <article className="flex flex-col justify-between rounded-3xl border border-border bg-card p-6 shadow-sm">
          <div>
            <div className="flex flex-wrap items-center justify-between gap-3 pb-3">
              <div className="flex items-center gap-2">
                <Bell className="h-5 w-5 text-blue-500" />
                <h2 className="font-display text-lg font-bold">Simulated Alert Dispatcher</h2>
              </div>
              <div className="flex gap-1 rounded-full border border-border bg-muted/40 p-1 text-xs">
                {(["All", "Patient", "Caregiver", "Clinician"] as const).map((item) => (
                  <button
                    key={item}
                    type="button"
                    onClick={() => setChannel(item)}
                    className={`rounded-full px-2.5 py-0.5 text-xs font-medium transition-all ${
                      channel === item ? "bg-[#2563eb] text-white shadow-sm" : "text-muted-foreground hover:bg-muted"
                    }`}
                  >
                    {item}
                  </button>
                ))}
              </div>
            </div>
            <p className="mb-4 text-xs text-muted-foreground">
              Simulated notification routing for Patient, Family Caregiver, and Primary Care Clinician. (Demonstration mode — no external SMS/Push sent).
            </p>

            {shownAlerts.length ? (
              <div className="space-y-3">
                {shownAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="relative flex items-start justify-between gap-3 rounded-2xl border-l-4 bg-muted/40 p-3.5 transition-colors hover:bg-muted/60"
                    style={{ borderLeftColor: severityColor(alert.severity) }}
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 text-[11px] font-semibold">
                        <span
                          className="rounded px-1.5 py-0.5 uppercase tracking-wider"
                          style={{
                            backgroundColor: `${severityColor(alert.severity)}18`,
                            color: severityColor(alert.severity),
                          }}
                        >
                          {alert.channel} · {alert.severity}
                        </span>
                      </div>
                      <p className="font-medium text-foreground">{alert.title}</p>
                      <p className="text-xs text-muted-foreground">{alert.message}</p>
                    </div>

                    <button
                      type="button"
                      onClick={() => toggleAcknowledge(alert.id)}
                      title="Acknowledge alert"
                      className="rounded-full p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
                    >
                      <CheckCircle className="h-4 w-4" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex h-32 flex-col items-center justify-center rounded-2xl border border-dashed border-border text-center text-xs text-muted-foreground">
                <CheckCircle className="mb-1 h-6 w-6 text-emerald-500" />
                <span>No active alerts for channel &ldquo;{channel}&rdquo;. All vitals are within target ranges.</span>
              </div>
            )}
          </div>
        </article>

        {/* 30-Day Physiological Baseline Summary */}
        <article className="flex flex-col justify-between rounded-3xl border border-border bg-card p-6 shadow-sm">
          <div>
            <div className="flex items-center gap-2 pb-3">
              <Clock className="h-5 w-5 text-indigo-500" />
              <h2 className="font-display text-lg font-bold">30-Day Sensor Baselines</h2>
            </div>
            <p className="mb-4 text-xs text-muted-foreground">
              Statistical baseline mean and 7-day velocity compared against evidence-based targets.
            </p>

            <ul className="space-y-3 text-xs">
              {[
                { metric: "rhr", label: "Resting Heart Rate", unit: "bpm", target: "< 75 bpm" },
                { metric: "hrv_rmssd", label: "Heart Rate Variability (RMSSD)", unit: "ms", target: "> 40 ms" },
                { metric: "steps", label: "Daily Steps", unit: "steps", target: "> 8,000 steps" },
                { metric: "sleep_hours", label: "Sleep Duration", unit: "hrs", target: "7.0–9.0 hrs" },
                { metric: "spo2_min", label: "Minimum Nocturnal SpO₂", unit: "%", target: "≥ 94%" },
              ].map((item) => {
                const tr = getMetricSummary(item.metric);
                return (
                  <li key={item.metric} className="flex items-center justify-between rounded-2xl border border-border/50 bg-muted/20 p-2.5">
                    <div>
                      <span className="font-medium text-foreground">{item.label}</span>
                      <span className="block text-[10px] text-muted-foreground">Target: {item.target}</span>
                    </div>
                    <div className="text-right font-mono">
                      <span className="font-bold text-foreground">
                        {tr ? `${tr.mean_30} ${item.unit}` : "—"}
                      </span>
                      <span className="block text-[10px] text-muted-foreground capitalize">
                        {tr ? `7d: ${tr.mean_7} · ${tr.trend}` : ""}
                      </span>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        </article>
      </section>

      {/* Interactive Trend Line Charts */}
      <div className="space-y-6">
        {/* Resting Heart Rate */}
        <ChartCard
          title="Resting Heart Rate (RHR)"
          note={trendNote(trends, "rhr")}
          summary={getMetricSummary("rhr")}
          icon={<Heart className="h-4 w-4 text-amber-500" />}
        >
          <LineChart
            points={numeric("rhr")}
            threshold={90}
            thresholdLabel="Alert: 90 bpm"
            anomalies={anomalies}
            unit=" bpm"
            color="#f59e0b"
          />
        </ChartCard>

        {/* Heart Rate Variability (RMSSD) */}
        <ChartCard
          title="Heart Rate Variability (RMSSD Autonomic Balance)"
          note={trendNote(trends, "hrv_rmssd")}
          summary={getMetricSummary("hrv_rmssd")}
          icon={<Zap className="h-4 w-4 text-purple-500" />}
        >
          <LineChart
            points={numeric("hrv_rmssd")}
            color="#8b5cf6"
            unit=" ms"
          />
        </ChartCard>

        {/* Daily Step Count */}
        <ChartCard
          title="Daily Physical Activity (Steps)"
          note={trendNote(trends, "steps")}
          summary={getMetricSummary("steps")}
          icon={<Activity className="h-4 w-4 text-emerald-500" />}
        >
          <LineChart
            points={numeric("steps")}
            color="#10b981"
            goal={8000}
            goalLabel="Display Target: 8,000 steps"
            unit=" steps"
          />
        </ChartCard>

        {/* Nightly Sleep Duration */}
        <ChartCard
          title="Nightly Sleep Duration"
          note={trendNote(trends, "sleep_hours")}
          summary={getMetricSummary("sleep_hours")}
          icon={<Moon className="h-4 w-4 text-blue-500" />}
        >
          <LineChart
            points={numeric("sleep_hours")}
            color="#2563eb"
            goal={7.0}
            goalLabel="Goal: 7.0 h"
            unit=" hrs"
          />
        </ChartCard>

        {/* Minimum Nocturnal SpO2 */}
        <ChartCard
          title="Minimum Nocturnal Blood Oxygen (SpO₂)"
          note={trendNote(trends, "spo2_min")}
          summary={getMetricSummary("spo2_min")}
          icon={<Wind className="h-4 w-4 text-cyan-500" />}
        >
          <LineChart
            points={numeric("spo2_min")}
            color="#0891b2"
            threshold={94}
            thresholdLabel="Hypoxemia Alert: 94%"
            unit="%"
          />
        </ChartCard>
      </div>
    </div>
  );
}

function ChartCard({
  title,
  note,
  summary,
  icon,
  children,
}: {
  title: string;
  note: string;
  summary?: Trend;
  icon?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <article className="rounded-3xl border border-border bg-card p-6 shadow-sm">
      <div className="mb-4 flex flex-wrap items-baseline justify-between gap-3 border-b border-border/50 pb-3">
        <div className="flex items-center gap-2">
          {icon}
          <h2 className="font-display text-base font-bold text-foreground">{title}</h2>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
          {summary ? (
            <span className="flex items-center gap-1 font-mono">
              <span>30d Mean: {summary.mean_30}</span>
              <span className="text-border">|</span>
              <span>7d Velocity: {summary.trend}</span>
              {summary.anomaly_dates.length > 0 ? (
                <>
                  <span className="text-border">|</span>
                  <span className="text-rose-500 font-semibold">{summary.anomaly_dates.length} Anomalies</span>
                </>
              ) : null}
            </span>
          ) : (
            <span>{note}</span>
          )}
        </div>
      </div>
      {children}
    </article>
  );
}

function MetricCard({
  label,
  value,
  badge,
  detail,
  unit,
  tone,
  icon,
}: {
  label: string;
  value: string;
  badge: string;
  detail: string;
  unit?: string;
  tone?: string;
  icon?: React.ReactNode;
}) {
  return (
    <article className="flex flex-col justify-between rounded-3xl border border-border bg-card p-5 shadow-sm">
      <div className="flex items-center justify-between pb-1">
        <span className="text-xs uppercase tracking-wider text-muted-foreground">{label}</span>
        {icon}
      </div>
      <div className="my-1 flex items-baseline gap-1.5">
        <span className={`font-display text-3xl font-extrabold ${tone ? bandClass(tone) : "text-foreground"}`}>
          {value}
        </span>
        {unit ? <span className="text-xs text-muted-foreground">{unit}</span> : null}
      </div>
      <div className="flex items-center justify-between text-xs text-muted-foreground pt-1 border-t border-border/40">
        <span>{detail}</span>
        <span className={`font-semibold capitalize ${tone ? bandClass(tone) : "text-foreground"}`}>{badge}</span>
      </div>
    </article>
  );
}

function trendBadge(trend?: string): string {
  if (!trend) return "Stable";
  if (trend === "up") return "Rising";
  if (trend === "down") return "Falling";
  return "Stable";
}

function trendNote(trends: Trend[], metric: string): string {
  const trend = trends.find((item) => item.metric === metric);
  if (!trend) return "";
  return `30-day mean ${trend.mean_30} · 7-day trend ${trend.trend}`;
}

function num(value: unknown): number {
  return typeof value === "number" ? value : 0;
}

function fmt(value: unknown): string {
  return typeof value === "number" ? value.toFixed(value >= 20 ? 0 : 1) : "—";
}

function severityColor(severity: SimulatedAlert["severity"]): string {
  if (severity === "urgent") return "#ef4444";
  if (severity === "warning") return "#f59e0b";
  return "#2563eb";
}

function buildAlerts(
  latest: SeriesPoint | undefined,
  trends: Trend[],
  diabetes?: Risk,
  cardiac?: Risk,
): SimulatedAlert[] {
  const alerts: SimulatedAlert[] = [];
  const rhr = num(latest?.rhr);
  const spo2 = num(latest?.spo2_min);
  const steps = num(latest?.steps);
  const sleep = num(latest?.sleep_hours);
  const rhrAnomalies = trends.find((item) => item.metric === "rhr")?.anomaly_dates.length ?? 0;

  if (rhr >= 90) {
    alerts.push({
      id: "rhr-high",
      channel: "Patient",
      severity: "warning",
      title: "Resting Heart Rate Elevated (>90 bpm)",
      message: `Latest resting heart rate is ${rhr.toFixed(0)} bpm. Autonomic recovery deficit or physiological stress indicated.`,
    });
  }
  if (spo2 > 0 && spo2 < 94) {
    alerts.push({
      id: "spo2-low",
      channel: "Caregiver",
      severity: "urgent",
      title: "Nocturnal SpO₂ Desaturation (<94%)",
      message: `Minimum oxygen saturation fell to ${spo2.toFixed(0)}%. Check sensor strap fit; monitor for nocturnal sleep apnea symptoms.`,
    });
  }
  if (steps > 0 && steps < 3500) {
    alerts.push({
      id: "steps-low",
      channel: "Patient",
      severity: "info",
      title: "Low Physical Activity Recorded",
      message: `${steps.toFixed(0)} steps on latest day versus the 8,000-step display target. Regular daily walking stimulates glucose uptake.`,
    });
  }
  if (sleep > 0 && sleep < 5.5) {
    alerts.push({
      id: "sleep-low",
      channel: "Patient",
      severity: "warning",
      title: "Significant Sleep Debt Detected",
      message: `Only ${sleep.toFixed(1)} hours of sleep recorded. Chronic short sleep elevates sympathetic tone and worsens glycemic regulation.`,
    });
  }
  if (rhrAnomalies >= 3) {
    alerts.push({
      id: "rhr-anomalies",
      channel: "Clinician",
      severity: "info",
      title: "Persistent Resting Heart Rate Anomaly Run",
      message: `${rhrAnomalies} flagged anomalous days exceeding 2 standard deviations from patient baseline. Review for stress, infection, or medication changes.`,
    });
  }
  if (diabetes?.band === "High" || cardiac?.band === "High") {
    alerts.push({
      id: "risk-high",
      channel: "Clinician",
      severity: "urgent",
      title: "Elevated Composite Screening Range",
      message: `Composite multi-factor risk is classified as High (${diabetes?.composite.toFixed(0) || cardiac?.composite.toFixed(0)}). Follow-up clinical lab panel advised.`,
    });
  }
  if (!alerts.length) {
    alerts.push({
      id: "nominal",
      channel: "Patient",
      severity: "info",
      title: "All Telemetry Within Normal Educational Bounds",
      message: "Continuous wearable parameters are tracking within nominal healthy physiological bands.",
    });
  }
  return alerts;
}
