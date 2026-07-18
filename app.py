import datetime as dt

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Employee Productivity Report", layout="wide", initial_sidebar_state="expanded")

# ============================================================
# Palette (validated categorical / sequential / diverging / status set)
# ============================================================
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRIDLINE = "#e1e0d9"
SURFACE = "#fcfcfb"
PAGE = "#f4f4f1"
BORDER = "rgba(11,11,11,0.10)"

CAT = {
    "blue": "#2a78d6", "green": "#008300", "magenta": "#e87ba4", "yellow": "#eda100",
    "aqua": "#1baf7a", "orange": "#eb6834", "violet": "#4a3aa7", "red": "#e34948",
}
CAT_ORDER = ["blue", "green", "magenta", "yellow", "aqua", "orange", "violet", "red"]
CAT_LIST = [CAT[k] for k in CAT_ORDER]

SEQ_BLUE = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#2a78d6", "#1c5cab", "#104281", "#0d366b"]
DIVERGING = [[0.0, CAT["blue"]], [0.5, "#f0efec"], [1.0, CAT["red"]]]

GOOD = "#0ca30c"
GOOD_TEXT = "#006300"
CRITICAL = "#d03b3b"
ACCENT = CAT["violet"]

CHART_FONT = dict(family="system-ui, -apple-system, 'Segoe UI', sans-serif", color=INK_SECONDARY, size=13)


def style_fig(fig, title=None, height=360, showlegend=False):
    layout_kwargs = dict(
        font=CHART_FONT,
        plot_bgcolor=SURFACE,
        paper_bgcolor=SURFACE,
        height=height,
        margin=dict(l=10, r=10, t=40 if title else 10, b=10),
        showlegend=showlegend,
    )
    if title:
        layout_kwargs["title"] = dict(text=title, font=dict(size=14, color=INK_PRIMARY))
    if showlegend:
        layout_kwargs["legend"] = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)
    fig.update_layout(**layout_kwargs)
    fig.update_xaxes(gridcolor=GRIDLINE, zeroline=False, showline=True, linecolor=GRIDLINE, color=INK_MUTED)
    fig.update_yaxes(gridcolor=GRIDLINE, zeroline=False, showline=False, color=INK_MUTED)
    return fig


# ============================================================
# CSS
# ============================================================
st.markdown(
    f"""
    <style>
    .stAppDeployButton, .stDeployButton, [data-testid="stSkillsNudge"] {{ display: none !important; }}
    header[data-testid="stHeader"] {{ display: none !important; }}
    .stApp {{ background: {PAGE}; }}
    .block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1300px; }}

    .report-header {{
        display: flex; justify-content: space-between; align-items: flex-end;
        margin-bottom: 1.4rem;
    }}
    .report-title {{ font-size: 1.6rem; font-weight: 700; color: {INK_PRIMARY}; margin: 0; }}
    .report-subtitle {{ font-size: 0.9rem; color: {INK_MUTED}; margin-top: 2px; }}
    .report-meta {{
        text-align: right; font-size: 0.82rem; color: {INK_MUTED};
        background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 999px;
        padding: 6px 14px;
    }}

    div[class*="st-key-card-"] {{
        background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 18px;
        padding: 20px 22px; box-shadow: 0 1px 2px rgba(11,11,11,0.04);
        margin-bottom: 1.1rem;
    }}
    .card-title {{ font-size: 0.95rem; font-weight: 600; color: {INK_PRIMARY}; margin-bottom: 2px; }}
    .card-subtitle {{ font-size: 0.78rem; color: {INK_MUTED}; margin-bottom: 10px; }}

    .kpi-card {{
        border-radius: 18px; padding: 18px 20px; margin-bottom: 1.1rem;
        border: 1px solid {BORDER};
    }}
    .kpi-hero {{
        background: linear-gradient(135deg, {ACCENT} 0%, #6f5fd8 100%);
        color: white; border: none;
    }}
    .kpi-hero .kpi-label, .kpi-hero .kpi-caption {{ color: rgba(255,255,255,0.78); }}
    .kpi-hero .kpi-value {{ color: white; }}
    .kpi-plain {{ background: {SURFACE}; }}
    .kpi-label {{ font-size: 0.8rem; color: {INK_MUTED}; margin-bottom: 6px; }}
    .kpi-value {{ font-size: 1.7rem; font-weight: 700; color: {INK_PRIMARY}; line-height: 1.1; }}
    .kpi-num {{ white-space: nowrap; }}
    .kpi-caption {{ font-size: 0.76rem; color: {INK_MUTED}; margin-top: 6px; }}

    .badge {{
        display: inline-block; padding: 2px 9px; border-radius: 999px;
        font-size: 0.74rem; font-weight: 600; margin-left: 6px;
    }}
    .badge-good {{ background: rgba(12,163,12,0.12); color: {GOOD_TEXT}; }}
    .badge-critical {{ background: rgba(208,59,59,0.12); color: {CRITICAL}; }}
    .badge-neutral {{ background: rgba(11,11,11,0.06); color: {INK_SECONDARY}; }}

    .rank-row {{
        display: flex; align-items: center; justify-content: space-between;
        padding: 8px 0; border-bottom: 1px solid {GRIDLINE};
    }}
    .rank-row:last-child {{ border-bottom: none; }}
    .rank-dot {{ width: 9px; height: 9px; border-radius: 50%; display: inline-block; margin-right: 9px; }}
    .rank-name {{ font-size: 0.86rem; color: {INK_PRIMARY}; font-weight: 500; }}
    .rank-value {{ font-size: 0.86rem; color: {INK_SECONDARY}; font-variant-numeric: tabular-nums; }}

    section[data-testid="stSidebar"] {{ background: {SURFACE}; border-right: 1px solid {BORDER}; }}
    section[data-testid="stSidebar"] .block-container {{ padding-top: 1.5rem; }}
    .sidebar-title {{ font-size: 1.05rem; font-weight: 700; color: {INK_PRIMARY}; margin-bottom: 0.2rem; }}
    .sidebar-group {{ font-size: 0.78rem; font-weight: 600; color: {INK_MUTED}; text-transform: uppercase;
        letter-spacing: 0.04em; margin-top: 1.1rem; margin-bottom: 0.3rem; }}

    div[data-baseweb="tag"] {{ background-color: {ACCENT} !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Data
# ============================================================
@st.cache_data
def load_data():
    df = pd.read_csv("data/Extended_Employee_Performance_and_Productivity_Data.csv")
    df["Hire_Date"] = pd.to_datetime(df["Hire_Date"])
    df["Resigned"] = df["Resigned"].astype(bool)
    for col in ["Department", "Gender", "Job_Title", "Education_Level"]:
        df[col] = df[col].astype(str).str.strip().str.title()

    df["Projects_per_Hour"] = df["Projects_Handled"] / df["Work_Hours_Per_Week"]

    def normalize(s):
        return (s - s.min()) / (s.max() - s.min())

    df["Productivity_Index"] = (
        normalize(df["Performance_Score"])
        + normalize(df["Projects_per_Hour"])
        + normalize(df["Employee_Satisfaction_Score"])
    ) / 3
    return df


df = load_data()
BASELINE = {
    "productivity": df["Productivity_Index"].mean(),
    "performance": df["Performance_Score"].mean(),
    "resignation": df["Resigned"].mean(),
    "count": len(df),
}

# ============================================================
# Sidebar filters
# ============================================================
with st.sidebar:
    st.markdown('<div class="sidebar-title">Filters</div>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-group">Department</div>', unsafe_allow_html=True)
    departments = sorted(df["Department"].unique())
    sel_departments = st.multiselect("Department", departments, default=departments, label_visibility="collapsed")

    st.markdown('<div class="sidebar-group">Education Level</div>', unsafe_allow_html=True)
    educations = sorted(df["Education_Level"].unique())
    sel_education = st.multiselect("Education", educations, default=educations, label_visibility="collapsed")

    st.markdown('<div class="sidebar-group">Gender</div>', unsafe_allow_html=True)
    genders = sorted(df["Gender"].unique())
    sel_gender = st.multiselect("Gender", genders, default=genders, label_visibility="collapsed")

    st.markdown('<div class="sidebar-group">Employment Status</div>', unsafe_allow_html=True)
    resign_options = {"Active": False, "Resigned": True}
    sel_resign_labels = st.multiselect(
        "Status", list(resign_options.keys()), default=list(resign_options.keys()), label_visibility="collapsed"
    )
    sel_resign = [resign_options[label] for label in sel_resign_labels]

    st.markdown('<div class="sidebar-group">Age Range</div>', unsafe_allow_html=True)
    age_min, age_max = int(df["Age"].min()), int(df["Age"].max())
    sel_age = st.slider("Age", age_min, age_max, (age_min, age_max), label_visibility="collapsed")

    st.markdown('<div class="sidebar-group">Years at Company</div>', unsafe_allow_html=True)
    tenure_min, tenure_max = int(df["Years_At_Company"].min()), int(df["Years_At_Company"].max())
    sel_tenure = st.slider("Tenure", tenure_min, tenure_max, (tenure_min, tenure_max), label_visibility="collapsed")

mask = (
    df["Department"].isin(sel_departments)
    & df["Education_Level"].isin(sel_education)
    & df["Gender"].isin(sel_gender)
    & df["Resigned"].isin(sel_resign)
    & df["Age"].between(*sel_age)
    & df["Years_At_Company"].between(*sel_tenure)
)
fdf = df[mask]

if fdf.empty:
    st.warning("No employees match the selected filters.")
    st.stop()

# ============================================================
# Header
# ============================================================
today = dt.date.today().strftime("%A, %B %d %Y")
st.markdown(
    f"""
    <div class="report-header">
        <div>
            <div class="report-title">Employee Productivity Report</div>
            <div class="report-subtitle">100,000 employees · Productivity Index blends Performance,
            Projects-per-Hour, and Satisfaction</div>
        </div>
        <div class="report-meta">{today}<br><b>{len(fdf):,}</b> of {len(df):,} employees shown</div>
    </div>
    """,
    unsafe_allow_html=True,
)


def badge(delta, higher_is_good=True):
    good = (delta >= 0) if higher_is_good else (delta <= 0)
    cls = "badge-good" if good else "badge-critical"
    arrow = "&#9650;" if delta >= 0 else "&#9660;"
    return f'<span class="badge {cls}">{arrow} {abs(delta):.1%}</span>'


# ============================================================
# KPI row
# ============================================================
avg_prod = fdf["Productivity_Index"].mean()
avg_perf = fdf["Performance_Score"].mean()
resign_rate = fdf["Resigned"].mean()

prod_delta = (avg_prod - BASELINE["productivity"]) / BASELINE["productivity"]
perf_delta = (avg_perf - BASELINE["performance"]) / BASELINE["performance"]
resign_delta = resign_rate - BASELINE["resignation"]
count_share = len(fdf) / len(df)

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        f"""<div class="kpi-card kpi-hero">
            <div class="kpi-label">Avg Productivity Index</div>
            <div class="kpi-value"><span class="kpi-num">{avg_prod:.3f}</span> {badge(prod_delta)}</div>
            <div class="kpi-caption">vs. company baseline {BASELINE['productivity']:.3f}</div>
        </div>""",
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f"""<div class="kpi-card kpi-plain">
            <div class="kpi-label">Employees (filtered)</div>
            <div class="kpi-value"><span class="kpi-num">{len(fdf):,}</span></div>
            <div class="kpi-caption">{count_share:.1%} of total workforce</div>
        </div>""",
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f"""<div class="kpi-card kpi-plain">
            <div class="kpi-label">Avg Performance Score</div>
            <div class="kpi-value"><span class="kpi-num">{avg_perf:.2f}</span> {badge(perf_delta)}</div>
            <div class="kpi-caption">vs. company baseline {BASELINE['performance']:.2f}</div>
        </div>""",
        unsafe_allow_html=True,
    )
with c4:
    st.markdown(
        f"""<div class="kpi-card kpi-plain">
            <div class="kpi-label">Resignation Rate</div>
            <div class="kpi-value"><span class="kpi-num">{resign_rate:.1%}</span> {badge(resign_delta, higher_is_good=False)}</div>
            <div class="kpi-caption">vs. company baseline {BASELINE['resignation']:.1%}</div>
        </div>""",
        unsafe_allow_html=True,
    )

# ============================================================
# Main row: department bar (left) + gauge & ranked list (right)
# ============================================================
left, right = st.columns([2, 1])

with left:
    with st.container(key="card-dept-chart"):
        st.markdown('<div class="card-title">Productivity Index by Department</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-subtitle">Sorted high to low · dashed line marks the overall average</div>', unsafe_allow_html=True)

        benchmarks = (
            fdf.groupby("Department")[["Performance_Score", "Projects_per_Hour", "Productivity_Index"]]
            .mean()
            .sort_values("Productivity_Index", ascending=False)
            .reset_index()
        )
        fig = px.bar(
            benchmarks, x="Department", y="Productivity_Index",
            color="Productivity_Index", color_continuous_scale=SEQ_BLUE,
        )
        fig.update_traces(marker_line_width=0, width=0.6)
        fig.add_hline(y=avg_prod, line_dash="dash", line_color=INK_MUTED, line_width=1.5)
        fig.update_layout(coloraxis_showscale=False)
        fig.update_yaxes(range=[0, max(1.0, benchmarks["Productivity_Index"].max() * 1.15)])
        st.plotly_chart(style_fig(fig, height=340), width="stretch")

with right:
    with st.container(key="card-glance"):
        st.markdown('<div class="card-title">Productivity at a Glance</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-subtitle">Filtered average vs. best department</div>', unsafe_allow_html=True)

        best_dept = benchmarks.iloc[0]
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=avg_prod,
            number={"valueformat": ".3f", "font": {"color": INK_PRIMARY}},
            delta={"reference": BASELINE["productivity"], "valueformat": ".3f",
                   "increasing": {"color": GOOD_TEXT}, "decreasing": {"color": CRITICAL}},
            gauge={
                "axis": {"range": [0, 1], "tickcolor": INK_MUTED, "tickfont": {"size": 9}},
                "bar": {"color": ACCENT, "thickness": 0.35},
                "bgcolor": GRIDLINE,
                "borderwidth": 0,
                "threshold": {
                    "line": {"color": CAT["blue"], "width": 3},
                    "thickness": 0.85,
                    "value": best_dept["Productivity_Index"],
                },
            },
        ))
        fig.update_layout(height=200, margin=dict(l=20, r=20, t=10, b=0), paper_bgcolor=SURFACE, font=CHART_FONT)
        st.plotly_chart(fig, width="stretch")
        st.caption(f"Blue marker = top department ({best_dept['Department']})")

        st.markdown('<div class="card-subtitle" style="margin-top:10px;">Top departments</div>', unsafe_allow_html=True)
        rows_html = ""
        for i, row in benchmarks.head(5).iterrows():
            dot = CAT_LIST[i % len(CAT_LIST)]
            d = (row["Productivity_Index"] - BASELINE["productivity"]) / BASELINE["productivity"]
            rows_html += f"""<div class="rank-row">
                <span><span class="rank-dot" style="background:{dot};"></span>
                <span class="rank-name">{row['Department']}</span></span>
                <span class="rank-value">{row['Productivity_Index']:.3f} {badge(d)}</span>
            </div>"""
        st.markdown(rows_html, unsafe_allow_html=True)

# ============================================================
# Correlation heatmap
# ============================================================
with st.container(key="card-heatmap"):
    st.markdown('<div class="card-title">Correlation Heatmap</div>', unsafe_allow_html=True)
    st.markdown('<div class="card-subtitle">Blue = negative, red = positive, gray = no relationship</div>', unsafe_allow_html=True)
    corr_cols = [
        "Age", "Years_At_Company", "Performance_Score", "Work_Hours_Per_Week",
        "Projects_Handled", "Overtime_Hours", "Sick_Days", "Remote_Work_Frequency",
        "Training_Hours", "Promotions", "Employee_Satisfaction_Score", "Productivity_Index",
    ]
    corr = fdf[corr_cols].corr()
    fig = px.imshow(corr, text_auto=".2f", color_continuous_scale=DIVERGING, zmin=-1, zmax=1, aspect="auto")
    fig.update_traces(textfont_size=10)
    fig.update_layout(coloraxis_showscale=False)
    st.plotly_chart(style_fig(fig, height=560), width="stretch")

# ============================================================
# Factor explorer
# ============================================================
with st.container(key="card-factor"):
    st.markdown('<div class="card-title">Factor vs Productivity</div>', unsafe_allow_html=True)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Training Hours", "Remote Work Frequency", "Overtime", "Tenure", "Education Level"]
    )

    with tab1:
        sample = fdf.sample(min(3000, len(fdf)), random_state=1)
        fig = px.scatter(sample, x="Training_Hours", y="Productivity_Index", trendline="ols",
                          opacity=0.35, trendline_color_override=ACCENT,
                          color_discrete_sequence=[CAT["blue"]])
        st.plotly_chart(style_fig(fig, height=380), width="stretch")

    with tab2:
        fig = px.box(fdf, x="Remote_Work_Frequency", y="Productivity_Index", color_discrete_sequence=[CAT["blue"]])
        st.plotly_chart(style_fig(fig, height=380), width="stretch")

    with tab3:
        sample = fdf.sample(min(3000, len(fdf)), random_state=1)
        c1, c2 = st.columns(2)
        with c1:
            fig = px.scatter(sample, x="Overtime_Hours", y="Employee_Satisfaction_Score", opacity=0.35,
                              color_discrete_sequence=[CAT["blue"]])
            st.plotly_chart(style_fig(fig, title="Overtime vs Satisfaction", height=340), width="stretch")
        with c2:
            fig = px.scatter(sample, x="Overtime_Hours", y="Productivity_Index", opacity=0.35,
                              color_discrete_sequence=[CAT["blue"]])
            st.plotly_chart(style_fig(fig, title="Overtime vs Productivity", height=340), width="stretch")

    with tab4:
        tenure_avg = fdf.groupby("Years_At_Company")["Productivity_Index"].mean().reset_index()
        fig = px.line(tenure_avg, x="Years_At_Company", y="Productivity_Index", markers=True,
                       color_discrete_sequence=[CAT["blue"]])
        fig.update_traces(line_width=2, marker_size=6)
        st.plotly_chart(style_fig(fig, height=380), width="stretch")

    with tab5:
        order = fdf.groupby("Education_Level")["Productivity_Index"].mean().sort_values(ascending=False).index
        fig = px.bar(
            fdf.groupby("Education_Level")["Productivity_Index"].mean().reindex(order).reset_index(),
            x="Education_Level", y="Productivity_Index", color_discrete_sequence=[CAT["blue"]],
        )
        fig.update_traces(marker_line_width=0, width=0.55)
        st.plotly_chart(style_fig(fig, height=380), width="stretch")

# ============================================================
# Resignation comparison
# ============================================================
with st.container(key="card-resign"):
    st.markdown('<div class="card-title">Resigned vs Active Employees</div>', unsafe_allow_html=True)
    st.markdown('<div class="card-subtitle">Average Productivity Index by employment status</div>', unsafe_allow_html=True)
    resign_avg = (
        fdf.groupby("Resigned")["Productivity_Index"].mean().rename({False: "Active", True: "Resigned"}).reset_index()
    )
    resign_avg.columns = ["Status", "Productivity_Index"]
    fig = px.bar(resign_avg, x="Status", y="Productivity_Index", color_discrete_sequence=[CAT["blue"]])
    fig.update_traces(marker_line_width=0, width=0.4)
    fig.update_yaxes(range=[0, 1])
    st.plotly_chart(style_fig(fig, height=280), width="stretch")

# ============================================================
# Insights
# ============================================================
with st.container(key="card-insights"):
    st.markdown('<div class="card-title">Key Findings & Recommendations</div>', unsafe_allow_html=True)
    st.markdown(
        """
1. **No single common HR factor drives productivity in this dataset.** Correlations between Productivity Index and
   Training Hours, Remote Work Frequency, Overtime Hours, Age, Tenure, Sick Days, Promotions, Education Level,
   Job Title, and Gender are all effectively zero.
2. **Department differences are marginal** — a spread of roughly 0.007 on a 0-1 scale across all departments.
3. **Work Hours Per Week shows a mild negative relationship (r &asymp; -0.15)** with Projects-per-Hour, largely a
   mechanical effect of dividing by more hours, not evidence that working more makes people less productive.
4. **Resigned vs. active employees show no productivity gap.**

**Recommendations:** don't over-invest based on weak signals; focus on Performance Score and Satisfaction
(which move together, r &asymp; 0.57); investigate hours vs. output quality rather than quantity; collect richer
data (project complexity, manager ratings, team dynamics); and benchmark departments sparingly given the
negligible spread.
"""
    )
