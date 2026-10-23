"use client";

import React, { useId, useState } from "react";

export type DataPoint = {
  x: string;
  y: number;
};

type LineProps = {
  points: DataPoint[];
  color?: string;
  threshold?: number;
  thresholdLabel?: string;
  goal?: number;
  goalLabel?: string;
  anomalies?: string[];
  height?: number;
  unit?: string;
  showGradient?: boolean;
};

/** Format ISO date string into readable short date (e.g., "15 Oct") */
function formatShortDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  } catch {
    return dateStr;
  }
}

/** Format ISO date into full readable date */
function formatFullDate(dateStr: string): string {
  try {
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return dateStr;
    return d.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric", year: "numeric" });
  } catch {
    return dateStr;
  }
}

/** Compute smooth cubic bezier path for an array of points */
function getSmoothPath(coords: { cx: number; cy: number }[]): string {
  if (coords.length === 0) return "";
  if (coords.length === 1) return `M ${coords[0].cx} ${coords[0].cy}`;

  let path = `M ${coords[0].cx.toFixed(1)} ${coords[0].cy.toFixed(1)}`;
  for (let i = 0; i < coords.length - 1; i++) {
    const current = coords[i];
    const next = coords[i + 1];
    const prev = coords[i - 1] || current;
    const nextNext = coords[i + 2] || next;

    const tension = 0.25;
    const cp1x = current.cx + (next.cx - prev.cx) * tension;
    const cp1y = current.cy + (next.cy - prev.cy) * tension;
    const cp2x = next.cx - (nextNext.cx - current.cx) * tension;
    const cp2y = next.cy - (nextNext.cy - current.cy) * tension;

    path += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${next.cx.toFixed(1)} ${next.cy.toFixed(1)}`;
  }
  return path;
}

export function LineChart({
  points,
  color = "#2563eb",
  threshold,
  thresholdLabel,
  goal,
  goalLabel,
  anomalies = [],
  height = 200,
  unit = "",
  showGradient = true,
}: LineProps) {
  const gradientId = useId();
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  if (!points || points.length < 2) {
    return (
      <div className="flex h-44 w-full items-center justify-center rounded-2xl border border-dashed border-border text-sm text-muted-foreground">
        Insufficient wearable records to render trend graph.
      </div>
    );
  }

  const width = 760;
  const padLeft = 46;
  const padRight = 32;
  const padTop = 24;
  const padBottom = 34;

  const values = points.map((p) => p.y);
  const extraVals = [threshold, goal].filter((v): v is number => v !== undefined);
  const rawMin = Math.min(...values, ...extraVals);
  const rawMax = Math.max(...values, ...extraVals);

  // Buffer so lines don't clamp to chart edges
  const valMargin = (rawMax - rawMin) * 0.12 || 1;
  const min = Math.max(0, Math.floor(rawMin - valMargin));
  const max = Math.ceil(rawMax + valMargin);
  const span = max - min || 1;

  const chartW = width - padLeft - padRight;
  const chartH = height - padTop - padBottom;

  const yFor = (value: number) => padTop + chartH - ((value - min) / span) * chartH;
  const xFor = (index: number) => padLeft + (index / (points.length - 1)) * chartW;

  const coords = points.map((p, index) => ({
    ...p,
    cx: xFor(index),
    cy: yFor(p.y),
    index,
  }));

  const smoothPath = getSmoothPath(coords);
  const areaPath = `${smoothPath} L ${coords[coords.length - 1].cx.toFixed(1)} ${(padTop + chartH).toFixed(1)} L ${coords[0].cx.toFixed(1)} ${(padTop + chartH).toFixed(1)} Z`;

  const anomalySet = new Set(anomalies);

  // Compute 4 evenly spaced horizontal grid lines
  const gridTicks = [min, min + span * 0.33, min + span * 0.66, max];

  // Pick ~5 representative date ticks along x-axis
  const step = Math.max(1, Math.floor((points.length - 1) / 4));
  const xTickIndices = [0, step, step * 2, step * 3, points.length - 1].filter(
    (idx, pos, arr) => idx < points.length && arr.indexOf(idx) === pos,
  );

  const activePoint = hoverIndex !== null && hoverIndex >= 0 && hoverIndex < coords.length ? coords[hoverIndex] : null;

  const avg30 = values.reduce((a, b) => a + b, 0) / values.length;

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const clientX = e.clientX - rect.left;
    const svgX = (clientX / rect.width) * width;

    // Find nearest point
    let nearestIdx = 0;
    let minDist = Infinity;
    for (let i = 0; i < coords.length; i++) {
      const dist = Math.abs(coords[i].cx - svgX);
      if (dist < minDist) {
        minDist = dist;
        nearestIdx = i;
      }
    }
    setHoverIndex(nearestIdx);
  };

  return (
    <div className="relative w-full">
      <svg
        viewBox={`0 0 ${width} ${height}`}
        className="h-56 w-full touch-pan-x select-none overflow-visible"
        role="img"
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setHoverIndex(null)}
      >
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={color} stopOpacity="0.28" />
            <stop offset="70%" stopColor={color} stopOpacity="0.05" />
            <stop offset="100%" stopColor={color} stopOpacity="0.0" />
          </linearGradient>
          <filter id={`glow-${gradientId}`} x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="2" stdDeviation="3" floodColor={color} floodOpacity="0.3" />
          </filter>
        </defs>

        {/* Horizontal gridlines and Y-axis scale */}
        {gridTicks.map((tickVal) => {
          const yPos = yFor(tickVal);
          return (
            <g key={tickVal} className="text-muted-foreground/40">
              <line
                x1={padLeft}
                x2={width - padRight}
                y1={yPos}
                y2={yPos}
                stroke="currentColor"
                strokeWidth="1"
                strokeDasharray="3 3"
              />
              <text
                x={padLeft - 8}
                y={yPos + 4}
                textAnchor="end"
                fontSize="11"
                className="fill-muted-foreground font-mono"
              >
                {tickVal >= 100 ? tickVal.toFixed(0) : tickVal.toFixed(1)}
              </text>
            </g>
          );
        })}

        {/* X-axis date labels */}
        {xTickIndices.map((idx) => {
          const pt = coords[idx];
          return (
            <text
              key={idx}
              x={pt.cx}
              y={padTop + chartH + 18}
              textAnchor="middle"
              fontSize="11"
              className="fill-muted-foreground font-medium"
            >
              {formatShortDate(pt.x)}
            </text>
          );
        })}

        {/* Threshold line */}
        {threshold !== undefined ? (
          <g>
            <line
              x1={padLeft}
              x2={width - padRight}
              y1={yFor(threshold)}
              y2={yFor(threshold)}
              stroke="#ef4444"
              strokeWidth="1.5"
              strokeDasharray="5 4"
            />
            <rect
              x={width - padRight - 94}
              y={yFor(threshold) - 10}
              width="90"
              height="16"
              rx="4"
              fill="#ef4444"
              className="opacity-90"
            />
            <text
              x={width - padRight - 49}
              y={yFor(threshold) + 2}
              textAnchor="middle"
              fontSize="9.5"
              fill="#ffffff"
              fontWeight="600"
            >
              {thresholdLabel || `Alert: ${threshold}${unit}`}
            </text>
          </g>
        ) : null}

        {/* Target goal line */}
        {goal !== undefined ? (
          <g>
            <line
              x1={padLeft}
              x2={width - padRight}
              y1={yFor(goal)}
              y2={yFor(goal)}
              stroke="#10b981"
              strokeWidth="1.5"
              strokeDasharray="5 4"
            />
            <rect
              x={width - padRight - 94}
              y={yFor(goal) - 10}
              width="90"
              height="16"
              rx="4"
              fill="#10b981"
              className="opacity-90"
            />
            <text
              x={width - padRight - 49}
              y={yFor(goal) + 2}
              textAnchor="middle"
              fontSize="9.5"
              fill="#ffffff"
              fontWeight="600"
            >
              {goalLabel || `Goal: ${goal}${unit}`}
            </text>
          </g>
        ) : null}

        {/* Gradient fill */}
        {showGradient ? <path d={areaPath} fill={`url(#${gradientId})`} /> : null}

        {/* Smooth trend curve */}
        <path
          d={smoothPath}
          fill="none"
          stroke={color}
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          filter={`url(#glow-${gradientId})`}
        />

        {/* Anomaly markers */}
        {coords
          .filter((pt) => anomalySet.has(pt.x))
          .map((pt) => (
            <g key={`anomaly-${pt.x}`}>
              <circle cx={pt.cx} cy={pt.cy} r="8" fill="#ef4444" opacity="0.25" className="animate-ping" />
              <circle cx={pt.cx} cy={pt.cy} r="4.5" fill="#ef4444" stroke="#ffffff" strokeWidth="1.5" />
            </g>
          ))}

        {/* Interactive Hover crosshair and indicator */}
        {activePoint ? (
          <g>
            <line
              x1={activePoint.cx}
              x2={activePoint.cx}
              y1={padTop}
              y2={padTop + chartH}
              stroke="currentColor"
              strokeWidth="1.5"
              strokeDasharray="3 3"
              className="text-foreground/60"
            />
            <circle
              cx={activePoint.cx}
              cy={activePoint.cy}
              r="6.5"
              fill={color}
              stroke="#ffffff"
              strokeWidth="2.5"
              filter="drop-shadow(0 2px 4px rgba(0,0,0,0.2))"
            />
          </g>
        ) : null}
      </svg>

      {/* Floating Hover Tooltip */}
      {activePoint ? (
        <div
          className="pointer-events-none absolute z-20 -translate-x-1/2 -translate-y-full rounded-xl border border-border bg-card/95 px-3 py-2 text-xs shadow-xl backdrop-blur-md transition-all duration-75"
          style={{
            left: `${(activePoint.cx / width) * 100}%`,
            top: `${Math.max(10, (activePoint.cy / height) * 100 - 6)}%`,
          }}
        >
          <div className="font-semibold text-foreground">{formatFullDate(activePoint.x)}</div>
          <div className="mt-1 flex items-baseline gap-1.5">
            <span className="text-base font-bold" style={{ color }}>
              {activePoint.y.toFixed(activePoint.y >= 100 ? 0 : 1)}
            </span>
            <span className="text-muted-foreground">{unit}</span>
            <span className="text-[10px] text-muted-foreground">
              ({activePoint.y - avg30 >= 0 ? "+" : ""}
              {(activePoint.y - avg30).toFixed(1)} vs mean)
            </span>
          </div>
          {anomalySet.has(activePoint.x) ? (
            <div className="mt-1 flex items-center gap-1 rounded bg-rose-500/10 px-1.5 py-0.5 text-[10px] font-medium text-rose-500">
              <span>⚠️</span>
              <span>Statistical Anomaly Flagged</span>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

/** Risk Composite Gauge with Uncertainty Interval (10th-90th percentile) and 3 Risk Bands */
export function Gauge({
  score,
  low,
  high,
  band,
}: {
  score: number;
  low: number;
  high: number;
  band: string;
}) {
  const color = band === "High" ? "#ef4444" : band === "Moderate" ? "#f59e0b" : "#10b981";
  const clampedScore = Math.max(0, Math.min(100, score));

  // Angles in radians for semicircle: Math.PI (180deg, left) to 2 * Math.PI (360deg, right)
  const angleFor = (val: number) => Math.PI + (Math.max(0, Math.min(100, val)) / 100) * Math.PI;

  const scoreAngle = angleFor(clampedScore);
  const lowAngle = angleFor(low);
  const highAngle = angleFor(high);

  const radius = 68;
  const cx = 100;
  const cy = 92;

  const arcPt = (ang: number, r: number) => ({
    x: cx + Math.cos(ang) * r,
    y: cy + Math.sin(ang) * r,
  });

  const makeArc = (startAng: number, endAng: number, r: number) => {
    const p1 = arcPt(startAng, r);
    const p2 = arcPt(endAng, r);
    const largeArc = endAng - startAng > Math.PI ? 1 : 0;
    return `M ${p1.x.toFixed(1)} ${p1.y.toFixed(1)} A ${r} ${r} 0 ${largeArc} 1 ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
  };

  return (
    <div className="relative mx-auto flex flex-col items-center">
      <svg viewBox="0 0 200 125" className="h-36 w-full max-w-[240px]" role="img" aria-label={`${band} Risk: ${score}`}>
        {/* Background Track with 3 colored zones */}
        {/* Low Zone: 0-29 (Green) */}
        <path
          d={makeArc(Math.PI, angleFor(29), radius)}
          fill="none"
          stroke="#10b981"
          strokeWidth="11"
          strokeLinecap="round"
          className="opacity-25"
        />
        {/* Moderate Zone: 29-59 (Amber) */}
        <path
          d={makeArc(angleFor(30), angleFor(59), radius)}
          fill="none"
          stroke="#f59e0b"
          strokeWidth="11"
          className="opacity-25"
        />
        {/* High Zone: 60-100 (Red) */}
        <path
          d={makeArc(angleFor(60), 2 * Math.PI, radius)}
          fill="none"
          stroke="#ef4444"
          strokeWidth="11"
          strokeLinecap="round"
          className="opacity-25"
        />

        {/* Shaded Confidence Interval Band [ci_low, ci_high] */}
        <path
          d={makeArc(lowAngle, highAngle, radius)}
          fill="none"
          stroke={color}
          strokeWidth="15"
          className="opacity-35"
        />

        {/* Active Progress Sweep Arc */}
        <path
          d={makeArc(Math.PI, scoreAngle, radius)}
          fill="none"
          stroke={color}
          strokeWidth="11"
          strokeLinecap="round"
          filter="drop-shadow(0 2px 5px rgba(0,0,0,0.25))"
        />

        {/* Current Score Dial Needle Marker */}
        {(() => {
          const needlePt = arcPt(scoreAngle, radius);
          return (
            <circle
              cx={needlePt.x}
              cy={needlePt.y}
              r="6.5"
              fill="#ffffff"
              stroke={color}
              strokeWidth="3.5"
              filter="drop-shadow(0 1px 3px rgba(0,0,0,0.3))"
            />
          );
        })()}

        {/* Score Readout */}
        <text x="100" y="78" textAnchor="middle" className="fill-foreground font-display font-extrabold" fontSize="30">
          {score.toFixed(0)}
        </text>
        <text x="100" y="93" textAnchor="middle" fill={color} fontSize="11" fontWeight="700" letterSpacing="0.05em">
          {band.toUpperCase()} RISK
        </text>
        <text x="100" y="112" textAnchor="middle" className="fill-muted-foreground font-mono" fontSize="10">
          90% CI: {low.toFixed(0)}–{high.toFixed(0)} pts
        </text>
      </svg>
    </div>
  );
}

/** Circular Vital Gauge for live wearable telemetry */
export function VitalGauge({
  title,
  value,
  min,
  max,
  suffix = "",
  color = "#2563eb",
  status,
}: {
  title: string;
  value: number;
  min: number;
  max: number;
  suffix?: string;
  color?: string;
  status?: string;
}) {
  const span = max - min || 1;
  const fraction = Math.max(0, Math.min(1, (value - min) / span));

  // Semicircle arc angles
  const startAng = Math.PI * 0.8;
  const totalSweep = Math.PI * 1.4;
  const endAng = startAng + totalSweep * fraction;

  const r = 58;
  const cx = 90;
  const cy = 78;

  const pt = (ang: number) => ({
    x: cx + Math.cos(ang) * r,
    y: cy + Math.sin(ang) * r,
  });

  const makeArc = (a1: number, a2: number) => {
    const p1 = pt(a1);
    const p2 = pt(a2);
    const large = a2 - a1 > Math.PI ? 1 : 0;
    return `M ${p1.x.toFixed(1)} ${p1.y.toFixed(1)} A ${r} ${r} 0 ${large} 1 ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
  };

  return (
    <div className="flex flex-col items-center">
      <svg viewBox="0 0 180 120" className="h-32 w-full max-w-[200px]" role="img" aria-label={`${title} ${value}${suffix}`}>
        {/* Track */}
        <path
          d={makeArc(startAng, startAng + totalSweep)}
          fill="none"
          stroke="currentColor"
          className="text-muted/30"
          strokeWidth="10"
          strokeLinecap="round"
        />
        {/* Active Arc */}
        {fraction > 0.01 ? (
          <path
            d={makeArc(startAng, endAng)}
            fill="none"
            stroke={color}
            strokeWidth="10"
            strokeLinecap="round"
          />
        ) : null}

        {/* Value text */}
        <text x={cx} y={cy - 2} textAnchor="middle" className="fill-foreground font-display font-bold" fontSize="22">
          {Number.isFinite(value) ? (value >= 100 ? value.toFixed(0) : value.toFixed(1)) : "—"}
          <tspan fontSize="11" fontWeight="500" className="fill-muted-foreground">
            {suffix}
          </tspan>
        </text>

        {/* Title */}
        <text x={cx} y={cy + 17} textAnchor="middle" className="fill-muted-foreground font-medium" fontSize="11">
          {title}
        </text>

        {/* Status Pill if provided */}
        {status ? (
          <text x={cx} y={cy + 32} textAnchor="middle" fill={color} fontSize="9.5" fontWeight="600">
            {status}
          </text>
        ) : null}
      </svg>
    </div>
  );
}

/** Risk Factor Contribution Waterfall / Bars */
export function Bars({ rows }: { rows: { label: string; value: number; max?: number }[] }) {
  if (!rows || rows.length === 0) {
    return <p className="text-xs text-muted-foreground">No specific risk factor deviations recorded.</p>;
  }

  const maxVal = Math.max(16, ...rows.map((r) => Math.abs(r.value)));

  return (
    <div className="space-y-3 pt-2">
      {rows.map((row) => {
        const widthPct = Math.min(100, (Math.abs(row.value) / maxVal) * 100);
        const isElevating = row.value >= 0;
        return (
          <div key={row.label} className="group">
            <div className="mb-1 flex items-baseline justify-between text-xs">
              <span className="font-medium text-foreground">{row.label}</span>
              <span className={`font-mono font-semibold ${isElevating ? "text-rose-500" : "text-emerald-500"}`}>
                {isElevating ? "+" : ""}
                {row.value.toFixed(1)} pts
              </span>
            </div>
            <div className="relative h-2 w-full overflow-hidden rounded-full bg-muted/50">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  isElevating ? "bg-rose-500" : "bg-emerald-500"
                }`}
                style={{ width: `${Math.max(5, widthPct)}%` }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}

/** Interactive 5-Dimensional Polar Concern Radar vs Target Benchmark */
export function Radar({ scores }: { scores: Record<string, number> }) {
  const [hoveredMetric, setHoveredMetric] = useState<string | null>(null);

  const labels = Object.keys(scores);
  if (!labels.length) return null;

  const size = 260;
  const center = size / 2;
  const radius = 94;

  const angle = (idx: number) => -Math.PI / 2 + (idx / labels.length) * Math.PI * 2;

  // Outer rim (100) = high concern. Center (0) = healthy.
  const ptFor = (idx: number, val: number) => {
    const fraction = Math.max(0, Math.min(100, val)) / 100;
    const r = radius * fraction;
    return [center + Math.cos(angle(idx)) * r, center + Math.sin(angle(idx)) * r];
  };

  // Patient polygon
  const patientPoly = labels.map((k, i) => ptFor(i, scores[k]).join(",")).join(" ");

  // Target healthy benchmark boundary (fixed reference at 25 concern score)
  const targetPoly = labels.map((_, i) => ptFor(i, 25).join(",")).join(" ");

  return (
    <div className="relative flex flex-col items-center">
      <svg viewBox={`0 0 ${size} ${size}`} className="h-64 w-full max-w-[280px]" role="img" aria-label="Wearable Concern Radar">
        {/* Concentric Web Rings (25, 50, 75, 100) */}
        {[0.25, 0.5, 0.75, 1.0].map((ring) => (
          <polygon
            key={ring}
            fill="none"
            stroke="currentColor"
            className="text-border/60"
            strokeWidth="1"
            strokeDasharray={ring === 0.25 ? "4 3" : undefined}
            points={labels
              .map((_, i) => {
                const x = center + Math.cos(angle(i)) * radius * ring;
                const y = center + Math.sin(angle(i)) * radius * ring;
                return `${x.toFixed(1)},${y.toFixed(1)}`;
              })
              .join(" ")}
          />
        ))}

        {/* Web Axes Lines */}
        {labels.map((_, i) => {
          const x = center + Math.cos(angle(i)) * radius;
          const y = center + Math.sin(angle(i)) * radius;
          return <line key={i} x1={center} y1={center} x2={x} y2={y} stroke="currentColor" className="text-border/50" strokeWidth="1" />;
        })}

        {/* Healthy Target Zone Polygon */}
        <polygon points={targetPoly} fill="#10b981" fillOpacity="0.1" stroke="#10b981" strokeWidth="1.5" strokeDasharray="4 3" />

        {/* Patient Score Polygon */}
        <polygon
          points={patientPoly}
          fill="#2563eb"
          fillOpacity="0.25"
          stroke="#2563eb"
          strokeWidth="2.5"
          className="transition-all duration-300"
        />

        {/* Vertex Markers & Interactions */}
        {labels.map((label, i) => {
          const [px, py] = ptFor(i, scores[label]);
          const isHovered = hoveredMetric === label;
          const labelAngle = angle(i);
          const lx = center + Math.cos(labelAngle) * (radius + 20);
          const ly = center + Math.sin(labelAngle) * (radius + 18);

          return (
            <g key={label} onMouseEnter={() => setHoveredMetric(label)} onMouseLeave={() => setHoveredMetric(null)}>
              <circle
                cx={px}
                cy={py}
                r={isHovered ? "6" : "4"}
                fill="#2563eb"
                stroke="#ffffff"
                strokeWidth="2"
                className="cursor-pointer transition-transform"
              />
              <text
                x={lx}
                y={ly}
                textAnchor="middle"
                fontSize="11"
                className={`cursor-pointer font-medium transition-colors ${
                  isHovered ? "fill-primary font-bold" : "fill-foreground"
                }`}
              >
                {label} ({scores[label].toFixed(0)})
              </text>
            </g>
          );
        })}
      </svg>

      {/* Legend */}
      <div className="mt-2 flex items-center justify-center gap-4 text-xs text-muted-foreground">
        <div className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-emerald-500/80" />
          <span>Healthy Target (&lt;25)</span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="inline-block h-2.5 w-2.5 rounded-full bg-blue-600" />
          <span>Patient Score (Rim = High Concern)</span>
        </div>
      </div>
    </div>
  );
}
