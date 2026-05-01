"use client";

import { Controller, useForm } from "react-hook-form";

import { Button } from "@/components/ui/button";
import { ReviewAction } from "@/types";

type ReviewFormValues = {
  action: ReviewAction;
  note: string;
};

const options: { value: ReviewAction; label: string; description: string }[] = [
  { value: "agree", label: "同意 AI 风险等级", description: "保留当前辅助分诊等级，进入常规复核流程。" },
  { value: "adjust", label: "调整风险等级", description: "根据影像与临床背景重新调整分诊优先级。" },
  { value: "follow-up", label: "需要进一步检查", description: "建议结合更多检查或临床信息继续评估。" },
  { value: "uncertain", label: "标记为不确定", description: "当前影像或 AI 结果不适合直接用于排序结论。" }
];

export function ReviewForm() {
  const { control, handleSubmit, formState: { isSubmitting } } = useForm<ReviewFormValues>({
    defaultValues: {
      action: "agree",
      note: ""
    }
  });

  const onSubmit = async () => {
    await new Promise((resolve) => setTimeout(resolve, 1000));
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      <Controller
        name="action"
        control={control}
        render={({ field }) => (
          <div className="space-y-3">
            {options.map((option) => (
              <label key={option.value} className={`block rounded-2xl border p-4 transition ${field.value === option.value ? "border-primary bg-primary/5" : "border-border bg-surface"}`}>
                <div className="flex items-start gap-3">
                  <input
                    type="radio"
                    className="mt-1 h-4 w-4 accent-primary"
                    checked={field.value === option.value}
                    onChange={() => field.onChange(option.value)}
                  />
                  <div>
                    <div className="font-semibold text-text">{option.label}</div>
                    <div className="mt-1 text-sm leading-6 text-textMuted">{option.description}</div>
                  </div>
                </div>
              </label>
            ))}
          </div>
        )}
      />

      <Controller
        name="note"
        control={control}
        rules={{ required: "请填写复核备注。" }}
        render={({ field, fieldState }) => (
          <div>
            <label className="mb-2 block text-sm font-semibold text-text">医生备注</label>
            <textarea
              {...field}
              rows={5}
              placeholder="请记录复核意见、风险分层调整原因或需要进一步检查的说明。"
              className="w-full rounded-2xl border border-border bg-surface px-4 py-3 text-sm text-text outline-none transition focus:border-primary"
            />
            {fieldState.error ? <p className="mt-2 text-sm text-danger">{fieldState.error.message}</p> : null}
          </div>
        )}
      />

      <Button type="submit" className="w-full">{isSubmitting ? "正在保存复核记录" : "保存复核记录"}</Button>
    </form>
  );
}
