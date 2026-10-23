"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  AlertTriangle,
  Bot,
  Check,
  Copy,
  Mic,
  MicOff,
  RotateCcw,
  Send,
  Sparkles,
  User,
  Volume2,
  VolumeX,
} from "lucide-react";

import { usePatientId } from "@/components/dashboard/shell";
import { api, API_URL, type Patient } from "@/lib/api";

type Message = {
  role: "user" | "assistant";
  text: string;
  sources?: string[];
  tools?: string[];
  emergency?: boolean;
};

const PERSONA_CHIPS: Record<number, string[]> = {
  1: [
    "What precautions should I take to maintain my low risk?",
    "What dietary suggestions optimize my energy and glucose stability?",
    "How do my daily steps and sleep compare to healthy benchmarks?",
    "What routine preventive health checks should I schedule?",
  ],
  2: [
    "What precautions should I take for my prediabetes and blood sugar?",
    "What dietary suggestions will lower my fasting glucose effectively?",
    "How does my moderate risk index impact my daily exercise routine?",
    "What follow-up lab tests does ICMR recommend for prediabetes?",
  ],
  3: [
    "What urgent precautions should I take given my high cardiovascular risk?",
    "What lifestyle suggestions help reverse arterial strain and low SpO2?",
    "How can I safely start walking more without overstraining my heart?",
    "What specific questions should I ask my doctor at my next visit?",
  ],
};

const DEFAULT_CHIPS = [
  "What precautions should I take based on my risk score?",
  "What dietary and lifestyle suggestions will improve my health index?",
  "How can I safely increase my daily physical activity?",
  "What preventive medical checks should I prioritize next?",
];

/** Clean Markdown Formatter for Assistant Messages with Interactive Follow-up Actions */
function MarkdownRenderer({
  content,
  onSelectFollowUp,
}: {
  content: string;
  onSelectFollowUp?: (question: string) => void;
}) {
  if (!content) return null;

  const lines = content.split("\n");
  let currentSection = "";

  return (
    <div className="space-y-2 text-sm leading-relaxed">
      {lines.map((line, idx) => {
        const trimmed = line.trim();

        // Empty line
        if (!trimmed) {
          return <div key={idx} className="h-1.5" />;
        }

        // Heading 3
        if (trimmed.startsWith("### ")) {
          currentSection = "";
          return (
            <h3 key={idx} className="font-display pt-2 text-base font-bold text-foreground">
              {renderInline(trimmed.replace(/^###\s+/, ""))}
            </h3>
          );
        }

        // Heading 4
        if (trimmed.startsWith("#### ")) {
          const headingText = trimmed.replace(/^####\s+/, "");
          if (headingText.includes("Precautions")) {
            currentSection = "precautions";
            return (
              <div
                key={idx}
                className="mt-3 mb-1.5 flex items-center gap-1.5 rounded-lg border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-xs font-bold uppercase tracking-wider text-amber-600 dark:text-amber-400"
              >
                <AlertTriangle className="h-3.5 w-3.5" />
                <span>{headingText}</span>
              </div>
            );
          }
          if (headingText.includes("Suggestions") || headingText.includes("Lifestyle")) {
            currentSection = "suggestions";
            return (
              <div
                key={idx}
                className="mt-3 mb-1.5 flex items-center gap-1.5 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-xs font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-400"
              >
                <Sparkles className="h-3.5 w-3.5" />
                <span>{headingText}</span>
              </div>
            );
          }
          if (headingText.includes("Follow-up")) {
            currentSection = "followups";
            return (
              <div
                key={idx}
                className="mt-3 mb-1.5 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-blue-600 dark:text-blue-400"
              >
                <span>{headingText}</span>
              </div>
            );
          }
          currentSection = "other";
          return (
            <h4 key={idx} className="font-display pt-2 text-xs font-semibold uppercase tracking-wider text-primary">
              {renderInline(headingText)}
            </h4>
          );
        }

        // Under followups section -> Interactive Clickable Question Buttons
        if (
          currentSection === "followups" &&
          (trimmed.startsWith("- ") || trimmed.startsWith("* ") || trimmed.startsWith("· "))
        ) {
          const rawQ = trimmed.replace(/^[-*·]\s+/, "").replace(/^\*|\*$/g, "").trim();
          return (
            <button
              key={idx}
              type="button"
              onClick={() => onSelectFollowUp?.(rawQ)}
              className="group my-1 flex w-full items-center justify-between gap-2 rounded-xl border border-blue-500/25 bg-blue-500/5 px-3 py-2 text-left text-xs font-medium text-blue-700 transition-all hover:border-blue-500/50 hover:bg-blue-500/10 dark:text-blue-300"
            >
              <span>{rawQ}</span>
              <span className="shrink-0 rounded-full bg-blue-500/15 px-2 py-0.5 text-[10px] font-semibold group-hover:bg-blue-500/30">
                Ask ↵
              </span>
            </button>
          );
        }

        // Blockquote
        if (trimmed.startsWith("> ")) {
          return (
            <blockquote
              key={idx}
              className="my-1.5 rounded-xl border-l-4 border-primary/40 bg-muted/40 p-2.5 text-xs italic text-muted-foreground"
            >
              {renderInline(trimmed.replace(/^>\s+/, ""))}
            </blockquote>
          );
        }

        // Bullet point
        if (trimmed.startsWith("- ") || trimmed.startsWith("· ") || trimmed.startsWith("* ")) {
          const bulletText = trimmed.replace(/^[-·*]\s+/, "");
          const bulletBg =
            currentSection === "precautions"
              ? "bg-amber-500"
              : currentSection === "suggestions"
              ? "bg-emerald-500"
              : "bg-primary";

          return (
            <div key={idx} className="flex items-start gap-2 pl-1">
              <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${bulletBg}`} />
              <div className="flex-1 text-foreground">{renderInline(bulletText)}</div>
            </div>
          );
        }

        // Regular paragraph
        return (
          <p key={idx} className="text-foreground">
            {renderInline(trimmed)}
          </p>
        );
      })}
    </div>
  );
}

/** Helper to parse **bold** and `code` spans */
function renderInline(text: string): React.ReactNode[] {
  // Regex splitting by bold (**...**) and inline code (`...`)
  const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);

  return parts.map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={i} className="font-semibold text-foreground">
          {part.slice(2, -2)}
        </strong>
      );
    }
    if (part.startsWith("`") && part.endsWith("`")) {
      return (
        <code key={i} className="rounded bg-muted px-1.5 py-0.5 font-mono text-xs font-medium text-foreground">
          {part.slice(1, -1)}
        </code>
      );
    }
    return part;
  });
}

export default function ChatPage() {
  const patientId = usePatientId();
  const [patient, setPatient] = useState<Patient | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      text: "### 👋 PreventVital Clinical AI Assistant\n\nI am grounded strictly in this patient's validated laboratory results, 180-day continuous wearable telemetry, and evidence-based clinical screening guidelines (ICMR, WHO, ADA, AHA).\n\n- **No Hallucinated Data**: Every number and risk factor quoted comes directly from verified database records.\n- **Evidence-Based Guidance**: Concrete lifestyle actions are linked directly to clinical prevention protocols.\n- **Non-Diagnostic**: This assistant is a preventive risk-awareness tool, not a diagnostic or prescribing service.\n\nHow can I help you analyze this record today?",
    },
  ]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);
  const [listening, setListening] = useState(false);
  const [speakingIdx, setSpeakingIdx] = useState<number | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    api.patient(patientId).then(setPatient).catch(console.error);
  }, [patientId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, busy]);

  // Speech Recognition (Voice Input)
  const toggleListening = () => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const win = window as any;
    const SpeechRecognitionClass = win.SpeechRecognition || win.webkitSpeechRecognition;

    if (!SpeechRecognitionClass) {
      alert("Speech recognition is not supported in this browser. Please use Google Chrome or Edge.");
      return;
    }

    if (listening) {
      setListening(false);
      return;
    }

    try {
      const recognition = new SpeechRecognitionClass();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = "en-US";

      recognition.onstart = () => setListening(true);
      recognition.onend = () => setListening(false);
      recognition.onerror = () => setListening(false);

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      recognition.onresult = (event: any) => {
        const transcript = event.results?.[0]?.[0]?.transcript;
        if (transcript) {
          setDraft((prev) => (prev ? `${prev} ${transcript}` : transcript));
        }
      };

      recognition.start();
    } catch (err) {
      console.error(err);
      setListening(false);
    }
  };

  // Text-to-Speech (Read Aloud)
  const toggleSpeak = (idx: number, text: string) => {
    if (speakingIdx === idx) {
      window.speechSynthesis?.cancel();
      setSpeakingIdx(null);
      return;
    }

    if (!("speechSynthesis" in window)) {
      alert("Text-to-speech is not supported in this browser.");
      return;
    }

    window.speechSynthesis.cancel();
    const cleanText = text.replace(/[*#`_>-]/g, " ");
    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    utterance.onend = () => setSpeakingIdx(null);
    utterance.onerror = () => setSpeakingIdx(null);

    setSpeakingIdx(idx);
    window.speechSynthesis.speak(utterance);
  };

  const copyToClipboard = (text: string, idx: number) => {
    void navigator.clipboard.writeText(text);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  const clearChat = () => {
    window.speechSynthesis?.cancel();
    setMessages([
      {
        role: "assistant",
        text: `Chat session refreshed for **${patient?.name || "Patient"}**. Ask any question regarding their diabetes risk, cardiovascular score, sleep quality, or lifestyle interventions.`,
      },
    ]);
  };

  async function send(text: string) {
    const message = text.trim();
    if (!message || busy) return;
    setDraft("");
    setBusy(true);

    setMessages((current) => [...current, { role: "user", text: message }, { role: "assistant", text: "" }]);

    try {
      const response = await fetch(`${API_URL}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patient_id: patientId, message }),
      });

      if (!response.ok || !response.body) throw new Error(await response.text());

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let sources: string[] = [];
      let tools: string[] = [];
      let emergency = false;

      while (true) {
        const chunk = await reader.read();
        if (chunk.done) break;
        buffer += decoder.decode(chunk.value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";

        for (const part of parts) {
          const line = part.replace(/^data:\s*/, "");
          if (!line) continue;
          const payload = JSON.parse(line) as {
            token?: string;
            done?: boolean;
            sources?: string[];
            tools?: string[];
            emergency?: boolean;
          };

          if (payload.token) {
            const token = payload.token;
            setMessages((current) => {
              const next = [...current];
              const last = next[next.length - 1];
              next[next.length - 1] = { ...last, text: last.text + token };
              return next;
            });
          }

          if (payload.done) {
            sources = payload.sources || [];
            tools = payload.tools || [];
            emergency = Boolean(payload.emergency);
          }
        }
      }

      setMessages((current) => {
        const next = [...current];
        const last = next[next.length - 1];
        next[next.length - 1] = { ...last, sources, tools, emergency };
        return next;
      });
    } catch (reason) {
      const textError = reason instanceof Error ? reason.message : "Chat service unreachable.";
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          text: `⚠️ **Connection Error**: ${textError}\n\nPlease ensure the FastAPI backend is active on port 8000.`,
        },
      ]);
    } finally {
      setBusy(false);
    }
  }

  const activeChips = PERSONA_CHIPS[patientId] || DEFAULT_CHIPS;

  return (
    <div className="mx-auto flex min-h-[82vh] max-w-4xl flex-col">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border pb-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-500/10 text-blue-500">
              <Bot className="h-5 w-5" />
            </div>
            <h1 className="font-display text-2xl font-extrabold tracking-tight">AI Virtual Health Assistant</h1>
            <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400">
              RAG Grounded Engine
            </span>
          </div>
          <p className="mt-1 text-xs text-muted-foreground">
            Scoped to {patient ? `${patient.name} (${patient.age} ${patient.sex})` : "Active Patient"}. Query labs, sleep trends, risk scores, and ICMR/WHO guidelines.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={clearChat}
            className="flex items-center gap-1.5 rounded-full border border-border bg-card px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Clear History</span>
          </button>
        </div>
      </div>

      {/* Suggested Quick Prompt Chips */}
      <div className="my-4">
        <span className="mb-2 block text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
          Suggested Inquiries for {patient ? patient.name : "this profile"}:
        </span>
        <div className="flex flex-wrap gap-2">
          {activeChips.map((chip) => (
            <button
              key={chip}
              type="button"
              disabled={busy}
              onClick={() => send(chip)}
              className="flex items-center gap-1.5 rounded-full border border-border bg-card px-3.5 py-1.5 text-xs font-medium text-foreground shadow-sm transition-all hover:border-primary hover:bg-primary/5 hover:text-primary disabled:opacity-50"
            >
              <Sparkles className="h-3 w-3 text-primary" />
              <span>{chip}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Message Feed */}
      <div className="flex-1 space-y-4 overflow-y-auto pb-4">
        {messages.map((message, index) => {
          const isUser = message.role === "user";
          const isEmergency = message.emergency;

          return (
            <article
              key={index}
              className={`group relative flex gap-3 rounded-3xl p-5 transition-all ${
                isUser
                  ? "ml-auto max-w-[85%] bg-[#2563eb] text-white shadow-md shadow-blue-500/10"
                  : isEmergency
                  ? "mr-auto w-full border-2 border-rose-500 bg-rose-500/10 text-foreground"
                  : "mr-auto w-full border border-border bg-card text-foreground shadow-sm"
              }`}
            >
              <div
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-2xl ${
                  isUser
                    ? "bg-white/20 text-white"
                    : isEmergency
                    ? "bg-rose-500 text-white"
                    : "bg-primary/10 text-primary"
                }`}
              >
                {isUser ? <User className="h-4 w-4" /> : isEmergency ? <AlertTriangle className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
              </div>

              <div className="min-w-0 flex-1 space-y-2">
                <div className="flex items-center justify-between gap-2">
                  <span className={`text-xs font-bold ${isUser ? "text-white/90" : "text-muted-foreground"}`}>
                    {isUser ? "You" : isEmergency ? "Emergency Triage System" : "PreventVital Assistant"}
                  </span>

                  {!isUser && message.text ? (
                    <div className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                      <button
                        type="button"
                        onClick={() => copyToClipboard(message.text, index)}
                        className="rounded-lg p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                        title="Copy message"
                      >
                        {copiedIdx === index ? <Check className="h-3.5 w-3.5 text-emerald-500" /> : <Copy className="h-3.5 w-3.5" />}
                      </button>
                      <button
                        type="button"
                        onClick={() => toggleSpeak(index, message.text)}
                        className="rounded-lg p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                        title={speakingIdx === index ? "Stop speaking" : "Listen aloud"}
                      >
                        {speakingIdx === index ? <VolumeX className="h-3.5 w-3.5 text-primary" /> : <Volume2 className="h-3.5 w-3.5" />}
                      </button>
                    </div>
                  ) : null}
                </div>

                {/* Message Body */}
                {isUser ? (
                  <p className="whitespace-pre-wrap text-sm leading-relaxed">{message.text}</p>
                ) : message.text ? (
                  <MarkdownRenderer
                    content={message.text}
                    onSelectFollowUp={(q) => void send(q)}
                  />
                ) : (
                  <div className="flex items-center gap-2 py-2 text-xs text-muted-foreground">
                    <span className="h-2 w-2 animate-ping rounded-full bg-primary" />
                    <span>Accessing patient records and guideline index…</span>
                  </div>
                )}

                {/* Citations & Evidence Panel */}
                {!isUser && (message.tools?.length || message.sources?.length) ? (
                  <details className="mt-3 rounded-2xl border border-border/80 bg-muted/30 p-2.5 text-xs text-muted-foreground">
                    <summary className="cursor-pointer font-medium hover:text-foreground">
                      Sources & Grounding Verification ({message.tools?.length || 0} tools, {message.sources?.length || 0} guidelines)
                    </summary>
                    <div className="mt-2 space-y-1.5 pt-1 border-t border-border/50 text-[11px]">
                      {message.tools?.length ? (
                        <div>
                          <span className="font-semibold text-foreground">Tools Executed: </span>
                          <span className="font-mono text-primary">{message.tools.join(", ")}</span>
                        </div>
                      ) : null}
                      {message.sources?.length ? (
                        <div>
                          <span className="font-semibold text-foreground">Guideline Passages: </span>
                          <ul className="mt-1 list-disc space-y-0.5 pl-4 font-mono">
                            {message.sources.map((src, i) => (
                              <li key={i}>{src}</li>
                            ))}
                          </ul>
                        </div>
                      ) : null}
                    </div>
                  </details>
                ) : null}
              </div>
            </article>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Box & Voice Dictation */}
      <form
        className="sticky bottom-0 z-20 mt-2 flex items-center gap-2 rounded-full border border-border bg-card/95 p-1.5 shadow-xl backdrop-blur-md"
        onSubmit={(e) => {
          e.preventDefault();
          void send(draft);
        }}
      >
        <button
          type="button"
          onClick={toggleListening}
          className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition-colors ${
            listening ? "bg-rose-500 text-white animate-pulse" : "bg-muted text-muted-foreground hover:text-foreground"
          }`}
          title={listening ? "Listening... click to stop" : "Voice dictation (speech-to-text)"}
        >
          {listening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
        </button>

        <input
          className="flex-1 bg-transparent px-3 py-2 text-sm text-foreground outline-none placeholder:text-muted-foreground"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder={`Ask anything about ${patient?.name || "this patient"}'s vitals, sleep, or guidelines...`}
          disabled={busy}
        />

        <button
          type="submit"
          disabled={busy || !draft.trim()}
          className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#2563eb] text-white shadow-md shadow-blue-500/20 transition-all hover:bg-blue-700 disabled:opacity-40"
          title="Send inquiry"
        >
          <Send className="h-4 w-4" />
        </button>
      </form>
    </div>
  );
}
