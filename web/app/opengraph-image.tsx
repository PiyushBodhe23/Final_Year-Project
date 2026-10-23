import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "PreventVital — Understand your health. Catch risks early.";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          background: "#f8fafc",
          padding: "72px",
          color: "#0f172a",
        }}
      >
        <div style={{ display: "flex", fontSize: 28, fontWeight: 700, color: "#2563eb" }}>PreventVital</div>
        <div style={{ display: "flex", flexDirection: "column", gap: 16, maxWidth: 860 }}>
          <div style={{ fontSize: 64, fontWeight: 700, lineHeight: 1.05, letterSpacing: -1.5 }}>
            Catch risks before they become disease.
          </div>
          <div style={{ fontSize: 28, color: "#475569" }}>Preventive health insight for people and workplaces in India.</div>
        </div>
      </div>
    ),
    { ...size },
  );
}
