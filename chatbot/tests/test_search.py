"""The search_products tool and the Mongo filter helpers."""
import pytest

from app.utils.mongo import keyword_filter, keyword_patterns


def names(reply):
    return [p["name"] for p in reply["data"] or []]


@pytest.mark.parametrize("keyword", ["shirt", "shirts", "Shirts", "SHIRT"])
def test_keyword_matches_singular_and_plural(keyword):
    assert any("shirt" in p for p in keyword_patterns(keyword))
    assert keyword_filter(keyword)


def test_stopwords_only_gives_no_filter():
    assert not keyword_filter("the for")


async def test_plural_keyword_with_budget_finds_products(script_agent):
    """Regression: 'men's shirts under 2000' used to return nothing."""
    from app.chatbot.pipeline import run_chat
    script_agent({"category": "men", "keyword": "shirts", "max_price": 2000}, "Here are men's shirts under ₹2000!")
    reply = await run_chat("men's shirts under 2000")
    assert reply["type"] == "products"
    assert names(reply) == ["Striped Polo Shirt", "Sky Blue Linen Shirt"]  # cheapest first, all under budget


async def test_category_filter_is_exact(script_agent):
    from app.chatbot.pipeline import run_chat
    script_agent({"category": "WOMEN"})
    reply = await run_chat("women's clothes")
    assert set(names(reply)) == {"Red Floral Dress", "Pink Cotton Kurti"}


async def test_price_range(script_agent):
    from app.chatbot.pipeline import run_chat
    script_agent({"min_price": 600, "max_price": 1300})
    reply = await run_chat("something between 600 and 1300")
    assert all(600 <= p["price"] <= 1300 for p in reply["data"])
    assert [p["price"] for p in reply["data"]] == sorted(p["price"] for p in reply["data"])


async def test_nothing_in_budget_tells_the_model_what_exists(script_agent):
    from app.chatbot.pipeline import run_chat
    script_agent({"keyword": "jacket", "max_price": 1000}, "{tool}")
    reply = await run_chat("jackets under 1000")
    assert reply["type"] == "text"
    assert "No products found in that price range" in reply["message"]
    assert "₹3,499" in reply["message"]


async def test_results_carry_ids_and_image_urls_not_raw_data(script_agent):
    from app.chatbot.pipeline import run_chat
    script_agent({"keyword": "kurti"})
    product = (await run_chat("kurti"))["data"][0]
    assert len(product["id"]) == 24
    assert product["image"].startswith("data:image/jpeg;base64,")
    assert "image_data" not in product and "_id" not in product
