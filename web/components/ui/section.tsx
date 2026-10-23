import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

export function Section({
  id,
  className,
  children,
  labelledBy,
}: {
  id?: string;
  className?: string;
  children: ReactNode;
  labelledBy?: string;
}) {
  return (
    <section id={id} aria-labelledby={labelledBy} className={cn("relative py-14 sm:py-20 lg:py-24", className)}>
      {children}
    </section>
  );
}
