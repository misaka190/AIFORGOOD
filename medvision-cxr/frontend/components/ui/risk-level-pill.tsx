import { RiskLevel } from "@/types";

import { cn } from "@/lib/utils";

const labelMap: Record<RiskLevel, string> = {
  low: "低风险",
  medium: "中风险",
  high: "高风险",
  "priority-review": "需优先复核"
};

const toneMap: Record<RiskLevel, string> = {
  low: "bg-success/10 text-success border-success/20",
  medium: "bg-warning/10 text-warning border-warning/20",
  high: "bg-accent/15 text-accent border-accent/30",
  "priority-review": "bg-danger/10 text-danger border-danger/30"
};

export function RiskLevelPill({ level }: { level: RiskLevel }) {
  return <span className={cn("inline-flex items-center rounded-full border px-4 py-2 text-sm font-semibold", toneMap[level])}>{labelMap[level]}</span>;
}
