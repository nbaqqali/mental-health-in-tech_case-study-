# Mental Health in Technology-related Jobs — Case Study

Case study for **DLBDSMLUSL01 – Machine Learning: Unsupervised Learning and
Feature Engineering** (Task 1: Mental Health in Technology-related Jobs).

Student: **Niama Baqqali**

## What this repository contains

- `data/survey_raw.csv` — the OSMI *Mental Health in Tech Survey 2016* export
  (source: https://www.kaggle.com/osmi/mental-health-in-tech-2016).
- `src/analysis.py` — cleans the data, engineers features, restricts the
  sample to company employees, runs PCA for dimensionality reduction, and
  runs K-Means clustering (k chosen via the elbow method + silhouette
  score). Writes every figure and table used in the report to `outputs/`.
- `outputs/figures/` — all generated charts (PNG).
- `outputs/tables/` — cluster profile, run summary, and the fully engineered
  feature table with cluster labels (CSV).


## Method summary

1. **Scope**: only respondents employed by a company are analysed (the
   survey branches after the self-employment question, and employer
   benefit questions are only asked of employees).
2. **Cleaning**: invalid ages removed, free-text gender normalised,
   multi-label attitude/policy answers consolidated onto a 0–1 ordinal
   scale.
3. **Feature engineering**: 23 features across four themes — HR/employer
   policy, personal comfort & stigma, personal mental-health history, and
   firmographics/demographics.
4. **Dimensionality reduction**: PCA on the standardised feature matrix.
5. **Clustering**: K-Means on the PCA-reduced data; k selected via the
   elbow method and silhouette score.

