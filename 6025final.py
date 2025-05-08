pip install -r requirements.txt

st.set_page_config(page_title="Ice‑Hockey Battery Dashboard", layout="wide")
st.title("San Diego Hockey Club Performance Testing")

# ─────────────────────────── Data loader ─────────────────────────────────── #
@st.cache_data
def load_data(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path).rename(columns={
        "CMJ Peak Force (N)":  "CMJ_Peak_Force_N",
        "IMTP Peak Force (N)": "IMTP_Peak_Force_N",
        "CMJ Jump Height (cm)":"CMJ_Jump_Height_cm",
        "RSImod":              "CMJ_RSImod",
        "RFD@250ms":           "IMTP_RFD_0_250ms",
        "DSI":                 "Dynamic_Strength_Index",
        "Athlete Name":"Athlete","Name":"Athlete"
    })
    desc_cols = ["Sex","Age","Height (cm)","Weight (kg)"]
    kpi_cols = ["CMJ_Peak_Force_N","IMTP_Peak_Force_N","Dynamic_Strength_Index",
                "CMJ_Jump_Height_cm","CMJ_RSImod","IMTP_RFD_0_250ms"]
    df = df[["Athlete"]+desc_cols+kpi_cols].apply(pd.to_numeric, errors="ignore")
    for c in kpi_cols:
        mu, sd = df[c].mean(), df[c].std(ddof=0)
        df[f"{c}_T"] = 50 + 10*(df[c]-mu)/sd
        df[f"{c}_Z"] = (df[c]-mu)/sd
    df["Battery_Score_T"] = df[[f"{c}_T" for c in kpi_cols]].mean(1).round(1)
    return df

DATA = Path("6025_final_data.csv")
df   = load_data(DATA) if DATA.exists() else st.stop()

KPI_LABELS = {
    "CMJ_Peak_Force_N":       "Dynamic Peak Force (N)",
    "IMTP_Peak_Force_N":      "Isometric Peak Force (N)",
    "Dynamic_Strength_Index": "DSI",
    "CMJ_Jump_Height_cm":     "Jump Height (cm)",
    "CMJ_RSImod":             "RSImod",
    "IMTP_RFD_0_250ms":       "RFD 250 ms",
}
KPI_COLS = list(KPI_LABELS.keys())

# Gulls palette
NAVY   = "#041E42"
LTBLUE = "#6BC3F6"
ORANGE = "#F47A38"

# ───── IMTP bars (now with T‑score hover) ───── #
def make_imtp_bars(d):
    fig = go.Figure()

    fig.add_bar(
        x=d["Athlete"], y=d["IMTP_Peak_Force_N"],
        name="Peak Force (N)", offsetgroup="PF",
        marker_color=LTBLUE, marker_line=dict(color="#021025"),
        customdata=d["IMTP_Peak_Force_N_T"],
        hovertemplate="%{y:.0f} N<br>T‑score: %{customdata:.1f}<extra>%{x}</extra>",
        yaxis="y",
    )
    fig.add_bar(
        x=d["Athlete"], y=d["IMTP_RFD_0_250ms"],
        name="RFD 250 (N/s)", offsetgroup="RFD",
        marker_color=ORANGE, marker_line=dict(color="#c33d16"),
        customdata=d["IMTP_RFD_0_250ms_T"],
        hovertemplate="%{y:.0f} N/s<br>T‑score: %{customdata:.1f}<extra>%{x}</extra>",
        yaxis="y2",
    )

    fig.update_layout(
        barmode="group", bargap=0.25, height=520,
        yaxis=dict(title="Peak Force (N)",
                   tickmode="array", tickvals=[0,1200,2400,3600,4800,6000],
                   showgrid=True, gridcolor="rgba(255,255,255,0.15)"),
        yaxis2=dict(title="RFD 0‑250 (N/s)", overlaying="y", side="right",
                    tickmode="array", tickvals=[0,2400,4800,7200,9600,12000],
                    showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(l=40, r=60, t=40, b=40),
    )
    return fig

# ───── CMJ bars (now with T‑score hover) ───── #
def make_cmj_bars(d):
    fig = go.Figure()

    fig.add_bar(
        x=d["Athlete"], y=d["CMJ_Jump_Height_cm"],
        name="Jump Height (cm)", offsetgroup="JH",
        marker_color=LTBLUE, marker_line=dict(color="#378eb3"),
        customdata=d["CMJ_Jump_Height_cm_T"],
        hovertemplate="%{y:.1f} cm<br>T‑score: %{customdata:.1f}<extra>%{x}</extra>",
        yaxis="y",
    )
    fig.add_bar(
        x=d["Athlete"], y=d["CMJ_RSImod"],
        name="RSImod", offsetgroup="RSI",
        marker_color=ORANGE, marker_line=dict(color="#c33d16"),
        customdata=d["CMJ_RSImod_T"],
        hovertemplate="%{y:.2f}<br>T‑score: %{customdata:.1f}<extra>%{x}</extra>",
        yaxis="y2",
    )

    fig.update_layout(
        barmode="group", bargap=0.25, height=520,
        yaxis=dict(title="Jump Height (cm)",
                   tickmode="array", tickvals=[0,10,20,30,40,50],
                   showgrid=True, gridcolor="rgba(255,255,255,0.15)"),
        yaxis2=dict(title="RSImod", overlaying="y", side="right",
                    tickmode="array", tickvals=[0.0,0.2,0.4,0.6,0.8,1.0],
                    showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        margin=dict(l=40, r=60, t=40, b=40),
    )
    return fig

# Battery bar (unchanged)
battery_fig = px.bar(
    df.sort_values("Battery_Score_T"),
    x="Battery_Score_T", y="Athlete", orientation="h", text="Battery_Score_T",
    color="Battery_Score_T", range_color=(30,80),
    labels={"Battery_Score_T":"Mean T-Score"},
    color_continuous_scale=["#d62728","#ff7f0e","#d3d3d3","#2ca02c","#1f77b4"],
).update_layout(coloraxis_showscale=False, height=450)

# FV scatter (add T‑score in hover)
colour_scale=[[0,"red"],[0.2,"red"],[0.4,"orange"],[0.7,"green"],[1.0,"orange"]]
fv_fig = px.scatter(
    df, x="IMTP_Peak_Force_N", y="CMJ_Peak_Force_N",
    color="Dynamic_Strength_Index", hover_name="Athlete",
    custom_data=["Dynamic_Strength_Index_T"],
    color_continuous_scale=colour_scale, range_color=(0,1),
    labels={"IMTP_Peak_Force_N":"Isometric Peak Force (N)",
            "CMJ_Peak_Force_N":"Dynamic Peak Force (N)","Dynamic_Strength_Index":"DSI"},
    height=450
)
fv_fig.update_traces(
    marker=dict(size=24, line=dict(width=1, color="black")),
    hovertemplate="Iso PF: %{x:.0f} N<br>Dyn PF: %{y:.0f} N"
                  "<br>DSI: %{marker.color:.2f}"
                  "<br>T‑score: %{customdata[0]:.1f}"
                  "<extra>%{hovertext}</extra>"
)
fv_fig.update_layout(
    coloraxis_colorbar=dict(
        title="DSI", tickmode="array",
        tickvals=[0.0,0.2,0.4,0.6,0.8,1.0],
        ticktext=["0.0","0.2","0.4","0.6","0.8","1.0"],
        len=1.0, y=0.5, thickness=15),
    margin=dict(l=20, r=60, t=40, b=40)
)

# ───── Tabs ───── #
team_tab, athlete_tab = st.tabs(["📊 Team", "👤 Athlete"])

# ================================ TEAM TAB ================================ #
with team_tab:
    st.markdown("#### Overall Battery Score")
    st.plotly_chart(battery_fig, use_container_width=True)

    col_imtp, col_cmj = st.columns(2)
    with col_imtp:
        st.markdown("##### IMTP Profile")
        st.plotly_chart(make_imtp_bars(df.sort_values("Athlete")), use_container_width=True)
    with col_cmj:
        st.markdown("##### CMJ Profile")
        st.plotly_chart(make_cmj_bars(df.sort_values("Athlete")), use_container_width=True)

    st.markdown("#### Dynamic Strength Index")
    st.plotly_chart(fv_fig, use_container_width=True)

    if set(["Sex","Age","Height (cm)","Weight (kg)"]).issubset(df.columns):
        with st.expander("Athlete Descriptive Statistics"):
            desc_cols=["Sex","Age","Height (cm)","Weight (kg)"]
            st.dataframe(df[["Athlete"]+desc_cols], use_container_width=True)

# ============================== ATHLETE TAB =============================== #
with athlete_tab:
    athlete = st.selectbox("Select Athlete", df["Athlete"], key="athlete_select")
    row = df[df["Athlete"]==athlete].iloc[0]

    st.subheader(f"{athlete}")

    g_col, r_col = st.columns(2)

    with g_col:
        st.markdown("#### Battery Score")
        gauge_fig = go.Figure(go.Indicator(
            mode="gauge+number", value=row["Battery_Score_T"],
            number={'suffix':' T'},
            gauge={
                "axis":{"range":[20,80]},
                "steps":[
                    {"range":[20,40],"color":"#d62728"},
                    {"range":[40,50],"color":"#ff7f0e"},
                    {"range":[50,60],"color":"#d3d3d3"},
                    {"range":[60,80],"color":"#2ca02c"},
                ],
                "threshold":{"line":{"color":"#1f77b4","width":4},"value":row["Battery_Score_T"]},
            }
        ))
        gauge_fig.update_layout(height=350, margin=dict(l=10,r=10,t=40,b=10))
        st.plotly_chart(gauge_fig, use_container_width=True)

    with r_col:
        st.markdown("#### KPI Z‑score Radar")

        theta = [KPI_LABELS[c] for c in KPI_COLS] + [KPI_LABELS[KPI_COLS[0]]]
        athlete_vals = [row[f"{c}_Z"] for c in KPI_COLS] + [row[f"{KPI_COLS[0]}_Z"]]
        team_mean    = [0]*len(KPI_COLS) + [0]

        radar = go.Figure()

        radar.add_scatterpolar(
            r=team_mean, theta=theta, fill="toself",
            name="Team Average", line=dict(color=ORANGE),
            fillcolor="rgba(244,122,56,0.30)"
        )
        radar.add_scatterpolar(
            r=athlete_vals, theta=theta, fill="toself",
            name=athlete, line=dict(color=LTBLUE, width=3),
            fillcolor="rgba(107,195,246,0.50)"
        )

        radar.update_layout(
            polar=dict(
                bgcolor=NAVY,
                radialaxis=dict(range=[-3,3],
                                tickvals=[-2,-1,0,1,2],
                                gridcolor="rgba(255,255,255,0.2)",
                                tickfont=dict(color="white")),
                angularaxis=dict(tickfont=dict(color="white"))
            ),
            # paper_bgcolor/plot_bgcolor removed → default app background
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
            height=350, margin=dict(l=10, r=10, t=40, b=10)
        )
        st.plotly_chart(radar, use_container_width=True)

    with st.expander("Raw KPI Values"):
        st.dataframe(pd.DataFrame({
            "KPI":[KPI_LABELS[c] for c in KPI_COLS],
            "Value":[row[c] for c in KPI_COLS],
            "Z‑score":[row[f"{c}_Z"] for c in KPI_COLS],
            "T‑score":[row[f"{c}_T"] for c in KPI_COLS],
        }).round(2), use_container_width=True)
