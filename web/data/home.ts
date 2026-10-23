export const trustBadges = [
  "Built for India",
  "Consent before sharing",
  "Encrypted by default",
  "Insight, not a diagnosis",
] as const;

export const partners = [
  "CityCare Hospitals",
  "Nimbus Labs",
  "MetroWorks",
  "Saffron Mutual",
  "Helio Diagnostics",
  "Harbour Health",
] as const;

export const stats = [
  {
    value: 6,
    suffix: "",
    label: "signals in one view",
    detail: "Heart rate, oxygen, breathing, temperature, blood pressure, and activity.",
  },
  {
    value: 3,
    suffix: "",
    label: "people who can stay informed",
    detail: "You, a family member, and a clinician can each see a role-specific heads-up.",
  },
  {
    value: 4,
    suffix: "",
    label: "prevention paths",
    detail: "Diabetes, cardiac, lifestyle, and sleep programs you can actually follow.",
  },
] as const;

export const steps = [
  {
    title: "Connect your data",
    body: "Bring heart rate, oxygen, sleep, and activity from the watch or phone you already use. One picture, whatever the brand.",
  },
  {
    title: "AI understands your health",
    body: "We look at recent patterns, not a single reading, and explain what is steady and what is changing in plain language.",
  },
  {
    title: "Emerging risks identified",
    body: "A Health Score shows which signals raised it, using ranges that shift with age. You see the reason, not just a number.",
  },
  {
    title: "Personalized action plan",
    body: "Rest, movement, food, and when to talk to a doctor. Guidance you can act on while prevention still has room to work.",
  },
] as const;

export type FeatureIcon =
  | "spark"
  | "pulse"
  | "heart"
  | "watch"
  | "chart"
  | "users";

export const features: {
  title: string;
  body: string;
  icon: FeatureIcon;
  span: string;
  visual: "score" | "trend" | "programs" | "steps" | "bars";
}[] = [
  {
    title: "AI health assessment",
    body: "A clear Health Score with the readings that moved it. Built to explain, not to alarm.",
    icon: "spark",
    span: "md:col-span-2 md:row-span-2",
    visual: "score",
  },
  {
    title: "Continuous risk monitoring",
    body: "Trends over days, so a single busy afternoon does not look like a crisis.",
    icon: "pulse",
    span: "",
    visual: "trend",
  },
  {
    title: "Disease prevention programs",
    body: "Diabetes and cardiac paths with small weekly actions, not a lecture.",
    icon: "heart",
    span: "",
    visual: "programs",
  },
  {
    title: "Wellness tracking",
    body: "Sleep, steps, and recovery sit beside vitals so the day makes sense as a whole.",
    icon: "watch",
    span: "",
    visual: "steps",
  },
  {
    title: "Health analytics",
    body: "See what changed this month, and share a simple summary with your care circle.",
    icon: "chart",
    span: "",
    visual: "bars",
  },
];

export const programs = [
  {
    id: "diabetes",
    label: "Diabetes",
    outcome: "Earlier awareness of drifting glucose patterns",
    points: [
      "Weekly rhythm for meals, walks, and sleep",
      "Flags when trends stay off your usual range",
      "A short note you can take to your doctor",
    ],
  },
  {
    id: "cardiac",
    label: "Cardiac",
    outcome: "A calmer read on heart and blood pressure trends",
    points: [
      "Resting heart rate and pressure in one timeline",
      "Age-aware ranges so the score stays fair",
      "Family can be looped in when risk rises",
    ],
  },
  {
    id: "lifestyle",
    label: "Lifestyle",
    outcome: "Habits that fit Indian workdays and family meals",
    points: [
      "Movement goals that survive a commute",
      "Food guidance without imported diet fads",
      "Check-ins that take a minute, not an hour",
    ],
  },
  {
    id: "sleep",
    label: "Sleep and recovery",
    outcome: "Wearable sleep, finally in the same language as vitals",
    points: [
      "Sleep, oxygen, and next-day energy together",
      "Plain explanation when recovery looks thin",
      "A gentler plan after late nights or travel",
    ],
  },
] as const;

export const everyday = [
  {
    title: "A score you can see through",
    body: "Each Health Score shows which readings raised it, using ranges that shift with age.",
  },
  {
    title: "Plain recommendations",
    body: "Rest, food, and when to seek medical help, based on your signals and risk level.",
  },
  {
    title: "Family and care visibility",
    body: "Alerts can reach you, a caregiver, and a clinician together, so no one is left guessing.",
  },
  {
    title: "A guide you can ask",
    body: "An assistant explains your numbers in everyday words. Educational support, not a diagnosis.",
  },
] as const;

export const corporateMetrics = [
  { value: "1 view", label: "Workforce health, without exposing private readings" },
  { value: "Earlier", label: "Screening conversations before sick leave piles up" },
  { value: "Clear ROI", label: "Participation, check-ins, and program completion in one report" },
] as const;

export const testimonials = [
  {
    quote:
      "I stopped jumping between three apps. I can see if my father’s oxygen and sleep are drifting before the weekend visit.",
    name: "Meera Iyer",
    role: "Daughter and caregiver, Bengaluru",
  },
  {
    quote:
      "The score tells me why it moved. That is the first time a health app felt honest instead of dramatic.",
    name: "Arjun Shah",
    role: "Product lead, Pune",
  },
  {
    quote:
      "Our HR team finally has a wellness view that does not ask employees to paste medical reports into a spreadsheet.",
    name: "Neha Kapoor",
    role: "People partner, Gurugram",
  },
  {
    quote:
      "I use it as a conversation starter with my doctor, not as a verdict. The language stays calm.",
    name: "Dr. Farhan Qureshi",
    role: "Family physician, Hyderabad",
  },
] as const;

export const securityPoints = [
  {
    title: "Privacy first",
    body: "You choose what is stored and who can see a summary. Sharing is off until you say otherwise.",
  },
  {
    title: "Encryption",
    body: "Data is encrypted in transit and at rest. Access inside the product is limited to what a role needs.",
  },
  {
    title: "Consent you can change",
    body: "Connect a device, pause it, or remove a family member without writing to support.",
  },
  {
    title: "Designed for India",
    body: "We align product choices with India’s data-protection principles. This is not a government certification.",
  },
] as const;

export const resources = [
  {
    title: "What a Health Score is, and is not",
    body: "How we turn several signals into one number, and why it is a guide rather than a diagnosis.",
  },
  {
    title: "Talking to parents about wearables",
    body: "A short guide for families who want earlier conversations without daily worry.",
  },
  {
    title: "A workplace wellness brief",
    body: "What HR can see, what stays private, and how a pilot usually runs.",
  },
] as const;

export const faqs = [
  {
    q: "Is PreventVital a medical device or a diagnosis?",
    a: "No. It is a prevention and education companion. It helps you notice patterns and prepare for a conversation with a clinician. It does not diagnose disease.",
  },
  {
    q: "Which devices can I connect?",
    a: "The product is built for common watches and phones used in India. A demo can walk through Apple, Fitbit, and Garmin-style data. You can also start from a manual check-in.",
  },
  {
    q: "Who sees my health data?",
    a: "Only you, until you invite a family member or clinician. Workplace views are aggregated. Individual readings are not a company dashboard.",
  },
  {
    q: "Where is data stored?",
    a: "PreventVital is designed so personal data can stay in India. Exact hosting is confirmed in your agreement. We do not claim a certification we have not earned.",
  },
  {
    q: "Can my company see an employee’s score?",
    a: "No. Employers see participation and program trends. Personal scores stay with the employee unless that person chooses to share a summary.",
  },
  {
    q: "What happens if I feel unwell right now?",
    a: "Contact a doctor or emergency services. PreventVital is not for emergencies and will not send a real ambulance, SMS, or pager alert.",
  },
] as const;
