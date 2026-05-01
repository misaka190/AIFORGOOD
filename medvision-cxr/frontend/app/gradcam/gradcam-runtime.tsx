"use client";

import { useEffect, useMemo, useState } from "react";

import { GradCamViewer } from "@/components/gradcam/gradcam-viewer";
import { PageHeader } from "@/components/ui/page-header";
import { StatePanel } from "@/components/ui/state-panel";
import { buildRawImageUrl, frontendApi, getApiErrorMessage } from "@/lib/api";
import { AnalysisResult } from "@/types";

export function GradcamRuntime({ predictionId, imageIdFromQuery, storageKey, initialLabelFromQuery }: { predictionId: string | null; imageIdFromQuery: string | null; storageKey: string | null; initialLabelFromQuery: string | null }) {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!predictionId) {
      setIsLoading(false);
      setErrorMessage("缺少 predictionId，无法读取真实 Grad-CAM 标签上下文。请从结果页进入。");
      return;
    }

    const resolvedPredictionId = predictionId;

    let cancelled = false;

    async function loadResult() {
      try {
        const response = await frontendApi.fetchAnalysisResult(resolvedPredictionId);
        if (!cancelled) {
          setResult(response);
        }
      } catch (error) {
        if (!cancelled) {
          setErrorMessage(getApiErrorMessage(error, "无法加载对应预测结果，Grad-CAM 页面无法初始化。"));
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    loadResult();

    return () => {
      cancelled = true;
    };
  }, [predictionId]);

  const labels = useMemo(() => {
    if (!result) {
      return [];
    }
    return [...result.ai_assisted_findings]
      .sort((left, right) => right.risk_probability - left.risk_probability)
      .map((item) => item.label);
  }, [result]);

  const effectiveImageId = result?.image_id ?? imageIdFromQuery;
  const initialLabel = labels.includes(initialLabelFromQuery ?? "") ? (initialLabelFromQuery as string) : labels[0];
  const originalImageUrl = storageKey ? buildRawImageUrl(storageKey) : null;

  if (!predictionId || !storageKey || !imageIdFromQuery) {
    return (
      <div className="container-page space-y-8 pb-14">
        <PageHeader
          eyebrow="Grad-CAM 页面"
          title="无法初始化 Grad-CAM 页面"
          description="当前页面需要来自真实结果页的 predictionId、imageId 和 storageKey。"
        />
        <StatePanel tone="error" title="参数缺失" description="请从真实结果页进入 Grad-CAM 页面。" actionLabel="返回上传页" actionHref="/upload" />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="container-page space-y-8 pb-14">
        <PageHeader
          eyebrow="Grad-CAM 页面"
          title="正在加载真实热力图上下文"
          description="页面正在读取多标签结果，并准备对应标签的真实 Grad-CAM 请求。"
        />
        <div className="card-medical p-8 text-sm leading-7 text-textMuted">正在获取预测结果与标签列表，请稍候...</div>
      </div>
    );
  }

  if (!result || !effectiveImageId || !originalImageUrl || !initialLabel || errorMessage) {
    return (
      <div className="container-page space-y-8 pb-14">
        <PageHeader
          eyebrow="Grad-CAM 页面"
          title="热力图不可用"
          description="当前无法从后端获取支撑 Grad-CAM 的真实预测上下文。"
        />
        <StatePanel tone="error" title="Grad-CAM 初始化失败" description={errorMessage ?? "未能获取预测结果或图像地址。"} actionLabel="返回上传页" actionHref="/upload" />
      </div>
    );
  }

  return (
    <div className="container-page space-y-8 pb-14">
      <PageHeader
        eyebrow="Grad-CAM 页面"
        title="可解释热力图查看"
        description="模型在生成该风险提示时重点关注了以下区域。热力图仅用于辅助理解，不代表医学诊断依据。最终判断应由专业医生结合临床信息完成。"
      />

      <section className="card-medical p-6 sm:p-8">
        <GradCamViewer imageId={effectiveImageId} originalImageUrl={originalImageUrl} labels={labels} initialLabel={initialLabel} />
      </section>
    </div>
  );
}