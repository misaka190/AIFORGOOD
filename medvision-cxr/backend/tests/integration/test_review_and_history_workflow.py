from __future__ import annotations

import pytest


pytestmark = pytest.mark.integration


def test_upload_and_history_returns_prediction_for_current_user(api_client, db_client):
    _, clinician_token = api_client.register_and_login("clinician")

    upload_payload = api_client.upload_test_image(clinician_token)
    assert upload_payload["storage_key"].startswith("uploads/")
    assert upload_payload["quality_check"]["too_small"] is False

    prediction = db_client.create_prediction(upload_payload["image_id"])

    history_response = api_client.get("/cxr/history", headers=api_client.auth_headers(clinician_token))
    assert history_response.status_code == 200, history_response.text

    history_payload = history_response.json()
    assert history_payload["total"] >= 1

    matching_item = next((item for item in history_payload["items"] if item["prediction_id"] == prediction["id"]), None)
    assert matching_item is not None
    assert matching_item["image_id"] == upload_payload["image_id"]
    assert matching_item["overall_risk_level"] == "medium"
    assert matching_item["doctor_review_required"] is True
    assert matching_item["model_version"] == prediction["model_version"]


def test_prediction_results_endpoint_returns_seeded_prediction(api_client, db_client):
    _, clinician_token = api_client.register_and_login("clinician")

    upload_payload = api_client.upload_test_image(clinician_token)
    prediction = db_client.create_prediction(upload_payload["image_id"])

    results_response = api_client.get(
        f"/cxr/results/{prediction['id']}",
        headers=api_client.auth_headers(clinician_token),
    )
    assert results_response.status_code == 200, results_response.text

    results_payload = results_response.json()
    assert results_payload["prediction_id"] == prediction["id"]
    assert results_payload["image_id"] == upload_payload["image_id"]
    assert results_payload["risk_assessment"]["overall_risk_level"] == "medium"
    assert results_payload["risk_assessment"]["doctor_review_required"] is True
    assert any(item["label"] == "Pneumonia" for item in results_payload["ai_assisted_findings"])


def test_doctor_review_flow_persists_review_record(api_client, db_client):
    _, clinician_token = api_client.register_and_login("clinician")
    doctor_user, doctor_token = api_client.register_and_login("doctor")

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
            "review_note": "建议优先进一步检查。",
        },
    )
    assert review_response.status_code == 201, review_response.text

    review_payload = review_response.json()
    assert review_payload["saved"] is True
    assert review_payload["prediction_id"] == prediction["id"]

    db_row = db_client.fetch_doctor_review(prediction["id"])
    assert db_row is not None
    assert db_row["prediction_id"] == prediction["id"]
    assert db_row["reviewer_id"] == doctor_user["id"]
    assert db_row["review_priority"] == "high"
    assert db_row["review_status"] == "reviewed"
    assert db_row["review_action"] == "escalate"
    assert db_row["review_note"] == "建议优先进一步检查。"


def test_doctor_can_get_review_detail(api_client, db_client):
    _, clinician_token = api_client.register_and_login("clinician")
    doctor_user, doctor_token = api_client.register_and_login("doctor")

    upload_payload = api_client.upload_test_image(clinician_token)
    prediction = db_client.create_prediction(upload_payload["image_id"])

    create_response = api_client.post(
        "/reviews",
        headers=api_client.auth_headers(doctor_token),
        json={
            "prediction_id": prediction["id"],
            "review_priority": "high",
            "review_status": "reviewed",
            "review_action": "escalate",
            "review_note": "建议优先进一步检查。",
        },
    )
    assert create_response.status_code == 201, create_response.text

    get_response = api_client.get(
        f"/reviews/{prediction['id']}",
        headers=api_client.auth_headers(doctor_token),
    )
    assert get_response.status_code == 200, get_response.text

    payload = get_response.json()
    assert payload["prediction_id"] == prediction["id"]
    assert payload["reviewer_id"] == doctor_user["id"]
    assert payload["review_priority"] == "high"
    assert payload["review_status"] == "reviewed"
    assert payload["review_action"] == "escalate"
    assert payload["review_note"] == "建议优先进一步检查。"


def test_model_metrics_returns_active_model_metrics(api_client, db_client):
    metrics = {
        "macro_auc": 0.882,
        "macro_f1": 0.641,
        "validation_dataset": "CheXpert-based",
        "calibration_status": "validated",
    }
    active_model = db_client.update_active_model_metrics(metrics)
    assert active_model is not None

    response = api_client.get("/model/metrics")
    assert response.status_code == 200, response.text

    payload = response.json()
    assert payload["model_version"] == active_model["version_name"]
    assert payload["model_family"] == active_model["model_family"]
    assert payload["metrics"] == metrics


def test_direct_delete_marks_image_deleted_and_removes_raw_object_on_hard_delete(api_client, db_client):
    _, clinician_token = api_client.register_and_login("clinician")

    upload_payload = api_client.upload_test_image(clinician_token)
    image_row = db_client.fetch_image(upload_payload["image_id"])
    assert image_row is not None
    raw_path = db_client.local_raw_object_path(image_row["storage_key"])
    assert raw_path.exists()

    response = api_client.delete(
        f"/cxr/{upload_payload['image_id']}",
        headers=api_client.auth_headers(clinician_token),
        json={"delete_mode": "hard", "reason": "测试直接删除接口。"},
    )
    assert response.status_code == 200, response.text

    payload = response.json()
    assert payload["image_id"] == upload_payload["image_id"]
    assert payload["request_status"] == "completed"
    assert payload["delete_mode"] == "hard"
    assert payload["reason"] == "测试直接删除接口。"

    image_row_after = db_client.fetch_image(upload_payload["image_id"])
    assert image_row_after is not None
    assert image_row_after["is_deleted"] is True
    assert not raw_path.exists()


def test_clinician_cannot_submit_doctor_review(api_client, db_client):
    _, clinician_token = api_client.register_and_login("clinician")

    upload_payload = api_client.upload_test_image(clinician_token)
    prediction = db_client.create_prediction(upload_payload["image_id"])

    review_response = api_client.post(
        "/reviews",
        headers=api_client.auth_headers(clinician_token),
        json={
            "prediction_id": prediction["id"],
            "review_priority": "high",
            "review_status": "reviewed",
            "review_action": "escalate",
            "review_note": "普通用户无权写入医生复核。",
        },
    )
    assert review_response.status_code == 403, review_response.text