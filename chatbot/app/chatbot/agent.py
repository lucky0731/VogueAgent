"""
The Pydantic AI shopping agent: system prompt, dependencies, and its
`search_products` tool for querying the store's MongoDB catalog.

Routed through Portkey when configured (see utils/llm_gateway.py), otherwise
talks to Groq directly.
"""
from typing import List, Optional, Dict, Any

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.fallback import FallbackModel
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider

from ..config import REFUSAL_MESSAGE, settings
from ..database import products_collection
from ..utils.images import resolve_image_field
from ..utils.mongo import case_insensitive_exact, keyword_filter, price_range_filter
from ..utils.llm_gateway import (
    PORTKEY_API_KEY,
    PORTKEY_BASE_URL,
    is_groq_key_configured,
    is_portkey_configured,
    resolve_model_name,
)

RAW_AGENT_MODEL = settings.agent_model_name

SYSTEM_PROMPT = (
    "You are a friendly shopping assistant for The House of Hem — an online clothing store. "
    "The store has 3 categories: men, women, and kids."
    "\n\n"
    "RULES:\n"
    "1. If the user greets you or asks who you are → reply naturally and warmly.\n"
    "2. If the user wants to browse, find, or buy products → ALWAYS call the `search_products` tool with the right filters. Never describe products yourself.\n"
    "3. After calling `search_products`, base your reply ONLY on what the tool returned. If it found products, "
    "confirm briefly what you searched for (e.g. 'Here are men's shirts under ₹2000!') — the products are shown "
    "to the customer as cards, so don't list them. If it found nothing, say so plainly (never start with 'Here are') "
    "and offer the closest alternative the tool suggests.\n"
    "4. Pass the product type as a short singular keyword ('shirt', 'dress', 'jeans'); put men/women/kids in "
    "`category` and budgets in `min_price`/`max_price`, not in the keyword.\n"
    f"5. If the user asks something completely unrelated to shopping or clothes, reply: '{REFUSAL_MESSAGE}'\n"
    "6. DO NOT make up product names, prices, or details ever."
)


class StoreDeps(BaseModel):
    """Side-channel for a single agent run: the products `search_products` found."""
    found_products: List[Dict[str, Any]] = []


DIRECT_GROQ_MODEL = f"groq:{RAW_AGENT_MODEL}"

if is_portkey_configured():
    portkey_model = OpenAIChatModel(
        model_name=resolve_model_name(RAW_AGENT_MODEL),
        provider=OpenAIProvider(
            base_url=PORTKEY_BASE_URL, api_key=PORTKEY_API_KEY),
    )
    # If the Portkey call fails (wrong provider slug, gateway down, quota…),
    # retry the same model directly on Groq so chat keeps working.
    agent_model = (
        FallbackModel(portkey_model, DIRECT_GROQ_MODEL)
        if is_groq_key_configured() else portkey_model
    )
else:
    agent_model = DIRECT_GROQ_MODEL

# Live evaluation is optional (see backend/chatbot/online_evals.py). Imported only
# when enabled, so the standalone chatbot POC can ship this file unchanged without
# depending on pydantic-evals.
_capabilities = []
if settings.online_evals_enabled:
    from .online_evals import online_evaluation

    _capabilities = [online_evaluation]

agent = Agent(
    agent_model,
    name="chatbot",
    deps_type=StoreDeps,
    capabilities=_capabilities,
    system_prompt=SYSTEM_PROMPT,
)


@agent.tool
def search_products(
    ctx: RunContext[StoreDeps],
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    max_price: Optional[int] = None,
    min_price: Optional[int] = None,
) -> str:
    """
    Search the store's product database.

    Args:
        category: Filter by category — one of 'men', 'women', 'kids'.
        keyword: Product type or style, e.g. 'shirt', 'dress', 'jacket', 'floral'. Singular is best.
        max_price: Maximum price in rupees (e.g. 2000 means under ₹2000).
        min_price: Minimum price in rupees.

    Returns:
        A short confirmation string of what was found.
    """
    base: Dict[str, Any] = {}
    if category:
        base["category"] = case_insensitive_exact(category.strip())
    words = keyword_filter(keyword) if keyword else None
    if words:
        base.update(words)

    query = dict(base)
    price_filter = price_range_filter(min_price, max_price)
    if price_filter:
        query["price"] = price_filter

    raw_results = list(products_collection.find(query).sort("price", 1).limit(8))

    processed = []
    for r in raw_results:
        r["id"] = str(r["_id"])
        r.pop("_id", None)
        resolve_image_field(r)
        processed.append(r)

    # Store results so the endpoint can send them to the frontend
    ctx.deps.found_products = processed

    if processed:
        return f"Found {len(processed)} products matching the request."

    # Nothing in budget: tell the model what the closest options are, so it can
    # suggest something useful instead of a dead end. (Not shown as cards.)
    if price_filter:
        nearby = list(products_collection.find(base, {"name": 1, "price": 1}).sort("price", 1).limit(50))
        if nearby:
            prices = sorted(p["price"] for p in nearby)
            return (
                "No products found in that price range. Without the price limit there are "
                f"{len(nearby)} matching products, priced from ₹{prices[0]:,.0f} to ₹{prices[-1]:,.0f}."
            )
    return "No products found matching those filters."
