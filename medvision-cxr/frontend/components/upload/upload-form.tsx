"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Controller, useForm } from "react-hook-form";
import { AlertTriangle, FileImage, LockKeyhole, UploadCloud } from "lucide-react";

import { Button } from "@/components/ui/button";
import { frontendApi, getApiErrorMessage } from "@/lib/api";

type UploadFormValues = {
  consentAccepted: boolean;
  confirmNoIdentityInfo: boolean;
  file: FileList | null;
};

const ACCEPTED_TYPES = ["image/png", "image/jpeg", "application/dicom"];
const MAX_MB = 15;

export function UploadForm() {
  const router = useRouter();
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [submitState, setSubmitState] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [submitMessage, setSubmitMessage] = useState<string | null>(null);
  const {
    control,
    handleSubmit,
    formState: { errors, isValid },
    watch
  } = useForm<UploadFormValues>({
    mode: "onChange",
    defaultValues: {
      consentAccepted: false,
      confirmNoIdentityInfo: false,
      file: null
    }
  });

  const currentFileList = watch("file");
  const file = currentFileList?.[0] ?? null;

  const fileHint = useMemo(() => {
    if (!file) {
      return "支持 PNG、JPG、JPEG，可选 DICOM，单文件建议不超过 15MB。";
    }
    const sizeMb = file.size / 1024 / 1024;
    return `${file.name} · ${sizeMb.toFixed(2)} MB`;
  }, [file]);

  const onSubmit = async () => {
    if (!file) {
      setSubmitState("error");
      setSubmitMessage("请先选择胸部 X 光图像。");
      return;
    }

    setSubmitState("submitting");
    setSubmitMessage("正在上传图像并创建真实分析任务...");

    try {
      const formData = new FormData();
      formData.set("file", file);

      const upload = await frontendApi.uploadCxr(formData);
      setSubmitState("success");
      setSubmitMessage("上传完成，正在进入分析流程...");
      router.push(`/analysis?imageId=${encodeURIComponent(upload.image_id)}&storageKey=${encodeURIComponent(upload.storage_key)}`);
    } catch (error) {
      setSubmitState("error");
      setSubmitMessage(getApiErrorMessage(error, "上传失败，请确认后端服务已启动并可访问。"));
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
      <section className="card-medical p-6 sm:p-8">
        <div className="chip mb-4">胸片上传</div>
        <Controller
          name="file"
          control={control}
          rules={{
            validate: (value) => {
              const current = value?.[0];
              if (!current) {
                return "请先选择胸部 X 光图像。";
              }
              if (!ACCEPTED_TYPES.includes(current.type) && !current.name.toLowerCase().endsWith(".dcm")) {
                return "仅支持 PNG、JPG、JPEG 或 DICOM 文件。";
              }
              if (current.size > MAX_MB * 1024 * 1024) {
                return `文件大小需小于 ${MAX_MB}MB。`;
              }
              return true;
            }
          }}
          render={({ field: { onChange, ref } }) => (
            <label className="flex cursor-pointer flex-col items-center justify-center rounded-[28px] border border-dashed border-border bg-surfaceMuted/70 px-6 py-14 text-center transition hover:border-primary hover:bg-surfaceMuted">
              <div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-primary text-primaryInk shadow-soft">
                <UploadCloud className="h-7 w-7" />
              </div>
              <div className="mt-5 text-lg font-semibold text-text">拖拽上传胸部 X 光图像</div>
              <div className="mt-2 max-w-md text-sm leading-6 text-textMuted">请上传胸部 X 光正位或符合项目范围的影像文件。若使用屏幕截图，请确保未包含明显身份信息。</div>
              <input
                ref={ref}
                type="file"
                accept=".png,.jpg,.jpeg,.dcm"
                className="hidden"
                onChange={(event) => {
                  const nextFile = event.target.files?.[0] ?? null;
                  onChange(event.target.files);
                  if (nextFile && nextFile.type.startsWith("image/")) {
                    setPreviewUrl(URL.createObjectURL(nextFile));
                  } else {
                    setPreviewUrl(null);
                  }
                }}
              />
              <div className="mt-4 text-sm text-textMuted">{fileHint}</div>
            </label>
          )}
        />
        {errors.file ? <p className="mt-3 text-sm text-danger">{errors.file.message}</p> : null}

        <div className="mt-6 rounded-2xl border border-border bg-surface p-4">
          <div className="flex items-start gap-3">
            <LockKeyhole className="mt-0.5 h-5 w-5 text-primary" />
            <div>
              <div className="font-semibold text-text">隐私提醒</div>
              <ul className="mt-2 space-y-2 text-sm leading-6 text-textMuted">
                <li>系统默认使用匿名化命名，不建议上传带姓名、病历号、手机号等信息的截图。</li>
                <li>上传前请确认已获得合法授权，且仅用于辅助分析与医生复核排序。</li>
                <li>DICOM 文件在进入后端后应进一步清理身份元数据。</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <aside className="space-y-6">
        <div className="card-medical p-6">
          <div className="chip mb-4">图像预览</div>
          {previewUrl ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={previewUrl} alt="胸片预览" className="h-[340px] w-full rounded-2xl object-cover" />
          ) : (
            <div className="flex h-[340px] items-center justify-center rounded-2xl border border-dashed border-border bg-surfaceMuted text-sm text-textMuted">
              选择文件后将在此处显示预览
            </div>
          )}
        </div>

        <div className="card-medical space-y-4 p-6">
          <div className="chip">上传前确认</div>
          <Controller
            name="consentAccepted"
            control={control}
            rules={{ required: "请先确认知情同意说明。" }}
            render={({ field }) => (
              <label className="flex items-start gap-3 text-sm leading-6 text-textMuted">
                <input type="checkbox" className="mt-1 h-4 w-4 accent-primary" checked={field.value} onChange={field.onChange} />
                我已阅读并同意本系统仅用于辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断。
              </label>
            )}
          />
          {errors.consentAccepted ? <p className="text-sm text-danger">{errors.consentAccepted.message}</p> : null}

          <Controller
            name="confirmNoIdentityInfo"
            control={control}
            rules={{ required: "请确认上传内容未包含明显身份信息。" }}
            render={({ field }) => (
              <label className="flex items-start gap-3 text-sm leading-6 text-textMuted">
                <input type="checkbox" className="mt-1 h-4 w-4 accent-primary" checked={field.value} onChange={field.onChange} />
                我确认该图像不包含明显身份信息截图、条码截图或患者个人资料页面。
              </label>
            )}
          />
          {errors.confirmNoIdentityInfo ? <p className="text-sm text-danger">{errors.confirmNoIdentityInfo.message}</p> : null}

          <div className="rounded-2xl border border-warning/25 bg-warning/10 p-4 text-sm leading-6 text-textMuted">
            <div className="mb-2 flex items-center gap-2 font-semibold text-text">
              <AlertTriangle className="h-4 w-4 text-warning" />
              医疗安全提示
            </div>
            AI 结果仅供医生复核参考，上传后仍需结合影像质量、临床背景和人工判断综合处理。
          </div>

          <Button type="submit" className="w-full gap-2" disabled={!isValid || submitState === "submitting"}>
            <FileImage className="h-4 w-4" />
            {submitState === "submitting"
              ? "正在上传到真实后端"
              : submitState === "success"
                ? "上传成功，正在跳转分析页"
                : "上传胸片"}
          </Button>
          {submitMessage ? <p className={`text-sm ${submitState === "error" ? "text-danger" : "text-textMuted"}`}>{submitMessage}</p> : null}
        </div>
      </aside>
    </form>
  );
}
