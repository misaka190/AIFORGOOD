import { Suspense } from "react";

import { AnalysisRuntime } from "./analysis-runtime";

export default async function AnalysisPage({
  searchParams
}: {
  searchParams: Promise<{ imageId?: string; storageKey?: string }>;
}) {
  const params = await searchParams;

  return (
    <Suspense fallback={<div className="container-page pb-14 pt-8 text-sm text-textMuted">正在初始化分析任务...</div>}>
      <AnalysisRuntime imageId={params.imageId ?? null} storageKey={params.storageKey ?? null} />
    </Suspense>
  );
}
