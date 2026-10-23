"""Generate an easy 150-question bank with short answers."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

QA_A = [
    ("What is the name of this project?", "An Interoperable Wearable Health Data Framework for real-time predictive health monitoring. The demo product is also called PulseVanguard AI."),
    ("Who are the student authors?", "Akash Deshmukh, Aarya Thakare, and Tanish Khedekar, final-year B.Tech students in E&TC at JSPM’s Rajarshi Shahu College of Engineering, Pune."),
    ("Who is the project guide?", "Dr. Nilima Mohite (the paper also thanks Mr. P. A. Gangarde for mentorship). Academic year 2025–26."),
    ("What problem does the paper start with?", "Most healthcare is reactive: we check a patient mainly after symptoms appear or only at clinic visits, so chronic disease can worsen in between."),
    ("What does WHO say about non-communicable diseases?", "Conditions such as heart disease, diabetes, hypertension, and chronic lung disease cause about 74% of deaths worldwide, and many are preventable with earlier detection."),
    ("What are NCDs in simple words?", "Long-term diseases that are not passed from person to person, such as diabetes, high blood pressure, and heart disease."),
    ("Why are clinic visits not enough?", "They capture a snapshot. Wearables can record heart rate, SpO₂, activity, and temperature continuously, filling the gap between visits."),
    ("Name three common wearables mentioned in the work.", "Apple Watch, Samsung Galaxy Watch, and Fitbit (also other fitness brands in the demo story)."),
    ("What three technology gaps did the survey find?", "Fragmented wearable data, no personal health baseline, and alerts that go to only one person at a time."),
    ("How many research papers were reviewed?", "Twenty peer-reviewed studies published between 2016 and 2025."),
    ("Which databases were searched?", "IEEE Xplore, PubMed/MEDLINE, Springer, and MDPI, plus a few other health-informatics sources."),
    ("Name the five survey themes.", "Wearable IoT monitoring, ML disease-risk prediction, health-data interoperability, smart alerting, and AI virtual health assistants."),
    ("What is interoperability in this project?", "Making data from different apps and watches speak one common format so one AI model can use all of it."),
    ("What is HRI?", "Health Risk Index: one score from 0 to 100 that summarises how concerning the current vitals are."),
    ("What are the four HRI bands in the software?", "Low (0–25), moderate (25–50), high (50–75), and critical (75–100)."),
    ("Which machine-learning models does the paper propose?", "An ensemble using Random Forest and LSTM, plus rules if the neural net is not available."),
    ("Why Random Forest?", "Studies such as Zhou et al. found RF works well on noisy wearable data, often better than SVM in that setting."),
    ("Why LSTM?", "LSTM networks remember patterns over time, which fits hourly vital history and papers such as Miotto and Rigla."),
    ("What is a three-channel alert?", "The same risk event is explained to the patient, a caregiver, and a clinician at the same time—not only one of them."),
    ("What did older alert systems usually do?", "They notified either staff or caregivers, but not patient, family, and clinician together."),
    ("What is the virtual health assistant?", "A chatbot (Ollama in the demo) that answers using this patient’s live vitals, history, and short forecast."),
    ("Why must the chatbot see live data?", "Earlier healthcare chatbots used only a static profile, so they could not react to today’s heart rate or SpO₂."),
    ("Is this a medical device?", "No. It is an academic / educational demo with synthetic data. It is not a diagnosis and does not replace a doctor."),
    ("What vitals does the demo mainly use?", "Heart rate, SpO₂, respiratory rate, temperature, systolic and diastolic blood pressure, and steps."),
    ("What does the seven-stage pipeline start with?", "Wearable devices collecting signals, then normalization, then AI scoring, then HRI, alerts, and a dashboard with an assistant."),
    ("What does ‘normalize’ mean here?", "Convert each vendor’s reading into one schema: who, when, what metric, value, unit, and source."),
    ("Where does the demo run?", "A local FastAPI server at http://127.0.0.1:8000 (site) and http://127.0.0.1:8000/demo."),
    ("What data is in the 500-patient set?", "Synthetic patients P001–P500 with age, gender, names, and about 24 hours of hourly vitals each."),
    ("How do you add a new patient in the demo?", "Enter name, age, and gender. The system gives the next ID (for example P501) and writes 24 hours of history into the dataset."),
    ("Can age be only 18–90?", "No. New users can have a normal age (about 1–120). The original synthetic cohort was generated as adults."),
    ("How do you search a patient?", "Type a name or ID (for example Priya or P002) in the search box, then pick them from the list."),
    ("What does the forecast show?", "A short future trend (about 6 hours) of vitals and predicted HRI, for teaching only."),
    ("Name the three alert roles you will see on screen.", "Patient, caregiver, and clinician."),
    ("What should you say if HRI is ‘low’?", "Vitals look relatively stable in this simulation; keep normal habits. Still not a medical clearance."),
    ("What should you say if HRI is ‘critical’?", "The simulated score is in the highest band; the demo shows urgent-style messages to all three channels. A real patient would need a clinician."),
    ("Which paper supports open health APIs?", "Mandl and Kohane (2016) argued lack of interoperability is a major barrier and called for open APIs."),
    ("Which review said software lagged behind wearable hardware?", "Dias and Cunha (2018), review of 47 wearable systems."),
    ("What did Escobar / Kaiser Permanente show?", "An ML early-warning system in hospitals gave about 12 hours extra warning and cut ICU transfers by about 18%. That is hospital EHR, not our wearable trial."),
    ("What did Laranjo et al. find about chatbots?", "Conversational agents can help engagement (for example medication habits), but the reviewed bots were not tied to live wearable streams."),
    ("What did Torous et al. report?", "About a 26% improvement in treatment adherence with smartphone-style digital health in some studies."),
    ("Do we claim we saved $1,200 per patient?", "No. That range comes from cost papers such as Kolasa & Grzybowski, not from our demo."),
    ("What is PulseVanguard AI?", "The name of the marketing/demo website that sits on top of the wearable-health-framework software."),
    ("What happens if Ollama is off?", "Chat falls back to a local text reply using the same vitals/HRI context, and we say the model is offline."),
    ("Why not open demo.html as a file?", "The page must be served by the server so it can call /patients and /chat. Use localhost:8000/demo."),
    ("What is synthetic data?", "Made-up educational records that look like vitals, used so we never handle real patient secrets in this college project."),
    ("Name one limitation of the current software.", "Vendor OAuth (Fitbit/Google Fit, etc.) is only a demo stub; LSTM may be skipped if TensorFlow is not installed."),
    ("What is the main originality you should claim?", "One academic platform that combines multi-source vitals, a composite HRI, three-channel alerts, and a live-data assistant—not ‘we invented AI healthcare’."),
    ("How would you explain the project in 20 seconds?", "Watches already collect data, but it sits in silos. We unify it, score a Health Risk Index, alert patient, family, and clinician together, and let an assistant explain the numbers. Demo only."),
    ("What must every chat answer include?", "A disclaimer that this is educational, not a diagnosis or a substitute for professional care."),
    ("If asked ‘can this replace doctors?’ what do you say?", "No. It is a monitoring and explanation aid for teaching. Clinical decisions stay with qualified professionals."),
]

QA_B = [
    ("What does ‘reactive healthcare’ mean in one line?", "We mostly act after the person already feels unwell or comes to hospital, instead of watching trends early."),
    ("Why mention Apple, Samsung, and Fitbit in the introduction?", "They show that sensors are already in people’s pockets; the missing piece is a shared, intelligent software layer."),
    ("What is a personal baseline?", "A person’s usual vital range. A fixed ‘normal’ for everyone can false-alarm athletes or miss risk in older adults. The paper wants per-user HRI; the demo uses population bands plus history."),
    ("List the HRI bands again.", "Low 0–25, moderate 25–50, high 50–75, critical 75–100."),
    ("What files store the 500 patients?", "patient_history.csv for hourly vitals, patient_demographics.csv for age, gender, and name, and a training Excel snapshot."),
    ("What ID do synthetic patients use?", "P001, P002, … up to P500, then new enrollments continue (P501, …)."),
    ("Which Python app serves the website?", "FastAPI in backend/main.py using uvicorn on port 8000."),
    ("Which folder holds the public pages?", "website/index.html (landing) and website/demo.html (live dashboard)."),
    ("What is Streamlit used for?", "An optional second dashboard (frontend/app.py) that talks to the same backend ideas."),
    ("What does the risk engine combine?", "Random Forest score (if weights exist), optional LSTM, and a rule-based heuristic, then maps the number to a band."),
    ("What if LSTM is missing?", "The system still scores HRI using Random Forest and/or heuristic rules so the demo does not crash."),
    ("Why keep a heuristic score?", "If the ML model under-scores obviously bad vitals, rules still push HRI up (important for critical test patients)."),
    ("Name the alert channels in code.", "patient, caregiver, and clinician."),
    ("Are WhatsApp messages really sent?", "No. Delivery is simulated on the dashboard so we can show the three-channel design without live messaging accounts."),
    ("What does /chat need?", "The user question plus patient_id so the server can attach vitals, HRI, history text, and forecast."),
    ("What local AI software is used?", "Ollama, typically a Llama 3.x model running on the laptop."),
    ("Why can the first chat be slow?", "The model must load into memory on CPU; later replies are usually faster if the model stays loaded."),
    ("What is a unified metric JSON?", "A record with user_id, timestamp, metric_type, value, unit, and source so Fitbit and Apple-style data can look the same."),
    ("Does the demo fully connect Apple Health?", "Not with real OAuth. Connectors are stubs for the academic story; scoring uses the CSV dataset."),
    ("What did Kajornkasirat et al. build?", "A wearable IoT pipeline with MAX30102 and temperature sensors and an RF/MLP/SVM ensemble; limited by a small sample."),
    ("What accuracy did Ekanath et al. report?", "About 92% in their prototype, with alerts in roughly 3–5 seconds. They used simulated data."),
    ("What is Deng et al.’s simple takeaway?", "Using several sensors together (HR, SpO₂, temperature, activity) usually beats one sensor; battery and standards remain hard."),
    ("What is Rigla et al. known for here?", "LSTM on glucose data predicting low sugar about 30 minutes ahead with high sensitivity—example of time-series prediction, not our exact task."),
    ("What is Perez / Apple Watch known for?", "A very large study showing consumer ECG can help find atrial fibrillation—not a full multi-vital HRI pipeline."),
    ("What does Table III Gap 1 say?", "No cross-platform wearable integration; our response is a unified API/schema layer."),
    ("What does Table III Gap 2 say?", "Single-recipient alerts; our response is three-channel alerts."),
    ("What does Table III Gap 4 say?", "Virtual assistants without live data; our response is a chatbot fed with current vitals and forecast."),
    ("Why ‘zero hardware cost’ in the paper?", "The design uses consumer watches people already own, instead of building a custom Arduino kit for every user."),
    ("Is the college demo cloud-native today?", "It runs locally for the viva. The paper’s ‘cloud-native’ line is the intended scale, not the current laptop setup."),
    ("How do you start the server?", "Activate the venv, then: uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000 from the wearable-health-framework folder."),
    ("What does the patient card show?", "Name or ID, age, gender, and latest HR, SpO₂, respiration, temperature, BP, and steps."),
    ("What tables appear on the demo?", "Past readings, forecast, alerts, and the AI assistant chat."),
    ("How do you pick a ‘critical’ demo patient?", "Search IDs such as P002, P010, P050, or P100 that were given extreme simulated vitals for testing alerts."),
    ("What is SpO₂?", "Blood oxygen saturation, shown as a percentage. Low values in the demo raise HRI."),
    ("What is systolic vs diastolic BP?", "Systolic is the top number (heart beating); diastolic is the bottom (heart resting). Both enter HRI."),
    ("Why include steps?", "Activity context; rest versus walking changes how we read heart rate. It is also a model feature."),
    ("What is sepsis_label in the CSV?", "A dataset flag for experiments, not a real hospital diagnosis of the named demo person."),
    ("Can you search by first name?", "Yes. After names were added (for example Meera Sharma), search matches name, ID, age, or gender."),
    ("What if the dropdown says No matches?", "Clear the search box and refresh http://127.0.0.1:8000/demo while the server is running."),
    ("What is FastAPI?", "The Python web framework that serves pages and JSON APIs."),
    ("What is the disclaimer you always repeat?", "Educational demonstration only; not medical advice, not a diagnosis."),
    ("Name one hospital ML result you can quote carefully.", "Escobar et al.: about 18% fewer ICU transfers and ~12-hour earlier warning—in hospitals, not in our wearable study."),
    ("Name one chatbot review result.", "Laranjo et al.: better engagement in several studies, but no live wearable hook in those bots."),
    ("What is the Composite HRI meant to replace?", "Looking at each vital in isolation, or using one fixed alarm limit for every human."),
    ("How is forecast different from HRI?", "HRI is the score now. Forecast is a simple projection of vitals and HRI a few hours ahead for illustration."),
    ("What language is the backend?", "Python."),
    ("What must you not claim in viva?", "That we diagnosed disease, treated patients, or clinically validated accuracy on real Indian hospital data."),
    ("How do alerts change with band?", "Low: mostly patient info. Moderate: patient + caregiver. High/critical: all three roles with stronger wording."),
    ("What is Ollama?", "A program that runs large language models on your computer so chat does not need a paid cloud key."),
    ("Give a 15-second process answer.", "Collect vitals → put them in one format → compute HRI with ML and rules → send three alerts → show charts and a grounded chatbot."),
]

QA_C = [
    ("What is the demo URL?", "http://127.0.0.1:8000/demo after uvicorn is running."),
    ("What is the landing-page URL?", "http://127.0.0.1:8000 for PulseVanguard AI."),
    ("What should you open in the browser?", "Chrome or Edge on localhost. Do not double-click the HTML file."),
    ("How do you tell the problem in one sentence?", "Health data from watches is scattered, visits are late, and warnings do not reach patient, family, and doctor together."),
    ("How do you tell the solution in one sentence?", "We unify vitals, compute a Health Risk Index, alert three roles, and let an assistant explain that patient’s numbers."),
    ("What does ‘fragmented data’ look like to a user?", "Steps in one app, heart rate in another, and the clinic seeing none of it in one place."),
    ("What screen proves three-channel alerts?", "The Alerts panel listing patient, caregiver, and clinician messages for the same HRI."),
    ("What screen proves prediction?", "The Forecast table with +hours, HR, SpO₂, predicted HRI, and band."),
    ("What screen proves the assistant uses data?", "Ask ‘What is the current HRI and age?’ and check it matches the patient card."),
    ("Why might age have been ‘not specified’ before?", "The small model ignored the file. We now inject age and gender from demographics into the prompt."),
    ("Is the assistant always correct?", "No. It can still ramble. We cap length and attach facts. Always verify against the dashboard numbers."),
    ("What is a good viva question to ask the bot?", "‘Summarise this patient’s trend and risk band’ or ‘Why might alerts have fired?’"),
    ("What is a bad thing for the bot to say?", "A real diagnosis, a drug dose, or ‘go to hospital now’ as if it were a licensed clinician. We treat it as a demo explainer."),
    ("How many hours of history does a new user get?", "Twenty-four hourly simulated rows so charts and forecasts work immediately."),
    ("What gender options exist in enrollment?", "Female and male only, matching the cleaned demographics file."),
    ("What is patient_memory.py for?", "Loading a person’s history, building trend text, and making the short forecast."),
    ("What is alert_system.py for?", "Turning an HRI band into the three-role messages."),
    ("What is ollama_agent.py for?", "Building the system prompt and calling the local LLM."),
    ("What is normalizer.py for?", "Mapping messy incoming vitals into the common fields the scorer expects."),
    ("What is risk_engine.py for?", "Calculating HRI and choosing the risk band."),
    ("Where are RF weights stored?", "backend/models/weights/rf_model.pkl (LSTM files are optional)."),
    ("What command trains models?", "python backend/models/train_model.py from the project folder (needs the training data)."),
    ("Why show both Streamlit and the website?", "Streamlit is a researcher dashboard; the website is the presentation-facing PulseVanguard UI. Same idea."),
    ("What is CORS in one line?", "A browser rule we relax in the demo so the local page can call the local API."),
    ("Can examiners use this on a real patient today?", "No. Synthetic data, no clinical licence, no hospital validation."),
    ("What did Mandl & Kohane want?", "A more open, patient-accessible health information economy via APIs."),
    ("What did Kawamoto’s alert research teach (as used in the paper)?", "Decision support works better when alerts fire automatically inside the workflow, not when staff must remember to open a tool."),
    ("Why is automatic alerting in the design?", "Because the literature says optional, hidden alerts are often ignored."),
    ("What is the lifestyle engine in the paper vs the code?", "The survey lists personalised lifestyle advice as a goal. The live build focuses on HRI, forecast, alerts, and Q&A—not a full diet app."),
    ("How do you admit that honestly?", "‘Proposed in the architecture; not fully implemented in the current demo.’"),
    ("What is multi-sensor fusion in plain words?", "Using several measurements together so one noisy sensor does not decide everything."),
    ("Give two vitals that often move HRI up.", "Very high or very low heart rate, and SpO₂ dropping toward or below about 90% in the rule table."),
    ("What temperature is concerning in the heuristic table?", "Normal is about 36.1–37.2 °C; values toward 39 °C or below 35 °C are treated as more serious in the demo rules."),
    ("How do you reset a stuck chat?", "Do not click Send repeatedly. Wait, or refresh after Ollama is running."),
    ("What port is Ollama?", "Usually 11434 on the same PC."),
    ("What port is the website?", "8000."),
    ("How do you prove 500 patients exist?", "Open the patient dropdown after a hard refresh; you should see P001 onward with names."),
    ("What is display_name?", "The human name stored with each ID so search and the assistant can say ‘Priya Sharma’, not only P002."),
    ("What is the academic contribution in simple words?", "We surveyed 20 papers, named seven gaps, and built a teaching system that shows how those gaps could be closed together."),
    ("What should you do if the server is not running?", "Start uvicorn again; the empty list is not ‘the 500 patients were deleted’."),
    ("Name the institute and city.", "JSPM’s Rajarshi Shahu College of Engineering, Pune, Maharashtra, India."),
    ("What department are you from?", "Electronics and Telecommunication Engineering."),
    ("How would you start a presentation?", "Problem (late, siloed care) → idea (HRI + 3 alerts + assistant) → demo (one patient) → limits (not clinical)."),
    ("How would you end a presentation?", "Repeat: educational prototype; future work could be real wearables, FHIR, and a proper clinical study."),
    ("What is FHIR in one line?", "A modern standard for sharing health data between systems; a possible next step, not in the current demo."),
    ("Why Python?", "Fast libraries for ML (scikit-learn), APIs (FastAPI), and data (pandas); good for an academic prototype."),
    ("What is scikit-learn used for?", "The Random Forest model for part of HRI."),
    ("Give one easy difference vs Kajornkasirat [1].", "They built custom IoT hardware; we target consumer wearables and a software HRI dashboard."),
    ("Give one easy difference vs Ekanath [2].", "Their alerts targeted caregivers in a prototype; we show three roles at once and add a live-data assistant."),
    ("Final line if you forget everything else?", "Unify wearable data, score HRI, alert three people, explain with AI—demo only, not a doctor."),
]


def _font(run, name="Calibri", size=11, bold=False, italic=False, color=None):
    run.font.name = name
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.bold = bold
    run.italic = italic
    if color is not None:
        run.font.color.rgb = color


def add_qa(doc: Document, n: int, question: str, answer: str) -> None:
    pq = doc.add_paragraph()
    pq.paragraph_format.space_after = Pt(2)
    pq.paragraph_format.space_before = Pt(8)
    pq.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    r = pq.add_run(f"Q{n}. ")
    _font(r, size=11, bold=True, color=RGBColor(0x3D, 0x4B, 0xC8))
    r2 = pq.add_run(question)
    _font(r2, size=11, bold=True)

    pa = doc.add_paragraph()
    pa.paragraph_format.space_after = Pt(6)
    pa.paragraph_format.left_indent = Inches(0.15)
    r = pa.add_run("A. ")
    _font(r, size=11, bold=True, color=RGBColor(0x1A, 0x1F, 0x4A))
    r2 = pa.add_run(answer)
    _font(r2, size=11)


def main() -> None:
    assert len(QA_A) == 50 and len(QA_B) == 50 and len(QA_C) == 50
    doc = Document()
    section = doc.sections[0]
    section.top_margin = Inches(0.85)
    section.bottom_margin = Inches(0.85)
    section.left_margin = Inches(0.95)
    section.right_margin = Inches(0.95)

    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = t.add_run("Easy Q&A Bank (with answers)")
    _font(r, name="Georgia", size=22, bold=True, color=RGBColor(0x1A, 0x1F, 0x4A))

    st = doc.add_paragraph()
    st.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = st.add_run(
        "Interoperable Wearable Health Data Framework  ·  PulseVanguard AI demo\n"
        "150 easy questions · 3 sets of 50  ·  Use this for practice; keep the harder set for tough panels"
    )
    _font(r, name="Georgia", size=12, italic=True, color=RGBColor(0x3D, 0x4B, 0xC8))

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = meta.add_run(
        "Akash Deshmukh · Aarya Thakare · Tanish Khedekar  |  Guide: Dr. Nilima Mohite\n"
        "JSPM’s RSCOE, Pune  ·  AY 2025–26"
    )
    _font(r, size=10, color=RGBColor(0x4A, 0x50, 0x78))

    note = doc.add_paragraph()
    r = note.add_run("How to use. ")
    _font(r, size=11, bold=True)
    r = note.add_run(
        "Answers are short and spoken-style. About ten ideas repeat across sets in simpler words "
        "(problem, three gaps, HRI bands, RF+LSTM, three alerts, chatbot, demo URL, not a doctor). "
        "Always add: this is an educational prototype with synthetic data."
    )
    _font(r, size=11)

    sets = [
        ("Set A — Easy questions and answers", "Mostly ‘what is this project?’ and the paper’s story.", QA_A),
        ("Set B — Easy questions and answers", "Mostly how the system works and famous papers in one line.", QA_B),
        ("Set C — Easy questions and answers", "Mostly the live demo, files, and what to say on stage.", QA_C),
    ]
    for title, blurb, items in sets:
        doc.add_page_break()
        h = doc.add_paragraph()
        r = h.add_run(title)
        _font(r, name="Georgia", size=16, bold=True, color=RGBColor(0x1A, 0x1F, 0x4A))
        b = doc.add_paragraph()
        r = b.add_run(blurb)
        _font(r, size=10, italic=True, color=RGBColor(0x4A, 0x50, 0x78))
        for i, (q, a) in enumerate(items, start=1):
            add_qa(doc, i, q, a)

    path = Path(r"d:\IEEE_Survey_Paper_Health_Framework_QA_150_Easy.docx")
    doc.save(path)
    print("wrote", path)


if __name__ == "__main__":
    main()
