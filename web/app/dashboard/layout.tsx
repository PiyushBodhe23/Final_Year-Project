import { Suspense } from "react";

import { Shell } from "@/components/dashboard/shell";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <Suspense fallback={<div className="p-8">Loading the demo…</div>}>
      <Shell>{children}</Shell>
    </Suspense>
  );
}
