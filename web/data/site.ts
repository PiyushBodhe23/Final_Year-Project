export const site = {
  name: "PreventVital",
  url: "https://preventvital.in",
  tagline: "Continuous wearable intelligence. Explainable clinical risk screening. AI health assistant.",
  description:
    "PreventVital is an AI-powered preventive healthcare platform for India. It turns continuous wearable telemetry and clinical baseline markers into explainable diabetes and cardiovascular risk ranges, with an evidence-grounded AI assistant.",
  email: "hello@preventvital.in",
  disclaimer:
    "PreventVital is an academic risk-screening prototype. It offers educational health insights and prevention support. It does not diagnose, treat, or replace care from a qualified clinician. If you feel unwell, contact a doctor or emergency services.",
} as const;

export const navLinks = [
  { href: "#platform", label: "Platform" },
  { href: "#how", label: "How It Works" },
  { href: "#comparison", label: "Comparison" },
  { href: "#assess", label: "Risk Calculator" },
  { href: "#corporates", label: "Corporates" },
  { href: "/dashboard/chat", label: "AI Assistant" },
] as const;

export const footerColumns = [
  {
    title: "Platform",
    links: [
      { href: "/dashboard", label: "Patient Dashboard" },
      { href: "/dashboard/wearables", label: "Wearable Telemetry" },
      { href: "/dashboard/clinical", label: "Clinical Baseline" },
      { href: "/dashboard/chat", label: "AI Virtual Assistant" },
    ],
  },
  {
    title: "Solutions",
    links: [
      { href: "#programs", label: "Diabetes Risk Screening" },
      { href: "#programs", label: "Cardiovascular Awareness" },
      { href: "#everyday", label: "Family & Caregiver Triage" },
      { href: "#corporates", label: "Workplace Wellness" },
    ],
  },
  {
    title: "Scientific Foundation",
    links: [
      { href: "#platform", label: "Indian Diabetes Risk Score (IDRS)" },
      { href: "#platform", label: "Framingham 10-Yr CVD Model" },
      { href: "#resources", label: "ICMR & ADA Clinical Guidelines" },
      { href: "#faq", label: "Frequently Asked Questions" },
    ],
  },
] as const;

export const legalLinks = [
  { href: "#security", label: "Data Privacy & Consent" },
  { href: "#faq", label: "Academic Research Prototype" },
  { href: "#faq", label: "Non-Diagnostic Disclaimer" },
] as const;
