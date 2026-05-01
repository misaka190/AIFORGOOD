import Link from "next/link";
import { ArrowRight, Eye, Shield, Stethoscope, Target, Upload } from "lucide-react";

import { Button } from "@/components/ui/button";
import { disclaimer } from "@/lib/mock-data";

const features = [
  {
    title: "多标签风险提示",
    text: "对胸片异常风险进行多标签概率输出，支持辅助筛查、辅助分诊和医生复核排序。",
    icon: Target
  },
  {
    title: "Grad-CAM 可解释性",
    text: "展示模型在生成风险提示时重点关注的区域，帮助医生快速理解模型关注点。",
    icon: Eye
  },
  {
    title: "隐私与审计保护",
    text: "默认匿名化、最小化数据处理、删除机制和审计留痕，适配 Responsible AI 医疗场景。",
    icon: Shield
  }
];

export default function HomePage() {
  return (
    <div className="container-page space-y-8 pb-14 pt-8 sm:space-y-10 lg:pt-12">
      <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div className="card-medical relative overflow-hidden p-8 sm:p-10">
          <div className="absolute right-0 top-0 h-36 w-36 rounded-full bg-accent/15 blur-3xl" />
          <div className="chip mb-5">AI for Good · SDG 3 健康与福祉</div>
          <h1 className="headline max-w-3xl">
            MedVision-CXR：面向基层医疗的可解释胸部 X 光辅助分诊系统
          </h1>
          <p className="subheadline mt-5 max-w-2xl">
            上传胸部 X 光图像后，系统返回 AI 辅助风险提示、多标签概率、总体分诊等级、模型置信度、不确定性提示、Grad-CAM 热力图和医生复核建议。
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link href="/upload">
              <Button className="w-full gap-2 sm:w-auto">
                <Upload className="h-4 w-4" />
                上传胸片进行辅助分析
              </Button>
            </Link>
            <Link href="/privacy">
              <Button variant="secondary" className="w-full gap-2 sm:w-auto">
                查看隐私与伦理说明
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
          <div className="mt-8 grid gap-4 sm:grid-cols-3">
            <div className="rounded-2xl border border-border bg-surfaceMuted p-4">
              <div className="text-sm font-semibold text-text">基层友好</div>
              <div className="mt-2 text-sm text-textMuted">适配社区诊所、基层医院、移动筛查和低资源部署场景。</div>
            </div>
            <div className="rounded-2xl border border-border bg-surfaceMuted p-4">
              <div className="text-sm font-semibold text-text">人机协同</div>
              <div className="mt-2 text-sm text-textMuted">高风险与高不确定性结果建议优先进入医生复核流程。</div>
            </div>
            <div className="rounded-2xl border border-border bg-surfaceMuted p-4">
              <div className="text-sm font-semibold text-text">可解释输出</div>
              <div className="mt-2 text-sm text-textMuted">使用医疗审慎文案，避免确定性表述和误导性结论。</div>
            </div>
          </div>
        </div>

        <aside className="card-medical flex flex-col justify-between p-6 sm:p-8">
          <div>
            <div className="chip mb-4">项目定位</div>
            <div className="text-xl font-semibold text-text">辅助筛查、辅助分诊、医生复核优先级排序</div>
            <div className="mt-4 space-y-3 text-sm leading-6 text-textMuted">
              <p>本系统不用于自动诊断，不替代医生，不提供治疗建议。</p>
              <p>适合在胸片量大、医生资源有限的场景中帮助快速排序需优先复核的病例。</p>
            </div>
          </div>
          <div className="mt-8 rounded-2xl bg-primary p-5 text-primaryInk">
            <div className="flex items-center gap-3 text-sm font-semibold">
              <Stethoscope className="h-4 w-4" />
              医疗安全提醒
            </div>
            <p className="mt-3 text-sm leading-6 text-primaryInk/85">{disclaimer}</p>
          </div>
        </aside>
      </section>

      <section className="grid gap-5 lg:grid-cols-3">
        {features.map(({ title, text, icon: Icon }) => (
          <article key={title} className="card-medical p-6">
            <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-accentSoft text-primary">
              <Icon className="h-5 w-5" />
            </div>
            <h2 className="text-xl font-semibold text-text">{title}</h2>
            <p className="mt-3 text-sm leading-6 text-textMuted">{text}</p>
          </article>
        ))}
      </section>

      <section className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr]">
        <div className="card-medical p-6">
          <div className="chip mb-4">医疗免责声明</div>
          <p className="text-sm leading-7 text-textMuted">{disclaimer}</p>
        </div>
        <div className="card-medical p-6">
          <div className="chip mb-4">隐私保护说明</div>
          <ul className="space-y-3 text-sm leading-6 text-textMuted">
            <li>默认采用匿名化文件名和最小化数据处理策略。</li>
            <li>上传前需确认知情同意，避免提交含明显身份信息的截图或屏摄图。</li>
            <li>支持数据删除请求与访问留痕，帮助满足 Responsible AI 与合规要求。</li>
          </ul>
        </div>
      </section>
    </div>
  );
}