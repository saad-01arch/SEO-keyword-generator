import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
ETSY_API_KEY = os.getenv("ETSY_API_KEY")
ETSY_SHOP_ID = os.getenv("ETSY_SHOP_ID")


# ─────────────────────────────────────────────────────────────
# APPROACH 1 — Google Shopping via SerpAPI
# Searches "chikankari kurta etsy" on Google and returns
# competitor listing titles, prices, and sellers
# Free tier: 100 searches/month at serpapi.com
# ─────────────────────────────────────────────────────────────

def scrape_via_serpapi(product_name: str, num_results: int = 10) -> list[dict]:
    """
    Search Google Shopping for competitor Etsy listings.

    Args:
        product_name : e.g. "chikankari kurta"
        num_results  : how many results to return (max 20)

    Returns:
        list of dicts with keys: title, price, seller, source, link
    """
    if not SERPAPI_KEY:
        raise ValueError(
            "SERPAPI_KEY not found in .env\n"
            "Get a free key at https://serpapi.com — 100 free searches/month"
        )

    print(f"  → Searching Google Shopping for: '{product_name} etsy'")

    params = {
        "engine"  : "google_shopping",
        "q"       : f"{product_name} etsy",
        "api_key" : SERPAPI_KEY,
        "num"     : num_results,
        "gl"      : "us",      # Search from US perspective
        "hl"      : "en"
    }

    response = requests.get("https://serpapi.com/search", params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    results = []
    for item in data.get("shopping_results", []):
        results.append({
            "title"  : item.get("title", ""),
            "price"  : item.get("price", "N/A"),
            "seller" : item.get("seller", ""),
            "source" : item.get("source", ""),
            "link"   : item.get("link", ""),
            "rating" : item.get("rating", None),
            "reviews": item.get("reviews", None),
        })

    return results[:num_results]


# ─────────────────────────────────────────────────────────────
# APPROACH 2 — Etsy Official API
# Searches Etsy listings directly using their public API
# Requires an Etsy API key (free at etsy.com/developers)
# ─────────────────────────────────────────────────────────────

def scrape_via_etsy_api(product_name: str, num_results: int = 10) -> list[dict]:
    """
    Search Etsy listings using the official Etsy API v3.

    Args:
        product_name : e.g. "chikankari kurta"
        num_results  : how many listings to return (max 25)

    Returns:
        list of dicts with listing details
    """
    if not ETSY_API_KEY:
        raise ValueError(
            "ETSY_API_KEY not found in .env\n"
            "Get a free key at https://www.etsy.com/developers"
        )

    print(f"  → Searching Etsy API for: '{product_name}'")

    url = "https://openapi.etsy.com/v3/application/listings/active"
    headers = {"x-api-key": ETSY_API_KEY}
    params  = {
        "keywords" : product_name,
        "limit"    : num_results,
        "sort_on"  : "score",        # sort by relevance
    }

    response = requests.get(url, headers=headers, params=params, timeout=15)
    response.raise_for_status()
    data = response.json()

    results = []
    for item in data.get("results", []):
        results.append({
            "listing_id"  : item.get("listing_id"),
            "title"       : item.get("title", ""),
            "price"       : item.get("price", {}).get("amount", "N/A"),
            "currency"    : item.get("price", {}).get("currency_code", "USD"),
            "views"       : item.get("views", 0),
            "num_favorers": item.get("num_favorers", 0),
            "tags"        : item.get("tags", []),
            "url"         : item.get("url", ""),
        })

    return results


# ─────────────────────────────────────────────────────────────
# APPROACH 3 — No API key fallback
# If neither key is available, uses requests + BeautifulSoup
# on a publicly accessible Google search page
# Less reliable but works for quick testing
# ─────────────────────────────────────────────────────────────

def scrape_via_requests(product_name: str, num_results: int = 10) -> list[dict]:
    """
    Scrape Google search results for Etsy listings.
    Fallback when no API keys are available.
    Less stable — use SerpAPI or Etsy API for production.
    """
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        raise ImportError("Run: pip install beautifulsoup4")

    query   = f"{product_name} site:etsy.com"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }

    print(f"  → Scraping Google for: '{query}'")
    url      = f"https://www.google.com/search?q={query.replace(' ', '+')}&num={num_results}"
    response = requests.get(url, headers=headers, timeout=15)

    soup    = BeautifulSoup(response.text, "html.parser")
    results = []

    for g in soup.select("div.g")[:num_results]:
        title_tag = g.select_one("h3")
        link_tag  = g.select_one("a")
        desc_tag  = g.select_one("div.VwiC3b")

        if title_tag and link_tag:
            results.append({
                "title"      : title_tag.get_text(),
                "link"       : link_tag.get("href", ""),
                "description": desc_tag.get_text() if desc_tag else "",
                "price"      : "N/A",
                "seller"     : "unknown",
            })

    return results


# ─────────────────────────────────────────────────────────────
# ANALYSIS — extract insights from scraped results
# ─────────────────────────────────────────────────────────────

def analyze_competitors(results: list[dict]) -> dict:
    """
    Extract actionable insights from scraped competitor listings.

    Returns dict with:
        - common_words   : most frequent title words
        - price_range    : min, max, average price
        - title_patterns : observed naming conventions
        - top_titles     : 3 best-performing titles to learn from
    """
    from collections import Counter

    # Collect all title words
    stop_words = {
        "the", "a", "an", "and", "or", "for", "with", "in", "of",
        "on", "at", "to", "by", "&", "-", "|", "etsy"
    }

    all_words = []
    for r in results:
        words = r.get("title", "").lower().split()
        all_words.extend([w.strip(",.|-") for w in words if w not in stop_words and len(w) > 2])

    word_counts  = Counter(all_words)
    common_words = word_counts.most_common(15)

    # Extract prices
    prices = []
    for r in results:
        price_str = str(r.get("price", "")).replace("$", "").replace(",", "").strip()
        try:
            prices.append(float(price_str))
        except ValueError:
            pass

    price_range = {}
    if prices:
        price_range = {
            "min"    : round(min(prices), 2),
            "max"    : round(max(prices), 2),
            "average": round(sum(prices) / len(prices), 2),
            "count"  : len(prices)
        }

    # Top 3 titles (highest engagement if available, else first 3)
    sorted_results = sorted(
        results,
        key=lambda x: int(x.get("reviews") or x.get("num_favorers") or 0),
        reverse=True
    )
    top_titles = [r["title"] for r in sorted_results[:3]]

    return {
        "common_words"  : common_words,
        "price_range"   : price_range,
        "top_titles"    : top_titles,
        "total_scraped" : len(results),
    }


def run_competitor_analysis(product_name: str) -> dict:
    """
    Master function — auto-selects the best available scraping
    method and returns scraped results + analysis together.

    Priority: Etsy API → SerpAPI → requests fallback
    """
    results = []

    if ETSY_API_KEY:
        print("  Using: Etsy Official API")
        results = scrape_via_etsy_api(product_name)
    elif SERPAPI_KEY:
        print("  Using: SerpAPI Google Shopping")
        results = scrape_via_serpapi(product_name)
    else:
        print("  Using: requests fallback (no API keys found)")
        print("  Tip: Add SERPAPI_KEY or ETSY_API_KEY to .env for better results")
        results = scrape_via_requests(product_name)

    analysis = analyze_competitors(results)

    return {
        "product"  : product_name,
        "results"  : results,
        "analysis" : analysis
    }


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":

    print("=" * 55)
    print("  Chikan Diaries — Competitor Scraper")
    print("=" * 55)

    product = "chikankari kurta"

    print(f"\nRunning competitor analysis for: '{product}'")
    data = run_competitor_analysis(product)

    print(f"\n── Results ({data['analysis']['total_scraped']} listings found) ──")
    for i, r in enumerate(data["results"][:5], 1):
        print(f"\n  [{i}] {r['title']}")
        print(f"       Price  : {r.get('price', 'N/A')}")
        print(f"       Seller : {r.get('seller', r.get('source', 'N/A'))}")

    print("\n── Analysis ──")
    analysis = data["analysis"]

    print(f"\n  Price range : ${analysis['price_range'].get('min','?')} "
          f"— ${analysis['price_range'].get('max','?')} "
          f"(avg ${analysis['price_range'].get('average','?')})")

    print(f"\n  Top 15 words in competitor titles:")
    for word, count in analysis["common_words"]:
        print(f"    {word:<20} {count}x")

    print(f"\n  Top performing titles:")
    for i, t in enumerate(analysis["top_titles"], 1):
        print(f"    [{i}] {t}")

    # Save results
    os.makedirs("data/outputs", exist_ok=True)
    out_path = f"data/outputs/competitor_{product.replace(' ', '_')}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"\n  ✓ Saved to {out_path}")
