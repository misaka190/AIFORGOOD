export function DisclaimerPanel({ title = "免责声明", text }: { title?: string; text: string }) {
  return (
    <div className="rounded-2xl border border-warning/25 bg-warning/10 p-4">
      <div className="text-sm font-semibold text-text">{title}</div>
      <p className="mt-2 text-sm leading-6 text-textMuted">{text}</p>
    </div>
  );
}
