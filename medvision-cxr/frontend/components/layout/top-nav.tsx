import type { Route } from "next";
import Link from "next/link";
import { ActivitySquare, BookOpenText, Clock3, FileImage, ShieldCheck, Stethoscope } from "lucide-react";

const navItems: Array<{ href: Route; label: string; icon: typeof FileImage }> = [
  { href: "/upload", label: "上传分析", icon: FileImage },
  { href: "/results", label: "结果页", icon: ActivitySquare },
  { href: "/review", label: "医生复核", icon: Stethoscope },
  { href: "/history", label: "历史记录", icon: Clock3 },
  { href: "/privacy", label: "隐私与伦理", icon: ShieldCheck },
  { href: "/docs", label: "API 文档", icon: BookOpenText }
];

export function TopNav() {
  return (
    <header className="sticky top-0 z-40 border-b border-border/70 bg-surface/90 backdrop-blur-xl">
      <div className="container-page flex items-center justify-between gap-6 py-4">
        <Link href="/" className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary text-primaryInk shadow-soft">
            <Stethoscope className="h-5 w-5" />
          </div>
          <div>
            <div className="font-display text-lg font-semibold text-text">MedVision-CXR</div>
            <div className="text-sm text-textMuted">Explainable Chest X-ray Triage</div>
          </div>
        </Link>
        <nav className="hidden items-center gap-2 lg:flex">
          {navItems.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className="inline-flex items-center gap-2 rounded-full border border-transparent px-4 py-2 text-sm font-medium text-textMuted transition hover:border-border hover:bg-surfaceMuted hover:text-text"
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
