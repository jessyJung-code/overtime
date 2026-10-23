"""
🌙 퇴근 대시보드 (Streamlit)

실행:  streamlit run app.py
데이터: data/퇴근기록.csv  (열: 날짜, 출근, 퇴근 / 시간은 HH:MM)
"""
import datetime as dt
from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ─────────────────────────────────────────────────────────────
# 기본 설정
# ─────────────────────────────────────────────────────────────
DATA_PATH = Path(__file__).parent / "data" / "퇴근기록.csv"
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]
C = {
    "ink": "#1E2A3B", "sub": "#7A8699", "line": "#E6EAF0",
    "teal": "#2A9D8F", "coral": "#F4845F", "sand": "#E9C46A",
    "plum": "#7B6CF6", "sky": "#8ECAE6", "rose": "#E05A6D", "navy": "#264653",
}
FONT = "Pretendard, 'Noto Sans KR', 'Malgun Gothic', sans-serif"

st.set_page_config(page_title="퇴근 대시보드", page_icon="🌙", layout="wide")

st.markdown(
    """
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<style>
html, body, [class*="css"], .stApp, button, input, textarea { font-family: Pretendard, 'Noto Sans KR', sans-serif !important; }
.stApp { background: linear-gradient(180deg, #F4F6FB 0%, #FBFCFE 100%); }
.block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1400px; }
section[data-testid="stSidebar"] { background: #1E2A3B; }
section[data-testid="stSidebar"] * { color: #E8ECF3 !important; }
section[data-testid="stSidebar"] input, section[data-testid="stSidebar"] textarea { color: #1E2A3B !important; }
section[data-testid="stSidebar"] .stButton button, section[data-testid="stSidebar"] .stDownloadButton button,
section[data-testid="stSidebar"] .stFormSubmitButton button {
  background: #F4845F; border: none; color: white !important; font-weight: 700; border-radius: 10px; width: 100%;
}
.hero { background: linear-gradient(120deg, #1E2A3B 0%, #2B3F5C 55%, #3D3A6B 100%);
  border-radius: 22px; padding: 26px 32px; color: white; margin-bottom: 18px; position: relative; overflow: hidden; }
.hero:after { content: "🌙"; position: absolute; right: 34px; top: 10px; font-size: 92px; opacity: .18; }
.hero h1 { font-size: 30px; font-weight: 800; margin: 0 0 6px 0; color: white; letter-spacing: -0.5px; }
.hero p { margin: 0; color: #C9D3E3; font-size: 14px; }
.badge { display: inline-block; margin-top: 12px; padding: 6px 14px; border-radius: 999px;
  background: rgba(255,255,255,.13); font-size: 14px; font-weight: 700; color: #FFE7A3; }
.kpi { background: white; border-radius: 18px; padding: 18px 18px 14px; border: 1px solid #E6EAF0;
  box-shadow: 0 4px 18px rgba(30,42,59,.06); height: 100%; position: relative; overflow: hidden; }
.kpi:before { content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 5px; background: var(--c); }
.kpi .lab { font-size: 13px; color: #7A8699; font-weight: 600; }
.kpi .val { font-size: 30px; font-weight: 800; color: var(--c); line-height: 1.25; margin-top: 4px; letter-spacing: -0.5px; }
.kpi .val small { font-size: 15px; font-weight: 700; margin-left: 2px; }
.kpi .sub { font-size: 12px; color: #7A8699; margin-top: 4px; }
.kpi .ico { position: absolute; right: 14px; top: 12px; font-size: 22px; opacity: .85; }
.sec { font-size: 18px; font-weight: 800; color: #1E2A3B; margin: 22px 0 6px 2px; }
.sec span { font-size: 13px; color: #7A8699; font-weight: 500; margin-left: 8px; }
div[data-testid="stPlotlyChart"] { background: white; border-radius: 18px; border: 1px solid #E6EAF0;
  box-shadow: 0 4px 18px rgba(30,42,59,.05); padding: 6px 6px 0 6px; }
</style>
""",
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────
# 데이터 처리
# ─────────────────────────────────────────────────────────────
def to_hhmm(v):
    """여러 형태의 시간 값을 'HH:MM' 문자열로 통일"""
    if v is None or (isinstance(v, float) and pd.isna(v)) or (isinstance(v, str) and not v.strip()):
        return None
    if isinstance(v, pd.Timestamp):
        v = v.to_pydatetime()
    if isinstance(v, dt.datetime):
        return v.strftime("%H:%M")
    if isinstance(v, dt.time):
        return v.strftime("%H:%M")
    if isinstance(v, (int, float)):  # 엑셀 시간(하루의 비율)
        m = round(float(v) % 1 * 1440)
        return f"{m // 60:02d}:{m % 60:02d}"
    s = str(v).strip()
    for fmt in ("%H:%M", "%H:%M:%S", "%H시%M분", "%H%M"):
        try:
            return dt.datetime.strptime(s, fmt).strftime("%H:%M")
        except ValueError:
            pass
    return None


def norm_col(c) -> str:
    """'퇴근시간', '출근 시각' 같은 열 이름을 '퇴근', '출근'으로 통일"""
    c = str(c).strip()
    for key in ("날짜", "출근", "퇴근"):
        if c.startswith(key):
            return key
    return c


def tidy(df: pd.DataFrame) -> pd.DataFrame:
    """열 이름 정리 + 형식 통일 + 같은 날짜는 마지막 값만 남김"""
    df = df.rename(columns=norm_col)
    if "출근" not in df.columns:
        df["출근"] = None
    df = df[["날짜", "출근", "퇴근"]].copy()
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce").dt.date
    df["출근"] = df["출근"].map(to_hhmm)
    df["퇴근"] = df["퇴근"].map(to_hhmm)
    df = df.dropna(subset=["날짜", "퇴근"])
    df = df.drop_duplicates("날짜", keep="last").sort_values("날짜").reset_index(drop=True)
    return df


def read_any(file) -> pd.DataFrame:
    """CSV 또는 엑셀(앞서 만든 대시보드 엑셀 포함)에서 날짜·출근·퇴근 표를 찾아 읽기"""
    if file.name.lower().endswith(".csv"):
        return tidy(pd.read_csv(file))
    sheets = pd.read_excel(file, sheet_name=None, header=None)
    for raw in sheets.values():
        for i in range(min(len(raw), 30)):
            row = [norm_col(x) for x in raw.iloc[i].tolist()]
            if "날짜" in row and "퇴근" in row:
                body = raw.iloc[i + 1:].copy()
                body.columns = row
                return tidy(body)
    raise ValueError("'날짜'와 '퇴근' 열이 있는 표를 찾지 못했어요.")


def load() -> pd.DataFrame:
    if DATA_PATH.exists():
        return tidy(pd.read_csv(DATA_PATH, dtype=str))
    return pd.DataFrame(columns=["날짜", "출근", "퇴근"])


def save(df: pd.DataFrame):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    out = df.copy()
    out["날짜"] = pd.to_datetime(out["날짜"]).dt.strftime("%Y-%m-%d")
    out.to_csv(DATA_PATH, index=False, encoding="utf-8-sig")


def mins(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def hhmm(total_min: float) -> str:
    total_min = int(round(total_min))
    return f"{(total_min // 60) % 24:02d}:{total_min % 60:02d}"


def compute(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    d = df.copy()
    d["출근"] = d["출근"].fillna(cfg["start"])
    s = d["출근"].map(mins)
    e = d["퇴근"].map(mins)
    e = e.where(e >= s, e + 1440)  # 자정 넘긴 퇴근
    d["출근분"], d["퇴근분"] = s, e
    d["근무"] = (e - s) / 60 - cfg["lunch"]
    d["야근"] = (d["근무"] - cfg["regular"]).clip(lower=0)
    dts = pd.to_datetime(d["날짜"])
    d["요일"] = dts.dt.weekday.map(lambda i: WEEKDAYS[i])
    d["월"] = dts.dt.to_period("M").astype(str)
    d["주"] = (dts - pd.to_timedelta(dts.dt.weekday, unit="D")).dt.date
    d["늦은퇴근"] = d["퇴근분"] >= cfg["late"]
    return d


def to_excel(d: pd.DataFrame) -> bytes:
    out = d[["날짜", "요일", "출근", "퇴근", "근무", "야근"]].copy()
    out.columns = ["날짜", "요일", "출근", "퇴근", "근무시간(h)", "야근시간(h)"]
    out[["근무시간(h)", "야근시간(h)"]] = out[["근무시간(h)", "야근시간(h)"]].round(2)
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        out.to_excel(xw, index=False, sheet_name="퇴근기록")
        ws = xw.sheets["퇴근기록"]
        for col, w in zip("ABCDEF", [13, 6, 8, 8, 12, 12]):
            ws.column_dimensions[col].width = w
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────
# 상태 & 사이드바
# ─────────────────────────────────────────────────────────────
if "df" not in st.session_state:
    st.session_state.df = load()

with st.sidebar:
    st.markdown("## 🌙 퇴근 기록")

    with st.expander("⚙️ 기준 설정", expanded=False):
        start_t = st.time_input("기본 출근", dt.time(9, 30), step=600)
        lunch = st.number_input("점심(시간)", 0.0, 3.0, 1.0, 0.5)
        regular = st.number_input("정규근무(시간)", 1.0, 12.0, 8.0, 0.5)
        late_t = st.time_input("늦은 퇴근 기준", dt.time(21, 0), step=600)
    cfg = {"start": start_t.strftime("%H:%M"), "lunch": lunch, "regular": regular,
           "late": late_t.hour * 60 + late_t.minute}

    st.markdown("### ➕ 오늘 기록 추가")
    with st.form("add", clear_on_submit=False):
        day = st.date_input("날짜", dt.date.today())
        c1, c2 = st.columns(2)
        in_t = c1.time_input("출근", start_t, step=300)
        out_t = c2.time_input("퇴근", dt.time(21, 0), step=300)
        if st.form_submit_button("저장하기"):
            new = pd.DataFrame([{"날짜": day, "출근": in_t.strftime("%H:%M"), "퇴근": out_t.strftime("%H:%M")}])
            st.session_state.df = tidy(pd.concat([st.session_state.df, new], ignore_index=True))
            save(st.session_state.df)
            st.toast(f"{day:%m/%d} 퇴근 {out_t:%H:%M} 저장했어요 ✅")

    st.markdown("### 📂 데이터")
    up = st.file_uploader("엑셀/CSV 불러오기", type=["xlsx", "csv"],
                          help="'날짜', '퇴근' 열이 있으면 됩니다. '출근'은 없어도 돼요.")
    if up is not None and st.session_state.get("_uploaded") != up.file_id:
        try:
            loaded = read_any(up)
            mode = st.radio("불러온 데이터를", ["기존 기록에 합치기", "기존 기록 대신 쓰기"], key="mode")
            if st.button("적용"):
                base = st.session_state.df if mode.startswith("기존 기록에") else loaded.iloc[0:0]
                st.session_state.df = tidy(pd.concat([base, loaded], ignore_index=True))
                save(st.session_state.df)
                st.session_state._uploaded = up.file_id
                st.rerun()
            st.caption(f"{len(loaded)}일치 기록을 찾았어요.")
        except Exception as ex:  # noqa: BLE001
            st.error(str(ex))

df_raw = st.session_state.df
if df_raw.empty:
    st.info("왼쪽에서 첫 퇴근 기록을 추가하거나 엑셀 파일을 불러오세요.")
    st.stop()

d = compute(df_raw, cfg)

with st.sidebar:
    st.download_button("⬇️ 엑셀로 내려받기", to_excel(d), file_name="퇴근기록.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.caption(f"기록 {len(d)}일 · {d['날짜'].min():%Y.%m.%d} ~ {d['날짜'].max():%Y.%m.%d}")

# ─────────────────────────────────────────────────────────────
# 지표 계산
# ─────────────────────────────────────────────────────────────
n = len(d)
tot_work, tot_ot = d["근무"].sum(), d["야근"].sum()
avg_out = d["퇴근분"].mean()
late_ratio = d["늦은퇴근"].mean()
kal = int((d["야근"] == 0).sum())
latest = d.loc[d["퇴근분"].idxmax()]
movies = tot_ot / 2

if avg_out < 19 * 60:
    title = "🌇 칼퇴 요정"
elif avg_out < 20 * 60 + 30:
    title = "🌆 저녁 있는 사람"
elif avg_out < 21 * 60 + 30:
    title = "🌙 야근 전사"
else:
    title = "🦉 올빼미 마스터"

# 이번 달 vs 지난 달
months = sorted(d["월"].unique())
cur_m = months[-1]
cur_avg = d.loc[d["월"] == cur_m, "야근"].mean()
delta_txt = ""
if len(months) > 1:
    prev_avg = d.loc[d["월"] == months[-2], "야근"].mean()
    diff = (cur_avg - prev_avg) * 60
    arrow = "▲" if diff > 0 else "▼"
    delta_txt = f" · 지난달보다 하루 {arrow}{abs(diff):.0f}분"

# ─────────────────────────────────────────────────────────────
# 헤더 & KPI
# ─────────────────────────────────────────────────────────────
st.markdown(
    f"""<div class="hero"><h1>퇴근 대시보드</h1>
<p>{d['날짜'].min():%Y.%m.%d} – {d['날짜'].max():%Y.%m.%d} · 근무일 {n}일 ·
정시퇴근 기준 {hhmm(mins(cfg['start']) + (cfg['regular'] + cfg['lunch']) * 60)}</p>
<div class="badge">나의 퇴근 칭호: {title}</div></div>""",
    unsafe_allow_html=True,
)


def kpi(col, label, value, unit, sub, color, icon):
    col.markdown(
        f"""<div class="kpi" style="--c:{color}"><div class="ico">{icon}</div>
<div class="lab">{label}</div><div class="val">{value}<small>{unit}</small></div>
<div class="sub">{sub}</div></div>""",
        unsafe_allow_html=True,
    )


k = st.columns(6)
kpi(k[0], "근무일수", n, "일", f"칼퇴 {kal}일", C["navy"], "📅")
kpi(k[1], "총 근무시간", f"{tot_work:,.1f}", "h", f"하루 평균 {tot_work / n:.1f}h", C["teal"], "💼")
kpi(k[2], "총 야근시간", f"{tot_ot:,.1f}", "h", f"하루 평균 {tot_ot / n * 60:.0f}분{delta_txt}", C["coral"], "🔥")
kpi(k[3], "평균 퇴근", hhmm(avg_out), "", f"{late_t:%H:%M} 이후 퇴근 {late_ratio:.0%}", C["plum"], "🕘")
kpi(k[4], "가장 늦은 퇴근", hhmm(latest['퇴근분']), "",
    f"{latest['날짜']:%m/%d} ({latest['요일']})", C["rose"], "🌃")
kpi(k[5], "야근을 영화로", f"{movies:.0f}", "편", "2시간짜리 영화 기준", "#C08B1E", "🎬")


# ─────────────────────────────────────────────────────────────
# 차트 공통
# ─────────────────────────────────────────────────────────────
def base(fig, title, h=340):
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", x=0.02, y=0.96, font=dict(size=15, color=C["ink"])),
        height=h, margin=dict(l=16, r=16, t=56, b=16),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family=FONT, color=C["ink"], size=12),
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
        hoverlabel=dict(bgcolor="white", font_family=FONT), bargap=0.35,
    )
    fig.update_xaxes(showgrid=False, linecolor=C["line"])
    fig.update_yaxes(gridcolor="#F0F2F6", zeroline=False)
    return fig


def show(fig):
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def time_axis(lo, hi, step=30):
    vals = list(range(int(lo), int(hi) + 1, step))
    return dict(tickvals=vals, ticktext=[hhmm(v) for v in vals], range=[lo, hi])


lo_out = max(0, (d["퇴근분"].min() // 30) * 30 - 30)
hi_out = (d["퇴근분"].max() // 30) * 30 + 60

# ─────────────────────────────────────────────────────────────
# 1행: 월별 · 요일별
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="sec">📈 월별 · 요일별 흐름</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)

m = d.groupby("월").agg(근무=("근무", "sum"), 야근=("야근", "sum"),
                       야근일=("야근", lambda s: int((s > 0).sum())), 일수=("날짜", "count")).reset_index()
m["라벨"] = m["월"].map(lambda s: f"{int(s[5:])}월")
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_bar(x=m["라벨"], y=m["근무"] - m["야근"], name="정규 근무", marker_color=C["teal"],
            hovertemplate="%{x} 정규 %{y:.1f}h<extra></extra>")
fig.add_bar(x=m["라벨"], y=m["야근"], name="야근", marker_color=C["coral"],
            text=m["근무"].map(lambda v: f"총 {v:.0f}h"), textposition="outside",
            hovertemplate="%{x} 야근 %{y:.1f}h<extra></extra>")
fig.add_scatter(x=m["라벨"], y=m["야근일"], name="야근 일수", mode="lines+markers+text",
                line=dict(color=C["plum"], width=3), marker=dict(size=10),
                text=m["야근일"].map(lambda v: f"{v}일"), textposition="top center",
                secondary_y=True, hovertemplate="%{x} 야근 %{y}일<extra></extra>")
fig.update_layout(barmode="stack")
fig.update_yaxes(title_text="근무시간(h)", secondary_y=False, range=[0, m["근무"].max() * 1.25])
fig.update_yaxes(title_text="야근 일수", secondary_y=True, showgrid=False, range=[0, m["야근일"].max() * 1.5])
with c1:
    show(base(fig, "월별 근무시간 & 야근 일수"))

w = (d.groupby("요일").agg(야근=("야근", "sum"), 평균퇴근=("퇴근분", "mean"), 일수=("날짜", "count"))
     .reindex([x for x in WEEKDAYS if x in set(d["요일"])]).reset_index())
fig = make_subplots(specs=[[{"secondary_y": True}]])
colors = [C["coral"] if v == w["야근"].max() else "#9DB4CF" for v in w["야근"]]
fig.add_bar(x=w["요일"], y=w["야근"], name="총 야근시간", marker_color=colors,
            text=w["야근"].map(lambda v: f"{v:.1f}h"), textposition="outside",
            hovertemplate="%{x}요일 야근 %{y:.1f}h<extra></extra>")
fig.add_scatter(x=w["요일"], y=w["평균퇴근"], name="평균 퇴근", mode="lines+markers",
                line=dict(color=C["plum"], width=3, shape="spline"), marker=dict(size=10, symbol="diamond"),
                secondary_y=True, customdata=w["평균퇴근"].map(hhmm),
                hovertemplate="%{x}요일 평균 퇴근 %{customdata}<extra></extra>")
fig.update_yaxes(title_text="야근시간(h)", secondary_y=False, range=[0, w["야근"].max() * 1.3])
fig.update_yaxes(secondary_y=True, showgrid=False, **time_axis(lo_out, hi_out, 60))
with c2:
    show(base(fig, "요일별 야근시간 & 평균 퇴근시각"))

# ─────────────────────────────────────────────────────────────
# 2행: 시간대 분포 · 도넛 · 원형
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="sec">🍩 퇴근 패턴</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1.4, 1, 1])

edges = list(range(int(lo_out), int(hi_out) + 1, 30))
labels = [f"{hhmm(a)}~{hhmm(b)}" for a, b in zip(edges[:-1], edges[1:])]
cnt = pd.cut(d["퇴근분"], bins=edges, right=False, labels=labels).value_counts().reindex(labels).fillna(0)
grad = ["#B8E0D2", "#8ECAE6", "#2A9D8F", "#E9C46A", "#F4A261", "#F4845F", "#E05A6D", "#9B2C4B"]
fig = go.Figure(go.Bar(x=cnt.index, y=cnt.values,
                       marker_color=[grad[min(i, len(grad) - 1)] for i in range(len(cnt))],
                       text=[f"{int(v)}일" if v else "" for v in cnt.values], textposition="outside",
                       hovertemplate="%{x}<br>%{y}일<extra></extra>"))
fig.update_yaxes(range=[0, max(cnt.max(), 1) * 1.3], title_text="일수")
with c1:
    show(base(fig, "퇴근 시간대 분포 (30분 단위)"))

fig = go.Figure(go.Pie(labels=["정규 근무", "야근"], values=[tot_work - tot_ot, tot_ot], hole=0.62,
                       marker=dict(colors=[C["teal"], C["coral"]], line=dict(color="white", width=3)),
                       textinfo="percent", sort=False,
                       hovertemplate="%{label} %{value:.1f}h<extra></extra>"))
fig.add_annotation(text=f"<b>{tot_ot / tot_work:.0%}</b><br><span style='font-size:12px;color:{C['sub']}'>야근 비중</span>",
                   showarrow=False, font=dict(size=24, color=C["coral"]))
with c2:
    show(base(fig, "근무시간 구성"))

late_n = int(d["늦은퇴근"].sum())
fig = go.Figure(go.Pie(labels=[f"{late_t:%H:%M} 이전", f"{late_t:%H:%M} 이후"], values=[n - late_n, late_n],
                       marker=dict(colors=[C["sky"], C["rose"]], line=dict(color="white", width=3)),
                       textinfo="percent+value", texttemplate="%{percent}<br>%{value}일", sort=False,
                       pull=[0, 0.06], hovertemplate="%{label} 퇴근 %{value}일<extra></extra>"))
with c3:
    show(base(fig, "늦은 퇴근 비율"))

# ─────────────────────────────────────────────────────────────
# 3행: 일별 추이 · 주별 · 캘린더 히트맵
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="sec">🗓️ 날짜별로 보기</div>', unsafe_allow_html=True)

fig = go.Figure()
fig.add_hrect(y0=cfg["late"], y1=hi_out, fillcolor=C["rose"], opacity=0.06, line_width=0)
fig.add_hline(y=cfg["late"], line=dict(color=C["rose"], dash="dot"),
              annotation_text=f"늦은 퇴근 {late_t:%H:%M}", annotation_position="top left",
              annotation_font_color=C["rose"])
fig.add_scatter(x=pd.to_datetime(d["날짜"]), y=d["퇴근분"], mode="lines+markers", name="퇴근",
                line=dict(color=C["plum"], width=2.5, shape="spline", smoothing=0.6),
                marker=dict(size=8, color=[C["rose"] if x else C["plum"] for x in d["늦은퇴근"]],
                            line=dict(color="white", width=1.5)),
                customdata=d[["퇴근", "요일"]],
                hovertemplate="%{x|%m/%d} (%{customdata[1]})<br>퇴근 %{customdata[0]}<extra></extra>")
roll = d["퇴근분"].rolling(5, min_periods=1).mean()
fig.add_scatter(x=pd.to_datetime(d["날짜"]), y=roll, mode="lines", name="5일 평균",
                line=dict(color=C["sand"], width=3), hoverinfo="skip")
fig.update_yaxes(**time_axis(lo_out, hi_out, 30))
fig.update_xaxes(tickformat="%m/%d")
show(base(fig, "매일 퇴근시각 (빨간 점 = 늦은 퇴근)", h=330))

c1, c2 = st.columns([1, 1.15])
wk = d.groupby("주").agg(야근=("야근", "sum"), 일수=("날짜", "count")).reset_index()
wk["라벨"] = wk["주"].map(lambda x: f"{x:%m/%d}주")
fig = go.Figure(go.Bar(x=wk["라벨"], y=wk["야근"],
                       marker=dict(color=wk["야근"], colorscale=[[0, "#C9C2FF"], [1, C["plum"]]]),
                       text=wk["야근"].map(lambda v: f"{v:.1f}"), textposition="outside",
                       customdata=wk["일수"],
                       hovertemplate="%{x} · %{customdata}일<br>야근 %{y:.1f}h<extra></extra>"))
fig.update_yaxes(title_text="야근시간(h)", range=[0, wk["야근"].max() * 1.25])
with c1:
    show(base(fig, "주별 야근시간"))

days_shown = [x for x in WEEKDAYS if x in set(d["요일"])]
piv = d.pivot_table(index="요일", columns="주", values="퇴근분", aggfunc="mean").reindex(days_shown)
txt = d.pivot_table(index="요일", columns="주", values="퇴근", aggfunc="first").reindex(days_shown)
fig = go.Figure(go.Heatmap(
    z=piv.values, x=[f"{c:%m/%d}" for c in piv.columns], y=piv.index,
    text=txt.values, texttemplate="%{text}", textfont=dict(size=10),
    colorscale=[[0, "#E3F4EF"], [0.5, "#FFE8A8"], [1, "#F08A6C"]],
    xgap=4, ygap=4, showscale=False,
    hovertemplate="%{x}주 %{y}요일<br>퇴근 %{text}<extra></extra>"))
fig.update_yaxes(autorange="reversed", showgrid=False)
fig.update_xaxes(title_text="주 시작일(월)", side="bottom")
with c2:
    show(base(fig, "퇴근 캘린더 (진할수록 늦게 퇴근)"))

# ─────────────────────────────────────────────────────────────
# 기록 보기 · 수정
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="sec">📋 기록 보기 · 수정 <span>표에서 바로 고치거나 행을 지울 수 있어요</span></div>',
            unsafe_allow_html=True)
with st.expander("기록 표 열기", expanded=False):
    edit = df_raw.copy()
    edit["날짜"] = pd.to_datetime(edit["날짜"])
    edited = st.data_editor(
        edit, num_rows="dynamic", hide_index=True, width="stretch",
        column_config={
            "날짜": st.column_config.DateColumn("날짜", format="YYYY-MM-DD", required=True),
            "출근": st.column_config.TextColumn("출근 (HH:MM)", help="비우면 기본 출근시각 사용"),
            "퇴근": st.column_config.TextColumn("퇴근 (HH:MM)", required=True),
        },
        key="editor",
    )
    if st.button("수정 내용 저장"):
        st.session_state.df = tidy(edited)
        save(st.session_state.df)
        st.success("저장했어요.")
        st.rerun()
