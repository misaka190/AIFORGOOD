# MedVision-CXR: Explainable Chest X-ray Triage for Primary Healthcare

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)
![Next.js](https://img.shields.io/badge/Next.js-15-black?logo=next.js&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.x-EE4C2C?logo=pytorch&logoColor=white)
![Responsible AI](https://img.shields.io/badge/Responsible%20AI-Enabled-0D5C63)
![SDG 3](https://img.shields.io/badge/UN%20SDG-3%20Good%20Health%20and%20Well--being-4C9F38)
![License](https://img.shields.io/badge/License-TBD-lightgrey)

</div>

**中文名：MedVision-CXR：面向基层医疗的可解释胸部 X 光辅助分诊系统**

MedVision-CXR is an explainable AI-assisted chest X-ray triage system that helps healthcare teams prioritize doctor review by generating multi-label risk probabilities, overall triage level, confidence score, uncertainty prompt, Grad-CAM heatmaps, and review recommendations.

## Medical Disclaimer

This project is **not** a medical diagnosis system.

- It is designed **only for AI-assisted triage, screening support, and doctor review prioritization**.
- It must **not** be used as the sole basis for clinical judgment.
- It must **not** be used for emergency medical decision-making.
- It does **not** replace licensed clinicians.
- It does **not** provide treatment advice.
- Final judgment must be made by qualified medical professionals in combination with clinical information.

## Responsible AI

MedVision-CXR is designed as a human-in-the-loop chest X-ray triage system rather than an automated diagnosis product.

- The system provides AI-assisted risk prompts, triage prioritization, Grad-CAM interpretability, and doctor review support.
- It does not provide deterministic diagnosis or treatment advice.
- Final clinical judgment must always be made by qualified healthcare professionals.
- High-risk or uncertain outputs should automatically enter doctor review.
- The platform uses anonymized file naming, EXIF stripping, DICOM de-identification, JWT authentication, RBAC, audit logging, and governed deletion workflows.
- Fairness should be evaluated across sex, age, device source, hospital source, image quality, and disease labels.
- All outputs must include a disclaimer and be presented as AI-assisted risk assessment only.

See [docs/medvision-cxr-responsible-ai.md](docs/medvision-cxr-responsible-ai.md) for the full Responsible AI, privacy, fairness, and governance design, and see [docs/medvision-cxr-model-card.md](docs/medvision-cxr-model-card.md) for the model card.

## AI for Good / SDG 3

MedVision-CXR aligns with **AI for Good** and the **United Nations Sustainable Development Goal 3: Good Health and Well-being**.

The project targets real constraints in primary healthcare and low-resource settings:

- Limited access to radiology specialists
- Large chest X-ray screening workloads
- Delays in identifying higher-risk cases for review
- Low trust in black-box AI without interpretability or uncertainty prompts

By focusing on **human-in-the-loop triage support**, this project aims to improve review efficiency rather than automate clinical diagnosis.

## Project Background

Chest X-ray is one of the most widely used imaging modalities in community clinics, primary hospitals, mobile screening units, and public health programs. In many such settings, imaging capacity exists but expert review capacity is constrained. As a result, clinically important images may not be reviewed quickly enough.

MedVision-CXR addresses this gap with an explainable workflow that combines:

- chest X-ray upload
- file and image validation
- AI-assisted multi-label risk assessment
- overall triage prioritization
- uncertainty flagging
- Grad-CAM visual explanation
- doctor review workflow
- auditability and model version traceability

## Core Features

- Multi-label chest X-ray risk probability output for 12 labels including Atelectasis, Cardiomegaly, Consolidation, Edema, Pleural Effusion, Pneumonia, Pneumothorax, Lung Opacity, Enlarged Cardiomediastinum, Fracture, Support Devices, and No Finding
- Overall triage level for review prioritization
- Model confidence score and uncertainty prompt
- Grad-CAM heatmap and overlay generation for explainability
- Doctor review recommendations and review capture workflow
- Upload validation, anonymized storage, EXIF stripping, and DICOM de-identification
- Model version tracking and audit logging
- Frontend workflow for upload, analysis, results, review, history, and privacy pages
- Backend APIs for auth, upload, analysis, results, Grad-CAM, history, and review
- Deletion request workflow with request submission, approval or rejection, audit logging, and soft or hard delete execution

## Demo Screenshots

> Screenshot placeholders for GitHub showcase and competition submission. Replace with real product captures before public release.

| View | Placeholder |
|---|---|
| Home | `docs/assets/demo-home.png` |
| Upload | `docs/assets/demo-upload.png` |
| Results | `docs/assets/demo-results.png` |
| Grad-CAM | `docs/assets/demo-gradcam.png` |
| Doctor Review | `docs/assets/demo-review.png` |

## System Architecture

```mermaid
flowchart TD
    A[Next.js Frontend] --> B[FastAPI Backend]
    B --> C[Auth and RBAC]
    B --> D[Upload and Validation]
    B --> E[Prediction Service]
    B --> F[Grad-CAM Service]
    B --> G[Doctor Review Service]
    B --> H[Audit Log Service]

    D --> I[MinIO Object Storage]
    D --> J[PostgreSQL]
    E --> J
    F --> I
    F --> J
    G --> J
    H --> J

    B --> K[Redis]
    K --> L[Celery Worker]
    L --> E
    L --> F

    M[ML Training Pipeline] --> N[DVC]
    M --> O[MLflow]
    M --> P[Model Registry]
    P --> E
```

## Tech Stack

### Frontend

- Next.js
- TypeScript
- Tailwind CSS
- Axios
- React Hook Form
- Recharts

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Redis
- Celery
- MinIO
- JWT

### AI / MLOps

- PyTorch
- DenseNet121 / EfficientNet-B0
- Grad-CAM
- MLflow
- DVC
- Docker

## Project Structure

```text
.
├── docs/
│   └── medvision-cxr-blueprint.md
├── medvision-cxr/
│   ├── backend/
│   │   ├── app/
│   │   ├── alembic/
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── frontend/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   ├── types/
│   │   ├── Dockerfile
│   │   └── package.json
│   ├── ml-training/
│   │   ├── configs/
│   │   ├── notebooks/
│   │   ├── src/
│   │   └── requirements.txt
│   ├── model-serving/
│   ├── data/
│   ├── deployment/
│   ├── docker/
│   ├── scripts/
│   ├── tests/
│   └── pitch/
└── README.md
```

## Quick Start

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd AIFORGOOD
```

### 2. Recommended local setup

- Python virtual environment for backend and training
- Node.js 20+ for frontend
- PostgreSQL 15+
- Redis 7+
- MinIO or S3-compatible object storage

### 3. Read the design blueprint

The full project design document is available in [docs/medvision-cxr-blueprint.md](docs/medvision-cxr-blueprint.md).

## Environment Variables

### Backend

Recommended environment variables for `medvision-cxr/backend`:

```env
APP_NAME=MedVision-CXR Backend
API_V1_PREFIX=/api/v1
ENVIRONMENT=development
SECRET_KEY=change-this-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/medvision_cxr
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
MINIO_BUCKET_RAW=cxr-raw
MINIO_BUCKET_OUTPUTS=cxr-outputs
MODEL_ARTIFACT_PATH=artifacts/cxr_model.pt
MODEL_VERSION_NAME=cxr-densenet121-v1.3.0
MAX_UPLOAD_MB=15
ALLOW_DICOM=true
```

### Frontend

The current frontend example environment file is in [medvision-cxr/frontend/.env.example](medvision-cxr/frontend/.env.example).

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

## Docker Compose Startup

This repository includes a runnable root-level [docker-compose.yml](docker-compose.yml) for local demo and evaluation environments. The stack includes:

- frontend
- backend
- postgres
- redis
- minio

Start the full stack with:

```bash
docker compose up --build
```

The backend example environment file is available at [medvision-cxr/backend/.env.example](medvision-cxr/backend/.env.example).

Suggested exposed ports:

- frontend: `3000`
- backend: `8000`
- postgres: `5432`
- redis: `6379`
- minio api: `9000`

## Deletion Workflow API

The backend now exposes a complete deletion approval workflow.

### Endpoints

- `POST /api/v1/deletions/requests`
- `GET /api/v1/deletions/requests`
- `POST /api/v1/deletions/requests/{deletion_request_id}/decision`

### Request Example: Submit Deletion Request

```json
{
  "image_id": "11111111-1111-1111-1111-111111111111",
  "delete_mode": "soft",
  "reason": "影像上传错误，请求撤回并重新上传。"
}
```

### Request Example: Approve Deletion Request

```json
{
  "approval_action": "approve",
  "approval_note": "已核对病例状态，允许执行软删除。"
}
```

### Request Example: Reject Deletion Request

```json
{
  "approval_action": "reject",
  "approval_note": "建议保留影像用于审计追踪。",
  "rejection_reason": "该影像已进入医生复核流程，当前不允许删除。"
}
```

### Status Codes

- `201 Created`: 删除请求已创建。
- `200 OK`: 删除请求查询成功，或审批动作已执行。
- `400 Bad Request`: `delete_mode` 不合法，或拒绝请求时未提供 `rejection_reason`。
- `401 Unauthorized`: 未提供或提供了无效访问令牌。
- `403 Forbidden`: 当前用户无权删除该影像，或无权审批删除请求。
- `404 Not Found`: 指定影像或删除请求不存在。
- `409 Conflict`: 已存在待处理删除请求，或该删除请求已经被审批处理。

### Behavior Notes

- `soft` delete 会将影像标记为 `is_deleted=true`，保留数据库审计链。
- `hard` delete 会额外清理原始影像与 Grad-CAM 对象存储文件，同时仍保留删除请求与审计日志。
- 普通用户只能为自己上传的影像发起删除请求。
- `doctor` 和 `admin` 可以审批或拒绝删除请求。
- minio console: `9001`

## Frontend Startup

```bash
cd medvision-cxr/frontend
npm install
npm run dev
```

Default URL:

```text
http://localhost:3000
```

## Backend Startup

```bash
cd medvision-cxr/backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Default API base URL:

```text
http://localhost:8000/api/v1
```

## Backend Integration Tests

The backend now includes repeatable pytest integration tests for the deletion approval workflow in [medvision-cxr/backend/tests/integration/test_deletion_workflow.py](medvision-cxr/backend/tests/integration/test_deletion_workflow.py).

These tests exercise a running FastAPI service over real HTTP using `pytest + requests`, covering:

- OpenAPI response code regression checks for deletion routes
- direct database assertions for `deletion_reason`, `approval_note`, and `rejection_reason`
- soft-delete approval flow
- rejection flow with rejection reason persistence
- duplicate pending deletion request conflict
- upload and history regression coverage
- prediction results regression coverage
- doctor review persistence and authorization checks
- unauthorized review attempt returning `403`

Run them against a running backend instance after PostgreSQL migrations are applied:

```bash
cd medvision-cxr/backend
pip install -r requirements.txt
pytest -m integration tests/integration/test_deletion_workflow.py
```

Optional environment variables:

```bash
MEDVISION_API_BASE_URL=http://127.0.0.1:8000/api/v1
MEDVISION_API_TIMEOUT_SECONDS=30
MEDVISION_TEST_DATABASE_URL=postgresql+psycopg2://postgres@127.0.0.1:5433/medvision_cxr
```

The tests assert that `/health` returns `status=ok` and `db=up` before executing workflow scenarios. Redis may remain unavailable during this test run.

For local Windows development, you can also use the one-click orchestration script in [medvision-cxr/scripts/run_backend_integration.ps1](medvision-cxr/scripts/run_backend_integration.ps1). It will:

- start PostgreSQL from `.pgdata-dev` when needed
- ensure the `medvision_cxr` database exists
- run Alembic migrations to `head`
- reuse a healthy backend on port `8000` or start `uvicorn` if needed
- execute the backend integration suite

Example:

```powershell
pwsh -File medvision-cxr/scripts/run_backend_integration.ps1 -SkipDependencyInstall
```

To keep the backend process running after the test suite finishes:

```powershell
pwsh -File medvision-cxr/scripts/run_backend_integration.ps1 -KeepBackendRunning
```

## Model Training

```bash
cd medvision-cxr/ml-training
pip install -r requirements.txt
python src/train.py --config configs/cxr_densenet121.yaml
```

Training outputs include:

- best model checkpoint
- metrics JSON
- calibration JSON
- error case export
- sample inference output

## Model Inference

Inference is integrated in the FastAPI backend through the model service in [medvision-cxr/backend/app/services/model_service.py](medvision-cxr/backend/app/services/model_service.py).

Current inference behavior includes:

- image preprocessing
- sigmoid-based multi-label probability output
- overall triage level derivation
- uncertainty flag derivation
- doctor review recommendation
- model version and disclaimer output

## API Documentation

When the backend is running, OpenAPI docs are available at:

- `/docs`
- `/redoc`

A project-specific OpenAPI-style reference is also available at [docs/medvision-cxr-api-reference.md](docs/medvision-cxr-api-reference.md).

A consumable OpenAPI 3.1 YAML specification is available at [docs/medvision-cxr-openapi.yaml](docs/medvision-cxr-openapi.yaml).

Key API endpoints include:

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/cxr/upload`
- `POST /api/v1/cxr/{image_id}/analyze`
- `POST /api/v1/cxr/{image_id}/gradcam`
- `GET /api/v1/cxr/results/{prediction_id}`
- `GET /api/v1/cxr/history`
- `GET /api/v1/cxr/{image_id}/heatmap`
- `POST /api/v1/reviews`
- `GET /api/v1/model/version`
- `GET /api/v1/health`

## Dataset Notes

MedVision-CXR is designed to work with **publicly available de-identified chest X-ray datasets** for research and demonstration purposes.

Recommended public datasets:

- CheXpert
- NIH ChestX-ray14
- MIMIC-CXR
- PadChest
- RSNA Pneumonia Detection Challenge

Current baseline recommendation:

- Primary demo dataset: **CheXpert**
- Split strategy: **patient-level split to prevent data leakage**
- Small demo scope: **3,000 to 8,000 studies**

Do not upload or train on identifiable clinical data unless you have proper legal, ethical, and institutional approval.

## Model Evaluation

Recommended evaluation metrics for this project:

- AUROC per label
- Macro AUROC
- AUPRC
- Precision
- Recall
- F1-score
- Confusion matrix
- Threshold search analysis
- Calibration curve
- Error case export
- Fairness evaluation across sex, age groups, and device sources

In this triage context, **accuracy alone is not sufficient**. Special attention should be given to:

- false negatives
- calibration quality
- uncertainty-aware review routing

## Grad-CAM Explainability

Grad-CAM is used to visualize which image regions contributed most to a selected risk prompt.

This repository includes:

- training-side reusable Grad-CAM utilities
- backend Grad-CAM generation service
- frontend Grad-CAM viewer for label switching

Interpretation rules used in this project:

- “模型在生成该风险提示时重点关注了以下区域。”
- “热力图仅用于辅助理解，不代表医学诊断依据。”
- “最终判断应由专业医生结合临床信息完成。”

The README intentionally does **not** describe Grad-CAM as detecting lesions or proving disease presence.

## Privacy and Ethics

Responsible AI is a first-class requirement in MedVision-CXR.

- AI output is for triage support only
- Doctor review remains mandatory for high-risk or uncertain outputs
- The system should not be used for emergency-only decision making
- Uploaded filenames are anonymized
- EXIF metadata should be stripped
- DICOM identity fields should be removed
- Audit logs should avoid storing sensitive personal information
- Public de-identified datasets are recommended for research workflows
- Model bias and external validation limits must be communicated clearly

## Model Card

### Intended use

- AI-assisted chest X-ray triage
- screening support
- doctor review prioritization

### Not intended for

- automated diagnosis
- standalone clinical decision-making
- emergency medical decision without clinician oversight
- treatment recommendation

### Model family

- DenseNet121 baseline
- EfficientNet-B0 optional improvement path

### Output format

- multi-label `risk_probability`
- `overall_risk_level`
- `confidence_score`
- `uncertainty_flag`
- `doctor_review_required`
- `disclaimer`

### Known limitations

- sensitive to distribution shift
- may underperform on unseen acquisition settings
- interpretability maps are approximate attention-style explanations, not medical proof
- requires external validation before real-world deployment

## Data Card

### Data source type

- public de-identified chest X-ray datasets

### Recommended labels

- Atelectasis
- Cardiomegaly
- Consolidation
- Edema
- Pleural Effusion
- Pneumonia
- Pneumothorax
- Lung Opacity
- Enlarged Cardiomediastinum
- Fracture
- Support Devices
- No Finding

### Data handling guidance

- use patient-level split
- avoid leakage across train, validation, and test
- document uncertain and blank label strategy
- track preprocessing and versioning with DVC or equivalent

### Ethical notes

- use de-identified public data for demos and reproducibility
- do not claim clinical safety from benchmark performance alone
- publish limitations and subgroup performance where possible

## Roadmap

- [x] Competition-grade project blueprint
- [x] Frontend workflow prototype
- [x] FastAPI backend skeleton and core APIs
- [x] Training pipeline baseline
- [x] Grad-CAM explainability module
- [ ] Alembic migrations
- [x] Docker Compose orchestration
- [ ] Integration tests
- [ ] External validation report
- [ ] Full model card and data card documents
- [ ] Production-grade monitoring and alerting

## Contributing

Contributions are welcome, especially in the following areas:

- frontend usability improvements
- backend robustness and tests
- training reproducibility
- fairness evaluation
- documentation quality
- low-resource deployment

Suggested contribution flow:

1. Fork the repository.
2. Create a feature branch.
3. Keep medical wording aligned with the project safety policy.
4. Submit a pull request with a clear summary, validation notes, and any UI or API screenshots.

Before contributing, please ensure that your changes do **not** make unsupported medical claims.

Detailed contribution guidance is available in [CONTRIBUTING.md](CONTRIBUTING.md).

## License

This repository is released under the **MIT License**. See [LICENSE](LICENSE).

## Citation

If you use this repository in research, hackathons, or academic demos, please cite it as:

```bibtex
@misc{medvision_cxr_2026,
  title        = {MedVision-CXR: Explainable Chest X-ray Triage for Primary Healthcare},
  author       = {MedVision-CXR Contributors},
  year         = {2026},
  howpublished = {GitHub repository},
  note         = {AI-assisted chest X-ray triage system for primary healthcare}
}
```

## Contact

For project discussion, competition collaboration, or research inquiry:

- GitHub Issues: use this repository issue tracker
- Maintainer email: `your-email@example.com`
- Competition deck and narrative materials: see `medvision-cxr/pitch/`

## Competition Positioning

MedVision-CXR is intentionally positioned as a **Responsible AI-assisted triage platform** rather than an autonomous medical diagnosis tool. This makes it suitable for:

- AI for Good competitions
- healthcare innovation demos
- academic team showcases
- GitHub portfolio presentation

The core message is consistent across the system:

**AI supports prioritization and review. Doctors remain responsible for final interpretation.**