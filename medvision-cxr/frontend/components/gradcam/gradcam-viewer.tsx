"use client";

import { useEffect, useState, useTransition } from "react";

import { Button } from "@/components/ui/button";
import { DisclaimerPanel } from "@/components/ui/disclaimer-panel";
import { frontendApi } from "@/lib/api";
import { GradCAMResponse } from "@/types";

type GradCamViewerProps = {
  imageId: string;
  originalImageUrl: string;
  labels: string[];
  initialLabel: string;
};

export function GradCamViewer({ imageId, originalImageUrl, labels, initialLabel }: GradCamViewerProps) {
  const [selectedLabel, setSelectedLabel] = useState(initialLabel);
  const [gradcam, setGradcam] = useState<GradCAMResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    setSelectedLabel(initialLabel);
  }, [initialLabel]);

  useEffect(() => {
    startTransition(async () => {
      try {
        setErrorMessage(null);
        const response = await frontendApi.generateGradcam(imageId, selectedLabel);
        setGradcam(response);
      } catch {
        setGradcam(null);
        setErrorMessage("当前标签热力图暂时不可用，请稍后重试。");
      }
    });
  }, [imageId, selectedLabel]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-3">
        {labels.map((label) => (
          <Button key={label} variant={label === selectedLabel ? "primary" : "secondary"} onClick={() => setSelectedLabel(label)}>
            {label}
          </Button>
        ))}
      </div>

      {errorMessage ? (
        <div className="rounded-2xl border border-danger/25 bg-danger/10 p-4 text-sm leading-6 text-textMuted">{errorMessage}</div>
      ) : null}

      <div className="grid gap-6 lg:grid-cols-3">
        {[
          { title: "原图", imageUrl: originalImageUrl, caption: "用于对照查看原始胸片。" },
          { title: "热力图", imageUrl: gradcam?.heatmap_url ?? originalImageUrl, caption: "模型在生成该风险提示时重点关注了以下区域。" },
          { title: "叠加图", imageUrl: gradcam?.overlay_url ?? originalImageUrl, caption: "将热力图叠加到原图上，便于辅助理解。" }
        ].map((panel) => (
          <div key={panel.title} className="rounded-3xl border border-border bg-surface p-4">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={panel.imageUrl} alt={panel.title} className="h-[320px] w-full rounded-2xl object-cover" />
            <div className="mt-4 font-semibold text-text">{panel.title}</div>
            <p className="mt-2 text-sm leading-6 text-textMuted">{isPending && panel.title !== "原图" ? "正在生成对应标签的热力图，请稍候。" : panel.caption}</p>
          </div>
        ))}
      </div>

      <DisclaimerPanel
        title="解释说明"
        text={
          gradcam?.notice ??
          "模型在生成该风险提示时重点关注了以下区域。热力图仅用于辅助理解，不代表医学诊断依据。最终判断应由专业医生结合临床信息完成。"
        }
      />
    </div>
  );
}