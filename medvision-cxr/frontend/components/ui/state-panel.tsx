import type { Route } from "next";
import Link from "next/link";
import { ReactNode } from "react";
import { AlertTriangle, Inbox, RefreshCw } from "lucide-react";

import { Button } from "@/components/ui/button";

type StatePanelProps = {
  tone?: "empty" | "error";
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: Route;
  actionIcon?: ReactNode;
};

export function StatePanel({ tone = "empty", title, description, actionLabel, actionHref, actionIcon }: StatePanelProps) {
  const Icon = tone === "error" ? AlertTriangle : Inbox;

  return (
    <div className="card-medical flex flex-col items-center justify-center px-6 py-12 text-center">
      <div className={`mb-4 flex h-14 w-14 items-center justify-center rounded-2xl ${tone === "error" ? "bg-danger/10 text-danger" : "bg-surfaceMuted text-textMuted"}`}>
        <Icon className="h-6 w-6" />
      </div>
      <h2 className="text-xl font-semibold text-text">{title}</h2>
      <p className="mt-3 max-w-xl text-sm leading-6 text-textMuted">{description}</p>
      {actionLabel && actionHref ? (
        <Link href={actionHref} className="mt-6">
          <Button variant={tone === "error" ? "danger" : "secondary"} className="gap-2">
            {actionIcon ?? <RefreshCw className="h-4 w-4" />}
            {actionLabel}
          </Button>
        </Link>
      ) : null}
    </div>
  );
}
