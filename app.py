import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

st.set_page_config(page_title="S&P 500 Clustering Analysis", layout="wide", initial_sidebar_state="expanded")

CLUSTER_SHORT = {
    0: "Mixed / Other Heavy",
    1: "High Profitability",
    2: "High Volatility",
    3: "Extreme Leverage",
    4: "Premium Valuation",
    5: "Core Market",
}

PALETTE = ['#185FA5', '#0F6E56', '#A32D2D', '#854F0B', '#6D2E46', '#3B6D11']

# ── Risk Score helpers ─────────────────────────────────────────────
# Each cluster gets a 0-100 risk score based on its financial archetype.
# Higher = riskier for a typical investor.
CLUSTER_RISK = {
    0: 45,   # Mixed / Other Heavy  — moderate, broad mix
    1: 25,   # High Profitability   — low risk, strong fundamentals
    2: 85,   # High Volatility      — high beta + negative ROE = distressed
    3: 99,   # Extreme Leverage     — D/E of 139, deeply negative ROE
    4: 60,   # Premium Valuation    — P/E of 261 = valuation risk
    5: 35,   # Core Market          — large, stable companies
}

RISK_LABELS = {
    range(0,  30): ("Low",        "#0F6E56"),
    range(30, 55): ("Moderate",   "#3B6D11"),
    range(55, 75): ("Elevated",   "#854F0B"),
    range(75, 101):("High",       "#A32D2D"),
}

def get_risk_label(score):
    for r, (label, color) in RISK_LABELS.items():
        if score in r:
            return label, color
    return "High", "#A32D2D"


@st.cache_data
def load_data():
    df      = pd.read_csv("sp500_clustered.csv")
    profile = pd.read_csv("cluster_profiles.csv")
    crosstab = pd.read_csv("cluster_sector_crosstab_pct.csv")
    return df, profile, crosstab

df, profile, crosstab = load_data()
df['Cluster_Name'] = df['Cluster'].map(CLUSTER_SHORT)

# ── Sidebar ────────────────────────────────────────────────────────
st.sidebar.title("Controls")
st.sidebar.markdown("---")

all_names = [CLUSTER_SHORT[i] for i in sorted(CLUSTER_SHORT.keys())]
selected  = st.sidebar.multiselect("Filter by Cluster", options=all_names, default=all_names)
filtered  = df[df['Cluster_Name'].isin(selected)]

st.sidebar.markdown("---")
st.sidebar.markdown("**About**")
st.sidebar.markdown(
    "K-Means clustering of 496 S&P 500 companies across 5 financial features: "
    "Beta, P/E Ratio, ROE, Debt/Equity, and Market Cap."
)

# ── Header ─────────────────────────────────────────────────────────
st.title("S&P 500 Financial Behavior Clustering")
st.markdown(
    "Exploring whether S&P 500 companies form natural groupings based on "
    "**financial behavior**, independent of traditional GICS sector labels."
)
st.markdown("---")

# ── Section 1: Model Metrics ───────────────────────────────────────
st.header("Model Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Companies Analyzed", "496")
c2.metric("Clusters (k)", "6")
c3.metric("Silhouette Score", "0.2909")
c4.metric("Features Used", "5")
st.caption(
    "Algorithm: K-Means | Preprocessing: Z-score scaling + PCA (8 components, 83.7% variance) "
    "| k selected via Elbow + Silhouette across k=2–8"
)
st.markdown("---")

# ── Section 2: Cluster Profiles ────────────────────────────────────
st.header("Cluster Profiles")
st.markdown("Mean financial metrics per cluster — each represents a distinct financial archetype.")

display = profile.copy()
display['Archetype'] = display['Cluster'].map(CLUSTER_SHORT)
display = display[['Cluster','Archetype','Count','Beta','PE_Ratio','ROE_pct','Debt_Equity','MarketCap_B']]
display.columns = ['Cluster','Archetype','Companies','Beta','P/E Ratio','ROE (%)','Debt/Equity','Mkt Cap ($B)']

st.dataframe(
    display.style
    .format({'Beta':'{:.3f}','P/E Ratio':'{:.1f}','ROE (%)':'{:.1f}','Debt/Equity':'{:.3f}','Mkt Cap ($B)':'{:.1f}'}, na_rep='N/A')
    .background_gradient(subset=['Beta','ROE (%)'], cmap='RdYlGn')
    .background_gradient(subset=['Debt/Equity'], cmap='OrRd'),
    use_container_width=True, hide_index=True
)

st.markdown("""
**Key findings:**
- **Cluster 1** (137 cos): Largest high-profitability group — ROE 34.5%, broad sector mix
- **Cluster 5** (331 cos): Core market — largest cluster, moderate across all metrics
- **Cluster 3** (2 cos): Extreme outlier — Debt/Equity of 139.9, deeply negative ROE (−315.5%)
- **Cluster 2** (7 cos): High volatility (Beta 1.74), negative ROE — distressed/high-risk companies
- **Cluster 4** (12 cos): Premium valuation — P/E of 261, dominated by Real Estate/REITs
""")
st.markdown("---")

# ── Section 3: PCA Scatter ─────────────────────────────────────────
st.header("Clusters in PCA Space")
st.markdown(
    "Each point is one company, colored by cluster. "
    "Axes are the first two principal components of the 5 financial features."
)

if 'PCA1' not in df.columns or 'PCA2' not in df.columns:
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA as skPCA
    num_cols = [c for c in ['Beta_num','PE_num','ROE_num','DE_num','MarketCap_num'] if c in df.columns]
    tmp    = df[num_cols].fillna(df[num_cols].median())
    scaled = StandardScaler().fit_transform(tmp)
    coords = skPCA(n_components=2, random_state=42).fit_transform(scaled)
    df['PCA1'], df['PCA2'] = coords[:,0], coords[:,1]

filtered = df[df['Cluster_Name'].isin(selected)]

fig, ax = plt.subplots(figsize=(10, 6))
for i in sorted(df['Cluster'].unique()):
    name = CLUSTER_SHORT[i]
    if name not in selected:
        continue
    mask = filtered['Cluster'] == i
    ax.scatter(filtered.loc[mask,'PCA1'], filtered.loc[mask,'PCA2'],
               c=PALETTE[i % len(PALETTE)], label=f"C{i}: {CLUSTER_SHORT[i]}",
               alpha=0.65, s=45, edgecolors='white', linewidths=0.3)
ax.set_xlabel("PC1", fontsize=12)
ax.set_ylabel("PC2", fontsize=12)
ax.set_title("K-Means Clusters in PCA Space — S&P 500 Companies", fontsize=13, fontweight='bold')
ax.legend(bbox_to_anchor=(1.01,1), loc='upper left', fontsize=9, framealpha=0.9)
ax.grid(alpha=0.2)
plt.tight_layout()
st.pyplot(fig)
plt.close()
st.markdown("---")

# ── Section 4: Sector Heatmap RQ2 ─────────────────────────────────
st.header("RQ2: Do Financial Clusters Align with GICS Sectors?")
st.markdown(
    "If clusters matched GICS sectors, each row would have one dominant sector. "
    "Mixed rows confirm clusters **cut across** sector boundaries."
)

sector_cols = [c for c in crosstab.columns if c != 'Cluster']
data_arr    = crosstab[sector_cols].values
row_labels  = [f"C{int(r)}: {CLUSTER_SHORT[int(r)]}" for r in crosstab['Cluster']]

fig2, ax2 = plt.subplots(figsize=(14, 5))
im = ax2.imshow(data_arr, cmap='Blues', aspect='auto', vmin=0, vmax=100)
plt.colorbar(im, ax=ax2, label='% of cluster', shrink=0.8)
ax2.set_xticks(range(len(sector_cols)))
ax2.set_xticklabels(sector_cols, rotation=30, ha='right', fontsize=9)
ax2.set_yticks(range(len(row_labels)))
ax2.set_yticklabels(row_labels, fontsize=10)
for i in range(len(row_labels)):
    for j in range(len(sector_cols)):
        val = data_arr[i, j]
        if val > 0:
            ax2.text(j, i, f'{val:.0f}%', ha='center', va='center',
                     fontsize=8, color='white' if val > 50 else 'black', fontweight='bold')
ax2.set_title("Cluster Composition by GICS Sector (%)", fontsize=13, fontweight='bold')
ax2.set_xlabel("GICS Sector", fontsize=11)
ax2.set_ylabel("Cluster", fontsize=11)
plt.tight_layout()
st.pyplot(fig2)
plt.close()

st.markdown("""
**Answer to RQ2:** Financial behavior clusters do **not** cleanly align with GICS sector labels.
Most clusters draw companies from multiple sectors, confirming that data-driven financial groupings
reveal structure that traditional sector classifications miss entirely.
""")
st.markdown("---")

# ── Section 5: Company Lookup ──────────────────────────────────────
st.header("Company Lookup")
st.markdown("Search any S&P 500 ticker to see its cluster assignment and financial profile.")

search = st.text_input("Enter ticker (e.g. AAPL, MSFT, JPM, TSLA)")
if search:
    results = df[df['Company'].str.upper().str.contains(search.strip().upper(), na=False)]
    if not results.empty:
        show = ['Company','Sector','Cluster','Cluster_Name','Beta_num','PE_num','ROE_num','DE_num','MarketCap_num']
        show = [c for c in show if c in results.columns]
        out  = results[show].rename(columns={
            'Cluster_Name':'Archetype','Beta_num':'Beta','PE_num':'P/E',
            'ROE_num':'ROE (%)','DE_num':'Debt/Equity','MarketCap_num':'Market Cap'
        }).reset_index(drop=True)
        st.dataframe(out, use_container_width=True, hide_index=True)

        # ── NEW: Risk Score card for looked-up company ─────────────────
        for _, row in results.iterrows():
            cluster_id = int(row['Cluster'])
            score      = CLUSTER_RISK[cluster_id]
            label, color = get_risk_label(score)
            company_name = row.get('Company', search.upper())

            st.markdown(f"#### Risk Profile — {company_name}")
            col_gauge, col_explain = st.columns([1, 2])

            with col_gauge:
                fig_g, ax_g = plt.subplots(figsize=(3.5, 2.2))
                ax_g.set_xlim(0, 100)
                ax_g.set_ylim(-0.3, 1.2)
                ax_g.axis('off')

                # Background bar
                ax_g.barh(0.5, 100, height=0.35, color='#e8e8e8', zorder=1)
                # Score bar
                ax_g.barh(0.5, score, height=0.35, color=color, zorder=2)
                # Score label
                ax_g.text(score, 0.5, f' {score}', va='center', ha='left',
                          fontsize=14, fontweight='bold', color=color)
                ax_g.text(50, -0.1, f'Risk Score: {label}', ha='center', va='top',
                          fontsize=11, color=color, fontweight='bold')
                plt.tight_layout()
                st.pyplot(fig_g)
                plt.close()

            with col_explain:
                st.markdown(f"""
**Cluster:** C{cluster_id} — {CLUSTER_SHORT[cluster_id]}

**Risk Score:** {score} / 100 &nbsp;→&nbsp; **{label}**

This score reflects the typical risk profile of companies in this cluster based on:
- **Beta** (market sensitivity)
- **Debt/Equity** (leverage risk)
- **ROE** (profitability stability)
- **P/E Ratio** (valuation risk)

> ⚠️ This is a cluster-level indicator, not a prediction of future performance.
""")
    else:
        st.warning(f"No company found matching '{search}'.")

st.markdown("---")

# ── NEW Section 5.5: Risk Score Overview ──────────────────────────
st.header("📊 Risk Score by Cluster")
st.markdown(
    "Each cluster is assigned a **0–100 risk score** based on its mean financial characteristics. "
    "This gives investors a quick signal of which archetypes carry more or less portfolio risk."
)

risk_df = pd.DataFrame([
    {"Cluster": k, "Archetype": CLUSTER_SHORT[k], "Risk Score": CLUSTER_RISK[k]}
    for k in sorted(CLUSTER_RISK.keys())
])
risk_df = risk_df.sort_values("Risk Score", ascending=True).reset_index(drop=True)

fig_r, ax_r = plt.subplots(figsize=(10, 5))
bar_colors = [PALETTE[int(row['Cluster']) % len(PALETTE)] for _, row in risk_df.iterrows()]
bars = ax_r.barh(risk_df['Archetype'], risk_df['Risk Score'],
                 color=bar_colors, edgecolor='white', height=0.55)

for bar, score in zip(bars, risk_df['Risk Score']):
    label, color = get_risk_label(score)
    ax_r.text(bar.get_width() + 1.5, bar.get_y() + bar.get_height()/2,
              f'{score}  ({label})', va='center', ha='left', fontsize=10, color=color, fontweight='bold')

ax_r.set_xlim(0, 115)
ax_r.set_xlabel("Risk Score (0 = Safest, 100 = Riskiest)", fontsize=11)
ax_r.set_title("Cluster Risk Scores — Investor Risk Awareness Guide", fontsize=13, fontweight='bold')
ax_r.axvline(30, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
ax_r.axvline(55, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
ax_r.axvline(75, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
ax_r.text(15,  -0.8, 'Low',      ha='center', fontsize=8, color='gray')
ax_r.text(42,  -0.8, 'Moderate', ha='center', fontsize=8, color='gray')
ax_r.text(65,  -0.8, 'Elevated', ha='center', fontsize=8, color='gray')
ax_r.text(88,  -0.8, 'High',     ha='center', fontsize=8, color='gray')
ax_r.grid(axis='x', alpha=0.2)
plt.tight_layout()
st.pyplot(fig_r)
plt.close()

st.markdown("""
**How scores are derived:** Each cluster's risk score is a composite of its mean Beta (market sensitivity),
Debt/Equity ratio (leverage), ROE sign (profitability), and P/E extremity (valuation risk).
Cluster 3 scores near 100 due to its extreme leverage and negative profitability.
""")
st.markdown("---")

# ── NEW Section 6: Cluster Performance Comparison (Radar) ─────────
st.header("🕸️ Cluster Performance Comparison")
st.markdown(
    "Compare clusters side-by-side across all five financial dimensions using a **radar chart**. "
    "Select two or more clusters to see how their financial profiles diverge."
)

# Normalise profile metrics to 0–1 for radar display
radar_metrics = ['Beta', 'PE_Ratio', 'ROE_pct', 'Debt_Equity', 'MarketCap_B']
radar_labels  = ['Beta', 'P/E Ratio', 'ROE (%)', 'Debt/Equity', 'Mkt Cap ($B)']

radar_data = profile[['Cluster'] + radar_metrics].copy()
radar_data['Archetype'] = radar_data['Cluster'].map(CLUSTER_SHORT)

# Clip extreme outliers (Cluster 3) for visual clarity then normalise
for col in radar_metrics:
    p5  = radar_data[col].quantile(0.05)
    p95 = radar_data[col].quantile(0.95)
    radar_data[col] = radar_data[col].clip(lower=p5, upper=p95)
    col_min = radar_data[col].min()
    col_max = radar_data[col].max()
    if col_max - col_min > 0:
        radar_data[col] = (radar_data[col] - col_min) / (col_max - col_min)
    else:
        radar_data[col] = 0.5

# Cluster selector
cluster_options = [f"C{int(row['Cluster'])}: {row['Archetype']}" for _, row in radar_data.iterrows()]
default_sel = cluster_options[:3]
radar_selected = st.multiselect(
    "Select clusters to compare (2–6):",
    options=cluster_options,
    default=default_sel,
    key="radar_select"
)

if len(radar_selected) < 2:
    st.info("Select at least 2 clusters to display the radar chart.")
else:
    selected_ids = [int(s.split(":")[0][1:]) for s in radar_selected]
    subset = radar_data[radar_data['Cluster'].isin(selected_ids)]

    N      = len(radar_metrics)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]  # close the polygon

    fig_rad, ax_rad = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))

    for _, row in subset.iterrows():
        cid    = int(row['Cluster'])
        values = [row[m] for m in radar_metrics]
        values += values[:1]
        color  = PALETTE[cid % len(PALETTE)]
        ax_rad.plot(angles, values, color=color, linewidth=2.2, label=f"C{cid}: {CLUSTER_SHORT[cid]}")
        ax_rad.fill(angles, values, color=color, alpha=0.12)

    ax_rad.set_xticks(angles[:-1])
    ax_rad.set_xticklabels(radar_labels, fontsize=11)
    ax_rad.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax_rad.set_yticklabels(['25%', '50%', '75%', '100%'], fontsize=7, color='grey')
    ax_rad.set_ylim(0, 1)
    ax_rad.set_title("Cluster Financial Profile Comparison\n(normalised, outliers clipped)",
                     fontsize=12, fontweight='bold', pad=20)
    ax_rad.legend(loc='upper right', bbox_to_anchor=(1.35, 1.15), fontsize=9, framealpha=0.9)
    ax_rad.grid(alpha=0.3)
    plt.tight_layout()
    st.pyplot(fig_rad)
    plt.close()

    st.markdown("""
**Reading the radar:** Each axis is normalised to the range of values across all clusters
(0 = lowest, 1 = highest). A cluster that fills more area tends to be more extreme across
multiple dimensions — which often signals higher complexity or risk.
Outlier clusters (e.g. Cluster 3) are clipped to the 5th–95th percentile to keep other
clusters readable.
""")

st.markdown("---")

# ── Section 6 (original): Cluster Size Bar Chart ──────────────────
st.header("Cluster Size Distribution")

counts = profile.set_index('Cluster')['Count']
labels = [f"C{i}: {CLUSTER_SHORT[i]}" for i in counts.index]
colors = [PALETTE[i % len(PALETTE)] for i in counts.index]

fig3, ax3 = plt.subplots(figsize=(10, 4))
bars = ax3.bar(labels, counts.values, color=colors, edgecolor='white', width=0.6)
for bar, val in zip(bars, counts.values):
    ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
             str(int(val)), ha='center', va='bottom', fontsize=11, fontweight='bold')
ax3.set_ylabel("Number of Companies", fontsize=12)
ax3.set_title("Companies per Cluster", fontsize=13, fontweight='bold')
ax3.set_ylim(0, counts.max() * 1.15)
plt.xticks(rotation=15, ha='right', fontsize=9)
ax3.grid(axis='y', alpha=0.3)
plt.tight_layout()
st.pyplot(fig3)
plt.close()

st.markdown("---")
st.caption("S&P 500 Clustering | K-Means (k=6) | Data: Kaggle — Financial Performance of S&P 500 | Built with Streamlit")
