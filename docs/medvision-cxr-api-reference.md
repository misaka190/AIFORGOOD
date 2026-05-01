# MedVision-CXR API Reference

## Overview

This document provides an OpenAPI-style reference for the MedVision-CXR backend APIs.

- API base URL: `/api/v1`
- Auth scheme: `Bearer <JWT access_token>` unless noted otherwise
- Response language: English field names with medically safe wording
- Clinical wording rule: the API uses `risk_assessment`, `triage_result`, `ai_assisted_findings`, `doctor_review_required`, `uncertainty_flag`, and `disclaimer`
- Prohibited wording: `diagnosis`

## Status Notes

- Implemented in current backend: `Register`, `Login`, `Upload CXR Image`, `Analyze CXR Image`, `Get Prediction Result`, `Get User History`, `Generate Grad-CAM`, `Get Grad-CAM Output`, `Submit Doctor Review`, `Get Review`, `Get Model Version`, `Get Model Metrics`, `Delete CXR Image`, `Health Check`, `List Audit Logs`, `Get Audit Log`
- Implemented governed deletion workflow: `/api/v1/deletions/requests`, `/api/v1/deletions/requests/{deletion_request_id}/decision`, `/api/v1/deletions/requests?request_status=`
- Deletion model: both direct delete and governed approval workflow are available; the approval workflow remains the safer default for production governance
- Generated spec: `docs/medvision-cxr-openapi.yaml` is now intended to be regenerated from the backend app so frontend documentation pages and backend behavior stay aligned

## Security Model

- `clinician`: upload images, request analysis, view own history, request Grad-CAM, submit deletion requests for owned images
- `doctor`: all clinician capabilities plus doctor review, deletion approval decisions, and read-only audit log access
- `admin`: full administrative access
- Public endpoints: `Register`, `Login`, `Get Model Version`, `Health Check`

## Audit Log APIs

### List Audit Logs

- Endpoint: `/api/v1/audit/logs`
- Method: `GET`
- Permission: `doctor`, `admin`
- Query parameters:
  - `action_type`
  - `resource_type`
  - `request_id`
  - `actor_user_id`
  - `limit`
- Description: Returns governance-grade audit events for upload, analyze, review, delete, and approval actions. Intended for operational tracing, incident review, and competition governance demonstrations.

Example:

```bash
curl "http://localhost:8000/api/v1/audit/logs?action_type=upload&resource_type=cxr_image&limit=20" \
  -H "Authorization: Bearer <doctor_token>"
```

### Get Audit Log Detail

- Endpoint: `/api/v1/audit/logs/{audit_log_id}`
- Method: `GET`
- Permission: `doctor`, `admin`
- Description: Returns a single audit event including hashed IP, request correlation ID, actor, resource, and sanitized event payload.

Example response:

```json
{
  "id": "aef7ee31-4ac9-4ae7-bfd3-b7fc944d0d62",
  "actor_user_id": "9d321c72-b346-44f0-bf18-f1f7ae55783d",
  "action_type": "upload",
  "resource_type": "cxr_image",
  "resource_id": "3f2e31e8-1e33-4a39-bb45-6ceba6647576",
  "request_id": "b43fe5ad-a1f7-4024-b6ee-21b28f769476",
  "ip_hash": "<sha256>",
  "user_agent": "python-requests/2.32.3",
  "event_payload": {
    "image_id": "3f2e31e8-1e33-4a39-bb45-6ceba6647576"
  },
  "created_at": "2026-05-01T10:31:18.214512Z",
  "updated_at": "2026-05-01T10:31:18.214512Z",
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

## 1. Register

**Endpoint**

`/api/v1/auth/register`

**Method**

`POST`

**Description**

Create a new MedVision-CXR user account and assign a role.

**Authentication**

None.

**Role Permission**

Public.

**Request Headers**

- `Content-Type: application/json`

**Path Parameters**

None.

**Query Parameters**

None.

**Request Body**

```json
{
  "email": "clinician@example.com",
  "password": "StrongPass123!",
  "role_code": "clinician"
}
```

**Response Body**

```json
{
  "id": "3d4ce3f2-45d6-4d30-a77a-25df8e2e9328",
  "email": "clinician@example.com",
  "status": "active",
  "role": {
    "id": "f0f8353e-a1e5-4205-b4b5-8bcd4e37080d",
    "role_code": "clinician",
    "role_name": "Clinician"
  }
}
```

**Error Responses**

- `400 Bad Request`: invalid role or email already registered
- `422 Unprocessable Entity`: validation failure

**Example Request**

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "clinician@example.com",
    "password": "StrongPass123!",
    "role_code": "clinician"
  }'
```

**Example Response**

```json
{
  "id": "3d4ce3f2-45d6-4d30-a77a-25df8e2e9328",
  "email": "clinician@example.com",
  "status": "active",
  "role": {
    "id": "f0f8353e-a1e5-4205-b4b5-8bcd4e37080d",
    "role_code": "clinician",
    "role_name": "Clinician"
  }
}
```

**Security Notes**

- Password must meet minimum length requirements.
- The response does not expose password hash or privileged claims.

## 2. Login

**Endpoint**

`/api/v1/auth/login`

**Method**

`POST`

**Description**

Authenticate a user and return a JWT access token.

**Authentication**

None.

**Role Permission**

Public.

**Request Headers**

- `Content-Type: application/json`

**Path Parameters**

None.

**Query Parameters**

None.

**Request Body**

```json
{
  "email": "clinician@example.com",
  "password": "StrongPass123!"
}
```

**Response Body**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Error Responses**

- `401 Unauthorized`: invalid credentials
- `422 Unprocessable Entity`: validation failure

**Example Request**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "clinician@example.com",
    "password": "StrongPass123!"
  }'
```

**Example Response**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600,
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Security Notes**

- Store the token securely and send it only via `Authorization: Bearer <token>`.
- Tokens should not be logged in plaintext.

## 3. Upload CXR Image

**Endpoint**

`/api/v1/cxr/upload`

**Method**

`POST`

**Description**

Upload a chest X-ray image for downstream AI-assisted risk assessment. EXIF removal and DICOM de-identification are applied where relevant.

**Authentication**

Bearer token required.

**Role Permission**

`clinician`, `doctor`, `admin`

**Request Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: multipart/form-data`

**Path Parameters**

None.

**Query Parameters**

None.

**Request Body**

Multipart form with a single file field:

- `file`: chest X-ray image file, such as `.png`, `.jpg`, or `.dcm`

**Response Body**

```json
{
  "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
  "storage_key": "uploads/2fc79d1f8e6d4820b4efb3b0f48f4d3b.png",
  "quality_check": {
    "too_small": false,
    "orientation_warning": false,
    "requires_review": false
  },
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Error Responses**

- `400 Bad Request`: unsupported file or file too large
- `401 Unauthorized`: missing or invalid token
- `422 Unprocessable Entity`: malformed multipart request
- `500 Internal Server Error`: storage failure

**Example Request**

```bash
curl -X POST http://localhost:8000/api/v1/cxr/upload \
  -H "Authorization: Bearer <access_token>" \
  -F "file=@sample-cxr.png"
```

**Example Response**

```json
{
  "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
  "storage_key": "uploads/2fc79d1f8e6d4820b4efb3b0f48f4d3b.png",
  "quality_check": {
    "too_small": false,
    "orientation_warning": false,
    "requires_review": false
  },
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Security Notes**

- Upload only de-identified clinical images.
- File metadata is sanitized before persistence where applicable.

## 4. Analyze CXR Image

**Endpoint**

`/api/v1/cxr/{image_id}/analyze`

**Method**

`POST`

**Description**

Run AI-assisted risk assessment for the specified chest X-ray image and optionally generate Grad-CAM outputs for selected labels.

**Authentication**

Bearer token required.

**Role Permission**

`clinician`, `doctor`, `admin`

**Request Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path Parameters**

- `image_id`: UUID of the uploaded chest X-ray image

**Query Parameters**

None.

**Request Body**

```json
{
  "priority": "normal",
  "requested_heatmaps": ["Pneumonia", "Pleural Effusion"]
}
```

**Response Body**

```json
{
  "job_id": "95bfb7ce-48ca-4fd7-b2bd-d3a112d7f472",
  "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
  "status": "completed",
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Error Responses**

- `401 Unauthorized`: missing or invalid token
- `404 Not Found`: image not found
- `500 Internal Server Error`: model or storage failure

**Example Request**

```bash
curl -X POST http://localhost:8000/api/v1/cxr/1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15/analyze \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "priority": "normal",
    "requested_heatmaps": ["Pneumonia"]
  }'
```

**Example Response**

```json
{
  "job_id": "95bfb7ce-48ca-4fd7-b2bd-d3a112d7f472",
  "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
  "status": "completed",
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Security Notes**

- Analysis output is AI-assisted only and must not be treated as final clinical judgment.
- Access should be limited to authenticated workflows.

## 5. Get Prediction Result

**Endpoint**

`/api/v1/cxr/results/{prediction_id}`

**Method**

`GET`

**Description**

Fetch the structured AI-assisted result for a completed prediction, including `risk_assessment`, `triage_result`, `ai_assisted_findings`, confidence indicators, and disclaimer.

**Authentication**

Bearer token required.

**Role Permission**

`clinician`, `doctor`, `admin`

**Request Headers**

- `Authorization: Bearer <access_token>`

**Path Parameters**

- `prediction_id`: UUID of the prediction record

**Query Parameters**

None.

**Request Body**

None.

**Response Body**

```json
{
  "prediction_id": "95bfb7ce-48ca-4fd7-b2bd-d3a112d7f472",
  "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
  "model_version": "cxr-densenet121-v1.3.0",
  "risk_level": "medium",
  "risk_assessment": {
    "overall_risk_level": "medium",
    "confidence_score": 0.87,
    "uncertainty_flag": false,
    "doctor_review_required": true
  },
  "triage_result": {
    "priority": "high",
    "recommended_action": "doctor_review"
  },
  "ai_assisted_findings": [
    {
      "label": "Pneumonia",
      "risk_probability": 0.82,
      "threshold": 0.5,
      "risk_flag": true
    },
    {
      "label": "Pleural Effusion",
      "risk_probability": 0.18,
      "threshold": 0.5,
      "risk_flag": false
    }
  ],
  "label_probabilities": {
    "Pneumonia": 0.82,
    "Pleural Effusion": 0.18
  },
  "confidence_score": 0.87,
  "uncertainty_flag": false,
  "doctor_review_required": true,
  "heatmap_urls": {
    "Pneumonia": {
      "heatmap_url": "http://localhost:8000/storage/cxr-outputs/heatmaps/pneumonia.png",
      "overlay_url": "http://localhost:8000/storage/cxr-outputs/overlays/pneumonia.png"
    }
  },
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Error Responses**

- `401 Unauthorized`: missing or invalid token
- `404 Not Found`: prediction not found

**Example Request**

```bash
curl -X GET http://localhost:8000/api/v1/cxr/results/95bfb7ce-48ca-4fd7-b2bd-d3a112d7f472 \
  -H "Authorization: Bearer <access_token>"
```

**Example Response**

```json
{
  "prediction_id": "95bfb7ce-48ca-4fd7-b2bd-d3a112d7f472",
  "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
  "model_version": "cxr-densenet121-v1.3.0",
  "risk_level": "medium",
  "risk_assessment": {
    "overall_risk_level": "medium",
    "confidence_score": 0.87,
    "uncertainty_flag": false,
    "doctor_review_required": true
  },
  "triage_result": {
    "priority": "high",
    "recommended_action": "doctor_review"
  },
  "ai_assisted_findings": [
    {
      "label": "Pneumonia",
      "risk_probability": 0.82,
      "threshold": 0.5,
      "risk_flag": true
    }
  ],
  "label_probabilities": {
    "Pneumonia": 0.82
  },
  "confidence_score": 0.87,
  "uncertainty_flag": false,
  "doctor_review_required": true,
  "heatmap_urls": {
    "Pneumonia": {
      "heatmap_url": "http://localhost:8000/storage/cxr-outputs/heatmaps/pneumonia.png",
      "overlay_url": "http://localhost:8000/storage/cxr-outputs/overlays/pneumonia.png"
    }
  },
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Security Notes**

- The API response is AI-assisted risk output and must be reviewed by qualified clinicians.
- The `heatmap_urls` block is documented for client convenience; actual heatmap retrieval is handled through dedicated endpoints.

## 6. Get User History

**Endpoint**

`/api/v1/cxr/history`

**Method**

`GET`

**Description**

Return the authenticated user's historical prediction list.

**Authentication**

Bearer token required.

**Role Permission**

`clinician`, `doctor`, `admin`

**Request Headers**

- `Authorization: Bearer <access_token>`

**Path Parameters**

None.

**Query Parameters**

None.

**Request Body**

None.

**Response Body**

```json
{
  "items": [
    {
      "prediction_id": "95bfb7ce-48ca-4fd7-b2bd-d3a112d7f472",
      "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
      "uploaded_at": "2026-05-01T09:30:00Z",
      "overall_risk_level": "medium",
      "doctor_review_required": true,
      "uncertainty_flag": false,
      "model_version": "cxr-densenet121-v1.3.0"
    }
  ],
  "total": 1,
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Error Responses**

- `401 Unauthorized`: missing or invalid token

**Example Request**

```bash
curl -X GET http://localhost:8000/api/v1/cxr/history \
  -H "Authorization: Bearer <access_token>"
```

**Example Response**

```json
{
  "items": [
    {
      "prediction_id": "95bfb7ce-48ca-4fd7-b2bd-d3a112d7f472",
      "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
      "uploaded_at": "2026-05-01T09:30:00Z",
      "overall_risk_level": "medium",
      "doctor_review_required": true,
      "uncertainty_flag": false,
      "model_version": "cxr-densenet121-v1.3.0"
    }
  ],
  "total": 1,
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Security Notes**

- History should be scoped to the authenticated user or an explicitly authorized reviewer workflow.
- Historical results remain AI-assisted records, not clinical conclusions.

## 7. Generate Grad-CAM

**Endpoint**

`/api/v1/cxr/{image_id}/gradcam`

**Method**

`POST`

**Description**

Generate or refresh Grad-CAM outputs for a target label on an analyzed chest X-ray image.

**Authentication**

Bearer token required.

**Role Permission**

`clinician`, `doctor`, `admin`

**Request Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path Parameters**

- `image_id`: UUID of the uploaded chest X-ray image

**Query Parameters**

None.

**Request Body**

```json
{
  "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
  "target_label": "Pneumonia"
}
```

**Response Body**

```json
{
  "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
  "target_label": "Pneumonia",
  "heatmap_url": "http://localhost:8000/storage/cxr-outputs/heatmaps/pneumonia.png",
  "overlay_url": "http://localhost:8000/storage/cxr-outputs/overlays/pneumonia.png",
  "notice": "模型在生成该风险提示时重点关注了以下区域。热力图仅用于辅助理解，不代表医学诊断依据。最终判断应由专业医生结合临床信息完成。",
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Error Responses**

- `400 Bad Request`: `image_id` mismatch or unsupported target label
- `401 Unauthorized`: missing or invalid token
- `404 Not Found`: image or prerequisite prediction not found
- `500 Internal Server Error`: heatmap generation failure

**Example Request**

```bash
curl -X POST http://localhost:8000/api/v1/cxr/1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15/gradcam \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
    "target_label": "Pneumonia"
  }'
```

**Example Response**

```json
{
  "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
  "target_label": "Pneumonia",
  "heatmap_url": "http://localhost:8000/storage/cxr-outputs/heatmaps/pneumonia.png",
  "overlay_url": "http://localhost:8000/storage/cxr-outputs/overlays/pneumonia.png",
  "notice": "模型在生成该风险提示时重点关注了以下区域。热力图仅用于辅助理解，不代表医学诊断依据。最终判断应由专业医生结合临床信息完成。",
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Security Notes**

- Heatmap outputs are interpretability aids only.
- Clients should not expose heatmaps as standalone clinical evidence.

## 8. Get Grad-CAM Output

**Endpoint**

`/api/v1/cxr/{image_id}/heatmap`

**Method**

`GET`

**Description**

Retrieve stored Grad-CAM output URLs for the latest prediction of a given image and label.

**Authentication**

Bearer token required.

**Role Permission**

`clinician`, `doctor`, `admin`

**Request Headers**

- `Authorization: Bearer <access_token>`

**Path Parameters**

- `image_id`: UUID of the chest X-ray image

**Query Parameters**

- `label`: target label, for example `Pneumonia`

**Request Body**

None.

**Response Body**

```json
{
  "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
  "label": "Pneumonia",
  "heatmap_url": "http://localhost:8000/storage/cxr-outputs/heatmaps/pneumonia.png",
  "overlay_url": "http://localhost:8000/storage/cxr-outputs/overlays/pneumonia.png",
  "notice": "热力图仅用于辅助理解，不代表医学诊断依据。",
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Error Responses**

- `401 Unauthorized`: missing or invalid token
- `404 Not Found`: prediction or heatmap not found

**Example Request**

```bash
curl -X GET "http://localhost:8000/api/v1/cxr/1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15/heatmap?label=Pneumonia" \
  -H "Authorization: Bearer <access_token>"
```

**Example Response**

```json
{
  "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
  "label": "Pneumonia",
  "heatmap_url": "http://localhost:8000/storage/cxr-outputs/heatmaps/pneumonia.png",
  "overlay_url": "http://localhost:8000/storage/cxr-outputs/overlays/pneumonia.png",
  "notice": "热力图仅用于辅助理解，不代表医学诊断依据。",
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Security Notes**

- Interpretation artifacts should be access-controlled the same way as the associated image and result.

## 9. Submit Doctor Review

**Endpoint**

`/api/v1/reviews`

**Method**

`POST`

**Description**

Create or update a doctor review for a prediction.

**Authentication**

Bearer token required.

**Role Permission**

`doctor`, `admin`

**Request Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path Parameters**

None.

**Query Parameters**

None.

**Request Body**

```json
{
  "prediction_id": "95bfb7ce-48ca-4fd7-b2bd-d3a112d7f472",
  "review_priority": "high",
  "review_status": "reviewed",
  "review_action": "escalate",
  "review_note": "建议优先进一步检查。"
}
```

**Response Body**

```json
{
  "review_id": "93a4db76-f46a-4474-bd01-624dafbdf8cd",
  "prediction_id": "95bfb7ce-48ca-4fd7-b2bd-d3a112d7f472",
  "saved": true,
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Error Responses**

- `401 Unauthorized`: missing or invalid token
- `403 Forbidden`: insufficient role
- `422 Unprocessable Entity`: invalid review payload

**Example Request**

```bash
curl -X POST http://localhost:8000/api/v1/reviews \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "prediction_id": "95bfb7ce-48ca-4fd7-b2bd-d3a112d7f472",
    "review_priority": "high",
    "review_status": "reviewed",
    "review_action": "escalate",
    "review_note": "建议优先进一步检查。"
  }'
```

**Example Response**

```json
{
  "review_id": "93a4db76-f46a-4474-bd01-624dafbdf8cd",
  "prediction_id": "95bfb7ce-48ca-4fd7-b2bd-d3a112d7f472",
  "saved": true,
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Security Notes**

- Only qualified reviewer roles should be allowed to persist review decisions.
- Review content may contain sensitive operational notes and should be audited.

## 10. Get Review

**Endpoint**

`/api/v1/reviews/{prediction_id}`

**Method**

`GET`

**Description**

Retrieve the doctor review associated with a prediction.

**Authentication**

Bearer token required.

**Role Permission**

`doctor`, `admin`

**Request Headers**

- `Authorization: Bearer <access_token>`

**Path Parameters**

- `prediction_id`: UUID of the prediction record

**Query Parameters**

None.

**Request Body**

None.

**Response Body**

```json
{
  "review_id": "93a4db76-f46a-4474-bd01-624dafbdf8cd",
  "prediction_id": "95bfb7ce-48ca-4fd7-b2bd-d3a112d7f472",
  "review_priority": "high",
  "review_status": "reviewed",
  "review_action": "escalate",
  "review_note": "建议优先进一步检查。",
  "reviewed_at": "2026-05-01T10:15:00Z",
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Error Responses**

- `401 Unauthorized`: missing or invalid token
- `403 Forbidden`: insufficient role
- `404 Not Found`: review not found

**Example Request**

```bash
curl -X GET http://localhost:8000/api/v1/reviews/95bfb7ce-48ca-4fd7-b2bd-d3a112d7f472 \
  -H "Authorization: Bearer <access_token>"
```

**Example Response**

```json
{
  "review_id": "93a4db76-f46a-4474-bd01-624dafbdf8cd",
  "prediction_id": "95bfb7ce-48ca-4fd7-b2bd-d3a112d7f472",
  "review_priority": "high",
  "review_status": "reviewed",
  "review_action": "escalate",
  "review_note": "建议优先进一步检查。",
  "reviewed_at": "2026-05-01T10:15:00Z",
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Security Notes**

- Review detail retrieval is restricted to privileged reviewer roles.
- Review records should be treated as sensitive operational data and audited.

## 11. Get Model Version

**Endpoint**

`/api/v1/model/version`

**Method**

`GET`

**Description**

Return the active deployed model version used for AI-assisted inference.

**Authentication**

None in current backend.

**Role Permission**

Public.

**Request Headers**

None.

**Path Parameters**

None.

**Query Parameters**

None.

**Request Body**

None.

**Response Body**

```json
{
  "active_model_version": "cxr-densenet121-v1.3.0",
  "framework": "PyTorch",
  "deployed_at": "2026-05-01T08:00:00Z",
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Error Responses**

- `500 Internal Server Error`: model metadata lookup failure

**Example Request**

```bash
curl -X GET http://localhost:8000/api/v1/model/version
```

**Example Response**

```json
{
  "active_model_version": "cxr-densenet121-v1.3.0",
  "framework": "PyTorch",
  "deployed_at": "2026-05-01T08:00:00Z",
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Security Notes**

- Exposing version metadata is acceptable, but internal artifact locations should remain protected.

## 12. Get Model Metrics

**Endpoint**

`/api/v1/model/metrics`

**Method**

`GET`

**Description**

Return operational and validation metrics for the active model.

**Authentication**

None in current backend.

**Role Permission**

Public.

**Request Headers**

- `Authorization: Bearer <access_token>`

**Path Parameters**

None.

**Query Parameters**

None.

**Request Body**

None.

**Response Body**

```json
{
  "model_version": "cxr-densenet121-v1.3.0",
  "metrics": {
    "macro_auc": 0.882,
    "macro_f1": 0.641,
    "validation_dataset": "CheXpert-based",
    "calibration_status": "validated"
  },
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Error Responses**

- `401 Unauthorized`: missing or invalid token
- `403 Forbidden`: insufficient role
- `404 Not Found`: metrics unavailable

**Example Request**

```bash
curl -X GET http://localhost:8000/api/v1/model/metrics \
  -H "Authorization: Bearer <access_token>"
```

**Example Response**

```json
{
  "model_version": "cxr-densenet121-v1.3.0",
  "metrics": {
    "macro_auc": 0.882,
    "macro_f1": 0.641,
    "validation_dataset": "CheXpert-based",
    "calibration_status": "validated"
  },
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Security Notes**

- The endpoint is implemented, but teams may still choose to place it behind authentication in stricter deployments.
- Model validation metrics may be sensitive in regulated or competitive settings.

## 13. Delete CXR Image

**Endpoint**

`/api/v1/cxr/{image_id}`

**Method**

`DELETE`

**Description**

Delete or soft-delete a chest X-ray image record.

**Authentication**

Bearer token required.

**Role Permission**

Recommended: `clinician` for owned images, `doctor` and `admin` for governed workflows

**Request Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path Parameters**

- `image_id`: UUID of the chest X-ray image

**Query Parameters**

None.

**Request Body**

```json
{
  "delete_mode": "soft",
  "reason": "影像上传错误，请求撤回并重新上传。"
}
```

**Response Body**

```json
{
  "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
  "request_status": "completed",
  "delete_mode": "soft",
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Error Responses**

- `401 Unauthorized`: missing or invalid token
- `403 Forbidden`: insufficient permission
- `404 Not Found`: image not found
- `409 Conflict`: protected resource state

**Example Request**

```bash
curl -X DELETE http://localhost:8000/api/v1/cxr/1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15 \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "delete_mode": "soft",
    "reason": "影像上传错误，请求撤回并重新上传。"
  }'
```

**Example Response**

```json
{
  "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
  "request_status": "completed",
  "delete_mode": "soft",
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Security Notes**

- Direct delete is implemented and intended for tightly controlled operational flows.
- For audited or approval-gated deletion, prefer the governed deletion workflow endpoints documented below.

## 14. Health Check

**Endpoint**

`/api/v1/health`

**Method**

`GET`

**Description**

Return runtime health indicators for the API service, database, Redis, and model service loader state.

**Authentication**

None in current backend.

**Role Permission**

Public.

**Request Headers**

None.

**Path Parameters**

None.

**Query Parameters**

None.

**Request Body**

None.

**Response Body**

```json
{
  "status": "ok",
  "db": "up",
  "redis": "down",
  "model_service": "loaded",
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Error Responses**

- `500 Internal Server Error`: unexpected health probe failure

**Example Request**

```bash
curl -X GET http://localhost:8000/api/v1/health
```

**Example Response**

```json
{
  "status": "ok",
  "db": "up",
  "redis": "down",
  "model_service": "loaded",
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Security Notes**

- Public health endpoints should avoid exposing secrets, stack traces, or internal infrastructure metadata.

## Deletion Workflow APIs

This section documents the governed deletion approval workflow at the same granularity as the core API reference. These endpoints are already implemented and are recommended when deletion must be reviewed, approved, or audited.

### A. Submit Deletion Request

**Endpoint**

`/api/v1/deletions/requests`

**Method**

`POST`

**Description**

Submit a governed deletion request for a chest X-ray image. Non-privileged users may only request deletion for their own images.

**Authentication**

Bearer token required.

**Role Permission**

`clinician`, `doctor`, `admin`

**Request Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path Parameters**

None.

**Query Parameters**

None.

**Request Body**

```json
{
  "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
  "delete_mode": "soft",
  "reason": "影像上传错误，请求撤回并重新上传。"
}
```

**Response Body**

```json
{
  "request_id": "2b875f67-3750-4837-8b81-7cb7f657db7c",
  "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
  "delete_mode": "soft",
  "deletion_reason": "影像上传错误，请求撤回并重新上传。",
  "request_status": "pending",
  "requested_by": "3d4ce3f2-45d6-4d30-a77a-25df8e2e9328",
  "approved_by": null,
  "approval_note": null,
  "rejection_reason": null,
  "completed_at": null,
  "created_at": "2026-05-01T10:20:00Z",
  "updated_at": "2026-05-01T10:20:00Z",
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Error Responses**

- `400 Bad Request`: invalid delete mode
- `403 Forbidden`: user does not own the image and lacks elevated role
- `404 Not Found`: image not found
- `409 Conflict`: pending deletion request already exists
- `422 Unprocessable Entity`: validation failure

**Example Request**

```bash
curl -X POST http://localhost:8000/api/v1/deletions/requests \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
    "delete_mode": "soft",
    "reason": "影像上传错误，请求撤回并重新上传。"
  }'
```

**Example Response**

```json
{
  "request_id": "2b875f67-3750-4837-8b81-7cb7f657db7c",
  "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
  "delete_mode": "soft",
  "deletion_reason": "影像上传错误，请求撤回并重新上传。",
  "request_status": "pending",
  "requested_by": "3d4ce3f2-45d6-4d30-a77a-25df8e2e9328",
  "approved_by": null,
  "approval_note": null,
  "rejection_reason": null,
  "completed_at": null,
  "created_at": "2026-05-01T10:20:00Z",
  "updated_at": "2026-05-01T10:20:00Z",
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Security Notes**

- Use this endpoint when deletion must be reviewed rather than executed immediately.
- The request reason should avoid patient-identifying content.

### B. List Deletion Requests

**Endpoint**

`/api/v1/deletions/requests`

**Method**

`GET`

**Description**

List deletion requests. Doctors and admins may see all requests; other users only see their own.

**Authentication**

Bearer token required.

**Role Permission**

`clinician`, `doctor`, `admin`

**Request Headers**

- `Authorization: Bearer <access_token>`

**Path Parameters**

None.

**Query Parameters**

- `request_status`: optional filter such as `pending`, `completed`, or `rejected`

**Request Body**

None.

**Response Body**

```json
{
  "items": [
    {
      "request_id": "2b875f67-3750-4837-8b81-7cb7f657db7c",
      "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
      "delete_mode": "soft",
      "deletion_reason": "影像上传错误，请求撤回并重新上传。",
      "request_status": "pending",
      "requested_by": "3d4ce3f2-45d6-4d30-a77a-25df8e2e9328",
      "approved_by": null,
      "approval_note": null,
      "rejection_reason": null,
      "completed_at": null,
      "created_at": "2026-05-01T10:20:00Z",
      "updated_at": "2026-05-01T10:20:00Z",
      "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
    }
  ],
  "total": 1,
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Error Responses**

- `401 Unauthorized`: missing or invalid token

**Example Request**

```bash
curl -X GET "http://localhost:8000/api/v1/deletions/requests?request_status=pending" \
  -H "Authorization: Bearer <access_token>"
```

**Example Response**

```json
{
  "items": [
    {
      "request_id": "2b875f67-3750-4837-8b81-7cb7f657db7c",
      "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
      "delete_mode": "soft",
      "deletion_reason": "影像上传错误，请求撤回并重新上传。",
      "request_status": "pending",
      "requested_by": "3d4ce3f2-45d6-4d30-a77a-25df8e2e9328",
      "approved_by": null,
      "approval_note": null,
      "rejection_reason": null,
      "completed_at": null,
      "created_at": "2026-05-01T10:20:00Z",
      "updated_at": "2026-05-01T10:20:00Z",
      "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
    }
  ],
  "total": 1,
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Security Notes**

- This listing endpoint exposes operational governance state and should remain authenticated.

### C. Approve or Reject Deletion Request

**Endpoint**

`/api/v1/deletions/requests/{deletion_request_id}/decision`

**Method**

`POST`

**Description**

Approve or reject a deletion request. Approval executes the deletion path; rejection stores `rejection_reason` and optional review notes.

**Authentication**

Bearer token required.

**Role Permission**

`doctor`, `admin`

**Request Headers**

- `Authorization: Bearer <access_token>`
- `Content-Type: application/json`

**Path Parameters**

- `deletion_request_id`: UUID of the deletion request

**Query Parameters**

None.

**Request Body**

```json
{
  "approval_action": "reject",
  "approval_note": "建议保留影像用于审计追踪。",
  "rejection_reason": "该影像已进入医生复核流程，当前不允许删除。"
}
```

**Response Body**

```json
{
  "request_id": "2b875f67-3750-4837-8b81-7cb7f657db7c",
  "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
  "delete_mode": "soft",
  "deletion_reason": "影像上传错误，请求撤回并重新上传。",
  "request_status": "rejected",
  "requested_by": "3d4ce3f2-45d6-4d30-a77a-25df8e2e9328",
  "approved_by": "4f4acbb0-79fe-4ee1-97bc-eb6d246c7b4e",
  "approval_note": "建议保留影像用于审计追踪。",
  "rejection_reason": "该影像已进入医生复核流程，当前不允许删除。",
  "completed_at": null,
  "created_at": "2026-05-01T10:20:00Z",
  "updated_at": "2026-05-01T10:23:00Z",
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Error Responses**

- `400 Bad Request`: invalid action or missing `rejection_reason`
- `403 Forbidden`: insufficient permissions
- `404 Not Found`: deletion request or image not found
- `409 Conflict`: deletion request already processed
- `422 Unprocessable Entity`: validation failure

**Example Request**

```bash
curl -X POST http://localhost:8000/api/v1/deletions/requests/2b875f67-3750-4837-8b81-7cb7f657db7c/decision \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "approval_action": "approve",
    "approval_note": "已核对病例状态，允许执行软删除。",
    "rejection_reason": null
  }'
```

**Example Response**

```json
{
  "request_id": "2b875f67-3750-4837-8b81-7cb7f657db7c",
  "image_id": "1a0dc8cb-2824-49b6-95d4-c8f36f0a6b15",
  "delete_mode": "soft",
  "deletion_reason": "影像上传错误，请求撤回并重新上传。",
  "request_status": "completed",
  "requested_by": "3d4ce3f2-45d6-4d30-a77a-25df8e2e9328",
  "approved_by": "4f4acbb0-79fe-4ee1-97bc-eb6d246c7b4e",
  "approval_note": "已核对病例状态，允许执行软删除。",
  "rejection_reason": null,
  "completed_at": "2026-05-01T10:24:00Z",
  "created_at": "2026-05-01T10:20:00Z",
  "updated_at": "2026-05-01T10:24:00Z",
  "disclaimer": "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。"
}
```

**Security Notes**

- Approval endpoints should be restricted to privileged reviewer roles and audited.
- Rejection and approval notes should avoid unnecessary patient-identifying detail.
