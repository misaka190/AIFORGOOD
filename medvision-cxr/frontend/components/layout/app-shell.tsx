import { ReactNode } from "react";

import { TopNav } from "@/components/layout/top-nav";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell bg-hero-glow">
      <div className="clinical-grid bg-clinical-grid">
        <TopNav />
        <main>{children}</main>
      </div>
    </div>
  );
}
