import { Suspense } from "react";

import { GradcamRuntime } from "./gradcam-runtime";

export default async function GradCamPage({
  searchParams
}: {
  searchParams: Promise<{ predictionId?: string; imageId?: string; storageKey?: string; label?: string }>;
}) {
  const params = await searchParams;

  return (
    <Suspense fallback={<div className="container-page pb-14 pt-8 text-sm text-textMuted">正在初始化 Grad-CAM 页面...</div>}>
      <GradcamRuntime
        predictionId={params.predictionId ?? null}
        imageIdFromQuery={params.imageId ?? null}
        storageKey={params.storageKey ?? null}
        initialLabelFromQuery={params.label ?? null}
      />
    </Suspense>
  );
}
