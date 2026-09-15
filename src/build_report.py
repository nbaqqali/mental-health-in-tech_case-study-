"""
Builds the Word (.docx) case study report from the analysis outputs.
Run AFTER src/analysis.py has produced outputs/figures and outputs/tables.

Run with:  python src/build_report.py
Output:    report/Case_Study_Mental_Health_in_Tech_Baqqali.docx
"""

from pathlib import Path
import pandas as pd

from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "outputs" / "figures"
TAB_DIR = ROOT / "outputs" / "tables"
REPORT_DIR = ROOT / "report"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

GITHUB_URL = "https://github.com/nbaqqali/mental-health-in-tech-case-study"

AUTHOR = "Biama Baqqali"
COURSE = "DLBDSMLUSL01 - Machine Learning: Unsupervised Learning and Feature Engineering"
TITLE = "Mental Health in Technology-related Jobs"
SUBTITLE = "Clustering Survey Respondents to Support an HR Mental-Health Program"

summary = pd.read_csv(TAB_DIR / "run_summary.csv", index_col=0)["value"]
profile = pd.read_csv(TAB_DIR / "cluster_profile.csv", index_col=0)

N_TOTAL = int(summary["n_total_respondents"])
N_EMP = int(summary["n_employees_analysed"])
N_FEAT = int(summary["n_features"])
N_PCA80 = int(summary["n_pca_components_80pct"])
PC1_VAR = summary["pca2_var_pc1"]
PC2_VAR = summary["pca2_var_pc2"]
BEST_K = int(summary["best_k"])
SIL = summary["final_silhouette"]

# cluster ordering by size, descending, for narrative
profile_sorted = profile.sort_values("n_respondents", ascending=False)

CLUSTER_NAMES = {
    2: "Underserved & Unsupported",
    1: "Healthy but Culturally Cautious",
    3: "Well-Resourced & Actively Managed",
    0: "High Need, Low Psychological Safety",
    4: "Young, Remote, High-Need Niche",
}

# ---------------------------------------------------------------------------
# Document + base styling
# ---------------------------------------------------------------------------
doc = Document()

section = doc.sections[0]
section.left_margin = Cm(2.5)
section.right_margin = Cm(2.5)
section.top_margin = Cm(2.5)
section.bottom_margin = Cm(2.5)

style = doc.styles["Normal"]
style.font.name = "Times New Roman"
style.font.size = Pt(12)
style.paragraph_format.line_spacing = 1.5
style.paragraph_format.space_after = Pt(8)
rpr = style.element.get_or_add_rPr()
rFonts = rpr.find(qn("w:rFonts"))
if rFonts is None:
    rFonts = OxmlElement("w:rFonts")
    rpr.append(rFonts)
rFonts.set(qn("w:eastAsia"), "Times New Roman")

for i, size in zip(range(1, 4), (18, 15, 13)):
    hstyle = doc.styles[f"Heading {i}"]
    hstyle.font.name = "Times New Roman"
    hstyle.font.size = Pt(size)
    hstyle.font.bold = True
    hstyle.font.color.rgb = RGBColor(0, 0, 0)
    hstyle.paragraph_format.space_before = Pt(14)
    hstyle.paragraph_format.space_after = Pt(6)


def add_page_number_field(paragraph):
    run = paragraph.add_run()
    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")
    run._r.append(fld_begin)
    run._r.append(instr)
    run._r.append(fld_end)


footer = section.footer
footer_p = footer.paragraphs[0]
footer_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
add_page_number_field(footer_p)


def caption(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    run.italic = True
    run.font.size = Pt(10)
    return p


def add_figure(path, width_in=5.6, cap=None):
    doc.add_picture(str(path), width=Inches(width_in))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    if cap:
        caption(cap)


def add_table_from_df(df, first_col_header="Cluster"):
    table = doc.add_table(rows=1, cols=len(df.columns) + 1)
    table.style = "Light Grid Accent 1"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    hdr[0].text = first_col_header
    for j, col in enumerate(df.columns):
        hdr[j + 1].text = str(col)
    for idx, row in df.iterrows():
        cells = table.add_row().cells
        cells[0].text = str(idx)
        for j, val in enumerate(row):
            cells[j + 1].text = f"{val:.2f}" if isinstance(val, float) else str(val)
    for row in table.rows:
        for cell in row.cells:
            for p in cell.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(9)
    return table


# ---------------------------------------------------------------------------
# TITLE PAGE
# ---------------------------------------------------------------------------
for _ in range(4):
    doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run("CASE STUDY")
run.bold = True
run.font.size = Pt(16)

doc.add_paragraph()

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run(TITLE)
run.bold = True
run.font.size = Pt(24)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run(SUBTITLE)
run.italic = True
run.font.size = Pt(14)

for _ in range(4):
    doc.add_paragraph()

info_lines = [
    f"Course: {COURSE}",
    "Task 1: Mental Health in Technology-related Jobs",
    f"Author: {AUTHOR}",
    "Data source: OSMI Mental Health in Tech Survey 2016 (Kaggle)",
    f"Code repository: {GITHUB_URL}",
]
for line in info_lines:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run(line).font.size = Pt(12)

doc.add_page_break()

# ---------------------------------------------------------------------------
# TABLE OF CONTENTS (manual, since it is a small, fixed-structure document)
# ---------------------------------------------------------------------------
doc.add_heading("Table of Contents", level=1)
toc_entries = [
    "1. Introduction ................................................................... 3",
    "2. Data and Methodology ................................................ 3",
    "   2.1 Data Source and Scope ......................................... 3",
    "   2.2 Data Cleaning and Feature Engineering ............... 3",
    "   2.3 Dimensionality Reduction (PCA) .......................... 4",
    "   2.4 Clustering (K-Means) ............................................ 4",
    "3. Results ............................................................................ 4",
    "   3.1 Dimensionality Reduction Results ........................ 4",
    "   3.2 Cluster Solution and Segment Profiles ................. 5",
    "4. Discussion and Recommendations for HR ............... 6",
    "5. Conclusion and Critical Reflection ............................ 7",
    "Reference List ...................................................................... 7",
    "List of Appendices ............................................................... 8",
    "Appendix A: Code Repository and Reproducibility ..... 8",
]
for entry in toc_entries:
    doc.add_paragraph(entry)

doc.add_heading("List of Figures", level=2)
fig_list = [
    "Figure 1. Survey scope: total respondents vs. employees analysed",
    "Figure 2. PCA cumulative explained variance (scree plot)",
    "Figure 3. Selecting the number of clusters (elbow method and silhouette score)",
    "Figure 4. Respondent clusters in the first two principal components",
    "Figure 5. Cluster profiles across HR and attitude indicators (heatmap)",
    "Figure 6. Cluster sizes",
]
for f in fig_list:
    doc.add_paragraph(f, style="List Bullet")

doc.add_heading("List of Tables", level=2)
doc.add_paragraph("Table 1. Feature groups used for clustering", style="List Bullet")
doc.add_paragraph("Table 2. Mean indicator scores per cluster", style="List Bullet")

doc.add_heading("List of Abbreviations", level=2)
abbr = [
    ("HR", "Human Resources"),
    ("PCA", "Principal Component Analysis"),
    ("K-Means", "K-Means Clustering Algorithm"),
    ("OSMI", "Open Sourcing Mental Illness (survey provider)"),
    ("SSE", "Sum of Squared Errors"),
    ("PC", "Principal Component"),
]
for short, long in abbr:
    p = doc.add_paragraph()
    p.add_run(f"{short}\t").bold = True
    p.add_run(long)

doc.add_page_break()

# ---------------------------------------------------------------------------
# 1. INTRODUCTION
# ---------------------------------------------------------------------------
doc.add_heading("1. Introduction", level=1)
doc.add_paragraph(
    "Technology-oriented companies increasingly recognise that mental health "
    "shapes employee wellbeing, retention and productivity, yet the topic "
    "remains difficult to discuss openly in many workplaces (OSMI, 2016). "
    f"The Human Resources (HR) department of the company in this case study "
    "is preparing a pre-emptive mental-health program and has commissioned "
    "this analysis to turn a large, high-dimensional employee survey into a "
    "small number of interpretable employee segments that can be addressed "
    "with targeted measures."
)
doc.add_paragraph(
    "The underlying data set is not company-internal; per the task "
    "description it is treated as representative of the technology sector "
    "and is used as a stand-in for the company's own workforce. The data "
    "set is challenging for two reasons that are central to this course: "
    "(1) it is high-dimensional and largely categorical/ordinal, and (2) it "
    "contains missing values and free-text answers that must be cleaned "
    "before any machine-learning method can be applied. The goal of this "
    "case study is therefore twofold: (a) reduce the complexity and "
    "dimensionality of the survey while preserving its main characteristics, "
    "and (b) group respondents into homogeneous, well-described clusters "
    "that HR can use as a starting point for targeted interventions."
)

# ---------------------------------------------------------------------------
# 2. DATA AND METHODOLOGY
# ---------------------------------------------------------------------------
doc.add_heading("2. Data and Methodology", level=1)

doc.add_heading("2.1 Data Source and Scope", level=2)
doc.add_paragraph(
    "The analysis uses the OSMI Mental Health in Tech Survey 2016 "
    "(osmihelp.org; published on Kaggle), which contains open-ended and "
    "closed survey responses from technology employees worldwide on "
    "employer mental-health policy, personal mental-health history and "
    "workplace attitudes. The raw export contains "
    f"{N_TOTAL} respondents and roughly 60 raw questions."
)
doc.add_paragraph(
    "The questionnaire branches after the first question ('Are you "
    "self-employed?'): only respondents who are employed by a company are "
    "subsequently asked about employer-provided benefits, wellness "
    "communication and leave policy. Because the HR program in this case "
    "study targets a company's own staff, the self-employed respondents "
    "were excluded from the clustering step; this reduced the working "
    f"sample to {N_EMP} employees. This decision also removes a large block "
    "of structural missing values that would otherwise bias the distance "
    "calculations used by PCA and K-Means."
)

doc.add_heading("2.2 Data Cleaning and Feature Engineering", level=2)
doc.add_paragraph(
    "Three data-quality issues were addressed before feature engineering: "
    "(1) age contained clearly invalid entries (e.g. 3, 15, 99, 323), which "
    "were treated as missing and replaced with the sample median; "
    "(2) gender was entered as free text with dozens of spellings and was "
    "normalised into Male / Female / Other-Unknown; and (3) several "
    "attitude and policy questions mix near-synonymous answer scales "
    "('Yes' / 'I know some' / 'Very easy', etc.). These were consolidated "
    "into a consistent 0-1 ordinal scale (0 = negative/unaware, "
    "0.5 = neutral/uncertain, 1 = positive/aware) so that Euclidean-distance "
    "methods treat comparable answers consistently across questions."
)
doc.add_paragraph(
    f"A total of {N_FEAT} engineered features were constructed and grouped "
    "into four themes, summarised in Table 1: HR-controllable policy "
    "indicators (e.g., benefits, awareness of options, formal wellness "
    "communication, leave ease), personal comfort/stigma indicators "
    "(e.g., fear of negative consequences, comfort discussing mental "
    "health with coworkers/supervisors), personal mental-health relevance "
    "(family history, past/current disorder, treatment sought), and "
    "firmographics/demographics (company size, tech-company flag, remote "
    "work, age, gender). Company size was ordinally encoded "
    "(1-5 to 'More than 1000' -> 1-6) and gender was one-hot encoded. All "
    "features were standardised (zero mean, unit variance) before "
    "dimensionality reduction, since PCA and K-Means are scale-sensitive."
)

table1 = pd.DataFrame({
    "Feature group": [
        "HR / employer policy",
        "Personal comfort & stigma",
        "Personal mental-health history",
        "Firmographics & demographics",
    ],
    "Example variables": [
        "benefits, knows_options, wellness_discussed, resources_offered, "
        "anonymity_protected, leave_ease, employer_takes_seriously",
        "fear_negative_mh, fear_negative_phys, comfort_coworkers, "
        "comfort_supervisor, observed_negative_consequences",
        "family_history, past_disorder, current_disorder, sought_treatment",
        "company_size, is_tech_company, remote_work, age, gender (one-hot)",
    ],
})
doc.add_paragraph("Table 1. Feature groups used for clustering").runs[0].bold = True
t = doc.add_table(rows=1, cols=2)
t.style = "Light Grid Accent 1"
t.rows[0].cells[0].text = "Feature group"
t.rows[0].cells[1].text = "Example variables"
for _, r in table1.iterrows():
    cells = t.add_row().cells
    cells[0].text = r["Feature group"]
    cells[1].text = r["Example variables"]
for row in t.rows:
    for cell in row.cells:
        for p in cell.paragraphs:
            for run in p.runs:
                run.font.size = Pt(9)

doc.add_heading("2.3 Dimensionality Reduction (PCA)", level=2)
doc.add_paragraph(
    f"Principal Component Analysis (PCA) was applied to the {N_FEAT} "
    f"standardised features. {N_PCA80} principal components were required "
    "to retain 80% of the total variance (Figure 2); K-Means clustering "
    "was performed on this 80%-variance representation to reduce noise, "
    "while the first two components (explaining "
    f"{PC1_VAR}% and {PC2_VAR}% of variance respectively) were used purely "
    "for the two-dimensional visualisation in Figure 4."
)

doc.add_heading("2.4 Clustering (K-Means)", level=2)
doc.add_paragraph(
    "K-Means was chosen because the engineered features are continuous "
    "after ordinal/one-hot encoding and scaling, and because it scales well "
    "to the sample size. The number of clusters k was selected by "
    "inspecting the elbow of the within-cluster sum of squared errors "
    "(inertia) and by maximising the silhouette score across k = 2 to 8 "
    f"(Figure 3). Both criteria pointed to k = {BEST_K}, which was used for "
    f"the final solution (silhouette score = {SIL})."
)

doc.add_page_break()

# ---------------------------------------------------------------------------
# 3. RESULTS
# ---------------------------------------------------------------------------
doc.add_heading("3. Results", level=1)

doc.add_heading("3.1 Dimensionality Reduction Results", level=2)
add_figure(FIG_DIR / "fig1_scope.png", width_in=3.0,
           cap="Figure 1. Survey scope: total respondents vs. employees analysed.")
add_figure(FIG_DIR / "fig2_pca_scree.png", width_in=4.6,
           cap="Figure 2. PCA cumulative explained variance (scree plot).")
add_figure(FIG_DIR / "fig3_k_selection.png", width_in=6.0,
           cap="Figure 3. Elbow method (left) and silhouette score (right) across candidate k values.")

doc.add_heading("3.2 Cluster Solution and Segment Profiles", level=2)
doc.add_paragraph(
    f"The final K-Means solution identified {BEST_K} clusters, visualised "
    "in Figure 4 on the first two principal components and profiled in "
    "Figure 5 (mean indicator scores per cluster, 0-1 scale) and Figure 6 "
    "(cluster sizes). Table 2 reports the underlying mean values."
)
add_figure(FIG_DIR / "fig4_pca_clusters.png", width_in=5.0,
           cap="Figure 4. Respondent clusters in the first two principal components.")
add_figure(FIG_DIR / "fig5_cluster_heatmap.png", width_in=6.2,
           cap="Figure 5. Cluster profiles across HR and attitude indicators.")
add_figure(FIG_DIR / "fig6_cluster_sizes.png", width_in=3.4,
           cap="Figure 6. Cluster sizes.")

doc.add_paragraph("Table 2. Mean indicator scores per cluster (selected columns, 0-1 scale unless noted)").runs[0].bold = True
key_cols = ["benefits", "knows_options", "wellness_discussed", "leave_ease",
            "fear_negative_mh", "comfort_coworkers", "comfort_supervisor",
            "current_disorder", "n_respondents", "share_%"]
add_table_from_df(profile[key_cols])

doc.add_paragraph(
    "Based on the profiles in Table 2 and Figure 5, the five clusters were "
    "labelled as follows:"
)
for cid in profile_sorted.index:
    row = profile.loc[cid]
    name = CLUSTER_NAMES.get(cid, f"Cluster {cid}")
    doc.add_paragraph(
        f"Cluster {cid} - “{name}” ({int(row['n_respondents'])} "
        f"respondents, {row['share_%']}% of the sample): benefits "
        f"{row['benefits']:.2f}, comfort with supervisor "
        f"{row['comfort_supervisor']:.2f}, current mental-health disorder "
        f"{row['current_disorder']:.2f}, fear of negative consequences "
        f"{row['fear_negative_mh']:.2f}.",
        style="List Bullet",
    )

doc.add_paragraph(
    "Cluster 2 (“Underserved & Unsupported”) scores lowest on "
    "every HR-controllable indicator (benefits, awareness of options, "
    "formal wellness communication, leave ease) while still reporting "
    "substantial personal mental-health relevance and the lowest comfort "
    "discussing the topic with coworkers or supervisors. Cluster 0 "
    "(“High Need, Low Psychological Safety”) has the highest "
    "past/current disorder and treatment-seeking rates but only moderate "
    "comfort scores, suggesting unmet need even where basic benefits "
    "exist. Cluster 3 (“Well-Resourced & Actively Managed”) has "
    "the strongest employer policies and the highest comfort scores, and "
    "is concentrated in larger companies; it also has the highest "
    "self-reported current-disorder rate, which is consistent with more "
    "mental-health-literate employees being more willing to recognise and "
    "disclose a condition rather than with the policies causing harm. "
    "Cluster 1 (“Healthy but Culturally Cautious”) reports almost "
    "no personal mental-health history yet still shows a high fear of "
    "negative consequences, indicating that stigma perceptions are not "
    "confined to employees who are personally affected. Cluster 4 "
    "(“Young, Remote, High-Need Niche”) is a small "
    "(" + f"{profile.loc[4,'share_%']:.1f}%" + ") but distinct group of "
    "younger, highly remote, tech-company employees with above-average "
    "personal need and moderate policy support."
)

doc.add_page_break()

# ---------------------------------------------------------------------------
# 4. DISCUSSION AND RECOMMENDATIONS
# ---------------------------------------------------------------------------
doc.add_heading("4. Discussion and Recommendations for HR", level=1)
doc.add_paragraph(
    "The clustering result gives HR three concrete points of leverage. "
    "First, Cluster 2 and Cluster 0 together represent close to half of "
    "the workforce (about "
    f"{profile.loc[2,'share_%'] + profile.loc[0,'share_%']:.0f}% combined) "
    "and combine real mental-health need with weak policy support or low "
    "psychological safety. These two segments should be the primary "
    "target of the pre-emptive program: closing the awareness gap "
    "(communicating what benefits already exist), formally addressing "
    "mental health in wellness communication, and manager training aimed "
    "specifically at improving comfort discussing the topic with direct "
    "supervisors, since supervisor comfort is consistently the lowest "
    "scoring item in both segments."
)
doc.add_paragraph(
    "Second, the persistence of a high fear-of-negative-consequences score "
    "even in the best-supported cluster (Cluster 3) and in the "
    "personally-unaffected cluster (Cluster 1) suggests that formal "
    "benefits alone do not remove stigma. HR should complement policy "
    "improvements with visible, repeated communication (e.g., leadership "
    "role-modelling, anonymised success stories) rather than assuming that "
    "offering a benefit is sufficient."
)
doc.add_paragraph(
    "Third, Cluster 4, while small, points to a specific risk group "
    "(younger, highly remote employees) that may need a different channel "
    "of communication than the rest of the workforce, for example "
    "manager check-ins adapted to remote settings rather than in-person "
    "wellness events."
)

# ---------------------------------------------------------------------------
# 5. CONCLUSION AND CRITICAL REFLECTION
# ---------------------------------------------------------------------------
doc.add_heading("5. Conclusion and Critical Reflection", level=1)
doc.add_paragraph(
    f"Starting from {N_FEAT} engineered features across {N_EMP} employees, "
    f"PCA reduced the data to {N_PCA80} components that retain 80% of the "
    "variance, and K-Means identified five interpretable, HR-actionable "
    "clusters. The resulting segments differ meaningfully in policy "
    "support, personal mental-health relevance and psychological safety, "
    "giving HR a concrete basis for targeted, rather than one-size-fits-"
    "all, measures."
)
doc.add_paragraph(
    "Two limitations should be kept in mind. First, the silhouette score "
    f"of the final solution ({SIL}) is modest, which is expected for "
    "largely ordinal/attitudinal survey data where clusters overlap along "
    "continuous scales rather than forming well-separated groups; the "
    "clusters should be read as tendencies rather than sharply bounded "
    "types. Second, the analysis substitutes a public, anonymised industry "
    "survey for genuine company data, so the concrete cluster sizes should "
    "not be transferred to a specific organisation without re-running the "
    "pipeline on that company's own (anonymised) survey data, which the "
    "accompanying code (Appendix A) is designed to make straightforward."
)

doc.add_page_break()

# ---------------------------------------------------------------------------
# REFERENCE LIST
# ---------------------------------------------------------------------------
doc.add_heading("Reference List", level=1)
references = [
    "Open Sourcing Mental Illness (OSMI). (2016). Mental Health in Tech "
    "Survey 2016 [Data set]. Kaggle. "
    "https://www.kaggle.com/osmi/mental-health-in-tech-2016",
    "Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., "
    "Grisel, O., Blondel, M., Prettenhofer, P., Weiss, R., Dubourg, V., "
    "Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., "
    "& Duchesnay, E. (2011). Scikit-learn: Machine learning in Python. "
    "Journal of Machine Learning Research, 12, 2825-2830.",
    "Jolliffe, I. T., & Cadima, J. (2016). Principal component analysis: "
    "A review and recent developments. Philosophical Transactions of the "
    "Royal Society A, 374(2065), 20150202. "
    "https://doi.org/10.1098/rsta.2015.0202",
    "MacQueen, J. (1967). Some methods for classification and analysis of "
    "multivariate observations. Proceedings of the Fifth Berkeley "
    "Symposium on Mathematical Statistics and Probability, 1, 281-297.",
]
for ref in references:
    p = doc.add_paragraph(ref)
    p.paragraph_format.left_indent = Cm(1)
    p.paragraph_format.first_line_indent = Cm(-1)

doc.add_page_break()

# ---------------------------------------------------------------------------
# LIST OF APPENDICES + APPENDIX A
# ---------------------------------------------------------------------------
doc.add_heading("List of Appendices", level=1)
doc.add_paragraph("Appendix A: Code Repository and Reproducibility", style="List Bullet")

doc.add_heading("Appendix A: Code Repository and Reproducibility", level=1)
doc.add_paragraph(
    "The complete, runnable code for this case study (data cleaning, "
    "feature engineering, PCA, K-Means clustering and figure generation) "
    "is published on GitHub at:"
)
p = doc.add_paragraph()
run = p.add_run(GITHUB_URL)
run.font.color.rgb = RGBColor(5, 99, 193)
run.underline = True
doc.add_paragraph(
    "The repository contains: (1) the raw survey export used for this "
    "analysis, (2) src/analysis.py, which performs all cleaning, "
    "feature engineering, PCA and clustering steps and writes every "
    "figure and table used in this document, and (3) a README with setup "
    "and run instructions. Running 'python src/analysis.py' from the "
    "repository root reproduces every number and figure reported above."
)

doc.save(REPORT_DIR / "Case_Study_Mental_Health_in_Tech_Baqqali.docx")
print("Saved:", REPORT_DIR / "Case_Study_Mental_Health_in_Tech_Baqqali.docx")
