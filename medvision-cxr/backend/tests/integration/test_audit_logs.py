from __future__ import annotations

import pytest


pytestmark = pytest.mark.integration


def test_doctor_can_list_and_get_audit_logs(api_client, db_client):
    clinician_user, clinician_token = api_client.register_and_login("clinician")
    _, doctor_token = api_client.register_and_login("doctor")

    upload_payload = api_client.upload_test_image(clinician_token)
    prediction = db_client.create_prediction(upload_payload["image_id"])

    review_response = api_client.post(
        "/reviews",
        headers=api_client.auth_headers(doctor_token),
        json={
            "prediction_id": prediction["id"],
            "review_priority": "high",
            "review_status": "reviewed",
            "review_action": "escalate",
            "review_note": "审计链路测试。",
        },
    )
    assert review_response.status_code == 201, review_response.text

    upload_log = db_client.fetch_audit_log("upload", "cxr_image", upload_payload["image_id"])
    assert upload_log is not None

    list_response = api_client.get(
        f"/audit/logs?action_type=upload&resource_type=cxr_image&actor_user_id={clinician_user['id']}",
        headers=api_client.auth_headers(doctor_token),
    )
    assert list_response.status_code == 200, list_response.text

    payload = list_response.json()
    assert payload["total"] >= 1
    assert any(item["id"] == upload_log["id"] for item in payload["items"])

    detail_response = api_client.get(
        f"/audit/logs/{upload_log['id']}",
        headers=api_client.auth_headers(doctor_token),
    )
    assert detail_response.status_code == 200, detail_response.text

    detail_payload = detail_response.json()
    assert detail_payload["action_type"] == "upload"
    assert detail_payload["resource_type"] == "cxr_image"
    assert detail_payload["resource_id"] == upload_payload["image_id"]
    assert detail_payload["actor_user_id"] == clinician_user["id"]
    assert detail_payload["event_payload"]["image_id"] == upload_payload["image_id"]


def test_clinician_cannot_access_audit_logs(api_client):
    _, clinician_token = api_client.register_and_login("clinician")

    response = api_client.get("/audit/logs", headers=api_client.auth_headers(clinician_token))
    assert response.status_code == 403, response.text


def test_openapi_exposes_audit_log_endpoints(api_client):
    backend_origin = api_client.base_url.rsplit("/api/v1", 1)[0]
    response = api_client.session.get(f"{backend_origin}/openapi.json", timeout=api_client.timeout)
    assert response.status_code == 200, response.text

    payload = response.json()
    assert "/api/v1/audit/logs" in payload["paths"]
    assert "/api/v1/audit/logs/{audit_log_id}" in payload["paths"]
    assert payload["paths"]["/api/v1/audit/logs"]["get"]["tags"] == ["audit"]