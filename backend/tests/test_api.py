from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert "status" in response.json()


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


def test_chat_campaign_copy_route():
    payload = {
        "session_id": "test-session-campaign",
        "message": "根据云萃保温咖啡杯的卖点生成618促销文案",
        "model_provider": "mock",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "campaign_copy"
    assert "generate_campaign_copy" in data["used_tools"]


def test_chat_review_summary_route():
    payload = {
        "session_id": "test-session-review",
        "message": "总结云萃保温咖啡杯最近7天差评关键词",
        "model_provider": "mock",
    }
    response = client.post("/api/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "review_summary"
    assert "extract_negative_keywords" in data["used_tools"]


def test_session_detail_endpoint():
    session_id = "test-session-history"
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

