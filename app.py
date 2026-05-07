import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io

st.set_page_config(
    page_title="S&P 500 Cluster Investor Platform",
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

CLUSTER_RISK = {0: 45, 1: 25, 2: 85, 3: 99, 4: 60, 5: 35}

CLUSTER_EXPECTED_RETURN = {0: 0.085, 1: 0.110, 2: 0.155, 3: 0.070, 4: 0.095, 5: 0.080}
CLUSTER_VOLATILITY      = {0: 0.18,  1: 0.16,  2: 0.38,  3: 0.55,  4: 0.22,  5: 0.15}

RISK_LABELS = {
    range(0,  30): ("Low",      "#0F6E56"),
    range(30, 55): ("Moderate", "#3B6D11"),
    range(55, 75): ("Elevated", "#854F0B"),
    range(75,101): ("High",     "#A32D2D"),
}

CLUSTER_DIVIDEND = {0: 2.1, 1: 0.8, 2: 0.2, 3: 5.8, 4: 3.9, 5: 2.4}  # avg dividend yield %

CLUSTER_PLAIN_ENGLISH = {
    0: {"emoji": "🔀", "name": "The All-Rounders",      "desc": "Companies that don't fit neatly into one box — they have a bit of everything. Think of them as the middle-of-the-road option. Not super risky, not super safe.", "analogy": "Like buying a diversified mutual fund — some ups, some downs, nothing extreme."},
    1: {"emoji": "💎", "name": "The Profit Machines",    "desc": "These are companies that make serious money and keep making it. High return on investment, well-managed, and usually household names.", "analogy": "Like owning a successful franchise — consistent profits year after year."},
    2: {"emoji": "🎢", "name": "The Wild Rides",         "desc": "Fast-moving, exciting companies that can double your money — or cut it in half. Very high risk, very high potential reward.", "analogy": "Like betting on a startup. Huge upside, but buckle up."},
    3: {"emoji": "⚠️",  "name": "The Debt-Heavy Ones",   "desc": "These companies carry an enormous amount of debt. Two companies in the entire S&P 500 are this extreme. Approach with caution.", "analogy": "Like someone who owns a mansion but owes the bank 10x what it's worth."},
    4: {"emoji": "🏙️", "name": "The Premium Properties", "desc": "Mostly real estate investment trusts (REITs). You're paying a high price for stability and regular dividend income — like a landlord that pays you rent.", "analogy": "Like buying a rental property in a prime location. Expensive, but steady income."},
    5: {"emoji": "🏦", "name": "The Steady Giants",      "desc": "The backbone of the stock market. Large, stable, well-known companies. Not flashy, but reliable. These are the companies your grandparents probably owned.", "analogy": "Like putting money in a savings account that actually grows."},
}

def get_risk_label(score):
    for r, (label, color) in RISK_LABELS.items():
        if int(score) in r:
            return label, color
    return "High", "#A32D2D"

# ── All stocks flat lookup ─────────────────────────────────────────
CLUSTER_STOCKS = {
    0: [
        {"ticker":"GE",   "name":"GE Aerospace",        "sector":"Industrials",    "beta":1.12,"pe":22.1,"roe":18.3,"div":0.8},
        {"ticker":"HPE",  "name":"Hewlett Packard Ent.", "sector":"Tech",           "beta":1.05,"pe":11.4,"roe":14.2,"div":2.9},
        {"ticker":"MMM",  "name":"3M Company",           "sector":"Industrials",    "beta":0.93,"pe":15.8,"roe":21.5,"div":5.4},
        {"ticker":"F",    "name":"Ford Motor",           "sector":"Consumer Disc.", "beta":1.45,"pe":12.3,"roe": 9.8,"div":4.8},
        {"ticker":"WBA",  "name":"Walgreens Boots",      "sector":"Healthcare",     "beta":0.72,"pe": 8.1,"roe": 6.2,"div":6.2},
        {"ticker":"KHC",  "name":"Kraft Heinz",          "sector":"Cons. Staples",  "beta":0.55,"pe":14.2,"roe": 4.1,"div":4.5},
        {"ticker":"MET",  "name":"MetLife",              "sector":"Financials",     "beta":1.10,"pe": 9.8,"roe":12.4,"div":3.1},
        {"ticker":"IP",   "name":"International Paper",  "sector":"Materials",      "beta":1.02,"pe":16.5,"roe": 8.9,"div":4.0},
    ],
    1: [
        {"ticker":"AAPL", "name":"Apple Inc.",           "sector":"Tech",           "beta":1.20,"pe":28.5,"roe":147.9,"div":0.5},
        {"ticker":"MSFT", "name":"Microsoft",            "sector":"Tech",           "beta":0.90,"pe":32.1,"roe": 43.7,"div":0.7},
        {"ticker":"GOOGL","name":"Alphabet",             "sector":"Comm. Services", "beta":1.05,"pe":25.3,"roe": 29.2,"div":0.0},
        {"ticker":"MA",   "name":"Mastercard",           "sector":"Financials",     "beta":1.10,"pe":35.8,"roe":178.2,"div":0.5},
        {"ticker":"V",    "name":"Visa Inc.",            "sector":"Financials",     "beta":0.98,"pe":31.4,"roe": 48.9,"div":0.7},
        {"ticker":"UNH",  "name":"UnitedHealth Group",   "sector":"Healthcare",     "beta":0.62,"pe":22.7,"roe": 26.3,"div":1.5},
        {"ticker":"LLY",  "name":"Eli Lilly",            "sector":"Healthcare",     "beta":0.45,"pe":48.9,"roe": 59.8,"div":0.6},
        {"ticker":"AVGO", "name":"Broadcom",             "sector":"Tech",           "beta":1.30,"pe":27.3,"roe": 35.4,"div":1.4},
    ],
    2: [
        {"ticker":"NVDA", "name":"NVIDIA",               "sector":"Tech",           "beta":1.98,"pe":55.2,"roe": 91.4,"div":0.03},
        {"ticker":"TSLA", "name":"Tesla",                "sector":"Consumer Disc.", "beta":2.31,"pe":62.1,"roe": 17.2,"div":0.0},
        {"ticker":"MRNA", "name":"Moderna",              "sector":"Healthcare",     "beta":1.85,"pe": 0.0,"roe":-42.1,"div":0.0},
        {"ticker":"RIVN", "name":"Rivian Automotive",    "sector":"Consumer Disc.", "beta":1.92,"pe": 0.0,"roe":-85.3,"div":0.0},
        {"ticker":"COIN", "name":"Coinbase",             "sector":"Financials",     "beta":3.10,"pe":28.7,"roe": 14.8,"div":0.0},
        {"ticker":"PLUG", "name":"Plug Power",           "sector":"Industrials",    "beta":2.45,"pe": 0.0,"roe":-91.2,"div":0.0},
        {"ticker":"LCID", "name":"Lucid Group",          "sector":"Consumer Disc.", "beta":1.74,"pe": 0.0,"roe":-112.4,"div":0.0},
    ],
    3: [
        {"ticker":"T",    "name":"AT&T",                 "sector":"Comm. Services", "beta":0.65,"pe":10.2,"roe":-18.4,"div":6.5},
        {"ticker":"VZ",   "name":"Verizon",              "sector":"Comm. Services", "beta":0.42,"pe": 8.9,"roe": 19.8,"div":6.8},
    ],
    4: [
        {"ticker":"AMT",  "name":"American Tower",       "sector":"Real Estate",    "beta":0.82,"pe": 95.3,"roe": 22.1,"div":3.1},
        {"ticker":"CCI",  "name":"Crown Castle",         "sector":"Real Estate",    "beta":0.78,"pe":112.4,"roe": 15.3,"div":5.8},
        {"ticker":"EQIX", "name":"Equinix",              "sector":"Real Estate",    "beta":0.70,"pe": 88.7,"roe":  8.9,"div":2.0},
        {"ticker":"PLD",  "name":"Prologis",             "sector":"Real Estate",    "beta":0.85,"pe": 45.2,"roe":  7.4,"div":3.2},
        {"ticker":"SPG",  "name":"Simon Property",       "sector":"Real Estate",    "beta":1.22,"pe": 25.8,"roe": 78.4,"div":5.5},
        {"ticker":"O",    "name":"Realty Income",        "sector":"Real Estate",    "beta":0.58,"pe": 42.1,"roe":  3.8,"div":5.9},
        {"ticker":"NNN",  "name":"NNN REIT",             "sector":"Real Estate",    "beta":0.62,"pe": 38.5,"roe":  5.2,"div":5.4},
    ],
    5: [
        {"ticker":"JPM",  "name":"JPMorgan Chase",       "sector":"Financials",     "beta":1.12,"pe":12.4,"roe": 16.8,"div":2.3},
        {"ticker":"JNJ",  "name":"Johnson & Johnson",    "sector":"Healthcare",     "beta":0.55,"pe":15.8,"roe": 22.4,"div":3.0},
        {"ticker":"PG",   "name":"Procter & Gamble",     "sector":"Cons. Staples",  "beta":0.58,"pe":24.3,"roe": 31.2,"div":2.4},
        {"ticker":"KO",   "name":"Coca-Cola",            "sector":"Cons. Staples",  "beta":0.58,"pe":23.1,"roe": 38.6,"div":3.1},
        {"ticker":"WMT",  "name":"Walmart",              "sector":"Cons. Staples",  "beta":0.52,"pe":28.7,"roe": 16.9,"div":1.3},
        {"ticker":"BAC",  "name":"Bank of America",      "sector":"Financials",     "beta":1.28,"pe":12.1,"roe": 10.8,"div":2.5},
        {"ticker":"XOM",  "name":"ExxonMobil",           "sector":"Energy",         "beta":1.05,"pe":14.2,"roe": 16.3,"div":3.5},
        {"ticker":"CVX",  "name":"Chevron",              "sector":"Energy",         "beta":1.10,"pe":13.5,"roe": 12.7,"div":4.0},
        {"ticker":"HD",   "name":"Home Depot",           "sector":"Consumer Disc.", "beta":1.02,"pe":24.8,"roe": 85.0,"div":2.4},
        {"ticker":"MCD",  "name":"McDonald's",           "sector":"Consumer Disc.", "beta":0.72,"pe":22.6,"roe": 90.0,"div":2.3},
    ],
}

# Flat ticker→cluster lookup
TICKER_TO_CLUSTER = {}
TICKER_TO_INFO    = {}
for cid, stocks in CLUSTER_STOCKS.items():
    for s in stocks:
        TICKER_TO_CLUSTER[s["ticker"]] = cid
        TICKER_TO_INFO[s["ticker"]]    = {**s, "cluster": cid}

ALL_TICKERS = sorted(TICKER_TO_CLUSTER.keys())

PORTFOLIO_PRESETS = {
    "Conservative — Capital Preservation": {
        "description": "Prioritises stability and income over growth. Suitable for investors near retirement or with low risk tolerance.",
        "target_return": 0.072, "volatility": 0.12,
        "cluster_weights": {5: 0.55, 1: 0.25, 0: 0.15, 4: 0.05},
        "color": "#0F6E56", "icon": "🛡️",
    },
    "Balanced — Growth & Income": {
        "description": "Mix of stable blue-chips and growth companies. Seeks market-rate returns with managed risk.",
        "target_return": 0.092, "volatility": 0.17,
        "cluster_weights": {5: 0.35, 1: 0.35, 0: 0.20, 4: 0.10},
        "color": "#3B6D11", "icon": "⚖️",
    },
    "Growth — Aggressive Appreciation": {
        "description": "Tilts toward high-profitability and volatile names. Higher expected return with higher drawdown risk.",
        "target_return": 0.118, "volatility": 0.24,
        "cluster_weights": {1: 0.45, 2: 0.25, 0: 0.20, 5: 0.10},
        "color": "#854F0B", "icon": "📈",
    },
    "Speculative — High Risk / High Reward": {
        "description": "Heavy concentration in volatile and momentum names. For investors with long horizons and stomach for large swings.",
        "target_return": 0.148, "volatility": 0.36,
        "cluster_weights": {2: 0.55, 1: 0.25, 0: 0.20},
        "color": "#A32D2D", "icon": "🚀",
    },
}

RISK_LEVEL_MAP = {
    "Low (Conservative)":      "Conservative — Capital Preservation",
    "Medium (Balanced)":       "Balanced — Growth & Income",
    "High (Growth)":           "Growth — Aggressive Appreciation",
    "Very High (Speculative)": "Speculative — High Risk / High Reward",
}

# ── Monte Carlo helper ────────────────────────────────────────────
def run_projection(initial, monthly_contrib, annual_ret, annual_vol, years=5, n_sims=200):
    months      = years * 12
    monthly_ret = (1 + annual_ret) ** (1/12) - 1
    monthly_vol = annual_vol / np.sqrt(12)
    np.random.seed(42)
    det = [float(initial)]
    for _ in range(months):
        det.append(det[-1] * (1 + monthly_ret) + monthly_contrib)
    mc = np.zeros((n_sims, months + 1))
    mc[:, 0] = initial
    for m in range(months):
        shocks = np.random.normal(monthly_ret, monthly_vol, n_sims)
        mc[:, m+1] = mc[:, m] * (1 + shocks) + monthly_contrib
    return det, mc

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
st.sidebar.title("🏦 S&P 500 Platform")
st.sidebar.markdown("---")
all_names = [CLUSTER_SHORT[i] for i in sorted(CLUSTER_SHORT.keys())]
selected  = st.sidebar.multiselect("Filter Clusters (Analysis tab)", options=all_names, default=all_names)
st.sidebar.markdown("---")
st.sidebar.markdown("**About**")
st.sidebar.markdown("K-Means clustering of 496 S&P 500 companies across 5 financial features: Beta, P/E, ROE, Debt/Equity, Market Cap.")
st.sidebar.markdown("---")
st.sidebar.caption("⚠️ Educational tool only. Not financial advice.")

# ══════════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Clustering Analysis",
    "💼 Portfolio Builder",
    "🛠️ Custom Portfolio",
    "🔍 Analyze My Portfolio",
    "📖 Plain English Guide",
])

# ══════════════════════════════════════════════════════════════════
#  TAB 1 — CLUSTERING ANALYSIS
# ══════════════════════════════════════════════════════════════════
with tab1:
    st.title("S&P 500 Financial Behavior Clustering")
    st.markdown("Exploring whether S&P 500 companies form natural groupings based on **financial behavior**, independent of traditional GICS sector labels.")
    st.markdown("---")

    st.header("Model Overview")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Companies Analyzed","496"); c2.metric("Clusters (k)","6")
    c3.metric("Silhouette Score","0.2909"); c4.metric("Features Used","5")
    st.caption("Algorithm: K-Means | Preprocessing: Z-score scaling + PCA (8 components, 83.7% variance) | k selected via Elbow + Silhouette across k=2–8")
    st.markdown("---")

    st.header("Cluster Profiles")
    display = profile.copy()
    display['Archetype'] = display['Cluster'].map(CLUSTER_SHORT)
    display = display[['Cluster','Archetype','Count','Beta','PE_Ratio','ROE_pct','Debt_Equity','MarketCap_B']]
    display.columns = ['Cluster','Archetype','Companies','Beta','P/E Ratio','ROE (%)','Debt/Equity','Mkt Cap ($B)']
    st.dataframe(
        display.style
        .format({'Beta':'{:.3f}','P/E Ratio':'{:.1f}','ROE (%)':'{:.1f}','Debt/Equity':'{:.3f}','Mkt Cap ($B)':'{:.1f}'}, na_rep='N/A')
        .background_gradient(subset=['Beta','ROE (%)'], cmap='RdYlGn')
        .background_gradient(subset=['Debt/Equity'], cmap='OrRd'),
        use_container_width=True, hide_index=True)
    st.markdown("---")

    st.header("Clusters in PCA Space")
    if 'PCA1' not in df.columns or 'PCA2' not in df.columns:
        from sklearn.preprocessing import StandardScaler
        from sklearn.decomposition import PCA as skPCA
        num_cols = [c for c in ['Beta_num','PE_num','ROE_num','DE_num','MarketCap_num'] if c in df.columns]
        tmp = df[num_cols].fillna(df[num_cols].median())
        scaled = StandardScaler().fit_transform(tmp)
        coords = skPCA(n_components=2, random_state=42).fit_transform(scaled)
        df['PCA1'], df['PCA2'] = coords[:,0], coords[:,1]
    filtered = df[df['Cluster_Name'].isin(selected)]
    fig, ax = plt.subplots(figsize=(10,6))
    for i in sorted(df['Cluster'].unique()):
        if CLUSTER_SHORT[i] not in selected: continue
        mask = filtered['Cluster']==i
        ax.scatter(filtered.loc[mask,'PCA1'], filtered.loc[mask,'PCA2'],
                   c=PALETTE[i%len(PALETTE)], label=f"C{i}: {CLUSTER_SHORT[i]}", alpha=0.65, s=45, edgecolors='white', linewidths=0.3)
    ax.set_xlabel("PC1",fontsize=12); ax.set_ylabel("PC2",fontsize=12)
    ax.set_title("K-Means Clusters in PCA Space",fontsize=13,fontweight='bold')
    ax.legend(bbox_to_anchor=(1.01,1), loc='upper left', fontsize=9, framealpha=0.9)
    ax.grid(alpha=0.2); plt.tight_layout(); st.pyplot(fig); plt.close()
    st.markdown("---")

    st.header("RQ2: Do Financial Clusters Align with GICS Sectors?")
    sector_cols = [c for c in crosstab.columns if c!='Cluster']
    data_arr    = crosstab[sector_cols].values
    row_labels  = [f"C{int(r)}: {CLUSTER_SHORT[int(r)]}" for r in crosstab['Cluster']]
    fig2,ax2 = plt.subplots(figsize=(14,5))
    im = ax2.imshow(data_arr,cmap='Blues',aspect='auto',vmin=0,vmax=100)
    plt.colorbar(im,ax=ax2,label='% of cluster',shrink=0.8)
    ax2.set_xticks(range(len(sector_cols))); ax2.set_xticklabels(sector_cols,rotation=30,ha='right',fontsize=9)
    ax2.set_yticks(range(len(row_labels))); ax2.set_yticklabels(row_labels,fontsize=10)
    for i in range(len(row_labels)):
        for j in range(len(sector_cols)):
            val=data_arr[i,j]
            if val>0: ax2.text(j,i,f'{val:.0f}%',ha='center',va='center',fontsize=8,color='white' if val>50 else 'black',fontweight='bold')
    ax2.set_title("Cluster Composition by GICS Sector (%)",fontsize=13,fontweight='bold')
    plt.tight_layout(); st.pyplot(fig2); plt.close()
    st.success("**Key Finding:** No cluster is more than 40% any single sector. Financial behavior clusters cut straight across GICS boundaries — the structure is financial, not industrial.")
    st.markdown("---")

    st.header("Company Lookup")
    search = st.text_input("Enter ticker or company name (e.g. AAPL, Tesla)", key="lookup_search")
    if search:
        results = df[df['Company'].str.upper().str.contains(search.strip().upper(), na=False)]
        if not results.empty:
            show = [c for c in ['Company','Sector','Cluster','Cluster_Name','Beta_num','PE_num','ROE_num','DE_num','MarketCap_num'] if c in results.columns]
            st.dataframe(results[show].rename(columns={'Cluster_Name':'Archetype','Beta_num':'Beta','PE_num':'P/E','ROE_num':'ROE (%)','DE_num':'Debt/Equity','MarketCap_num':'Market Cap'}).reset_index(drop=True), use_container_width=True, hide_index=True)
            for _, row in results.iterrows():
                cid = int(row['Cluster']); score = CLUSTER_RISK[cid]; label, color = get_risk_label(score)
                st.markdown(f"#### Risk Profile — {row.get('Company', search.upper())}")
                cg, ce = st.columns([1,2])
                with cg:
                    fg,ag = plt.subplots(figsize=(3.5,2.2)); ag.set_xlim(0,100); ag.set_ylim(-0.3,1.2); ag.axis('off')
                    ag.barh(0.5,100,height=0.35,color='#e8e8e8',zorder=1); ag.barh(0.5,score,height=0.35,color=color,zorder=2)
                    ag.text(score,0.5,f' {score}',va='center',ha='left',fontsize=14,fontweight='bold',color=color)
                    ag.text(50,-0.1,f'Risk Score: {label}',ha='center',va='top',fontsize=11,color=color,fontweight='bold')
                    plt.tight_layout(); st.pyplot(fg); plt.close()
                with ce:
                    st.markdown(f"**Cluster:** C{cid} — {CLUSTER_SHORT[cid]}\n\n**Risk Score:** {score}/100 → **{label}**\n\nBased on: Beta · Debt/Equity · ROE · P/E\n\n> ⚠️ Cluster-level indicator only.")
        else:
            st.warning(f"No company found matching '{search}'.")
    st.markdown("---")

    st.header("📊 Risk Score by Cluster")
    risk_df = pd.DataFrame([{"Cluster":k,"Archetype":CLUSTER_SHORT[k],"Risk Score":CLUSTER_RISK[k]} for k in sorted(CLUSTER_RISK)]).sort_values("Risk Score",ascending=True).reset_index(drop=True)
    fig_r,ax_r = plt.subplots(figsize=(10,5))
    bcolors = [PALETTE[int(r['Cluster'])%len(PALETTE)] for _,r in risk_df.iterrows()]
    bars_r = ax_r.barh(risk_df['Archetype'],risk_df['Risk Score'],color=bcolors,edgecolor='white',height=0.55)
    for bar,score in zip(bars_r,risk_df['Risk Score']):
        lbl,col = get_risk_label(score)
        ax_r.text(bar.get_width()+1.5,bar.get_y()+bar.get_height()/2,f'{score}  ({lbl})',va='center',ha='left',fontsize=10,color=col,fontweight='bold')
    ax_r.set_xlim(0,115); ax_r.set_xlabel("Risk Score",fontsize=11); ax_r.set_title("Cluster Risk Scores",fontsize=13,fontweight='bold')
    for xv in [30,55,75]: ax_r.axvline(xv,color='gray',linestyle='--',linewidth=0.8,alpha=0.5)
    ax_r.grid(axis='x',alpha=0.2); plt.tight_layout(); st.pyplot(fig_r); plt.close()
    st.markdown("---")

    st.header("🕸️ Cluster Performance Comparison")
    radar_metrics=['Beta','PE_Ratio','ROE_pct','Debt_Equity','MarketCap_B']; radar_labels=['Beta','P/E','ROE (%)','D/E','Mkt Cap']
    rd = profile[['Cluster']+radar_metrics].copy(); rd['Archetype']=rd['Cluster'].map(CLUSTER_SHORT)
    for col in radar_metrics:
        p5,p95=rd[col].quantile(0.05),rd[col].quantile(0.95); rd[col]=rd[col].clip(p5,p95)
        cmin,cmax=rd[col].min(),rd[col].max(); rd[col]=(rd[col]-cmin)/(cmax-cmin) if cmax-cmin>0 else 0.5
    ropts=[f"C{int(r['Cluster'])}: {r['Archetype']}" for _,r in rd.iterrows()]
    rsel=st.multiselect("Select clusters to compare:",options=ropts,default=ropts[:3],key="radar_t1")
    if len(rsel)>=2:
        sids=[int(s.split(":")[0][1:]) for s in rsel]; sub=rd[rd['Cluster'].isin(sids)]
        N=len(radar_metrics); angles=np.linspace(0,2*np.pi,N,endpoint=False).tolist()+[0]
        fig_rad,ax_rad=plt.subplots(figsize=(7,7),subplot_kw=dict(polar=True))
        for _,row in sub.iterrows():
            cid=int(row['Cluster']); vals=[row[m] for m in radar_metrics]+[row[radar_metrics[0]]]
            ax_rad.plot(angles,vals,color=PALETTE[cid%len(PALETTE)],linewidth=2.2,label=f"C{cid}: {CLUSTER_SHORT[cid]}")
            ax_rad.fill(angles,vals,color=PALETTE[cid%len(PALETTE)],alpha=0.12)
        ax_rad.set_xticks(angles[:-1]); ax_rad.set_xticklabels(radar_labels,fontsize=11)
        ax_rad.set_yticks([0.25,0.5,0.75,1.0]); ax_rad.set_yticklabels(['25%','50%','75%','100%'],fontsize=7,color='grey')
        ax_rad.set_ylim(0,1); ax_rad.legend(loc='upper right',bbox_to_anchor=(1.35,1.15),fontsize=9); ax_rad.grid(alpha=0.3)
        plt.tight_layout(); st.pyplot(fig_rad); plt.close()
    st.markdown("---")
    st.caption("S&P 500 Clustering | K-Means (k=6) | Built with Streamlit")

# ══════════════════════════════════════════════════════════════════
#  TAB 2 — PRESET PORTFOLIO BUILDER
# ══════════════════════════════════════════════════════════════════
with tab2:
    st.title("💼 Investor Portfolio Builder")
    st.markdown("Select your risk tolerance to get a curated stock portfolio, expected returns, and a 5-year growth projection.")
    st.markdown("---")

    st.subheader("Step 1 — Choose Your Risk Level")
    selected_risk = st.radio("", options=list(RISK_LEVEL_MAP.keys()), horizontal=True, key="risk_radio")
    preset_key = RISK_LEVEL_MAP[selected_risk]; preset = PORTFOLIO_PRESETS[preset_key]; preset_color = preset["color"]
    st.markdown(f"""<div style="background:#f8f9fa;border-left:5px solid {preset_color};padding:16px 20px;border-radius:6px;margin:12px 0 20px 0;">
    <h4 style="color:{preset_color};margin:0 0 6px 0;">{preset['icon']} &nbsp;{preset_key}</h4>
    <p style="margin:0;color:#333;">{preset['description']}</p></div>""", unsafe_allow_html=True)
    st.markdown("---")

    st.subheader("Step 2 — Your Recommended Portfolio")
    cluster_weights = preset["cluster_weights"]
    stock_rows = []
    for cid, weight in cluster_weights.items():
        stocks = CLUSTER_STOCKS.get(cid, [])
        if not stocks: continue
        per_stock = weight / len(stocks)
        for s in stocks:
            stock_rows.append({"Ticker":s["ticker"],"Company":s["name"],"Sector":s["sector"],
                "Cluster":f"C{cid}: {CLUSTER_SHORT[cid]}","Beta":round(s["beta"],2),
                "P/E":round(s["pe"],1) if s["pe"]>0 else "N/A","ROE (%)":round(s["roe"],1) if -500<s["roe"]<500 else "N/A",
                "Div Yield %":round(s["div"],1),"Portfolio Wt.":f"{per_stock*100:.1f}%",
                "_weight":per_stock,"_exp_return":CLUSTER_EXPECTED_RETURN[cid],"_cluster_id":cid})
    stock_df = pd.DataFrame(stock_rows)

    col_pie, col_table = st.columns([1,2])
    with col_pie:
        fig_pie,ax_pie=plt.subplots(figsize=(5,5))
        pie_labels=[f"C{cid}: {CLUSTER_SHORT[cid]}\n({w*100:.0f}%)" for cid,w in cluster_weights.items()]
        pie_colors=[PALETTE[cid%len(PALETTE)] for cid in cluster_weights.keys()]
        wedges,texts,autotexts=ax_pie.pie(list(cluster_weights.values()),labels=pie_labels,colors=pie_colors,autopct='%1.0f%%',startangle=140,pctdistance=0.75,wedgeprops=dict(edgecolor='white',linewidth=2))
        for t in texts: t.set_fontsize(8)
        for t in autotexts: t.set_fontsize(9); t.set_fontweight('bold'); t.set_color('white')
        ax_pie.set_title("Portfolio Allocation\nby Cluster",fontsize=12,fontweight='bold')
        plt.tight_layout(); st.pyplot(fig_pie); plt.close()
    with col_table:
        st.dataframe(stock_df[["Ticker","Company","Sector","Cluster","Beta","P/E","ROE (%)","Div Yield %","Portfolio Wt."]], use_container_width=True, hide_index=True, height=420)

    # Sector concentration warning
    sector_counts = stock_df.groupby("Sector")["_weight"].sum().reset_index()
    sector_counts.columns = ["Sector","Weight"]
    max_sector = sector_counts.loc[sector_counts["Weight"].idxmax()]
    if max_sector["Weight"] > 0.35:
        st.warning(f"⚠️ **Sector Concentration Warning:** {max_sector['Sector']} represents {max_sector['Weight']*100:.0f}% of your portfolio — above the recommended 35% cap. Consider diversifying.")
    st.markdown("---")

    st.subheader("Step 3 — Expected Portfolio Return")
    total_weight = stock_df["_weight"].sum()
    portfolio_return = (stock_df["_weight"]*stock_df["_exp_return"]).sum()/total_weight if total_weight>0 else preset["target_return"]
    portfolio_vol = preset["volatility"]
    sharpe = (portfolio_return-0.043)/portfolio_vol
    worst_year = portfolio_return - 2*portfolio_vol
    weighted_div = (stock_df["_weight"]*stock_df["Div Yield %"]).sum()/total_weight if "Div Yield %" in stock_df else 0

    m1,m2,m3,m4,m5 = st.columns(5)
    m1.metric("📈 Expected Annual Return",f"{portfolio_return*100:.1f}%")
    m2.metric("📉 Annual Volatility (σ)",f"{portfolio_vol*100:.1f}%")
    m3.metric("⚡ Sharpe Ratio",f"{sharpe:.2f}")
    m4.metric("⚠️ Worst-Case Year (2σ)",f"{worst_year*100:.1f}%")
    m5.metric("💰 Avg Dividend Yield",f"{weighted_div:.1f}%")

    # Return vs risk comparison
    st.markdown("#### How Does This Compare?")
    pnames=list(PORTFOLIO_PRESETS.keys()); preturns=[PORTFOLIO_PRESETS[p]["target_return"]*100 for p in pnames]
    pvols=[PORTFOLIO_PRESETS[p]["volatility"]*100 for p in pnames]; pcolors=[PORTFOLIO_PRESETS[p]["color"] for p in pnames]
    snames=["Conservative","Balanced","Growth","Speculative"]
    fig_c,axes=plt.subplots(1,2,figsize=(12,4))
    for ax,vals,title,ylabel in [(axes[0],preturns,"Expected Return by Profile","Annual Return (%)"),
                                  (axes[1],pvols,"Risk (Volatility) by Profile","Annual Volatility (%)")]:
        bars=ax.bar(snames,vals,color=pcolors,edgecolor='white',width=0.5)
        for bar,val,name in zip(bars,vals,pnames):
            ax.text(bar.get_x()+bar.get_width()/2,bar.get_height()+0.3,f'{val:.1f}%',ha='center',va='bottom',fontsize=10,fontweight='bold',color=PORTFOLIO_PRESETS[name]["color"])
            if name==preset_key: bar.set_edgecolor('#FFD700'); bar.set_linewidth(3)
        ax.set_ylabel(ylabel,fontsize=11); ax.set_title(title,fontsize=12,fontweight='bold'); ax.grid(axis='y',alpha=0.2)
    plt.tight_layout(); st.pyplot(fig_c); plt.close()
    st.markdown("---")

    st.subheader("Step 4 — 5-Year Growth Projection")
    c1,c2,c3 = st.columns(3)
    with c1: init_t2 = st.number_input("Initial Investment ($)",min_value=100,max_value=10_000_000,value=10_000,step=500,key="init_t2")
    with c2: mthly_t2 = st.number_input("Monthly Contribution ($)",min_value=0,max_value=100_000,value=200,step=50,key="mthly_t2")
    with c3: ret_t2 = st.slider("Adjust Annual Return (%)",1.0,30.0,float(round(portfolio_return*100,1)),0.5,key="ret_t2")/100

    det,mc = run_projection(init_t2,mthly_t2,ret_t2,portfolio_vol)
    months=60; x_years=np.arange(months+1)/12; year_ends=[12,24,36,48,60]
    p10=np.percentile(mc,10,axis=0); p25=np.percentile(mc,25,axis=0); p50=np.percentile(mc,50,axis=0); p75=np.percentile(mc,75,axis=0); p90=np.percentile(mc,90,axis=0)

    fig_p,ax_p=plt.subplots(figsize=(12,6))
    ax_p.fill_between(x_years,p10,p90,alpha=0.12,color=preset_color,label='10th–90th pct.')
    ax_p.fill_between(x_years,p25,p75,alpha=0.22,color=preset_color,label='25th–75th pct.')
    ax_p.plot(x_years,p50,color=preset_color,linewidth=2,linestyle='--',label='Median (MC)')
    ax_p.plot(x_years,det,color='#222222',linewidth=2.5,label='Expected (deterministic)')
    contrib=[init_t2+mthly_t2*m for m in range(months+1)]
    ax_p.plot(x_years,contrib,color='gray',linewidth=1.2,linestyle=':',label='Total contributed')
    for ye in year_ends:
        ax_p.annotate(f"${det[ye]:,.0f}",xy=(ye/12,det[ye]),xytext=(0,14),textcoords='offset points',ha='center',fontsize=9,fontweight='bold',color='#222222',arrowprops=dict(arrowstyle='->',color='gray',lw=0.8))
        ax_p.axvline(ye/12,color='gray',linestyle=':',linewidth=0.8,alpha=0.4)
    ax_p.set_xlabel("Years",fontsize=12); ax_p.set_ylabel("Portfolio Value ($)",fontsize=12)
    ax_p.set_title(f"5-Year Projection — {preset['icon']} {preset_key}\nInitial: ${init_t2:,.0f} | Monthly: ${mthly_t2:,.0f} | Return: {ret_t2*100:.1f}%/yr",fontsize=12,fontweight='bold')
    ax_p.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f'${x:,.0f}'))
    ax_p.legend(fontsize=9,framealpha=0.9,loc='upper left'); ax_p.grid(alpha=0.2)
    plt.tight_layout(); st.pyplot(fig_p); plt.close()

    st.markdown("#### 📋 Year-by-Year Summary")
    rows=[]
    for ye in year_ends:
        tc=init_t2+mthly_t2*ye; dv=det[ye]; gain=dv-tc; roi=(dv/tc-1)*100 if tc>0 else 0
        rows.append({"Year":ye//12,"Total Contributed":f"${tc:,.0f}","Expected Value":f"${dv:,.0f}","Total Gain":f"${gain:,.0f}","ROI":f"{roi:.1f}%","Pessimistic (10th)":f"${p10[ye]:,.0f}","Median (50th)":f"${p50[ye]:,.0f}","Optimistic (90th)":f"${p90[ye]:,.0f}"})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)

    # CSV download
    csv_buf = io.StringIO()
    stock_df[["Ticker","Company","Sector","Cluster","Beta","P/E","ROE (%)","Div Yield %","Portfolio Wt."]].to_csv(csv_buf, index=False)
    st.download_button("⬇️ Download Portfolio as CSV", data=csv_buf.getvalue(), file_name=f"portfolio_{preset_key[:12].replace(' ','_')}.csv", mime="text/csv")
    st.markdown("---")
    st.info("⚠️ **Disclaimer:** Educational tool only. Expected returns are cluster-level estimates, not historical price data. Consult a licensed financial advisor before investing.")

# ══════════════════════════════════════════════════════════════════
#  TAB 3 — CUSTOM PORTFOLIO BUILDER
# ══════════════════════════════════════════════════════════════════
with tab3:
    st.title("🛠️ Custom Portfolio Builder")
    st.markdown("Hand-pick your own stocks, set your own weights, and get a **real-time risk score and 5-year projection** for your exact portfolio.")
    st.markdown("---")

    st.subheader("Step 1 — Select Your Stocks")
    st.caption("Choose from the 44 curated stocks across all 6 clusters. You can select as many as you want.")

    selected_tickers = st.multiselect(
        "Add stocks to your portfolio:",
        options=ALL_TICKERS,
        default=["AAPL","JPM","KO","NVDA","O"],
        format_func=lambda t: f"{t} — {TICKER_TO_INFO[t]['name']} ({TICKER_TO_INFO[t]['sector']})",
        key="custom_tickers"
    )

    if not selected_tickers:
        st.info("Select at least 2 stocks above to get started.")
        st.stop()

    st.markdown("---")
    st.subheader("Step 2 — Set Your Weights")
    st.caption("Use the sliders to set how much of your portfolio goes into each stock. They must sum to 100%.")

    weight_inputs = {}
    n = len(selected_tickers)
    default_w = round(100 / n, 1)
    cols_per_row = 4
    for row_start in range(0, n, cols_per_row):
        cols = st.columns(min(cols_per_row, n - row_start))
        for ci, ticker in enumerate(selected_tickers[row_start:row_start+cols_per_row]):
            info = TICKER_TO_INFO[ticker]
            with cols[ci]:
                w = st.slider(f"**{ticker}**\n{info['name'][:18]}",0.0,100.0,default_w,0.5,key=f"wgt_{ticker}")
                weight_inputs[ticker] = w

    total_w = sum(weight_inputs.values())
    if abs(total_w - 100) > 0.5:
        st.error(f"⚠️ Weights sum to **{total_w:.1f}%**. Please adjust sliders to reach exactly **100%**.")
    else:
        st.success(f"✅ Weights sum to {total_w:.1f}% — ready to analyze.")

    st.markdown("---")
    st.subheader("Step 3 — Portfolio Risk Score & Health Check")

    # Build portfolio metrics
    port_rows = []
    for ticker, raw_w in weight_inputs.items():
        w = raw_w / total_w if total_w > 0 else 0
        info = TICKER_TO_INFO[ticker]
        cid  = info["cluster"]
        port_rows.append({
            "Ticker": ticker, "Company": info["name"], "Sector": info["sector"],
            "Cluster": f"C{cid}: {CLUSTER_SHORT[cid]}",
            "Beta": info["beta"], "P/E": info["pe"] if info["pe"]>0 else None,
            "ROE (%)": info["roe"] if -500<info["roe"]<500 else None,
            "Div Yield %": info["div"], "Weight (%)": round(w*100,1),
            "_w": w, "_cid": cid,
            "_risk": CLUSTER_RISK[cid], "_ret": CLUSTER_EXPECTED_RETURN[cid],
            "_vol": CLUSTER_VOLATILITY[cid],
        })
    port_df = pd.DataFrame(port_rows)

    # Composite metrics
    composite_risk    = (port_df["_w"] * port_df["_risk"]).sum()
    composite_return  = (port_df["_w"] * port_df["_ret"]).sum()
    composite_vol     = (port_df["_w"] * port_df["_vol"]).sum()
    composite_beta    = (port_df["_w"] * port_df["Beta"]).sum()
    composite_div     = (port_df["_w"] * port_df["Div Yield %"]).sum()
    risk_label, risk_color = get_risk_label(int(composite_risk))
    sharpe_custom = (composite_return - 0.043) / composite_vol

    # Score display
    m1,m2,m3,m4,m5,m6 = st.columns(6)
    m1.metric("🎯 Portfolio Risk Score", f"{composite_risk:.0f}/100")
    m2.metric("🏷️ Risk Level", risk_label)
    m3.metric("📈 Expected Return", f"{composite_return*100:.1f}%/yr")
    m4.metric("📉 Volatility", f"{composite_vol*100:.1f}%/yr")
    m5.metric("⚡ Sharpe Ratio", f"{sharpe_custom:.2f}")
    m6.metric("💰 Div Yield", f"{composite_div:.1f}%")

    # Risk gauge
    fig_gauge, ax_g = plt.subplots(figsize=(8, 1.8))
    ax_g.axis('off')
    # Background zones
    zones=[(0,30,"#0F6E56","Low"),(30,55,"#3B6D11","Moderate"),(55,75,"#854F0B","Elevated"),(75,100,"#A32D2D","High")]
    for zl,zh,zc,zt in zones:
        ax_g.barh(0.5,zh-zl,left=zl,height=0.35,color=zc,alpha=0.25)
        ax_g.text((zl+zh)/2,0.88,zt,ha='center',va='bottom',fontsize=9,color=zc,fontweight='bold')
    ax_g.axvline(composite_risk,color=risk_color,linewidth=4,ymin=0.1,ymax=0.9)
    ax_g.text(composite_risk,0.12,f'▲ {composite_risk:.0f}',ha='center',va='bottom',fontsize=13,fontweight='bold',color=risk_color)
    ax_g.set_xlim(0,100); ax_g.set_ylim(0,1.2)
    ax_g.set_title(f"Your Portfolio Risk Score: {composite_risk:.0f} / 100  —  {risk_label}",fontsize=13,fontweight='bold',color=risk_color)
    plt.tight_layout(); st.pyplot(fig_gauge); plt.close()

    # Health checks
    st.markdown("#### 🩺 Portfolio Health Check")
    issues = []
    # Cluster concentration
    cluster_conc = port_df.groupby("_cid")["_w"].sum()
    for cid, w in cluster_conc.items():
        if w > 0.50:
            issues.append(f"⚠️ **Cluster Concentration:** {w*100:.0f}% in *{CLUSTER_SHORT[cid]}* — exceeds 50% threshold.")
    # Sector concentration
    sector_conc = port_df.groupby("Sector")["_w"].sum()
    for sec, w in sector_conc.items():
        if w > 0.40:
            issues.append(f"⚠️ **Sector Concentration:** {w*100:.0f}% in *{sec}* — above 40% recommended cap.")
    # High volatility exposure
    vol_exp = port_df[port_df["_cid"]==2]["_w"].sum()
    if vol_exp > 0.30:
        issues.append(f"🎢 **High Volatility Exposure:** {vol_exp*100:.0f}% in High Volatility cluster — significant drawdown risk.")
    # Leverage exposure
    lev_exp = port_df[port_df["_cid"]==3]["_w"].sum()
    if lev_exp > 0.10:
        issues.append(f"💣 **Leverage Risk:** {lev_exp*100:.0f}% in Extreme Leverage cluster — these 2 companies carry very high debt.")
    if not issues:
        st.success("✅ No major concentration issues detected. Your portfolio looks well-distributed.")
    else:
        for issue in issues:
            st.warning(issue)

    # Portfolio breakdown chart
    col_left, col_right = st.columns(2)
    with col_left:
        # Cluster donut
        ccluster = port_df.groupby("_cid")["_w"].sum().reset_index()
        fig_d, ax_d = plt.subplots(figsize=(5,5))
        ax_d.pie(ccluster["_w"], labels=[f"C{int(r['_cid'])}: {CLUSTER_SHORT[int(r['_cid'])]}" for _,r in ccluster.iterrows()],
                 colors=[PALETTE[int(r['_cid'])%len(PALETTE)] for _,r in ccluster.iterrows()],
                 autopct='%1.0f%%', startangle=140, pctdistance=0.75, wedgeprops=dict(edgecolor='white',linewidth=2))
        ax_d.set_title("Cluster Allocation",fontsize=12,fontweight='bold')
        plt.tight_layout(); st.pyplot(fig_d); plt.close()

    with col_right:
        # Sector donut
        csector = port_df.groupby("Sector")["_w"].sum().reset_index()
        sec_colors = plt.cm.Set3(np.linspace(0, 1, len(csector)))
        fig_s, ax_s = plt.subplots(figsize=(5,5))
        ax_s.pie(csector["_w"], labels=csector["Sector"], colors=sec_colors,
                 autopct='%1.0f%%', startangle=140, pctdistance=0.75, wedgeprops=dict(edgecolor='white',linewidth=2))
        ax_s.set_title("Sector Allocation",fontsize=12,fontweight='bold')
        plt.tight_layout(); st.pyplot(fig_s); plt.close()

    # Full stock table
    st.markdown("#### Your Custom Portfolio")
    disp_df = port_df[["Ticker","Company","Sector","Cluster","Beta","P/E","ROE (%)","Div Yield %","Weight (%)"]].copy()
    disp_df["P/E"] = disp_df["P/E"].apply(lambda x: f"{x:.1f}" if x else "N/A")
    disp_df["ROE (%)"] = disp_df["ROE (%)"].apply(lambda x: f"{x:.1f}" if x else "N/A")
    st.dataframe(disp_df, use_container_width=True, hide_index=True)

    # "Explain This Stock" expander per ticker
    st.markdown("#### 💡 Explain This Stock")
    explain_ticker = st.selectbox("Select a stock to get a plain-English explanation:", selected_tickers, key="explain_pick")
    if explain_ticker:
        ei = TICKER_TO_INFO[explain_ticker]; ecid = ei["cluster"]
        erisk = CLUSTER_RISK[ecid]; elbl, ecol = get_risk_label(erisk)
        epe = f"{ei['pe']:.1f}x" if ei['pe']>0 else "not applicable (no profit yet)"
        eroe = f"{ei['roe']:.1f}%" if ei['roe']>-500 else "negative (losing money)"
        with st.expander(f"📋 {explain_ticker} — {ei['name']}", expanded=True):
            st.markdown(f"""
**What kind of company is it?**
{ei['name']} belongs to the **{CLUSTER_SHORT[ecid]}** cluster — these are {CLUSTER_PLAIN_ENGLISH[ecid]['desc'].lower()}

**Risk Level:** {elbl} ({erisk}/100)
This means {explain_ticker} carries {'relatively low' if erisk<40 else 'moderate' if erisk<60 else 'significant'} risk compared to the overall market.

**Key Numbers in Plain English:**
- **Beta of {ei['beta']}:** {'Moves roughly in line with the market.' if 0.8<ei['beta']<1.2 else 'More volatile than the market — bigger swings up AND down.' if ei['beta']>=1.2 else 'Less volatile than the market — more stable.'}
- **P/E Ratio of {epe}:** {'Investors are paying a premium for expected growth.' if ei['pe']>30 else 'Reasonably priced relative to earnings.' if 10<(ei['pe'] or 0)<30 else 'Cheap valuation — or the market has concerns.' if ei['pe']>0 else 'No earnings yet — pre-profit company.'}
- **ROE of {eroe}:** {'Very profitable — the company generates strong returns on shareholder money.' if (ei['roe'] or 0)>25 else 'Decent profitability.' if (ei['roe'] or 0)>10 else 'Weak or negative profitability — watch closely.'}
- **Dividend Yield of {ei['div']}%:** {'Solid income stream — pays regular dividends.' if ei['div']>3 else 'Small dividend — more of a growth stock.' if 0<ei['div']<=3 else 'No dividend — all returns come from price appreciation.'}

**Bottom line:** {CLUSTER_PLAIN_ENGLISH[ecid]['analogy']}
""")

    st.markdown("---")
    st.subheader("Step 4 — 5-Year Projection for Your Custom Portfolio")
    cc1,cc2 = st.columns(2)
    with cc1: init_c3 = st.number_input("Initial Investment ($)",min_value=100,max_value=10_000_000,value=10_000,step=500,key="init_c3")
    with cc2: mthly_c3 = st.number_input("Monthly Contribution ($)",min_value=0,max_value=100_000,value=200,step=50,key="mthly_c3")

    det_c, mc_c = run_projection(init_c3, mthly_c3, composite_return, composite_vol)
    x_yrs = np.arange(61)/12; ye_list=[12,24,36,48,60]
    p10c=np.percentile(mc_c,10,axis=0); p25c=np.percentile(mc_c,25,axis=0)
    p50c=np.percentile(mc_c,50,axis=0); p75c=np.percentile(mc_c,75,axis=0); p90c=np.percentile(mc_c,90,axis=0)

    fig_cp,ax_cp=plt.subplots(figsize=(12,6))
    ax_cp.fill_between(x_yrs,p10c,p90c,alpha=0.12,color=risk_color,label='10th–90th pct.')
    ax_cp.fill_between(x_yrs,p25c,p75c,alpha=0.22,color=risk_color,label='25th–75th pct.')
    ax_cp.plot(x_yrs,p50c,color=risk_color,linewidth=2,linestyle='--',label='Median (MC)')
    ax_cp.plot(x_yrs,det_c,color='#222222',linewidth=2.5,label='Expected')
    ax_cp.plot(x_yrs,[init_c3+mthly_c3*m for m in range(61)],color='gray',linewidth=1.2,linestyle=':',label='Contributed')
    for ye in ye_list:
        ax_cp.annotate(f"${det_c[ye]:,.0f}",xy=(ye/12,det_c[ye]),xytext=(0,14),textcoords='offset points',ha='center',fontsize=9,fontweight='bold',arrowprops=dict(arrowstyle='->',color='gray',lw=0.8))
    ax_cp.set_xlabel("Years",fontsize=12); ax_cp.set_ylabel("Portfolio Value ($)",fontsize=12)
    ax_cp.set_title(f"5-Year Projection — Custom Portfolio\nRisk Score: {composite_risk:.0f} ({risk_label}) | Return: {composite_return*100:.1f}%/yr | Initial: ${init_c3:,.0f}",fontsize=12,fontweight='bold')
    ax_cp.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f'${x:,.0f}'))
    ax_cp.legend(fontsize=9,loc='upper left'); ax_cp.grid(alpha=0.2)
    plt.tight_layout(); st.pyplot(fig_cp); plt.close()

    # Download custom portfolio
    csv_c = io.StringIO()
    disp_df.to_csv(csv_c, index=False)
    st.download_button("⬇️ Download Custom Portfolio CSV", data=csv_c.getvalue(), file_name="custom_portfolio.csv", mime="text/csv")
    st.markdown("---")
    st.info("⚠️ **Disclaimer:** Educational tool only. Risk scores are cluster-level estimates. Not financial advice.")

# ══════════════════════════════════════════════════════════════════
#  TAB 4 — ANALYZE MY PORTFOLIO
# ══════════════════════════════════════════════════════════════════
with tab4:
    st.title("🔍 Analyze My Portfolio")
    st.markdown("**Paste in what you already own.** We'll map each ticker to its financial cluster, calculate your hidden risk score, and show you exactly where your concentrations are — and what a rebalanced version would look like.")
    st.markdown("---")

    st.subheader("Enter Your Current Holdings")
    st.caption("Enter one ticker and its portfolio percentage per line, e.g.  `AAPL 30`")

    default_holdings = "AAPL 25\nTSLA 20\nJPM 15\nNVDA 20\nKO 10\nAMT 10"
    holdings_input = st.text_area("Your holdings (ticker  weight%):", value=default_holdings, height=180, key="holdings_input")

    parsed = []
    errors = []
    for line in holdings_input.strip().split("\n"):
        parts = line.strip().split()
        if len(parts) == 2:
            ticker, weight = parts[0].upper(), parts[1]
            try:
                w = float(weight)
                if ticker in TICKER_TO_INFO:
                    parsed.append((ticker, w))
                else:
                    errors.append(f"'{ticker}' not found in our database (not in curated 44-stock universe)")
            except:
                errors.append(f"Could not parse weight for '{ticker}'")
        elif line.strip():
            errors.append(f"Could not parse line: '{line}'")

    if errors:
        for e in errors: st.warning(f"⚠️ {e}")

    if not parsed:
        st.info("Enter your holdings above to get started. Use the format: TICKER WEIGHT (e.g. AAPL 30)")
    else:
        total_entered = sum(w for _,w in parsed)
        norm_holdings = [(t, w/total_entered) for t,w in parsed]

        st.markdown("---")
        st.subheader("Your Portfolio Analysis")

        # Build analysis rows
        an_rows = []
        for ticker, w in norm_holdings:
            info = TICKER_TO_INFO[ticker]; cid = info["cluster"]
            an_rows.append({"Ticker":ticker,"Company":info["name"],"Sector":info["sector"],
                "Cluster":f"C{cid}: {CLUSTER_SHORT[cid]}","Weight (%)":round(w*100,1),
                "_w":w,"_cid":cid,"_risk":CLUSTER_RISK[cid],"_ret":CLUSTER_EXPECTED_RETURN[cid],"_vol":CLUSTER_VOLATILITY[cid],
                "Beta":info["beta"],"Div Yield %":info["div"]})
        an_df = pd.DataFrame(an_rows)

        your_risk   = (an_df["_w"]*an_df["_risk"]).sum()
        your_return = (an_df["_w"]*an_df["_ret"]).sum()
        your_vol    = (an_df["_w"]*an_df["_vol"]).sum()
        your_beta   = (an_df["_w"]*an_df["Beta"]).sum()
        your_lbl, your_col = get_risk_label(int(your_risk))

        # Before vs After banner
        st.markdown("### 🔴 What You Think vs. What You Actually Have")
        sector_breakdown = an_df.groupby("Sector")["_w"].sum().reset_index()
        cluster_breakdown= an_df.groupby("_cid")["_w"].sum().reset_index()

        b1,b2,b3,b4 = st.columns(4)
        b1.metric("Your Risk Score",f"{your_risk:.0f}/100",delta=None)
        b2.metric("Risk Level",your_lbl)
        b3.metric("Expected Annual Return",f"{your_return*100:.1f}%")
        b4.metric("Weighted Beta",f"{your_beta:.2f}")

        # Visual risk gauge
        fig_ag,ax_ag=plt.subplots(figsize=(9,1.8)); ax_ag.axis('off')
        zones=[(0,30,"#0F6E56","Low"),(30,55,"#3B6D11","Moderate"),(55,75,"#854F0B","Elevated"),(75,100,"#A32D2D","High")]
        for zl,zh,zc,zt in zones:
            ax_ag.barh(0.5,zh-zl,left=zl,height=0.35,color=zc,alpha=0.25)
            ax_ag.text((zl+zh)/2,0.88,zt,ha='center',va='bottom',fontsize=9,color=zc,fontweight='bold')
        ax_ag.axvline(your_risk,color=your_col,linewidth=5,ymin=0.08,ymax=0.92)
        ax_ag.text(your_risk,0.1,f'▲ {your_risk:.0f}',ha='center',va='bottom',fontsize=13,fontweight='bold',color=your_col)
        ax_ag.set_xlim(0,100); ax_ag.set_ylim(0,1.2)
        ax_ag.set_title(f"Your Portfolio Risk Score: {your_risk:.0f}/100 — {your_lbl}",fontsize=13,fontweight='bold',color=your_col)
        plt.tight_layout(); st.pyplot(fig_ag); plt.close()

        # Cluster vs Sector breakdown
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("#### Cluster Breakdown")
            fig_cb,ax_cb=plt.subplots(figsize=(5,5))
            ax_cb.pie(cluster_breakdown["_w"],
                      labels=[f"C{int(r['_cid'])}: {CLUSTER_SHORT[int(r['_cid'])]}" for _,r in cluster_breakdown.iterrows()],
                      colors=[PALETTE[int(r['_cid'])%len(PALETTE)] for _,r in cluster_breakdown.iterrows()],
                      autopct='%1.0f%%',startangle=140,pctdistance=0.75,wedgeprops=dict(edgecolor='white',linewidth=2))
            ax_cb.set_title("Your Cluster Exposure",fontsize=12,fontweight='bold')
            plt.tight_layout(); st.pyplot(fig_cb); plt.close()
        with col_b:
            st.markdown("#### Sector Breakdown")
            fig_sb,ax_sb=plt.subplots(figsize=(5,5))
            sb_colors=plt.cm.Set3(np.linspace(0,1,len(sector_breakdown)))
            ax_sb.pie(sector_breakdown["_w"],labels=sector_breakdown["Sector"],colors=sb_colors,
                      autopct='%1.0f%%',startangle=140,pctdistance=0.75,wedgeprops=dict(edgecolor='white',linewidth=2))
            ax_sb.set_title("Your Sector Exposure",fontsize=12,fontweight='bold')
            plt.tight_layout(); st.pyplot(fig_sb); plt.close()

        # Concentration flags
        st.markdown("#### 🩺 Hidden Risk Flags")
        flags = []
        for cid_val, w in cluster_breakdown.values:
            cid_int = int(cid_val)
            if w > 0.45: flags.append(f"⚠️ **{w*100:.0f}%** of your portfolio is in the *{CLUSTER_SHORT[cid_int]}* cluster. This is significant concentration.")
            if cid_int==2 and w>0.2: flags.append(f"🎢 **{w*100:.0f}%** in High Volatility stocks — this cluster can swing ±40% in a single year.")
            if cid_int==3 and w>0.05: flags.append(f"💣 **{w*100:.0f}%** in Extreme Leverage — these are the 2 most debt-laden companies in the S&P 500.")
        for sec, w in zip(sector_breakdown["Sector"], sector_breakdown["_w"]):
            if w > 0.40: flags.append(f"🏭 **Sector risk:** {w*100:.0f}% in {sec} — above the 40% cap for single-sector exposure.")
        if not flags:
            st.success("✅ No major concentration issues detected in your portfolio.")
        else:
            for flag in flags: st.warning(flag)

        st.markdown("---")
        st.subheader("📊 Your Portfolio vs. The Four Presets")
        st.markdown("See how your portfolio's risk and return compare to the recommended portfolio profiles.")

        compare_data = {
            "Portfolio":    [your_risk, your_return*100, your_vol*100],
            "Conservative": [32, PORTFOLIO_PRESETS["Conservative — Capital Preservation"]["target_return"]*100, PORTFOLIO_PRESETS["Conservative — Capital Preservation"]["volatility"]*100],
            "Balanced":     [45, PORTFOLIO_PRESETS["Balanced — Growth & Income"]["target_return"]*100, PORTFOLIO_PRESETS["Balanced — Growth & Income"]["volatility"]*100],
            "Growth":       [62, PORTFOLIO_PRESETS["Growth — Aggressive Appreciation"]["target_return"]*100, PORTFOLIO_PRESETS["Growth — Aggressive Appreciation"]["volatility"]*100],
            "Speculative":  [80, PORTFOLIO_PRESETS["Speculative — High Risk / High Reward"]["target_return"]*100, PORTFOLIO_PRESETS["Speculative — High Risk / High Reward"]["volatility"]*100],
        }
        comp_df = pd.DataFrame(compare_data, index=["Risk Score","Expected Return (%)","Volatility (%)"]).T.reset_index()
        comp_df.columns = ["Portfolio","Risk Score","Expected Return (%)","Volatility (%)"]

        fig_cmp, axes_cmp = plt.subplots(1,3,figsize=(14,4))
        metrics_cmp = ["Risk Score","Expected Return (%)","Volatility (%)"]
        bar_colors_cmp = [your_col,"#0F6E56","#3B6D11","#854F0B","#A32D2D"]
        for ax, metric in zip(axes_cmp, metrics_cmp):
            bars = ax.bar(comp_df["Portfolio"], comp_df[metric], color=bar_colors_cmp, edgecolor='white', width=0.6)
            bars[0].set_edgecolor('#FFD700'); bars[0].set_linewidth(3)
            for bar, val in zip(bars, comp_df[metric]):
                ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5, f'{val:.1f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
            ax.set_title(metric, fontsize=12, fontweight='bold'); ax.grid(axis='y', alpha=0.2)
            plt.setp(ax.get_xticklabels(), rotation=20, ha='right', fontsize=9)
        plt.tight_layout(); st.pyplot(fig_cmp); plt.close()

        # Rebalancing suggestion
        st.markdown("---")
        st.subheader("🔄 Suggested Rebalance")
        # Find closest preset
        closest = min(PORTFOLIO_PRESETS.keys(), key=lambda p: abs(PORTFOLIO_PRESETS[p]["target_return"] - your_return))
        closest_risk = {"Conservative — Capital Preservation":32,"Balanced — Growth & Income":45,"Growth — Aggressive Appreciation":62,"Speculative — High Risk / High Reward":80}[closest]
        pp = PORTFOLIO_PRESETS[closest]
        st.markdown(f"""
Based on your portfolio's expected return of **{your_return*100:.1f}%/yr** and risk score of **{your_risk:.0f}**, 
the closest matching profile is the **{pp['icon']} {closest}** (Risk Score: ~{closest_risk}).

**Suggested rebalance to reduce concentration:**
""")
        reb_rows = []
        for cid, target_w in pp["cluster_weights"].items():
            current_w = cluster_breakdown[cluster_breakdown["_cid"]==cid]["_w"].values
            current_w = current_w[0] if len(current_w)>0 else 0
            delta = target_w - current_w
            reb_rows.append({"Cluster":f"C{cid}: {CLUSTER_SHORT[cid]}","Current (%)":f"{current_w*100:.0f}%","Target (%)":f"{target_w*100:.0f}%","Adjustment":("➕ Add" if delta>0.03 else "➖ Reduce" if delta<-0.03 else "✅ OK") + f" {abs(delta*100):.0f}%"})
        st.dataframe(pd.DataFrame(reb_rows), use_container_width=True, hide_index=True)

        # 5-Year projection
        st.markdown("---")
        st.subheader("📈 5-Year Projection for Your Portfolio")
        ai1,ai2 = st.columns(2)
        with ai1: init_a4 = st.number_input("Initial Investment ($)",min_value=100,max_value=10_000_000,value=10_000,step=500,key="init_a4")
        with ai2: mthly_a4 = st.number_input("Monthly Contribution ($)",min_value=0,max_value=100_000,value=200,step=50,key="mthly_a4")
        det_a,mc_a = run_projection(init_a4,mthly_a4,your_return,your_vol)
        x_ya=np.arange(61)/12
        p10a=np.percentile(mc_a,10,axis=0); p25a=np.percentile(mc_a,25,axis=0)
        p50a=np.percentile(mc_a,50,axis=0); p75a=np.percentile(mc_a,75,axis=0); p90a=np.percentile(mc_a,90,axis=0)
        fig_pa,ax_pa=plt.subplots(figsize=(12,6))
        ax_pa.fill_between(x_ya,p10a,p90a,alpha=0.12,color=your_col,label='10th–90th pct.')
        ax_pa.fill_between(x_ya,p25a,p75a,alpha=0.22,color=your_col,label='25th–75th pct.')
        ax_pa.plot(x_ya,p50a,color=your_col,linewidth=2,linestyle='--',label='Median (MC)')
        ax_pa.plot(x_ya,det_a,color='#222222',linewidth=2.5,label='Expected')
        ax_pa.plot(x_ya,[init_a4+mthly_a4*m for m in range(61)],color='gray',linewidth=1.2,linestyle=':',label='Contributed')
        for ye in [12,24,36,48,60]:
            ax_pa.annotate(f"${det_a[ye]:,.0f}",xy=(ye/12,det_a[ye]),xytext=(0,14),textcoords='offset points',ha='center',fontsize=9,fontweight='bold',arrowprops=dict(arrowstyle='->',color='gray',lw=0.8))
        ax_pa.set_xlabel("Years",fontsize=12); ax_pa.set_ylabel("Portfolio Value ($)",fontsize=12)
        ax_pa.set_title(f"Your Portfolio — 5-Year Projection\nRisk: {your_risk:.0f} ({your_lbl}) | Return: {your_return*100:.1f}%/yr | Initial: ${init_a4:,.0f}",fontsize=12,fontweight='bold')
        ax_pa.yaxis.set_major_formatter(plt.FuncFormatter(lambda x,_: f'${x:,.0f}'))
        ax_pa.legend(fontsize=9,loc='upper left'); ax_pa.grid(alpha=0.2)
        plt.tight_layout(); st.pyplot(fig_pa); plt.close()
        st.markdown("---")
        st.info("⚠️ **Disclaimer:** Educational tool only. Not financial advice.")

# ══════════════════════════════════════════════════════════════════
#  TAB 5 — PLAIN ENGLISH GUIDE
# ══════════════════════════════════════════════════════════════════
with tab5:
    st.title("📖 Plain English Guide")
    st.markdown("**Not a data scientist? Perfect.** This tab explains everything in the app in plain, simple language — no jargon, no formulas.")
    st.markdown("---")

    # What is this app
    st.header("🤔 What Is This App?")
    st.markdown("""
Most investors pick stocks by sector — Tech, Healthcare, Energy, and so on. But two companies in the same sector 
can be completely different financially. One might be incredibly profitable and low-risk. Another in the same 
sector might be drowning in debt and swinging wildly every week.

**This app uses math to find the "financial personality types" of S&P 500 companies** — groupings based on 
how they actually behave, not what industry they're in. We found 6 personality types. Once you know which 
type your stocks belong to, you can make smarter, less risky investment decisions.

> Think of it like dating apps. Two people might both list "music" as a hobby, but one loves jazz and the other 
> loves death metal. The label is the same — the reality is totally different. This app finds the death metal fans.
""")
    st.markdown("---")

    # What is a cluster
    st.header("🧩 What Is a 'Cluster'? (The 6 Financial Personality Types)")
    st.markdown("We used a computer algorithm to group the 496 S&P 500 companies into 6 groups based on 5 numbers: how volatile they are, how expensive they are, how profitable they are, how much debt they have, and how big they are. Here's what each group means in plain English:")

    for cid in sorted(CLUSTER_PLAIN_ENGLISH.keys()):
        info = CLUSTER_PLAIN_ENGLISH[cid]
        risk_score = CLUSTER_RISK[cid]
        rlbl, rcol = get_risk_label(risk_score)
        with st.expander(f"{info['emoji']}  **Cluster {cid}: {info['name']}**  —  Risk: {rlbl} ({risk_score}/100)", expanded=(cid==5)):
            col_txt, col_stocks = st.columns([2,1])
            with col_txt:
                st.markdown(f"**What are these companies?**\n{info['desc']}\n\n**Think of it like this:**\n*{info['analogy']}*")
                st.markdown(f"**Expected annual return:** ~{CLUSTER_EXPECTED_RETURN[cid]*100:.0f}%  |  **Typical dividend:** ~{CLUSTER_DIVIDEND[cid]:.1f}%  |  **Risk score:** {risk_score}/100")
            with col_stocks:
                st.markdown("**Example stocks:**")
                for s in CLUSTER_STOCKS[cid][:4]:
                    st.markdown(f"- **{s['ticker']}** — {s['name']}")

    st.markdown("---")

    # Risk scores explained
    st.header("🎯 What Do the Risk Scores Mean?")
    st.markdown("Every cluster gets a risk score from 0 to 100. Here's the scale — and what it means for a real investor:")

    risk_zones = [
        ("🟢 0–29: Low Risk",      "#0F6E56", "Your money is relatively safe. Expect slow, steady growth. Best for: retirees, people who can't afford to lose money, conservative savers.","Example: Coca-Cola, Johnson & Johnson, Walmart"),
        ("🟡 30–54: Moderate Risk", "#3B6D11", "Balanced mix of safety and growth. You might see some dips, but the long-term trend is upward. Best for: most investors with a 5–10 year horizon.","Example: Apple, Microsoft, JPMorgan"),
        ("🟠 55–74: Elevated Risk", "#854F0B", "More volatility. Your portfolio might drop 15–25% in a bad year, but could also spike significantly. Best for: investors with 10+ year horizons who don't panic-sell.","Example: American Tower, Equinix (REITs)"),
        ("🔴 75–100: High Risk",    "#A32D2D", "Buckle up. These stocks can double or lose half their value in a year. Best for: young investors, small allocations, people who can stomach big swings.","Example: NVIDIA, Tesla, Coinbase"),
    ]
    for zone, color, desc, example in risk_zones:
        st.markdown(f"""<div style="border-left:5px solid {color};padding:12px 16px;margin:8px 0;background:#f9f9f9;border-radius:4px;">
        <strong style="color:{color};font-size:15px;">{zone}</strong><br>
        <span style="color:#333;">{desc}</span><br>
        <span style="color:#666;font-size:13px;font-style:italic;">{example}</span></div>""", unsafe_allow_html=True)

    st.markdown("---")

    # How to use each tab
    st.header("🗺️ How to Use This App — Step by Step")
    steps = [
        ("📊 Tab 1: Clustering Analysis", "This is the research tab. It shows the science behind the app — how the 6 clusters were found, what makes each cluster unique, and proof that these clusters don't just follow industry labels. **Best for:** understanding how the app works and what the data says."),
        ("💼 Tab 2: Portfolio Builder", "Pick your risk level (Low / Medium / High / Very High) and instantly get a recommended portfolio of real stocks with expected returns, a risk score, and a 5-year growth chart. **Best for:** investors who want a quick, guided recommendation."),
        ("🛠️ Tab 3: Custom Portfolio Builder", "Hand-pick exactly which stocks you want, set how much goes into each one, and instantly see your portfolio's risk score, cluster breakdown, health check, and projection. **Best for:** investors who already have stocks in mind and want to stress-test their choices."),
        ("🔍 Tab 4: Analyze My Portfolio", "Type in what you already own (ticker + %) and the app will tell you your hidden risk score, where your concentrations are, how you compare to each preset, and what a rebalanced version would look like. **Best for:** existing investors who want to audit their current holdings."),
        ("📖 Tab 5: Plain English Guide", "You're here! **Best for:** anyone who wants to understand what they're looking at before making decisions."),
    ]
    for title, desc in steps:
        with st.expander(title, expanded=False):
            st.markdown(desc)

    st.markdown("---")

    # Decision guide
    st.header("🧭 Which Portfolio Is Right for Me?")
    st.markdown("Answer these three questions to find your starting point:")

    q1 = st.radio("1. When do you need this money?", ["Within 3 years","In 3–7 years","In 7–15 years","15+ years away"], key="q1_guide")
    q2 = st.radio("2. If your portfolio dropped 25% tomorrow, you would:", ["Sell everything immediately","Lose sleep but hold on","Stay calm — markets recover","See it as a buying opportunity"], key="q2_guide")
    q3 = st.radio("3. What's most important to you?", ["Keeping what I have (capital preservation)","Steady growth with some safety","Strong growth, accept some risk","Maximum growth at any cost"], key="q3_guide")

    score_q1 = {"Within 3 years":0,"In 3–7 years":1,"In 7–15 years":2,"15+ years away":3}[q1]
    score_q2 = {"Sell everything immediately":0,"Lose sleep but hold on":1,"Stay calm — markets recover":2,"See it as a buying opportunity":3}[q2]
    score_q3 = {"Keeping what I have (capital preservation)":0,"Steady growth with some safety":1,"Strong growth, accept some risk":2,"Maximum growth at any cost":3}[q3]
    total_score = score_q1 + score_q2 + score_q3

    if total_score <= 2:
        rec = "Conservative — Capital Preservation"; rec_icon="🛡️"; rec_color="#0F6E56"
        rec_desc = "You prioritise safety above all else. Stick to Core Market and High Profitability stocks. Accept lower returns in exchange for sleeping well at night."
    elif total_score <= 4:
        rec = "Balanced — Growth & Income"; rec_icon="⚖️"; rec_color="#3B6D11"
        rec_desc = "You want your money to grow but can't stomach huge swings. A mix of stable blue chips and quality growth companies is your sweet spot."
    elif total_score <= 6:
        rec = "Growth — Aggressive Appreciation"; rec_icon="📈"; rec_color="#854F0B"
        rec_desc = "You're comfortable with volatility and have time on your side. Leaning into High Profitability and some High Volatility names makes sense for you."
    else:
        rec = "Speculative — High Risk / High Reward"; rec_icon="🚀"; rec_color="#A32D2D"
        rec_desc = "You have a long time horizon and can handle big swings. High Volatility and momentum names could generate outsized returns — but also big losses. Only invest money you won't need for 10+ years."

    st.markdown(f"""<div style="background:#f0f9f0;border:2px solid {rec_color};padding:20px;border-radius:8px;margin:16px 0;">
    <h3 style="color:{rec_color};margin:0 0 8px 0;">{rec_icon} Recommended Profile: {rec}</h3>
    <p style="margin:0;color:#333;">{rec_desc}</p>
    <p style="margin:8px 0 0 0;color:#666;font-size:13px;">👉 Head to the <strong>Portfolio Builder tab</strong> and select "<strong>{rec.split('—')[0].strip()}</strong>" to see your recommended stocks and projections.</p>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Glossary
    st.header("📚 Glossary — Key Terms Explained Simply")
    glossary = [
        ("Beta", "How much a stock moves compared to the overall market. A beta of 1.0 means it moves exactly with the market. A beta of 2.0 means it moves twice as much — in both directions."),
        ("P/E Ratio (Price-to-Earnings)", "How much investors are paying for every $1 of profit a company makes. A P/E of 20 means you're paying $20 for every $1 of annual earnings. High P/E = expensive but expected to grow fast. Low P/E = cheap or slow-growing."),
        ("ROE (Return on Equity)", "How efficiently a company uses investor money to generate profit. A 30% ROE means the company earns 30 cents for every $1 shareholders have invested. Higher is better."),
        ("Debt/Equity Ratio", "How much debt a company has compared to what shareholders own. A ratio of 1.0 means equal debt and equity. Very high ratios (like 139x) mean the company is extremely leveraged — risky if something goes wrong."),
        ("Market Cap", "The total value of a company's shares. Large-cap ($10B+) = stable, well-established. Small-cap (under $2B) = riskier but more growth potential."),
        ("Silhouette Score", "A technical measure of how well-separated the clusters are. Ranges from -1 to 1. Our score of 0.29 means the clusters are meaningfully distinct — not perfect, but real. (Financial data is messy — 0.29 is actually good.)"),
        ("Monte Carlo Simulation", "A way of projecting the future by running thousands of random scenarios and showing you the range of possible outcomes. The shaded bands on the projection chart show the spread of those outcomes."),
        ("Sharpe Ratio", "A measure of return-per-unit-of-risk. A Sharpe ratio above 1.0 is considered good — you're getting meaningful return for the risk you're taking. Below 0.5 means the risk might not be worth it."),
        ("Dividend Yield", "The annual dividend payment as a percentage of the stock price. A 4% dividend yield means a $100 stock pays you $4/year just for owning it — before any price appreciation."),
        ("Cluster / K-Means", "K-Means is the algorithm we used to group companies. It found 6 natural groupings (clusters) by looking for companies with similar financial characteristics. Think of it as sorting M&Ms by color — except the 'colors' are financial metrics."),
    ]
    for term, definition in glossary:
        with st.expander(f"**{term}**"):
            st.markdown(definition)

    st.markdown("---")
    st.info("⚠️ **Disclaimer:** This app is for educational purposes only. Nothing here is financial advice. Always consult a licensed financial advisor before making investment decisions. Past performance and cluster characteristics do not guarantee future results.")
    st.caption("S&P 500 Clustering Platform | K-Means (k=6) | Built with Streamlit")
