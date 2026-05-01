from __future__ import annotations

import pytest


pytestmark = pytest.mark.integration


def test_openapi_documents_deletion_workflow(api_client):
    response = api_client.session.get(f"{api_client.base_url.removesuffix('/api/v1')}/openapi.json", timeout=api_client.timeout)
    assert response.status_code == 200, response.text

    payload = response.json()
    create_codes = sorted(payload["paths"]["/api/v1/deletions/requests"]["post"]["responses"].keys())
    decision_codes = sorted(payload["paths"]["/api/v1/deletions/requests/{deletion_request_id}/decision"]["post"]["responses"].keys())

    assert create_codes == ["201", "400", "403", "404", "409", "422"]
    assert decision_codes == ["200", "400", "403", "404", "409", "422"]


def test_soft_delete_request_can_be_approved(api_client, db_client):
    _, clinician_token = api_client.register_and_login("clinician")
    _, doctor_token = api_client.register_and_login("doctor")

    upload_payload = api_client.upload_test_image(clinician_token)
    request_response = api_client.post(
        "/deletions/requests",
        headers=api_client.auth_headers(clinician_token),
        json={
            "image_id": upload_payload["image_id"],
            "delete_mode": "soft",
            "reason": "影像上传错误，请求撤回并重新上传。",
        },
    )
    assert request_response.status_code == 201, request_response.text

    deletion_request = request_response.json()
    decision_response = api_client.post(
        f"/deletions/requests/{deletion_request['request_id']}/decision",
        headers=api_client.auth_headers(doctor_token),
        json={"approval_action": "approve", "approval_note": "已核对病例状态，允许执行软删除。"},
    )
    assert decision_response.status_code == 200, decision_response.text

    decision_payload = decision_response.json()
    assert decision_payload["request_status"] == "completed"
    assert decision_payload["approval_note"] == "已核对病例状态，允许执行软删除。"
    assert decision_payload["rejection_reason"] is None

    db_row = db_client.fetch_deletion_request(deletion_request["request_id"])
    assert db_row is not None
    assert db_row["request_status"] == "completed"
    assert db_row["deletion_reason"] == "影像上传错误，请求撤回并重新上传。"
    assert db_row["approval_note"] == "已核对病例状态，允许执行软删除。"
    assert db_row["rejection_reason"] is None
    assert db_row["approved_by"] is not None
    assert db_row["completed_at"] is not None
    assert db_row["image_is_deleted"] is True


def test_soft_delete_request_can_be_rejected(api_client, db_client):
    _, clinician_token = api_client.register_and_login("clinician")
    _, doctor_token = api_client.register_and_login("doctor")

    upload_payload = api_client.upload_test_image(clinician_token)
    request_response = api_client.post(
        "/deletions/requests",
        headers=api_client.auth_headers(clinician_token),
        json={
            "image_id": upload_payload["image_id"],
            "delete_mode": "soft",
            "reason": "该案例仍需保留，但先验证拒绝链。",
        },
    )
    assert request_response.status_code == 201, request_response.text

    deletion_request = request_response.json()
    decision_response = api_client.post(
        f"/deletions/requests/{deletion_request['request_id']}/decision",
        headers=api_client.auth_headers(doctor_token),
        json={
            "approval_action": "reject",
            "approval_note": "建议保留影像用于审计追踪。",
            "rejection_reason": "该影像已进入医生复核流程，当前不允许删除。",
        },
    )
    assert decision_response.status_code == 200, decision_response.text

    decision_payload = decision_response.json()
    assert decision_payload["request_status"] == "rejected"
    assert decision_payload["approval_note"] == "建议保留影像用于审计追踪。"
    assert decision_payload["rejection_reason"] == "该影像已进入医生复核流程，当前不允许删除。"

    db_row = db_client.fetch_deletion_request(deletion_request["request_id"])
    assert db_row is not None
    assert db_row["request_status"] == "rejected"
    assert db_row["deletion_reason"] == "该案例仍需保留，但先验证拒绝链。"
    assert db_row["approval_note"] == "建议保留影像用于审计追踪。"
    assert db_row["rejection_reason"] == "该影像已进入医生复核流程，当前不允许删除。"
    assert db_row["approved_by"] is not None
    assert db_row["completed_at"] is None
    assert db_row["image_is_deleted"] is False


def test_duplicate_pending_deletion_request_returns_conflict(api_client):
    _, clinician_token = api_client.register_and_login("clinician")

    upload_payload = api_client.upload_test_image(clinician_token)
    first_response = api_client.post(
        "/deletions/requests",
        headers=api_client.auth_headers(clinician_token),
        json={
            "image_id": upload_payload["image_id"],
            "delete_mode": "soft",
            "reason": "第一次提交删除申请。",
        },
    )
    assert first_response.status_code == 201, first_response.text

    duplicate_response = api_client.post(
        "/deletions/requests",
        headers=api_client.auth_headers(clinician_token),
        json={
            "image_id": upload_payload["image_id"],
            "delete_mode": "soft",
            "reason": "重复提交删除申请。",
        },
    )
    assert duplicate_response.status_code == 409, duplicate_response.text
    assert duplicate_response.json()["detail"] == "A pending deletion request already exists for this image"


def test_clinician_cannot_review_deletion_request(api_client):
    _, clinician_token = api_client.register_and_login("clinician")
    _, another_clinician_token = api_client.register_and_login("clinician")

    upload_payload = api_client.upload_test_image(clinician_token)
    request_response = api_client.post(
        "/deletions/requests",
        headers=api_client.auth_headers(clinician_token),
        json={
            "image_id": upload_payload["image_id"],
            "delete_mode": "soft",
            "reason": "等待审批的删除申请。",
        },
    )
    assert request_response.status_code == 201, request_response.text

    deletion_request = request_response.json()
    decision_response = api_client.post(
        f"/deletions/requests/{deletion_request['request_id']}/decision",
        headers=api_client.auth_headers(another_clinician_token),
        json={"approval_action": "approve", "approval_note": "无权审批但尝试提交。"},
    )
    assert decision_response.status_code == 403, decision_response.text