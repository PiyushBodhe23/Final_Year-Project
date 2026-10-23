import * as React from "react";

import { cn } from "@/lib/utils";

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-3xl border border-border/80 bg-card/80 text-card-foreground shadow-card backdrop-blur-md",
        className,
      )}
      {...props}
    />
  );
}
