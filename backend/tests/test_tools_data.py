from app.services.seed_service import seed_service
from app.tools.campaign_tools import generate_campaign_copy
from app.tools.product_tools import get_product_info
from app.tools.review_tools import summarize_reviews


def test_seed_counts_are_expanded():
    assert len(seed_service.get_products()) >= 12
    assert len(seed_service.get_reviews()) >= 60
    assert len(seed_service.get_competitors()) >= 6


def test_product_fuzzy_match_supports_short_name():
    product = seed_service.find_product("咖啡杯")
    assert product is not None
    assert product["name"] == "云萃保温咖啡杯"


def test_detect_product_name_supports_message_alias():
    product_name = seed_service.detect_product_name("帮我总结一下这款咖啡杯最近的差评")
    assert product_name == "云萃保温咖啡杯"


def test_tool_response_contract_for_product_info():
    result = get_product_info("云萃保温咖啡杯")
    assert result["success"] is True
    assert result["tool_name"] == "get_product_info"
    assert result["input"]["product_name"] == "云萃保温咖啡杯"
    assert "output" in result
    assert isinstance(result["latency_ms"], int)
    assert result["error"] is None
    assert result["found"] is True


def test_tool_response_contract_for_review_summary():
    result = summarize_reviews("云萃保温咖啡杯", days=7)
    assert result["success"] is True
    assert result["tool_name"] == "summarize_reviews"
    assert result["input"]["days"] == 7
    assert result["output"]["review_count"] >= 1


def test_tool_response_contract_for_campaign_copy():
    result = generate_campaign_copy("咖啡杯", "618", "上班族")
    assert result["success"] is True
    assert result["tool_name"] == "generate_campaign_copy"
    assert result["headline"]
    assert result["error"] is None

