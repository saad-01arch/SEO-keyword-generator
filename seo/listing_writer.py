import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from keyword_generator import generate_keywords, format_for_etsy

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-3.1-flash-lite")


def write_listing(product_name: str, product_details: dict = None) -> dict:
    """
    Generate a complete Etsy listing for a Chikankari product.

    Args:
        product_name    : e.g. "white chikankari kurta"
        product_details : optional dict with extra context, e.g.:
                          {
                            "color": "white",
                            "fabric": "cotton",
                            "occasion": "casual, festive",
                            "size_range": "XS to 3XL",
                            "price_usd": 45
                          }

    Returns:
        dict with keys:
            - title         : Etsy listing title (max 140 chars)
            - description   : full listing description (HTML-friendly)
            - tags          : 13 Etsy tags as a comma-separated string
            - keywords_used : raw keyword dict from keyword_generator
    """

    # Step 1: Generate keywords first, feed them into the listing prompt
    print(f"  → Generating keywords for: {product_name}")
    keyword_dict = generate_keywords(product_name)
    keywords     = keyword_dict["keywords"]
    long_tail    = keyword_dict["long_tail"]
    etsy_tags    = format_for_etsy(keyword_dict)

    # Step 2: Build extra context string if product_details provided
    details_str = ""
    if product_details:
        details_str = "\n".join(
            f"- {k.replace('_', ' ').title()}: {v}"
            for k, v in product_details.items()
        )
    else:
        details_str = "- No extra details provided. Use general chikankari context."

    # Step 3: Prompt Gemini to write the listing
    prompt = f"""
You are an expert Etsy copywriter specialising in handcrafted Indian ethnic wear.

Write a complete Etsy product listing for:
Product: "{product_name}"
Category: Chikankari embroidery — handcrafted in Lucknow, India

Product details:
{details_str}

SEO keywords to naturally include:
Short keywords: {', '.join(keywords)}
Long-tail phrases: {', '.join(long_tail)}

Return ONLY a valid JSON object with exactly these keys:
{{
  "title": "Etsy listing title — max 140 characters, include top 2-3 keywords naturally",
  "description": "Full listing description — 200 to 300 words. Structure it as:\\n\\n✨ Opening hook (1-2 lines)\\n\\n📦 Product details (bullet points)\\n\\n🧵 About the craft (2-3 lines about Lucknowi chikankari)\\n\\n🌍 Shipping & sizing info (2-3 lines)\\n\\n💌 Closing line inviting the buyer"
}}

Rules:
- Title must be under 140 characters
- Description must use the bullet point structure above
- Weave in keywords naturally — do NOT keyword-stuff
- Tone: warm, premium, culturally proud — not generic
- Write for international buyers (USA, UK, Canada, Australia)
- No markdown in JSON values, use plain text with the emoji structure
- No explanation outside the JSON
"""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    result          = json.loads(raw)
    result["tags"]  = etsy_tags
    result["keywords_used"] = keyword_dict

    return result


def write_listings_bulk(products: list[dict]) -> list[dict]:
    """
    Generate listings for multiple products at once.

    Args:
        products : list of dicts, each with:
                   { "name": "...", "details": {...} }

    Returns:
        list of listing dicts
    """
    listings = []
    for i, p in enumerate(products, 1):
        print(f"\n[{i}/{len(products)}] Writing listing for: {p['name']}")
        listing = write_listing(p["name"], p.get("details"))
        listings.append(listing)
    return listings


def save_listing(listing: dict, filename: str = None) -> str:
    """
    Save a listing dict to a JSON file in data/outputs/.

    Returns the saved file path.
    """
    os.makedirs("data/outputs", exist_ok=True)

    if not filename:
        safe_name = listing.get("title", "listing")[:40]
        safe_name = "".join(c if c.isalnum() or c in " _-" else "" for c in safe_name)
        safe_name = safe_name.strip().replace(" ", "_").lower()
        filename  = f"data/outputs/{safe_name}.json"

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(listing, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Saved to {filename}")
    return filename


# ── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":

    print("=" * 55)
    print("  Chikan Diaries — Listing Writer")
    print("=" * 55)

    # Test 1: Basic listing with no extra details
    print("\n[Test 1] Basic listing — no extra product details")
    listing = write_listing("white chikankari kurta")

    print(f"\nTITLE:\n{listing['title']}")
    print(f"\nTAGS:\n{listing['tags']}")
    print(f"\nDESCRIPTION:\n{listing['description']}")

    # Test 2: Listing with full product details
    print("\n" + "=" * 55)
    print("[Test 2] Detailed listing — with product context")
    listing2 = write_listing(
        "pink chikankari anarkali suit",
        product_details={
            "color"      : "blush pink",
            "fabric"     : "pure georgette",
            "occasion"   : "wedding, festive, party wear",
            "size_range" : "XS to 3XL, custom sizing available",
            "price_usd"  : 85
        }
    )

    print(f"\nTITLE:\n{listing2['title']}")
    print(f"\nTAGS:\n{listing2['tags']}")
    print(f"\nDESCRIPTION:\n{listing2['description']}")

    # Test 3: Save to file
    print("\n" + "=" * 55)
    print("[Test 3] Saving listing to data/outputs/")
    path = save_listing(listing2)
    print(f"Saved: {path}")
