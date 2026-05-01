export type RiskLevel = "low" | "medium" | "high" | "priority-review";

export type LabelProbability = {
  label: string;
  risk_probability: number;
  threshold: number;
  risk_flag: boolean;
};

export type RiskAssessment = {
  overall_risk_level: RiskLevel;
  confidence_score: number;
  uncertainty_flag: boolean;
  doctor_review_required: boolean;
};

export type AnalysisResult = {
  prediction_id: string;
  image_id: string;
  image_url?: string;
  overlay_url?: string;
  model_version: string;
  result_type: "AI-assisted risk assessment";
  risk_assessment: RiskAssessment;
  triage_result: {
    queue_priority: string;
    review_reason: string;
  };
  ai_assisted_findings: LabelProbability[];
  doctor_review_suggestion: string;
  disclaimer: string;
};

export type UploadResponse = {
  image_id: string;
  storage_key: string;
  quality_check: {
    too_small: boolean;
    orientation_warning: boolean;
    requires_review: boolean;
  };
  disclaimer: string;
};

export type AnalyzeResponse = {
  job_id: string;
  image_id: string;
  status: string;
  disclaimer: string;
};

export type ReviewAction = "agree" | "adjust" | "follow-up" | "uncertain";

export type HistoryItem = {
  id: string;
  uploaded_at: string;
  overall_risk_level: RiskLevel;
  doctor_reviewed: boolean;
  uncertainty_flag: boolean;
  image_name: string;
};

export type GradCAMResponse = {
  image_id: string;
  target_label: string;
  heatmap_url: string;
  overlay_url: string;
  notice: string;
  disclaimer: string;
};
