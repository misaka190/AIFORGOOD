from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


DISCLAIMER_TEXT = (
    "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
)


class RoleOut(BaseModel):
    id: UUID
    role_code: str
    role_name: str

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role_code: str = "clinician"


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    status: str
    role: RoleOut

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    disclaimer: str = DISCLAIMER_TEXT


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ConsentCreate(BaseModel):
    consent_version: str = "v1.0"
    consent_text_snapshot: str = DISCLAIMER_TEXT


class UploadResponse(BaseModel):
    image_id: UUID
    storage_key: str
    quality_check: dict
    disclaimer: str = DISCLAIMER_TEXT


class AnalyzeRequest(BaseModel):
    priority: str = "normal"
    requested_heatmaps: list[str] = Field(default_factory=list)


class AnalyzeResponse(BaseModel):
    job_id: UUID
    image_id: UUID
    status: str
    disclaimer: str = DISCLAIMER_TEXT


class LabelProbabilityOut(BaseModel):
    label: str
    risk_probability: float
    threshold: float
    risk_flag: bool


class RiskAssessmentOut(BaseModel):
    overall_risk_level: str
    confidence_score: float | None
    uncertainty_flag: bool
    doctor_review_required: bool


class PredictionResultOut(BaseModel):
    prediction_id: UUID
    image_id: UUID
    model_version: str
    result_type: str = "AI-assisted risk assessment"
    risk_assessment: RiskAssessmentOut
    triage_result: dict
    ai_assisted_findings: list[LabelProbabilityOut]
    doctor_review_suggestion: str
    disclaimer: str = DISCLAIMER_TEXT


class HistoryItemOut(BaseModel):
    prediction_id: UUID
    image_id: UUID
    uploaded_at: datetime
    overall_risk_level: str
    doctor_review_required: bool
    uncertainty_flag: bool
    model_version: str


class HistoryResponse(BaseModel):
    items: list[HistoryItemOut]
    total: int
    disclaimer: str = DISCLAIMER_TEXT


class HeatmapResponse(BaseModel):
    image_id: UUID
    label: str
    heatmap_url: str
    overlay_url: str
    notice: str = "热力图仅用于辅助理解，不代表医学诊断依据。"
    disclaimer: str = DISCLAIMER_TEXT


class GradCAMRequest(BaseModel):
    image_id: UUID
    target_label: str


class GradCAMGenerateResponse(BaseModel):
    image_id: UUID
    target_label: str
    heatmap_url: str
    overlay_url: str
    notice: str = "模型在生成该风险提示时重点关注了以下区域。热力图仅用于辅助理解，不代表医学诊断依据。最终判断应由专业医生结合临床信息完成。"
    disclaimer: str = DISCLAIMER_TEXT


class ReviewCreate(BaseModel):
    prediction_id: UUID
    review_priority: str
    review_status: str
    review_action: str
    review_note: str | None = None


class ReviewResponse(BaseModel):
    review_id: UUID
    prediction_id: UUID
    saved: bool
    disclaimer: str = DISCLAIMER_TEXT


class ReviewDetailResponse(BaseModel):
    review_id: UUID
    prediction_id: UUID
    reviewer_id: UUID
    review_priority: str
    review_status: str
    review_action: str
    review_note: str | None = None
    reviewed_at: datetime | None = None
    disclaimer: str = DISCLAIMER_TEXT


class DeleteImageRequest(BaseModel):
    delete_mode: str = Field(default="soft")
    reason: str | None = Field(default=None, max_length=1000)


class DeleteImageResponse(BaseModel):
    image_id: UUID
    request_status: str
    delete_mode: str
    deleted_by: UUID
    completed_at: datetime
    reason: str | None = None
    disclaimer: str = DISCLAIMER_TEXT


class DeletionRequestCreate(BaseModel):
    image_id: UUID
    delete_mode: str = Field(default="soft")
    reason: str | None = Field(default=None, max_length=1000)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "image_id": "11111111-1111-1111-1111-111111111111",
                "delete_mode": "soft",
                "reason": "影像上传错误，请求撤回并重新上传。",
            }
        }
    )


class DeletionDecisionRequest(BaseModel):
    approval_action: str = Field(description="approve or reject")
    approval_note: str | None = Field(default=None, max_length=1000)
    rejection_reason: str | None = Field(default=None, max_length=1000)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "approval_action": "approve",
                    "approval_note": "已核对病例状态，允许执行软删除。",
                    "rejection_reason": None,
                },
                {
                    "approval_action": "reject",
                    "approval_note": "建议保留影像用于审计追踪。",
                    "rejection_reason": "该影像已进入医生复核流程，当前不允许删除。",
                },
            ]
        }
    )


class DeletionRequestOut(BaseModel):
    request_id: UUID
    image_id: UUID
    delete_mode: str
    deletion_reason: str | None
    request_status: str
    requested_by: UUID
    approved_by: UUID | None
    approval_note: str | None
    rejection_reason: str | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    disclaimer: str = DISCLAIMER_TEXT


class DeletionRequestListResponse(BaseModel):
    items: list[DeletionRequestOut]
    total: int
    disclaimer: str = DISCLAIMER_TEXT


class ModelVersionResponse(BaseModel):
    active_model_version: str
    framework: str
    deployed_at: datetime | None
    disclaimer: str = DISCLAIMER_TEXT


class ModelMetricsResponse(BaseModel):
    model_version: str
    model_family: str
    metrics: dict
    deployed_at: datetime | None
    disclaimer: str = DISCLAIMER_TEXT


class AuditLogOut(BaseModel):
    id: UUID
    actor_user_id: UUID | None
    action_type: str
    resource_type: str
    resource_id: UUID | None
    request_id: str | None
    ip_hash: str | None
    user_agent: str | None
    event_payload: dict | None
    created_at: datetime
    updated_at: datetime
    disclaimer: str = DISCLAIMER_TEXT

    model_config = ConfigDict(from_attributes=True)


class AuditLogListResponse(BaseModel):
    items: list[AuditLogOut]
    total: int
    disclaimer: str = DISCLAIMER_TEXT


class HealthResponse(BaseModel):
    status: str
    db: str
    redis: str
    model_service: str
    disclaimer: str = DISCLAIMER_TEXT