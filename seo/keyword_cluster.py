import os
import sys
import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# Load the sentence embedding model once at module level
# all-MiniLM-L6-v2 is small (80MB), fast, and great for short keyword phrases
print("  Loading sentence embedding model...")
EMBEDDER = SentenceTransformer("all-MiniLM-L6-v2")


# ─────────────────────────────────────────────────────────────
# STEP 1 — Embed keywords into vectors
# ─────────────────────────────────────────────────────────────

def embed_keywords(keywords: list[str]) -> np.ndarray:
    """
    Convert a list of keyword strings into numeric vectors
    using a pretrained sentence transformer model.

    Each keyword becomes a 384-dimensional vector that
    captures its semantic meaning — so "wedding kurta" and
    "bridal outfit" end up close together in vector space.

    Args:
        keywords : list of keyword strings

    Returns:
        numpy array of shape (n_keywords, 384)
    """
    print(f"  → Embedding {len(keywords)} keywords...")
    embeddings = EMBEDDER.encode(keywords, show_progress_bar=False)

    # L2 normalize so cosine similarity == dot product
    # This makes K-Means work better on text embeddings
    embeddings = normalize(embeddings, norm="l2")
    return embeddings


# ─────────────────────────────────────────────────────────────
# STEP 2 — Find the optimal number of clusters
# ─────────────────────────────────────────────────────────────

def find_optimal_k(embeddings: np.ndarray, max_k: int = 8) -> dict:
    """
    Use the Elbow Method + Silhouette Score to find the best
    number of clusters K for the given keyword set.

    Elbow Method  : plot inertia vs K — look for the "elbow"
    Silhouette    : score between -1 and 1, higher = better clusters

    Args:
        embeddings : output of embed_keywords()
        max_k      : maximum K to try (default 8)

    Returns:
        dict with inertias, silhouette scores, and recommended K
    """
    n = len(embeddings)

    # Need at least 2 samples per cluster
    max_k = min(max_k, n // 2)
    k_range = range(2, max_k + 1)

    inertias    = []
    silhouettes = []

    print(f"  → Finding optimal K (testing K=2 to K={max_k})...")

    for k in k_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(embeddings)
        inertias.append(km.inertia_)
        silhouettes.append(silhouette_score(embeddings, labels))

    # Best K = highest silhouette score
    best_k = list(k_range)[np.argmax(silhouettes)]

    print(f"  → Recommended K = {best_k} "
          f"(silhouette score: {max(silhouettes):.3f})")

    return {
        "k_range"     : list(k_range),
        "inertias"    : inertias,
        "silhouettes" : silhouettes,
        "best_k"      : best_k
    }


# ─────────────────────────────────────────────────────────────
# STEP 3 — Cluster the keywords
# ─────────────────────────────────────────────────────────────

def cluster_keywords(keywords: list[str], k: int = None) -> dict:
    """
    Cluster keywords into K groups using K-Means on embeddings.

    If k is None, automatically finds the optimal K first.

    Args:
        keywords : list of keyword strings
        k        : number of clusters (optional — auto-detected if None)

    Returns:
        dict with:
            - clusters      : { cluster_id: { label, keywords, centroid_keyword } }
            - assignments   : { keyword: cluster_id } for every keyword
            - k_used        : final K value used
            - silhouette    : silhouette score of this clustering
            - embeddings    : raw numpy array (for plotting)
            - labels        : cluster label per keyword (for plotting)
    """
    embeddings = embed_keywords(keywords)

    # Auto-detect K if not provided
    if k is None:
        k_analysis = find_optimal_k(embeddings)
        k = k_analysis["best_k"]

    print(f"  → Clustering {len(keywords)} keywords into {k} groups...")

    km     = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(embeddings)
    score  = silhouette_score(embeddings, labels)

    # Group keywords by cluster
    clusters = {}
    for cluster_id in range(k):
        indices    = [i for i, l in enumerate(labels) if l == cluster_id]
        kws        = [keywords[i] for i in indices]

        # Find the keyword closest to the cluster centroid
        centroid   = km.cluster_centers_[cluster_id]
        distances  = [np.linalg.norm(embeddings[i] - centroid) for i in indices]
        closest_kw = kws[np.argmin(distances)]

        clusters[cluster_id] = {
            "centroid_keyword" : closest_kw,   # most representative keyword
            "keywords"         : kws,
            "size"             : len(kws),
        }

    # Build keyword → cluster_id lookup
    assignments = {keywords[i]: int(labels[i]) for i in range(len(keywords))}

    return {
        "clusters"   : clusters,
        "assignments": assignments,
        "k_used"     : k,
        "silhouette" : round(score, 4),
        "embeddings" : embeddings,
        "labels"     : labels,
        "keywords"   : keywords,
    }


# ─────────────────────────────────────────────────────────────
# STEP 4 — Auto-label clusters with Gemini
# ─────────────────────────────────────────────────────────────

def label_clusters_with_ai(cluster_result: dict) -> dict:
    """
    Use Gemini to assign a human-readable label to each cluster.
    e.g. Cluster 0 → "Wedding & Occasion Wear"
         Cluster 1 → "Fabric & Material"
         Cluster 2 → "Style & Silhouette"

    Args:
        cluster_result : output of cluster_keywords()

    Returns:
        Same dict with "label" added to each cluster
    """
    import google.generativeai as genai
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-3.1-flash-lite")

    clusters = cluster_result["clusters"]

    for cluster_id, data in clusters.items():
        kws_str = ", ".join(data["keywords"])

        prompt = f"""
You are an SEO expert. Given these keywords from one cluster, give a short 2-4 word label
that describes what theme or category they share.

Keywords: {kws_str}

Reply with ONLY the label, nothing else. Example: "Wedding & Occasion Wear"
"""
        response = model.generate_content(prompt)
        label    = response.text.strip().strip('"')
        clusters[cluster_id]["label"] = label
        print(f"    Cluster {cluster_id} → '{label}'")

    cluster_result["clusters"] = clusters
    return cluster_result


# ─────────────────────────────────────────────────────────────
# STEP 5 — Visualize clusters (PCA → 2D scatter plot)
# ─────────────────────────────────────────────────────────────

def plot_clusters(cluster_result: dict, save_path: str = None):
    """
    Reduce embeddings to 2D with PCA and plot the clusters.
    Each dot = one keyword, colored by cluster.
    Great for your capstone notebook / presentation.

    Args:
        cluster_result : output of cluster_keywords() or label_clusters_with_ai()
        save_path      : optional file path to save the PNG
    """
    embeddings = cluster_result["embeddings"]
    labels     = cluster_result["labels"]
    keywords   = cluster_result["keywords"]
    clusters   = cluster_result["clusters"]
    k          = cluster_result["k_used"]

    # Reduce to 2D
    pca   = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(embeddings)

    # Color palette
    colors = plt.cm.Set2(np.linspace(0, 1, k))

    fig, ax = plt.subplots(figsize=(11, 7))
    fig.patch.set_facecolor("#0f0f0f")
    ax.set_facecolor("#0f0f0f")

    for cluster_id in range(k):
        mask = labels == cluster_id
        ax.scatter(
            coords[mask, 0], coords[mask, 1],
            color=colors[cluster_id], s=80, alpha=0.85, zorder=3
        )

    # Annotate each keyword
    for i, kw in enumerate(keywords):
        ax.annotate(
            kw, (coords[i, 0], coords[i, 1]),
            fontsize=7, color="white", alpha=0.75,
            xytext=(4, 4), textcoords="offset points"
        )

    # Legend using cluster labels
    legend_patches = []
    for cluster_id, data in clusters.items():
        cluster_label = data.get("label", f"Cluster {cluster_id}")
        patch = mpatches.Patch(
            color=colors[cluster_id],
            label=f'{cluster_label} ({data["size"]} keywords)'
        )
        legend_patches.append(patch)

    ax.legend(
        handles=legend_patches, loc="upper left",
        facecolor="#1a1a1a", edgecolor="#444", labelcolor="white",
        fontsize=8
    )

    ax.set_title(
        f"Keyword Clusters — Chikan Diaries SEO\n"
        f"K={k}  |  Silhouette Score: {cluster_result['silhouette']}",
        color="white", fontsize=12, pad=14
    )
    ax.tick_params(colors="gray")
    for spine in ax.spines.values():
        spine.set_edgecolor("#333")

    plt.tight_layout()

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"  ✓ Plot saved to {save_path}")

    plt.show()


# ─────────────────────────────────────────────────────────────
# Master function
# ─────────────────────────────────────────────────────────────

def run_keyword_clustering(keywords: list[str], k: int = None,
                            label_with_ai: bool = True,
                            plot: bool = True) -> dict:
    """
    Full pipeline: embed → cluster → label → plot.

    Args:
        keywords      : flat list of keyword strings
        k             : number of clusters (auto if None)
        label_with_ai : use Gemini to name each cluster
        plot          : show and save the scatter plot

    Returns:
        Final cluster result dict
    """
    result = cluster_keywords(keywords, k=k)

    if label_with_ai:
        print("\n  → Labelling clusters with Gemini...")
        result = label_clusters_with_ai(result)

    if plot:
        save_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..", "data", "outputs", "keyword_clusters.png"
        )
        plot_clusters(result, save_path=save_path)

    return result


# ── Quick test ───────────────────────────────────────────────
if __name__ == "__main__":

    print("=" * 55)
    print("  Chikan Diaries — Keyword Clustering (ML)")
    print("=" * 55)

    # Sample keyword pool — in real use this comes from
    # keyword_generator.py run across your full product catalog
    sample_keywords = [
        "chikankari kurta", "embroidered kurta", "white kurta",
        "cotton kurta", "georgette kurta", "silk kurta",
        "wedding outfit", "bridal wear", "festive dress",
        "party wear", "occasion wear", "ethnic wear",
        "handmade clothing", "hand embroidered", "artisan made",
        "lucknow chikankari", "traditional indian wear", "indian ethnic",
        "summer kurta", "casual kurta", "daily wear",
        "anarkali suit", "straight kurta", "a-line kurta",
        "plus size kurta", "custom sizing", "xl kurta",
        "gift for her", "diwali gift", "eid outfit",
    ]

    print(f"\nInput: {len(sample_keywords)} keywords")

    result = run_keyword_clustering(
        keywords     = sample_keywords,
        k            = None,          # auto-detect best K
        label_with_ai= True,
        plot         = True
    )

    # Print cluster summary
    print("\n── Cluster Summary ──")
    for cid, data in result["clusters"].items():
        print(f"\n  Cluster {cid} — {data.get('label', 'Unlabelled')}")
        print(f"  Representative: '{data['centroid_keyword']}'")
        print(f"  Keywords: {', '.join(data['keywords'])}")

    print(f"\n  Silhouette Score : {result['silhouette']}")
    print(f"  K used           : {result['k_used']}")

    # Save result
    out_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..", "..", "data", "outputs"
    )
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "keyword_clusters.json")

    save_data = {k: v for k, v in result.items()
                 if k not in ("embeddings", "labels")}  # skip numpy arrays

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(save_data, f, indent=2, ensure_ascii=False)

    print(f"\n  ✓ Cluster data saved to {out_path}")
