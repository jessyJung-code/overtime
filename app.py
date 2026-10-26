"""
🌙 퇴근 대시보드 (Streamlit) — 여러 사람이 함께 쓰는 버전

실행:  streamlit run app.py

저장 위치
- Streamlit secrets에 Google Sheets 설정이 있으면 → 구글 스프레드시트에 저장 (모든 사람이 같은 데이터를 봄)
- 설정이 없으면 → data/퇴근기록.csv 에 저장 (내 컴퓨터에서 혼자 쓸 때)

열: 이름, 날짜(YYYY-MM-DD), 출근(HH:MM), 퇴근(HH:MM), 입력시각
"""
import datetime as dt
import re
from io import BytesIO
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ─────────────────────────────────────────────────────────────
# 기본 설정
# ─────────────────────────────────────────────────────────────
DATA_PATH = Path(__file__).parent / "data" / "퇴근기록.csv"
SHEET_TAB = "퇴근기록"
COLS = ["이름", "날짜", "출근", "퇴근", "입력시각"]
KST = ZoneInfo("Asia/Seoul")
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]
C = {
    "ink": "#1E2A3B", "sub": "#4F5B6E", "line": "#E6EAF0",
    "teal": "#2A9D8F", "coral": "#F4845F", "sand": "#E9C46A",
    "plum": "#7B6CF6", "sky": "#8ECAE6", "rose": "#E05A6D", "navy": "#264653",
}
PEOPLE_COLORS = ["#7B6CF6", "#2A9D8F", "#F4845F", "#E9C46A", "#264653", "#E05A6D", "#8ECAE6", "#9B5DE5"]
FONT = "Pretendard, 'Noto Sans KR', 'Malgun Gothic', sans-serif"

st.set_page_config(page_title="퇴근 대시보드", page_icon="🌙", layout="wide")

st.markdown(
    """
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css">
<style>
/* 색 기준: 본문은 밝은 바탕 + 진한 글씨, 사이드바는 진한 남색 바탕 + 밝은 글씨.
브라우저/Streamlit이 어두운 모드여도 같은 색이 나오도록 직접 지정 */
:root { --ink:#1E2A3B; --sub:#4F5B6E; --side:#1E2A3B; --side-ink:#F3F6FA; --side-sub:#B9C4D4;
--field:#2C3B52; --field-line:#4A5C78; --accent:#F4845F; }
html, body, [class*="css"], .stApp, button, input, textarea { font-family: Pretendard, 'Noto Sans KR', sans-serif !important; }
.stApp { background: linear-gradient(180deg, #F4F6FB 0%, #FBFCFE 100%); color: var(--ink); color-scheme: light; }
header[data-testid="stHeader"] { background: rgba(244,246,251,.85); }
header[data-testid="stHeader"] * { color: var(--ink) !important; }
.block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1400px; }
/* 본문: 글씨는 모두 진하게 */
[data-testid="stMain"] [data-testid="stMarkdownContainer"],
[data-testid="stMain"] [data-testid="stMarkdownContainer"] *:not(.hero *):not(.kpi *),
[data-testid="stMain"] [data-testid="stWidgetLabel"] *,
[data-testid="stMain"] [data-testid="stCaptionContainer"],
[data-testid="stMain"] [data-testid="stExpander"] summary * { color: var(--ink) !important; }
[data-testid="stMain"] [data-testid="stExpander"] details { background: #FFFFFF; border: 1px solid #D5DBE5; border-radius: 12px; }
[data-testid="stMain"] [data-testid="stExpander"] summary { background: #FFFFFF; }
[data-testid="stMain"] input { background: #FFFFFF !important; color: var(--ink) !important; -webkit-text-fill-color: var(--ink); }
[data-testid="stMain"] [data-baseweb="input"], [data-testid="stMain"] [data-baseweb="base-input"] { background: #FFFFFF !important; border-color: #C5CEDB !important; }
[data-testid="stMain"] .stButton button { background: var(--accent); color: #FFFFFF !important; border: none; font-weight: 700; }
[data-testid="stMain"] .stButton button * { color: #FFFFFF !important; }
/* 사이드바: 진한 바탕 + 밝은 글씨, 입력칸도 진한 칸 + 밝은 글씨로 통일 */
section[data-testid="stSidebar"] { background: var(--side); color-scheme: dark; }
section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] *,
section[data-testid="stSidebar"] [data-testid="stWidgetLabel"] *,
section[data-testid="stSidebar"] [data-testid="stExpander"] summary *,
section[data-testid="stSidebar"] [data-testid="stTooltipIcon"] * { color: var(--side-ink) !important; }
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] * { color: var(--side-sub) !important; }
section[data-testid="stSidebar"] [data-testid="stExpander"] details,
section[data-testid="stSidebar"] [data-testid="stForm"] { background: transparent; border: 1px solid var(--field-line); border-radius: 12px; }
section[data-testid="stSidebar"] [data-testid="stExpander"] summary { background: transparent; }
section[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover * { color: #FFD8C9 !important; }
section[data-testid="stSidebar"] [data-baseweb="input"],
section[data-testid="stSidebar"] [data-baseweb="base-input"],
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] [data-testid="stNumberInputContainer"],
section[data-testid="stSidebar"] [data-testid="stNumberInput"] button,
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {
background: var(--field) !important; border-color: var(--field-line) !important; }
section[data-testid="stSidebar"] input, section[data-testid="stSidebar"] textarea,
section[data-testid="stSidebar"] [data-baseweb="select"] *,
section[data-testid="stSidebar"] [data-testid="stNumberInput"] button *,
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * {
color: var(--side-ink) !important; -webkit-text-fill-color: var(--side-ink); }
section[data-testid="stSidebar"] input, section[data-testid="stSidebar"] [data-baseweb="input"] > div,
section[data-testid="stSidebar"] [data-baseweb="base-input"] > div { background: var(--field) !important; }
section[data-testid="stSidebar"] svg { fill: var(--side-ink); color: var(--side-ink); }
section[data-testid="stSidebar"] input::placeholder { color: var(--side-sub) !important; -webkit-text-fill-color: var(--side-sub); }
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button { background: #FFFFFF !important; border: none; }
section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] button * { color: var(--ink) !important; -webkit-text-fill-color: var(--ink); }
section[data-testid="stSidebar"] .stButton button, section[data-testid="stSidebar"] .stDownloadButton button,
section[data-testid="stSidebar"] .stFormSubmitButton button {
background: var(--accent); border: none; font-weight: 700; border-radius: 10px; width: 100%;
}
section[data-testid="stSidebar"] .stButton button *, section[data-testid="stSidebar"] .stDownloadButton button *,
section[data-testid="stSidebar"] .stFormSubmitButton button * { color: #FFFFFF !important; }
.store { font-size: 12px; padding: 6px 10px; border-radius: 8px; background: rgba(255,255,255,.10); color: var(--side-ink); }
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
.kpi .lab { font-size: 13px; color: #4F5B6E; font-weight: 600; }
.kpi .val { font-size: 30px; font-weight: 800; color: var(--c); line-height: 1.25; margin-top: 4px; letter-spacing: -0.5px; }
.kpi .val small { font-size: 15px; font-weight: 700; margin-left: 2px; }
.kpi .sub { font-size: 12px; color: #4F5B6E; margin-top: 4px; }
.kpi .ico { position: absolute; right: 14px; top: 12px; font-size: 22px; opacity: .85; }
.sec { font-size: 18px; font-weight: 800; color: #1E2A3B; margin: 22px 0 6px 2px; }
.sec span { font-size: 13px; color: #4F5B6E; font-weight: 500; margin-left: 8px; }
div[data-testid="stPlotlyChart"] { background: white; border-radius: 18px; border: 1px solid #E6EAF0;
box-shadow: 0 4px 18px rgba(30,42,59,.05); padding: 6px 6px 0 6px; }
</style>
""",
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────
# 값 정리 (구글 시트에서 사람이 직접 고친 값도 읽을 수 있게)
# ─────────────────────────────────────────────────────────────
def to_hhmm(v):
    """'21:05', '21:05:00', '오후 9:05:00', '9:05 PM', 엑셀 시간 등을 'HH:MM'으로 통일"""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, pd.Timestamp):
        v = v.to_pydatetime()
    if isinstance(v, (dt.datetime, dt.time)):
        return v.strftime("%H:%M")
    if isinstance(v, (int, float)):  # 엑셀 시간(하루의 비율)
        m = round(float(v) % 1 * 1440)
        return f"{m // 60:02d}:{m % 60:02d}"
    s = str(v).strip()
    if not s:
        return None
    pm = ("오후" in s) or bool(re.search(r"\bpm\b", s, re.I))
    am = ("오전" in s) or bool(re.search(r"\bam\b", s, re.I))
    s2 = re.sub(r"(오전|오후|am|pm|AM|PM)", "", s).strip()
    mt = re.match(r"^(\d{1,2})\s*[:시]\s*(\d{1,2})", s2) or re.match(r"^(\d{2})(\d{2})$", s2)
    if not mt:
        return None
    h, m = int(mt.group(1)), int(mt.group(2))
    if pm and h < 12:
        h += 12
    if am and h == 12:
        h = 0
    if h > 23 or m > 59:
        return None
    return f"{h:02d}:{m:02d}"


def to_date(v):
    """'2026-09-01', '2026. 9. 1', '2026/9/1', 엑셀 날짜 등을 date로 통일"""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, (pd.Timestamp, dt.datetime)):
        return v.date()
    if isinstance(v, dt.date):
        return v
    s = str(v).strip()
    mt = re.match(r"^(\d{4})\s*[-./년]\s*(\d{1,2})\s*[-./월]\s*(\d{1,2})", s)
    if mt:
        try:
            return dt.date(int(mt.group(1)), int(mt.group(2)), int(mt.group(3)))
        except ValueError:
            return None
    try:
        return pd.to_datetime(s).date()
    except (ValueError, TypeError):
        return None


def norm_col(c) -> str:
    """'퇴근시간', '출근 시각', '성명' 같은 열 이름을 표준 이름으로 통일"""
    c = str(c).strip()
    for key in ("날짜", "출근", "퇴근", "입력시각"):
        if c.startswith(key):
            return key
    if c in ("이름", "성명", "작성자", "name", "Name"):
        return "이름"
    return c


def tidy(df: pd.DataFrame, default_name: str = "") -> pd.DataFrame:
    """열 정리 + 형식 통일 + 같은 사람의 같은 날짜는 마지막 값만 남김"""
    df = df.rename(columns=norm_col)
    df = df.loc[:, ~df.columns.duplicated()].copy()
    for c in COLS:
        if c not in df.columns:
            df[c] = None
    df = df[COLS].copy()
    df["이름"] = df["이름"].map(lambda x: str(x).strip() if x is not None and not pd.isna(x) else "")
    df.loc[df["이름"] == "", "이름"] = default_name
    df["날짜"] = df["날짜"].map(to_date)
    df["출근"] = df["출근"].map(to_hhmm)
    df["퇴근"] = df["퇴근"].map(to_hhmm)
    df["입력시각"] = df["입력시각"].fillna("").astype(str)
    df = df.dropna(subset=["날짜", "퇴근"])
    df = df[df["이름"] != ""]
    df = (df.drop_duplicates(["이름", "날짜"], keep="last")
            .sort_values(["날짜", "이름"]).reset_index(drop=True))
    return df


def to_rows(df: pd.DataFrame) -> list:
    return [[r["이름"], r["날짜"].strftime("%Y-%m-%d"), r["출근"] or "", r["퇴근"], r["입력시각"] or ""]
            for _, r in df.iterrows()]


def read_any(file, default_name: str) -> pd.DataFrame:
    """CSV 또는 엑셀(앞서 만든 엑셀 포함)에서 날짜·퇴근 표를 찾아 읽기"""
    if file.name.lower().endswith(".csv"):
        return tidy(pd.read_csv(file, dtype=str), default_name)
    sheets = pd.read_excel(file, sheet_name=None, header=None)
    for raw in sheets.values():
        for i in range(min(len(raw), 30)):
            row = [norm_col(x) for x in raw.iloc[i].tolist()]
            if "날짜" in row and "퇴근" in row:
                body = raw.iloc[i + 1:].copy()
                body.columns = row
                return tidy(body, default_name)
    raise ValueError("'날짜'와 '퇴근' 열이 있는 표를 찾지 못했어요.")


def now_kst() -> str:
    return dt.datetime.now(KST).strftime("%Y-%m-%d %H:%M:%S")


# ─────────────────────────────────────────────────────────────
# 저장소: 구글 시트(공유) 또는 CSV(로컬)
# ─────────────────────────────────────────────────────────────
def secret(key, default=None):
    try:
        return st.secrets[key] if key in st.secrets else default
    except Exception:  # secrets 파일이 없을 때
        return default


SHEET_URL = secret("sheet_url")
SA_INFO = secret("gcp_service_account")
USE_SHEET = bool(SHEET_URL and SA_INFO)
ADMIN_PW = secret("admin_password")


@st.cache_resource(show_spinner=False)
def get_ws():
    import gspread
    gc = gspread.service_account_from_dict(dict(SA_INFO))
    sh = gc.open_by_url(SHEET_URL)
    try:
        ws = sh.worksheet(SHEET_TAB)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=SHEET_TAB, rows=2000, cols=len(COLS))
    if not any(ws.row_values(1)):
        ws.update(values=[COLS], range_name="A1", value_input_option="RAW")
    return ws


def _read_raw() -> pd.DataFrame:
    if USE_SHEET:
        vals = get_ws().get_all_values()
        if len(vals) <= 1:
            return pd.DataFrame(columns=COLS)
        width = len(vals[0])
        return pd.DataFrame([r + [""] * (width - len(r)) for r in vals[1:]], columns=vals[0])
    if DATA_PATH.exists():
        return pd.read_csv(DATA_PATH, dtype=str, keep_default_na=False)
    return pd.DataFrame(columns=COLS)


@st.cache_data(ttl=20, show_spinner=False)
def load_records() -> pd.DataFrame:
    """모든 사람의 기록 (20초마다 새로 읽음)"""
    return tidy(_read_raw(), "이름없음")


def _write_csv(df: pd.DataFrame):
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(to_rows(df), columns=COLS).to_csv(DATA_PATH, index=False, encoding="utf-8-sig")


def upsert(new: pd.DataFrame):
    """새 기록 저장. 같은 이름+날짜가 있으면 그 줄만 고치고, 없으면 맨 아래에 추가.
    (다른 사람이 동시에 입력해도 서로의 기록을 덮어쓰지 않도록 전체를 다시 쓰지 않음)"""
    new = tidy(new)
    if new.empty:
        return 0
    if USE_SHEET:
        ws = get_ws()
        vals = ws.get_all_values()
        hdr = [norm_col(h) for h in (vals[0] if vals else COLS)]
        ni, di = hdr.index("이름"), hdr.index("날짜")
        where = {}
        for i, r in enumerate(vals[1:], start=2):
            if len(r) > max(ni, di):
                where[(r[ni].strip(), to_date(r[di]))] = i
        appends = []
        for row in to_rows(new):
            key = (row[0], to_date(row[1]))
            if key in where:
                ws.update(values=[row], range_name=f"A{where[key]}:E{where[key]}", value_input_option="RAW")
            else:
                appends.append(row)
        if appends:
            ws.append_rows(appends, value_input_option="RAW")
    else:
        cur = tidy(_read_raw(), "이름없음")
        _write_csv(tidy(pd.concat([cur, new], ignore_index=True)))
    load_records.clear()
    return len(new)


def apply_edits(original: pd.DataFrame, edited: pd.DataFrame):
    """표에서 고친 내용 반영: 지운 줄은 지우고 고친 줄은 덮어씀.
    저장 직전에 최신 데이터를 다시 읽어서, 그 사이 다른 사람이 넣은 기록은 그대로 둠."""
    edited = tidy(edited)
    key = lambda df: set(zip(df["이름"], df["날짜"]))
    removed = key(original) - key(edited)
    latest = tidy(_read_raw(), "이름없음")
    latest = latest[[k not in removed for k in zip(latest["이름"], latest["날짜"])]]
    result = tidy(pd.concat([latest, edited], ignore_index=True))
    if USE_SHEET:
        ws = get_ws()
        ws.clear()
        ws.update(values=[COLS] + to_rows(result), range_name="A1", value_input_option="RAW")
    else:
        _write_csv(result)
    load_records.clear()


# ─────────────────────────────────────────────────────────────
# 계산
# ─────────────────────────────────────────────────────────────
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
    out = d[["이름", "날짜", "요일", "출근", "퇴근", "근무", "야근"]].copy()
    out.columns = ["이름", "날짜", "요일", "출근", "퇴근", "근무시간(h)", "야근시간(h)"]
    out[["근무시간(h)", "야근시간(h)"]] = out[["근무시간(h)", "야근시간(h)"]].round(2)
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as xw:
        out.to_excel(xw, index=False, sheet_name="퇴근기록")
        ws = xw.sheets["퇴근기록"]
        for col, w in zip("ABCDEFG", [10, 13, 6, 8, 8, 12, 12]):
            ws.column_dimensions[col].width = w
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────
# 사이드바: 입력
# ─────────────────────────────────────────────────────────────
try:
    records = load_records()
    load_error = None
except Exception as ex:  # noqa: BLE001
    records, load_error = pd.DataFrame(columns=COLS), ex

names = sorted(records["이름"].unique().tolist())

if "my_name" not in st.session_state:
    st.session_state.my_name = st.query_params.get("name", "")

with st.sidebar:
    st.markdown("## 🌙 퇴근 기록")
    if USE_SHEET:
        st.markdown('<div class="store">☁️ 구글 시트에 저장 중 · 모든 사람이 같은 기록을 봐요</div>',
                    unsafe_allow_html=True)
    else:
        st.markdown('<div class="store">💾 이 컴퓨터의 CSV 파일에 저장 중 (혼자 쓰는 모드)</div>',
                    unsafe_allow_html=True)

    with st.expander("⚙️ 기준 설정", expanded=False):
        start_t = st.time_input("기본 출근", dt.time(9, 30), step=600)
        lunch = st.number_input("점심(시간)", 0.0, 3.0, 1.0, 0.5)
        regular = st.number_input("정규근무(시간)", 1.0, 12.0, 8.0, 0.5)
        late_t = st.time_input("늦은 퇴근 기준", dt.time(21, 0), step=600)
    cfg = {"start": start_t.strftime("%H:%M"), "lunch": lunch, "regular": regular,
           "late": late_t.hour * 60 + late_t.minute}

    st.markdown("### ➕ 기록 추가")
    with st.form("add", clear_on_submit=False):
        my_name = st.text_input("이름", key="my_name", placeholder="예: 김세연",
                                help="같은 이름으로 입력한 기록끼리 모여요.")
        day = st.date_input("날짜", dt.datetime.now(KST).date())
        c1, c2 = st.columns(2)
        in_t = c1.time_input("출근", start_t, step=300)
        out_t = c2.time_input("퇴근", dt.time(21, 0), step=300)
        submitted = st.form_submit_button("저장하기")
    if submitted:
        if not my_name.strip():
            st.error("이름을 입력해 주세요.")
        else:
            try:
                upsert(pd.DataFrame([{"이름": my_name.strip(), "날짜": day, "출근": in_t.strftime("%H:%M"),
                                      "퇴근": out_t.strftime("%H:%M"), "입력시각": now_kst()}]))
                st.session_state.view = my_name.strip()
                st.toast(f"{my_name.strip()} · {day:%m/%d} 퇴근 {out_t:%H:%M} 저장했어요 ✅")
                st.rerun()
            except Exception as ex:  # noqa: BLE001
                st.error(f"저장하지 못했어요: {ex}")

    st.markdown("### 👀 보기")
    options = ["전체"] + names
    if st.session_state.get("view") not in options:
        st.session_state.view = names[0] if len(names) == 1 else "전체"
    view = st.selectbox("누구의 기록을 볼까요?", options, key="view")
    if st.button("🔄 최신 기록 불러오기"):
        load_records.clear()
        st.rerun()

    st.markdown("### 📂 데이터")
    up = st.file_uploader("엑셀/CSV 불러오기", type=["xlsx", "csv"],
                          help="'날짜', '퇴근' 열이 있으면 됩니다. '이름' 열이 없으면 위에 입력한 이름으로 저장돼요.")
    if up is not None and st.session_state.get("_uploaded") != up.file_id:
        try:
            loaded = read_any(up, (st.session_state.my_name or "").strip())
            if loaded.empty:
                st.warning("이름을 먼저 입력하거나, 파일에 '이름' 열을 넣어 주세요.")
            else:
                st.caption(f"{loaded['이름'].nunique()}명 · {len(loaded)}건을 찾았어요. "
                           "같은 이름·날짜는 새 값으로 바뀌어요.")
                if st.button("기록에 추가하기"):
                    loaded["입력시각"] = now_kst()
                    upsert(loaded)
                    st.session_state._uploaded = up.file_id
                    st.rerun()
        except Exception as ex:  # noqa: BLE001
            st.error(str(ex))

if load_error is not None:
    st.error(f"기록을 불러오지 못했어요. 구글 시트 설정(secrets)과 공유 권한을 확인해 주세요.\n\n{load_error}")
    st.stop()

if records.empty:
    st.info("아직 기록이 없어요. 왼쪽에서 이름과 퇴근시간을 넣고 저장해 보세요.")
    st.stop()

all_d = compute(records, cfg)
d = all_d if view == "전체" else all_d[all_d["이름"] == view].reset_index(drop=True)
team_view = view == "전체" and all_d["이름"].nunique() > 1

with st.sidebar:
    st.download_button("⬇️ 엑셀로 내려받기", to_excel(d), file_name=f"퇴근기록_{view}.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.caption(f"{view} · {len(d)}건 · {d['날짜'].min():%Y.%m.%d} ~ {d['날짜'].max():%Y.%m.%d}")

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
who = f"{all_d['이름'].nunique()}명 전체" if view == "전체" else view
badge = "우리 팀 퇴근 칭호" if team_view else f"{view}님의 퇴근 칭호"
st.markdown(
    f"""<div class="hero"><h1>퇴근 대시보드</h1>
<p>{who} · {d['날짜'].min():%Y.%m.%d} – {d['날짜'].max():%Y.%m.%d} · 기록 {n}건 ·
정시퇴근 기준 {hhmm(mins(cfg['start']) + (cfg['regular'] + cfg['lunch']) * 60)}</p>
<div class="badge">{badge}: {title}</div></div>""",
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
if team_view:
    kpi(k[0], "참여 인원", all_d["이름"].nunique(), "명", f"기록 {n}건 · 칼퇴 {kal}건", C["navy"], "👥")
else:
    kpi(k[0], "근무일수", n, "일", f"칼퇴 {kal}일", C["navy"], "📅")
kpi(k[1], "총 근무시간", f"{tot_work:,.1f}", "h", f"1건 평균 {tot_work / n:.1f}h", C["teal"], "💼")
kpi(k[2], "총 야근시간", f"{tot_ot:,.1f}", "h", f"1건 평균 {tot_ot / n * 60:.0f}분{delta_txt}", C["coral"], "🔥")
kpi(k[3], "평균 퇴근", hhmm(avg_out), "", f"{late_t:%H:%M} 이후 퇴근 {late_ratio:.0%}", C["plum"], "🕘")
kpi(k[4], "가장 늦은 퇴근", hhmm(latest['퇴근분']), "",
    f"{latest['날짜']:%m/%d} ({latest['요일']})" + (f" · {latest['이름']}" if team_view else ""), C["rose"], "🌃")
kpi(k[5], "야근을 영화로", f"{movies:.0f}", "편", "2시간짜리 영화 기준", "#C08B1E", "🎬")


# ─────────────────────────────────────────────────────────────
# 차트 공통
# ─────────────────────────────────────────────────────────────
def base(fig, title, h=340):
    fig.update_layout(
        title=dict(text=f"<b>{title}</b>", x=0.02, y=0.96, font=dict(size=15, color=C["ink"])),
        height=h, margin=dict(l=56, r=24, t=56, b=40), autosize=True,
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family=FONT, color=C["ink"], size=12),
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
        legend_font=dict(color=C["ink"]),
        hoverlabel=dict(bgcolor="white", font_family=FONT, font_color=C["ink"]), bargap=0.35,
    )
    axis = dict(tickfont=dict(color=C["sub"], size=12), title_font=dict(color=C["sub"]))
    fig.update_xaxes(showgrid=False, linecolor="#C9D1DC", automargin=True, **axis)
    fig.update_yaxes(gridcolor="#EDF0F5", zeroline=False, automargin=True, **axis)
    return fig


def show(fig):
    # theme=None: Streamlit의 어두운 테마 색이 차트 글씨를 흐리게 덮어쓰지 않도록 함
    st.plotly_chart(fig, theme=None, width="stretch", config={"displayModeBar": False})


def time_axis(lo, hi, step=30):
    vals = list(range(int(lo), int(hi) + 1, step))
    return dict(tickvals=vals, ticktext=[hhmm(v) for v in vals], range=[lo, hi])


lo_out = max(0, (d["퇴근분"].min() // 30) * 30 - 30)
hi_out = (d["퇴근분"].max() // 30) * 30 + 60
person_color = {nm: PEOPLE_COLORS[i % len(PEOPLE_COLORS)] for i, nm in enumerate(sorted(all_d["이름"].unique()))}

# ─────────────────────────────────────────────────────────────
# 사람별 비교 (전체 보기 + 2명 이상일 때)
# ─────────────────────────────────────────────────────────────
if team_view:
    st.markdown('<div class="sec">👥 사람별 비교</div>', unsafe_allow_html=True)
    p = (d.groupby("이름").agg(건수=("날짜", "count"), 평균야근=("야근", "mean"), 평균퇴근=("퇴근분", "mean"),
                              늦은퇴근=("늦은퇴근", "mean"))
         .sort_values("평균야근", ascending=False).reset_index())
    c1, c2 = st.columns([1.3, 1])
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=p["이름"], y=p["평균야근"] * 60, name="하루 평균 야근(분)",
                marker_color=[person_color[x] for x in p["이름"]],
                text=(p["평균야근"] * 60).map(lambda v: f"{v:.0f}분"), textposition="outside",
                customdata=p["건수"], hovertemplate="%{x} · %{customdata}건<br>평균 야근 %{y:.0f}분<extra></extra>")
    fig.add_scatter(x=p["이름"], y=p["평균퇴근"], name="평균 퇴근", mode="markers",
                    marker=dict(size=14, symbol="diamond", color=C["ink"], line=dict(color="white", width=2)),
                    secondary_y=True, customdata=p["평균퇴근"].map(hhmm),
                    hovertemplate="%{x} 평균 퇴근 %{customdata}<extra></extra>")
    fig.update_yaxes(title_text="하루 평균 야근(분)", secondary_y=False, range=[0, max(p["평균야근"].max() * 60, 1) * 1.3])
    fig.update_yaxes(secondary_y=True, showgrid=False, **time_axis(lo_out, hi_out, 60))
    with c1:
        show(base(fig, "사람별 하루 평균 야근 & 평균 퇴근"))
    fig = go.Figure(go.Bar(y=p["이름"], x=p["늦은퇴근"], orientation="h",
                           marker_color=[person_color[x] for x in p["이름"]],
                           text=p["늦은퇴근"].map(lambda v: f"{v:.0%}"), textposition="outside",
                           hovertemplate="%{y} · %{x:.0%}<extra></extra>"))
    fig.update_xaxes(tickformat=".0%", range=[0, 1.15], gridcolor="#F0F2F6", showgrid=True)
    fig.update_yaxes(autorange="reversed")
    with c2:
        show(base(fig, f"{late_t:%H:%M} 이후 퇴근 비율"))

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
fig.add_scatter(x=m["라벨"], y=m["야근일"], name="야근 일수" if not team_view else "야근 건수",
                mode="lines+markers+text", line=dict(color=C["plum"], width=3), marker=dict(size=10),
                text=m["야근일"].map(lambda v: f"{v}{'건' if team_view else '일'}"), textposition="top center",
                secondary_y=True, hovertemplate="%{x} 야근 %{y}<extra></extra>")
fig.update_layout(barmode="stack")
fig.update_yaxes(title_text="근무시간(h)", secondary_y=False, range=[0, m["근무"].max() * 1.25])
fig.update_yaxes(title_text="야근 일수" if not team_view else "야근 건수", secondary_y=True, showgrid=False,
                 range=[0, max(m["야근일"].max(), 1) * 1.5])
with c1:
    show(base(fig, "월별 근무시간 & 야근 " + ("건수" if team_view else "일수")))

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
fig.update_yaxes(title_text="야근시간(h)", secondary_y=False, range=[0, max(w["야근"].max(), 0.1) * 1.3])
fig.update_yaxes(secondary_y=True, showgrid=False, **time_axis(lo_out, hi_out, 60))
with c2:
    show(base(fig, "요일별 야근시간 & 평균 퇴근시각"))

# ─────────────────────────────────────────────────────────────
# 2행: 시간대 분포 · 도넛 · 원형
# ─────────────────────────────────────────────────────────────
unit = "건" if team_view else "일"
st.markdown('<div class="sec">🍩 퇴근 패턴</div>', unsafe_allow_html=True)
c1, c2, c3 = st.columns([1.4, 1, 1])

edges = list(range(int(lo_out), int(hi_out) + 1, 30))
labels = [f"{hhmm(a)}~{hhmm(b)}" for a, b in zip(edges[:-1], edges[1:])]
cnt = pd.cut(d["퇴근분"], bins=edges, right=False, labels=labels).value_counts().reindex(labels).fillna(0)
grad = ["#B8E0D2", "#8ECAE6", "#2A9D8F", "#E9C46A", "#F4A261", "#F4845F", "#E05A6D", "#9B2C4B"]
fig = go.Figure(go.Bar(x=cnt.index, y=cnt.values,
                       marker_color=[grad[min(i, len(grad) - 1)] for i in range(len(cnt))],
                       text=[f"{int(v)}{unit}" if v else "" for v in cnt.values], textposition="outside",
                       hovertemplate="%{x}<br>%{y}" + unit + "<extra></extra>"))
fig.update_yaxes(range=[0, max(cnt.max(), 1) * 1.3], title_text=f"{unit}수")
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
                       textinfo="percent+value", texttemplate="%{percent}<br>%{value}" + unit, sort=False,
                       pull=[0, 0.06], hovertemplate="%{label} 퇴근 %{value}" + unit + "<extra></extra>"))
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
if team_view:  # 사람마다 선 하나씩
    for nm, g in d.groupby("이름"):
        fig.add_scatter(x=pd.to_datetime(g["날짜"]), y=g["퇴근분"], mode="lines+markers", name=nm,
                        line=dict(color=person_color[nm], width=2.2, shape="spline", smoothing=0.6),
                        marker=dict(size=7, line=dict(color="white", width=1.2)),
                        customdata=g[["퇴근", "요일"]],
                        hovertemplate=nm + " · %{x|%m/%d} (%{customdata[1]})<br>퇴근 %{customdata[0]}<extra></extra>")
    chart_title = "사람별 매일 퇴근시각"
else:
    fig.add_scatter(x=pd.to_datetime(d["날짜"]), y=d["퇴근분"], mode="lines+markers", name="퇴근",
                    line=dict(color=C["plum"], width=2.5, shape="spline", smoothing=0.6),
                    marker=dict(size=8, color=[C["rose"] if x else C["plum"] for x in d["늦은퇴근"]],
                                line=dict(color="white", width=1.5)),
                    customdata=d[["퇴근", "요일"]],
                    hovertemplate="%{x|%m/%d} (%{customdata[1]})<br>퇴근 %{customdata[0]}<extra></extra>")
    roll = d["퇴근분"].rolling(5, min_periods=1).mean()
    fig.add_scatter(x=pd.to_datetime(d["날짜"]), y=roll, mode="lines", name="5일 평균",
                    line=dict(color=C["sand"], width=3), hoverinfo="skip")
    chart_title = "매일 퇴근시각 (빨간 점 = 늦은 퇴근)"
fig.update_yaxes(**time_axis(lo_out, hi_out, 30))
fig.update_xaxes(tickformat="%m/%d")
show(base(fig, chart_title, h=330))

c1, c2 = st.columns([1, 1.15])
wk = d.groupby("주").agg(야근=("야근", "sum"), 일수=("날짜", "count")).reset_index()
wk["라벨"] = wk["주"].map(lambda x: f"{x:%m/%d}주")
fig = go.Figure(go.Bar(x=wk["라벨"], y=wk["야근"],
                       marker=dict(color=wk["야근"], colorscale=[[0, "#C9C2FF"], [1, C["plum"]]]),
                       text=wk["야근"].map(lambda v: f"{v:.1f}"), textposition="outside",
                       customdata=wk["일수"],
                       hovertemplate="%{x} · %{customdata}" + unit + "<br>야근 %{y:.1f}h<extra></extra>"))
fig.update_yaxes(title_text="야근시간(h)", range=[0, max(wk["야근"].max(), 0.1) * 1.25])
with c1:
    show(base(fig, "주별 야근시간"))

days_shown = [x for x in WEEKDAYS if x in set(d["요일"])]
piv = d.pivot_table(index="요일", columns="주", values="퇴근분", aggfunc="mean").reindex(days_shown)
txt = piv.apply(lambda col: col.map(lambda v: hhmm(v) if pd.notna(v) else ""))
fig = go.Figure(go.Heatmap(
    z=piv.values, x=[f"{c:%m/%d}" for c in piv.columns], y=piv.index,
    text=txt.values, texttemplate="%{text}", textfont=dict(size=10),
    colorscale=[[0, "#E3F4EF"], [0.5, "#FFE8A8"], [1, "#F08A6C"]],
    xgap=4, ygap=4, showscale=False,
    hovertemplate="%{x}주 %{y}요일<br>퇴근 %{text}<extra></extra>"))
fig.update_yaxes(autorange="reversed", showgrid=False)
fig.update_xaxes(side="bottom")
with c2:
    show(base(fig, "퇴근 캘린더 (가로: 주 시작일 · 진할수록 늦게 퇴근" + (", 평균)" if team_view else ")")))

# ─────────────────────────────────────────────────────────────
# 기록 보기 · 수정
# ─────────────────────────────────────────────────────────────
st.markdown('<div class="sec">📋 기록 보기 · 수정 <span>표에서 고치거나 행을 지운 뒤 저장하세요</span></div>',
            unsafe_allow_html=True)
with st.expander("기록 표 열기", expanded=False):
    base_df = records if view == "전체" else records[records["이름"] == view].reset_index(drop=True)
    unlocked = True
    if ADMIN_PW:
        pw = st.text_input("수정·삭제는 관리자 비밀번호가 필요해요", type="password", key="pw")
        unlocked = pw == ADMIN_PW
        if pw and not unlocked:
            st.error("비밀번호가 맞지 않아요.")
    edit = base_df[["이름", "날짜", "출근", "퇴근", "입력시각"]].copy()
    edit["날짜"] = pd.to_datetime(edit["날짜"])
    edited = st.data_editor(
        edit, num_rows="dynamic" if unlocked else "fixed", disabled=not unlocked,
        hide_index=True, width="stretch",
        column_config={
            "이름": st.column_config.TextColumn("이름", required=True),
            "날짜": st.column_config.DateColumn("날짜", format="YYYY-MM-DD", required=True),
            "출근": st.column_config.TextColumn("출근 (HH:MM)", help="비우면 기본 출근시각 사용"),
            "퇴근": st.column_config.TextColumn("퇴근 (HH:MM)", required=True),
            "입력시각": st.column_config.TextColumn("입력시각", disabled=True),
        },
        key="editor",
    )
    if unlocked and st.button("수정 내용 저장"):
        try:
            apply_edits(base_df, edited)
            st.success("저장했어요. 다른 사람 화면에도 곧 반영돼요.")
            st.rerun()
        except Exception as ex:  # noqa: BLE001
            st.error(f"저장하지 못했어요: {ex}")
