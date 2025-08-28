
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import re

st.set_page_config(page_title="MSH Interactive Dashboard", layout="wide", page_icon="📊")

DATA_PATH = Path("data/Cohort2_startups.xlsx")
SHEET = "Cohort 2 Startups"

@st.cache_data
def load_data():
    df = pd.read_excel(DATA_PATH, sheet_name=SHEET)
    df.columns = [c.strip() for c in df.columns]
    # Column mapping
    col_startup = "Name of Startup"
    col_accel = "Name of Accelerator"
    col_sector = "Sector"
    col_tech = "Technology used (AI, IoT, DeepTech, Blockchain etc.)"
    col_trl = "Technology Readiness Level （TRL）"
    col_state = "State"
    col_stage = "Stage of startup (Ideation, PMF, Product launched, Scale up)"
    keep = [col_startup, col_accel, col_sector, col_tech, col_trl, col_state, col_stage]
    data = df[keep].copy()
    data.rename(columns={
        col_startup: "startup",
        col_accel: "accelerator",
        col_sector: "sector",
        col_tech: "technology",
        col_trl: "trl",
        col_state: "state",
        col_stage: "stage",
    }, inplace=True)

    # Parse TRL as int (1..9)
    data["trl_num"] = (
        data["trl"]
        .astype(str)
        .str.extract(r"(\d+)")[0]
        .astype("float")
    )
    data["trl_num"] = data["trl_num"].astype("Int64")

    # TRL buckets
    def bucket(n):
        if pd.isna(n): return "Unknown"
        n = int(n)
        if 1 <= n <= 3: return "Early (1–3)"
        if 4 <= n <= 6: return "Mid (4–6)"
        if 7 <= n <= 9: return "Late (7–9)"
        return "Unknown"
    data["trl_bucket"] = data["trl_num"].map(bucket)

    # Normalize stage
    def norm_stage(s: str):
        s = str(s).strip().lower()
        if "ideation" in s: return "Ideation"
        if "pmf" in s: return "PMF"
        if "product" in s or "launched" in s or "launch" in s: return "Product/Launched"
        if "scale" in s: return "Scale-up"
        return "Unknown"
    data["stage_norm"] = data["stage"].apply(norm_stage)

    # Clean text
    for c in ["startup","accelerator","sector","technology","state"]:
        data[c] = data[c].astype(str).str.strip()

    return data

data = load_data()

# Sidebar filters
st.sidebar.header("Filters")
accel_sel = st.sidebar.multiselect("Accelerator", sorted([a for a in data["accelerator"].dropna().unique() if a]), placeholder="All")
state_sel = st.sidebar.multiselect("State", sorted([s for s in data["state"].dropna().unique() if s]), placeholder="All")
sector_sel = st.sidebar.multiselect("Sector", sorted([s for s in data["sector"].dropna().unique() if s])[:100], placeholder="All (top 100 shown)")
trl_bucket_sel = st.sidebar.multiselect("TRL Bucket", ["Early (1–3)","Mid (4–6)","Late (7–9)"], placeholder="All")

# Apply filters
f = data.copy()
if accel_sel:
    f = f[f["accelerator"].isin(accel_sel)]
if state_sel:
    f = f[f["state"].isin(state_sel)]
if sector_sel:
    f = f[f["sector"].isin(sector_sel)]
if trl_bucket_sel:
    f = f[f["trl_bucket"].isin(trl_bucket_sel)]

# KPIs
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Startups", f["startup"].nunique())
c2.metric("Total Accelerators", f["accelerator"].nunique())
c3.metric("States Covered", f["state"].nunique())
# Most common TRL
common_trl = int(f["trl_num"].dropna().mode().iloc[0]) if not f["trl_num"].dropna().empty else "-"
c4.metric("Most Common TRL", common_trl)

st.markdown("---")

# Accelerator drill-down
st.subheader("Accelerator → Startups")
accel_counts = f.groupby("accelerator")["startup"].nunique().sort_values(ascending=False).head(20).reset_index()
fig_acc = px.bar(accel_counts, y="accelerator", x="startup", orientation="h",
                 labels={"accelerator": "Accelerator", "startup": "# Startups"},
                 color="startup", color_continuous_scale="Tealgrn")
fig_acc.update_layout(height=450, coloraxis_showscale=False, template="plotly_dark", margin=dict(l=10,r=10,t=40,b=10))
st.plotly_chart(fig_acc, use_container_width=True)

# Optional: show startup list for a selected accelerator
sel_accel = st.selectbox("Show startup list for accelerator", ["(select one)"] + accel_counts["accelerator"].tolist())
if sel_accel != "(select one)":
    st.dataframe(f[f["accelerator"] == sel_accel][["startup","sector","stage_norm","trl_num","state"]].sort_values("startup"),
                 use_container_width=True, height=300)

st.markdown("---")

# Three-column analytic view
colA, colB, colC = st.columns(3)

with colA:
    st.subheader("Top Sectors")
    sector_counts = f.groupby("sector")["startup"].nunique().sort_values(ascending=False).head(15).reset_index()
    fig_sector = px.bar(sector_counts, y="sector", x="startup", orientation="h",
                        labels={"sector":"Sector", "startup":"# Startups"},
                        color="startup", color_continuous_scale="Magenta")
    fig_sector.update_layout(height=500, coloraxis_showscale=False, template="plotly_dark", margin=dict(l=10,r=10,t=40,b=10))
    st.plotly_chart(fig_sector, use_container_width=True)

with colB:
    st.subheader("TRL Distribution")
    trl_counts = f["trl_num"].value_counts().sort_index().reset_index()
    trl_counts.columns = ["TRL", "Count"]
    fig_trl = px.pie(trl_counts, values="Count", names="TRL", hole=0.5, color="TRL",
                     color_discrete_sequence=px.colors.sequential.Viridis)
    fig_trl.update_traces(textposition="outside", textinfo="label+percent")
    fig_trl.update_layout(template="plotly_dark", height=500, margin=dict(l=10,r=10,t=40,b=10))
    st.plotly_chart(fig_trl, use_container_width=True)

with colC:
    st.subheader("Stage of Startups")
    stage_counts = f["stage_norm"].value_counts().rename_axis("Stage").reset_index(name="Count")
    fig_stage = px.pie(stage_counts, values="Count", names="Stage", hole=0.5,
                       color_discrete_sequence=["#66c2a5","#fc8d62","#8da0cb","#e78ac3","#999999"])
    fig_stage.update_traces(textposition="outside", textinfo="label+percent")
    fig_stage.update_layout(template="plotly_dark", height=500, margin=dict(l=10,r=10,t=40,b=10))
    st.plotly_chart(fig_stage, use_container_width=True)

st.markdown("---")
st.subheader("Geography (States)")
state_counts = f.groupby("state")["startup"].nunique().sort_values(ascending=False).reset_index()
fig_state = px.bar(state_counts.head(20), x="state", y="startup", labels={"state":"State","startup":"# Startups"},
                   color="startup", color_continuous_scale="Teal")
fig_state.update_layout(template="plotly_dark", height=420, showlegend=False, margin=dict(l=10,r=10,t=40,b=10))
st.plotly_chart(fig_state, use_container_width=True)

st.caption("Tip: Use the filters on the left to slice by Accelerator, State, Sector, or TRL bucket. Click a bar to cross-filter, and use the selector above to view startup names for a specific accelerator.")
