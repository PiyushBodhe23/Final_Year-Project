"""Aarya Thakare: question bank + answer bank."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ITEMS = [
    (
        "Q1",
        "What is the name of this project?",
        "An Interoperable Wearable Health Data Framework for Real-Time Predictive Health Monitoring and Early Disease Risk Detection. The live demo website is branded PulseVanguard AI.",
    ),
    (
        "Q2",
        "What problem does the paper start with?",
        "Healthcare is still mostly reactive. A patient is often assessed only after symptoms have already progressed, or only at scheduled clinic visits. That works poorly for chronic conditions such as diabetes, hypertension, and heart disease, because trouble can build quietly between visits.",
    ),
    (
        "Q3",
        "Name the three recurring technology gaps the survey isolates after reviewing twenty studies from 2016–2025.",
        "First, wearable data is fragmented across incompatible platforms. Second, there is little personalised health-baseline modelling — systems use one-size-fits-all thresholds. Third, alert systems are built for only one recipient at a time (patient or staff), not patient, caregiver, and clinician together.",
    ),
    (
        "Q4",
        "In what way do proprietary wearable ecosystems (Apple, Samsung, Fitbit) create a clinical blind spot even when the sensors themselves are accurate?",
        "The watch may measure heart rate or SpO₂ well, but each brand stores data in its own silo. The clinic never sees a single, joined timeline. Accurate sensors still fail public health if the numbers never leave the vendor app.",
    ),
    (
        "Q5",
        "What does WHO say about non-communicable diseases?",
        "WHO estimates that NCDs — cardiovascular disease, type 2 diabetes, hypertension, chronic respiratory disease, and similar conditions — account for roughly 74% of global deaths each year, and that many of those deaths are preventable with earlier detection and ongoing monitoring.",
    ),
    (
        "Q6",
        "What does WHO’s 74% figure actually refer to?",
        "It is the share of deaths worldwide that come from non-communicable diseases, not from infections. The paper uses it to argue that continuous monitoring and earlier warning could save lives, not that our demo already reduced mortality.",
    ),
    (
        "Q7",
        "Why are clinic visits not enough?",
        "A visit is a snapshot. Between appointments there is a blind spot where disease can progress unnoticed. Wearables can fill that gap with a continuous stream of vitals — if the data is actually used.",
    ),
    (
        "Q8",
        "What are the 3 technical gaps found by the research paper?",
        "The same three as the survey conclusion: fragmented wearable ecosystems, no personalised baseline / composite scoring, and single-recipient alerts. The paper treats these as architectural gaps, not just ‘we need a slightly more accurate model.’",
    ),
    (
        "Q9",
        "What is HRI, simply?",
        "Health Risk Index: one score from 0 to 100 that summarises how concerning the current vitals look. In software the bands are low (0–25), moderate (25–50), high (50–75), and critical (75–100).",
    ),
    (
        "Q11",
        "Which databases were searched?",
        "IEEE Xplore, PubMed/MEDLINE, Springer Digital Library, and MDPI Open Access Journals, plus IJARCCE, Elsevier health-informatics journals, and NEJM Catalyst.",
    ),
    (
        "Q12",
        "Why is a single abnormal vital (for example tachycardia) an insufficient basis for an early-warning claim?",
        "Heart rate rises with exercise, stress, or caffeine. Without SpO₂, blood pressure, temperature, activity, and trend, you get false alarms. The literature also shows multi-sensor fusion beats a single channel. HRI combines several vitals on purpose.",
    ),
    (
        "Q13",
        "Which five thematic areas structured the literature search, and why is that taxonomy better than grouping papers only by year?",
        "Wearable IoT monitoring, machine-learning disease-risk prediction, health-data interoperability, smart alerting, and AI virtual assistants. Themes map onto the gaps we actually try to close. Grouping only by year would mix unrelated problems and hide that no single paper combined all five.",
    ),
    (
        "Q14",
        "What’s a three-channel alert?",
        "The same risk event is explained to three roles at once: the patient, a caregiver, and a clinician — not only one of them. In the demo those messages appear together on the Alerts panel (delivery is simulated).",
    ),
    (
        "Q15",
        "Is this a medical device?",
        "No. It is an academic, educational prototype on synthetic data. It is not a registered medical device, not a diagnosis, and not a substitute for a clinician.",
    ),
    (
        "Q16",
        "Say the ethical line before you use the words ‘early disease detection.’",
        "We are not detecting disease in a real body. HRI is a simulated risk score on synthetic vitals. ‘Early detection’ in the paper title is the research ambition of the survey, not something this college demo has clinically proven.",
    ),
    (
        "Q17",
        "If they ask ‘can this replace doctors?’",
        "No. It is a teaching monitor and explainer. Clinical decisions stay with qualified professionals. The contribution is architecture — unify, score, alert, explain — not autonomous practice of medicine.",
    ),
    (
        "Q18",
        "Outline the seven-stage pipeline from wearable device to intervention.",
        "1) Wearable devices collect signals. 2) Data is pulled through health APIs / connectors. 3) Readings are normalised into one schema. 4) AI/ML scores anomalies and risk. 5) A composite HRI is computed. 6) Three-channel alerts fire. 7) Dashboard, virtual assistant, and (in the paper) lifestyle guidance support intervention. In the live build, lifestyle advice is only proposed, not a full diet engine.",
    ),
    (
        "Q19",
        "Why is Random Forest described as more robust than SVM once real-world sensor noise is present?",
        "Zhou et al. found both SVM and RF above 85% for hypertension-risk style tasks, but Random Forest held up better when realistic sensor noise was introduced. That is why we prefer a tree ensemble for noisy wearable tables, not a lab-clean SVM alone.",
    ),
    (
        "Q20",
        "Why LSTM?",
        "LSTM networks remember patterns over time. Miotto argued they fit longitudinal health records; Rigla used LSTM on glucose streams with about 30 minutes of lead time. Hourly vital history is a sequence, so LSTM complements Random Forest, which looks more at one moment’s features. In the demo LSTM is optional if TensorFlow weights are missing; RF and rules still run.",
    ),
    (
        "Q21",
        "Name one limitation of the current software.",
        "Any honest one: real Fitbit/Google/Apple OAuth is stubbed; chat can be slow on CPU; LSTM may be skipped without TensorFlow; data is synthetic; WhatsApp/email alerts are simulated on screen, not actually sent.",
    ),
    (
        "Q22",
        "How would you explain the project in 20 seconds?",
        "Watches already collect data, but it sits in silos and care is still late. We put vitals in one format, compute a Health Risk Index, warn patient, family, and clinician together, and let an assistant explain that person’s numbers. It is a demo, not a doctor.",
    ),
    (
        "Q23",
        "Name three wearables the paper talks about.",
        "Apple Watch, Samsung Galaxy Watch, and Fitbit (the demo story also mentions other fitness brands).",
    ),
    (
        "Q24",
        "Kajornkasirat got high correlation with medical sensors. Why isn’t that the same as clinical decision support?",
        "High Pearson R means their MAX30102/AHT20 readings tracked a medical-grade reference. Decision support means you change a care decision inside a workflow, with alerts and evidence. They validated sensing, not a full care pathway. We must not pretend our HRI is clinically validated either.",
    ),
    (
        "Q25",
        "Table II contrasts custom IoT hardware with consumer APIs. What deployment and cost argument follows from choosing APIs?",
        "Custom Arduino/MAX30102 kits mean you manufacture hardware for every user. Consumer APIs mean people use watches they already own, so hardware cost is near zero and scale is easier. Honesty for viva: we did not finish real vendor OAuth; we score a dataset as if that layer existed.",
    ),
    (
        "Q26",
        "Where in the pipeline would FHIR/HL7 mapping sit if this moved beyond an academic prototype?",
        "After normalisation — map our unified JSON (user, timestamp, metric, value, unit, source) into FHIR Observation (or HL7) resources so a hospital EHR could ingest them. It is a next step, not in the current repo.",
    ),
    (
        "Q27",
        "What limitation of Kajornkasirat [1] and Ekanath [2] alert designs does Gap 2 in Table III mark, and how does your demo close it on screen?",
        "Gap 2 is single-recipient alerts: Kajornkasirat notified medical staff (LINE Notify); Ekanath leaned caregivers. Neither did patient + caregiver + clinician at once. On the demo, pick a high/critical synthetic patient and the Alerts panel shows all three channels together.",
    ),
    (
        "Q28",
        "What ethical boundary must you state before using the phrase ‘early disease detection’ in a viva?",
        "Do not claim we diagnosed or detected disease in real patients. HRI is a simulated index on synthetic vitals. The phrase in the title is the goal of the research area, not a clinical result of this prototype.",
    ),
    (
        "Q30",
        "What does PulseVanguard AI actually implement today versus what Table II lists as a full lifestyle-recommendation engine?",
        "Today: unified vitals, HRI, short forecast, three-channel alert texts, dashboard, and a live-data assistant (Ollama). Table II also lists a personalised lifestyle engine. That is proposed in the paper; the live build does not run a full diet/lifestyle coach. Say: proposed in architecture, not fully implemented.",
    ),
    (
        "Q31",
        "How do you answer: ‘Can this system replace a physician?’ without undermining the contribution?",
        "No, it cannot and should not. The contribution is an academic architecture that the literature kept splitting: one score, three alerts, grounded explanation. Replacing a physician would be unsafe and is not the claim. Aids teaching and future research; does not practise medicine.",
    ),
    (
        "Q32",
        "If asked for originality, which combination of HRI + three-channel alerts + live assistant is hard to find in any single reviewed paper?",
        "Plenty of papers do IoT, or RF, or a chatbot, or hospital early warning — usually one slice. What is hard to find in one paper is consumer-style multi-source vitals, a composite HRI, simultaneous three-role alerts, and an assistant that sees live history and forecast together. That combination is our academic originality — not ‘we invented AI in healthcare.’",
    ),
]


def _font(run, name="Calibri", size=12, bold=False, italic=False, color=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color is not None:
        run.font.color.rgb = color


def _cover(doc: Document, title: str, subtitle: str) -> None:
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run(title)
    _font(r, name="Georgia", size=22, bold=True, color=RGBColor(0x1A, 0x1F, 0x4A))

    s = doc.add_paragraph()
    s.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = s.add_run(subtitle)
    _font(r, name="Georgia", size=13, italic=True, color=RGBColor(0x3D, 0x4B, 0xC8))

    m = doc.add_paragraph()
    m.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = m.add_run(
        "Aarya Thakare  ·  Final-year B.Tech (E&TC)\n"
        "JSPM’s Rajarshi Shahu College of Engineering, Pune  ·  AY 2025–26\n"
        "Guide: Dr. Nilima Mohite\n"
        "Interoperable Wearable Health Data Framework  ·  PulseVanguard AI"
    )
    _font(r, size=11, color=RGBColor(0x4A, 0x50, 0x78))


def build_questions() -> Path:
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Inches(0.9)
    sec.bottom_margin = Inches(0.9)
    sec.left_margin = Inches(1.0)
    sec.right_margin = Inches(1.0)
    _cover(doc, "Question Bank", "Viva / presentation questions (questions only)")
    n = doc.add_paragraph()
    r = n.add_run(
        "Use this sheet in the hall. Numbering matches the personal list (Q10 and Q29 are not used)."
    )
    _font(r, size=10, italic=True, color=RGBColor(0x4A, 0x50, 0x78))
    for num, q, _a in ITEMS:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(8)
        r = p.add_run(f"{num}. ")
        _font(r, size=12, bold=True, color=RGBColor(0x3D, 0x4B, 0xC8))
        r2 = p.add_run(q)
        _font(r2, size=12)
    path = Path(r"d:\Aarya_Thakare_Question_Bank.docx")
    doc.save(path)
    return path


def build_answers() -> Path:
    doc = Document()
    sec = doc.sections[0]
    sec.top_margin = Inches(0.9)
    sec.bottom_margin = Inches(0.9)
    sec.left_margin = Inches(1.0)
    sec.right_margin = Inches(1.0)
    _cover(doc, "Answer Bank", "Spoken-style answers for the Question Bank")
    n = doc.add_paragraph()
    r = n.add_run(
        "Practise out loud. Always add: educational prototype, synthetic data, not a medical device. "
        "Q3 and Q8 are the same three gaps; Q16/Q28 and Q17/Q31 overlap — say it twice in slightly different words if both are asked."
    )
    _font(r, size=10, italic=True, color=RGBColor(0x4A, 0x50, 0x78))
    for num, q, a in ITEMS:
        pq = doc.add_paragraph()
        pq.paragraph_format.space_before = Pt(10)
        pq.paragraph_format.space_after = Pt(2)
        r = pq.add_run(f"{num}. ")
        _font(r, size=12, bold=True, color=RGBColor(0x3D, 0x4B, 0xC8))
        r2 = pq.add_run(q)
        _font(r2, size=12, bold=True)
        pa = doc.add_paragraph()
        pa.paragraph_format.space_after = Pt(6)
        pa.paragraph_format.left_indent = Inches(0.15)
        r = pa.add_run("A. ")
        _font(r, size=12, bold=True, color=RGBColor(0x1A, 0x1F, 0x4A))
        r2 = pa.add_run(a)
        _font(r2, size=12)
    path = Path(r"d:\Aarya_Thakare_Answer_Bank.docx")
    doc.save(path)
    return path


def main() -> None:
    q = build_questions()
    a = build_answers()
    print("wrote", q)
    print("wrote", a)


if __name__ == "__main__":
    main()
