import { PageHeader } from "@/components/ui/page-header";

const sections = [
  {
    title: "知情同意与使用边界",
    body: "上传前，用户应确认自己理解 AI 分析结果不是诊断，只用于辅助分诊、辅助筛查和医生复核支持。任何临床决策都必须由具备资质的医生结合临床信息完成。"
  },
  {
    title: "数据如何被处理",
    body: "上传文件会经过格式校验、匿名化命名、必要的图像预处理、AI 辅助风险分析和合规审计留痕。平台只处理完成本次分析和安全治理所必需的最小数据。"
  },
  {
    title: "默认匿名化与最小化",
    body: "系统默认使用 UUID 或匿名化文件名，不要求录入真实姓名、身份证号、手机号等直接身份信息。对常见图像文件会移除 EXIF，对 DICOM 文件执行必要的去标识化处理。"
  },
  {
    title: "默认不长期保存原图",
    body: "除满足分析、合规和必要审计要求外，平台不建议长期保留原始图像。系统设计优先支持最小保留、短期缓存和可治理的删除机制。"
  },
  {
    title: "访问控制与安全保护",
    body: "平台采用 HTTPS、JWT、RBAC、审计日志、受控删除机制和存储保护策略，降低未授权访问、数据泄露和错误使用风险。"
  },
  {
    title: "可请求删除",
    body: "用户可以根据平台规则发起删除请求。系统支持软删除和经审批后的硬删除，并对删除理由、审批记录和完成时间保留合规留痕。"
  },
  {
    title: "模型局限性与偏差风险",
    body: "AI 模型可能因图像质量、设备差异、医院来源差异、样本偏差和外部泛化不足而产生误差或偏差。高风险或不确定结果必须由专业医生复核。"
  }
];

export default function PrivacyPage() {
  return (
    <div className="container-page space-y-8 pb-14">
      <PageHeader
        eyebrow="隐私与伦理页面"
        title="隐私政策与数据保护说明"
        description="本页面说明平台如何处理上传图像、如何进行匿名化与最小化、如何保护访问安全，以及用户如何请求删除相关数据。"
      />
      <section className="grid gap-5 lg:grid-cols-2">
        {sections.map((section) => (
          <article key={section.title} className="card-medical p-6">
            <h2 className="text-xl font-semibold text-text">{section.title}</h2>
            <p className="mt-3 text-sm leading-7 text-textMuted">{section.body}</p>
          </article>
        ))}
      </section>
      <section className="card-medical p-6">
        <h2 className="text-xl font-semibold text-text">上传前知情同意</h2>
        <div className="mt-4 space-y-3 text-sm leading-7 text-textMuted">
          <p>1. 我理解 AI 分析结果不是医学诊断。</p>
          <p>2. 我理解系统仅用于辅助分诊和医生复核。</p>
          <p>3. 我理解系统可能出现错误或偏差。</p>
          <p>4. 我理解高风险或不确定结果应咨询医生。</p>
          <p>5. 我同意系统处理我上传的图像用于本次分析。</p>
          <p>6. 我知道可以请求删除相关数据。</p>
        </div>
      </section>
    </div>
  );
}
