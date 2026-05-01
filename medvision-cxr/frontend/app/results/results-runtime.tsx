"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, ArrowRight, BrainCircuit, ShieldAlert } from "lucide-react";

import { ProbabilityChart } from "@/components/results/probability-chart";
import { DisclaimerPanel } from "@/components/ui/disclaimer-panel";
import { PageHeader } from "@/components/ui/page-header";
import { RiskLevelPill } from "@/components/ui/risk-level-pill";
import { StatePanel } from "@/components/ui/state-panel";
import { buildRawImageUrl, frontendApi, getApiErrorMessage } from "@/lib/api";
import { AnalysisResult, GradCAMResponse, LabelProbability } from "@/types";

export function ResultsRuntime({ predictionId, imageIdFromQuery, storageKey }: { predictionId: string | null; imageIdFromQuery: string | null; storageKey: string | null }) {
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [gradcam, setGradcam] = useState<GradCAMResponse | null>(null);
  const [resultError, setResultError] = useState<string | null>(null);
  const [gradcamError, setGradcamError] = useState<string | null>(null);
  const [isLoadingResult, setIsLoadingResult] = useState(true);
  const [isLoadingGradcam, setIsLoadingGradcam] = useState(false);

  const sortedFindings = useMemo<LabelProbability[]>(() => {
    if (!result) {
      return [];
    }
    return [...result.ai_assisted_findings].sort((left, right) => right.risk_probability - left.risk_probability);
  }, [result]);

  const primaryLabel = sortedFindings[0]?.label ?? null;
  const effectiveImageId = result?.image_id ?? imageIdFromQuery;
  const originalImageUrl = storageKey ? buildRawImageUrl(storageKey) : null;

  useEffect(() => {
    if (!predictionId) {
      setIsLoadingResult(false);
      setResultError("缺少 predictionId，无法加载真实分析结果。请从上传页重新提交图像。");
      return;
    }

    const resolvedPredictionId = predictionId;

    let cancelled = false;

    async function loadResult() {
      try {
        setIsLoadingResult(true);
        setResultError(null);
        const response = await frontendApi.fetchAnalysisResult(resolvedPredictionId);
        if (!cancelled) {
          setResult(response);
        }
      } catch (error) {
        if (!cancelled) {
          setResultError(getApiErrorMessage(error, "无法加载分析结果，请确认后端服务可用。"));
        }
      } finally {
        if (!cancelled) {
          setIsLoadingResult(false);
        }
      }
    }

    loadResult();

    return () => {
      cancelled = true;
    };
  }, [predictionId]);

  useEffect(() => {
    if (!effectiveImageId || !primaryLabel) {
      return;
    }

    const resolvedImageId = effectiveImageId;
    const resolvedPrimaryLabel = primaryLabel;

    let cancelled = false;

    async function loadGradcam() {
      try {
        setIsLoadingGradcam(true);
        setGradcamError(null);

        try {
          const cached = await frontendApi.fetchHeatmap(resolvedImageId, resolvedPrimaryLabel);
          if (!cancelled) {
            setGradcam(cached);
          }
          return;
        } catch {
        }

        const generated = await frontendApi.generateGradcam(resolvedImageId, resolvedPrimaryLabel);
        if (!cancelled) {
          setGradcam(generated);
        }
      } catch (error) {
        if (!cancelled) {
          setGradcamError(getApiErrorMessage(error, "无法加载对应标签的 Grad-CAM 结果。"));
        }
      } finally {
        if (!cancelled) {
          setIsLoadingGradcam(false);
        }
      }
    }

    loadGradcam();

    return () => {
      cancelled = true;
    };
  }, [effectiveImageId, primaryLabel]);

  if (!predictionId || !storageKey) {
    return (
      <div className="container-page space-y-8 pb-14">
        <PageHeader
          eyebrow="结果页面"
          title="无法加载结果页"
          description="当前页面需要真实分析任务返回的 predictionId 和 storageKey 才能展示结果。"
        />
        <StatePanel tone="error" title="结果参数缺失" description="请从上传页重新发起真实分析任务。" actionLabel="返回上传页" actionHref="/upload" />
      </div>
    );
  }

  if (isLoadingResult) {
    return (
      <div className="container-page space-y-8 pb-14">
        <PageHeader
          eyebrow="结果页面"
          title="正在加载真实分析结果"
          description="页面正在向后端读取多标签风险结果、分诊等级和热力图信息。"
        />
        <div className="card-medical p-8 text-sm leading-7 text-textMuted">正在获取真实预测结果，请稍候...</div>
      </div>
    );
  }

  if (!result || resultError) {
    return (
      <div className="container-page space-y-8 pb-14">
        <PageHeader
          eyebrow="结果页面"
          title="结果页加载失败"
          description="无法从后端获取该 predictionId 对应的真实分析结果。"
        />
        <StatePanel tone="error" title="结果不可用" description={resultError ?? "未找到分析结果。"} actionLabel="返回上传页" actionHref="/upload" />
      </div>
    );
  }

  const gradcamHref = effectiveImageId && primaryLabel
    ? `/gradcam?predictionId=${encodeURIComponent(result.prediction_id)}&imageId=${encodeURIComponent(effectiveImageId)}&storageKey=${encodeURIComponent(storageKey)}&label=${encodeURIComponent(primaryLabel)}`
    : "/gradcam";
  const confidenceScore = result.risk_assessment.confidence_score ?? 0;

  return (
    <div className="container-page space-y-8 pb-14">
      <PageHeader
        eyebrow="结果页面"
        title="AI 辅助分析结果"
        description="以下内容用于辅助筛查、辅助分诊和医生复核优先级排序。页面只展示风险提示、辅助分析概率和复核建议，不展示确定性诊断结论。"
        actions={
          <>
            <a href={gradcamHref} className="chip hover:border-primary hover:text-primary">查看 Grad-CAM 解释</a>
            <Link href="/review" className="chip hover:border-primary hover:text-primary">进入医生复核</Link>
          </>
        }
      />

      <section className="grid gap-6 lg:grid-cols-[0.92fr_1.08fr]">
        <div className="space-y-6">
          <div className="card-medical p-4">
            {originalImageUrl ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={originalImageUrl} alt="原始胸片" className="h-[520px] w-full rounded-2xl object-cover" />
            ) : (
              <div className="flex h-[520px] items-center justify-center rounded-2xl border border-dashed border-border bg-surfaceMuted text-sm text-textMuted">
                缺少原图地址，无法显示上传影像。
              </div>
            )}
            <div className="mt-4 flex items-center justify-between rounded-2xl bg-surfaceMuted px-4 py-3 text-sm text-textMuted">
              <span>原始胸片</span>
              <span>影像 ID: {result.image_id}</span>
            </div>
          </div>
          <div className="card-medical p-4">
            {gradcam?.overlay_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={gradcam.overlay_url} alt="Grad-CAM overlay" className="h-[280px] w-full rounded-2xl object-cover" />
            ) : (
              <div className="flex h-[280px] items-center justify-center rounded-2xl border border-dashed border-border bg-surfaceMuted text-sm text-textMuted">
                {isLoadingGradcam ? "正在加载真实 Grad-CAM 叠加图..." : "当前尚未取得可用的 Grad-CAM 叠加图。"}
              </div>
            )}
            <div className="mt-4 flex items-start gap-3 rounded-2xl border border-info/20 bg-info/10 p-4 text-sm leading-6 text-textMuted">
              <BrainCircuit className="mt-0.5 h-5 w-5 text-info" />
              <div>
                <div>{gradcam?.target_label ? `当前展示标签：${gradcam.target_label}` : "模型在生成当前风险提示时重点关注了相关影像区域。"}</div>
                {gradcamError ? <div className="mt-1 text-danger">{gradcamError}</div> : null}
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="card-medical p-6 sm:p-8">
            <div className="flex flex-wrap items-center gap-4">
              <RiskLevelPill level={result.risk_assessment.overall_risk_level} />
              <div className="chip">模型版本：{result.model_version}</div>
              {result.risk_assessment.doctor_review_required ? <div className="chip border-danger/20 bg-danger/10 text-danger">建议医生复核</div> : null}
            </div>
            <div className="mt-6 grid gap-4 sm:grid-cols-3">
              <div className="rounded-2xl border border-border bg-surfaceMuted p-4">
                <div className="text-sm text-textMuted">模型置信度</div>
                <div className="mt-2 text-3xl font-semibold text-text">{Math.round(confidenceScore * 100)}%</div>
              </div>
              <div className="rounded-2xl border border-border bg-surfaceMuted p-4">
                <div className="text-sm text-textMuted">不确定性提示</div>
                <div className="mt-2 text-lg font-semibold text-text">{result.risk_assessment.uncertainty_flag ? "存在不确定性" : "未见明显不确定性"}</div>
              </div>
              <div className="rounded-2xl border border-border bg-surfaceMuted p-4">
                <div className="text-sm text-textMuted">结果类型</div>
                <div className="mt-2 text-lg font-semibold text-text">AI-assisted risk assessment</div>
              </div>
            </div>

            <div className="mt-6 rounded-2xl border border-accent/25 bg-accent/10 p-4">
              <div className="flex items-start gap-3">
                <ShieldAlert className="mt-0.5 h-5 w-5 text-accent" />
                <div>
                  <div className="font-semibold text-text">医生复核建议</div>
                  <p className="mt-2 text-sm leading-6 text-textMuted">{result.doctor_review_suggestion}</p>
                </div>
              </div>
            </div>
          </div>

          <div className="card-medical p-6 sm:p-8">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <div className="text-xl font-semibold text-text">多标签风险概率</div>
                <div className="mt-1 text-sm text-textMuted">数值用于辅助理解模型输出和优先复核排序，不表示确定性结论。</div>
              </div>
              <a href={gradcamHref} className="inline-flex items-center gap-2 text-sm font-semibold text-primary">
                查看标签热力图
                <ArrowRight className="h-4 w-4" />
              </a>
            </div>
            <ProbabilityChart items={sortedFindings} />
            <div className="mt-5 space-y-3">
              {sortedFindings.map((item) => (
                <div key={item.label} className="flex items-center justify-between rounded-2xl border border-border bg-surface px-4 py-3">
                  <div>
                    <div className="font-semibold text-text">{item.label}</div>
                    <div className="text-sm text-textMuted">阈值 {Math.round(item.threshold * 100)}%</div>
                  </div>
                  <div className="text-right">
                    <div className="text-lg font-semibold text-text">{Math.round(item.risk_probability * 100)}%</div>
                    <div className={`text-sm ${item.risk_flag ? "text-accent" : "text-textMuted"}`}>{item.risk_flag ? "已触发风险提示" : "未触发风险提示"}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <DisclaimerPanel text={result.disclaimer} />
          {result.risk_assessment.uncertainty_flag ? (
            <div className="rounded-2xl border border-danger/25 bg-danger/10 p-4 text-sm leading-6 text-textMuted">
              <div className="mb-2 flex items-center gap-2 font-semibold text-text">
                <AlertTriangle className="h-4 w-4 text-danger" />
                不确定性提示
              </div>
              当前结果存在不确定性，建议优先由医生复核，并结合影像质量、既往资料和临床信息综合判断。
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}