"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  Activity,
  Bot,
  Check,
  ChevronDown,
  LayoutDashboard,
  Search,
  User,
  UserPlus,
} from "lucide-react";

import { ThemeToggle } from "@/components/theme-toggle";
import { api, type Patient } from "@/lib/api";
import { AddPatientDialog } from "./add-patient-dialog";

const LINKS = [
  { href: "/dashboard", label: "Overview", icon: LayoutDashboard },
  { href: "/dashboard/wearables", label: "Wearables & Trends", icon: Activity },
  { href: "/dashboard/chat", label: "AI Assistant", icon: Bot },
];

export function patientHref(path: string, id: number): string {
  return `${path}?patient=${id}`;
}

export function usePatientId(): number {
  const params = useSearchParams();
  const id = Number(params.get("patient") || "1");
  return Number.isFinite(id) && id > 0 ? id : 1;
}

/** Custom Accessible Patient Persona Dropdown with Unified 100-Patient List */
function PatientSelector({
  patients,
  currentId,
  onSelect,
  onOpenAddPatient,
}: {
  patients: Patient[];
  currentId: number;
  onSelect: (id: number) => void;
  onOpenAddPatient: () => void;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close on click outside or Escape
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
      document.addEventListener("keydown", handleKeyDown);
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  const currentPatient = patients.find((p) => p.id === currentId) || patients[0];

  const filteredPatients = useMemo(() => {
    if (!search.trim()) return patients;
    const query = search.toLowerCase();
    return patients.filter(
      (p) =>
        p.name.toLowerCase().includes(query) ||
        `#${p.id}`.includes(query) ||
        p.id.toString().includes(query) ||
        `${p.age}`.includes(query),
    );
  }, [patients, search]);

  return (
    <div className="relative" ref={dropdownRef}>
      {/* Trigger Pill */}
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="flex items-center gap-2 rounded-full border border-border/80 bg-muted/60 dark:bg-card px-3 py-1.5 text-xs font-semibold text-foreground shadow-xs transition-all hover:border-primary/40 hover:bg-muted"
        aria-expanded={open}
        aria-label="Select Patient Persona"
      >
        <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary/10 text-primary">
          <User className="h-3 w-3" />
        </span>
        <span className="font-semibold text-foreground max-w-[170px] sm:max-w-none truncate">
          {currentPatient
            ? `${currentPatient.name} (${currentPatient.age}y ${currentPatient.sex})`
            : "Select Patient"}
        </span>
        <ChevronDown
          className={`h-3.5 w-3.5 text-muted-foreground transition-transform duration-200 ${
            open ? "rotate-180" : ""
          }`}
        />
      </button>

      {/* Floating Dropdown Menu (Unified Single List) */}
      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 sm:w-96 rounded-2xl border border-border bg-card/95 dark:bg-card p-2.5 shadow-2xl z-50 backdrop-blur-xl animate-in fade-in-50 zoom-in-95">
          {/* Quick Filter Search & Counter */}
          <div className="mb-2 px-1">
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-muted-foreground" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder={`Search ${patients.length} patients by name, ID or age...`}
                className="w-full rounded-xl border border-border bg-muted/40 py-2 pl-8 pr-3 text-xs outline-none focus:border-primary/50 text-foreground placeholder:text-muted-foreground"
                autoFocus
              />
            </div>
            <div className="flex items-center justify-between pt-2 px-1 text-[11px] font-medium text-muted-foreground">
              <span>Patient Directory</span>
              <span className="font-mono">
                {filteredPatients.length} of {patients.length} records
              </span>
            </div>
          </div>

          {/* Unified Scrollable Patient List */}
          <div className="max-h-72 overflow-y-auto pr-1 space-y-1">
            {filteredPatients.map((p) => {
              const isSelected = p.id === currentId;
              const initials = p.name.slice(0, 2).toUpperCase();

              return (
                <button
                  key={p.id}
                  type="button"
                  onClick={() => {
                    onSelect(p.id);
                    setOpen(false);
                  }}
                  className={`flex w-full items-center justify-between rounded-xl px-2.5 py-2 text-xs text-left transition-colors ${
                    isSelected
                      ? "bg-primary/10 text-primary font-bold shadow-xs ring-1 ring-primary/20"
                      : "text-foreground hover:bg-muted/60"
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-muted text-[10px] font-bold text-muted-foreground">
                      {initials}
                    </span>
                    <div className="min-w-0">
                      <div className="flex items-center gap-1.5">
                        <span className="font-semibold text-foreground truncate">{p.name}</span>
                        <span className="font-mono text-[10px] text-muted-foreground">
                          #{p.id.toString().padStart(3, "0")}
                        </span>
                      </div>
                      <div className="text-[10px] text-muted-foreground">
                        {p.age} Years · {p.sex === "M" ? "Male" : "Female"}{" "}
                        {p.bmi ? `· BMI ${p.bmi}` : ""}
                      </div>
                    </div>
                  </div>
                  {isSelected && <Check className="h-4 w-4 shrink-0 text-primary" />}
                </button>
              );
            })}

            {filteredPatients.length === 0 && (
              <div className="py-6 text-center text-xs text-muted-foreground">
                No matching patients found.
              </div>
            )}
          </div>

          {/* Pinned Bottom "+ Register New Patient" Action */}
          <div className="pt-2 border-t border-border/60 px-1 mt-1">
            <button
              type="button"
              onClick={() => {
                setOpen(false);
                onOpenAddPatient();
              }}
              className="flex w-full items-center justify-center gap-2 rounded-xl border border-dashed border-blue-500/50 bg-blue-500/10 py-2.5 text-xs font-bold text-blue-600 dark:text-blue-400 hover:bg-blue-500/20 transition-colors"
            >
              <UserPlus className="h-3.5 w-3.5" />
              <span>+ Register New Patient Profile</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export function Shell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const patientId = usePatientId();
  const [patients, setPatients] = useState<Patient[]>([]);
  const [apiError, setApiError] = useState("");
  const [addPatientOpen, setAddPatientOpen] = useState(false);
  const [justAddedPatient, setJustAddedPatient] = useState<string | null>(null);

  useEffect(() => {
    api
      .patients()
      .then((rows) => {
        setPatients(rows);
        setApiError("");
      })
      .catch((reason: Error) => {
        setPatients([]);
        setApiError(reason.message || "Could not reach the PreventVital API.");
      });
  }, []);

  function handlePatientCreated(newPatient: Patient) {
    setPatients((prev) => [newPatient, ...prev]);
    setJustAddedPatient(newPatient.name);
    router.push(patientHref(pathname, newPatient.id));
    setTimeout(() => setJustAddedPatient(null), 6000);
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-40 border-b border-border bg-background/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-4 px-4 py-3">
          <div className="flex items-center gap-6">
            <Link href="/" className="flex items-center gap-2">
              <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#2563eb] text-white font-bold text-sm shadow-sm">
                PV
              </span>
              <span className="font-display text-lg font-bold tracking-tight">PreventVital</span>
            </Link>

            <nav className="flex flex-wrap items-center gap-1 text-xs font-medium">
              {LINKS.map((link) => {
                const Icon = link.icon;
                const isActive = pathname === link.href;
                return (
                  <Link
                    key={link.href}
                    href={patientHref(link.href, patientId)}
                    className={`flex items-center gap-1.5 rounded-full px-3 py-1.5 transition-all ${
                      isActive
                        ? "bg-[#2563eb] text-white font-semibold shadow-sm"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground"
                    }`}
                  >
                    <Icon className="h-3.5 w-3.5" />
                    <span>{link.label}</span>
                  </Link>
                );
              })}
            </nav>
          </div>

          <div className="flex items-center gap-2">
            {/* Quick "+ Add Patient" Button */}
            <button
              type="button"
              onClick={() => setAddPatientOpen(true)}
              className="flex items-center gap-1.5 rounded-full bg-blue-600 hover:bg-blue-700 text-white px-3.5 py-1.5 text-xs font-bold shadow-xs transition-all hover:scale-[1.02] active:scale-[0.98]"
            >
              <UserPlus className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Add Patient</span>
            </button>

            {/* Unified 100-Patient Dropdown */}
            <PatientSelector
              patients={patients}
              currentId={patientId}
              onSelect={(newId) => router.push(patientHref(pathname, newId))}
              onOpenAddPatient={() => setAddPatientOpen(true)}
            />

            <ThemeToggle />
          </div>
        </div>
      </header>

      {/* Success Notification after adding patient */}
      {justAddedPatient && (
        <div className="mx-auto max-w-7xl px-4 pt-4">
          <div className="flex items-center justify-between rounded-2xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-600 dark:text-emerald-400 shadow-sm animate-in fade-in-50">
            <span className="font-semibold">
              ✓ Successfully registered patient &ldquo;{justAddedPatient}&rdquo;! 180-day continuous wearable telemetry and risk scores have been computed.
            </span>
            <button
              type="button"
              onClick={() => setJustAddedPatient(null)}
              className="text-xs font-bold hover:underline"
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      <main className="mx-auto max-w-7xl px-4 py-6">
        {apiError ? (
          <div className="mb-6 rounded-2xl border border-rose-500/20 bg-rose-500/10 p-4 text-xs text-rose-500 shadow-sm">
            <span className="font-semibold">Backend Connection Notice: </span>
            <span>
              PreventVital API is currently offline. Start the backend server (`uvicorn
              backend.app.main:app --reload --app-dir .` on port 8000), then refresh. ({apiError})
            </span>
          </div>
        ) : null}
        {children}
      </main>

      {/* Add Patient Modal Dialog */}
      <AddPatientDialog
        open={addPatientOpen}
        onClose={() => setAddPatientOpen(false)}
        onPatientCreated={handlePatientCreated}
      />

      <footer className="mx-auto max-w-7xl border-t border-border/40 px-4 py-6 text-center text-xs text-muted-foreground">
        <p className="font-medium text-foreground">
          PreventVital · Explainable Preventive Healthcare Monitoring Prototype
        </p>
        <p className="mt-1">
          Academic prototype built on public datasets and synthetic multi-sensor continuous telemetry.
          Not intended for clinical diagnosis, prescribing, or emergency care.
        </p>
      </footer>
    </div>
  );
}
