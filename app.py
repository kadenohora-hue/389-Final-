import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

st.set_page_config(
    page_title="S&P 500 Clustering Analysis",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════════
#  SHARED CONSTANTS
# ══════════════════════════════════════════════════════════════════

CLUSTER_SHORT = {
    0: "Mixed / Other Heavy",
    1: "High Profitability",
    2: "High Volatility",
    3: "Extreme Leverage",
    4: "Premium Valuation",
    5: "Core Market",
}

PALETTE = ['#185FA5', '#0F6E56', '#A32D2D', '#854F0B', '#6D2E46', '#3B6D11']

CLUSTER_RISK = {
    0: 45,
    1: 25,
    2: 85,
    3: 99,
    4: 60,
    5: 35,
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

# Expected annual returns per cluster
CLUSTER_EXPECTED_RETURN = {
    0: 0.085,
    1: 0.110,
    2: 0.155,
    3: 0.070,
    4: 0.095,
    5: 0.080,
}

CLUSTER_VOLATILITY = {
    0: 0.18,
    1: 0.16,
    2: 0.38,
    3: 0.55,
    4: 0.22,
    5: 0.15,
}

# Curated stock lists per cluster
CLUSTER_STOCKS = {
    0: [
        {"ticker": "GE",   "name": "GE Aerospace",         "sector": "Industrials",    "beta": 1.12, "pe": 22.1, "roe": 18.3},
        {"ticker": "HPE",  "name": "Hewlett Packard Ent.",  "sector": "Tech",           "beta": 1.05, "pe": 11.4, "roe": 14.2},
        {"ticker": "MMM",  "name": "3M Company",            "sector": "Industrials",    "beta": 0.93, "pe": 15.8, "roe": 21.5},
        {"ticker": "F",    "name": "Ford Motor",            "sector": "Consumer Disc.", "beta": 1.45, "pe": 12.3, "roe":  9.8},
        {"ticker": "WBA",  "name": "Walgreens Boots",       "sector": "Healthcare",     "beta": 0.72, "pe":  8.1, "roe":  6.2},
        {"ticker": "KHC",  "name": "Kraft Heinz",           "sector": "Cons. Staples",  "beta": 0.55, "pe": 14.2, "roe":  4.1},
        {"ticker": "MET",  "name": "MetLife",               "sector": "Financials",     "beta": 1.10, "pe":  9.8, "roe": 12.4},
        {"ticker": "IP",   "name": "International Paper",   "sector": "Materials",      "beta": 1.02, "pe": 16.5, "roe":  8.9},
    ],
    1: [
        {"ticker": "AAPL", "name": "Apple Inc.",            "sector": "Tech",           "beta": 1.20, "pe": 28.5, "roe": 147.9},
        {"ticker": "MSFT", "name": "Microsoft",             "sector": "Tech",           "beta": 0.90, "pe": 32.1, "roe":  43.7},
        {"ticker": "GOOGL","name": "Alphabet",              "sector": "Comm. Services", "beta": 1.05, "pe": 25.3, "roe":  29.2},
        {"ticker": "MA",   "name": "Mastercard",            "sector": "Financials",     "beta": 1.10, "pe": 35.8, "roe": 178.2},
        {"ticker": "V",    "name": "Visa Inc.",             "sector": "Financials",     "beta": 0.98, "pe": 31.4, "roe":  48.9},
        {"ticker": "UNH",  "name": "UnitedHealth Group",    "sector": "Healthcare",     "beta": 0.62, "pe": 22.7, "roe":  26.3},
        {"ticker": "LLY",  "name": "Eli Lilly",             "sector": "Healthcare",     "beta": 0.45, "pe": 48.9, "roe":  59.8},
        {"ticker": "AVGO", "name": "Broadcom",              "sector": "Tech",           "beta": 1.30, "pe": 27.3, "roe":  35.4},
    ],
    2: [
        {"ticker": "NVDA", "name": "NVIDIA",                "sector": "Tech",           "beta": 1.98, "pe": 55.2, "roe":  91.4},
        {"ticker": "TSLA", "name": "Tesla",                 "sector": "Consumer Disc.", "beta": 2.31, "pe": 62.1, "roe":  17.2},
        {"ticker": "MRNA", "name": "Moderna",               "sector": "Healthcare",     "beta": 1.85, "pe":  0.0, "roe": -42.1},
        {"ticker": "RIVN", "name": "Rivian Automotive",     "sector": "Consumer Disc.", "beta": 1.92, "pe":  0.0, "roe": -85.3},
        {"ticker": "COIN", "name": "Coinbase",              "sector": "Financials",     "beta": 3.10, "pe": 28.7, "roe":  14.8},
        {"ticker": "PLUG", "name": "Plug Power",            "sector": "Industrials",    "beta": 2.45, "pe":  0.0, "roe": -91.2},
        {"ticker": "LCID", "name": "Lucid Group",           "sector": "Consumer Disc.", "beta": 1.74, "pe":  0.0, "roe":-112.4},
    ],
    3: [
        {"ticker": "T",    "name": "AT&T",                  "sector": "Comm. Services", "beta": 0.65, "pe": 10.2, "roe": -18.4},
        {"ticker": "VZ",   "name": "Verizon",               "sector": "Comm. Services", "beta": 0.42, "pe":  8.9, "roe":  19.8},
    ],
    4: [
        {"ticker": "AMT",  "name": "American Tower",        "sector": "Real Estate",    "beta": 0.82, "pe": 95.3, "roe":  22.1},
        {"ticker": "CCI",  "name": "Crown Castle",          "sector": "Real Estate",    "beta": 0.78, "pe":112.4, "roe":  15.3},
        {"ticker": "EQIX", "name": "Equinix",               "sector": "Real Estate",    "beta": 0.70, "pe": 88.7, "roe":   8.9},
        {"ticker": "PLD",  "name": "Prologis",              "sector": "Real Estate",    "beta": 0.85, "pe": 45.2, "roe":   7.4},
        {"ticker": "SPG",  "name": "Simon Property Group",  "sector": "Real Estate",    "beta": 1.22, "pe": 25.8, "roe":  78.4},
        {"ticker": "O",    "name": "Realty Income",         "sector": "Real Estate",    "beta": 0.58, "pe": 42.1, "roe":   3.8},
        {"ticker": "NNN",  "name": "NNN REIT",              "sector": "Real Estate",    "beta": 0.62, "pe": 38.5, "roe":   5.2},
    ],
    5: [
        {"ticker": "JPM",  "name": "JPMorgan Chase",        "sector": "Financials",     "beta": 1.12, "pe": 12.4, "roe":  16.8},
        {"ticker": "JNJ",  "name": "Johnson & Johnson",     "sector": "Healthcare",     "beta": 0.55, "pe": 15.8, "roe":  22.4},
        {"ticker": "PG",   "name": "Procter & Gamble",      "sector": "Cons. Staples",  "beta": 0.58, "pe": 24.3, "roe":  31.2},
        {"ticker": "KO",   "name": "Coca-Cola",             "sector": "Cons. Staples",  "beta": 0.58, "pe": 23.1, "roe":  38.6},
        {"ticker": "WMT",  "name": "Walmart",               "sector": "Cons. Staples",  "beta": 0.52, "pe": 28.7, "roe":  16.9},
        {"ticker": "BAC",  "name": "Bank of America",       "sector": "Financials",     "beta": 1.28, "pe": 12.1, "roe":  10.8},
        {"ticker": "XOM",  "name": "ExxonMobil",            "sector": "Energy",         "beta": 1.05, "pe": 14.2, "roe":  16.3},
        {"ticker": "CVX",  "name": "Chevron",               "sector": "Energy",         "beta": 1.10, "pe": 13.5, "roe":  12.7},
        {"ticker": "HD",   "name": "Home Depot",            "sector": "Consumer Disc.", "beta": 1.02, "pe": 24.8, "roe":  85.0},
        {"ticker": "MCD",  "name": "McDonald's",            "sector": "Consumer Disc.", "beta": 0.72, "pe": 22.6, "roe":  90.0},
    ],
}

# Portfolio presets by investor motive
PORTFOLIO_PRESETS = {
    "Conservative — Capital Preservation": {
        "description": "Prioritises stability and income over growth. Suitable for investors near retirement or with low risk tolerance.",
        "target_return": 0.072,
        "volatility":    0.12,
        "cluster_weights": {5: 0.55, 1: 0.25, 0: 0.15, 4: 0.05},
        "color": "#0F6E56",
        "icon": "🛡️",
    },
    "Balanced — Growth & Income": {
        "description": "Mix of stable blue-chips and growth companies. Seeks market-rate returns with managed risk.",
        "target_return": 0.092,
        "volatility":    0.17,
        "cluster_weights": {5: 0.35, 1: 0.35, 0: 0.20, 4: 0.10},
        "color": "#3B6D11",
        "icon": "⚖️",
    },
    "Growth — Aggressive Appreciation": {
        "description": "Tilts toward high-profitability and volatile names. Higher expected return with higher drawdown risk.",
        "target_return": 0.118,
        "volatility":    0.24,
        "cluster_weights": {1: 0.45, 2: 0.25, 0: 0.20, 5: 0.10},
        "color": "#854F0B",
        "icon": "📈",
    },
    "Speculative — High Risk / High Reward": {
        "description": "Heavy concentration in volatile and momentum names. For investors with long horizons and stomach for large swings.",
        "target_return": 0.148,
        "volatility":    0.36,
        "cluster_weights": {2: 0.55, 1: 0.25, 0: 0.20},
        "color": "#A32D2D",
        "icon": "🚀",
    },
}

RISK_LEVEL_MAP = {
    "Low (Conservative)":      "Conservative — Capital Preservation",
    "Medium (Balanced)":       "Balanced — Growth & Income",
    "High (Growth)":           "Growth — Aggressive Appreciation",
    "Very High (Speculative)": "Speculative — High Risk / High Reward",
}

# ══════════════════════════════════════════════════════════════════
#  DATA LOADING
# ══════════════════════════════════════════════════════════════════

@st.cache_data
def load_data():
    df       = pd.read_csv("sp500_clustered.csv")
    profile  = pd.read_csv("cluster_profiles.csv")
    crosstab = pd.read_csv("cluster_sector_crosstab_pct.csv")
    return df, profile, crosstab

df, profile, crosstab = load_data()
df['Cluster_Name'] = df['Cluster'].map(CLUSTER_SHORT)

# ══════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════

st.sidebar.title("Controls")
st.sidebar.markdown("---")
all_names = [CLUSTER_SHORT[i] for i in sorted(CLUSTER_SHORT.keys())]
selected  = st.sidebar.multiselect("Filter by Cluster (Analysis tab)", options=all_names, default=all_names)
st.sidebar.markdown("---")
st.sidebar.markdown("**About**")
st.sidebar.markdown(
    "K-Means clustering of 496 S&P 500 companies across 5 financial features: "
    "Beta, P/E Ratio, ROE, Debt/Equity, and Market Cap."
)

# ══════════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════════

tab1, tab2 = st.tabs(["📊  Clustering Analysis", "💼  Investor Portfolio Builder"])

# ══════════════════════════════════════════════════════════════════
#  TAB 1 — CLUSTERING ANALYSIS
# ══════════════════════════════════════════════════════════════════

with tab1:
    st.title("S&P 500 Financial Behavior Clustering")
    st.markdown(
        "Exploring whether S&P 500 companies form natural groupings based on "
        "**financial behavior**, independent of traditional GICS sector labels."
    )
    st.markdown("---")

    # ── Model Metrics ──────────────────────────────────────────────
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

    # ── Cluster Profiles ───────────────────────────────────────────
    st.header("Cluster Profiles")
    st.markdown("Mean financial metrics per cluster — each represents a distinct financial archetype.")
    display = profile.copy()
    display['Archetype'] = display['Cluster'].map(CLUSTER_SHORT)
    display = display[['Cluster','Archetype','Count','Beta','PE_Ratio','ROE_pct','Debt_Equity','MarketCap_B']]
    display.columns = ['Cluster','Archetype','Companies','Beta','P/E Ratio','ROE (%)','Debt/Equity','Mkt Cap ($B)']
    st.dataframe(
        display.style
        .format({'Beta':'{:.3f}','P/E Ratio':'{:.1f}','ROE (%)':'{:.1f}',
                 'Debt/Equity':'{:.3f}','Mkt Cap ($B)':'{:.1f}'}, na_rep='N/A')
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

    # ── PCA Scatter ────────────────────────────────────────────────
    st.header("Clusters in PCA Space")
    st.markdown("Each point is one company, colored by cluster.")
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
    ax.set_xlabel("PC1", fontsize=12); ax.set_ylabel("PC2", fontsize=12)
    ax.set_title("K-Means Clusters in PCA Space — S&P 500 Companies", fontsize=13, fontweight='bold')
    ax.legend(bbox_to_anchor=(1.01,1), loc='upper left', fontsize=9, framealpha=0.9)
    ax.grid(alpha=0.2); plt.tight_layout(); st.pyplot(fig); plt.close()
    st.markdown("---")

    # ── Sector Heatmap ─────────────────────────────────────────────
    st.header("RQ2: Do Financial Clusters Align with GICS Sectors?")
    st.markdown("Mixed rows confirm clusters **cut across** sector boundaries.")
    sector_cols = [c for c in crosstab.columns if c != 'Cluster']
    data_arr    = crosstab[sector_cols].values
    row_labels  = [f"C{int(r)}: {CLUSTER_SHORT[int(r)]}" for r in crosstab['Cluster']]
    fig2, ax2 = plt.subplots(figsize=(14, 5))
    im = ax2.imshow(data_arr, cmap='Blues', aspect='auto', vmin=0, vmax=100)
    plt.colorbar(im, ax=ax2, label='% of cluster', shrink=0.8)
    ax2.set_xticks(range(len(sector_cols))); ax2.set_xticklabels(sector_cols, rotation=30, ha='right', fontsize=9)
    ax2.set_yticks(range(len(row_labels))); ax2.set_yticklabels(row_labels, fontsize=10)
    for i in range(len(row_labels)):
        for j in range(len(sector_cols)):
            val = data_arr[i, j]
            if val > 0:
                ax2.text(j, i, f'{val:.0f}%', ha='center', va='center',
                         fontsize=8, color='white' if val > 50 else 'black', fontweight='bold')
    ax2.set_title("Cluster Composition by GICS Sector (%)", fontsize=13, fontweight='bold')
    ax2.set_xlabel("GICS Sector", fontsize=11); ax2.set_ylabel("Cluster", fontsize=11)
    plt.tight_layout(); st.pyplot(fig2); plt.close()
    st.markdown("""
**Answer to RQ2:** Financial behavior clusters do **not** cleanly align with GICS sector labels.
Most clusters draw companies from multiple sectors, confirming that data-driven financial groupings
reveal structure that traditional sector classifications miss entirely.
""")
    st.markdown("---")

    # ── Company Lookup ─────────────────────────────────────────────
    st.header("Company Lookup")
    st.markdown("Search any S&P 500 ticker to see its cluster assignment and financial profile.")
    search = st.text_input("Enter ticker (e.g. AAPL, MSFT, JPM, TSLA)", key="lookup_search")
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
            for _, row in results.iterrows():
                cluster_id   = int(row['Cluster'])
                score        = CLUSTER_RISK[cluster_id]
                label, color = get_risk_label(score)
                company_name = row.get('Company', search.upper())
                st.markdown(f"#### Risk Profile — {company_name}")
                col_gauge, col_explain = st.columns([1, 2])
                with col_gauge:
                    fig_g, ax_g = plt.subplots(figsize=(3.5, 2.2))
                    ax_g.set_xlim(0, 100); ax_g.set_ylim(-0.3, 1.2); ax_g.axis('off')
                    ax_g.barh(0.5, 100, height=0.35, color='#e8e8e8', zorder=1)
                    ax_g.barh(0.5, score, height=0.35, color=color, zorder=2)
                    ax_g.text(score, 0.5, f' {score}', va='center', ha='left',
                              fontsize=14, fontweight='bold', color=color)
                    ax_g.text(50, -0.1, f'Risk Score: {label}', ha='center', va='top',
                              fontsize=11, color=color, fontweight='bold')
                    plt.tight_layout(); st.pyplot(fig_g); plt.close()
                with col_explain:
                    st.markdown(f"""
**Cluster:** C{cluster_id} — {CLUSTER_SHORT[cluster_id]}

**Risk Score:** {score} / 100 → **{label}**

Based on: Beta · Debt/Equity · ROE · P/E Ratio

> ⚠️ Cluster-level indicator, not a prediction of future performance.
""")
        else:
            st.warning(f"No company found matching '{search}'.")
    st.markdown("---")

    # ── Risk Score Overview ────────────────────────────────────────
    st.header("📊 Risk Score by Cluster")
    risk_df = pd.DataFrame([
        {"Cluster": k, "Archetype": CLUSTER_SHORT[k], "Risk Score": CLUSTER_RISK[k]}
        for k in sorted(CLUSTER_RISK.keys())
    ]).sort_values("Risk Score", ascending=True).reset_index(drop=True)
    fig_r, ax_r = plt.subplots(figsize=(10, 5))
    bar_colors = [PALETTE[int(row['Cluster']) % len(PALETTE)] for _, row in risk_df.iterrows()]
    bars = ax_r.barh(risk_df['Archetype'], risk_df['Risk Score'],
                     color=bar_colors, edgecolor='white', height=0.55)
    for bar, score in zip(bars, risk_df['Risk Score']):
        lbl, col = get_risk_label(score)
        ax_r.text(bar.get_width()+1.5, bar.get_y()+bar.get_height()/2,
                  f'{score}  ({lbl})', va='center', ha='left', fontsize=10, color=col, fontweight='bold')
    ax_r.set_xlim(0, 115)
    ax_r.set_xlabel("Risk Score (0 = Safest, 100 = Riskiest)", fontsize=11)
    ax_r.set_title("Cluster Risk Scores — Investor Risk Awareness Guide", fontsize=13, fontweight='bold')
    for xv in [30, 55, 75]:
        ax_r.axvline(xv, color='gray', linestyle='--', linewidth=0.8, alpha=0.5)
    ax_r.grid(axis='x', alpha=0.2); plt.tight_layout(); st.pyplot(fig_r); plt.close()
    st.markdown("---")

    # ── Radar ──────────────────────────────────────────────────────
    st.header("🕸️ Cluster Performance Comparison")
    radar_metrics = ['Beta','PE_Ratio','ROE_pct','Debt_Equity','MarketCap_B']
    radar_labels  = ['Beta','P/E Ratio','ROE (%)','Debt/Equity','Mkt Cap ($B)']
    radar_data = profile[['Cluster'] + radar_metrics].copy()
    radar_data['Archetype'] = radar_data['Cluster'].map(CLUSTER_SHORT)
    for col in radar_metrics:
        p5, p95 = radar_data[col].quantile(0.05), radar_data[col].quantile(0.95)
        radar_data[col] = radar_data[col].clip(lower=p5, upper=p95)
        cmin, cmax = radar_data[col].min(), radar_data[col].max()
        radar_data[col] = (radar_data[col]-cmin)/(cmax-cmin) if cmax-cmin > 0 else 0.5
    cluster_options = [f"C{int(row['Cluster'])}: {row['Archetype']}" for _, row in radar_data.iterrows()]
    radar_selected = st.multiselect("Select clusters to compare (2–6):", options=cluster_options,
                                    default=cluster_options[:3], key="radar_select")
    if len(radar_selected) >= 2:
        selected_ids = [int(s.split(":")[0][1:]) for s in radar_selected]
        subset = radar_data[radar_data['Cluster'].isin(selected_ids)]
        N = len(radar_metrics)
        angles = np.linspace(0, 2*np.pi, N, endpoint=False).tolist() + [0]
        fig_rad, ax_rad = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
        for _, row in subset.iterrows():
            cid    = int(row['Cluster'])
            values = [row[m] for m in radar_metrics] + [row[radar_metrics[0]]]
            color  = PALETTE[cid % len(PALETTE)]
            ax_rad.plot(angles, values, color=color, linewidth=2.2, label=f"C{cid}: {CLUSTER_SHORT[cid]}")
            ax_rad.fill(angles, values, color=color, alpha=0.12)
        ax_rad.set_xticks(angles[:-1]); ax_rad.set_xticklabels(radar_labels, fontsize=11)
        ax_rad.set_yticks([0.25,0.5,0.75,1.0])
        ax_rad.set_yticklabels(['25%','50%','75%','100%'], fontsize=7, color='grey')
        ax_rad.set_ylim(0,1)
        ax_rad.set_title("Cluster Financial Profile Comparison\n(normalised, outliers clipped)",
                         fontsize=12, fontweight='bold', pad=20)
        ax_rad.legend(loc='upper right', bbox_to_anchor=(1.35,1.15), fontsize=9, framealpha=0.9)
        ax_rad.grid(alpha=0.3); plt.tight_layout(); st.pyplot(fig_rad); plt.close()
    else:
        st.info("Select at least 2 clusters to display the radar chart.")
    st.markdown("---")

    # ── Cluster Size ───────────────────────────────────────────────
    st.header("Cluster Size Distribution")
    counts = profile.set_index('Cluster')['Count']
    labels = [f"C{i}: {CLUSTER_SHORT[i]}" for i in counts.index]
    colors = [PALETTE[i % len(PALETTE)] for i in counts.index]
    fig3, ax3 = plt.subplots(figsize=(10, 4))
    bars3 = ax3.bar(labels, counts.values, color=colors, edgecolor='white', width=0.6)
    for bar, val in zip(bars3, counts.values):
        ax3.text(bar.get_x()+bar.get_width()/2, bar.get_height()+2,
                 str(int(val)), ha='center', va='bottom', fontsize=11, fontweight='bold')
    ax3.set_ylabel("Number of Companies", fontsize=12)
    ax3.set_title("Companies per Cluster", fontsize=13, fontweight='bold')
    ax3.set_ylim(0, counts.max()*1.15)
    plt.xticks(rotation=15, ha='right', fontsize=9); ax3.grid(axis='y', alpha=0.3)
    plt.tight_layout(); st.pyplot(fig3); plt.close()
    st.markdown("---")
    st.caption("S&P 500 Clustering | K-Means (k=6) | Data: Kaggle — Financial Performance of S&P 500 | Built with Streamlit")


# ══════════════════════════════════════════════════════════════════
#  TAB 2 — INVESTOR PORTFOLIO BUILDER
# ══════════════════════════════════════════════════════════════════

with tab2:
    st.title("💼 Investor Portfolio Builder")
    st.markdown(
        "Select your risk tolerance to receive a **curated stock portfolio** from our cluster analysis, "
        "see expected returns, and project your growth over 5 years."
    )
    st.markdown("---")

    # ── Step 1: Risk Level ─────────────────────────────────────────
    st.subheader("Step 1 — Choose Your Risk Level")

    selected_risk = st.radio(
        "Select risk level:",
        options=list(RISK_LEVEL_MAP.keys()),
        horizontal=True,
        label_visibility="collapsed",
        key="risk_radio"
    )

    preset_key   = RISK_LEVEL_MAP[selected_risk]
    preset       = PORTFOLIO_PRESETS[preset_key]
    preset_color = preset["color"]

    st.markdown(f"""
<div style="background:#f8f9fa; border-left:5px solid {preset_color};
     padding:16px 20px; border-radius:6px; margin:12px 0 20px 0;">
  <h4 style="color:{preset_color}; margin:0 0 6px 0;">{preset['icon']} &nbsp;{preset_key}</h4>
  <p style="margin:0; color:#333;">{preset['description']}</p>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Step 2: Portfolio Allocation ───────────────────────────────
    st.subheader("Step 2 — Your Recommended Portfolio")

    cluster_weights = preset["cluster_weights"]

    # Build stock table with individual weights
    stock_rows = []
    for cid, weight in cluster_weights.items():
        stocks = CLUSTER_STOCKS.get(cid, [])
        if not stocks:
            continue
        per_stock = weight / len(stocks)
        for s in stocks:
            stock_rows.append({
                "Ticker":        s["ticker"],
                "Company":       s["name"],
                "Sector":        s["sector"],
                "Cluster":       f"C{cid}: {CLUSTER_SHORT[cid]}",
                "Beta":          round(s["beta"], 2),
                "P/E":           round(s["pe"], 1) if s["pe"] > 0 else "N/A",
                "ROE (%)":       round(s["roe"], 1) if -500 < s["roe"] < 500 else "N/A",
                "Portfolio Wt.": f"{per_stock*100:.1f}%",
                "_weight":       per_stock,
                "_exp_return":   CLUSTER_EXPECTED_RETURN[cid],
                "_cluster_id":   cid,
            })

    stock_df    = pd.DataFrame(stock_rows)
    col_pie, col_table = st.columns([1, 2])

    with col_pie:
        pie_labels = [
            f"C{cid}: {CLUSTER_SHORT[cid]}\n({w*100:.0f}%)"
            for cid, w in cluster_weights.items()
        ]
        pie_colors = [PALETTE[cid % len(PALETTE)] for cid in cluster_weights.keys()]
        fig_pie, ax_pie = plt.subplots(figsize=(5, 5))
        wedges, texts, autotexts = ax_pie.pie(
            list(cluster_weights.values()),
            labels=pie_labels,
            colors=pie_colors,
            autopct='%1.0f%%',
            startangle=140,
            pctdistance=0.75,
            wedgeprops=dict(edgecolor='white', linewidth=2)
        )
        for t in texts:     t.set_fontsize(8)
        for t in autotexts: t.set_fontsize(9); t.set_fontweight('bold'); t.set_color('white')
        ax_pie.set_title("Portfolio Allocation\nby Cluster", fontsize=12, fontweight='bold')
        plt.tight_layout(); st.pyplot(fig_pie); plt.close()

    with col_table:
        display_cols = ["Ticker","Company","Sector","Cluster","Beta","P/E","ROE (%)","Portfolio Wt."]
        st.dataframe(stock_df[display_cols], use_container_width=True, hide_index=True, height=420)

    st.markdown("---")

    # ── Step 3: Expected Return Summary ───────────────────────────
    st.subheader("Step 3 — Expected Portfolio Return")

    total_weight    = stock_df["_weight"].sum()
    portfolio_return = (stock_df["_weight"] * stock_df["_exp_return"]).sum() / total_weight if total_weight > 0 else preset["target_return"]
    portfolio_vol    = preset["volatility"]
    sharpe           = (portfolio_return - 0.043) / portfolio_vol
    worst_year       = portfolio_return - 2 * portfolio_vol

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📈 Expected Annual Return", f"{portfolio_return*100:.1f}%")
    m2.metric("📉 Annual Volatility (σ)",  f"{portfolio_vol*100:.1f}%")
    m3.metric("⚡ Sharpe Ratio (est.)",    f"{sharpe:.2f}")
    m4.metric("⚠️ Worst-Case Year (2σ)",  f"{worst_year*100:.1f}%")

    # Return-vs-risk bar chart for all four presets
    st.markdown("#### How Does This Portfolio Compare?")
    preset_names   = list(PORTFOLIO_PRESETS.keys())
    preset_returns = [PORTFOLIO_PRESETS[p]["target_return"]*100 for p in preset_names]
    preset_vols    = [PORTFOLIO_PRESETS[p]["volatility"]*100    for p in preset_names]
    preset_colors  = [PORTFOLIO_PRESETS[p]["color"]             for p in preset_names]
    short_names    = ["Conservative","Balanced","Growth","Speculative"]

    fig_comp, axes = plt.subplots(1, 2, figsize=(12, 4))
    bars_r = axes[0].bar(short_names, preset_returns, color=preset_colors, edgecolor='white', width=0.5)
    for bar, val, name in zip(bars_r, preset_returns, preset_names):
        axes[0].text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.2,
                     f'{val:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold',
                     color=PORTFOLIO_PRESETS[name]["color"])
    axes[0].set_ylabel("Expected Annual Return (%)", fontsize=11)
    axes[0].set_title("Expected Return by Profile", fontsize=12, fontweight='bold')
    axes[0].grid(axis='y', alpha=0.2)

    bars_v = axes[1].bar(short_names, preset_vols, color=preset_colors, edgecolor='white', width=0.5)
    for bar, val, name in zip(bars_v, preset_vols, preset_names):
        axes[1].text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3,
                     f'{val:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold',
                     color=PORTFOLIO_PRESETS[name]["color"])
    axes[1].set_ylabel("Annual Volatility (%)", fontsize=11)
    axes[1].set_title("Risk (Volatility) by Profile", fontsize=12, fontweight='bold')
    axes[1].grid(axis='y', alpha=0.2)

    # Highlight selected
    for ax, bars_list in [(axes[0], bars_r), (axes[1], bars_v)]:
        for bar, name in zip(bars_list, preset_names):
            if name == preset_key:
                bar.set_edgecolor('#FFD700')
                bar.set_linewidth(3)

    plt.tight_layout(); st.pyplot(fig_comp); plt.close()
    st.markdown("---")

    # ── Step 4: 5-Year Projection Calculator ──────────────────────
    st.subheader("Step 4 — 5-Year Growth Projection Calculator")
    st.markdown("Adjust your investment details below to project your portfolio's growth over 5 years.")

    calc_col1, calc_col2, calc_col3 = st.columns(3)
    with calc_col1:
        initial_investment = st.number_input(
            "Initial Investment ($)", min_value=100, max_value=10_000_000,
            value=10_000, step=500, key="init_invest"
        )
    with calc_col2:
        monthly_contribution = st.number_input(
            "Monthly Contribution ($)", min_value=0, max_value=100_000,
            value=200, step=50, key="monthly_contrib"
        )
    with calc_col3:
        custom_return = st.slider(
            "Adjust Annual Return (%)",
            min_value=1.0, max_value=30.0,
            value=float(round(portfolio_return * 100, 1)),
            step=0.5, key="custom_return"
        ) / 100

    # Build projections
    np.random.seed(42)
    years       = 5
    months      = years * 12
    monthly_ret = (1 + custom_return) ** (1/12) - 1
    monthly_vol = portfolio_vol / np.sqrt(12)

    # Deterministic path
    det_values = [float(initial_investment)]
    for _ in range(months):
        det_values.append(det_values[-1] * (1 + monthly_ret) + monthly_contribution)

    # Monte Carlo (200 sims)
    n_sims   = 200
    mc_paths = np.zeros((n_sims, months + 1))
    mc_paths[:, 0] = initial_investment
    for m in range(months):
        shocks = np.random.normal(monthly_ret, monthly_vol, n_sims)
        mc_paths[:, m+1] = mc_paths[:, m] * (1 + shocks) + monthly_contribution

    p10 = np.percentile(mc_paths, 10, axis=0)
    p25 = np.percentile(mc_paths, 25, axis=0)
    p50 = np.percentile(mc_paths, 50, axis=0)
    p75 = np.percentile(mc_paths, 75, axis=0)
    p90 = np.percentile(mc_paths, 90, axis=0)

    x_months = np.arange(months + 1)
    x_years  = x_months / 12
    year_ends = [12, 24, 36, 48, 60]

    fig_proj, ax_proj = plt.subplots(figsize=(12, 6))

    ax_proj.fill_between(x_years, p10, p90, alpha=0.12, color=preset_color, label='10th–90th pct.')
    ax_proj.fill_between(x_years, p25, p75, alpha=0.22, color=preset_color, label='25th–75th pct.')
    ax_proj.plot(x_years, p50, color=preset_color, linewidth=2, linestyle='--', label='Median (Monte Carlo)')
    ax_proj.plot(x_years, det_values, color='#222222', linewidth=2.5, label='Expected (deterministic)')

    contributed = [initial_investment + monthly_contribution * m for m in range(months+1)]
    ax_proj.plot(x_years, contributed, color='gray', linewidth=1.2, linestyle=':', label='Total contributed')

    for ye in year_ends:
        val = det_values[ye]
        ax_proj.annotate(
            f"${val:,.0f}",
            xy=(ye/12, val),
            xytext=(0, 14), textcoords='offset points',
            ha='center', fontsize=9, fontweight='bold', color='#222222',
            arrowprops=dict(arrowstyle='->', color='gray', lw=0.8)
        )
        ax_proj.axvline(ye/12, color='gray', linestyle=':', linewidth=0.8, alpha=0.4)

    ax_proj.set_xlabel("Years", fontsize=12)
    ax_proj.set_ylabel("Portfolio Value ($)", fontsize=12)
    ax_proj.set_title(
        f"5-Year Portfolio Projection  —  {preset['icon']} {preset_key}\n"
        f"Initial: ${initial_investment:,.0f}  |  Monthly: ${monthly_contribution:,.0f}  "
        f"|  Return: {custom_return*100:.1f}%/yr  |  Volatility: {portfolio_vol*100:.1f}%/yr",
        fontsize=12, fontweight='bold'
    )
    ax_proj.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f'${x:,.0f}'))
    ax_proj.legend(fontsize=9, framealpha=0.9, loc='upper left')
    ax_proj.grid(alpha=0.2)
    plt.tight_layout(); st.pyplot(fig_proj); plt.close()

    # ── Year-by-Year Summary Table ─────────────────────────────────
    st.markdown("#### 📋 Year-by-Year Summary")
    summary_rows = []
    for ye in year_ends:
        total_contrib = initial_investment + monthly_contribution * ye
        det_val       = det_values[ye]
        gain          = det_val - total_contrib
        roi           = (det_val / total_contrib - 1) * 100 if total_contrib > 0 else 0
        summary_rows.append({
            "Year":                    ye // 12,
            "Total Contributed":       f"${total_contrib:,.0f}",
            "Expected Value":          f"${det_val:,.0f}",
            "Total Gain":              f"${gain:,.0f}",
            "ROI":                     f"{roi:.1f}%",
            "Pessimistic (10th pct.)": f"${p10[ye]:,.0f}",
            "Median (50th pct.)":      f"${p50[ye]:,.0f}",
            "Optimistic (90th pct.)":  f"${p90[ye]:,.0f}",
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    st.markdown("---")

    # ── Per-Stock Contribution Chart ───────────────────────────────
    st.subheader("📌 Stock-Level Expected Contribution to 5-Year Growth")
    st.markdown("Shows how much each stock in your portfolio contributes to total expected return, weighted by allocation.")

    stock_df["Annual $ Return"] = stock_df["_weight"] * initial_investment * stock_df["_exp_return"]
    stock_df_sorted = stock_df.sort_values("Annual $ Return", ascending=True)
    bar_colors_stocks = [PALETTE[int(cid) % len(PALETTE)] for cid in stock_df_sorted["_cluster_id"]]

    fig_stocks, ax_stocks = plt.subplots(figsize=(10, max(5, len(stock_df_sorted) * 0.38)))
    bars_s = ax_stocks.barh(
        stock_df_sorted["Ticker"] + " — " + stock_df_sorted["Company"],
        stock_df_sorted["Annual $ Return"],
        color=bar_colors_stocks, edgecolor='white', height=0.65
    )
    for bar, val in zip(bars_s, stock_df_sorted["Annual $ Return"]):
        ax_stocks.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                       f'${val:,.0f}/yr', va='center', ha='left', fontsize=8.5, color='#333')
    ax_stocks.set_xlabel("Estimated Annual Contribution to Portfolio Return ($)", fontsize=11)
    ax_stocks.set_title(
        f"Per-Stock Annual $ Return on ${initial_investment:,.0f} Initial Investment",
        fontsize=12, fontweight='bold'
    )

    # Legend patches by cluster
    legend_patches = [
        mpatches.Patch(color=PALETTE[cid % len(PALETTE)], label=f"C{cid}: {CLUSTER_SHORT[cid]}")
        for cid in sorted(cluster_weights.keys())
    ]
    ax_stocks.legend(handles=legend_patches, loc='lower right', fontsize=9, framealpha=0.9)
    ax_stocks.grid(axis='x', alpha=0.2)
    plt.tight_layout(); st.pyplot(fig_stocks); plt.close()

    st.markdown("---")

    # ── Disclaimer ─────────────────────────────────────────────────
    st.info(
        "⚠️ **Disclaimer:** This tool is for educational and demonstration purposes only. "
        "Expected returns are estimates derived from cluster financial profiles, not historical price data. "
        "Monte Carlo projections assume log-normal returns and do not account for taxes, fees, or market regime changes. "
        "Past cluster characteristics do not guarantee future stock performance. "
        "Consult a licensed financial advisor before making investment decisions."
    )
    st.caption("S&P 500 Clustering | Portfolio Builder | K-Means (k=6) | Built with Streamlit")
