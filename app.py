import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

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

@st.cache_data
def load_data():
    df       = pd.read_csv("sp500_clustered.csv")
    profile  = pd.read_csv("cluster_profiles.csv")
    crosstab = pd.read_csv("cluster_sector_crosstab_pct.csv")
    return df, profile, crosstab

df, profile, crosstab = load_data()
df['Cluster_Name'] = df['Cluster'].map(CLUSTER_SHORT)

# ── Sidebar ────────────────────────────────────────────────────────
st.sidebar.title("Controls")
st.sidebar.markdown("---")
all_names = [CLUSTER_SHORT[i] for i in sorted(CLUSTER_SHORT.keys())]
selected = st.sidebar.multiselect("Filter by Cluster", options=all_names, default=all_names)
filtered = df[df['Cluster_Name'].isin(selected)]
st.sidebar.markdown("---")
st.sidebar.markdown("**About**")
st.sidebar.markdown("K-Means clustering of 496 S&P 500 companies across 5 financial features: Beta, P/E Ratio, ROE, Debt/Equity, and Market Cap.")

# ── Header ─────────────────────────────────────────────────────────
st.title("S&P 500 Financial Behavior Clustering")
st.markdown("Exploring whether S&P 500 companies form natural groupings based on **financial behavior**, independent of traditional GICS sector labels.")
st.markdown("---")

# ── Section 1: Model Metrics ───────────────────────────────────────
st.header("Model Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Companies Analyzed", "496")
c2.metric("Clusters (k)", "6")
c3.metric("Silhouette Score", "0.2909")
c4.metric("Features Used", "5")
st.caption("Algorithm: K-Means | Preprocessing: Z-score scaling + PCA (8 components, 83.7% variance) | k selected via Elbow + Silhouette across k=2–8")
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
st.markdown("Each point is one company, colored by cluster. Axes are the first two principal components of the 5 financial features.")

if 'PCA1' not in df.columns or 'PCA2' not in df.columns:
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA as skPCA
    num_cols = [c for c in ['Beta_num','PE_num','ROE_num','DE_num','MarketCap_num'] if c in df.columns]
    tmp = df[num_cols].fillna(df[num_cols].median())
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
st.markdown("If clusters matched GICS sectors, each row would have one dominant sector. Mixed rows confirm clusters **cut across** sector boundaries.")

sector_cols = [c for c in crosstab.columns if c != 'Cluster']
data_arr = crosstab[sector_cols].values
row_labels = [f"C{int(r)}: {CLUSTER_SHORT[int(r)]}" for r in crosstab['Cluster']]

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
        out = results[show].rename(columns={
            'Cluster_Name':'Archetype','Beta_num':'Beta','PE_num':'P/E',
            'ROE_num':'ROE (%)','DE_num':'Debt/Equity','MarketCap_num':'Market Cap'
        }).reset_index(drop=True)
        st.dataframe(out, use_container_width=True, hide_index=True)
    else:
        st.warning(f"No company found matching '{search}'.")

# ── Section 6: Cluster Size Bar Chart ─────────────────────────────
st.markdown("---")
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
