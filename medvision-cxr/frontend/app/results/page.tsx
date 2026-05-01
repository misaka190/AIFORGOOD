import { Suspense } from "react";

import { ResultsRuntime } from "./results-runtime";

export default async function ResultsPage({
  searchParams
}: {
  searchParams: Promise<{ predictionId?: string; imageId?: string; storageKey?: string }>;
}) {
  const params = await searchParams;

  return (
    <Suspense fallback={<div className="container-page pb-14 pt-8 text-sm text-textMuted">正在加载分析结果页面...</div>}>
      <ResultsRuntime
        predictionId={params.predictionId ?? null}
        imageIdFromQuery={params.imageId ?? null}
        storageKey={params.storageKey ?? null}
      />
    </Suspense>
  );
}
