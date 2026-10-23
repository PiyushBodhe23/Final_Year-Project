"use client";

import Link from "next/link";
import { ArrowRight, Bot, Menu, X } from "lucide-react";
import { useEffect, useState } from "react";

import { ThemeToggle } from "@/components/theme-toggle";
import { navLinks, site } from "@/data/site";
import { cn } from "@/lib/utils";

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <header
      className={cn(
        "sticky top-0 z-50 transition-all duration-200",
        scrolled || open
          ? "border-b border-border/80 bg-background/90 backdrop-blur-xl shadow-xs"
          : "border-b border-transparent bg-background/60 backdrop-blur-md",
      )}
    >
      <div className="mx-auto flex h-20 w-full max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        {/* Brand Logo & Tagline */}
        <Link
          href="/"
          className="group flex shrink-0 items-center gap-3 no-underline"
        >
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-600 via-blue-600 to-indigo-600 text-sm font-black text-white shadow-md shadow-blue-500/25 transition-transform group-hover:scale-105">
            PV
          </span>
          <div className="flex flex-col justify-center">
            <span className="font-display text-lg font-extrabold tracking-tight text-foreground whitespace-nowrap leading-tight">
              {site.name}
            </span>
            <span className="text-[10px] font-bold tracking-wider uppercase text-blue-600 dark:text-blue-400 whitespace-nowrap leading-tight">
              Wearable Clinical AI
            </span>
          </div>
        </Link>

        {/* Center Navigation Links (Pill Style) */}
        <nav
          aria-label="Primary"
          className="hidden items-center rounded-full border border-border/80 bg-muted/40 p-1.5 shadow-xs lg:flex"
        >
          {navLinks.map((link) => (
            <a
              key={link.href}
              href={link.href}
              className="whitespace-nowrap rounded-full px-3.5 py-1.5 text-xs font-semibold text-muted-foreground transition-all hover:bg-background hover:text-foreground"
            >
              {link.label}
            </a>
          ))}
        </nav>

        {/* Right Actions: Theme Toggle, AI Assistant, Launch Dashboard */}
        <div className="hidden shrink-0 items-center gap-2.5 lg:flex">
          <ThemeToggle />

          <Link
            href="/dashboard/chat"
            className="whitespace-nowrap flex items-center gap-1.5 rounded-full border border-border/80 bg-card px-3.5 py-2 text-xs font-semibold text-foreground shadow-xs transition-all hover:border-primary/40 hover:bg-muted"
          >
            <Bot className="h-3.5 w-3.5 text-blue-600 dark:text-blue-400" />
            <span>AI Assistant</span>
          </Link>

          <Link
            href="/dashboard"
            className="whitespace-nowrap group flex items-center gap-1.5 rounded-full bg-[#2563eb] px-4 py-2 text-xs font-bold text-white shadow-sm shadow-blue-500/25 transition-all hover:bg-blue-600"
          >
            <span>Live Dashboard</span>
            <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
          </Link>
        </div>

        {/* Mobile Controls */}
        <div className="flex items-center gap-2 lg:hidden">
          <ThemeToggle />
          <button
            type="button"
            className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-border bg-card text-foreground"
            aria-expanded={open}
            aria-controls="mobile-nav"
            aria-label={open ? "Close menu" : "Open menu"}
            onClick={() => setOpen((value) => !value)}
          >
            {open ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {open ? (
        <nav
          id="mobile-nav"
          aria-label="Mobile Navigation"
          className="border-t border-border bg-background/95 p-4 backdrop-blur-xl lg:hidden shadow-xl"
        >
          <div className="flex flex-col gap-1">
            {navLinks.map((link) => (
              <a
                key={link.href}
                href={link.href}
                className="rounded-xl px-3 py-2.5 text-sm font-semibold text-foreground transition-colors hover:bg-muted"
                onClick={() => setOpen(false)}
              >
                {link.label}
              </a>
            ))}
          </div>

          <div className="mt-4 flex flex-col gap-2 border-t border-border/60 pt-4">
            <Link
              href="/dashboard/chat"
              onClick={() => setOpen(false)}
              className="flex items-center justify-center gap-2 rounded-xl border border-border bg-card py-2.5 text-xs font-bold text-foreground"
            >
              <Bot className="h-4 w-4 text-emerald-500" />
              <span>AI Health Assistant</span>
            </Link>

            <Link
              href="/dashboard"
              onClick={() => setOpen(false)}
              className="flex items-center justify-center gap-2 rounded-xl bg-[#2563eb] py-2.5 text-xs font-bold text-white shadow-md shadow-blue-500/20"
            >
              <span>Launch Live Dashboard</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>
        </nav>
      ) : null}
    </header>
  );
}
