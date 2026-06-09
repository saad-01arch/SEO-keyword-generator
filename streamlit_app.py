import os
import sys
import json
import streamlit as st

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ─────────────────────────────────────────────────────────────
# Page config — must be first Streamlit call
# ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title = "Chikan Diaries AI — SEO Engine",
    page_icon  = "🧵",
    layout     = "wide",
    initial_sidebar_state = "expanded"
)

# ─────────────────────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .stApp { background-color: #0e0e0e; color: #f0ede6; }
    section[data-testid="stSidebar"] {
        background-color: #141414;
        border-right: 1px solid #2a2a2a;
    }
    .cd-card {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 12px;
        padding: 20px 24px;
        margin-bottom: 16px;
    }
    .cd-result {
        background: #111;
        border: 1px solid #333;
        border-left: 3px solid #c9a96e;
        border-radius: 8px;
        padding: 16px 20px;
        margin-top: 12px;
        font-size: 14px;
        line-height: 1.7;
        white-space: pre-wrap;
    }
    .cd-tag {
        display: inline-block;
        background: #2a2218;
        color: #c9a96e;
        border: 1px solid #c9a96e44;
        border-radius: 20px;
        padding: 3px 12px;
        margin: 3px;
        font-size: 12px;
    }
    .cd-section-title {
        font-size: 13px;
        font-weight: 600;
        color: #c9a96e;
        text-transform: uppercase;
        letter-spacing: .08em;
        margin-bottom: 8px;
    }
    .cd-metric {
        background: #1a1a1a;
        border: 1px solid #2a2a2a;
        border-radius: 10px;
        padding: 14px 18px;
        text-align: center;
    }
    .cd-metric-value { font-size: 24px; font-weight: 600; color: #c9a96e; }
    .cd-metric-label { font-size: 11px; color: #888; margin-top: 2px; }
    .stButton > button {
        background: #c9a96e !important;
        color: #0e0e0e !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 10px 28px !important;
    }
    .stButton > button:hover { background: #e0c080 !important; }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div {
        background: #1a1a1a !important;
        border: 1px solid #333 !important;
        color: #f0ede6 !important;
        border-radius: 8px !important;
    }
    #MainMenu { visibility: hidden; }
    footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# USD to INR rate — fetch live or fallback to fixed
# ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def get_usd_to_inr():
    try:
        import requests
        r = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5)
        return r.json()["rates"]["INR"]
    except Exception:
        return 83.5  # fallback rate

USD_TO_INR = get_usd_to_inr()


def to_inr(usd_val):
    try:
        return f"₹{round(float(usd_val) * USD_TO_INR):,}"
    except Exception:
        return "N/A"


# ─────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🧵 Chikan Diaries AI")
    st.markdown("<div style='color:#888;font-size:13px;margin-bottom:24px'>SEO Engine — Module 1</div>",
                unsafe_allow_html=True)

    page = st.radio(
        "Navigate",
        options=[
            "🏠  Overview",
            "🔍  Keyword Generator",
            "✍️  Listing Writer",
            "🕵️  Competitor Analysis",
            "🗂️  Keyword Clusters",
        ],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown(f"<div style='color:#555;font-size:11px'>Powered by Gemini 1.5 Flash<br>Built for Chikan Diaries, Lucknow<br><br>USD→INR rate: ₹{USD_TO_INR}</div>",
                unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Lazy imports
# ─────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def load_keyword_generator():
    from keyword_generator import generate_keywords, format_for_etsy
    return generate_keywords, format_for_etsy

@st.cache_resource(show_spinner=False)
def load_listing_writer():
    from listing_writer import write_listing
    return write_listing

@st.cache_resource(show_spinner=False)
def load_competitor_scraper():
    from competitor_scraper import run_competitor_analysis
    return run_competitor_analysis

@st.cache_resource(show_spinner=False)
def load_clusterer():
    from keyword_cluster import run_keyword_clustering
    return run_keyword_clustering


# ─────────────────────────────────────────────────────────────
# PAGE 1 — Overview
# ─────────────────────────────────────────────────────────────

if "Overview" in page:
    st.markdown("# 🧵 Chikan Diaries AI — SEO Engine")
    st.markdown("<div style='color:#888;margin-bottom:32px'>AI-powered SEO automation for Lucknowi Chikankari on Etsy</div>",
                unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        ("🔍", "Keyword Generator", "Gemini API + NLP"),
        ("✍️", "Listing Writer",    "Title + Desc + Tags"),
        ("🕵️", "Competitor Scraper","Live Etsy Analysis"),
        ("🗂️", "Keyword Clusters",  "K-Means + Embeddings"),
    ]
    for col, (icon, title, sub) in zip([col1,col2,col3,col4], metrics):
        with col:
            st.markdown(f"""
            <div class='cd-metric'>
                <div style='font-size:28px'>{icon}</div>
                <div style='font-size:14px;font-weight:600;color:#f0ede6;margin-top:6px'>{title}</div>
                <div class='cd-metric-label'>{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("### What this project does")
        st.markdown("""
This system automates the most time-consuming parts of running an Etsy shop
for a handcrafted Chikankari business:

- **Keyword research** — generate buyer-intent keywords for any product in seconds
- **Listing writing** — produce complete, SEO-optimised Etsy listings automatically
- **Competitor analysis** — see what top sellers are doing and how they price

        """)
    with col_b:
        st.markdown("### Tech stack")
        st.markdown("""
| Layer | Technology |
|---|---|
| LLM | Gemini 1.5 Flash |


| API | FastAPI + Pydantic |
| UI | Streamlit |
| Data | Etsy API, SerpAPI |
        """)

    st.markdown("---")
    st.markdown("<div style='color:#555;font-size:12px;text-align:center'>Use the sidebar to navigate between tools ←</div>",
                unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# PAGE 2 — Keyword Generator
# ─────────────────────────────────────────────────────────────

elif "Keyword" in page and "Cluster" not in page:
    st.markdown("# 🔍 Keyword Generator")
    st.markdown("<div style='color:#888;margin-bottom:24px'>Generate SEO keywords for any Chikankari product using Gemini</div>",
                unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        product_name = st.text_input("Product name", placeholder="e.g. white chikankari kurta")
    with col2:
        n_keywords = st.slider("Number of keywords", 5, 20, 10)

    run_btn = st.button("Generate Keywords ✨", disabled=not product_name)

    if run_btn and product_name:
        with st.spinner("Generating keywords with Gemini..."):
            generate_keywords, format_for_etsy = load_keyword_generator()
            result = generate_keywords(product_name, n=n_keywords)

        st.success("Done!")
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.markdown("<div class='cd-section-title'>Short Keywords</div>", unsafe_allow_html=True)
            tags_html = "".join(f"<span class='cd-tag'>{kw}</span>" for kw in result["keywords"])
            st.markdown(tags_html, unsafe_allow_html=True)

        with col_b:
            st.markdown("<div class='cd-section-title'>Long-tail Phrases</div>", unsafe_allow_html=True)
            for lt in result["long_tail"]:
                st.markdown(f"<span class='cd-tag'>{lt}</span>", unsafe_allow_html=True)

        with col_c:
            st.markdown("<div class='cd-section-title'>Negative Keywords</div>", unsafe_allow_html=True)
            for neg in result["negative"]:
                st.markdown(f"<span class='cd-tag' style='color:#e07070;border-color:#e0707044;background:#1e1010'>{neg}</span>",
                            unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("<div class='cd-section-title'>Etsy Tags (ready to paste)</div>", unsafe_allow_html=True)
        etsy_tags = format_for_etsy(result)
        st.code(etsy_tags, language=None)

        with st.expander("View raw JSON"):
            st.json(result)


# ─────────────────────────────────────────────────────────────
# PAGE 3 — Listing Writer
# ─────────────────────────────────────────────────────────────

elif "Listing" in page:
    st.markdown("# ✍️ Listing Writer")
    st.markdown("<div style='color:#888;margin-bottom:24px'>Generate a complete Etsy listing — title, description, and tags</div>",
                unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Product Info")
        product_name = st.text_input("Product name *", placeholder="e.g. pink chikankari anarkali suit")
        color        = st.text_input("Color",           placeholder="e.g. blush pink")
        fabric       = st.text_input("Fabric",          placeholder="e.g. pure georgette")
    with col2:
        st.markdown("#### More Details")
        occasion   = st.text_input("Occasion",    placeholder="e.g. wedding, festive, party wear")
        size_range = st.text_input("Size range",  placeholder="e.g. XS to 3XL, custom available")
        price_usd  = st.number_input("Price (USD)", min_value=0, max_value=500, value=0)

    if price_usd > 0:
        st.caption(f"≈ {to_inr(price_usd)} at current rate (₹{USD_TO_INR}/USD)")

    run_btn = st.button("Write Listing ✨", disabled=not product_name)

    if run_btn and product_name:
        details = {}
        if color:      details["color"]      = color
        if fabric:     details["fabric"]     = fabric
        if occasion:   details["occasion"]   = occasion
        if size_range: details["size_range"] = size_range
        if price_usd:  details["price_usd"]  = price_usd

        with st.spinner("Generating keywords then writing your listing..."):
            write_listing = load_listing_writer()
            listing = write_listing(product_name, details if details else None)

        st.success("Listing ready!")

        st.markdown("<div class='cd-section-title'>Title</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='cd-result'>{listing['title']}</div>", unsafe_allow_html=True)
        char_count = len(listing['title'])
        st.caption(f"{char_count}/140 characters {'✅' if char_count <= 140 else '⚠️ too long'}")

        st.markdown("<div class='cd-section-title' style='margin-top:16px'>Etsy Tags</div>",
                    unsafe_allow_html=True)
        tags_html = "".join(f"<span class='cd-tag'>{t.strip()}</span>" for t in listing['tags'].split(","))
        st.markdown(tags_html, unsafe_allow_html=True)

        st.markdown("<div class='cd-section-title' style='margin-top:16px'>Description</div>",
                    unsafe_allow_html=True)
        st.markdown(f"<div class='cd-result'>{listing['description']}</div>", unsafe_allow_html=True)

        st.download_button(
            label    = "⬇️ Download as JSON",
            data     = json.dumps(listing, indent=2, ensure_ascii=False),
            file_name= f"{product_name.replace(' ','_')}_listing.json",
            mime     = "application/json"
        )


# ─────────────────────────────────────────────────────────────
# PAGE 4 — Competitor Analysis
# ─────────────────────────────────────────────────────────────

elif "Competitor" in page:
    st.markdown("# 🕵️ Competitor Analysis")
    st.markdown("<div style='color:#888;margin-bottom:24px'>See what top Etsy sellers are doing for any product</div>",
                unsafe_allow_html=True)

    product_name = st.text_input("Product to research", placeholder="e.g. chikankari kurta")
    run_btn      = st.button("Analyse Competitors 🔎", disabled=not product_name)

    if run_btn and product_name:
        with st.spinner("Scraping competitor listings..."):
            run_competitor_analysis = load_competitor_scraper()
            data = run_competitor_analysis(product_name)

        analysis = data["analysis"]
        results  = data["results"]

        st.success(f"Found {analysis['total_scraped']} competitor listings!")

        # ── Price metrics in INR ──────────────────────────────
        if analysis.get("price_range"):
            pr = analysis["price_range"]
            c1, c2, c3, c4 = st.columns(4)
            for col, label, val in zip(
                [c1, c2, c3, c4],
                ["Min Price (INR)", "Max Price (INR)", "Avg Price (INR)", "Listings Found"],
                [
                    to_inr(pr.get("min", 0)),
                    to_inr(pr.get("max", 0)),
                    to_inr(pr.get("average", 0)),
                    analysis["total_scraped"]
                ]
            ):
                with col:
                    st.markdown(f"""
                    <div class='cd-metric'>
                        <div class='cd-metric-value'>{val}</div>
                        <div class='cd-metric-label'>{label}</div>
                    </div>""", unsafe_allow_html=True)

            st.caption(f"Prices converted at ₹{USD_TO_INR} per USD")

        st.markdown("---")
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("#### 🏆 Top Performing Titles")
            for i, title in enumerate(analysis.get("top_titles", []), 1):
                st.markdown(f"<div class='cd-result'><b>{i}.</b> {title}</div>",
                            unsafe_allow_html=True)

        with col_right:
            st.markdown("#### 📊 Most Common Title Words")
            words = analysis.get("common_words", [])
            if words:
                import pandas as pd
                import plotly.express as px
                df = pd.DataFrame(words[:12], columns=["Word", "Count"])
                fig = px.bar(
                    df, x="Count", y="Word", orientation="h",
                    color="Count", color_continuous_scale="Oranges",
                    template="plotly_dark"
                )
                fig.update_layout(
                    paper_bgcolor="#0e0e0e", plot_bgcolor="#0e0e0e",
                    margin=dict(l=0, r=0, t=0, b=0),
                    showlegend=False, coloraxis_showscale=False,
                    yaxis=dict(autorange="reversed")
                )
                st.plotly_chart(fig, use_container_width=True)

        # ── Raw listings table with seller + INR price ────────
        if results:
            st.markdown("#### All Scraped Listings")
            import pandas as pd

            rows = []
            for r in results:
                # Seller: prefer 'seller', fallback to 'source', fallback to 'Unknown'
                seller = (
                    r.get("seller") or
                    r.get("source") or
                    "Unknown"
                )
                # Price in INR
                raw_price = r.get("price", "")
                price_str = str(raw_price).replace("$", "").replace(",", "").strip()
                try:
                    price_inr = f"₹{round(float(price_str) * USD_TO_INR):,}"
                except Exception:
                    price_inr = "N/A"

                rows.append({
                    "Title"       : r.get("title", ""),
                    "Price (INR)" : price_inr,
                    "Seller/Source": seller,
                    "Link"        : r.get("link", r.get("url", "")),
                })

            df = pd.DataFrame(rows)
            st.dataframe(df, use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────
# PAGE 5 — Keyword Clusters
# ─────────────────────────────────────────────────────────────

elif "Cluster" in page:
    st.markdown("# 🗂️ Keyword Clusters")
    st.markdown("<div style='color:#888;margin-bottom:24px'>Group keywords by theme using K-Means + sentence embeddings</div>",
                unsafe_allow_html=True)

    st.markdown("#### Enter your keywords")
    st.caption("Paste one keyword per line, or comma-separated")

    default_kws = """chikankari kurta, embroidered kurta, white kurta
cotton kurta, georgette kurta, silk kurta
wedding outfit, bridal wear, festive dress
party wear, occasion wear, ethnic wear
handmade clothing, hand embroidered, artisan made
lucknow chikankari, traditional indian wear, indian ethnic
summer kurta, casual kurta, daily wear
anarkali suit, straight kurta, a-line kurta
gift for her, diwali gift, eid outfit"""

    raw_input = st.text_area("Keywords", value=default_kws, height=180)

    col1, col2 = st.columns(2)
    with col1:
        k_mode = st.radio("Number of clusters", ["Auto-detect (recommended)", "Manual"], horizontal=True)
    with col2:
        k_manual = st.slider("K (if manual)", 2, 10, 4,
                             disabled=(k_mode == "Auto-detect (recommended)"))

    label_ai = st.checkbox("Label clusters with Gemini AI", value=True)
    run_btn  = st.button("Run Clustering 🧠", disabled=not raw_input.strip())

    if run_btn and raw_input.strip():
        raw_lines = raw_input.replace("\n", ",").split(",")
        keywords  = [kw.strip() for kw in raw_lines if kw.strip()]
        keywords  = list(dict.fromkeys(keywords))

        st.info(f"Clustering {len(keywords)} unique keywords...")
        k = None if k_mode == "Auto-detect (recommended)" else k_manual

        with st.spinner("Embedding keywords and running K-Means..."):
            run_keyword_clustering = load_clusterer()
            result = run_keyword_clustering(
                keywords      = keywords,
                k             = k,
                label_with_ai = label_ai,
                plot          = False
            )

        st.success(f"Done! Found {result['k_used']} clusters  |  Silhouette Score: {result['silhouette']}")

        score = result["silhouette"]
        if score > 0.5:
            quality = "🟢 Strong separation"
        elif score > 0.25:
            quality = "🟡 Moderate separation"
        else:
            quality = "🔴 Weak separation — try fewer clusters"
        st.caption(f"Silhouette Score: {score} — {quality}")

        st.markdown("---")

        clusters = result["clusters"]
        cols = st.columns(min(len(clusters), 3))

        for idx, (cid, data) in enumerate(clusters.items()):
            with cols[idx % 3]:
                label     = data.get("label", f"Cluster {cid}")
                kws       = data["keywords"]
                rep       = data["centroid_keyword"]
                tags_html = "".join(f"<span class='cd-tag'>{kw}</span>" for kw in kws)
                st.markdown(f"""
                <div class='cd-card'>
                    <div class='cd-section-title'>{label}</div>
                    <div style='font-size:11px;color:#888;margin-bottom:10px'>
                        Representative: <span style='color:#c9a96e'>{rep}</span>
                        &nbsp;·&nbsp; {len(kws)} keywords
                    </div>
                    {tags_html}
                </div>""", unsafe_allow_html=True)

       # st.markdown("#### Cluster Visualization (PCA → 2D)")
        try:
            import numpy as np
            import plotly.express as px
            import pandas as pd
            from sklearn.decomposition import PCA

            embeddings = result["embeddings"]
            labels_arr = result["labels"]
            pca        = PCA(n_components=2, random_state=42)
            coords     = pca.fit_transform(embeddings)

            cluster_labels = [
                clusters[l].get("label", f"Cluster {l}")
                for l in labels_arr
            ]

            df_plot = pd.DataFrame({
                "x"      : coords[:, 0],
                "y"      : coords[:, 1],
                "keyword": keywords,
                "cluster": cluster_labels
            })

            fig = px.scatter(
                df_plot, x="x", y="y",
                color="cluster", text="keyword",
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig.update_traces(
                textposition="top center",
                textfont=dict(size=9),
                marker=dict(size=10)
            )
            fig.update_layout(
                paper_bgcolor="#0e0e0e",
                plot_bgcolor ="#111",
                legend=dict(bgcolor="#1a1a1a", bordercolor="#333"),
                margin=dict(l=0, r=0, t=10, b=0),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            )
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not render plot: {e}")

        clean = {k: v for k, v in result.items() if k not in ("embeddings", "labels")}
        st.download_button(
            label    = "⬇️ Download Cluster Data",
            data     = json.dumps(clean, indent=2, ensure_ascii=False),
            file_name= "keyword_clusters.json",
            mime     = "application/json"
        )
