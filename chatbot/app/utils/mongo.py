"""
Shared MongoDB query-fragment helpers.
"""
import re


def case_insensitive_exact(value: str) -> dict:
    """Query fragment for an exact, case-insensitive string match."""
    return {"$regex": f"^{re.escape(value)}$", "$options": "i"}


def case_insensitive_contains(value: str) -> dict:
    """Query fragment for a case-insensitive substring match."""
    return {"$regex": re.escape(value), "$options": "i"}


def price_range_filter(min_price: int = None, max_price: int = None) -> dict:
    """Query fragment for a price range; empty dict if neither bound is given."""
    price_query = {}
    if min_price is not None:
        price_query["$gte"] = min_price
    if max_price is not None:
        price_query["$lte"] = max_price
    return price_query


# Words that say *who* or *how*, not *what* — the category/price filters cover these.
_STOPWORDS = {
    "a", "an", "the", "for", "and", "or", "with", "in", "of", "some", "any", "show", "me",
    "men", "mens", "man", "women", "womens", "woman", "ladies", "kids", "kid", "boys", "girls",
    "children", "child", "under", "below", "above", "over", "cheap", "new", "rs", "inr",
}
# Shoppers' words → words used in product names.
_SYNONYMS = {
    "tshirt": "t-shirt", "tee": "tee|t-shirt", "tees": "tee|t-shirt", "top": "top|blouse|t-shirt",
    "pant": "trouser|chino|jean", "pants": "trouser|chino|jean", "trousers": "trouser|chino",
    "denim": "jean", "pajama": "pajama|pyjama", "pyjama": "pajama|pyjama", "sweatshirt": "sweater|hoodie",
    "jumper": "sweater", "pullover": "sweater", "blazer": "jacket|suit", "coat": "coat|jacket",
}


def _singular(word: str) -> str:
    """Very small English de-pluraliser: shirts→shirt, dresses→dress, hoodies→hoodie."""
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y" if not word.endswith("dies") else word[:-1]
    if word.endswith(("sses", "shes", "ches", "xes")):
        return word[:-2]
    if word.endswith("s") and not word.endswith(("ss", "us")) and len(word) > 3:
        return word[:-1]
    return word


def keyword_patterns(keyword: str) -> list[str]:
    """Regex patterns for each meaningful word of `keyword` (plural-tolerant, with synonyms)."""
    words = re.findall(r"[a-z0-9-]+", (keyword or "").lower().replace("'s", ""))
    patterns = []
    for word in words:
        if word in _STOPWORDS or word.isdigit():
            continue
        patterns.append(_SYNONYMS.get(word) or _SYNONYMS.get(_singular(word)) or re.escape(_singular(word)))
    return patterns


def keyword_filter(keyword: str) -> dict | None:
    """
    Query fragment matching every meaningful word of `keyword` in the product
    name or description (case-insensitive, plural-tolerant). None if nothing
    meaningful is left (e.g. the keyword was just "men's").
    """
    clauses = []
    for pattern in keyword_patterns(keyword):
        regex = {"$regex": pattern, "$options": "i"}
        clauses.append({"$or": [{"name": regex}, {"description": regex}]})
    if not clauses:
        return None
    return clauses[0] if len(clauses) == 1 else {"$and": clauses}

