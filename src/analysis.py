"""
Mental Health in Technology-related Jobs -- clustering & dimensionality reduction
Case study for DLBDSMLUSL01 (Machine Learning - Unsupervised Learning and Feature Engineering)
Author: Biama Baqqali

Data source: OSMI Mental Health in Tech Survey 2016
             https://www.kaggle.com/osmi/mental-health-in-tech-2016

What this script does
----------------------
1. Loads the raw survey export.
2. Restricts the analysis to respondents employed by a company (the HR
   program in the case study targets *staff*, not the self-employed).
3. Cleans / feature-engineers a compact set of HR-relevant indicators
   (company benefits & policy questions, personal comfort/stigma
   questions, demographics).
4. Standardises the features and reduces dimensionality with PCA.
5. Clusters respondents with K-Means, choosing k with the elbow method
   and the silhouette score.
6. Produces the figures and tables used in the written case study.

Run with:  python src/analysis.py
Outputs land in ../outputs/figures and ../outputs/tables
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "survey_raw.csv"
FIG_DIR = ROOT / "outputs" / "figures"
TAB_DIR = ROOT / "outputs" / "tables"
FIG_DIR.mkdir(parents=True, exist_ok=True)
TAB_DIR.mkdir(parents=True, exist_ok=True)

RANDOM_STATE = 42

# ---------------------------------------------------------------------------
# 1. Load
# ---------------------------------------------------------------------------
df_raw = pd.read_csv(DATA)
n_total = len(df_raw)

# ---------------------------------------------------------------------------
# 2. Scope: employees of a company only (self-employed respondents follow a
#    different question branch and were not asked about employer benefits,
#    which is exactly what HR needs for the pre-emptive program).
# ---------------------------------------------------------------------------
df = df_raw[df_raw["Are you self-employed?"] == 0].copy()
n_employees = len(df)

# ---------------------------------------------------------------------------
# 3. Feature engineering
# ---------------------------------------------------------------------------

def yes_no_maybe(series: pd.Series) -> pd.Series:
    """Ordinal-encode 3/4-level attitude & policy questions.

    The survey mixes several near-synonymous label sets for the same
    underlying scale (agreement / awareness / ease). We collapse them onto
    a single 0-1 scale so that Euclidean-distance methods (PCA, K-Means)
    treat "more positive/aware" consistently across questions.
    """
    positive = {
        "Yes", "Yes, they all did", "Yes, I was aware of all of them",
        "Very easy", "Very open", "I know some", "Yes, I know several",
    }
    negative = {
        "No", "No, none did", "N/A (not currently aware)",
        "Very difficult", "Not open at all", "No, I don't know any",
    }
    neutral = {
        "Maybe", "I don't know", "Some did", "I was aware of some",
        "Some of them", "Neither easy nor difficult", "Somewhat easy",
        "Somewhat difficult", "Neutral", "Somewhat open", "Somewhat not open",
        "I am not sure", "Not applicable to me (I do not have a mental illness)",
    }

    def _map(v):
        if pd.isna(v):
            return 0.5
        if v in positive:
            return 1.0
        if v in negative:
            return 0.0
        if v in neutral:
            return 0.5
        return 0.5

    return series.apply(_map)


def company_size_ordinal(series: pd.Series) -> pd.Series:
    mapping = {
        "1-5": 1, "6-25": 2, "26-100": 3, "100-500": 4,
        "500-1000": 5, "More than 1000": 6,
    }
    return series.map(mapping)


def remote_ordinal(series: pd.Series) -> pd.Series:
    mapping = {"Never": 0, "Sometimes": 1, "Always": 2}
    return series.map(mapping)


def clean_gender(series: pd.Series) -> pd.Series:
    def _map(v):
        if pd.isna(v):
            return "Other/Unknown"
        v = str(v).strip().lower()
        male_tokens = ["male", "m", "man", "cis male", "cis man"]
        female_tokens = ["female", "f", "woman", "cis female", "cis woman"]
        if v in male_tokens:
            return "Male"
        if v in female_tokens:
            return "Female"
        return "Other/Unknown"
    return series.apply(_map)


def clean_age(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    s = s.where((s >= 18) & (s <= 75))  # drop obvious data-entry errors (3, 15, 323, ...)
    return s.fillna(s.median())


engineered = pd.DataFrame(index=df.index)

# --- HR / employer policy indicators (the levers HR can pull) -------------
engineered["benefits"] = yes_no_maybe(df["Does your employer provide mental health benefits as part of healthcare coverage?"])
engineered["knows_options"] = yes_no_maybe(df["Do you know the options for mental health care available under your employer-provided coverage?"])
engineered["wellness_discussed"] = yes_no_maybe(df["Has your employer ever formally discussed mental health (for example, as part of a wellness campaign or other official communication)?"])
engineered["resources_offered"] = yes_no_maybe(df["Does your employer offer resources to learn more about mental health concerns and options for seeking help?"])
engineered["anonymity_protected"] = yes_no_maybe(df["Is your anonymity protected if you choose to take advantage of mental health or substance abuse treatment resources provided by your employer?"])
engineered["leave_ease"] = yes_no_maybe(df["If a mental health issue prompted you to request a medical leave from work, asking for that leave would be:"])
engineered["employer_takes_seriously"] = yes_no_maybe(df["Do you feel that your employer takes mental health as seriously as physical health?"])

# --- Personal comfort / perceived-stigma indicators ------------------------
engineered["fear_negative_mh"] = 1 - yes_no_maybe(df["Do you think that discussing a mental health disorder with your employer would have negative consequences?"])
engineered["fear_negative_phys"] = 1 - yes_no_maybe(df["Do you think that discussing a physical health issue with your employer would have negative consequences?"])
engineered["comfort_coworkers"] = yes_no_maybe(df["Would you feel comfortable discussing a mental health disorder with your coworkers?"])
engineered["comfort_supervisor"] = yes_no_maybe(df["Would you feel comfortable discussing a mental health disorder with your direct supervisor(s)?"])
engineered["observed_negative_consequences"] = 1 - yes_no_maybe(df["Have you heard of or observed negative consequences for co-workers who have been open about mental health issues in your workplace?"])

# --- Personal mental-health history / relevance ----------------------------
engineered["family_history"] = yes_no_maybe(df["Do you have a family history of mental illness?"])
engineered["past_disorder"] = yes_no_maybe(df["Have you had a mental health disorder in the past?"])
engineered["current_disorder"] = yes_no_maybe(df["Do you currently have a mental health disorder?"])
engineered["sought_treatment"] = df["Have you ever sought treatment for a mental health issue from a mental health professional?"].fillna(0).astype(float)

# --- Firmographics & demographics ------------------------------------------
engineered["company_size"] = company_size_ordinal(df["How many employees does your company or organization have?"])
engineered["is_tech_company"] = df["Is your employer primarily a tech company/organization?"].fillna(0.5).astype(float)
engineered["remote_work"] = remote_ordinal(df["Do you work remotely?"])
engineered["age"] = clean_age(df["What is your age?"])
gender = clean_gender(df["What is your gender?"])

# fill any remaining ordinal/company-size gaps with the column median
for col in ["company_size"]:
    engineered[col] = engineered[col].fillna(engineered[col].median())

engineered = pd.concat([engineered, pd.get_dummies(gender, prefix="gender")], axis=1)

feature_cols = [c for c in engineered.columns]
X = engineered[feature_cols].astype(float)

# ---------------------------------------------------------------------------
# 4. Standardise + PCA
# ---------------------------------------------------------------------------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

pca_full = PCA(random_state=RANDOM_STATE).fit(X_scaled)
cum_var = np.cumsum(pca_full.explained_variance_ratio_)
n_components_80 = int(np.searchsorted(cum_var, 0.80) + 1)

pca = PCA(n_components=n_components_80, random_state=RANDOM_STATE)
X_pca = pca.fit_transform(X_scaled)

pca_2d = PCA(n_components=2, random_state=RANDOM_STATE)
X_pca2 = pca_2d.fit_transform(X_scaled)

# scree plot -----------------------------------------------------------------
plt.figure(figsize=(6, 4))
plt.plot(range(1, len(cum_var) + 1), cum_var, marker="o")
plt.axhline(0.80, color="grey", linestyle="--", linewidth=1)
plt.axvline(n_components_80, color="grey", linestyle="--", linewidth=1)
plt.xlabel("Number of principal components")
plt.ylabel("Cumulative explained variance")
plt.title("Figure 2. PCA cumulative explained variance")
plt.tight_layout()
plt.savefig(FIG_DIR / "fig2_pca_scree.png", dpi=200)
plt.close()

# ---------------------------------------------------------------------------
# 5. Choose k: elbow + silhouette on the PCA-reduced features
# ---------------------------------------------------------------------------
inertias, sils = [], []
k_range = range(2, 9)
for k in k_range:
    km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=10).fit(X_pca)
    inertias.append(km.inertia_)
    sils.append(silhouette_score(X_pca, km.labels_))

fig, axes = plt.subplots(1, 2, figsize=(11, 4))
axes[0].plot(list(k_range), inertias, marker="o")
axes[0].set_xlabel("k (number of clusters)")
axes[0].set_ylabel("Inertia (within-cluster SSE)")
axes[0].set_title("Elbow method")
axes[1].plot(list(k_range), sils, marker="o", color="darkorange")
axes[1].set_xlabel("k (number of clusters)")
axes[1].set_ylabel("Silhouette score")
axes[1].set_title("Silhouette score")
fig.suptitle("Figure 3. Selecting the number of clusters")
plt.tight_layout()
plt.savefig(FIG_DIR / "fig3_k_selection.png", dpi=200)
plt.close()

best_k = list(k_range)[int(np.argmax(sils))]

# ---------------------------------------------------------------------------
# 6. Final clustering
# ---------------------------------------------------------------------------
kmeans = KMeans(n_clusters=best_k, random_state=RANDOM_STATE, n_init=10)
labels = kmeans.fit_predict(X_pca)
engineered["cluster"] = labels
final_silhouette = silhouette_score(X_pca, labels)

# PCA scatter colored by cluster ---------------------------------------------
plt.figure(figsize=(6.5, 5))
scatter = plt.scatter(X_pca2[:, 0], X_pca2[:, 1], c=labels, cmap="tab10", s=18, alpha=0.75)
plt.xlabel(f"PC1 ({pca_2d.explained_variance_ratio_[0]*100:.1f}% var.)")
plt.ylabel(f"PC2 ({pca_2d.explained_variance_ratio_[1]*100:.1f}% var.)")
plt.title(f"Figure 4. Respondent clusters in the first two principal components (k={best_k})")
plt.colorbar(scatter, label="Cluster")
plt.tight_layout()
plt.savefig(FIG_DIR / "fig4_pca_clusters.png", dpi=200)
plt.close()

# ---------------------------------------------------------------------------
# 7. Cluster profiling
# ---------------------------------------------------------------------------
profile_cols = [c for c in feature_cols if not c.startswith("gender_")]
profile = engineered.groupby("cluster")[profile_cols].mean().round(2)
profile["n_respondents"] = engineered.groupby("cluster").size()
profile["share_%"] = (profile["n_respondents"] / len(engineered) * 100).round(1)
profile.to_csv(TAB_DIR / "cluster_profile.csv")

# cluster profile heatmap ------------------------------------------------
heat_cols = [
    "benefits", "knows_options", "wellness_discussed", "resources_offered",
    "anonymity_protected", "leave_ease", "employer_takes_seriously",
    "fear_negative_mh", "comfort_coworkers", "comfort_supervisor",
    "family_history", "past_disorder", "current_disorder", "sought_treatment",
]
heat_data = profile[heat_cols]
plt.figure(figsize=(9, 4.5))
im = plt.imshow(heat_data.values, cmap="RdYlGn", vmin=0, vmax=1, aspect="auto")
plt.xticks(range(len(heat_cols)), heat_cols, rotation=60, ha="right")
plt.yticks(range(len(heat_data)), [f"Cluster {i}" for i in heat_data.index])
plt.colorbar(im, label="Mean score (0 = negative/low, 1 = positive/high)")
plt.title("Figure 5. Cluster profiles across HR & attitude indicators")
plt.tight_layout()
plt.savefig(FIG_DIR / "fig5_cluster_heatmap.png", dpi=200)
plt.close()

# cluster size bar chart ---------------------------------------------------
plt.figure(figsize=(5, 4))
profile["n_respondents"].plot(kind="bar", color="steelblue")
plt.xlabel("Cluster")
plt.ylabel("Number of respondents")
plt.title("Figure 6. Cluster sizes")
plt.tight_layout()
plt.savefig(FIG_DIR / "fig6_cluster_sizes.png", dpi=200)
plt.close()

# funnel figure: total -> employees analysed --------------------------------
plt.figure(figsize=(4.5, 4))
plt.bar(["All respondents", "Employees analysed"], [n_total, n_employees], color=["grey", "steelblue"])
plt.title("Figure 1. Survey scope")
plt.ylabel("Respondents")
plt.tight_layout()
plt.savefig(FIG_DIR / "fig1_scope.png", dpi=200)
plt.close()

# ---------------------------------------------------------------------------
# 8. Summary written to disk for the report-builder script
# ---------------------------------------------------------------------------
summary = {
    "n_total_respondents": n_total,
    "n_employees_analysed": n_employees,
    "n_features": X.shape[1],
    "n_pca_components_80pct": n_components_80,
    "pca2_var_pc1": round(float(pca_2d.explained_variance_ratio_[0]) * 100, 1),
    "pca2_var_pc2": round(float(pca_2d.explained_variance_ratio_[1]) * 100, 1),
    "best_k": int(best_k),
    "final_silhouette": round(float(final_silhouette), 3),
}
pd.Series(summary).to_csv(TAB_DIR / "run_summary.csv", header=["value"])

engineered.to_csv(TAB_DIR / "engineered_features_with_clusters.csv", index=False)

print("Done.")
for k, v in summary.items():
    print(f"  {k}: {v}")
print("\nCluster profile:")
print(profile)
