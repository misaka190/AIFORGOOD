import { AnalysisResult, HistoryItem } from "@/types";

export const disclaimer =
  "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。";

export const mockResult: AnalysisResult = {
  prediction_id: "pred-demo-001",
  image_id: "cxr-demo-001",
  image_url: "https://images.unsplash.com/photo-1583912267550-d4bcdd4fa3e8?auto=format&fit=crop&w=1200&q=80",
  overlay_url: "https://images.unsplash.com/photo-1583912267550-d4bcdd4fa3e8?auto=format&fit=crop&w=1200&q=80",
  model_version: "cxr-densenet121-v1.3.0",
  result_type: "AI-assisted risk assessment",
  risk_assessment: {
    overall_risk_level: "high",
    confidence_score: 0.84,
    uncertainty_flag: true,
    doctor_review_required: true
  },
  triage_result: {
    queue_priority: "urgent",
    review_reason: "high-risk-or-uncertain"
  },
  ai_assisted_findings: [
    { label: "Pleural Effusion", risk_probability: 0.82, threshold: 0.48, risk_flag: true },
    { label: "Lung Opacity", risk_probability: 0.76, threshold: 0.45, risk_flag: true },
    { label: "Pneumonia", risk_probability: 0.58, threshold: 0.43, risk_flag: true },
    { label: "Cardiomegaly", risk_probability: 0.37, threshold: 0.5, risk_flag: false },
    { label: "No Finding", risk_probability: 0.09, threshold: 0.55, risk_flag: false }
  ],
  doctor_review_suggestion:
    "当前结果包含高风险提示且存在不确定性，建议由医生优先复核影像表现，并结合临床信息进一步判断。",
  disclaimer
};

export const mockHistory: HistoryItem[] = [
  {
    id: "rec-001",
    uploaded_at: "2026-04-30 09:12",
    overall_risk_level: "priority-review",
    doctor_reviewed: true,
    uncertainty_flag: false,
    image_name: "anon_5f0b6f.png"
  },
  {
    id: "rec-002",
    uploaded_at: "2026-04-29 18:06",
    overall_risk_level: "medium",
    doctor_reviewed: false,
    uncertainty_flag: true,
    image_name: "anon_4c2aa1.jpg"
  },
  {
    id: "rec-003",
    uploaded_at: "2026-04-28 14:31",
    overall_risk_level: "low",
    doctor_reviewed: true,
    uncertainty_flag: false,
    image_name: "anon_21dd8c.jpeg"
  }
];

export const mockGradcam = {
  image_id: mockResult.image_id,
  target_label: "Pleural Effusion",
  heatmap_url: mockResult.image_url,
  overlay_url: mockResult.overlay_url,
  notice: "模型在生成该风险提示时重点关注了以下区域。热力图仅用于辅助理解，不代表医学诊断依据。最终判断应由专业医生结合临床信息完成。",
  disclaimer
};
