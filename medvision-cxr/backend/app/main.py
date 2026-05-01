import uuid

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from redis import Redis
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.api import audit_routes, auth, cxr_routes, deletion_routes, review_routes
from app.core.config import get_settings
from app.db.database import get_db, get_engine
from app.models.models import ModelVersion, Role
from app.schemas.schemas import HealthResponse, ModelMetricsResponse, ModelVersionResponse


settings = get_settings()
app = FastAPI(title=settings.app_name)
settings.local_storage_root.mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=settings.local_storage_root), name="storage")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request, call_next):
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


@app.on_event("startup")
def startup() -> None:
    if not inspect(get_engine()).has_table("roles"):
        return

    db = next(get_db())
    try:
        if not db.query(Role).filter(Role.role_code == "admin").first():
            db.add_all(
                [
                    Role(role_code="admin", role_name="Administrator", permissions_json={"all": True}),
                    Role(role_code="doctor", role_name="Doctor", permissions_json={"review": True}),
                    Role(role_code="clinician", role_name="Clinician", permissions_json={"upload": True}),
                ]
            )
            db.commit()
        if not db.query(ModelVersion).filter(ModelVersion.is_active.is_(True)).first():
            db.add(
                ModelVersion(
                    version_name=settings.model_version_name,
                    model_family="DenseNet121",
                    dataset_summary={"source": "CheXpert-based"},
                    metrics_json={"status": "demo"},
                    artifact_uri=settings.model_artifact_path,
                    is_active=True,
                )
            )
            db.commit()
    finally:
        db.close()


app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(cxr_routes.router, prefix=settings.api_v1_prefix)
app.include_router(audit_routes.router, prefix=settings.api_v1_prefix)
app.include_router(deletion_routes.router, prefix=settings.api_v1_prefix)
app.include_router(review_routes.router, prefix=settings.api_v1_prefix)


@app.get(f"{settings.api_v1_prefix}/model/version", response_model=ModelVersionResponse, tags=["model"])
def get_model_version(db: Session = Depends(get_db)) -> ModelVersionResponse:
    model_version = db.query(ModelVersion).filter(ModelVersion.is_active.is_(True)).first()
    if not model_version:
        model_version = ModelVersion(
            version_name=settings.model_version_name,
            model_family="DenseNet121",
            dataset_summary={"source": "CheXpert-based"},
            metrics_json={"status": "demo"},
            artifact_uri=settings.model_artifact_path,
            is_active=True,
        )
        db.add(model_version)
        db.commit()
        db.refresh(model_version)
    return ModelVersionResponse(
        active_model_version=model_version.version_name,
        framework="PyTorch",
        deployed_at=model_version.deployed_at,
    )


@app.get(f"{settings.api_v1_prefix}/model/metrics", response_model=ModelMetricsResponse, tags=["model"])
def get_model_metrics(db: Session = Depends(get_db)) -> ModelMetricsResponse:
    model_version = db.query(ModelVersion).filter(ModelVersion.is_active.is_(True)).first()
    if not model_version:
        model_version = ModelVersion(
            version_name=settings.model_version_name,
            model_family="DenseNet121",
            dataset_summary={"source": "CheXpert-based"},
            metrics_json={"status": "demo"},
            artifact_uri=settings.model_artifact_path,
            is_active=True,
        )
        db.add(model_version)
        db.commit()
        db.refresh(model_version)

    return ModelMetricsResponse(
        model_version=model_version.version_name,
        model_family=model_version.model_family,
        metrics=model_version.metrics_json,
        deployed_at=model_version.deployed_at,
    )


@app.get(f"{settings.api_v1_prefix}/health", response_model=HealthResponse, tags=["health"])
def health(db: Session = Depends(get_db)) -> HealthResponse:
    try:
        db.execute(text("SELECT 1"))
        db_status = "up"
    except Exception:
        db_status = "down"

    try:
        redis_client = Redis.from_url(settings.redis_url)
        redis_status = "up" if redis_client.ping() else "down"
    except Exception:
        redis_status = "down"

    return HealthResponse(status="ok", db=db_status, redis=redis_status, model_service="loaded")