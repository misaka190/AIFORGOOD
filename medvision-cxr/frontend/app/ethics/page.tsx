import { PageHeader } from "@/components/ui/page-header";

const principles = [
  {
    title: "AI 仅作辅助分诊",
    body: "MedVision-CXR 只输出风险提示、风险分层和医生复核建议，不用于自动诊断。"
  },
  {
    title: "不替代医生",
    body: "系统不会替代具备资质的医生。任何临床判断都必须结合临床信息和专业意见。"
  },
  {
    title: "透明可解释",
    body: "系统提供模型版本、风险提示、不确定性标记与 Grad-CAM 热力图，但热力图仅用于辅助理解。"
  },
  {
    title: "公平性评估",
    body: "部署前和上线后都应评估不同性别、年龄、设备来源、医院来源、图像质量和标签上的性能差异。"
  },
  {
    title: "隐私与安全",
    body: "平台采用匿名化命名、元数据清洗、权限控制、审计日志和删除机制来降低隐私与安全风险。"
  },
  {
    title: "问责机制",
    body: "所有关键操作应保留可追踪记录，包括模型版本、上传、分析、复核、审批和删除。"
  }
];

export default function EthicsPage() {
  return (
    <div className="container-page space-y-8 pb-14">
      <PageHeader
        eyebrow="伦理说明页面"
        title="医疗伦理与 Responsible AI"
        description="本页面说明系统的能力边界、人工复核要求、公平性原则、透明解释机制以及问责与治理要求。"
      />
      <section className="grid gap-5 lg:grid-cols-2">
        {principles.map((section) => (
          <article key={section.title} className="card-medical p-6">
            <h2 className="text-xl font-semibold text-text">{section.title}</h2>
            <p className="mt-3 text-sm leading-7 text-textMuted">{section.body}</p>
          </article>
        ))}
      </section>
      <section className="card-medical p-6">
        <h2 className="text-xl font-semibold text-text">结果页免责声明</h2>
        <div className="mt-4 space-y-4 text-sm leading-7 text-textMuted">
          <p>
            本系统展示的 AI 辅助结果不是医学诊断，也不能作为临床决策的唯一依据。若涉及诊疗判断，请咨询具备资质的医疗专业人员。
          </p>
          <p>
            The AI-assisted result shown by this system is not a medical diagnosis and must not be used as the sole basis for clinical decision-making. For any clinical decision, consult a qualified healthcare professional.
          </p>
          <p>
            热力图仅用于可解释性展示，不代表病灶定位结论。系统可能因为数据分布、图像质量、设备差异和模型局限性而存在误差与偏差。
          </p>
        </div>
      </section>
    </div>
  );
}