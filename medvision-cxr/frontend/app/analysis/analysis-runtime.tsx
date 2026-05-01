"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, Cpu, FileCheck2, Flame, Sparkles } from "lucide-react";

import { DisclaimerPanel } from "@/components/ui/disclaimer-panel";
import { PageHeader } from "@/components/ui/page-header";
import { StatePanel } from "@/components/ui/state-panel";
import { frontendApi, getApiErrorMessage } from "@/lib/api";

const DISCLAIMER_TEXT = "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。";

export function AnalysisRuntime({ imageId, storageKey }: { imageId: string | null; storageKey: string | null }) {
  const router = useRouter();
  const [phase, setPhase] = useState<"running" | "done" | "error">("running");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const steps = useMemo(() => {
    const statuses = phase === "done"
      ? ["done", "done", "done", "done", "done"]
      : ["done", "done", "active", "pending", "pending"];

    return [
      { title: "图像校验", detail: "检查文件格式、大小与基础质量", icon: FileCheck2, status: statuses[0] },
      { title: "图像预处理", detail: "标准化尺寸、归一化与质量标记", icon: Sparkles, status: statuses[1] },
      { title: "AI 辅助分析", detail: "执行多标签风险提示与置信度计算", icon: Cpu, status: statuses[2] },
      { title: "生成热力图", detail: "生成 Grad-CAM 可解释热力图", icon: Flame, status: statuses[3] },
      { title: "生成结果", detail: "汇总辅助分析结果与复核建议", icon: CheckCircle2, status: statuses[4] }
    ];
  }, [phase]);

  useEffect(() => {
    if (!imageId || !storageKey) {
      setPhase("error");
      setErrorMessage("缺少分析所需的图像参数，请从上传页重新发起任务。");
      return;
    }

    const resolvedImageId = imageId;
    const resolvedStorageKey = storageKey;

    let cancelled = false;

    async function runAnalysis() {
      try {
        const analysis = await frontendApi.analyzeCxr(resolvedImageId);
        if (cancelled) {
          return;
        }
        setPhase("done");
        router.replace(
          `/results?predictionId=${encodeURIComponent(analysis.job_id)}&imageId=${encodeURIComponent(analysis.image_id)}&storageKey=${encodeURIComponent(resolvedStorageKey)}`
        );
      } catch (error) {
        if (cancelled) {
          return;
        }
        setPhase("error");
        setErrorMessage(getApiErrorMessage(error, "分析任务启动失败，请确认后端推理服务可用。"));
      }
    }

    runAnalysis();

    return () => {
      cancelled = true;
    };
  }, [imageId, router, storageKey]);

  if (phase === "error") {
    return (
      <div className="container-page space-y-8 pb-14">
        <PageHeader
          eyebrow="分析中页面"
          title="分析任务未能完成"
          description="当前页面期望承接上传后的真实分析任务。如果参数缺失或后端不可用，会在这里显示错误。"
        />
        <StatePanel tone="error" title="无法继续分析" description={errorMessage ?? "分析任务启动失败。"} actionLabel="返回上传页" actionHref="/upload" />
      </div>
    );
  }

  return (
    <div className="container-page space-y-8 pb-14">
      <PageHeader
        eyebrow="分析中页面"
        title="AI 正在生成辅助分析结果"
        description="当前任务会依次完成图像校验、图像预处理、AI 辅助分析、热力图生成和结果汇总。请勿将中间状态视为最终意见。"
      />

      <section className="grid gap-6 lg:grid-cols-[1.15fr_0.85fr]">
        <div className="card-medical p-6 sm:p-8">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <div className="text-sm font-semibold text-text">当前进度</div>
              <div className="mt-1 text-sm text-textMuted">当前正在调用真实后端完成推理并生成结果，预计用时 10 至 30 秒。</div>
            </div>
            <div className="text-2xl font-semibold text-primary">62%</div>
          </div>
          <div className="h-3 rounded-full bg-surfaceMuted">
            <div className="h-3 w-[62%] rounded-full bg-primary" />
          </div>

          <div className="mt-8 space-y-4">
            {steps.map(({ title, detail, icon: Icon, status }) => (
              <div key={title} className={`rounded-2xl border p-4 ${status === "active" ? "border-primary bg-primary/5" : "border-border bg-surface"}`}>
                <div className="flex items-start gap-4">
                  <div className={`mt-1 flex h-10 w-10 items-center justify-center rounded-2xl ${status === "done" ? "bg-success/10 text-success" : status === "active" ? "bg-primary text-primaryInk" : "bg-surfaceMuted text-textMuted"}`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <div>
                    <div className="font-semibold text-text">{title}</div>
                    <div className="mt-1 text-sm leading-6 text-textMuted">{detail}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <DisclaimerPanel title="安全提示" text="AI 结果仅供医生复核参考。高风险提示或不确定性较高的结果不应被视为自动结论，仍需结合人工判断。" />
          <div className="card-medical p-6">
            <div className="chip mb-4">当前状态</div>
            <div className="text-lg font-semibold text-text">AI 辅助分析进行中</div>
            <div className="mt-3 text-sm leading-6 text-textMuted">系统正在计算多标签风险概率、总体分诊等级、置信度与不确定性，并准备可解释热力图输出。</div>
          </div>
          <DisclaimerPanel text={DISCLAIMER_TEXT} />
        </div>
      </section>
    </div>
  );
}