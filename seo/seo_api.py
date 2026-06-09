import os
import sys
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from keyword_generator import generate_keywords, generate_keywords_bulk, format_for_etsy
from listing_writer import write_listing, write_listings_bulk, save_listing
from competitor_scraper import run_competitor_analysis
from keyword_cluster import run_keyword_clustering

# ─────────────────────────────────────────────────────────────
# FastAPI app
# ─────────────────────────────────────────────────────────────

app = FastAPI(
    title       = "Chikan Diaries — SEO API",
    description = "Module 1: AI-powered SEO tools for Chikankari product listings",
    version     = "1.0.0"
)

# Allow requests from your frontend / Streamlit dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins  = ["*"],
    allow_methods  = ["*"],
    allow_headers  = ["*"],
)


# ─────────────────────────────────────────────────────────────
# Request / Response models
# ─────────────────────────────────────────────────────────────

class KeywordRequest(BaseModel):
    product_name : str
    product_type : Optional[str] = "chikankari"
    n            : Optional[int] = 10

class BulkKeywordRequest(BaseModel):
    products : list[str]

class ListingRequest(BaseModel):
    product_name    : str
    product_details : Optional[dict] = None

class BulkListingRequest(BaseModel):
    products : list[dict]   # each: { "name": "...", "details": {...} }

class CompetitorRequest(BaseModel):
    product_name : str

class ClusterRequest(BaseModel):
    keywords      : list[str]
    k             : Optional[int] = None
    label_with_ai : Optional[bool] = True


# ─────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "module"  : "Module 1 — SEO Engine",
        "status"  : "running",
        "endpoints": [
            "POST /seo/keywords",
            "POST /seo/keywords/bulk",
            "POST /seo/keywords/etsy-tags",
            "POST /seo/listing",
            "POST /seo/listing/bulk",
            "POST /seo/competitors",
            "POST /seo/cluster",
            "GET  /seo/health",
        ]
    }


@app.get("/seo/health")
def health():
    """Quick check that the API and env vars are loaded."""
    return {
        "status"         : "ok",
        "gemini_key_set" : bool(os.getenv("GEMINI_API_KEY")),
        "etsy_key_set"   : bool(os.getenv("ETSY_API_KEY")),
        "serpapi_key_set": bool(os.getenv("SERPAPI_KEY")),
    }


# ── Keywords ─────────────────────────────────────────────────

@app.post("/seo/keywords")
def get_keywords(req: KeywordRequest):
    """
    Generate SEO keywords for a single product.

    Example body:
    {
        "product_name": "white chikankari kurta",
        "product_type": "chikankari",
        "n": 10
    }
    """
    try:
        result = generate_keywords(req.product_name, req.product_type, req.n)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/seo/keywords/bulk")
def get_keywords_bulk(req: BulkKeywordRequest):
    """
    Generate keywords for multiple products at once.

    Example body:
    {
        "products": ["white chikankari kurta", "pink anarkali suit"]
    }
    """
    try:
        results = generate_keywords_bulk(req.products)
        return {"success": True, "count": len(results), "data": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/seo/keywords/etsy-tags")
def get_etsy_tags(req: KeywordRequest):
    """
    Generate keywords and return them pre-formatted as Etsy tags
    (13 tags max, each under 20 characters, comma-separated).
    """
    try:
        keyword_dict = generate_keywords(req.product_name, req.product_type, req.n)
        etsy_tags    = format_for_etsy(keyword_dict)
        return {
            "success"  : True,
            "product"  : req.product_name,
            "etsy_tags": etsy_tags,
            "raw"      : keyword_dict
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Listings ─────────────────────────────────────────────────

@app.post("/seo/listing")
def get_listing(req: ListingRequest):
    """
    Generate a full Etsy listing (title + description + tags).

    Example body:
    {
        "product_name": "pink chikankari anarkali suit",
        "product_details": {
            "color": "blush pink",
            "fabric": "pure georgette",
            "occasion": "wedding, festive",
            "size_range": "XS to 3XL",
            "price_usd": 85
        }
    }
    """
    try:
        listing = write_listing(req.product_name, req.product_details)
        save_listing(listing)
        return {"success": True, "data": listing}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/seo/listing/bulk")
def get_listings_bulk(req: BulkListingRequest):
    """
    Generate listings for multiple products at once.

    Example body:
    {
        "products": [
            { "name": "white chikankari kurta", "details": {} },
            { "name": "embroidered dupatta",    "details": { "fabric": "cotton" } }
        ]
    }
    """
    try:
        listings = write_listings_bulk(req.products)
        for listing in listings:
            save_listing(listing)
        return {"success": True, "count": len(listings), "data": listings}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Competitors ───────────────────────────────────────────────

@app.post("/seo/competitors")
def get_competitors(req: CompetitorRequest):
    """
    Scrape competitor listings and return analysis.

    Example body:
    { "product_name": "chikankari kurta" }
    """
    try:
        data = run_competitor_analysis(req.product_name)
        # Remove raw results to keep response clean — just analysis
        return {
            "success" : True,
            "product" : req.product_name,
            "analysis": data["analysis"],
            "sample_listings": data["results"][:5]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Clustering ────────────────────────────────────────────────

@app.post("/seo/cluster")
def get_clusters(req: ClusterRequest):
    """
    Cluster a list of keywords into topic groups using K-Means.
    Returns clusters with AI-generated labels.
    Plot is saved to data/outputs/keyword_clusters.png.

    Example body:
    {
        "keywords": ["chikankari kurta", "wedding outfit", "cotton fabric", ...],
        "k": null,
        "label_with_ai": true
    }
    """
    try:
        result = run_keyword_clustering(
            keywords      = req.keywords,
            k             = req.k,
            label_with_ai = req.label_with_ai,
            plot          = False        # no GUI in API mode
        )

        # Strip numpy arrays before returning JSON
        clean = {
            "k_used"     : result["k_used"],
            "silhouette" : result["silhouette"],
            "clusters"   : result["clusters"],
            "assignments": result["assignments"],
        }

        return {"success": True, "data": clean}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────────────────────
# Run directly for testing
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("=" * 55)
    print("  Chikan Diaries — SEO API")
    print("=" * 55)
    print("\n  Swagger docs → http://127.0.0.1:8000/docs")
    print("  Health check → http://127.0.0.1:8000/seo/health\n")
    uvicorn.run("seo_api:app", host="127.0.0.1", port=8000, reload=True)
