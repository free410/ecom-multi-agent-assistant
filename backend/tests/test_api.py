from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def sid(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:8]}"


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in {"ok", "partial", "degraded"}
    assert data["database"]["message"]
    assert data["redis"]["message"]


def test_seed_init_endpoint():
    response = client.post("/api/seed/init")
    assert response.status_code == 200
    data = response.json()
    assert data["product_count"] >= 6
    assert data["review_count"] >= 20


def test_products_endpoint():
    client.post("/api/seed/init")
    response = client.get("/api/products")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 6
    assert data[0]["name"]


def test_chat_campaign_copy_route_has_structured_fields():
    payload = {
        "session_id": sid("test-session-campaign"),
        "message": "根据云萃保温咖啡杯的卖点生成618促销文案",
        "model_provider": "mock",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "campaign_copy"
    assert "generate_campaign_copy" in data["used_tools"]
    assert data["confidence"] > 0.5
    assert data["routing_reason"]
    assert isinstance(data["structured_result"], dict)
    assert data["structured_result"]["agent"] == "ContentAgent"
    assert isinstance(data["tool_details"], list)
    assert data["tool_details"][0]["tool_name"] == "generate_campaign_copy"


def test_chat_review_summary_route_has_tool_details():
    payload = {
        "session_id": sid("test-session-review"),
        "message": "总结云萃保温咖啡杯最近7天差评关键词",
        "model_provider": "mock",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "review_summary"
    assert "extract_negative_keywords" in data["used_tools"]
    assert len(data["tool_details"]) >= 2
    assert data["structured_result"]["agent"] == "AnalysisAgent"


def test_chat_clarification_route():
    payload = {
        "session_id": sid("test-session-clarification"),
        "message": "给我生成一段618促销文案",
        "model_provider": "mock",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "campaign_copy"
    assert data["structured_result"]["agent"] == "ClarificationNode"
    assert "任务主体" in data["answer"] or "商品名" in data["answer"]
    assert data["confidence"] <= 0.45


def test_session_detail_endpoint_contains_last_result():
    session_id = sid("test-session-history")
    client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "整理云萃保温咖啡杯与竞品的差异",
            "model_provider": "mock",
        },
    )
    response = client.get(f"/api/session/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert len(data["history"]) >= 2
    assert data["last_result"] is not None
    assert "confidence" in data["last_result"]
    assert "tool_details" in data["last_result"]


def test_memory_restore_product_name_from_short_term_memory():
    session_id = sid("test-session-memory")
    first_response = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "总结云萃保温咖啡杯最近7天差评关键词",
            "model_provider": "mock",
        },
    )
    assert first_response.status_code == 200

    second_response = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "再整理一下这款产品与竞品的差异",
            "model_provider": "mock",
        },
    )
    assert second_response.status_code == 200
    data = second_response.json()
    assert data["intent"] == "competitor_compare"
    assert data["memory_used"]["short_term_memory"] is True
    assert "product_name" in data["restored_fields"]


def test_chat_general_greeting_route_returns_answer():
    payload = {
        "session_id": sid("test-session-general-chat"),
        "message": "你好",
        "model_provider": "mock",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "general_chat"
    assert data["structured_result"]["agent"] == "GeneralAgent"
    assert "你好" in data["answer"] or "电商运营智能助手" in data["answer"]
    assert "GeneralAgent" in data["agent_path"]


def test_generic_category_campaign_copy_should_work_without_seed_product():
    payload = {
        "session_id": sid("test-session-generic-category"),
        "message": "给我写一个手机的文案",
        "model_provider": "mock",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "campaign_copy"
    assert data["structured_result"]["agent"] == "ContentAgent"
    assert data["structured_result"]["product_name"] == "手机"
    assert "generate_campaign_copy" in data["used_tools"]


def test_clarification_follow_up_should_resume_previous_task():
    session_id = sid("test-session-follow-up")
    first = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "给我写一个文案",
            "model_provider": "mock",
        },
    )
    assert first.status_code == 200
    first_data = first.json()
    assert first_data["intent"] == "campaign_copy"
    assert first_data["structured_result"]["agent"] == "ClarificationNode"

    second = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "手机",
            "model_provider": "mock",
        },
    )
    assert second.status_code == 200
    data = second.json()
    assert data["intent"] == "campaign_copy"
    assert data["structured_result"]["agent"] == "ContentAgent"
    assert data["memory_used"]["short_term_memory"] is True
    assert "generate_campaign_copy" in data["used_tools"]


def test_clarification_follow_up_with_earphone_should_resume_previous_task():
    session_id = sid("test-session-follow-up-earphone")
    first = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "给我写一个文案",
            "model_provider": "mock",
        },
    )
    assert first.status_code == 200
    first_data = first.json()
    assert first_data["intent"] == "campaign_copy"
    assert first_data["structured_result"]["agent"] == "ClarificationNode"

    second = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "耳机",
            "model_provider": "mock",
        },
    )
    assert second.status_code == 200
    data = second.json()
    assert data["intent"] == "campaign_copy"
    assert data["structured_result"]["agent"] == "ContentAgent"
    assert data["structured_result"]["product_name"] == "耳机"
    assert data["memory_used"]["short_term_memory"] is True
    assert "generate_campaign_copy" in data["used_tools"]
    assert "ContentAgent" in data["agent_path"]


def test_follow_up_with_restatement_should_keep_business_intent():
    session_id = sid("test-session-restatement")
    first = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "给我写一个文案",
            "model_provider": "mock",
        },
    )
    assert first.status_code == 200

    second = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "我说的是手机的文案",
            "model_provider": "mock",
        },
    )
    assert second.status_code == 200
    data = second.json()
    assert data["intent"] == "campaign_copy"
    assert data["structured_result"]["agent"] == "ContentAgent"
    assert data["structured_result"]["product_name"] == "手机"


def test_delete_session_endpoint_removes_session_from_list():
    session_id = sid("test-session-delete")
    created = client.post(
        "/api/chat",
        json={
            "session_id": session_id,
            "message": "给我写一个手机的文案",
            "model_provider": "mock",
        },
    )
    assert created.status_code == 200

    before = client.get("/api/sessions")
    assert before.status_code == 200
    assert any(item["session_id"] == session_id for item in before.json())

    deleted = client.delete(f"/api/session/{session_id}")
    assert deleted.status_code == 200

    after = client.get("/api/sessions")
    assert after.status_code == 200
    assert not any(item["session_id"] == session_id for item in after.json())
