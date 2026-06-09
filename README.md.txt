# 🧵 Chikan Diaries AI — SEO Engine

> AI-powered SEO automation system for Lucknowi Chikankari on Etsy

Built as an ML & DL capstone project — and a real tool used in my
handcrafted Chikankari clothing business.

---

## 🚀 What it does

Automates the most time-consuming parts of running an Etsy shop:

- **Keyword Generator** — Gemini 1.5 Flash generates buyer-intent
  keywords, long-tail phrases, and negative keywords for any product
- **Listing Writer** — chains keyword output into a full Etsy listing
  (title + 300-word description + 13 tags)
- **Competitor Scraper** — pulls live competitor listings from Etsy
  and Google Shopping with price analysis
- **Keyword Clusters** — embeds keywords with sentence-transformers,
  clusters by theme using K-Means, visualises with PCA scatter plot

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| LLM | Gemini 1.5 Flash (Google AI) |
| Embeddings | all-MiniLM-L6-v2 (sentence-transformers) |
| ML | K-Means + PCA + Silhouette Score (scikit-learn) |
| API | FastAPI + Pydantic |
| UI | Streamlit + Plotly |
| Data | Etsy API, SerpAPI, requests fallback |

---

## 📁 Project Structure