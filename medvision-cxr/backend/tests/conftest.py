from __future__ import annotations

import io
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

import psycopg2
import pytest
import requests
from PIL import Image
from psycopg2.extras import Json, RealDictCursor
from sqlalchemy.engine import make_url


DEFAULT_API_BASE_URL = "http://127.0.0.1:8000/api/v1"
DEFAULT_TIMEOUT_SECONDS = 30
DEFAULT_PASSWORD = "StrongPass123!"
DEFAULT_DATABASE_URL = "postgresql+psycopg2://postgres@127.0.0.1:5433/medvision_cxr"
BACKEND_ROOT = Path(__file__).resolve().parents[1]


@dataclass
class ApiClient:
    base_url: str
    timeout: int

    def __post_init__(self) -> None:
        self.session = requests.Session()

    def get(self, path: str, **kwargs):
        return self.session.get(f"{self.base_url}{path}", timeout=self.timeout, **kwargs)

    def post(self, path: str, **kwargs):
        return self.session.post(f"{self.base_url}{path}", timeout=self.timeout, **kwargs)

    def delete(self, path: str, **kwargs):
        return self.session.delete(f"{self.base_url}{path}", timeout=self.timeout, **kwargs)

    def register_user(self, role_code: str) -> dict:
        email = f"{role_code}-{uuid4().hex}@example.com"
        payload = {"email": email, "password": DEFAULT_PASSWORD, "role_code": role_code}
        response = self.post("/auth/register", json=payload)
        assert response.status_code == 201, response.text
        return response.json()

    def login_user(self, email: str) -> str:
        response = self.post("/auth/login", json={"email": email, "password": DEFAULT_PASSWORD})
        assert response.status_code == 200, response.text
        return response.json()["access_token"]

    def register_and_login(self, role_code: str) -> tuple[dict, str]:
        user = self.register_user(role_code)
        token = self.login_user(user["email"])
        return user, token

    def auth_headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    def upload_test_image(self, token: str) -> dict:
        buffer = io.BytesIO()
        image = Image.new("L", (512, 512), color=192)
        image.save(buffer, format="PNG")
        buffer.seek(0)

        response = self.post(
            "/cxr/upload",
            headers=self.auth_headers(token),
            files={"file": ("test-cxr.png", buffer.getvalue(), "image/png")},
        )
        assert response.status_code == 201, response.text
        return response.json()


@dataclass
class DatabaseClient:
    database_url: str

    def __post_init__(self) -> None:
        url = make_url(self.database_url)
        self.connection = psycopg2.connect(
            dbname=url.database,
            user=url.username,
            password=url.password,
            host=url.host,
            port=url.port,
        )
        self.connection.autocommit = True

    def fetch_one(self, query: str, params: tuple[Any, ...] = ()) -> dict[str, Any] | None:
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
        return dict(row) if row else None

    def execute(self, query: str, params: tuple[Any, ...] = ()) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(query, params)

    def fetch_deletion_request(self, request_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            select
                dr.id::text as id,
                dr.image_id::text as image_id,
                dr.request_status,
                dr.delete_mode,
                dr.deletion_reason,
                dr.approval_note,
                dr.rejection_reason,
                dr.approved_by::text as approved_by,
                dr.completed_at,
                img.is_deleted as image_is_deleted
            from deletion_requests dr
            join cxr_images img on img.id = dr.image_id
            where dr.id::text = %s
            """,
            (request_id,),
        )

    def ensure_active_model_version(self) -> dict[str, Any]:
        existing = self.fetch_one(
            """
            select id::text as id, version_name
            from model_versions
            where is_active = true
            order by created_at asc
            limit 1
            """
        )
        if existing:
            return existing

        version_name = "integration-test-model"
        current = self.fetch_one(
            "select id::text as id, version_name from model_versions where version_name = %s limit 1",
            (version_name,),
        )
        if current:
            self.execute("update model_versions set is_active = true where id::text = %s", (current["id"],))
            return current

        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            model_version_id = str(uuid4())
            cursor.execute(
                """
                insert into model_versions (
                    id,
                    version_name,
                    model_family,
                    dataset_summary,
                    metrics_json,
                    artifact_uri,
                    is_active
                )
                values (%s::uuid, %s, %s, %s, %s, %s, true)
                returning id::text as id, version_name
                """,
                (
                    model_version_id,
                    version_name,
                    "DenseNet121",
                    Json({"source": "integration-test"}),
                    Json({"status": "integration"}),
                    "artifacts/integration-test-model.pt",
                ),
            )
            row = cursor.fetchone()
        return dict(row)

    def create_prediction(self, image_id: str) -> dict[str, Any]:
        model_version = self.ensure_active_model_version()
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            prediction_id = str(uuid4())
            cursor.execute(
                """
                insert into cxr_predictions (
                    id,
                    image_id,
                    model_version_id,
                    job_status,
                    overall_risk_level,
                    uncertainty_flag,
                    doctor_review_required,
                    confidence_score,
                    disclaimer,
                    raw_scores_json,
                    triage_result_json
                )
                values (%s::uuid, %s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s)
                returning id::text as id, image_id::text as image_id, model_version_id::text as model_version_id
                """,
                (
                    prediction_id,
                    image_id,
                    model_version["id"],
                    "completed",
                    "medium",
                    False,
                    True,
                    0.82,
                    "本系统仅用于胸部 X 光影像的辅助筛查、辅助分诊和医生复核优先级排序，不用于自动诊断，不替代医生，不提供治疗建议。",
                    Json({"Pneumonia": 0.82}),
                    Json({"priority": "high", "doctor_review_required": True}),
                ),
            )
            prediction = dict(cursor.fetchone())
            prediction_label_id = str(uuid4())
            cursor.execute(
                """
                insert into prediction_labels (
                    id,
                    prediction_id,
                    label_code,
                    risk_probability,
                    threshold_used,
                    risk_flag,
                    calibrated_score,
                    finding_text
                )
                values (%s::uuid, %s::uuid, %s, %s, %s, %s, %s, %s)
                """,
                (
                    prediction_label_id,
                    prediction["id"],
                    "Pneumonia",
                    0.82,
                    0.5,
                    True,
                    0.82,
                    "提示存在 Pneumonia 相关风险特征，建议结合医生复核。",
                ),
            )
        prediction["model_version"] = model_version["version_name"]
        return prediction

    def fetch_doctor_review(self, prediction_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            select
                id::text as id,
                prediction_id::text as prediction_id,
                reviewer_id::text as reviewer_id,
                review_priority,
                review_status,
                review_action,
                review_note
            from doctor_reviews
            where prediction_id::text = %s
            """,
            (prediction_id,),
        )

    def fetch_audit_log(self, action_type: str, resource_type: str, resource_id: str | None = None) -> dict[str, Any] | None:
        if resource_id:
            return self.fetch_one(
                """
                select
                    id::text as id,
                    actor_user_id::text as actor_user_id,
                    action_type,
                    resource_type,
                    resource_id::text as resource_id,
                    request_id,
                    event_payload,
                    created_at
                from audit_logs
                where action_type = %s and resource_type = %s and resource_id::text = %s
                order by created_at desc
                limit 1
                """,
                (action_type, resource_type, resource_id),
            )

        return self.fetch_one(
            """
            select
                id::text as id,
                actor_user_id::text as actor_user_id,
                action_type,
                resource_type,
                resource_id::text as resource_id,
                request_id,
                event_payload,
                created_at
            from audit_logs
            where action_type = %s and resource_type = %s
            order by created_at desc
            limit 1
            """,
            (action_type, resource_type),
        )

    def fetch_image(self, image_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            select id::text as id, storage_key, is_deleted
            from cxr_images
            where id::text = %s
            """,
            (image_id,),
        )

    def update_active_model_metrics(self, metrics: dict[str, Any]) -> dict[str, Any] | None:
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                update model_versions
                set metrics_json = %s
                where is_active = true
                returning id::text as id, version_name, model_family, metrics_json, deployed_at
                """,
                (Json(metrics),),
            )
            row = cursor.fetchone()
        return dict(row) if row else None

    def local_raw_object_path(self, storage_key: str) -> Path:
        return BACKEND_ROOT / "storage" / "cxr-raw" / storage_key

    def close(self) -> None:
        self.connection.close()


@pytest.fixture(scope="session")
def api_base_url() -> str:
    return os.getenv("MEDVISION_API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/")


@pytest.fixture(scope="session")
def api_timeout_seconds() -> int:
    return int(os.getenv("MEDVISION_API_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)))


@pytest.fixture(scope="session")
def database_url() -> str:
    return os.getenv("MEDVISION_TEST_DATABASE_URL") or os.getenv("DATABASE_URL") or DEFAULT_DATABASE_URL


@pytest.fixture(scope="session")
def api_client(api_base_url: str, api_timeout_seconds: int) -> ApiClient:
    client = ApiClient(base_url=api_base_url, timeout=api_timeout_seconds)
    health_response = client.get("/health")
    assert health_response.status_code == 200, health_response.text

    health_payload = health_response.json()
    assert health_payload["status"] == "ok", health_payload
    assert health_payload["db"] == "up", health_payload
    return client


@pytest.fixture(scope="session")
def db_client(database_url: str) -> DatabaseClient:
    client = DatabaseClient(database_url=database_url)
    yield client
    client.close()