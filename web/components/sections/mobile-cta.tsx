"use client";

import { useEffect, useState } from "react";

export function MobileCta() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const onScroll = () => setVisible(window.scrollY > 640);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  if (!visible) return null;

  return (
    <div className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-background/95 p-3 backdrop-blur md:hidden">
      <a href="/dashboard" className="flex h-11 items-center justify-center rounded-full bg-brand-600 text-sm font-semibold text-white">
        Open dashboard
      </a>
    </div>
  );
}
