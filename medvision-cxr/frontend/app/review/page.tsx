import { ReviewForm } from "@/components/review/review-form";
import { DisclaimerPanel } from "@/components/ui/disclaimer-panel";
import { PageHeader } from "@/components/ui/page-header";
import { RiskLevelPill } from "@/components/ui/risk-level-pill";
import { mockResult } from "@/lib/mock-data";

export default function ReviewPage() {
  return (
    <div className="container-page space-y-8 pb-14">
      <PageHeader
        eyebrow="医生复核页面"
        title="医生复核与人工备注"
        description="医生可以查看原图、AI 辅助结果与 Grad-CAM 热力图，并选择同意当前风险等级、调整风险等级、建议进一步检查或标记为不确定。"
      />

      <section className="grid gap-6 lg:grid-cols-[0.95fr_1.05fr]">
        <div className="space-y-6">
          <div className="card-medical p-4">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={mockResult.image_url} alt="医生复核原图" className="h-[360px] w-full rounded-2xl object-cover" />
            <div className="mt-4 grid gap-3 sm:grid-cols-2">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={mockResult.overlay_url} alt="热力图" className="h-[150px] w-full rounded-2xl object-cover" />
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={mockResult.overlay_url} alt="叠加图" className="h-[150px] w-full rounded-2xl object-cover" />
            </div>
          </div>

          <div className="card-medical p-6">
            <div className="flex flex-wrap items-center gap-3">
              <RiskLevelPill level={mockResult.risk_assessment.overall_risk_level} />
              {mockResult.risk_assessment.uncertainty_flag ? <span className="chip border-danger/20 bg-danger/10 text-danger">存在不确定性</span> : null}
            </div>
            <div className="mt-4 space-y-3 text-sm leading-6 text-textMuted">
              {mockResult.ai_assisted_findings.slice(0, 3).map((item) => (
                <div key={item.label} className="flex items-center justify-between rounded-2xl border border-border bg-surface px-4 py-3">
                  <span className="font-medium text-text">{item.label}</span>
                  <span>{Math.round(item.risk_probability * 100)}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="card-medical p-6 sm:p-8">
            <div className="mb-4 text-xl font-semibold text-text">复核决策</div>
            <ReviewForm />
          </div>
          <DisclaimerPanel text="AI 输出仅用于辅助理解和复核排序。医生复核记录应保留人工判断依据，并避免将模型结果视为自动结论。" />
        </div>
      </section>
    </div>
  );
}
