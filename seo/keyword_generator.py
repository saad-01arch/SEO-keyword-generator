import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
print(os.getenv("GEMINI_API_KEY"))  # Debug: Check if API key is loaded
genai.configure(api_key= os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-3.1-flash-lite")


def generate_keywords(product_name: str, product_type: str = "chikankari", n: int = 10) -> dict:
    """
    Generate SEO keywords for a given product using Gemini.

    Args:
        product_name  : e.g. "white chikankari kurta"
        product_type  : context hint, default "chikankari"
        n             : how many keywords to return (default 10)

    Returns:
        dict with keys:
            - product       : original input
            - keywords      : list of keyword strings
            - long_tail     : list of longer 3-5 word phrases
            - negative      : keywords to AVOID in ads
    """

    prompt = f"""
You are an expert Etsy SEO specialist for handcrafted Indian clothing.

Generate SEO keywords for this product listed on Etsy:
Product: "{product_name}"
Category: {product_type}
Target market: International buyers (USA, UK, Canada, Australia)

Return ONLY a valid JSON object with exactly these keys:
{{
  "product": "{product_name}",
  "keywords": [list of {n} short 1-3 word keywords, high search volume],
  "long_tail": [list of 5 long-tail phrases, 4-6 words each, very specific],
  "negative": [list of 5 keywords to AVOID in paid ads, irrelevant to this product]
}}

Rules:
- Keywords must be in English
- Focus on buyer intent (people ready to purchase)
- Include style, occasion, fabric, and cultural keywords
- Long-tail phrases should be very specific to chikankari / Indian ethnic wear
- No markdown, no explanation, just the raw JSON
"""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Strip markdown code fences if Gemini wraps in ```json ... ```
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result = json.loads(raw)
    return result


def generate_keywords_bulk(products: list[str]) -> list[dict]:
    """
    Run keyword generation for a list of products at once.

    Args:
        products : list of product name strings

    Returns:
        list of keyword dicts, one per product
    """
    results = []
    for product in products:
        print(f"  → Generating keywords for: {product}")
        result = generate_keywords(product)
        results.append(result)
    return results


def format_for_etsy(keyword_dict: dict) -> str:
    """
    Flatten keywords + long_tail into a single comma-separated
    Etsy tags string (max 13 tags, each under 20 chars).

    Etsy allows 13 tags per listing, each max 20 characters.
    """
    all_tags = keyword_dict["keywords"] + keyword_dict["long_tail"]

    # Filter: Etsy tag limit is 20 characters
    valid_tags = [tag for tag in all_tags if len(tag) <= 20]

    # Deduplicate while preserving order
    seen = set()
    unique_tags = []
    for tag in valid_tags:
        if tag.lower() not in seen:
            seen.add(tag.lower())
            unique_tags.append(tag)

    # Etsy max is 13 tags
    etsy_tags = unique_tags[:13]
    return ", ".join(etsy_tags)


# ── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":

    print("=" * 55)
    print("  Chikan Diaries — Keyword Generator")
    print("=" * 55)

    # Test 1: Single product
    print("\n[Test 1] Single product keyword generation")
    result = generate_keywords("white chikankari kurta", n=10)
    print(json.dumps(result, indent=2))

    # Test 2: Etsy tags formatter
    print("\n[Test 2] Etsy tag formatter output")
    etsy_tags = format_for_etsy(result)
    print(f"Etsy Tags: {etsy_tags}")

    # Test 3: Bulk generation
    print("\n[Test 3] Bulk generation for 3 products")
    products = [
        "pink chikankari anarkali suit",
        "chikankari cotton dupatta",
        "embroidered chikankari saree"
    ]
    bulk = generate_keywords_bulk(products)
    for item in bulk:
        print(f"\n  Product : {item['product']}")
        print(f"  Keywords: {', '.join(item['keywords'][:5])} ...")
        print(f"  Long-tail: {item['long_tail'][0]}")
