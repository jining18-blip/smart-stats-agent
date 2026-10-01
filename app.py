# -*- coding: utf-8 -*-
"""
================================================================
  실험 데이터 자동 통계 분석 시스템  (스마트 통계 에이전트)
================================================================
실행: streamlit run app.py
"""
import io, copy, re
from collections import Counter
import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from lxml import etree
from scipy import stats
from scipy.stats import studentized_range
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.multicomp import pairwise_tukeyhsd
import scikit_posthocs as sp
from sklearn.linear_model import LogisticRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import (RandomForestClassifier, RandomForestRegressor,
                              ExtraTreesClassifier, ExtraTreesRegressor,
                              GradientBoostingClassifier, GradientBoostingRegressor,
                              HistGradientBoostingClassifier, HistGradientBoostingRegressor,
                              AdaBoostClassifier, AdaBoostRegressor)
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
from sklearn.svm import SVC, SVR
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor
from sklearn.naive_bayes import GaussianNB
from sklearn.pipeline import Pipeline
from sklearn.inspection import permutation_importance
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, r2_score
try:
    import anthropic
    _HAS_ANTHROPIC = True
except Exception:
    _HAS_ANTHROPIC = False
try:
    import requests as _requests
    _HAS_REQUESTS = True
except Exception:
    _HAS_REQUESTS = False
try:
    import docx as _docx_probe  # 설치 여부 확인용
    _ = _docx_probe
    _HAS_DOCX = True
except Exception:
    _HAS_DOCX = False

_KOREAN_FONT = None


def set_korean_font():
    """그래프 한글 폰트를 잡는다. (윈도우·맥·리눅스 서버 배포 모두 대응)

    리눅스 서버(클라우드 배포)에서는 한글 폰트를 나중에 설치하는 경우가 많아
    matplotlib 캐시에 폰트가 없을 수 있다. 그때는 폰트 파일을 직접 등록하고
    캐시를 다시 만들어 본다. 이걸 안 하면 그래프 글자가 전부 □로 나온다.
    """
    global _KOREAN_FONT
    cands = ["Malgun Gothic", "AppleGothic", "NanumGothic", "NanumBarunGothic",
             "Noto Sans CJK KR", "Noto Sans KR", "UnDotum"]
    names = {f.name for f in fm.fontManager.ttflist}
    if not names & set(cands):
        import glob as _glob
        for _pat in ("/usr/share/fonts/**/Nanum*.tt[fc]",
                     "/usr/share/fonts/**/NotoSansCJK*.tt[fc]",
                     "/usr/share/fonts/**/NotoSansKR*.tt[fc]"):
            for _p in _glob.glob(_pat, recursive=True):
                try:
                    fm.fontManager.addfont(_p)
                except Exception:
                    pass
        names = {f.name for f in fm.fontManager.ttflist}
        if not names & set(cands):
            try:                      # 마지막 수단: 폰트 캐시를 통째로 다시 만든다
                fm._load_fontmanager(try_read_cache=False)
                names = {f.name for f in fm.fontManager.ttflist}
            except Exception:
                pass
    for c in cands:
        if c in names:
            plt.rcParams["font.family"] = c
            _KOREAN_FONT = c
            break
    plt.rcParams["axes.unicode_minus"] = False
set_korean_font()

# ================================================================ 공통 그래프 디자인
# 원클릭 분석의 차분한 블루 톤을 앱 전체 그래프의 기본값으로 사용한다.
# 개별 그래프에서 별도 색을 지정하지 않아도 같은 분위기로 보이도록 rcParams에 반영한다.
from cycler import cycler as _cycler
_SMART_CHART_BLUE = ["#DCE9F5", "#C2D9EE", "#A3C4E2", "#82ACD3",
                     "#6291C2", "#4576AB", "#2D5A8E", "#1F4569"]
_SMART_CHART_RED = "#C96767"
_SMART_CHART_RED_LIGHT = "#E9B5B5"
_SMART_CHART_NEUTRAL = "#E3E9EF"
plt.rcParams.update({
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
    "axes.edgecolor": "#AEBECD",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.labelcolor": "#43576A",
    "axes.titlecolor": "#23394D",
    "axes.titleweight": "bold",
    "axes.titlesize": 11.5,
    "axes.labelsize": 9.5,
    "xtick.color": "#5B6F82",
    "ytick.color": "#5B6F82",
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "grid.color": "#DCE7F0",
    "grid.linewidth": 0.8,
    "grid.alpha": 0.9,
    "legend.frameon": False,
    "legend.fontsize": 8,
    "axes.prop_cycle": _cycler(color=["#4576AB", "#6F9FC8", "#91B8D8", "#2D5A8E",
                                       "#B2CEE5", "#5A86B3", "#789FC3", "#355F8A"]),
})

st.set_page_config(page_title="스마트 통계 에이전트", page_icon="📊", layout="wide")

# 화면 글꼴: Pretendard(한글·영문·숫자 모양이 고른 무료 글꼴). 불러오지 못하는 망에서는
# 맑은 고딕 등 시스템 글꼴로 자연스럽게 대체된다. 아이콘 글꼴(Material Symbols)은 건드리지 않는다.
# (그래프·한글/워드 보고서의 글꼴은 '출력 및 그래프 설정'을 그대로 따른다)
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css');
html, body, .stApp, .stMarkdown, [data-testid="stMarkdownContainer"], [data-testid="stWidgetLabel"],
[data-testid="stSidebar"], button, input, textarea, select, label, p, li, td, th,
h1, h2, h3, h4, h5, h6, [data-baseweb="select"], [data-baseweb="tab"], [data-testid="stMetric"],
[data-testid="stExpander"] summary, [data-testid="stToast"], [data-testid="stAlert"] {
    font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont,
                 "Apple SD Gothic Neo", "Malgun Gothic", "맑은 고딕", "Noto Sans KR", sans-serif !important;
}
[data-testid="stIconMaterial"], .material-symbols-rounded, [class*="material-symbols"],
span[data-testid="stIconMaterial"] {
    font-family: "Material Symbols Rounded" !important;
}
code, pre, kbd, samp, .stCode, [data-testid="stCode"] * {
    font-family: "Source Code Pro", Consolas, "D2Coding", monospace !important;
}
/* 브라우저 저장소(로그인 유지·API 키 기억)용 보이지 않는 부품이 화면에 흰 줄·빈 칸을 만들지 않게 한다.
   display:none 대신 크기만 0으로 줄여, 부품 안의 스크립트는 그대로 실행되게 둔다. */
.stElementContainer:has(iframe[title*="streamlit_js_eval"]) {
    position:absolute !important; width:0 !important; height:0 !important; overflow:hidden !important;
    margin:0 !important; padding:0 !important; opacity:0 !important; pointer-events:none !important;
}
/* 스타일만 담은 보이지 않는 칸과 떠 있는 AI 버튼 자리가 본문 맨 위에 빈 간격을 쌓아
   상단 배너가 왼쪽 로고보다 아래로 밀리지 않게 한다(스타일은 숨겨도 그대로 적용된다). */
[data-testid="stMain"] [data-testid="stElementContainer"]:has(> [data-testid="stMarkdown"] [data-testid="stMarkdownContainer"] > style:only-child) {
    display:none !important;
}
[data-testid="stMain"] [data-testid="stLayoutWrapper"]:has(> .st-key-gai_dock) {margin-bottom:-1rem;}
</style>
""", unsafe_allow_html=True)

# ================================================================ V1 배포/테마 설정
def _v1_env(name, default=""):
    import os
    try:
        v = st.secrets.get(name, None)
        if v is not None:
            return str(v).strip()
    except Exception:
        pass
    return str(os.environ.get(name, default)).strip()

# Version 2 주소 — secrets에 V2_APP_URL을 넣으면 그 값이 우선한다.
V2_APP_URL = _v1_env("V2_APP_URL", "https://smart-stats-agent-v2.streamlit.app/")
# 문의처 — 사이드바·로그인 화면·오류 안내·사용설명서에 함께 표시된다.
CONTACT_NAME = "경상북도농업기술원 영양고추연구소 이효진"
CONTACT_EMAIL = "hyo99@korea.kr"

# 아래 CSS는 V1의 배경/사이드바 분위기만 바꿉니다.
# 통계 그래프와 Excel 차트 디자인은 기존 검증 버전을 그대로 사용합니다.
st.markdown("""<style>
.stApp {
 background-image:url("data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI0ODAiIGhlaWdodD0iMzIwIiB2aWV3Qm94PSIwIDAgNDgwIDMyMCI+CjxnIGZpbGw9Im5vbmUiIHN0cm9rZT0iIzVFOEY2OSIgc3Ryb2tlLXdpZHRoPSIyLjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgb3BhY2l0eT0iMC4zMCI+CiA8cGF0aCBkPSJNNDcwIDIyIEMzOTUgNDIgMzM3IDg4IDI5MiAxNTAgQzI2MCAxOTQgMjI2IDIyNiAxNzYgMjUwIi8+CiA8cGF0aCBkPSJNMzk0IDUyIEMzOTEgODggMzc3IDExNiAzNTAgMTQwIi8+CiA8cGF0aCBkPSJNMzM3IDk1IEMzMjUgNjggMzA1IDQ4IDI3OCAzOCIvPgogPHBhdGggZD0iTTMwNiAxMzMgQzI5MCAxNjQgMjY3IDE4MSAyMzYgMTkwIi8+CiA8cGF0aCBkPSJNMjcyIDE3NCBDMjUyIDE0NyAyMjcgMTMyIDE5OCAxMjgiLz4KIDxwYXRoIGQ9Ik0yMzAgMjE5IEMyMDQgMjEwIDE4MSAyMTIgMTU3IDIyNSIvPgo8L2c+CjxnIGZpbGw9IiM4RkJFOTgiIG9wYWNpdHk9IjAuMTYiPgogPGVsbGlwc2UgY3g9IjM5NCIgY3k9Ijc4IiByeD0iMTUiIHJ5PSIzMyIgdHJhbnNmb3JtPSJyb3RhdGUoMjYgMzk0IDc4KSIvPgogPGVsbGlwc2UgY3g9IjMwNyIgY3k9IjUyIiByeD0iMTQiIHJ5PSIzMSIgdHJhbnNmb3JtPSJyb3RhdGUoLTQ3IDMwNyA1MikiLz4KIDxlbGxpcHNlIGN4PSIyODQiIGN5PSIxNjEiIHJ4PSIxNiIgcnk9IjM2IiB0cmFuc2Zvcm09InJvdGF0ZSg1NCAyODQgMTYxKSIvPgogPGVsbGlwc2UgY3g9IjIyNiIgY3k9IjE0MSIgcng9IjE1IiByeT0iMzQiIHRyYW5zZm9ybT0icm90YXRlKC01MiAyMjYgMTQxKSIvPgogPGVsbGlwc2UgY3g9IjE5MyIgY3k9IjIxOSIgcng9IjE0IiByeT0iMzIiIHRyYW5zZm9ybT0icm90YXRlKDc2IDE5MyAyMTkpIi8+CjwvZz48L3N2Zz4="),linear-gradient(135deg,#F8FCF8 0%,#F1F8F2 48%,#F9FCF9 100%);
 background-repeat:no-repeat,no-repeat;
 background-position:right 1.2rem top 4.2rem,center;
 background-size:min(32vw,390px) auto,cover;
 background-attachment:fixed,fixed;
}
[data-testid="stAppViewContainer"] > .main {background:transparent;}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#EDF7EF 0%,#F8FBF8 100%); border-right:1px solid #D9E9DC;}
[data-testid="stHeader"] {background:rgba(248,252,248,.86);}
</style>""", unsafe_allow_html=True)



# ================================================================ 공통 화면/엑셀 표 디자인
# 모든 분석 화면이 같은 "스마트 블루" 표 디자인을 쓰도록 한 곳에서 관리한다.
# 나중에 색을 바꾸고 싶으면 아래 팔레트만 수정하면 앱 전체에 반영된다.
_ST_DATAFRAME = st.dataframe
_SMART_BLUE = {
    "navy": "#244A73", "header": "#3D6F9F", "mid": "#9EC5E5",
    "light": "#EAF3FA", "pale": "#F7FBFF", "line": "#C9DCEB",
}

# Streamlit 기본 표 주변도 카드처럼 보이게 한다. 셀 색은 pandas Styler가 담당한다.
st.markdown("""
<style>
[data-testid="stDataFrame"] {border:1px solid #d7e5f1; border-radius:10px; overflow:hidden;}
[data-testid="stDataEditor"] {border:1px solid #d7e5f1; border-radius:10px; overflow:hidden;}
</style>
""", unsafe_allow_html=True)


def _smart_excluded_gradient_col(name):
    """값의 크기가 '좋고 나쁨'을 뜻하지 않는 통계 열은 값 기반 그라데이션에서 제외."""
    s = str(name).lower().replace(" ", "")
    keys = ("p-value", "pvalue", "p값", "p(", "유의", "통계량", "t값", "t통계",
            "f값", "f통계", "df", "자유도", "ci", "신뢰구간", "표준오차", "se(",
            "표준편차", "sd(", "검정", "판정", "반복", "번호", "순번")
    return any(k in s for k in keys)


def smart_table(data, *args, **kwargs):
    """st.dataframe 호환 래퍼.

    - 원클릭 분석의 푸른 계열 분위기를 모든 표에 통일한다.
    - 일반 결과표에는 값 크기에 따른 자동 색상(그라데이션)을 넣지 않는다.
      숫자가 크다는 이유만으로 더 중요하거나 더 좋은 값처럼 보이는 오해를 막기 위함이다.
    - 머리행과 아주 옅은 행 구분만 유지한다.
    - 이미 Styler가 넘어온 경우(결측치 강조 등) 기존 의미 기반 스타일은 보존한다.
    """
    try:
        is_styler = data.__class__.__name__ == "Styler"
        if is_styler:
            sty = data
            try:
                sty = sty.set_table_styles([
                    {"selector": "th", "props": [("background-color", _SMART_BLUE["header"]),
                                                    ("color", "white"), ("font-weight", "700"),
                                                    ("border", f"1px solid {_SMART_BLUE['line']}")]},
                    {"selector": "td", "props": [("border", f"1px solid {_SMART_BLUE['line']}")]},
                ], overwrite=False)
            except Exception:
                pass
            return _ST_DATAFRAME(sty, *args, **kwargs)

        if isinstance(data, pd.DataFrame):
            shown = sup_display(data)
            sty = shown.style
            try:
                # 연한 행 구분 + 파란 머리행
                def _band_rows(row):
                    bg = _SMART_BLUE["pale"] if (row.name % 2 == 0 if isinstance(row.name, (int, np.integer)) else False) else "white"
                    return [f"background-color:{bg}" for _ in row]
                sty = sty.apply(_band_rows, axis=1)
            except Exception:
                pass

            try:
                sty = sty.set_table_styles([
                    {"selector": "th", "props": [("background-color", _SMART_BLUE["header"]),
                                                    ("color", "white"), ("font-weight", "700"),
                                                    ("border", f"1px solid {_SMART_BLUE['line']}")]},
                    {"selector": "td", "props": [("border", f"1px solid {_SMART_BLUE['line']}")]},
                ], overwrite=False)
            except Exception:
                pass
            return _ST_DATAFRAME(sty, *args, **kwargs)
    except Exception:
        pass
    return _ST_DATAFRAME(data, *args, **kwargs)


def dataframe_to_styled_xlsx(df, title="스마트 통계 에이전트 분석 결과", sheet_name="분석결과"):
    """화면의 스마트 블루 디자인을 실제 .xlsx에도 반영한다."""
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
    from openpyxl.formatting.rule import ColorScaleRule
    from openpyxl.utils import get_column_letter
    import datetime as _dt

    frame = sup_display(df.copy() if isinstance(df, pd.DataFrame) else pd.DataFrame(df))
    wb = Workbook()
    ws = wb.active
    ws.title = str(sheet_name)[:31] or "분석결과"
    ws.sheet_properties.tabColor = "3D6F9F"
    ws.sheet_view.showGridLines = False
    ncol = max(len(frame.columns), 1)

    # 제목/메타
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncol)
    c = ws.cell(1, 1, title)
    c.fill = PatternFill("solid", fgColor="244A73")
    c.font = Font(color="FFFFFF", bold=True, size=14)
    c.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[1].height = 27
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ncol)
    c2 = ws.cell(2, 1, f"생성일: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    c2.font = Font(color="5B6F82", size=9, italic=True)
    c2.fill = PatternFill("solid", fgColor="F7FBFF")
    c2.alignment = Alignment(horizontal="left")

    header_row = 4
    thin = Side(style="thin", color="C9DCEB")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    for j, col in enumerate(frame.columns, 1):
        cell = ws.cell(header_row, j, str(col))
        cell.fill = PatternFill("solid", fgColor="3D6F9F")
        cell.font = Font(color="FFFFFF", bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = border
    ws.row_dimensions[header_row].height = 24

    for i, row in enumerate(frame.itertuples(index=False, name=None), header_row + 1):
        for j, val in enumerate(row, 1):
            cell = ws.cell(i, j)
            if pd.isna(val):
                cell.value = None
            elif isinstance(val, (np.integer,)):
                cell.value = int(val)
            elif isinstance(val, (np.floating,)):
                cell.value = float(val)
            else:
                cell.value = val
            cell.border = border
            cell.alignment = Alignment(vertical="center")
            if (i - header_row) % 2 == 0:
                cell.fill = PatternFill("solid", fgColor="F7FBFF")
            if isinstance(cell.value, (int, float)) and not isinstance(cell.value, bool):
                cell.number_format = '#,##0.###'

    if len(frame) > 0 and len(frame.columns) > 0:
        # Excel 내장 TableStyle은 Office 테마에 따라 색이 달라져 앱 화면과 어긋날 수 있다.
        # 필터 기능만 유지하고 셀 색은 전부 스마트 블루 팔레트로 직접 지정한다.
        ref = f"A{header_row}:{get_column_letter(len(frame.columns))}{header_row + len(frame)}"
        ws.auto_filter.ref = ref

    ws.freeze_panes = f"A{header_row + 1}"
    ws.auto_filter.ref = (f"A{header_row}:{get_column_letter(len(frame.columns))}{header_row + len(frame)}"
                          if len(frame.columns) and len(frame) else None)
    for j, col in enumerate(frame.columns, 1):
        vals = [str(col)] + ["" if pd.isna(v) else str(v) for v in frame[col].head(200)]
        width = min(max(max((len(v) for v in vals), default=8) + 3, 10), 34)
        ws.column_dimensions[get_column_letter(j)].width = width

    bio = io.BytesIO()
    wb.save(bio)
    return bio.getvalue()

MM = 7200 / 25.4          # 1mm = 283.46 HWPUNIT
BODY_W = int(150 * MM)    # 본문 폭 150mm

# ---------------------------------------------------------------- 통계 헬퍼
def compact_letter_display(means_sorted, not_sig_pairs):
    """유의성 문자(a,b,c) 생성. Piepho(2004) insert-and-absorb 방식.
    means_sorted: 평균 내림차순 그룹 리스트, not_sig_pairs: 유의차 없는 쌍(frozenset)들.
    같은 문자를 공유하면 두 처리 간 유의차가 없음을 뜻한다(ab, bc 등 중간 그룹 지원)."""
    def diff(a, b):  # 유의차 있음 = 다른 문자여야 함
        return a != b and frozenset({a, b}) not in not_sig_pairs
    items = list(means_sorted)
    if not items:
        return {}
    cols = [set(items)]  # 모든 그룹을 한 열에서 시작
    changed = True
    while changed:
        changed = False
        for col in list(cols):
            broke = False
            members = list(col)
            for i in range(len(members)):
                for j in range(i + 1, len(members)):
                    a, b = members[i], members[j]
                    if diff(a, b):  # 유의차 있는 쌍이 한 열에 → 열을 쪼갬
                        cols.remove(col)
                        c1 = set(col); c1.discard(a)
                        c2 = set(col); c2.discard(b)
                        cols.append(c1); cols.append(c2)
                        changed = True; broke = True
                        break
                if broke: break
            if broke: break
    cols = [c for c in cols if c]
    # 다른 열의 부분집합인 열 흡수(제거)
    keep = [c for i, c in enumerate(cols)
            if not any(i != j and c < o for j, o in enumerate(cols))]
    uniq = []
    for c in keep:
        if c not in uniq: uniq.append(c)
    uniq.sort(key=lambda col: min(items.index(g) for g in col))
    letters = {g: "" for g in items}
    for i, col in enumerate(uniq):
        for g in col: letters[g] += chr(97 + i)
    return {g: "".join(sorted(v)) for g, v in letters.items()}

def _formula_design_matrix(model, newdata):
    """적합된 수식 모형의 설계행렬 규칙을 새 자료에 그대로 적용한다.

    statsmodels 0.14는 ``data.design_info``(patsy)를, 0.15부터는 ``data.model_spec``
    (patsy DesignInfo 또는 formulaic ModelSpec)을 쓰므로 버전별로 나눠 처리한다.
    열 순서는 항상 model.params 순서에 맞춘다.
    """
    mdata = model.model.data
    spec = getattr(mdata, "design_info", None)
    if spec is None:
        spec = getattr(mdata, "model_spec", None)
    if spec is None:
        raise RuntimeError("이 statsmodels 버전에서 모형의 설계 정보를 찾을 수 없습니다.")
    if hasattr(spec, "get_model_matrix"):              # formulaic ModelSpec
        mat = pd.DataFrame(spec.get_model_matrix(newdata))
    else:                                               # patsy DesignInfo
        from patsy import build_design_matrices
        mat = build_design_matrices([spec], newdata, return_type="dataframe")[0]
    names = list(getattr(model.model, "exog_names", None) or mat.columns)
    if list(mat.columns) != names:
        missing = [c for c in names if c not in mat.columns]
        if missing:
            raise RuntimeError("설계행렬 열이 모형 계수와 맞지 않습니다: " + ", ".join(map(str, missing)))
        mat = mat[names]
    return mat


def _model_emmeans(model, data, treatment_col):
    """적합된 statsmodels 모형에서 처리별 추정주변평균(EMM)과 설계벡터를 계산한다.

    블록이 포함된 RCBD/불균형 자료에서는 원자료 평균이 아니라 모형이 보정한 평균을
    사용해야 ANOVA와 사후검정이 같은 오차구조를 공유한다.
    """
    levels = list(pd.unique(data[treatment_col].dropna()))
    rows, means = {}, {}
    params = np.asarray(model.params, dtype=float)
    for level in levels:
        tmp = data.copy()
        tmp[treatment_col] = level
        mat = _formula_design_matrix(model, tmp)
        xbar = np.asarray(mat, dtype=float).mean(axis=0)
        rows[level] = xbar
        means[level] = float(xbar @ params)
    return levels, means, rows


def _simulate_dunnett_adjustment(t_values, corr, df_resid, alpha=0.05,
                                 n_sim=60000, seed=20260726):
    """모형 기반 대조들의 상관을 반영한 Dunnett 단일단계 보정.

    다변량 t 분포를 몬테카를로로 재현해 최대 |t| 분포를 구한다. 난괴법·불균형
    자료에서도 같은 적합모형의 공분산을 사용하므로 블록을 무시한 원자료 Dunnett보다
    ANOVA와 일관된 결과를 낸다.
    """
    tv = np.asarray(t_values, dtype=float)
    if tv.size == 0:
        return np.array([], dtype=float), np.nan
    if tv.size == 1:
        p = 2 * stats.t.sf(abs(tv[0]), df_resid)
        crit = stats.t.ppf(1 - alpha / 2, df_resid)
        return np.array([float(p)]), float(crit)
    corr = np.asarray(corr, dtype=float)
    corr = (corr + corr.T) / 2
    np.fill_diagonal(corr, 1.0)
    # 수치 오차로 음의 고유값이 생기면 아주 작게 보정
    vals, vecs = np.linalg.eigh(corr)
    vals = np.clip(vals, 1e-10, None)
    corr = (vecs * vals) @ vecs.T
    d = np.sqrt(np.diag(corr))
    corr = corr / np.outer(d, d)
    rng = np.random.default_rng(seed)
    z = rng.multivariate_normal(np.zeros(tv.size), corr, size=int(n_sim))
    chi = rng.chisquare(float(df_resid), size=int(n_sim))
    sims = z / np.sqrt(chi[:, None] / float(df_resid))
    max_abs = np.max(np.abs(sims), axis=1)
    p_adj = np.array([(1 + np.count_nonzero(max_abs >= abs(t))) / (len(max_abs) + 1)
                      for t in tv], dtype=float)
    crit = float(np.quantile(max_abs, 1 - alpha))
    return p_adj, crit


def posthoc_from_model(model, data, treatment_col, method, control=None,
                       alpha=0.05, random_state=20260726):
    """적합모형 기반 사후검정.

    반환값: {not_sig, table, means}. Dunnett는 대조구 비교만 table에 담고 CLD는 만들지 않는다.
    Tukey/Bonferroni/Duncan은 모든 처리쌍을 모형의 잔차 공분산으로 비교한다.
    """
    levels, emmeans, xrows = _model_emmeans(model, data, treatment_col)
    covb = np.asarray(model.cov_params(), dtype=float)
    dfe = float(model.df_resid)
    k = len(levels)
    rows = []
    not_sig = set()

    def contrast(a, b):
        c = np.asarray(xrows[a]) - np.asarray(xrows[b])
        diff = float(c @ np.asarray(model.params, dtype=float))
        var = float(c @ covb @ c)
        se = float(np.sqrt(max(var, 0.0)))
        tval = diff / se if se > 0 else (np.inf if diff else 0.0)
        p_raw = float(2 * stats.t.sf(abs(tval), dfe)) if np.isfinite(tval) else 0.0
        return c, diff, se, tval, p_raw

    if method.startswith("던넷") or method.startswith("Dunnett"):
        if control not in levels:
            _match = next((g for g in levels if str(g) == str(control)), None)
            control = _match if _match is not None else (levels[0] if levels else None)
        others = [g for g in levels if g != control]
        if control is None or not others:
            return {"not_sig": set(), "table": pd.DataFrame(), "means": emmeans,
                    "control": control, "method": method}
        contrasts, vals = [], []
        for g in others:
            c, diff, se, tval, p_raw = contrast(g, control)
            contrasts.append(c)
            vals.append((g, diff, se, tval, p_raw))
        cmat = np.vstack(contrasts)
        ccov = cmat @ covb @ cmat.T
        ses = np.sqrt(np.clip(np.diag(ccov), 0, None))
        denom = np.outer(ses, ses)
        corr = np.divide(ccov, denom, out=np.eye(len(others)), where=denom > 0)
        p_adj, crit = _simulate_dunnett_adjustment(
            [v[3] for v in vals], corr, dfe, alpha=alpha, seed=random_state)
        for i, (g, diff, se, tval, p_raw) in enumerate(vals):
            lo = diff - crit * se if np.isfinite(crit) else np.nan
            hi = diff + crit * se if np.isfinite(crit) else np.nan
            padj = float(p_adj[i])
            if padj >= alpha:
                not_sig.add(frozenset({control, g}))
            rows.append({
                "대조구": control, "처리구": g,
                "대조구 평균(보정)": emmeans[control], "처리 평균(보정)": emmeans[g],
                "평균 차이": diff, "t 통계량": tval,
                "p(동시보정)": padj, "95% 동시CI 하한": lo, "95% 동시CI 상한": hi,
                "판정": "유의(*)" if padj < alpha else "n.s.",
            })
        return {"not_sig": not_sig, "table": pd.DataFrame(rows), "means": emmeans,
                "control": control, "method": method, "critical": crit}

    pair_data = []
    ordered = sorted(levels, key=lambda g: emmeans[g], reverse=True)
    m = max(k * (k - 1) // 2, 1)
    for i in range(k):
        for j in range(i + 1, k):
            a, b = levels[i], levels[j]
            c, diff, se, tval, p_raw = contrast(a, b)
            if method == "Tukey HSD":
                q = abs(tval) * np.sqrt(2)
                p_adj = float(studentized_range.sf(q, k, dfe))
                significant = p_adj < alpha
                crit = float(studentized_range.ppf(1 - alpha, k, dfe) / np.sqrt(2))
            elif method == "던컨(Duncan)":
                ia, ib = ordered.index(a), ordered.index(b)
                rng_size = abs(ia - ib) + 1
                alpha_range = 1 - (1 - alpha) ** max(rng_size - 1, 1)
                q = abs(tval) * np.sqrt(2)
                qcrit = float(studentized_range.ppf(1 - alpha_range, rng_size, dfe))
                significant = q > qcrit
                p_adj = float(studentized_range.sf(q, rng_size, dfe))
                crit = qcrit / np.sqrt(2)
            else:  # Bonferroni
                p_adj = min(float(p_raw) * m, 1.0)
                significant = p_adj < alpha
                crit = float(stats.t.ppf(1 - alpha / (2 * m), dfe))
            if not significant:
                not_sig.add(frozenset({a, b}))
            pair_data.append({
                "그룹1": a, "그룹2": b, "평균차": diff, "표준오차": se,
                "t 통계량": tval, "p(보정)": p_adj,
                "95% 하한": diff - crit * se, "95% 상한": diff + crit * se,
                "판정": "유의(*)" if significant else "n.s.",
            })
    return {"not_sig": not_sig, "table": pd.DataFrame(pair_data),
            "means": emmeans, "method": method}


def posthoc_not_sig(data, group_col, value_col, method, alpha=0.05,
                    model=None, control=None):
    """하위호환용 래퍼. model이 주어지면 RCBD/불균형을 반영한 모형 기반 비교를 사용한다."""
    if model is not None:
        return posthoc_from_model(model, data, group_col, method,
                                  control=control, alpha=alpha)["not_sig"]
    not_sig = set()
    if method == "Tukey HSD":
        res = pairwise_tukeyhsd(data[value_col], data[group_col])
        for row in res._results_table.data[1:]:
            if not row[-1]:
                not_sig.add(frozenset({row[0], row[1]}))
    elif method == "던컨(Duncan)":
        groups = data.groupby(group_col)[value_col]
        means = groups.mean().sort_values(ascending=False)
        counts = groups.count()
        k, n_all = len(means), len(data)
        ssw = sum(((groups.get_group(g) - groups.get_group(g).mean()) ** 2).sum()
                  for g in means.index)
        dfe = n_all - k
        mse = ssw / dfe
        nh = k / sum(1 / counts[g] for g in means.index)
        se = np.sqrt(mse / nh)
        order = means.index.tolist()
        for i in range(k):
            for j in range(i + 1, k):
                rng_size = j - i + 1
                alpha_range = 1 - (1 - alpha) ** (rng_size - 1)
                rp = studentized_range.ppf(1 - alpha_range, rng_size, dfe)
                if abs(means[order[i]] - means[order[j]]) <= rp * se:
                    not_sig.add(frozenset({order[i], order[j]}))
    elif method.startswith("던넷") or method.startswith("Dunnett"):
        ctrl = control if control is not None else st.session_state.get("dunnett_ctrl")
        groups = data.groupby(group_col)[value_col]
        names = list(groups.groups.keys())
        if ctrl not in names:
            ctrl = names[0]
        try:
            from scipy.stats import dunnett as _dunnett
            others = [g for g in names if g != ctrl]
            res = _dunnett(*[groups.get_group(g).values for g in others],
                           control=groups.get_group(ctrl).values)
            for g, p in zip(others, np.atleast_1d(res.pvalue)):
                if p >= alpha:
                    not_sig.add(frozenset({ctrl, g}))
        except Exception as ex:
            st.warning(f"던넷 검정을 수행하지 못했습니다: {str(ex)[:80]}")
    else:
        pmat = sp.posthoc_ttest(data, val_col=value_col, group_col=group_col,
                               p_adjust="bonferroni")
        for a in pmat.index:
            for b in pmat.columns:
                if a != b and pmat.loc[a, b] >= alpha:
                    not_sig.add(frozenset({a, b}))
    return not_sig

_SUP_MAP = {"a": "ᵃ", "b": "ᵇ", "c": "ᶜ", "d": "ᵈ", "e": "ᵉ", "f": "ᶠ",
            "g": "ᵍ", "h": "ʰ", "i": "ⁱ", "j": "ʲ", "k": "ᵏ", "l": "ˡ",
            "m": "ᵐ", "n": "ⁿ", "*": "*"}

def sup_text(s):
    """'607.6^a' → '607.6ᵃ' (유니코드 위첨자). 문서 생성이 실패했을 때의 안전망이자
    화면·CSV 표시용 공통 변환기. '^'가 화면이나 문서에 그대로 남지 않게 한다."""
    t = str(s)
    if "^" not in t:
        return s
    base, _, sup = t.partition("^")
    if not sup or any(ch not in _SUP_MAP for ch in sup):
        return s          # 'm^2' 처럼 유의성 문자가 아닌 경우는 건드리지 않는다
    return base + "".join(_SUP_MAP[ch] for ch in sup)

def sup_display(df):
    """화면 표시용: '607.6^a' → '607.6ᵃ' (문서 저장 시엔 ^ 그대로 유지)"""
    try:
        out = df.copy()
    except Exception:
        return df
    for c in out.columns:
        # pandas 3.x는 문자열 열의 dtype이 object가 아니라 str이라, dtype 비교 대신
        # '숫자·날짜가 아니면 훑는다'로 두어야 버전이 올라가도 계속 동작한다.
        try:
            if (pd.api.types.is_numeric_dtype(out[c])
                    or pd.api.types.is_datetime64_any_dtype(out[c])):
                continue
        except Exception:
            pass
        try:
            out[c] = out[c].map(lambda v: sup_text(v) if isinstance(v, str) and "^" in v else v)
        except Exception:
            pass
    out.columns = [sup_text(c) if isinstance(c, str) else c for c in out.columns]
    return out

# ---------------------------------------------------------------- 오류 도우미
def error_help(err, context="", key="err"):
    """오류가 났을 때 (1) 앱 안에서 AI에게 바로 물어보고 답을 화면에 띄우고,
    (2) 구글·ChatGPT 링크도 함께 제공한다.

    스트림릿이 기본으로 붙여주는 구글/ChatGPT 링크는 '검색창에 붙여넣기'까지만 해 준다.
    (ChatGPT 쪽이 자동 전송을 막아서 예전처럼 바로 답이 뜨지 않는다.)
    그래서 앱 안에서 바로 답을 받는 버튼을 따로 만든다.
    """
    import urllib.parse as _up, traceback as _tb
    msg = (f"{type(err).__name__}: {err}" if isinstance(err, BaseException) else str(err))
    trace = ""
    if isinstance(err, BaseException):
        try:
            trace = "".join(_tb.format_exception(type(err), err, err.__traceback__))
        except Exception:
            trace = ""
    prompt = ("파이썬 Streamlit 앱에서 아래 오류가 났습니다. "
              "원인을 한국어로 쉽게 설명하고, 사용자가 바로 할 수 있는 해결 방법을 "
              "1·2·3 단계로 알려주세요.\n\n[오류]\n" + msg
              + (f"\n\n[상황]\n{context}" if context else "")
              + (f"\n\n[상세]\n{trace[-1500:]}" if trace else ""))
    with st.container(border=True):
        st.markdown("###### 🆘 이 오류, 도움받기")
        c1, c2, c3 = st.columns([1.6, 1, 1])
        _ans_key = f"errans_{key}"
        if c1.button("🤖 앱 안에서 바로 물어보기", key=f"errai_{key}", width="stretch",
                     help="AI 도우미에서 연결한 API 키를 사용합니다. 답이 이 화면에 바로 나옵니다."):
            if not st.session_state.get("api_key"):
                st.session_state[_ans_key] = ("⚠️ **🧠 AI 도우미 → AI 연결 설정**에서 API 키를 먼저 연결해 주세요.")
            else:
                try:
                    with st.spinner("AI가 오류를 살펴보는 중..."):
                        st.session_state[_ans_key] = ai_call(
                            prompt, st.session_state.get("api_key"),
                            st.session_state.get("ai_model_g"), max_tokens=900)
                except Exception as _ex:
                    st.session_state[_ans_key] = f"⚠️ AI 호출 실패: {_ex}"
        c2.link_button("🔎 구글 검색",
                       "https://www.google.com/search?q=" + _up.quote_plus(msg),
                       width="stretch")
        c3.link_button("💬 ChatGPT",
                       "https://chatgpt.com/?hints=search&q=" + _up.quote_plus(prompt[:1800]),
                       width="stretch")
        if st.session_state.get(_ans_key):
            st.markdown(st.session_state[_ans_key])
            st.caption("※ AI 답변은 참고용입니다.")
        st.caption(f"📮 해결이 안 되면 이 화면을 캡처해 **{CONTACT_EMAIL}** ({CONTACT_NAME})로 보내 주세요.")


def _install_error_helper():
    """스트림릿이 잡아 주는 '예기치 못한 오류' 아래에도 도움받기 상자를 붙인다."""
    try:
        from streamlit import error_util as _eu
    except Exception:
        return
    if getattr(_eu, "_smart_agent_patched", False):
        return
    _orig = _eu.handle_uncaught_app_exception

    def _patched(ex):
        # 세션 복원이 버튼 키를 건드리면 스트림릿이 막는다. 그 키를 기억해 두고
        # 세션에서 빼 두면 다음 실행부터는 같은 오류가 나지 않는다.
        try:
            if type(ex).__name__ == "StreamlitValueAssignmentNotAllowedError":
                import re as _re_k
                _m = _re_k.search(r"key[`'\s]{0,3}'?([^'`]+)'", str(ex))
                if _m:
                    _deny = set(st.session_state.get("_pin_deny", set()))
                    _deny.add(_m.group(1))
                    st.session_state["_pin_deny"] = _deny
                    st.session_state.pop(_m.group(1), None)
        except Exception:
            pass
        try:
            _orig(ex)
        except Exception:
            try: st.error(f"⚠️ {type(ex).__name__}: {ex}")
            except Exception: pass
        try:
            error_help(ex, context="앱 실행 중 예기치 못한 오류", key="uncaught")
        except Exception:
            pass

    _eu.handle_uncaught_app_exception = _patched
    _eu._smart_agent_patched = True


_install_error_helper()


def _quiet_pin_warnings():
    """화면 선택을 붙잡아 두는 기능(_pin_sync)은 위젯 값을 세션에 다시 써 넣는다. 이때 스트림릿이
    '기본값과 세션값이 둘 다 있다'는 경고를 서버 기록에 매번 남기는데, 동작에는 문제가 없고
    기록만 지저분해져 진짜 오류를 찾기 어렵게 하므로 이 경고 한 종류만 거른다."""
    import logging

    class _PinFilter(logging.Filter):
        def filter(self, record):
            return "was created with a default value but also had its value set via the Session State API" \
                not in str(record.getMessage())

    for _name in ("streamlit.elements.lib.policies", "streamlit"):
        _lg = logging.getLogger(_name)
        if not any(f.__class__.__name__ == "_PinFilter" for f in _lg.filters):
            _lg.addFilter(_PinFilter())


_quiet_pin_warnings()


def strip_md(text):
    """AI가 만든 마크다운 기호(**, ##, - 등)를 문서용 평문으로 정리"""
    import re as _re
    out = []
    for ln in str(text).split("\n"):
        t = ln.rstrip()
        # 제목(#, ##, ###) → 앞 기호 제거
        m = _re.match(r"^\s*#{1,6}\s*(.*)$", t)
        if m: t = m.group(1)
        # 굵게/기울임 제거
        t = _re.sub(r"\*\*(.+?)\*\*", r"\1", t)
        t = _re.sub(r"__(.+?)__", r"\1", t)
        t = _re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"\1", t)
        t = _re.sub(r"`(.+?)`", r"\1", t)
        # 마크다운 불릿 → 보고서 기호. AI가 앞에 공백을 넣어 오는 경우가 많은데
        # 그대로 두면 '    - ' 처럼 자꾸 깊어지므로 한 단계('  - ')로 통일한다.
        t = _re.sub(r"^\s*[-*+]\s+", "  - ", t)
        # 표 구분선 제거
        if _re.match(r"^\s*\|?[\s:\-|]+\|?\s*$", t) and "-" in t and t.count("-") > 2:
            continue
        # 빈 줄이 연달아 나오면 문서에서 문단 사이가 크게 벌어져 정렬이 어긋나 보인다
        if not t.strip() and (not out or not out[-1].strip()):
            continue
        out.append(t)
    while out and not out[-1].strip():
        out.pop()
    return "\n".join(out)

from decimal import Decimal, ROUND_HALF_UP

def fmt_p(p, sp=False, digits=4):
    """문장 속 p값 표기: 0.001 미만은 'p<0.001', 그 밖은 'p=0.0123' (논문 표기 관례)."""
    try:
        p = float(p)
    except (TypeError, ValueError):
        return "p=-"
    if not np.isfinite(p):
        return "p=-"
    eq, lt = (" = ", " < ") if sp else ("=", "<")
    return f"p{lt}0.001" if p < 0.001 else f"p{eq}{p:.{digits}f}"


def round_half_up(value, ndigits=0):
    """공통 표시용 반올림. V1은 economic_core에 의존하지 않는다."""
    try:
        q = Decimal("1") if int(ndigits) == 0 else Decimal("1").scaleb(-int(ndigits))
        _out = Decimal(str(value)).quantize(q, rounding=ROUND_HALF_UP)
        return int(_out) if int(ndigits) == 0 else float(_out)
    except Exception:
        _out = round(value, int(ndigits))
        return int(_out) if int(ndigits) == 0 else _out


def validate_repeated_measure_balance(data, subject_col, time_col):
    """개체별 조사시기 집합과 개체×시기 중복을 함께 검사한다."""
    d = data[[subject_col, time_col]].dropna().copy()
    expected = set(d[time_col].unique())
    bad_subjects, duplicate_subjects = [], []
    for subject, group in d.groupby(subject_col):
        if set(group[time_col].unique()) != expected:
            bad_subjects.append(subject)
        if group.duplicated([time_col], keep=False).any():
            duplicate_subjects.append(subject)
    return {
        "ok": not bad_subjects and not duplicate_subjects,
        "expected_times": sorted(expected, key=str),
        "bad_subjects": bad_subjects,
        "duplicate_subjects": duplicate_subjects,
    }


def scale_observed_value_to_10a(value, source_area_a):
    """원자료가 source_area_a 기준일 때 10a 기준으로 환산."""
    area = float(source_area_a)
    if area <= 0:
        raise ValueError("기준 면적은 0보다 커야 합니다.")
    return value * (10.0 / area)


def dataframe_signature(df):
    """세션에 남은 분석 결과가 현재 데이터에서 나온 것인지 확인하는 서명."""
    if df is None:
        return None
    try:
        h = int(pd.util.hash_pandas_object(df, index=True).sum())
    except Exception:
        h = hash((tuple(df.shape), tuple(map(str, df.columns))))
    return (tuple(df.shape), tuple(map(str, df.columns)), h)


def q_ref(col):
    """Patsy 수식에서 열 이름을 안전하게 참조 (작은따옴표·특수문자 포함 대응)"""
    name = str(col).replace("\\", "\\\\").replace("'", "\\'")
    return f"Q('{name}')"

def safe_formula(dep, factors=(), covars=(), interactions=()):
    """ANOVA·회귀·ANCOVA 공통 수식 생성.
    factors: 범주형(C()), covars: 연속형, interactions: [(a, b), ...]"""
    rhs = [f"C({q_ref(f)})" for f in factors if f]
    rhs += [q_ref(c) for c in covars if c]
    rhs += [f"C({q_ref(a)}):C({q_ref(b)})" for a, b in interactions if a and b]
    if not rhs:
        rhs = ["1"]
    return f"{q_ref(dep)} ~ " + " + ".join(rhs)

def clean_columns(df):
    """열 이름 중복·공백 문제를 자동으로 정리 (중복이면 뒤에 _2, _3 붙임)"""
    df = df.copy()
    cols, seen = [], {}
    for c in df.columns:
        name = str(c).strip()
        if name == "" or name.lower().startswith("unnamed"):
            name = "열"
        if name in seen:
            seen[name] += 1
            name = f"{name}_{seen[name]}"
        else:
            seen[name] = 1
        cols.append(name)
    df.columns = cols
    return df

def validate_anova_data(data, group_col, value_col, min_rep=2):
    """분산분석 전 자료가 분석 가능한지 확인. (실행가능여부, 안내메시지들)"""
    msgs = []
    if data.empty:
        return False, ["❌ 분석할 자료가 없습니다. 결측치를 확인하거나 다른 열을 선택하세요."]
    counts = data.groupby(group_col)[value_col].count()
    counts = counts[counts > 0]
    ng = len(counts)
    if ng < 2:
        return False, [f"❌ 처리구가 {ng}개뿐입니다. 분산분석은 **2개 이상**의 처리구가 필요합니다. "
                       "처리구 열을 다시 선택하거나, 결측치로 자료가 빠지지 않았는지 확인하세요."]
    small = counts[counts < min_rep]
    if len(small) == ng:
        return False, [f"❌ 모든 처리구의 반복이 {min_rep}개 미만입니다(각 1개). "
                       "분산분석은 처리구마다 반복이 2개 이상 있어야 오차를 계산할 수 있습니다."]
    if len(small) > 0:
        msgs.append(f"⚠️ 반복이 {min_rep}개 미만인 처리구가 있습니다: "
                    f"{', '.join(f'{k}({v}개)' for k, v in small.items())}. 결과 해석에 주의하세요.")
    if counts.min() < 3:
        msgs.append("ℹ️ 반복이 3개 미만인 처리구는 정규성 검정을 생략합니다.")
    if data[value_col].nunique() == 1:
        msgs.append("⚠️ 측정값이 모두 동일합니다. 처리 간 차이를 검정할 수 없습니다.")
    return True, msgs

def calc_cv_lsd(model, data, group_col, value_col, alpha=0.05):
    """분산분석 모형에서 CV(%)와 LSD를 계산.
    CV(%) = √(오차평균제곱) ÷ 전체평균 × 100
    LSD   = t(α/2, 오차자유도) × √(2×MSE/r)"""
    try:
        aov = sm.stats.anova_lm(model, typ=2)
        mse = aov.loc["Residual", "sum_sq"] / aov.loc["Residual", "df"]
        dfe = aov.loc["Residual", "df"]
        grand = data[value_col].mean()
        cv = np.sqrt(mse) / grand * 100 if grand else np.nan
        counts = data.groupby(group_col)[value_col].count()
        # 반복수가 다르면 조화평균 사용
        r = len(counts) / np.sum(1.0 / counts) if len(counts) else np.nan
        lsd = stats.t.ppf(1 - alpha/2, dfe) * np.sqrt(2 * mse / r) if r and r > 0 else np.nan
        return {"CV": cv, "LSD": lsd, "MSE": mse, "dfe": dfe, "r": r}
    except Exception:
        return {"CV": np.nan, "LSD": np.nan, "MSE": np.nan, "dfe": np.nan, "r": np.nan}

def cv_grade(cv):
    """포장시험 CV% 판정"""
    if np.isnan(cv): return "-"
    # 실제 포장시험에서 CV 1% 미만은 거의 나오지 않는다 — 평균값을 반복마다 복사해 넣은 경우가 많다.
    if cv < 1: return "확인 필요(너무 낮음)"
    if cv < 10: return "매우 우수"
    if cv < 20: return "양호"
    if cv < 30: return "다소 높음"
    return "재검토 필요"

def find_numeric_like(df, min_ratio=0.6):
    """문자로 읽혔지만 사실상 숫자인 열을 찾음 (콤마·단위·공백 포함)"""
    cands = {}
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            continue
        ser = df[c].dropna().astype(str).str.strip()
        if ser.empty:
            continue
        cleaned = (ser.str.replace(",", "", regex=False)
                      .str.replace(r"[^\d.\-]", "", regex=True))
        conv = pd.to_numeric(cleaned, errors="coerce")
        ratio = conv.notna().mean()
        if ratio >= min_ratio:
            cands[c] = round(ratio * 100, 1)
    return cands

def to_numeric_clean(ser):
    """'1,200 kg' → 1200.0 처럼 숫자만 추출"""
    cleaned = (ser.astype(str).str.strip()
                  .str.replace(",", "", regex=False)
                  .str.replace(r"[^\d.\-]", "", regex=True))
    return pd.to_numeric(cleaned, errors="coerce")

def _polish_figure(fig):
    """공통 그래프 마감.

    검은 윤곽선은 '그래프 전체'가 아니라 실제 데이터 요소에만 적용한다.
    - 막대그래프: 막대 자체에만 얇은 검은 선
    - 원형/도넛: 조각 자체에만 얇은 검은 선
    - 선그래프/히트맵/산점도: 검은 외곽 프레임 없음
    단일 계열 막대는 원클릭 보고서와 같은 블루 그라데이션으로 자동 통일한다.
    """
    try:
        from matplotlib.container import BarContainer
        from matplotlib.patches import Wedge
        fig.patch.set_facecolor("white")
        elem_border = bool(st.session_state.get("fig_border", True))
        for ax in fig.axes:
            ax.set_facecolor("white")
            ax.tick_params(colors="#4B5F73", labelsize=9, length=3, direction="out")
            ax.xaxis.label.set_color("#31485E")
            ax.yaxis.label.set_color("#31485E")
            if ax.title:
                ax.title.set_color("#23394D")
                ax.title.set_fontweight("bold")

            # 전체 사각 프레임 금지. 좌·하단 축선만 연하게 유지한다.
            if getattr(ax, "name", "rectilinear") == "rectilinear":
                for side in ("top", "right"):
                    if side in ax.spines:
                        ax.spines[side].set_visible(False)
                for side in ("left", "bottom"):
                    if side in ax.spines:
                        ax.spines[side].set_visible(True)
                        ax.spines[side].set_color("#AEBECD")
                        ax.spines[side].set_linewidth(0.75)

            bars = [c for c in getattr(ax, "containers", []) if isinstance(c, BarContainer)]
            # 단일 계열 막대는 옅은→진한 블루 그라데이션.
            if len(bars) == 1 and len(bars[0].patches) > 1:
                n = len(bars[0].patches)
                grad = ["#BFD7EA", "#93B9D8", "#6F9FC8", "#4F7FAF",
                        "#35658F", "#244A73"]
                for i, p in enumerate(bars[0].patches):
                    idx = round((len(grad)-1) * i / max(n-1, 1))
                    p.set_facecolor(grad[idx])

            # 검은 윤곽선은 '단일 계열의 일반 막대'에만 적용한다.
            # 리커트·누적경영비처럼 여러 계열을 쌓는 그래프까지 각 조각을 검게 두르면
            # 표가 잘게 끊겨 보이므로 해당 그래프는 원래의 흰 구분선을 유지한다.
            if elem_border:
                if len(bars) == 1:
                    for p in bars[0].patches:
                        try:
                            p.set_edgecolor("#111111")
                            p.set_linewidth(0.55)
                        except Exception:
                            pass
                # 원형/도넛 조각 윤곽선.
                for p in ax.patches:
                    if isinstance(p, Wedge):
                        try:
                            p.set_edgecolor("#111111")
                            p.set_linewidth(0.60)
                        except Exception:
                            pass

            lg = ax.get_legend()
            if lg is not None:
                try:
                    lg.get_frame().set_linewidth(0)
                    lg.get_frame().set_facecolor("white")
                except Exception:
                    pass
    except Exception:
        pass
    return fig

def _figure_png(fig, dpi=150):
    """Matplotlib Figure를 화면/다운로드 공용 PNG bytes로 변환한다."""
    _polish_figure(fig)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight", facecolor="white")
    buf.seek(0)
    return buf.getvalue()


def show_plot(fig, max_width=660):
    """그래프를 브라우저 전체 폭으로 억지 확대하지 않고 보고서 크기로 표시한다.

    Streamlit 버전에 따라 st.pyplot의 기본 폭 정책이 달라졌기 때문에, 화면 표시만큼은
    PNG로 고정해 CSS stretch의 영향을 받지 않게 한다. 그래프 가로 설정은 반영하되
    일반 단일 그래프는 660px, 2패널 이상은 최대 920px까지만 표시한다.
    """
    data = _figure_png(fig, dpi=145)
    try:
        fig_w = float(fig.get_figwidth())
    except Exception:
        fig_w = 6.0
    px = int(max(430, min(int(max_width), round(fig_w * 92))))
    st.image(data, width=px)
    return data


def fig_to_png(fig, show=True):
    """그래프를 스마트 블루 스타일로 마감해 PNG로 반환한다."""
    data = _figure_png(fig, dpi=160)
    if show:
        try:
            fig_w = float(fig.get_figwidth())
        except Exception:
            fig_w = 6.0
        # 1패널은 660px, 매우 넓은 다중패널 그림도 920px을 넘기지 않는다.
        cap = 920 if fig_w >= 10 else 660
        px = int(max(430, min(cap, round(fig_w * 92))))
        st.image(data, width=px)
    plt.close(fig)
    return data

def cronbach_alpha(df_items):
    k = df_items.shape[1]
    if k < 2: return np.nan
    item_var = df_items.var(axis=0, ddof=1).sum()
    total_var = df_items.sum(axis=1).var(ddof=1)
    if total_var == 0: return np.nan
    return (k / (k - 1)) * (1 - item_var / total_var)


def likert_cutoffs(scale_max):
    """척도 범위에 맞는 부정/긍정 경계. 5점이면 <=2 / >=4, 7점이면 <=3 / >=5."""
    m = max(int(scale_max), 2)
    center = (m + 1) / 2.0
    neg = int(np.ceil(center) - 1)
    pos = int(np.floor(center) + 1)
    return pos, neg

# ---------------------------------------------------------------- hwpx 스타일
_HH = "http://www.hancom.co.kr/hwpml/2011/head"
_HP = "http://www.hancom.co.kr/hwpml/2011/paragraph"
def _q(t): return f"{{{_HH}}}{t}"
_LANG = {"HANGUL":"hangul","LATIN":"latin","HANJA":"hanja","JAPANESE":"japanese",
         "OTHER":"other","SYMBOL":"symbol","USER":"user"}

def _reg_font(hdr, name):
    ids = {}
    for group in hdr.iter(_q("fontfaces")):
        for ff in group:
            cnt = int(ff.get("fontCnt")); f = etree.SubElement(ff, _q("font"))
            f.set("id", str(cnt)); f.set("face", name); f.set("type", "TTF"); f.set("isEmbedded", "0")
            for ch in ff.find(_q("font")): f.append(copy.deepcopy(ch))
            ff.set("fontCnt", str(cnt+1)); ids[ff.get("lang")] = str(cnt)
        break
    return ids

def _mk_charpr(hdr, cp0, fids, size, bold=False, sup=False, color=None, spacing=None):
    """color: '#0000FF' 같은 글자색 / spacing: 자간(%). 음수면 글자를 좁혀 한 줄에 더 넣는다."""
    cps = next(hdr.iter(_q("charProperties"))); new = copy.deepcopy(cp0); nid = str(len(cps))
    new.set("id", nid); new.set("height", str(int(size*100)))
    if bold: new.set("bold", "1")
    if color: new.set("textColor", color)
    if spacing is not None:
        el = next((c for c in new if c.tag == _q("spacing")), None)
        if el is not None:
            for k in list(el.attrib): el.set(k, str(int(spacing)))
    if sup:   # 위첨자: 작게 + 위로 올림
        # 한글(HWP)에서는 offset 이 '음수일 때 위로' 올라간다. (양수로 주면 아래첨자가 됨 —
        # 실제 한글에서 확인. 일부 문서에는 반대로 적혀 있으니 값을 바꾸지 말 것)
        rel = str(int(st.session_state.get("sup_size", 65)))
        off = str(-abs(int(st.session_state.get("sup_off", 35))))
        for tag, val in [("relSz", rel), ("offset", off)]:
            el = next((c for c in new if c.tag == _q(tag)), None)
            if el is not None:
                for k in list(el.attrib): el.set(k, val)
    fr = new.find(_q("fontRef"))
    for lang, fid in fids.items(): fr.set(_LANG.get(lang, lang.lower()), fid)
    cps.append(new); cps.set("itemCnt", str(len(cps))); return nid

def _mk_parapr(hdr, align="CENTER", left=0, intent=0):
    """left = 왼쪽 여백, intent = 첫 줄 들여쓰기(음수면 내어쓰기).
    left=L, intent=-L 로 주면 둘째 줄부터 첫 줄 글자 시작 위치에 맞춰 정렬된다."""
    pp = next(hdr.iter(_q("paraProperties"))); new = copy.deepcopy(pp[0]); nid = str(len(pp)); new.set("id", nid)
    al = next((c for c in new.iter() if c.tag == _q("align")), None)
    if al is None: al = etree.SubElement(new, _q("align"))
    al.set("horizontal", align); al.set("vertical", "CENTER")
    if left or intent:
        for mg in new.iter():
            if not isinstance(mg.tag, str) or not mg.tag.endswith("}margin"):
                continue
            for ch in mg:
                if not isinstance(ch.tag, str):
                    continue
                if ch.tag.endswith("}intent"): ch.set("value", str(int(intent)))
                elif ch.tag.endswith("}left"): ch.set("value", str(int(left)))
    pp.append(new); pp.set("itemCnt", str(len(pp))); return nid


def _bullet_layout(line):
    """'  - 내용' → (앞여백 1.0글자, 글머리 1.0글자, '- 내용')

    앞의 공백을 글자로 찍으면 '- ' 가 오른쪽으로 밀려 보기 싫으므로,
    공백은 지우고 **문단 왼쪽 여백**으로 옮긴다. 글머리 폭만큼 내어쓰기를 주면
    줄이 넘어갔을 때 둘째 줄이 본문 첫 글자에 맞춰 정렬된다.
    """
    import re as _re
    s = str(line)
    m = _re.match(r"^([ \t\u00a0]*)(([○◦●□■▪▶–—-])[ \t]*)?(.*)$", s, _re.S)
    if not m:
        return 0.0, 0.0, s.strip()
    ws, mark, rest = m.group(1), m.group(2) or "", m.group(4)
    def cells(t):
        return sum(1.0 if ord(ch) > 0x1100 else 0.5 for ch in t)
    if not mark:
        return 0.0, 0.0, s.strip()
    mark = mark.rstrip() + " "          # 글머리 뒤 공백은 한 칸으로 통일
    return cells(ws), cells(mark), mark + rest.strip()


def _prefix_cells(line):
    """'○ ', '  - ' 같은 글머리 부분의 폭을 '글자 수'로 잰다 (전각=1, 반각=0.5)."""
    ws, mark, _ = _bullet_layout(line)
    return ws + mark

def _fills(doc, shade, line_color, lw="0.1 mm", side_lines=False):
    def bf(borders, fill=None):
        return doc.ensure_border_fill(border_color=line_color, border_width=lw,
                                      fill_color=fill, active_borders=borders)
    full = ["top", "bottom", "left", "right"]
    edge = full if side_lines else ["top", "bottom"]
    return (bf(full), bf(full, shade), bf(edge), bf(edge, shade))


def _fills_plain(doc, shade, line_color, lw="0.1 mm"):
    """줄글이 많은 표(부분예산표 등)용 — 안쪽 가로선만 없애고
    표의 맨 위·머리행 아래·**맨 아래 선은 남긴다.**"""
    def bf(borders, fill=None):
        return doc.ensure_border_fill(border_color=line_color, border_width=lw,
                                      fill_color=fill, active_borders=borders)
    none_, top_bottom, bottom = [], ["top", "bottom"], ["bottom"]
    # (본문 안쪽, 머리행, 본문 가장자리, 머리행 가장자리, 마지막 행)
    return (bf(none_), bf(top_bottom, shade), bf(none_), bf(top_bottom, shade),
            bf(bottom))

def _selected_hwp_font():
    """한글 표/보고서에 실제 적용할 글꼴명. 목록 밖 글꼴은 직접 입력할 수 있다."""
    ss = st.session_state
    choice = str(ss.get("hwp_font", "휴먼명조"))
    if choice == "직접 입력…":
        custom = str(ss.get("hwp_font_custom", "")).strip()
        return custom or "휴먼명조"
    return choice


def _doc_opts():
    ss = st.session_state
    return dict(font=_selected_hwp_font(), size=ss.get("hwp_size", 10),
                shade=ss.get("hwp_shade", "#D9D9D9"), line=ss.get("hwp_line", "#000000"),
                lw=ss.get("hwp_lw", "0.1 mm"), sides=ss.get("hwp_sides", False),
                row_h=float(ss.get("hwp_rowh", 6.5)),
                tight=int(ss.get("hwp_tight", -14)),
                ai_color=ss.get("hwp_aicolor", "#0000FF"))

def _cells_of(s):
    """문자열의 표시 폭을 '반각 칸 수'로 센다 (한글·전각=2, 영문·숫자=1)."""
    return sum(2 if ord(ch) > 0x1100 else 1 for ch in str(s))


def _col_widths(tdf, total, min_cells=5, max_cells=46):
    """열마다 들어가는 글자 길이에 비례해 폭을 나눈다.
    (모든 열을 똑같이 나누면 긴 글이 든 열만 여러 줄로 접혀 표가 지저분해진다)"""
    n = tdf.shape[1]
    if n <= 0:
        return []
    need = []
    for c in range(n):
        vals = [tdf.columns[c]] + list(tdf.iloc[:, c])
        longest = max((_cells_of(v) for v in vals), default=min_cells)
        need.append(min(max(longest, min_cells), max_cells))
    s = float(sum(need)) or 1.0
    out = [max(int(total * w / s), int(total * 0.06)) for w in need]
    out[-1] = total - sum(out[:-1])          # 반올림 오차는 마지막 열이 흡수
    return out


def _fit_size(table, n_cols, row_h_mm=6.5, widths=None, row_lines=None):
    """표를 본문 폭에 맞추고 행 높이를 촘촘하게.
    widths: 열별 폭(HWPUNIT) / row_lines: 행별 줄 수(줄이 접히는 행은 높게)"""
    ws = list(widths) if widths else [BODY_W // n_cols] * n_cols
    h1 = int(row_h_mm * MM)
    try:
        total_h = 0
        for r in range(table.row_count):
            lines = 1
            if row_lines and r < len(row_lines):
                lines = max(1, int(row_lines[r]))
            h = h1 * lines
            total_h += h
            for c in range(n_cols):
                table.cell(r, c).set_size(width=ws[c], height=h)
        sz = next((e for e in table.element.iter(f"{{{_HP}}}sz")), None)
        if sz is not None:
            sz.set("width", str(sum(ws))); sz.set("height", str(total_h))
    except Exception:
        pass

# 한 표가 한 쪽을 넘으면 한글에서 표가 잘려 보이는 일이 잦다. 이 행 수를 넘으면
# 여러 개의 표로 나눠서 넣는다(제목에 (1/3) 표시).
_MAX_TABLE_ROWS = 24


def _split_long_table(tb, max_rows=_MAX_TABLE_ROWS):
    """행이 너무 많은 표를 쪽 단위로 나눈다. 나눌 필요가 없으면 원본 하나만 돌려준다."""
    if tb is None or len(tb) <= max_rows:
        return [tb]
    return [tb.iloc[i:i + max_rows] for i in range(0, len(tb), max_rows)]


def _write_table(doc, tdf, center, cp_body, cp_head, fills, cp_sup=None, row_h_mm=6.5,
                 size_pt=10, tight=0):
    """셀 값에 '^'가 있으면 뒤쪽을 위첨자로 (예: '13.5^a')
    tight: 셀 글자에 적용한 자간(%). 음수면 그만큼 글자가 좁아지므로 줄 수 계산에 반영한다."""
    inner, header, b_edge, h_edge = fills[:4]
    last_row_fill = fills[4] if len(fills) > 4 else None
    nr, nc = tdf.shape[0]+1, tdf.shape[1]
    table = doc.add_table(nr, nc)  # nr: 머리행 포함 행 수
    try:
        # 쪽이 바뀌어도 표가 셀 단위로 이어지고, 다음 쪽에 머리행이 다시 나오게 한다.
        table.element.set("pageBreak", "CELL")
        table.element.set("repeatHeader", "1")
    except Exception:
        pass
    widths = _col_widths(tdf, BODY_W)
    # 열 폭 대비 글자 길이로 '몇 줄이 될지'를 미리 재서 행 높이를 잡는다
    per_cell = max(size_pt * 100 / 2.0 * (1 + min(0, tight) / 100.0), 1.0)  # 반각 한 칸 폭
    cap = [max(int(w / per_cell) - 1, 4) for w in widths]
    row_lines = []
    for r in range(nr):
        vals = list(tdf.columns) if r == 0 else list(tdf.iloc[r-1])
        row_lines.append(max(
            [max(1, -(-_cells_of(v) // cap[c])) for c, v in enumerate(vals)] or [1]))

    def fill(r, c, txt, is_h):
        cell = table.cell(r, c); edge = (c == 0 or c == nc-1)
        bfid = (h_edge if edge else header) if is_h else (b_edge if edge else inner)
        if (not is_h) and last_row_fill is not None and r == nr - 1:
            bfid = last_row_fill
        try: cell.element.set("borderFillIDRef", bfid)
        except Exception: pass
        s = str(txt)
        try:
            paras = cell.paragraphs; pp = paras[0] if paras else cell.add_paragraph()
            pp.element.set("paraPrIDRef", center)
            if cp_sup and "^" in s:
                base, _, sup = s.partition("^")
                pp.add_run(base, char_pr_id_ref=(cp_head if is_h else cp_body))
                pp.add_run(sup, char_pr_id_ref=cp_sup)
            else:
                # cp_sup 를 못 만든 경우에도 '^'가 그대로 남지 않게 유니코드 위첨자로
                pp.add_run(sup_text(s), char_pr_id_ref=(cp_head if is_h else cp_body))
        except Exception:
            cell.text = str(sup_text(s))
    for c, name in enumerate(tdf.columns): fill(0, c, name, True)
    for r in range(tdf.shape[0]):
        for c in range(tdf.shape[1]): fill(r+1, c, tdf.iloc[r, c], False)
    _fit_size(table, nc, row_h_mm, widths=widths, row_lines=row_lines)

def _setup(doc, font):
    hdr = doc.headers[0].element
    cp0 = next(e for e in hdr.iter(_q("charPr")) if e.get("id") == "0")
    fids = _reg_font(hdr, font)
    return hdr, cp0, fids

def dataframe_to_hwpx(df, title="분석 결과표", **kw):
    from hwpx import HwpxDocument
    import tempfile, os
    o = _doc_opts(); o.update(kw)
    doc = HwpxDocument.new()
    hdr, cp0, fids = _setup(doc, o["font"])
    cp_body = _mk_charpr(hdr, cp0, fids, o["size"])
    cp_head = _mk_charpr(hdr, cp0, fids, o["size"], bold=True)
    cp_title = _mk_charpr(hdr, cp0, fids, o["size"] + 3, bold=True)
    cp_sup = _mk_charpr(hdr, cp0, fids, o["size"], sup=True)
    center = _mk_parapr(hdr, "CENTER"); left = _mk_parapr(hdr, "LEFT")
    p = doc.add_paragraph(); p.element.set("paraPrIDRef", left)
    p.add_run(title, char_pr_id_ref=cp_title)
    _write_table(doc, df, center, cp_body, cp_head,
                 _fills(doc, o["shade"], o["line"], o["lw"], o["sides"]),
                 cp_sup=cp_sup, row_h_mm=o["row_h"], size_pt=o["size"])
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".hwpx"); tmp.close()
    doc.save_to_path(tmp.name)
    with open(tmp.name, "rb") as f: data = f.read()
    os.unlink(tmp.name); return data

def collect_captions(items):
    """보고서에 들어갈 표·그림 목차를 미리 계산"""
    tno = fno = 0
    tabs, figs = [], []
    for it in items:
        blocks = it.get("blocks")
        if blocks:
            for b in blocks:
                if b.get("table") is not None:
                    tno += 1; tabs.append(f"<표 {tno}> {b.get('caption','')}".rstrip())
                if b.get("image"):
                    fno += 1; figs.append(f"<그림 {fno}> {b.get('caption','')}".rstrip())
        else:
            if it.get("table") is not None:
                tno += 1; tabs.append(f"<표 {tno}> {it.get('heading','')}".rstrip())
            if it.get("image"):
                fno += 1; figs.append(f"<그림 {fno}> {it.get('heading','')}".rstrip())
    return tabs, figs

def build_report_hwpx(items, doc_title="실험 통계 분석 보고서", **kw):
    from hwpx import HwpxDocument
    import tempfile, os
    o = _doc_opts(); o.update(kw)
    sz = o["size"]
    doc = HwpxDocument.new()
    hdr, cp0, fids = _setup(doc, o["font"])
    cp_title = _mk_charpr(hdr, cp0, fids, sz + 6, bold=True)
    cp_head = _mk_charpr(hdr, cp0, fids, sz + 2, bold=True)
    cp_cap = _mk_charpr(hdr, cp0, fids, sz, bold=True)
    cp_body = _mk_charpr(hdr, cp0, fids, sz)
    cp_th = _mk_charpr(hdr, cp0, fids, sz, bold=True)
    cp_sup = _mk_charpr(hdr, cp0, fids, sz, sup=True)
    # AI 해석은 사람이 쓴 문장과 구분되도록 파란색
    cp_ai = _mk_charpr(hdr, cp0, fids, sz, color=o.get("ai_color", "#0000FF"))
    # 줄글이 많은 표는 자간을 좁혀 한 줄에 담는다(두 줄로 접히면 보기 나쁨)
    _tight = int(o.get("tight", -14))
    cp_body_t = _mk_charpr(hdr, cp0, fids, sz, spacing=_tight)
    cp_th_t = _mk_charpr(hdr, cp0, fids, sz, bold=True, spacing=_tight)
    center = _mk_parapr(hdr, "CENTER"); left = _mk_parapr(hdr, "LEFT")
    _hang_cache = {(0.0, 0.0): left}

    def _hang(ws, mark):
        """앞여백 ws글자 + 글머리 mark글자 → 문단모양 id (같은 값은 재사용)."""
        key = (round(ws, 1), round(mark, 1))
        if key not in _hang_cache:
            L = int((key[0] + key[1]) * sz * 100)
            I = -int(key[1] * sz * 100)
            _hang_cache[key] = (_mk_parapr(hdr, "LEFT", left=L, intent=I) if L else left)
        return _hang_cache[key]

    fills = _fills(doc, o["shade"], o["line"], o["lw"], o["sides"])
    fills_plain = _fills_plain(doc, o["shade"], o["line"], o["lw"])

    p = doc.add_paragraph(); p.element.set("paraPrIDRef", center)
    p.add_run(doc_title, char_pr_id_ref=cp_title)
    doc.add_paragraph()

    tno, fno = 0, 0
    for idx, it in enumerate(items, 1):
        p = doc.add_paragraph(); p.element.set("paraPrIDRef", left)
        p.add_run(f"□ {it.get('heading','분석 결과')}", char_pr_id_ref=cp_head)

        def render_text(t, ai=False):
            if not t:
                return
            for line in strip_md(t).split("\n"):
                if not line.strip():
                    continue          # 빈 줄은 문서에서 문단 사이만 벌어져 보기 나쁘다
                ws, mark, body = _bullet_layout(line)
                pp = doc.add_paragraph()
                # 앞 공백은 글자로 찍지 않고 문단 왼쪽 여백으로 옮기고,
                # 글머리 폭만큼 내어쓰기를 줘서 둘째 줄이 본문에 맞춰지게 한다.
                pp.element.set("paraPrIDRef", _hang(ws, mark))
                pp.add_run(body, char_pr_id_ref=(cp_ai if ai else cp_body))

        def render_table(tb, cap="", plain=False):
            nonlocal tno
            if tb is None:
                return
            tno += 1
            parts = _split_long_table(tb)
            for _i, _part in enumerate(parts):
                doc.add_paragraph()          # 표 위 한 줄 띄우기
                pp = doc.add_paragraph(); pp.element.set("paraPrIDRef", left)
                _cap = f"<표 {tno}> {cap}".rstrip()
                if len(parts) > 1:
                    _cap += f" ({_i + 1}/{len(parts)})"
                pp.add_run(_cap, char_pr_id_ref=cp_cap)
                _write_table(doc, _part, left if plain else center,
                             cp_body_t if plain else cp_body,
                             cp_th_t if plain else cp_th,
                             fills_plain if plain else fills,
                             cp_sup=cp_sup, size_pt=sz,
                             # 줄글 표는 행 높이를 낮춰 위아래 여백을 줄인다
                             row_h_mm=(o["row_h"] * 0.7 if plain else o["row_h"]),
                             tight=_tight if plain else 0)

        def render_image(im, cap=""):
            nonlocal fno
            if im:
                fno += 1
                doc.add_paragraph()          # 그림 위 한 줄 띄우기
                iid = doc.add_image(im, "png")
                pp = doc.add_paragraph(); pp.element.set("paraPrIDRef", center)
                pp.add_picture(iid, width=int(120*MM), height=int(80*MM), align="CENTER")
                # 그림 제목은 가운데 정렬(표 제목은 왼쪽 정렬 유지)
                pp = doc.add_paragraph(); pp.element.set("paraPrIDRef", center)
                pp.add_run(f"<그림 {fno}> {cap}".rstrip(), char_pr_id_ref=cp_cap)

        blocks = it.get("blocks")
        if blocks:
            # 여러 블록을 순서대로 렌더링 (설문처럼 표·그림이 여러 개인 경우)
            for blk in blocks:
                render_text(blk.get("text"), ai=bool(blk.get("ai")))
                render_table(blk.get("table"), blk.get("caption", ""),
                             plain=bool(blk.get("plain")))
                render_image(blk.get("image"), blk.get("caption", ""))
        else:
            render_text(it.get("text"))
            render_table(it.get("table"), it.get("heading", ""))
            render_image(it.get("image"), it.get("heading", ""))
        doc.add_paragraph()
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".hwpx"); tmp.close()
    doc.save_to_path(tmp.name)
    with open(tmp.name, "rb") as f: data = f.read()
    os.unlink(tmp.name); return data

# ---------------------------------------------------------------- 워드(docx) 생성
def _docx_table(doc, df, sup=True):
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt
    nc = df.shape[1]
    t = doc.add_table(rows=1, cols=nc)
    try: t.style = "Light Grid Accent 1"
    except Exception:
        try: t.style = "Table Grid"
        except Exception: pass
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    def setcell(cell, val, bold=False):
        cell.text = ""
        p = cell.paragraphs[0]; p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        s = str(val)
        if sup and "^" in s:
            base, _, sp = s.partition("^")
            r = p.add_run(base); r.font.size = Pt(9); r.bold = bold
            r2 = p.add_run(sp); r2.font.size = Pt(9); r2.bold = bold
            r2.font.superscript = True
        else:
            # sup=False 로 불렸더라도 '^'가 그대로 찍히지 않게 유니코드 위첨자로 대체
            r = p.add_run(str(sup_text(s))); r.font.size = Pt(9); r.bold = bold
    for i, c in enumerate(df.columns): setcell(t.rows[0].cells[i], c, bold=True)
    for _, row in df.iterrows():
        cells = t.add_row().cells
        for i, v in enumerate(row): setcell(cells[i], v)
    try:
        # 표가 여러 쪽에 걸칠 때 다음 쪽에도 머리행이 나오게 한다.
        from docx.oxml.ns import qn as _qn
        from docx.oxml import OxmlElement as _Ox
        _el = _Ox("w:tblHeader"); _el.set(_qn("w:val"), "true")
        t.rows[0]._tr.get_or_add_trPr().append(_el)
    except Exception:
        pass
    return t

def dataframe_to_docx(df, title="분석 결과표"):
    if not _HAS_DOCX:
        raise RuntimeError("python-docx 미설치")
    import docx, tempfile, os
    from docx.shared import Pt
    doc = docx.Document()
    doc.styles["Normal"].font.name = "맑은 고딕"
    doc.styles["Normal"].font.size = Pt(10)
    doc.add_heading(title, level=1)
    _docx_table(doc, df)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx"); tmp.close()
    doc.save(tmp.name)
    with open(tmp.name, "rb") as f: data = f.read()
    os.unlink(tmp.name); return data

def build_report_docx(items, doc_title="실험 통계 분석 보고서"):
    if not _HAS_DOCX:
        raise RuntimeError("python-docx 미설치")
    import docx, io, tempfile, os
    from docx.shared import Pt, Mm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    doc = docx.Document()
    doc.styles["Normal"].font.name = "맑은 고딕"
    doc.styles["Normal"].font.size = Pt(10)
    h = doc.add_heading(doc_title, level=0)
    h.alignment = WD_ALIGN_PARAGRAPH.CENTER
    tno, fno = [0], [0]
    def add_text(t, ai=False):
        if not t:
            return
        from docx.shared import Pt as _Pt, RGBColor as _RGB
        for line in strip_md(t).split("\n"):
            if not line.strip():
                continue                     # 빈 줄은 문단 사이만 벌어져 보기 나쁘다
            ws, mark, body = _bullet_layout(line)
            p = doc.add_paragraph()
            r = p.add_run(body)
            if ai:
                r.font.color.rgb = _RGB(0x00, 0x00, 0xFF)
            if ws or mark:
                # 앞 공백은 글자로 찍지 않고 여백으로, 글머리 폭만큼 내어쓰기
                p.paragraph_format.left_indent = _Pt((ws + mark) * 10)
                p.paragraph_format.first_line_indent = _Pt(-mark * 10)
    def add_table(tb, cap=""):
        if tb is None:
            return
        tno[0] += 1
        parts = _split_long_table(tb)
        for _i, _part in enumerate(parts):
            _cap = f"<표 {tno[0]}> {cap}".rstrip()
            if len(parts) > 1:
                _cap += f" ({_i + 1}/{len(parts)})"
            c = doc.add_paragraph(_cap)
            c.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for r in c.runs: r.bold = True
            _docx_table(doc, _part)
    def add_image(im, cap=""):
        if im:
            fno[0] += 1
            p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(io.BytesIO(im), width=Mm(120))
            c = doc.add_paragraph(f"<그림 {fno[0]}> {cap}".rstrip())
            c.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for r in c.runs: r.bold = True
    for idx, it in enumerate(items, 1):
        doc.add_heading(f"□ {it.get('heading','분석 결과')}", level=1)
        blocks = it.get("blocks")
        if blocks:
            for blk in blocks:
                add_text(blk.get("text"), ai=bool(blk.get("ai")))
                add_table(blk.get("table"), blk.get("caption", ""))
                add_image(blk.get("image"), blk.get("caption", ""))
        else:
            add_text(it.get("text")); add_table(it.get("table"), it.get("heading", ""))
            add_image(it.get("image"), it.get("heading", ""))
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx"); tmp.close()
    doc.save(tmp.name)
    with open(tmp.name, "rb") as f: data = f.read()
    os.unlink(tmp.name); return data

# ---------------------------------------------------------------- 보고서 담기
@st.cache_data(show_spinner=False, max_entries=80)
def _make_docs(csv_text, title, fmt, opts_sig):
    _df = pd.read_csv(io.StringIO(csv_text), dtype=str).fillna("")
    return dataframe_to_hwpx(_df, title) if fmt == "hwpx" else dataframe_to_docx(_df, title)

_XL_NOT_VALUE = ("표준편차", "표준오차", "표준 편차", "표준 오차", "sd", "se", "std",
                 "p-value", "p값", "pvalue", "유의", "cv", "lsd", "df", "자유도",
                 "f값", "t값", "n수", "반복수", "순위", "rank", "개수")


def _xl_is_value_col(name):
    """차트에 그릴 '값' 열인지 판단. 표준편차·p값·n 같은 보조 열은 제외한다."""
    t = str(name).strip().lower()
    if t in ("n", "N".lower()):
        return False
    return not any(k in t for k in _XL_NOT_VALUE)


def _xl_split(v):
    """'345.500^a' 또는 '345.500ᵃ' → (345.5, 'a'). 숫자로 볼 수 없으면 (None, None).

    엑셀 차트는 **숫자 셀**만 그릴 수 있다. 이 앱의 표는 유의성 문자를 값에 붙여
    문자열로 만들어 두기 때문에, 그대로 내보내면 그래프가 그려지지 않는다.
    """
    import re as _re
    if isinstance(v, bool):
        return (None, None)
    if isinstance(v, (int, float)):
        return (float(v), "") if pd.notna(v) else (None, None)
    t = str(v).strip()
    if not t or t.lower() in ("nan", "none", "-", "―"):
        return (None, None)
    _SC = "ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿ"
    letters = ""
    while t and t[-1] in _SC:                     # 유니코드 위첨자를 보통 글자로
        letters = "abcdefghijklmn"[_SC.index(t[-1])] + letters
        t = t[:-1]
    m = _re.match(r"^\s*(-?[\d,]+(?:\.\d+)?)\s*\^?\s*([a-zA-Z]{1,3}\**|\*+)?\s*$", t)
    if not m:
        return (None, None)
    return float(m.group(1).replace(",", "")), (m.group(2) or "") + letters


def _xlsx_blue_fill(value, vmin, vmax):
    """숫자 셀용 옅은 파랑 그라데이션 색상(HEX)을 반환."""
    try:
        if value is None or pd.isna(value) or vmax <= vmin:
            return None
        ratio = max(0.0, min(1.0, (float(value) - float(vmin)) / (float(vmax) - float(vmin))))
        lo = (247, 251, 255)   # F7FBFF
        hi = (158, 197, 229)   # 9EC5E5
        rgb = tuple(round(lo[i] + (hi[i] - lo[i]) * ratio) for i in range(3))
        return ''.join(f'{x:02X}' for x in rgb)
    except Exception:
        return None


def _xlsx_sig_specs_for_df(df, sheet_name='데이터', hdr=4):
    """make_xlsx의 출력 열 구조를 그대로 재현해 차트용 유의성 문자 위치를 계산한다.

    반환 key: (시트명, 값 열 문자) -> {sig_col, sig_values, start_row}
    """
    from openpyxl.utils import get_column_letter
    out_cols = []
    sig_map = {}
    for c in df.columns:
        raw_vals = list(df[c])
        pairs = [_xl_split(v) for v in raw_vals]
        nonempty = [i for i, v in enumerate(raw_vals)
                    if not pd.isna(v) and str(v).strip().lower() not in ('', 'nan', 'none', '-', '―')]
        all_parseable = bool(nonempty) and all(pairs[i][0] is not None for i in nonempty)
        is_native_num = pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c])
        is_num_col = is_native_num or all_parseable
        value_pos = len(out_cols) + 1
        out_cols.append((c, is_num_col))
        letters = [p[1] or '' for p in pairs]
        if is_num_col and any(letters):
            sig_pos = len(out_cols) + 1
            out_cols.append((f'{c} 유의성', False))
            sig_map[(str(sheet_name), get_column_letter(value_pos))] = {
                'sig_col': get_column_letter(sig_pos),
                'sig_values': letters,
                'value_values': [p[0] for p in pairs],
                'start_row': hdr + 1,
            }
    return sig_map


def _inject_xlsx_significance_labels(xlsx_bytes, specs):
    """Excel 막대 위에 ``165.25ᵃ`` 형태의 유의성 레이블을 넣는다.

    Excel의 일반 데이터 레이블과 셀 참조 텍스트를 동시에 켜면 일부 버전에서
    작은 '범례 키 사각형 + a'처럼 렌더링되는 문제가 있다. 따라서 각 막대에
    **값과 유의성 문자를 합친 하나의 사용자 지정 텍스트 레이블**만 넣는다.
    범례 키·계열명·범주명은 모두 명시적으로 끈다.
    """
    if not specs:
        return xlsx_bytes
    import zipfile, re as _re
    from lxml import etree as _ET

    src = io.BytesIO(xlsx_bytes)
    out = io.BytesIO()
    CURI = 'http://schemas.openxmlformats.org/drawingml/2006/chart'
    AURI = 'http://schemas.openxmlformats.org/drawingml/2006/main'
    ns = {'c': CURI, 'a': AURI}
    C = '{%s}' % CURI
    A = '{%s}' % AURI

    def _parse_formula(f):
        m = _re.match(r"(?:'((?:[^']|'')+)'|([^!]+))!\$?([A-Z]+)\$?\d+", str(f or ''))
        if not m:
            return None, None
        sheet = (m.group(1) or m.group(2) or '').replace("''", "'")
        return sheet, m.group(3)

    def _fmt_num(v):
        try:
            x = float(v)
            if abs(x) >= 1000:
                return f"{x:,.2f}".rstrip('0').rstrip('.')
            return f"{x:.2f}".rstrip('0').rstrip('.')
        except Exception:
            return ''

    def _rich_value_sig(parent, value_txt, sig_txt):
        """Excel 데이터 레이블에 값 + 실제 위첨자 a/b/c를 rich text로 넣는다.

        작은 범례키 사각형이나 Unicode 위첨자 글꼴 깨짐 없이
        165.25ᵃ처럼 보이되, a는 DrawingML baseline 속성으로 진짜 위첨자 처리한다.
        """
        tx = _ET.SubElement(parent, C + 'tx')
        rich = _ET.SubElement(tx, C + 'rich')
        _ET.SubElement(rich, A + 'bodyPr')
        _ET.SubElement(rich, A + 'lstStyle')
        p = _ET.SubElement(rich, A + 'p')
        r1 = _ET.SubElement(p, A + 'r')
        _ET.SubElement(r1, A + 'rPr', lang='ko-KR', sz='900')
        _ET.SubElement(r1, A + 't').text = value_txt
        if sig_txt:
            r2 = _ET.SubElement(p, A + 'r')
            # baseline=30000은 본문 기준 약 30% 위로 올리는 DrawingML superscript 효과.
            _ET.SubElement(r2, A + 'rPr', lang='en-US', sz='720', baseline='30000')
            _ET.SubElement(r2, A + 't').text = str(sig_txt)
        _ET.SubElement(p, A + 'endParaRPr', lang='ko-KR', sz='900')

    with zipfile.ZipFile(src, 'r') as zin, zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as zout:
        for info in zin.infolist():
            raw = zin.read(info.filename)
            if not (info.filename.startswith('xl/charts/chart') and info.filename.endswith('.xml')):
                zout.writestr(info, raw)
                continue
            try:
                root = _ET.fromstring(raw)
                changed = False
                for ser in root.xpath('.//c:barChart/c:ser', namespaces=ns):
                    fnode = ser.find('.//c:val/c:numRef/c:f', namespaces=ns)
                    if fnode is None:
                        continue
                    sh, vcol = _parse_formula(fnode.text)
                    spec = specs.get((sh, vcol))
                    if not spec:
                        continue
                    old = ser.find(C + 'dLbls')
                    if old is not None:
                        ser.remove(old)
                    dlbls = _ET.Element(C + 'dLbls')
                    sig_values = list(spec.get('sig_values') or [])
                    num_values = list(spec.get('value_values') or [])
                    for i, sigv in enumerate(sig_values):
                        if not sigv:
                            continue
                        dl = _ET.SubElement(dlbls, C + 'dLbl')
                        _ET.SubElement(dl, C + 'idx', val=str(i))
                        _ET.SubElement(dl, C + 'layout')
                        _value_txt = _fmt_num(num_values[i] if i < len(num_values) else None)
                        _rich_value_sig(dl, _value_txt, sigv)
                        _ET.SubElement(dl, C + 'dLblPos', val='outEnd')
                        _ET.SubElement(dl, C + 'showLegendKey', val='0')
                        _ET.SubElement(dl, C + 'showVal', val='0')
                        _ET.SubElement(dl, C + 'showCatName', val='0')
                        _ET.SubElement(dl, C + 'showSerName', val='0')
                        _ET.SubElement(dl, C + 'showPercent', val='0')
                    _ET.SubElement(dlbls, C + 'showLegendKey', val='0')
                    _ET.SubElement(dlbls, C + 'showVal', val='0')
                    _ET.SubElement(dlbls, C + 'showCatName', val='0')
                    _ET.SubElement(dlbls, C + 'showSerName', val='0')
                    _ET.SubElement(dlbls, C + 'showPercent', val='0')
                    _ET.SubElement(dlbls, C + 'dLblPos', val='outEnd')
                    children = list(ser)
                    pos = next((i for i, el in enumerate(children)
                                if el.tag in (C + 'cat', C + 'val')), len(children))
                    ser.insert(pos, dlbls)
                    changed = True
                if changed:
                    raw = _ET.tostring(root, xml_declaration=True, encoding='UTF-8', standalone=True)
            except Exception:
                pass
            zout.writestr(info, raw)
    return out.getvalue()



def _xl_spec_list(chart_spec):
    """chart_spec(None | dict | list)를 목록으로 정리한다. None이면 기존 자동 막대그래프 동작을 쓴다."""
    if chart_spec is None:
        return None
    if isinstance(chart_spec, dict):
        chart_spec = [chart_spec]
    return [sp for sp in chart_spec if isinstance(sp, dict) and sp.get("data") is not None and len(sp["data"])]


def xl_chart(kind, data, title="", y_title=None, value_range=None):
    """엑셀에 넣을 그래프 지정.

    kind: 'bar'(세로 막대) · 'barh'(가로 막대) · 'stacked'(누적 막대) · 'stacked100'(100% 누적)
          · 'line'(꺾은선) · 'pie' · 'donut' · 'scatter'(산점도+추세선) · 'heatmap'(칸 색칠)
    data: 첫 열 = 항목(가로축), 나머지 열 = 숫자 계열. scatter는 첫 열 X, 둘째 열 Y.
    """
    d = data.reset_index(drop=True) if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
    return {"kind": kind, "data": d, "title": title, "y_title": y_title, "value_range": value_range}


def _xlsx_write_spec_charts(ws, specs, start_row, anchor_col, sheet_name='데이터'):
    """차트용 숫자 표를 본 표 아래에 쓰고, 그 표를 참조하는 '편집 가능한' 엑셀 차트를 만든다.
    숫자를 고치면 차트가 바로 따라 바뀐다."""
    from openpyxl.chart import BarChart, LineChart, PieChart, DoughnutChart, ScatterChart, Reference, Series
    from openpyxl.chart.label import DataLabelList
    from openpyxl.chart.trendline import Trendline
    from openpyxl.chart.data_source import AxDataSource, StrRef, StrData, StrVal
    from openpyxl.chart.shapes import GraphicalProperties
    from openpyxl.formatting.rule import ColorScaleRule
    from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    FONT = '맑은 고딕'
    thin = Side(style='thin', color='C9DCEB')
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    palette = ('3D6F9F', '6FA3CF', 'E0A458', '82B366', 'C96767', '9673A6', '9EC5E5', '5B6F82')
    r = start_row
    chart_no = 0
    for sp in specs:
        d = sp["data"]
        kind = sp.get("kind", "bar")
        cols = list(d.columns)
        t = ws.cell(r, 1, f"📈 그래프 데이터 — {sp.get('title') or ''}".rstrip(" —"))
        t.font = Font(name=FONT, size=10, bold=True, color='244A73')
        r += 1
        hdr = r
        for j, c in enumerate(cols, start=1):
            h = ws.cell(hdr, j, str(c))
            h.font = Font(name=FONT, bold=True, color='FFFFFF', size=9)
            h.fill = PatternFill('solid', fgColor='6F93B8')
            h.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
            h.border = border
        for i, row in enumerate(d.itertuples(index=False), start=hdr + 1):
            for j, v in enumerate(row, start=1):
                if isinstance(v, (np.floating, float)) and not np.isfinite(v):
                    v = None
                elif isinstance(v, np.generic):
                    v = v.item()
                if j == 1 and kind != "scatter":
                    v = "" if v is None else str(v)
                cell = ws.cell(i, j, v)
                cell.font = Font(name=FONT, size=9)
                cell.border = border
                if (j > 1 or kind == "scatter") and isinstance(v, (int, float)):
                    cell.number_format = '#,##0' if float(v).is_integer() else '#,##0.00'
        n = len(d)
        last = hdr + n
        cat_vals = [str(v) for v in d.iloc[:, 0].tolist()]
        cat_f = "'{}'!${}${}:${}${}".format(sheet_name, 'A', hdr + 1, 'A', last)

        def _cats(series_list):
            cache = StrData(ptCount=len(cat_vals), pt=[StrVal(idx=i, v=v) for i, v in enumerate(cat_vals)])
            for s_ in series_list:
                s_.cat = AxDataSource(strRef=StrRef(f=cat_f, strCache=cache))

        ch = None
        if kind == "heatmap":
            rng = f"B{hdr + 1}:{get_column_letter(len(cols))}{last}"
            lo, hi = (sp.get("value_range") or (None, None))
            ws.conditional_formatting.add(rng, ColorScaleRule(
                start_type='num' if lo is not None else 'min', start_value=lo, start_color='C96767',
                mid_type='num', mid_value=0 if lo is not None else None, mid_color='FFFFFF',
                end_type='num' if hi is not None else 'max', end_value=hi, end_color='3D6F9F')
                if lo is not None else ColorScaleRule(start_type='min', start_color='FFFFFF',
                                                      end_type='max', end_color='3D6F9F'))
            for i in range(hdr + 1, last + 1):
                for j in range(2, len(cols) + 1):
                    ws.cell(i, j).number_format = '0.00'
        elif kind in ("bar", "barh", "stacked", "stacked100"):
            ch = BarChart()
            ch.type = 'bar' if kind == "barh" else 'col'
            if kind in ("stacked", "stacked100"):
                ch.grouping = 'stacked' if kind == "stacked" else 'percentStacked'
                ch.overlap = 100
            for j in range(2, len(cols) + 1):
                ch.add_data(Reference(ws, min_col=j, min_row=hdr, max_row=last), titles_from_data=True)
            _cats(ch.series)
            if kind == "barh":
                ch.x_axis.scaling.orientation = "maxMin"     # 화면처럼 첫 항목이 위로
            ch.gapWidth = 70
        elif kind == "line":
            ch = LineChart()
            for j in range(2, len(cols) + 1):
                ch.add_data(Reference(ws, min_col=j, min_row=hdr, max_row=last), titles_from_data=True)
            _cats(ch.series)
            for s_ in ch.series:
                s_.marker.symbol = "circle"
                s_.marker.size = 7
                s_.smooth = False
        elif kind in ("pie", "donut"):
            ch = DoughnutChart() if kind == "donut" else PieChart()
            ch.add_data(Reference(ws, min_col=2, min_row=hdr, max_row=last), titles_from_data=True)
            _cats(ch.series)
            ch.dataLabels = DataLabelList()
            ch.dataLabels.showPercent = True
            ch.dataLabels.showVal = False
            ch.dataLabels.showCatName = False
            if kind == "donut":
                ch.holeSize = 55
        elif kind == "scatter":
            ch = ScatterChart()
            ch.style = 13
            xs = Reference(ws, min_col=1, min_row=hdr + 1, max_row=last)
            ys = Reference(ws, min_col=2, min_row=hdr, max_row=last)
            s_ = Series(ys, xs, title_from_data=True)
            s_.marker.symbol = "circle"
            s_.marker.size = 7
            s_.graphicalProperties.line.noFill = True
            s_.trendline = Trendline(trendlineType='linear', dispRSqr=True, dispEq=True)
            ch.series.append(s_)
            ch.x_axis.title = str(cols[0])
            ch.y_axis.title = str(cols[1])
            ch.legend = None
        if ch is not None:
            ch.title = sp.get("title") or None
            ch.height, ch.width = 9.2, 17
            if kind not in ("pie", "donut"):
                ch.x_axis.delete = False
                ch.y_axis.delete = False
            if sp.get("y_title") and kind not in ("pie", "donut", "scatter"):
                ch.y_axis.title = sp["y_title"]
            if kind not in ("pie", "donut"):
                for si, s_ in enumerate(ch.series):
                    try:
                        col = palette[si % len(palette)]
                        if kind == "line":
                            s_.graphicalProperties.line.solidFill = col
                            s_.graphicalProperties.line.width = 22000
                            s_.marker.graphicalProperties = GraphicalProperties(solidFill=col)
                        elif kind != "scatter":
                            s_.graphicalProperties.solidFill = col
                            s_.graphicalProperties.line.solidFill = 'FFFFFF'
                    except Exception:
                        pass
                if len(ch.series) > 1:
                    try:
                        ch.legend.position = "r"
                    except Exception:
                        pass
                elif kind != "scatter":
                    ch.legend = None
            ws.add_chart(ch, f"{get_column_letter(anchor_col)}{4 + chart_no * 20}")
            chart_no += 1
        r = last + 3
    return chart_no


def make_xlsx(df, title, chart=True, error_bars=False, chart_spec=None):
    """스마트 블루 표 + 엑셀에서 직접 편집 가능한 차트가 든 xlsx를 만든다.

    app(9)의 편집 가능한 Excel 차트 기능을 보존하면서, 화면과 같은 푸른 계열
    머리행·행 구분·숫자 그라데이션·테두리·필터·틀 고정을 적용한다.
    기본 차트는 처리구명 + 평균값을 명확히 보여주고 오차막대는 자동으로 넣지 않는다.
    """
    from openpyxl import Workbook
    from openpyxl.chart import BarChart, Reference
    from openpyxl.chart.error_bar import ErrorBars
    from openpyxl.chart.label import DataLabelList
    from openpyxl.chart.data_source import NumDataSource, NumRef, AxDataSource, StrRef, StrData, StrVal
    from openpyxl.chart.marker import DataPoint
    from openpyxl.chart.shapes import GraphicalProperties
    from openpyxl.styles import Alignment, Font, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter

    # ① 값과 유의성 문자를 분리해 숫자 셀로 만든다.
    # 문자열 열은 비어 있지 않은 값이 모두 숫자로 해석될 때만 숫자열로 취급한다.
    # 일부만 숫자인 열을 숫자열로 바꾸면 나머지 문자값이 빈칸으로 사라질 수 있다.
    cols, sig = [], {}
    for c in df.columns:
        raw_vals = list(df[c])
        pairs = [_xl_split(v) for v in raw_vals]
        nonempty = [i for i, v in enumerate(raw_vals)
                    if not pd.isna(v) and str(v).strip().lower() not in ('', 'nan', 'none', '-', '―')]
        all_parseable = bool(nonempty) and all(pairs[i][0] is not None for i in nonempty)
        is_native_num = pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c])
        is_num_col = is_native_num or all_parseable
        if is_num_col:
            vals = [p[0] if p[0] is not None else None for p in pairs]
            cols.append((c, vals, True))
            if any(p[1] for p in pairs):
                sig[c] = [p[1] or '' for p in pairs]
        else:
            cols.append((c, [('' if pd.isna(v) else str(v)) for v in raw_vals], False))

    wb = Workbook()
    ws = wb.active
    ws.title = '데이터'
    ws.sheet_properties.tabColor = '3D6F9F'
    ws.sheet_view.showGridLines = False
    FONT = '맑은 고딕'
    NAVY, HEADER, MID, LIGHT, PALE, LINE = '244A73', '3D6F9F', '9EC5E5', 'EAF3FA', 'F7FBFF', 'C9DCEB'
    thin = Side(style='thin', color=LINE)
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    HDR = 4
    out_cols = []
    for name, vals, is_num in cols:
        out_cols.append((name, vals, is_num))
        if name in sig:
            out_cols.append((f'{name} 유의성', sig[name], False))

    n_out = max(len(out_cols), 1)
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=n_out)
    a1 = ws.cell(1, 1, title)
    a1.fill = PatternFill('solid', fgColor=NAVY)
    a1.font = Font(name=FONT, size=14, bold=True, color='FFFFFF')
    a1.alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[1].height = 30

    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=n_out)
    _specs = _xl_spec_list(chart_spec)
    if _specs is not None:
        _has_chart = any(sp.get("kind") != "heatmap" for sp in _specs)
        _has_heat = any(sp.get("kind") == "heatmap" for sp in _specs)
    else:
        _vi = [j for j, (nm, _, isn) in enumerate(out_cols, 1)
               if j != 1 and isn and _xl_is_value_col(nm)]
        _has_chart = bool(chart and len(df) and out_cols and _vi)
        _has_heat = False
    if _has_chart:
        _a2_text = '숫자를 고치면 그래프가 바로 따라 바뀝니다. 그래프를 눌러 색·글꼴·축을 자유롭게 바꾸세요.'
    elif _has_heat:
        _a2_text = '아래 그래프 데이터의 칸 색은 값의 크기를 나타냅니다(파랑 = +, 빨강 = −). 숫자를 고치면 색도 따라 바뀝니다.'
    else:
        _a2_text = '표의 값은 엑셀에서 자유롭게 고치고 서식을 바꿀 수 있습니다.'
    a2 = ws.cell(2, 1, _a2_text)
    a2.font = Font(name=FONT, size=9, italic=True, color='5B6F82')
    a2.fill = PatternFill('solid', fgColor='F7FBFF')
    a2.alignment = Alignment(horizontal='left')

    for j, (name, vals, is_num) in enumerate(out_cols, start=1):
        h = ws.cell(row=HDR, column=j, value=str(name))
        h.font = Font(name=FONT, bold=True, color='FFFFFF', size=10)
        h.fill = PatternFill('solid', fgColor=HEADER)
        h.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        h.border = border
        for i, v in enumerate(vals, start=HDR + 1):
            cell = ws.cell(row=i, column=j, value=v)
            cell.font = Font(name=FONT)
            cell.border = border
            cell.alignment = Alignment(horizontal='center' if not is_num else 'right', vertical='center')
            # 값 크기와 무관한 아주 옅은 행 구분만 사용한다.
            # 평균·CV·순위 같은 숫자가 크다는 이유로 더 중요해 보이지 않게 한다.
            fill_color = PALE if (i - HDR) % 2 == 0 else 'FFFFFF'
            cell.fill = PatternFill('solid', fgColor=fill_color)
            if is_num and v is not None:
                try:
                    fv = float(v)
                    cell.number_format = '#,##0.00' if abs(fv) < 1000 else '#,##0.###'
                except Exception:
                    pass
        w = max([len(str(name))] + [len(str(v)) for v in vals[:200]]) * 1.55 + 4
        ws.column_dimensions[get_column_letter(j)].width = min(max(w, 11), 32)

    nrow = len(df)
    if out_cols:
        ws.freeze_panes = f'A{HDR+1}'
        ws.auto_filter.ref = f'A{HDR}:{get_column_letter(len(out_cols))}{HDR+nrow}' if nrow else f'A{HDR}:{get_column_letter(len(out_cols))}{HDR}'

    if _specs is not None:
        # 분석마다 화면 그래프와 같은 종류의 차트를 지정한 경우 (교차분석 누적막대, 상관 히트맵 등)
        if _specs:
            _xlsx_write_spec_charts(ws, _specs, start_row=HDR + nrow + 3, anchor_col=len(out_cols) + 2)
        buf = io.BytesIO(); wb.save(buf)
        return _inject_xlsx_significance_labels(buf.getvalue(), _xlsx_sig_specs_for_df(df, '데이터', HDR))

    if not chart or nrow == 0:
        buf = io.BytesIO(); wb.save(buf); return buf.getvalue()

    # ② 범주축은 원본 표의 첫 번째 열을 우선 사용한다.
    # 처리구가 1·2·3 같은 숫자 코드여도 유의성 문자 열을 X축으로 잘못 잡지 않는다.
    lab_idx = 1 if out_cols else None
    val_idx = [j for j, (nm, _, isn) in enumerate(out_cols, 1)
               if j != lab_idx and isn and _xl_is_value_col(nm)]
    err_idx = next((j for j, (nm, _, isn) in enumerate(out_cols, 1)
                    if isn and any(k in str(nm) for k in ('표준편차', '표준오차', 'SD', 'SE'))), None)
    if lab_idx is None or not val_idx:
        buf = io.BytesIO(); wb.save(buf); return buf.getvalue()
    val_idx = val_idx[:3]

    ch = BarChart()
    ch.type = 'col'
    # Excel 기본 테마(style 번호)는 앱의 색을 덮어쓸 수 있어 사용하지 않는다.
    ch.title = title
    # X축은 처리구명이 바로 보이므로 '처리구' 같은 축 제목은 따로 넣지 않는다.
    # 축 제목이 범주명 자리를 먹어 처리구명이 안 보이는 문제를 방지한다.
    # 단위/측정항목은 차트 제목에 이미 포함된다. Excel의 세로축 제목은
    # 폭이 좁을 때 눈금과 겹치므로 표시하지 않는다.
    ch.y_axis.title = None
    ch.x_axis.title = None
    ch.gapWidth = 82
    ch.height, ch.width = 9.2, 17
    ch.roundedCorners = False
    ch.x_axis.delete = False
    ch.y_axis.delete = False
    ch.x_axis.axPos = "b"
    ch.y_axis.axPos = "l"
    ch.x_axis.tickLblPos = "nextTo"
    ch.y_axis.tickLblPos = "nextTo"
    ch.x_axis.majorTickMark = "none"
    ch.y_axis.majorTickMark = "out"
    ch.x_axis.noMultiLvlLbl = True

    cats = Reference(ws, min_col=lab_idx, min_row=HDR + 1, max_row=HDR + nrow)
    for j in val_idx:
        data = Reference(ws, min_col=j, min_row=HDR, max_row=HDR + nrow)
        ch.add_data(data, titles_from_data=True, from_rows=False)
    ch.set_categories(cats)
    # 처리구가 문자일 때 openpyxl의 기본 set_categories()가 numRef를 만들면
    # Excel에서 X축 처리구명이 통째로 안 보일 수 있다. 문자 범주는 strRef로 강제한다.
    if not out_cols[lab_idx - 1][2]:
        _cat_formula = "'데이터'!${}${}:${}${}".format(
            get_column_letter(lab_idx), HDR + 1, get_column_letter(lab_idx), HDR + nrow)
        _cat_values = [str(v) if v is not None else "" for v in out_cols[lab_idx - 1][1]]
        _cache = StrData(
            ptCount=len(_cat_values),
            pt=[StrVal(idx=i, v=v) for i, v in enumerate(_cat_values)]
        )
        for _ser in ch.series:
            _ser.cat = AxDataSource(strRef=StrRef(f=_cat_formula, strCache=_cache))

    # 차트도 화면과 같은 스마트 블루. 단일 계열 막대는 처리별로 밝기 그라데이션을 준다.
    _excel_series = ('3D6F9F', '6FA3CF', '9EC5E5')
    _excel_points = ('C2D9EE', 'A3C4E2', '82ACD3', '6291C2', '4576AB', '2D5A8E', '1F4569')
    for _si, (ser, col) in enumerate(zip(ch.series, _excel_series)):
        try:
            ser.graphicalProperties.solidFill = col
            ser.graphicalProperties.line.solidFill = '000000'
            ser.graphicalProperties.line.width = 6350
            if len(ch.series) == 1 and nrow > 1:
                # 화면의 원클릭 막대처럼 각 처리별로 옅은→진한 블루를 준다.
                pts = []
                for _i in range(nrow):
                    _c = _excel_points[round((len(_excel_points)-1) * _i / max(nrow-1, 1))]
                    _dp = DataPoint(idx=_i)
                    _dp.graphicalProperties = GraphicalProperties(solidFill=_c)
                    _dp.graphicalProperties.line.solidFill = '000000'
                    _dp.graphicalProperties.line.width = 4763
                    pts.append(_dp)
                ser.dPt = pts
        except Exception:
            pass
    try:
        # 차트/플롯 전체를 둘러싸는 검은 사각 프레임은 넣지 않는다.
        ch.graphical_properties = GraphicalProperties(solidFill='FFFFFF')
        ch.graphical_properties.line.noFill = True
        ch.plot_area.graphicalProperties = GraphicalProperties(solidFill='FFFFFF')
        ch.plot_area.graphicalProperties.line.noFill = True

        # 사용자가 요청한 대로 차트 전체/축/격자선의 불필요한 선은 모두 제거한다.
        # 검은 윤곽선은 막대 자체에만 남는다.
        ch.x_axis.spPr = GraphicalProperties()
        ch.x_axis.spPr.line.noFill = True
        ch.y_axis.spPr = GraphicalProperties()
        ch.y_axis.spPr.line.noFill = True
        from openpyxl.chart.axis import ChartLines
        _nogrid_x = ChartLines()
        _nogrid_x.spPr = GraphicalProperties()
        _nogrid_x.spPr.line.noFill = True
        _nogrid_y = ChartLines()
        _nogrid_y.spPr = GraphicalProperties()
        _nogrid_y.spPr.line.noFill = True
        ch.x_axis.majorGridlines = _nogrid_x
        ch.y_axis.majorGridlines = _nogrid_y
    except Exception:
        pass
    if len(ch.series) == 1:
        ch.legend = None
        ch.varyColors = False
        try:
            # 평균값은 막대 위에 바로 표시한다.
            ch.dLbls = DataLabelList()
            ch.dLbls.showVal = True
            ch.dLbls.showCatName = False
            ch.dLbls.showSerName = False
            ch.dLbls.showLegendKey = False
            ch.dLbls.position = "outEnd"
            ch.dLbls.numFmt = '#,##0.00'
        except Exception:
            pass
    else:
        try:
            ch.legend.position = "r"
            ch.legend.overlay = False
            # 응답자 특성처럼 빈도·비율이 함께 있는 그룹 막대도 값이 바로 보이게 한다.
            ch.dLbls = DataLabelList()
            ch.dLbls.showVal = True
            ch.dLbls.showCatName = False
            ch.dLbls.showSerName = False
            ch.dLbls.showLegendKey = False
            ch.dLbls.position = "outEnd"
            ch.dLbls.numFmt = '0.##'
        except Exception:
            pass

    if error_bars and err_idx and len(val_idx) == 1:
        try:
            ref = NumRef("'데이터'!${}${}:${}${}".format(
                get_column_letter(err_idx), HDR + 1, get_column_letter(err_idx), HDR + nrow))
            ch.series[0].errBars = ErrorBars(
                errDir='y', errBarType='both', errValType='cust',
                plus=NumDataSource(numRef=ref), minus=NumDataSource(numRef=ref))
            try:
                ch.series[0].errBars.spPr = GraphicalProperties()
                ch.series[0].errBars.spPr.line.solidFill = '000000'
            except Exception:
                pass
        except Exception:
            pass

    ws.add_chart(ch, f'{get_column_letter(len(out_cols) + 2)}{HDR}')

    note = HDR + nrow + 2
    ws.cell(row=note, column=1, value='※ 유의성 문자(a, b, c)가 있는 결과는 그래프의 막대 위에도 자동 표시됩니다.').font = Font(name=FONT, size=9, color='5B6F82')
    if error_bars and err_idx and len(val_idx) == 1:
        ws.cell(row=note + 1, column=1,
                value=f"※ 오차막대는 '{out_cols[err_idx - 1][0]}' 열을 사용했습니다.").font = Font(name=FONT, size=9, color='5B6F82')

    buf = io.BytesIO(); wb.save(buf)
    _raw = buf.getvalue()
    _raw = _inject_xlsx_significance_labels(_raw, _xlsx_sig_specs_for_df(df, '데이터', HDR))
    return _raw


def _rewrite_chart_sheet_refs(chart, new_sheet, old_sheet='데이터'):
    """openpyxl 차트의 값·범주·오차막대 참조 시트명을 바꾼다."""
    old_tokens = (f"'{old_sheet}'", old_sheet)
    new_token = f"'{new_sheet}'"
    for ser in getattr(chart, 'series', []):
        refs = [getattr(ser, 'val', None), getattr(ser, 'cat', None),
                getattr(ser, 'tx', None), getattr(ser, 'errBars', None),
                getattr(ser, 'xVal', None), getattr(ser, 'yVal', None)]
        for ref in refs:
            if ref is None:
                continue
            for sub in ('numRef', 'strRef'):
                r = getattr(ref, sub, None)
                if r is not None and getattr(r, 'f', None):
                    f = r.f
                    for old in old_tokens:
                        f = f.replace(old + '!', new_token + '!')
                    r.f = f
            for side in ('plus', 'minus'):
                nd = getattr(ref, side, None)
                r = getattr(nd, 'numRef', None) if nd is not None else None
                if r is not None and getattr(r, 'f', None):
                    f = r.f
                    for old in old_tokens:
                        f = f.replace(old + '!', new_token + '!')
                    r.f = f
    return chart


def make_xlsx_multi(blocks, doc_title='분석 결과'):
    """여러 분석 결과를 항목별 시트로 나누고, 각 시트에 스마트 블루 표/편집가능 차트를 담는다."""
    from openpyxl import load_workbook
    used, sheets = set(), []
    for b in blocks:
        tb = b.get('table')
        if tb is None or not len(tb):
            continue
        nm = str(b.get('caption') or '결과')
        for bad in ':\\/?*[]':
            nm = nm.replace(bad, ' ')
        nm = (nm.strip() or '결과')[:28]
        base, i = nm, 2
        while nm in used:
            nm = f'{base[:26]}_{i}'; i += 1
        used.add(nm)
        sheets.append((nm, tb, str(b.get('caption') or doc_title), b.get('xlsx_chart')))
    if not sheets:
        return None

    first = io.BytesIO(make_xlsx(sheets[0][1], sheets[0][2], chart_spec=sheets[0][3]))
    wb = load_workbook(first)
    first_ws = wb.active
    first_name = sheets[0][0]
    first_ws.title = first_name
    try:
        first_ws.sheet_properties.tabColor = '3D6F9F'
        first_ws.sheet_view.showGridLines = False
    except Exception:
        pass
    for ch in getattr(first_ws, '_charts', []):
        _rewrite_chart_sheet_refs(ch, first_name)

    for nm, tb, cap, spec in sheets[1:]:
        src = load_workbook(io.BytesIO(make_xlsx(tb, cap, chart_spec=spec)))
        ws_src = src.active
        ws = wb.create_sheet(nm)
        # 병합 셀/행 높이/열 너비/셀 스타일을 최대한 그대로 복사한다.
        for mr in ws_src.merged_cells.ranges:
            ws.merge_cells(str(mr))
        for r, dim in ws_src.row_dimensions.items():
            ws.row_dimensions[r].height = dim.height
        for k, v in ws_src.column_dimensions.items():
            ws.column_dimensions[k].width = v.width
        for row in ws_src.iter_rows():
            for c in row:
                if c.value is None and not c.has_style:
                    continue
                nc = ws.cell(row=c.row, column=c.column, value=c.value)
                nc.font = c.font.copy(); nc.fill = c.fill.copy(); nc.border = c.border.copy()
                nc.alignment = c.alignment.copy(); nc.number_format = c.number_format
                nc.protection = c.protection.copy()
        ws.freeze_panes = ws_src.freeze_panes
        ws.auto_filter.ref = ws_src.auto_filter.ref
        try:   # 상관 히트맵 같은 칸 색칠(조건부 서식)도 함께 옮긴다
            for _cf in ws_src.conditional_formatting:
                for _rule in _cf.rules:
                    ws.conditional_formatting.add(str(_cf.sqref), _rule)
        except Exception:
            pass
        try:
            ws.sheet_properties.tabColor = '3D6F9F'
            ws.sheet_view.showGridLines = False
        except Exception:
            pass
        for ch in getattr(ws_src, '_charts', []):
            try:
                _rewrite_chart_sheet_refs(ch, nm)
                ws.add_chart(ch, ch.anchor)
            except Exception:
                pass
    buf = io.BytesIO(); wb.save(buf)
    _raw = buf.getvalue()
    _specs = {}
    for _nm, _tb, _cap, _spec in sheets:
        _specs.update(_xlsx_sig_specs_for_df(_tb, _nm, 4))
    _raw = _inject_xlsx_significance_labels(_raw, _specs)
    return _raw

def dl_table(df, title, key, fname="table", image=None, xlsx_chart=None):
    """표(+선택적으로 그래프) 내려받기 — 체크했을 때만 파일을 만들어 화면이 빨라집니다.
    image(PNG bytes)를 넘기면 한글/워드 파일에 표 아래 그래프도 함께 들어갑니다."""
    want = st.checkbox(f"📥 '{title}' 파일로 저장", key=f"dlchk_{key}")
    if not want:
        return
    c1, c2 = st.columns(2)
    csv_text = df.to_csv(index=False)
    opts_sig = tuple(sorted((k, str(v)) for k, v in st.session_state.items()
                            if str(k).startswith("hwp_")))
    try:
        if image:
            item = [{"heading": title, "table": df, "image": image}]
            hwpx_bytes = build_report_hwpx(item, doc_title=title)
        else:
            hwpx_bytes = _make_docs(csv_text, title, "hwpx", opts_sig)
        c1.download_button("📄 한글(hwpx)" + (" (그래프 포함)" if image else ""), hwpx_bytes,
                           f"{fname}.hwpx", key=f"hwx_{key}", width="stretch")
    except Exception as _e:
        c1.caption(f"한글 파일 생성 실패 ({type(_e).__name__})")
    if _HAS_DOCX:
        try:
            if image:
                item = [{"heading": title, "table": df, "image": image}]
                docx_bytes = build_report_docx(item, doc_title=title)
            else:
                docx_bytes = _make_docs(csv_text, title, "docx", opts_sig)
            c2.download_button("📝 워드(docx)" + (" (그래프 포함)" if image else ""), docx_bytes,
                               f"{fname}.docx", key=f"dcx_{key}", width="stretch")
        except Exception as _e:
            c2.caption(f"워드 파일 생성 실패 ({type(_e).__name__})")
    else:
        c2.caption("워드 저장: pip install python-docx 필요")
    # app(9)의 "편집 가능한 Excel 차트" 기능을 유지하면서 스마트 블루 디자인을 적용한다.
    try:
        c2.download_button("📈 엑셀(xlsx) — 스마트 블루 디자인 + 편집 가능한 그래프", make_xlsx(df, title, chart_spec=xlsx_chart),
                           f"{fname}.xlsx", key=f"xls_{key}", width="stretch",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           help="화면과 같은 스마트 블루 표·차트 디자인으로 저장됩니다. 막대 색·글꼴·축 범위·차트 종류도 엑셀에서 직접 바꿀 수 있습니다.")
    except Exception as _e:
        c2.caption(f"엑셀 파일 생성 실패 ({type(_e).__name__})")
    c1.download_button("📊 CSV (표만)", csv_text.encode("utf-8-sig"),
                       f"{fname}.csv", key=f"csv_{key}", width="stretch")

def report_capture(slot, heading, text=None, table=None, image=None, blocks=None, xlsx_chart=None):
    """단일 표/그림, 또는 여러 개(blocks)를 담을 수 있음.
    blocks = [{'text':.., 'table':df, 'image':png, 'xlsx_chart': xl_chart(...)}, ...]
    xlsx_chart는 엑셀 저장 때만 쓰이는 그래프 지정(한글·워드 보고서에는 영향 없음)."""
    st.session_state[slot] = {"heading": heading, "text": text,
                              "table": table, "image": image, "blocks": blocks,
                              "xlsx_chart": xlsx_chart}

def report_button(slot, label="➕ 이 결과를 보고서에 담기"):
    if st.session_state.get(slot):
        if st.button(label, key="btn_" + slot):
            st.session_state.report_items.append(st.session_state[slot])
            st.success(f"보고서에 담았습니다! (현재 {len(st.session_state.report_items)}개) — '📑 보고서'에서 생성하세요.")


def survey_download_panel(slot, key, fname):
    """설문 결과를 한글·워드·Excel로 바로 내려받는다.
    한글/워드는 표·그래프가 포함된 보고서, Excel은 사용자가 차트를 직접 수정하는 파일이다.
    """
    item = st.session_state.get(slot)
    if not item:
        return
    st.markdown("#### 📥 설문 분석 결과 다운로드")
    st.caption("한글·워드는 표와 그래프를 묶은 보고서로, Excel은 표와 편집 가능한 차트를 저장합니다.")

    # 과거 세션에 다운로드 버튼 key가 남아 있으면 Streamlit이 위젯 값 할당 오류를 낼 수 있어 렌더 직전에 정리한다.
    for _wk in (f"dl_svyhwp_{key}", f"dl_svydocx_{key}", f"dl_svyxls_{key}"):
        try:
            if _wk in st.session_state:
                del st.session_state[_wk]
        except Exception:
            pass

    c1, c2, c3 = st.columns(3)
    _title = item.get("heading", "설문조사 분석 결과")

    try:
        hwp = build_report_hwpx([item], doc_title=_title)
        c1.download_button("📘 한글(hwpx)", hwp, f"{fname}.hwpx",
                           key=f"dl_svyhwp_{key}", width="stretch")
    except Exception as ex:
        c1.caption(f"한글 파일 생성 실패 ({type(ex).__name__})")

    if _HAS_DOCX:
        try:
            docx_bytes = build_report_docx([item], doc_title=_title)
            c2.download_button("📝 워드(docx)", docx_bytes, f"{fname}.docx",
                               key=f"dl_svydocx_{key}", width="stretch")
        except Exception as ex:
            c2.caption(f"워드 파일 생성 실패 ({type(ex).__name__})")
    else:
        c2.caption("워드 저장: python-docx 설치 필요")

    blocks = item.get("blocks") or []
    if not blocks and item.get("table") is not None:
        blocks = [{"caption": item.get("heading", "설문 결과"), "table": item.get("table"),
                   "xlsx_chart": item.get("xlsx_chart")}]
    xblocks = [b for b in blocks if b.get("table") is not None]
    try:
        if xblocks:
            xls = make_xlsx_multi(xblocks, doc_title=_title)
            c3.download_button("📈 Excel(xlsx) — 편집 가능한 그래프", xls, f"{fname}.xlsx",
                               key=f"dl_svyxls_{key}", width="stretch",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                               help="Excel에서 그래프를 클릭해 막대 색·글꼴·축 범위·차트 종류를 직접 수정할 수 있습니다.")
        else:
            c3.caption("Excel로 저장할 표가 없습니다.")
    except Exception as ex:
        c3.caption(f"Excel 파일 생성 실패 ({type(ex).__name__})")


# ================================================================ 회원가입/로그인 (Firebase Auth)
# 로그인은 Firebase Authentication REST API(이메일/비밀번호)로 처리하고, 회원 명부·이용 기록은
# Firestore에 서비스 계정으로 저장한다. firebase SDK 없이 requests + google-auth만 사용한다.
# 비밀번호는 Firebase가 보관하며 이 앱은 저장하지 않는다.
_FB_AUTH_URL = "https://identitytoolkit.googleapis.com/v1/accounts:"
_FB_TOKEN_URL = "https://securetoken.googleapis.com/v1/token"
_FS_BASE_URL = "https://firestore.googleapis.com/v1"
_AUTH_SESSION_KEYS = ("auth_user", "auth_id_token", "auth_refresh_token", "auth_expires_at")
_NO_ORG_LABEL = "개인 (소속 없음)"
# 기관 유형별 소속기관 목록 — 직접 입력하면 '경북농기원/경상북도 농업기술원'처럼 같은 기관이
# 따로 집계되므로, 목록이 있는 유형은 고르게 하고 없을 때만 직접 입력한다.
_ORG_DIRECT = "✏️ 목록에 없음 (직접 입력)"
_ORG_CHOICES = {
    "도·특광역시 농업기술원": [
        "경기도농업기술원", "강원특별자치도농업기술원", "충청북도농업기술원", "충청남도농업기술원",
        "전북특별자치도농업기술원", "전라남도농업기술원", "경상북도농업기술원", "경상남도농업기술원",
        "제주특별자치도농업기술원",
        "서울특별시농업기술센터", "부산광역시농업기술센터", "대구광역시농업기술센터",
        "인천광역시농업기술센터", "광주광역시농업기술센터", "대전광역시농업기술센터",
        "울산광역시농업기술센터", "세종특별자치시농업기술센터"],
    "농촌진흥청/소속기관": [
        "농촌진흥청", "국립농업과학원", "국립식량과학원", "국립원예특작과학원", "국립축산과학원"],
}
# 예전에 직접 입력된 이름을 관리자 통계에서 같은 기관으로 묶는다(가입 정보 자체는 바꾸지 않는다).
_ORG_ALIASES = {
    "경기": "경기도농업기술원", "강원": "강원특별자치도농업기술원", "충북": "충청북도농업기술원",
    "충청북도": "충청북도농업기술원", "충남": "충청남도농업기술원", "충청남도": "충청남도농업기술원",
    "전북": "전북특별자치도농업기술원", "전라북도": "전북특별자치도농업기술원",
    "전북특별자치도": "전북특별자치도농업기술원", "전남": "전라남도농업기술원",
    "전라남도": "전라남도농업기술원", "경북": "경상북도농업기술원", "경상북도": "경상북도농업기술원",
    "경남": "경상남도농업기술원", "경상남도": "경상남도농업기술원", "제주": "제주특별자치도농업기술원",
    "제주특별자치도": "제주특별자치도농업기술원", "경기도": "경기도농업기술원",
    "강원도": "강원특별자치도농업기술원", "강원특별자치도": "강원특별자치도농업기술원",
}


def _org_canonical(name):
    """'경북 농기원', '경상북도 농업기술원' → '경상북도농업기술원' (도 농업기술원 본원 이름만 묶는다)."""
    raw = str(name or "").strip()
    key = re.sub(r"\s+", "", raw)
    m = re.fullmatch(r"(.+?)(?:도)?(?:농업기술원|농기원|농업기술연구원)(?:본원)?", key)
    if m:
        head = m.group(1)
        for cand in (head, head + "도"):
            if cand in _ORG_ALIASES:
                return _ORG_ALIASES[cand]
    return raw
_NO_ORG_VALUE = "개인"


def _secret(name, default=""):
    import os
    try:
        v = st.secrets.get(name, None)
        if v is not None:
            return str(v)
    except Exception:
        pass
    return str(os.environ.get(name, default))


def _truthy(v):
    return str(v).strip().lower() in ("1", "true", "yes", "y", "on")


def _service_account_info():
    """Streamlit secrets의 [firebase_service_account] 표 또는 JSON 문자열을 읽는다."""
    import json
    raw = None
    try:
        raw = st.secrets.get("firebase_service_account", None)
    except Exception:
        raw = None
    if raw is None:
        raw = _secret("FIREBASE_SERVICE_ACCOUNT", "") or None
    if not raw:
        return None
    if isinstance(raw, str):
        try:
            info = json.loads(raw)
        except Exception:
            return None
    else:
        try:
            info = {k: raw[k] for k in raw}
        except Exception:
            return None
    pk = str(info.get("private_key", ""))
    if "\\n" in pk:
        info["private_key"] = pk.replace("\\n", "\n")
    if not (info.get("client_email") and info.get("private_key")):
        return None
    return info


def _auth_config():
    sa = _service_account_info()
    return {
        "api_key": _secret("FIREBASE_WEB_API_KEY"),
        "project_id": _secret("FIREBASE_PROJECT_ID") or str((sa or {}).get("project_id", "")),
        "service_account": sa,
        "required": _truthy(_secret("AUTH_REQUIRED", "false")),
        "verify_email": _truthy(_secret("REQUIRE_EMAIL_VERIFICATION", "true")),
        "admins": {x.strip().lower() for x in _secret("ADMIN_EMAILS", "").split(",") if x.strip()},
        # 가입 허용: 도메인 목록(하위 도메인 포함) + 예외 이메일. 둘 다 비어 있으면 누구나 허용.
        "allowed_domains": [x.strip().lower().lstrip("@").lstrip(".")
                            for x in _secret("ALLOWED_EMAIL_DOMAINS", "").split(",") if x.strip()],
        "allowed_emails": {x.strip().lower() for x in _secret("ALLOWED_EMAILS", "").split(",") if x.strip()},
    }


def _email_allowed(email, cfg=None):
    """허용 도메인(하위 도메인 포함)·예외 이메일·관리자 이메일이면 True.

    예) 허용 도메인이 go.kr 이면 rda.go.kr, gb.go.kr 주소도 통과한다.
    허용 목록이 하나도 없으면 제한 없이 모두 허용한다.
    가입할 때와 로그인할 때 모두 검사하므로 Firebase 쪽 차단 기능(유료)은 쓰지 않는다.
    """
    cfg = cfg or _auth_config()
    email = str(email or "").strip().lower()
    if "@" not in email:
        return False
    domains, emails = cfg.get("allowed_domains") or [], cfg.get("allowed_emails") or set()
    if not domains and not emails:
        return True
    if email in emails or email in (cfg.get("admins") or set()):
        return True
    host = email.rsplit("@", 1)[1]
    return any(host == d or host.endswith("." + d) for d in domains)


def _allowed_hint(cfg=None):
    cfg = cfg or _auth_config()
    ds = cfg.get("allowed_domains") or []
    return ", ".join("@" + d for d in ds) if ds else ""


# ---------------------------------------------------------------- Firebase Auth REST
_FB_ERROR_KO = {
    "EMAIL_EXISTS": "이미 가입된 이메일입니다. 로그인하거나 비밀번호 찾기를 이용해 주세요.",
    "INVALID_LOGIN_CREDENTIALS": "이메일 또는 비밀번호가 올바르지 않습니다.",
    "INVALID_PASSWORD": "이메일 또는 비밀번호가 올바르지 않습니다.",
    "EMAIL_NOT_FOUND": "이메일 또는 비밀번호가 올바르지 않습니다.",
    "USER_DISABLED": "사용이 중지된 계정입니다. 관리자에게 문의해 주세요.",
    "TOO_MANY_ATTEMPTS_TRY_LATER": "시도가 너무 많습니다. 잠시 후 다시 시도해 주세요.",
    "WEAK_PASSWORD": "비밀번호가 너무 약합니다. 8자 이상으로 정해 주세요.",
    "INVALID_EMAIL": "이메일 형식이 올바르지 않습니다.",
    "MISSING_PASSWORD": "비밀번호를 입력해 주세요.",
    "OPERATION_NOT_ALLOWED": "Firebase 콘솔에서 '이메일/비밀번호' 로그인이 켜져 있지 않습니다.",
    "INVALID_ID_TOKEN": "로그인이 만료되었습니다. 다시 로그인해 주세요.",
    "TOKEN_EXPIRED": "로그인이 만료되었습니다. 다시 로그인해 주세요.",
    "USER_NOT_FOUND": "계정을 찾을 수 없습니다. 다시 가입해 주세요.",
    "NO_CONFIG": "로그인 설정(FIREBASE_WEB_API_KEY)이 없습니다.",
}


def _fb_error_code(msg):
    return str(msg or "").split(" ")[0].split(":")[0].strip()


def _fb_error_text(msg):
    code = _fb_error_code(msg)
    if code in _FB_ERROR_KO:
        return _FB_ERROR_KO[code]
    if code.startswith("NETWORK"):
        return "Firebase 서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요."
    if "API_KEY" in code or "API key" in str(msg):
        return "Firebase API 키가 올바르지 않습니다. 관리자에게 문의해 주세요."
    return f"요청을 처리하지 못했습니다 ({code or '알 수 없는 오류'})."


def _fb_post(endpoint, payload):
    """identitytoolkit accounts:<endpoint> 호출. (응답 dict, 오류코드) 반환."""
    cfg = _auth_config()
    if not cfg["api_key"]:
        return None, "NO_CONFIG"
    headers = {"Content-Type": "application/json", "X-Firebase-Locale": "ko"}
    try:
        r = _requests.post(_FB_AUTH_URL + endpoint, params={"key": cfg["api_key"]},
                           json=payload, headers=headers, timeout=20)
    except Exception as ex:
        return None, f"NETWORK:{type(ex).__name__}"
    try:
        js = r.json() or {}
    except Exception:
        js = {}
    if r.status_code != 200:
        msg = (js.get("error") or {}).get("message") if isinstance(js, dict) else None
        return None, str(msg or f"HTTP_{r.status_code}")
    return js, None


def _fb_signup(email, password):
    return _fb_post("signUp", {"email": email.strip(), "password": password,
                               "returnSecureToken": True})


def _fb_signin(email, password):
    return _fb_post("signInWithPassword", {"email": email.strip(), "password": password,
                                           "returnSecureToken": True})


def _fb_lookup(id_token):
    js, err = _fb_post("lookup", {"idToken": id_token})
    if err:
        return None, err
    users = (js or {}).get("users") or []
    return (users[0] if users else None), (None if users else "USER_NOT_FOUND")


def _fb_send_verify(id_token):
    return _fb_post("sendOobCode", {"requestType": "VERIFY_EMAIL", "idToken": id_token})


def _fb_send_reset(email):
    return _fb_post("sendOobCode", {"requestType": "PASSWORD_RESET", "email": email.strip()})


def _fb_set_display_name(id_token, name):
    return _fb_post("update", {"idToken": id_token, "displayName": name.strip(),
                               "returnSecureToken": False})


def _fb_refresh(refresh_token):
    cfg = _auth_config()
    if not cfg["api_key"]:
        return None, "NO_CONFIG"
    try:
        r = _requests.post(_FB_TOKEN_URL, params={"key": cfg["api_key"]},
                           data={"grant_type": "refresh_token", "refresh_token": refresh_token},
                           timeout=20)
    except Exception as ex:
        return None, f"NETWORK:{type(ex).__name__}"
    try:
        js = r.json() or {}
    except Exception:
        js = {}
    if r.status_code != 200:
        return None, str((js.get("error") or {}).get("message") or f"HTTP_{r.status_code}")
    return js, None


# ---------------------------------------------------------------- Firestore (서비스 계정)
@st.cache_resource(show_spinner=False)
def _fs_session_cached(sa_json):
    import json
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
    creds = service_account.Credentials.from_service_account_info(
        json.loads(sa_json), scopes=["https://www.googleapis.com/auth/datastore"])
    return AuthorizedSession(creds)


def _fs_session():
    """Firestore에 쓰기 위한 인증 세션. 서비스 계정이 없거나 google-auth가 없으면 None."""
    import json
    cfg = _auth_config()
    sa = cfg["service_account"]
    if not sa or not cfg["project_id"]:
        return None
    try:
        return _fs_session_cached(json.dumps(sa, sort_keys=True))
    except Exception:
        return None


def _fs_docs_url(path=""):
    pid = _auth_config()["project_id"]
    base = f"{_FS_BASE_URL}/projects/{pid}/databases/(default)/documents"
    return f"{base}/{path}" if path else base


def _now_utc():
    import datetime as _dt
    return _dt.datetime.now(_dt.timezone.utc)


def _fs_encode(value):
    import datetime as _dt
    if value is None:
        return {"nullValue": None}
    if isinstance(value, bool):
        return {"booleanValue": value}
    if isinstance(value, int):
        return {"integerValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    if isinstance(value, _dt.datetime):
        if value.tzinfo is None:
            value = value.replace(tzinfo=_dt.timezone.utc)
        return {"timestampValue": value.astimezone(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")}
    return {"stringValue": str(value)}


def _fs_decode(fields):
    out = {}
    for k, v in (fields or {}).items():
        if "stringValue" in v:
            out[k] = v["stringValue"]
        elif "integerValue" in v:
            out[k] = int(v["integerValue"])
        elif "doubleValue" in v:
            out[k] = float(v["doubleValue"])
        elif "booleanValue" in v:
            out[k] = bool(v["booleanValue"])
        elif "timestampValue" in v:
            out[k] = v["timestampValue"]
        else:
            out[k] = None
    return out


def _fs_set(collection, doc_id, data):
    """문서의 지정한 필드만 덮어쓴다(없으면 새로 만든다). 다른 필드는 유지된다."""
    sess = _fs_session()
    if sess is None:
        return "NO_FIRESTORE"
    try:
        r = sess.patch(_fs_docs_url(f"{collection}/{doc_id}"),
                       params={"updateMask.fieldPaths": list(data.keys())},
                       json={"fields": {k: _fs_encode(v) for k, v in data.items()}}, timeout=15)
        return None if r.status_code == 200 else f"HTTP_{r.status_code}"
    except Exception as ex:
        return f"NETWORK:{type(ex).__name__}"


def _fs_add(collection, data):
    sess = _fs_session()
    if sess is None:
        return "NO_FIRESTORE"
    try:
        r = sess.post(_fs_docs_url(collection),
                      json={"fields": {k: _fs_encode(v) for k, v in data.items()}}, timeout=10)
        return None if r.status_code == 200 else f"HTTP_{r.status_code}"
    except Exception as ex:
        return f"NETWORK:{type(ex).__name__}"


def _fs_get(collection, doc_id):
    sess = _fs_session()
    if sess is None:
        return None
    try:
        r = sess.get(_fs_docs_url(f"{collection}/{doc_id}"), timeout=10)
        if r.status_code != 200:
            return None
        return _fs_decode((r.json() or {}).get("fields"))
    except Exception:
        return None


def _fs_list(collection, max_docs=5000):
    """컬렉션 전체(최대 max_docs개)를 읽는다. (행 목록, 오류) 반환."""
    sess = _fs_session()
    if sess is None:
        return None, "Firestore 서비스 계정 설정이 없습니다."
    rows, token = [], None
    try:
        while len(rows) < max_docs:
            params = {"pageSize": 300}
            if token:
                params["pageToken"] = token
            r = sess.get(_fs_docs_url(collection), params=params, timeout=20)
            if r.status_code != 200:
                return None, f"HTTP_{r.status_code}: {r.text[:160]}"
            js = r.json() or {}
            rows += [_fs_decode(d.get("fields")) for d in js.get("documents", [])]
            token = js.get("nextPageToken")
            if not token:
                break
    except Exception as ex:
        return None, f"네트워크 오류: {type(ex).__name__}"
    return rows[:max_docs], None


def _fs_recent(collection, time_field, limit):
    """time_field 기준 최신순 limit개. (행 목록, 오류) 반환."""
    sess = _fs_session()
    if sess is None:
        return None, "Firestore 서비스 계정 설정이 없습니다."
    query = {"structuredQuery": {
        "from": [{"collectionId": collection}],
        "orderBy": [{"field": {"fieldPath": time_field}, "direction": "DESCENDING"}],
        "limit": int(limit)}}
    try:
        r = sess.post(_fs_docs_url() + ":runQuery", json=query, timeout=30)
        if r.status_code != 200:
            return None, f"HTTP_{r.status_code}: {r.text[:160]}"
        return [_fs_decode(x["document"].get("fields")) for x in (r.json() or [])
                if isinstance(x, dict) and x.get("document")], None
    except Exception as ex:
        return None, f"네트워크 오류: {type(ex).__name__}"


# ---------------------------------------------------------------- 세션·기록
def _save_auth_session(js, meta=None):
    """signIn/refresh 응답을 세션에 저장한다. 앱 나머지는 auth_user 형태만 사용한다."""
    import time
    if not js:
        return False
    uid = js.get("localId") or js.get("user_id")
    token = js.get("idToken") or js.get("id_token")
    if not uid or not token:
        return False
    old = st.session_state.get("auth_user") or {}
    st.session_state["auth_user"] = {
        "id": uid,
        "email": js.get("email") or old.get("email", ""),
        "user_metadata": meta if meta is not None else (old.get("user_metadata") or {}),
    }
    st.session_state["auth_id_token"] = token
    st.session_state["auth_refresh_token"] = js.get("refreshToken") or js.get("refresh_token", "")
    st.session_state["auth_expires_at"] = time.time() + float(js.get("expiresIn") or js.get("expires_in") or 3600)
    return True


def _clear_auth_session():
    for k in _AUTH_SESSION_KEYS:
        st.session_state.pop(k, None)


def _current_auth_user():
    """로그인 사용자. 토큰이 만료되면 갱신하고, 계정이 정지·삭제됐으면 로그아웃시킨다."""
    import time
    user = st.session_state.get("auth_user")
    if not user:
        return None
    if time.time() > float(st.session_state.get("auth_expires_at", 0)) - 60:
        rt = st.session_state.get("auth_refresh_token")
        js, err = _fb_refresh(rt) if rt else (None, "TOKEN_EXPIRED")
        if err and not str(err).startswith("NETWORK"):
            _clear_auth_session()
            return None
        if js:
            _save_auth_session(js)
    return st.session_state.get("auth_user")


def _load_profile(uid, email=""):
    prof = _fs_get("profiles", uid) or {}
    return {"name": prof.get("name", ""), "organization_type": prof.get("organization_type", ""),
            "organization": prof.get("organization", ""), "department": prof.get("department", ""),
            "email": prof.get("email", email)}


def _record_login(user):
    """관리자 대시보드용 최근 로그인 갱신 + 로그인 기록. 실패해도 앱 사용은 막지 않는다."""
    if not user:
        return
    try:
        meta = user.get("user_metadata") or {}
        now = _now_utc()
        _fs_set("profiles", user.get("id"), {"email": user.get("email", ""), "last_login_at": now})
        _fs_add("login_events", {
            "user_id": user.get("id"), "email": user.get("email", ""),
            "name": meta.get("name", ""), "organization_type": meta.get("organization_type", ""),
            "organization": meta.get("organization", ""), "department": meta.get("department", ""),
            "logged_in_at": now})
    except Exception:
        pass


def _auth_logout():
    _clear_auth_session()
    _remember_forget()
    _ai_remember_forget()                   # 공용 PC 대비: 기억한 AI 키도 함께 지운다
    st.session_state.pop("api_key", None)
    st.rerun()


# ---------------------------------------------------------------- 로그인 상태 유지(브라우저 저장소)
# Streamlit Community Cloud는 서버에서 쿠키를 읽을 수 없어서(st.context.cookies가 비어 있음),
# 브라우저 localStorage에 갱신 토큰을 저장하고 작은 JS 컴포넌트(streamlit-js-eval)로 읽고 쓴다.
_REMEMBER_KEY = "ssa_remember"
_REMEMBER_DAYS = 30
try:
    from streamlit_js_eval import streamlit_js_eval as _streamlit_js_eval
    _HAS_JS_EVAL = True
except Exception:
    _HAS_JS_EVAL = False


def _js_eval(expr, key):
    """브라우저에서 JS 식을 실행하고 결과를 돌려준다. 아직 응답 전이면 None."""
    if not _HAS_JS_EVAL:
        return ""
    try:
        return _streamlit_js_eval(js_expressions=expr, key=key)
    except Exception:
        return ""


def _remember_read():
    """저장된 갱신 토큰. 없거나 만료면 "", 브라우저 응답 전이면 None."""
    import json, time
    raw = _js_eval(f"localStorage.getItem('{_REMEMBER_KEY}') || ''", key="ssa_remember_read")
    if raw is None:
        return None
    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        return ""
    if not data.get("rt") or float(data.get("exp", 0)) < time.time():
        return ""
    return str(data["rt"])


def _remember_save(refresh_token):
    """로그인 상태 유지를 켠 세션에서 매 화면 호출. 같은 key라 브라우저에서는 한 번만 실행된다."""
    import json, time, hashlib
    payload = json.dumps({"rt": refresh_token, "exp": time.time() + _REMEMBER_DAYS * 86400})
    tag = hashlib.sha1(refresh_token.encode()).hexdigest()[:10]
    gen = st.session_state.get("_auth_remember_gen", 0)
    _js_eval(f"localStorage.setItem('{_REMEMBER_KEY}', {json.dumps(payload)}) || 'ok'",
             key=f"ssa_remember_save_{gen}_{tag}")


def _remember_bump():
    # 같은 세션에서 저장→삭제→저장을 반복해도 매번 브라우저에서 새로 실행되도록 key를 바꾼다.
    st.session_state["_auth_remember_gen"] = st.session_state.get("_auth_remember_gen", 0) + 1


def _remember_forget():
    st.session_state.pop("_auth_remember_rt", None)
    st.session_state["_auth_remember_clear"] = True
    _remember_bump()


def _remember_sync():
    """예약된 저장/삭제를 브라우저에 반영한다. 로그인 화면·앱 화면 모두에서 호출."""
    if st.session_state.get("_auth_remember_clear"):
        _js_eval(f"localStorage.removeItem('{_REMEMBER_KEY}') || 'ok'",
                 key=f"ssa_remember_clear_{st.session_state.get('_auth_remember_gen', 0)}")
    rt = st.session_state.get("_auth_remember_rt")
    if rt:
        _remember_save(rt)


# ---------------------------------------------------------------- AI 키 기억(이 기기에만)
# 휴대폰에서 매번 긴 API 키를 입력하지 않도록, 사용자가 체크한 경우에만 이 브라우저에 저장한다.
_AI_REMEMBER_KEY = "ssa_ai"


def _ai_remember_bump():
    st.session_state["_ai_remember_gen"] = st.session_state.get("_ai_remember_gen", 0) + 1


def _ai_remember_forget():
    st.session_state.pop("_ai_remember_payload", None)
    st.session_state["_ai_remember_loaded"] = False
    st.session_state["_ai_remember_clear"] = True
    _ai_remember_bump()


def _ai_remember_sync():
    """예약된 AI 키 저장/삭제를 브라우저에 반영한다. 매 화면 정확히 한 번 호출된다."""
    import json, hashlib
    gen = st.session_state.get("_ai_remember_gen", 0)
    if st.session_state.get("_ai_remember_clear"):
        _js_eval(f"localStorage.removeItem('{_AI_REMEMBER_KEY}') || 'ok'", key=f"ssa_ai_clear_{gen}")
    p = st.session_state.get("_ai_remember_payload")
    if p:
        payload = json.dumps(p, sort_keys=True)
        tag = hashlib.sha1(payload.encode()).hexdigest()[:10]
        _js_eval(f"localStorage.setItem('{_AI_REMEMBER_KEY}', {json.dumps(payload)}) || 'ok'",
                 key=f"ssa_ai_save_{gen}_{tag}")


def _ai_remember_load():
    """접속 시 한 번: 이 기기에 기억한 AI 연결(제공사·키·모델)을 불러온다."""
    import json
    if st.session_state.get("_ai_remember_tried") or st.session_state.get("_ai_remember_clear"):
        return
    if st.session_state.get("api_key"):
        st.session_state["_ai_remember_tried"] = True
        return
    raw = _js_eval(f"localStorage.getItem('{_AI_REMEMBER_KEY}') || ''", key="ssa_ai_read")
    if raw is None:
        return
    st.session_state["_ai_remember_tried"] = True
    try:
        data = json.loads(raw) if raw else {}
    except Exception:
        data = {}
    if data.get("key") and data.get("provider") in _AI_PROVIDERS:
        st.session_state["ai_provider"] = data["provider"]
        st.session_state["api_key"] = data["key"]
        if data.get("model"):
            st.session_state["ai_model_g"] = data["model"]
        st.session_state["_ai_remember_loaded"] = True
        st.session_state["ai_remember_on"] = True


def _ai_remember_widget():
    """'이 기기에 API 키 기억' 체크박스. AI 연결 설정·음성 입력 화면에서 사용."""
    if not _HAS_JS_EVAL:
        return
    st.session_state.setdefault("ai_remember_on", bool(st.session_state.get("_ai_remember_loaded")))
    on = st.checkbox("이 기기에 API 키 기억", key="ai_remember_on",
                     help="체크하면 이 브라우저에만 키가 저장되어 다음에 다시 입력하지 않아도 됩니다. "
                          "로그아웃하면 지워집니다. 공용 PC에서는 체크하지 마세요.")
    if on and st.session_state.get("api_key"):
        st.session_state["_ai_remember_payload"] = {
            "provider": st.session_state.get("ai_provider"),
            "key": st.session_state.get("api_key"),
            "model": st.session_state.get("ai_model_g")}
        st.session_state.pop("_ai_remember_clear", None)
    elif not on and (st.session_state.get("_ai_remember_payload")
                     or st.session_state.get("_ai_remember_loaded")):
        _ai_remember_forget()


def _try_remembered_login(cfg):
    """접속 시 한 번만: 저장된 토큰이 있으면 비밀번호 없이 로그인시킨다."""
    if st.session_state.get("_auth_remember_tried") or st.session_state.get("_auth_remember_clear"):
        return False
    rt = _remember_read()
    if rt is None:                 # 브라우저 응답 대기 중 — 응답이 오면 화면이 다시 그려진다
        return False
    st.session_state["_auth_remember_tried"] = True
    if not rt:
        return False
    js, err = _fb_refresh(rt)
    if err or not js:
        if not str(err).startswith("NETWORK"):
            _remember_forget()     # 만료·정지·비밀번호 변경된 토큰은 지운다
        return False
    info, err = _fb_lookup(js.get("id_token"))
    email = str((info or {}).get("email", ""))
    if err or not info or not _email_allowed(email, cfg) or (
            cfg["verify_email"] and not info.get("emailVerified")):
        _remember_forget()
        return False
    meta = _load_profile(js.get("user_id"), email)
    if _save_auth_session({**js, "email": email}, meta):
        st.session_state["_auth_remember_rt"] = rt
        _record_login(st.session_state.get("auth_user"))
        return True
    return False


def _record_usage(action):
    """로그인 사용자가 실제 분석/보고서 기능을 실행했을 때 기관별 이용량을 남긴다."""
    user = _current_auth_user()
    if not user:
        return
    try:
        meta = user.get("user_metadata") or {}
        _fs_add("usage_events", {
            "user_id": user.get("id"), "email": user.get("email", ""),
            "name": meta.get("name", ""), "organization": meta.get("organization", ""),
            "department": meta.get("department", ""), "action": str(action)[:300],
            "used_at": _now_utc()})
    except Exception:
        pass


def _finish_login(js):
    """비밀번호 확인이 끝난 signIn 응답으로 허용·인증 여부를 확인하고 로그인시킨다."""
    cfg = _auth_config()
    email = str((js or {}).get("email", ""))
    if not _email_allowed(email, cfg):
        st.error("이용이 허용되지 않은 이메일입니다. 관리자에게 문의해 주세요.")
        return False
    if cfg["verify_email"]:
        info, err = _fb_lookup(js.get("idToken"))
        if err or not info:
            st.error(_fb_error_text(err))
            return False
        if not info.get("emailVerified"):
            st.session_state["auth_unverified"] = {"email": email, "id_token": js.get("idToken")}
            return False
    st.session_state.pop("auth_unverified", None)
    meta = _load_profile(js.get("localId"), email)
    if _save_auth_session(js, meta):
        _record_login(st.session_state.get("auth_user"))
        return True
    st.error("로그인 응답을 확인하지 못했습니다.")
    return False


def render_auth_gate():
    """AUTH_REQUIRED=true이고 Firebase가 설정된 경우 회원만 앱에 진입하게 한다."""
    cfg = _auth_config()
    _ai_remember_sync()
    if not (cfg["api_key"] and cfg["required"]):
        return True
    user = _current_auth_user()
    if not user and _try_remembered_login(cfg):
        user = _current_auth_user()
    _remember_sync()
    if user and _email_allowed(user.get("email", ""), cfg):
        return True
    if user:
        _clear_auth_session()

    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.35, 1])
    with c2:
        st.markdown("## 📊 스마트 통계 에이전트")
        st.caption("회원가입 후 연구 데이터를 쉽고 정확하게 분석하세요.")
        login_tab, signup_tab, reset_tab = st.tabs(["🔐 로그인", "✨ 회원가입", "🔑 비밀번호 찾기"])
        with login_tab:
            em = st.text_input("이메일", key="auth_login_email", autocomplete="username")
            pw = st.text_input("비밀번호", type="password", key="auth_login_pw",
                               autocomplete="current-password")
            remember = False
            if _HAS_JS_EVAL:
                remember = st.checkbox("로그인 상태 유지 (30일)", key="auth_remember",
                                       help="체크하면 이 브라우저에서는 창을 닫았다 열어도 로그인 화면 없이 바로 들어갑니다. "
                                            "사이드바의 로그아웃을 누르면 해제됩니다.")
                st.caption("⚠️ 사무실 공용 PC에서는 체크하지 마세요.")
            if st.button("로그인", type="primary", width="stretch", key="auth_login_btn"):
                if not em or not pw:
                    st.warning("이메일과 비밀번호를 입력해 주세요.")
                else:
                    with st.spinner("로그인 중..."):
                        js, err = _fb_signin(em, pw)
                    if err:
                        st.error(_fb_error_text(err))
                    elif _finish_login(js):
                        if remember:
                            st.session_state.pop("_auth_remember_clear", None)
                            _remember_bump()
                            st.session_state["_auth_remember_rt"] = st.session_state.get("auth_refresh_token", "")
                        st.rerun()
            pending = st.session_state.get("auth_unverified")
            if pending:
                st.warning(f"**{pending['email']}** 의 이메일 인증이 아직 끝나지 않았습니다. "
                           "메일함(스팸함 포함)의 인증 링크를 누른 뒤 다시 로그인해 주세요.")
                if st.button("인증 메일 다시 보내기", width="stretch", key="auth_resend_verify"):
                    _, err = _fb_send_verify(pending.get("id_token"))
                    if err:
                        st.error(_fb_error_text(err))
                    else:
                        st.success("인증 메일을 다시 보냈습니다.")

        with signup_tab:
            nm = st.text_input("이름", key="auth_name")
            em2 = st.text_input("이메일", key="auth_signup_email", autocomplete="username")
            if _allowed_hint(cfg):
                st.caption(f"기관 메일({_allowed_hint(cfg)})로 가입할 수 있습니다. "
                           "다른 메일은 관리자가 등록해야 합니다.")
            pw2 = st.text_input("비밀번호 (8자 이상)", type="password", key="auth_signup_pw",
                                autocomplete="new-password")
            org_type = st.selectbox("기관 유형", ["도·특광역시 농업기술원", "농촌진흥청/소속기관",
                                                  "시·군 농업기술센터", "대학교/연구기관",
                                                  "농업 관련 기업/단체", "기타", _NO_ORG_LABEL],
                                    key="auth_org_type")
            if org_type == _NO_ORG_LABEL:
                # 농업인·학생 등 소속이 없는 사람도 가입할 수 있게 한다(관리자 통계에서는 '개인'으로 집계).
                org, dept = _NO_ORG_VALUE, ""
                st.caption("소속기관 없이 개인으로 가입합니다.")
            else:
                _choices = _ORG_CHOICES.get(org_type)
                if _choices:
                    _pick = st.selectbox("소속기관", _choices + [_ORG_DIRECT], index=None,
                                         placeholder="소속기관을 고르세요", key="auth_org_pick")
                    if _pick == _ORG_DIRECT:
                        org = st.text_input("소속기관 이름", placeholder="예: OO도농업기술원", key="auth_org")
                    else:
                        org = _pick or ""
                else:
                    org = st.text_input("소속기관", placeholder="예: 한국농수산대학교", key="auth_org")
                dept = st.text_input("부서/연구소 (선택)", placeholder="예: 영양고추연구소", key="auth_dept")
            consent = st.checkbox("이름·이메일·소속기관 및 서비스 접속기록을 운영 목적으로 저장하는 것에 동의합니다.",
                                  key="auth_consent")
            if st.button("회원가입", type="primary", width="stretch", key="auth_signup_btn"):
                if not all([nm, em2, pw2, org]) or not consent:
                    st.warning("이름·이메일·비밀번호·소속기관과 개인정보 안내 동의를 확인해 주세요.")
                elif len(pw2) < 8:
                    st.warning("비밀번호는 8자 이상이어야 합니다.")
                elif not _email_allowed(em2, cfg):
                    _h = _allowed_hint(cfg)
                    st.error("가입이 허용되지 않은 이메일입니다."
                             + (f" 기관 메일({_h})로 가입하거나" if _h else "")
                             + " 관리자에게 등록을 요청해 주세요.")
                else:
                    with st.spinner("회원가입 중..."):
                        js, err = _fb_signup(em2, pw2)
                    if err:
                        st.error(_fb_error_text(err))
                    else:
                        token, uid = js.get("idToken"), js.get("localId")
                        _fb_set_display_name(token, nm)
                        meta = {"name": nm.strip(), "organization_type": org_type,
                                "organization": org.strip(), "department": dept.strip()}
                        _fs_set("profiles", uid, {**meta, "email": em2.strip().lower(),
                                                  "created_at": _now_utc(), "consent_at": _now_utc()})
                        if cfg["verify_email"]:
                            _, verr = _fb_send_verify(token)
                            if verr:
                                st.error("가입은 되었지만 인증 메일을 보내지 못했습니다. "
                                         "로그인 탭에서 '인증 메일 다시 보내기'를 눌러 주세요.")
                            else:
                                st.success(f"**{em2.strip()}** 로 인증 메일을 보냈습니다. "
                                           "메일의 링크를 누른 뒤 로그인해 주세요. "
                                           "메일이 안 보이면 스팸함을 확인해 주세요.")
                        elif _save_auth_session(js, meta):
                            _record_login(st.session_state.get("auth_user"))
                            st.rerun()

        with reset_tab:
            rem = st.text_input("가입한 이메일", key="auth_reset_email", autocomplete="username")
            if st.button("비밀번호 재설정 메일 보내기", width="stretch", key="auth_reset_btn"):
                if not rem:
                    st.warning("이메일을 입력해 주세요.")
                else:
                    _, err = _fb_send_reset(rem)
                    code = _fb_error_code(err)
                    # 가입 여부를 드러내지 않도록 '없는 이메일'도 성공과 같은 안내를 보여 준다.
                    if err and code not in ("EMAIL_NOT_FOUND", "USER_NOT_FOUND"):
                        st.error(_fb_error_text(err))
                    else:
                        st.success("가입된 이메일이면 재설정 메일이 발송됩니다. 메일의 링크에서 새 비밀번호를 "
                                   "정한 뒤 로그인해 주세요. 메일이 안 보이면 스팸함을 확인해 주세요.")
        st.caption("🔒 비밀번호는 이 앱이 저장하지 않고 Google Firebase 인증이 처리합니다.")
        st.caption("📂 올린 분석 자료는 분석하는 동안만 서버 메모리에 있고 저장되지 않습니다. "
                   "AI 기능을 쓸 때만 해당 내용이 선택한 AI 회사로 전송됩니다. "
                   "미공개 자료는 소속 기관의 정보보안 지침을 확인한 뒤 사용해 주세요.")
        st.caption(f"📮 가입·로그인 문의: {CONTACT_NAME} · [{CONTACT_EMAIL}](mailto:{CONTACT_EMAIL})")
    st.stop()


def _is_admin_user(user=None):
    user = user or _current_auth_user()
    email = str((user or {}).get("email", "")).lower()
    return bool(email and email in _auth_config()["admins"])


def _to_kst_text(series):
    t = pd.to_datetime(series, errors="coerce", utc=True)
    return t.dt.tz_convert("Asia/Seoul").dt.strftime("%Y-%m-%d %H:%M").fillna("")


def render_admin_dashboard():
    st.title("👑 관리자 — 이용 현황")
    if not _is_admin_user():
        st.error("관리자 계정만 접근할 수 있습니다.")
        return
    if _fs_session() is None:
        st.warning("Firestore 서비스 계정(firebase_service_account)이 설정되어야 관리자 통계를 볼 수 있습니다.")
        return
    # Firestore 무료 요금제는 하루 읽기 5만 건이다. 이 화면은 한 번에 최대 2만 건을 읽으므로
    # 불러온 결과를 30분 동안 이 창에 보관하고, 새로고침 버튼을 눌렀을 때만 다시 읽는다.
    import time as _time
    _cache = st.session_state.get("_auth_admin_cache")
    _hc1, _hc2 = st.columns([3, 1])
    _refresh = _hc2.button("🔄 새로고침", key="auth_admin_refresh", width="stretch")
    if _refresh or not _cache or _time.time() - _cache[0] > 1800:
        with st.spinner("이용 기록을 불러오는 중..."):
            _data = (_fs_list("profiles", 5000),
                     _fs_recent("login_events", "logged_in_at", 5000),
                     _fs_recent("usage_events", "used_at", 10000))
        _cache = (_time.time(), _data)
        if not _data[0][1]:                        # 회원 목록을 못 읽었으면 보관하지 않는다
            st.session_state["_auth_admin_cache"] = _cache
    (profiles, e1), (events, e2), (usage, e3) = _cache[1]
    _hc1.caption(f"불러온 시각: {pd.Timestamp(_cache[0], unit='s', tz='Asia/Seoul'):%m-%d %H:%M} · "
                 "무료 사용량을 아끼려고 30분 동안은 다시 읽지 않습니다.")
    if e1:
        st.error(f"회원 목록을 불러오지 못했습니다: {e1}")
        return
    p = pd.DataFrame(profiles or [])
    ev = pd.DataFrame(events or [])
    uv = pd.DataFrame(usage or [])
    if not p.empty and "last_login_at" in p:
        p = p.sort_values("last_login_at", ascending=False, na_position="last")
    for df_, col in ((p, "last_login_at"), (p, "created_at"), (ev, "logged_in_at"), (uv, "used_at")):
        if not df_.empty and col in df_:
            df_[col] = _to_kst_text(df_[col])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("가입 사용자", f"{len(p):,}명")
    c2.metric("확인된 소속기관", f"{p['organization'].fillna('').map(_org_canonical).replace('', np.nan).nunique() if 'organization' in p else 0:,}곳")
    c3.metric("로그인 기록", f"{len(ev):,}회")
    c4.metric("기능 이용 기록", f"{len(uv):,}회")
    if not p.empty and "organization" in p:
        st.markdown("### 🏢 기관별 사용자")
        g = (p.assign(소속기관=p["organization"].fillna("").map(_org_canonical).replace("", "미입력"))
               .groupby("소속기관", dropna=False).size().reset_index(name="사용자 수")
               .sort_values("사용자 수", ascending=False))
        smart_table(g, width="stretch", hide_index=True)
    if not p.empty:
        st.markdown("### 👥 사용자 목록")
        cols = [c for c in ["name", "email", "organization_type", "organization", "department",
                            "created_at", "last_login_at"] if c in p]
        show = p[cols].rename(columns={"name": "이름", "email": "이메일", "organization_type": "기관유형",
                                       "organization": "소속기관", "department": "부서",
                                       "created_at": "가입일", "last_login_at": "최근 로그인"})
        smart_table(show, width="stretch", hide_index=True)
        st.download_button("📊 사용자 목록 Excel", dataframe_to_styled_xlsx(show, "스마트 통계 에이전트 사용자 목록"),
                           "사용자목록.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if e3:
        st.caption(f"기능 이용 기록을 불러오지 못했습니다: {e3}")
    if not uv.empty:
        st.markdown("### 📈 기관별 기능 이용")
        _orguse = (uv.assign(소속기관=uv.get("organization", pd.Series(index=uv.index, dtype=object)).fillna("").map(_org_canonical).replace("", "미입력"))
                     .groupby("소속기관", dropna=False).size().reset_index(name="기능 이용 횟수")
                     .sort_values("기능 이용 횟수", ascending=False))
        smart_table(_orguse, width="stretch", hide_index=True)
        st.markdown("### 🧭 최근 기능 이용 기록")
        _ucols = [c for c in ["used_at", "name", "email", "organization", "department", "action"] if c in uv]
        _ushow = uv[_ucols].head(500).rename(columns={"used_at": "이용시각", "name": "이름", "email": "이메일",
                                                        "organization": "소속기관", "department": "부서", "action": "기능"})
        smart_table(_ushow, width="stretch", hide_index=True)
    if e2:
        st.caption(f"로그인 기록을 불러오지 못했습니다: {e2}")
    if not ev.empty:
        st.markdown("### 🕘 최근 로그인")
        cols = [c for c in ["logged_in_at", "name", "email", "organization", "department"] if c in ev]
        show2 = ev[cols].head(300).rename(columns={"logged_in_at": "접속시각", "name": "이름", "email": "이메일",
                                                   "organization": "소속기관", "department": "부서"})
        smart_table(show2, width="stretch", hide_index=True)

# ---------------------------------------------------------------- AI 호출
_AI_SYS = (
    "당신은 농촌진흥청 및 도 농업기술원의 수석 응용통계 전문가입니다. "
    "농업 시험연구보고서와 농학 논문 작성을 20년간 지원해 왔습니다.\n\n"
    "【통계 해석 지침】\n"
    "- p-value: 단순히 '유의하다'로 끝내지 말고, 처리가 실제 생육·수량 반응으로 이어졌는지를 "
    "농학적으로 서술합니다. p<0.05는 '처리 간 차이가 우연으로 보기 어렵다'는 의미이며, "
    "p>=0.05는 '차이가 관찰되었더라도 오차 범위 내'임을 분명히 밝힙니다.\n"
    "- 자유도(df): 반복수·처리수와 연결해 시험 규모의 타당성을 언급합니다.\n"
    "- 변이계수(CV%): 포장시험 정밀도 지표로 해석합니다. 10% 미만 매우 우수, "
    "10~20% 양호, 20% 초과 시 포장 불균일·조사 오차 가능성을 지적합니다.\n"
    "- 사후검정 문자(a, b, c): 같은 문자를 공유하면 통계적으로 동등한 수준임을 뜻합니다. "
    "'ab'처럼 두 군에 걸친 처리는 중간 수준으로 해석합니다.\n"
    "- LSD: 두 평균의 차이가 이 값보다 클 때 유의하다고 서술합니다.\n\n"
    "【농학적 연결】\n"
    "- 수량 증가는 초장·엽수·생체중 등 생육 형질의 변화와 연결해 설명합니다.\n"
    "- 통계적 유의성과 농업적 실용성(증수량이 농가 소득에 미치는 영향)을 구분해 서술합니다.\n"
    "- 확인할 수 없는 원인(품종 특성, 기상, 토양)은 단정하지 말고 '~로 추정된다'로 씁니다.\n\n"
    "【서식 규칙】\n"
    "- 농촌진흥청 시험연구보고서 양식을 따릅니다. 주요 항목은 '○ ', 세부 항목은 '  - '로 시작합니다.\n"
    "- 마크다운 기호(**, ##, *, `, ---)는 절대 사용하지 않습니다. 평문으로만 작성합니다.\n"
    "- 문체는 '~하였다', '~로 나타났다', '~인 것으로 판단된다'를 사용합니다.\n"
    "- 표에 없는 수치나 사실은 만들어 내지 않습니다.\n\n"
    "【반드시 지킬 규칙】\n"
    "1. 제공된 JSON에 없는 숫자·처리명·p값·출처·원인을 만들어 내지 않습니다.\n"
    "2. 검정을 수행하지 않은 결과에 'p<0.05' 같은 표현을 붙이지 않습니다. "
    "yield_statistical_test.p_value가 null이면 유의성을 단정하지 않습니다.\n"
    "3. 통계적 유의성과 농업적·경제적 중요성을 구분해 서술합니다.\n"
    "4. 인과관계가 확인되지 않았으면 원인을 단정하지 않습니다('~로 추정된다').\n"
    "5. 입력 근거가 부족하면 '제공된 결과만으로는 판단할 수 없다'고 답합니다.\n"
    "6. 기준연도가 오래된 가격은 최신값처럼 표현하지 않고 기준연도를 함께 밝힙니다.\n"
    "7. 계산 결과와 서술이 어긋나면 계산 결과를 우선합니다.")

# AI 모델 목록 — 환경변수나 models.txt로 덮어쓸 수 있음(새 모델 나오면 코드 수정 불필요)
#   · 환경변수 예)  AI_MODELS_GEMINI="gemini-2.5-flash,gemini-2.5-pro"
#   · 또는 app.py 옆에 models.txt 파일:  gemini=gemini-2.5-flash,gemini-2.5-pro
_AI_PROVIDERS_BASE = {
    "Claude (Anthropic)": {
        "key": "claude",
        "models": ["claude-haiku-4-5-20251001", "claude-sonnet-5"],
        "key_hint": "console.anthropic.com 에서 발급 (sk-ant-...)"},
    "Gemini (Google)": {
        "key": "gemini",
        "models": ["gemini-3.6-flash", "gemini-3.5-flash"],
        "key_hint": "aistudio.google.com 에서 발급 (AIza...)"},
    "ChatGPT (OpenAI)": {
        "key": "openai",
        "models": ["gpt-5-mini", "gpt-5.1"],
        "key_hint": "platform.openai.com 에서 발급 (sk-...)"},
}

def _load_model_overrides():
    """환경변수·models.txt에서 모델 목록을 읽어 덮어씀"""
    import os
    over = {}
    for name, cfg in _AI_PROVIDERS_BASE.items():
        env = os.environ.get(f"AI_MODELS_{cfg['key'].upper()}")
        if env:
            over[cfg["key"]] = [m.strip() for m in env.split(",") if m.strip()]
    try:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models.txt")
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    ms = [m.strip() for m in v.split(",") if m.strip()]
                    if ms: over[k.strip().lower()] = ms
    except Exception:
        pass
    return over

def build_ai_providers():
    over = _load_model_overrides()
    out = {}
    for name, cfg in _AI_PROVIDERS_BASE.items():
        models = over.get(cfg["key"], cfg["models"])
        out[name] = {**cfg, "models": list(models)}
    return out

_AI_PROVIDERS = build_ai_providers()

def test_ai_connection(provider, api_key, model):
    """API 연결을 짧게 확인. 반환: dict(ok, provider, model, message, sample).

    Streamlit 위젯 key인 ``ai_provider``는 위젯이 생성된 뒤 수정할 수 없으므로,
    연결 테스트에서는 세션 상태를 바꾸지 않고 provider를 ai_call에 직접 전달한다.
    """
    out = {"ok": False, "provider": provider.split()[0], "model": model or "(미지정)",
           "message": "", "sample": ""}
    if not api_key:
        out["message"] = "API 키가 비어 있습니다."
        return out
    if not model:
        out["message"] = "모델명을 지정해 주세요."
        return out
    # GPT-5 계열은 max_output_tokens 안에 보이지 않는 추론 토큰도 포함됩니다.
    # 20토큰처럼 너무 작게 잡으면 인증은 성공해도 추론 예산을 모두 써서
    # 실제 텍스트가 비어 있을 수 있으므로 연결 테스트에는 넉넉한 예산을 둡니다.
    r = ai_call("연결 테스트입니다. '확인'이라고만 답하세요.",
                api_key=api_key, model=model, max_tokens=512,
                system="한 단어로만 답하세요.", provider=provider)
    if isinstance(r, str) and r.startswith("⚠️"):
        low = r.lower()
        if "401" in r or "auth" in low or "unauthor" in low or "api key" in low:
            out["message"] = "인증 실패 — API 키를 다시 확인해 주세요."
        elif "404" in r or "not found" in low or "model" in low:
            out["message"] = f"모델 '{model}'을(를) 찾을 수 없습니다. 모델명을 확인해 주세요."
        elif "429" in r or "rate" in low or "quota" in low:
            out["message"] = "사용량 한도에 걸렸습니다. 잠시 후 다시 시도해 주세요."
        elif "timeout" in low or "timed out" in low:
            out["message"] = "응답 시간이 초과되었습니다. 네트워크를 확인해 주세요."
        elif "500" in r or "502" in r or "503" in r:
            out["message"] = "제공사 서버 오류입니다. 잠시 후 다시 시도해 주세요."
        else:
            out["message"] = r.replace("⚠️", "").strip()[:120]
        return out
    if not str(r).strip():
        out["message"] = "응답이 비어 있습니다(안전 필터 차단 가능성)."
        return out
    out["ok"] = True
    out["message"] = "정상"
    out["sample"] = str(r).strip()
    return out


def _ai_mask(text, api_key):
    """오류 메시지에 API 키가 섞여 나가지 않도록 제거"""
    t = str(text)
    if api_key:
        t = t.replace(str(api_key), "***")
        if len(str(api_key)) > 8:
            t = t.replace(str(api_key)[:8], "***")
    return t


def _ai_http(method_fn, *args, api_key=None, retries=2, **kw):
    """HTTP 호출 + 제한적 재시도(429·5xx만, 최대 2회). 무한 재시도 없음."""
    import time
    last = None
    for attempt in range(retries + 1):
        try:
            r = method_fn(*args, **kw)
        except Exception as ex:
            last = ("exception", f"{type(ex).__name__}")
            if attempt < retries:
                time.sleep(1.0 * (attempt + 1))
                continue
            return None, f"네트워크 오류({last[1]}) — 연결을 확인해 주세요."
        if r.status_code == 200:
            return r, None
        if r.status_code == 429 and attempt < retries:
            time.sleep(2.0 * (attempt + 1))      # 짧은 backoff
            continue
        if 500 <= r.status_code < 600 and attempt < retries:
            time.sleep(1.5 * (attempt + 1))
            continue
        return None, _ai_error_message(r.status_code,
                                       _ai_mask(getattr(r, "text", ""), api_key))
    return None, "요청이 반복 실패했습니다. 잠시 후 다시 시도해 주세요."


def _ai_error_message(code, body=""):
    """HTTP 상태코드를 사용자 친화적 메시지로"""
    b = str(body)[:160]
    if code in (401, 403):
        return f"⚠️ 인증 실패({code}) — API 키를 다시 확인해 주세요."
    if code == 404:
        return f"⚠️ 모델을 찾을 수 없습니다({code}) — 모델명을 확인해 주세요."
    if code == 429:
        return f"⚠️ 사용량 한도 초과({code}) — 잠시 후 다시 시도해 주세요."
    if code == 400:
        return f"⚠️ 요청 형식 오류({code}): {b}"
    if 500 <= code < 600:
        return f"⚠️ 제공사 서버 오류({code}) — 잠시 후 다시 시도해 주세요."
    return f"⚠️ 호출 실패({code}): {b}"


def call_claude(prompt, api_key, model, max_tokens=900, system=None, timeout=60):
    """Claude(Anthropic) 호출"""
    if not _HAS_ANTHROPIC:
        return "⚠️ anthropic 라이브러리가 없습니다. (pip install anthropic)"
    try:
        client = anthropic.Anthropic(api_key=api_key, timeout=timeout, max_retries=2)
        msg = client.messages.create(
            model=model, max_tokens=max_tokens, system=system or _AI_SYS,
            messages=[{"role": "user", "content": prompt}])
        parts = [getattr(b, "text", "") for b in getattr(msg, "content", [])
                 if getattr(b, "type", "") == "text"]
        text = "".join(parts).strip()
        if not text:
            return "⚠️ 응답이 비어 있습니다(안전 필터 차단 또는 토큰 부족 가능성)."
        return text
    except Exception as ex:
        msg = _ai_mask(f"{type(ex).__name__}: {ex}", api_key)
        low = msg.lower()
        if "authentication" in low or "401" in msg or "api key" in low:
            return "⚠️ 인증 실패 — API 키를 다시 확인해 주세요."
        if "not_found" in low or "404" in msg or "model" in low:
            return f"⚠️ 모델 '{model}'을(를) 찾을 수 없습니다."
        if "rate" in low or "429" in msg:
            return "⚠️ 사용량 한도 초과 — 잠시 후 다시 시도해 주세요."
        if "timeout" in low:
            return "⚠️ 응답 시간이 초과되었습니다."
        return f"⚠️ Claude 호출 오류: {msg[:150]}"


def list_gemini_models(api_key, timeout=20):
    """현재 키로 generateContent를 지원하는 Gemini 모델 목록을 조회한다."""
    if not _HAS_REQUESTS:
        return [], "requests 라이브러리가 없습니다."
    r, err = _ai_http(_requests.get,
                      "https://generativelanguage.googleapis.com/v1beta/models",
                      api_key=api_key, headers={"x-goog-api-key": api_key},
                      params={"pageSize": 1000}, timeout=timeout, retries=1)
    if err:
        return [], err
    try:
        js = r.json()
    except Exception:
        return [], "Gemini 모델 목록 응답을 해석하지 못했습니다."
    out = []
    for item in js.get("models") or []:
        actions = item.get("supportedGenerationMethods") or item.get("supportedActions") or []
        if "generateContent" not in actions:
            continue
        name = str(item.get("name", "")).replace("models/", "", 1)
        if name and name not in out:
            out.append(name)
    return out, None


def list_openai_models(api_key, timeout=20):
    """현재 키에 열려 있는 텍스트 생성용 OpenAI 모델 후보를 조회한다."""
    if not _HAS_REQUESTS:
        return [], "requests 라이브러리가 없습니다."
    r, err = _ai_http(
        _requests.get, "https://api.openai.com/v1/models", api_key=api_key,
        headers={"Authorization": f"Bearer {api_key}"}, timeout=timeout, retries=1)
    if err:
        return [], err
    try:
        data = r.json().get("data") or []
    except Exception:
        return [], "OpenAI 모델 목록 응답을 해석하지 못했습니다."
    excluded = ("audio", "realtime", "transcribe", "tts", "image", "search",
                "chatgpt", "codex", "embedding", "moderation")
    allowed_prefix = ("gpt-5", "gpt-4.1", "gpt-4o", "o3", "o4")
    models = []
    for item in data:
        mid = str((item or {}).get("id", ""))
        low = mid.lower()
        if mid.startswith(allowed_prefix) and not any(x in low for x in excluded):
            models.append(mid)
    # 날짜 고정 스냅샷보다 일반 별칭을 우선 표시한다.
    models = sorted(set(models), key=lambda x: (x.count("-"), len(x), x))
    return models, None


def list_claude_models(api_key, timeout=20):
    """현재 키에 열려 있는 Claude 모델 목록을 조회한다."""
    if not _HAS_REQUESTS:
        return [], "requests 라이브러리가 없습니다."
    r, err = _ai_http(
        _requests.get, "https://api.anthropic.com/v1/models", api_key=api_key,
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01"},
        params={"limit": 100}, timeout=timeout, retries=1)
    if err:
        return [], err
    try:
        data = r.json().get("data") or []
    except Exception:
        return [], "Claude 모델 목록 응답을 해석하지 못했습니다."
    models = [str((item or {}).get("id", "")) for item in data
              if str((item or {}).get("id", "")).startswith("claude-")]
    return list(dict.fromkeys(m for m in models if m)), None


def call_gemini(prompt, api_key, model, max_tokens=900, system=None, timeout=60):
    """Gemini(Google) 호출 — 인증키를 URL이 아닌 헤더로 전달"""
    if not _HAS_REQUESTS:
        return "⚠️ requests 라이브러리가 없습니다. (pip install requests)"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {"contents": [{"parts": [{"text": prompt}]}],
               "generationConfig": {"maxOutputTokens": max_tokens}}
    if system:
        payload["systemInstruction"] = {"parts": [{"text": system}]}
    headers = {"x-goog-api-key": api_key, "Content-Type": "application/json"}
    r, err = _ai_http(_requests.post, url, api_key=api_key,
                      json=payload, headers=headers, timeout=timeout)
    if err:
        return err
    try:
        js = r.json()
    except Exception:
        return "⚠️ Gemini 응답을 해석하지 못했습니다."
    cands = js.get("candidates") or []
    if not cands:
        fb = (js.get("promptFeedback") or {}).get("blockReason")
        if fb:
            return f"⚠️ 안전 필터에 차단되었습니다(사유: {fb})."
        return "⚠️ Gemini 응답이 비어 있습니다."
    parts = ((cands[0] or {}).get("content") or {}).get("parts") or []
    text = "".join(p.get("text", "") for p in parts if isinstance(p, dict)).strip()
    if not text:
        fr = (cands[0] or {}).get("finishReason", "")
        return f"⚠️ Gemini 응답이 비어 있습니다{f'(사유: {fr})' if fr else ''}."
    return text


def call_openai(prompt, api_key, model, max_tokens=900, system=None, timeout=60):
    """OpenAI Responses API 호출. 결과 배열 구조가 달라도 텍스트를 안전하게 추출한다."""
    if not _HAS_REQUESTS:
        return "⚠️ requests 라이브러리가 없습니다. (pip install requests)"
    import re as _re
    requested_tokens = max(1, int(max_tokens))
    model_l = str(model).lower()
    is_gpt5 = model_l.startswith("gpt-5")
    # gpt-5.1, gpt-5.2 처럼 '점(.)'이 붙은 버전은 reasoning.effort로 minimal을 지원하지
    # 않거나(모델에 따라 오류) 권장하지 않는다 — OpenAI는 GPT-5.1부터 'none'을 새로 추가하고
    # 이를 기본값·권장값으로 안내한다. 점 없는 gpt-5(-mini/-nano 포함)는 계속 minimal을 쓴다.
    is_gpt51_plus = bool(_re.match(r"gpt-5\.\d", model_l))
    # Responses API의 max_output_tokens는 화면에 보이는 답변뿐 아니라 추론 토큰도 포함합니다.
    # GPT-5 계열에서 너무 작은 값은 status=incomplete / reason=max_output_tokens와
    # 빈 output_text를 만들 수 있으므로 최소 예산과 낮은 추론 강도를 적용합니다.
    output_budget = max(requested_tokens, 512) if is_gpt5 else requested_tokens
    payload = {"model": model, "input": prompt,
               "max_output_tokens": output_budget, "store": False}
    if is_gpt51_plus:
        payload["reasoning"] = {"effort": "none"}
    elif is_gpt5:
        payload["reasoning"] = {"effort": "minimal"}
    if system:
        payload["instructions"] = system
    r, err = _ai_http(
        _requests.post, "https://api.openai.com/v1/responses", api_key=api_key,
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": "application/json"},
        json=payload, timeout=timeout)
    if err:
        return err
    try:
        js = r.json()
    except Exception:
        return "⚠️ ChatGPT 응답을 해석하지 못했습니다."
    text = str(js.get("output_text") or "").strip()
    if not text:
        parts = []
        for item in js.get("output") or []:
            if not isinstance(item, dict):
                continue
            for content in item.get("content") or []:
                if not isinstance(content, dict):
                    continue
                if content.get("type") in ("output_text", "text"):
                    value = content.get("text", "")
                    if isinstance(value, dict):
                        value = value.get("value", "")
                    if value:
                        parts.append(str(value))
        text = "".join(parts).strip()
    if not text:
        status = js.get("status", "")
        incomplete = (js.get("incomplete_details") or {}).get("reason", "")
        suffix = incomplete or status
        if incomplete == "max_output_tokens":
            return ("⚠️ ChatGPT가 답변 토큰 한도에 도달했습니다. "
                    "연결 자체는 성공했지만 출력 예산이 부족했습니다. 다시 시도해 주세요.")
        return f"⚠️ ChatGPT 응답이 비어 있습니다{f'(사유: {suffix})' if suffix else ''}."
    return text


_AI_DISPATCH = {"Claude": call_claude, "Gemini": call_gemini, "ChatGPT": call_openai}


def ai_call(prompt, api_key=None, model=None, max_tokens=900, system=None, provider=None):
    """제공사별 함수로 분기.

    provider가 전달되면 해당 값을 우선 사용하고, 일반 분석 호출에서는
    사이드바에서 고른 제공사를 사용한다. 위젯 생성 뒤 session_state를 수정하지 않는다.
    """
    provider = provider or st.session_state.get("ai_provider", "Claude (Anthropic)")
    api_key = api_key or st.session_state.get("api_key")
    model = model or st.session_state.get("ai_model_g")
    system = system or _AI_SYS
    if not api_key:
        return "⚠️ AI 도우미에서 API 키를 연결하면 AI 해석을 사용할 수 있어요."
    if not model:
        return "⚠️ 모델명이 지정되지 않았습니다. 사이드바에서 모델을 선택해 주세요."
    fn = None
    for key, f in _AI_DISPATCH.items():
        if str(provider).startswith(key):
            fn = f
            break
    if fn is None:
        return "⚠️ 알 수 없는 AI 제공사입니다."
    return fn(prompt, api_key, model, max_tokens=max_tokens, system=system)


def ai_job_run(slot, prompt=None, max_tokens=900, spinner="AI가 답변을 만드는 중..."):
    """AI 질문을 '대기 → 답 저장 → 화면 표시' 순서로 처리한다.

    버튼을 누른 실행이 중간에 다시 그려지면(브라우저 저장소 부품이 값을 보내는 경우 등)
    화면에 바로 그린 답은 사라진다. 그래서 질문을 먼저 세션에 넣고, 답을 받는 즉시
    세션에 저장한 뒤, 세션에 있는 답을 그린다. prompt를 주면 새 질문으로 등록한다.
    반환: 답 문자열(없으면 None)
    """
    k = f"ai_job_{slot}"
    if prompt is not None:
        st.session_state[k] = {"prompt": prompt, "max_tokens": max_tokens,
                               "data": st.session_state.get("cur_key"), "ans": None}
    job = st.session_state.get(k)
    if not job or job.get("data") != st.session_state.get("cur_key"):
        return None
    if job.get("ans") is None:
        with st.spinner(spinner):
            try:
                ans = ai_call(job["prompt"], st.session_state.get("api_key"),
                              st.session_state.get("ai_model_g"), max_tokens=job["max_tokens"])
            except Exception as ex:
                ans = f"⚠️ AI 호출 실패: {type(ex).__name__}: {ex}"
            # 다른 화면 요소를 그리기 전에 바로 저장한다(이후 실행이 끊겨도 답이 남는다).
            job["ans"] = ans if str(ans or "").strip() else "⚠️ AI 응답이 비어 있습니다. 다시 시도해 주세요."
            st.session_state[k] = job
    return job["ans"]


# ================================================================ 이미지/음성 데이터 입력

def _extract_ai_text_from_openai_response(js):
    txt = str((js or {}).get("output_text") or "").strip()
    if txt:
        return txt
    parts = []
    for item in (js or {}).get("output") or []:
        if not isinstance(item, dict):
            continue
        for c in item.get("content") or []:
            if isinstance(c, dict) and c.get("type") in ("output_text", "text"):
                v = c.get("text", "")
                if isinstance(v, dict): v = v.get("value", "")
                if v: parts.append(str(v))
    return "".join(parts).strip()


def ai_multimodal_text(binary, mime_type, prompt, kind="image"):
    """AI 도우미에서 선택한 AI 제공사로 이미지/오디오를 읽어 텍스트를 반환."""
    import base64
    provider = st.session_state.get("ai_provider", "Claude (Anthropic)")
    api_key = st.session_state.get("api_key")
    model = st.session_state.get("ai_model_g")
    if not api_key or not model:
        return "⚠️ 먼저 `🧠 AI 도우미 → AI 연결 설정`에서 API 키와 모델을 설정해 주세요."
    if not _HAS_REQUESTS:
        return "⚠️ requests 라이브러리가 필요합니다."
    b64 = base64.b64encode(binary).decode("ascii")

    # Claude: 현재 모델은 이미지 입력 지원. 오디오는 직접 입력 미지원이므로 안내.
    if str(provider).startswith("Claude"):
        if kind == "audio":
            return "⚠️ Claude 선택 상태에서는 음성 전사를 지원하지 않습니다. ChatGPT 또는 Gemini를 선택해 주세요."
        try:
            client = anthropic.Anthropic(api_key=api_key, timeout=90, max_retries=2)
            msg = client.messages.create(
                model=model, max_tokens=4000,
                messages=[{"role":"user","content":[
                    {"type":"image", "source":{"type":"base64", "media_type":mime_type, "data":b64}},
                    {"type":"text", "text":prompt},
                ]}])
            return "".join(getattr(x, "text", "") for x in msg.content if getattr(x, "type", "") == "text").strip()
        except Exception as ex:
            return f"⚠️ 이미지 인식 오류: {_ai_mask(str(ex), api_key)[:160]}"

    if str(provider).startswith("Gemini"):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload = {"contents":[{"parts":[
            {"inline_data":{"mime_type":mime_type, "data":b64}}, {"text":prompt}
        ]}], "generationConfig":{"maxOutputTokens":4000}}
        r, err = _ai_http(_requests.post, url, api_key=api_key,
                          headers={"x-goog-api-key":api_key, "Content-Type":"application/json"},
                          json=payload, timeout=100)
        if err: return err
        try:
            parts = (((r.json().get("candidates") or [])[0].get("content") or {}).get("parts") or [])
            return "".join(p.get("text", "") for p in parts if isinstance(p, dict)).strip()
        except Exception:
            return "⚠️ Gemini 멀티모달 응답을 읽지 못했습니다."

    # OpenAI: image는 Responses API, audio는 공식 Transcriptions API.
    if str(provider).startswith("ChatGPT"):
        if kind == "audio":
            try:
                files = {"file": ("voice.wav", binary, mime_type or "audio/wav")}
                data = {"model": "gpt-transcribe",
                        "prompt": "한국어 농업 시험 조사 데이터입니다. 처리구, 반복, 초장, 수량, 과장, 과폭 등 숫자와 단위를 정확히 전사하세요."}
                r = _requests.post("https://api.openai.com/v1/audio/transcriptions",
                                   headers={"Authorization": f"Bearer {api_key}"},
                                   files=files, data=data, timeout=100)
                if r.status_code != 200:
                    return _ai_error_message(r.status_code, _ai_mask(r.text, api_key))
                return str((r.json() or {}).get("text") or "").strip()
            except Exception as ex:
                return f"⚠️ 음성 전사 오류: {_ai_mask(str(ex), api_key)[:160]}"
        try:
            payload = {
                "model": model, "store": False, "max_output_tokens": 4000,
                "input":[{"role":"user","content":[
                    {"type":"input_text", "text":prompt},
                    {"type":"input_image", "image_url":f"data:{mime_type};base64,{b64}"},
                ]}]
            }
            r, err = _ai_http(_requests.post, "https://api.openai.com/v1/responses", api_key=api_key,
                              headers={"Authorization":f"Bearer {api_key}", "Content-Type":"application/json"},
                              json=payload, timeout=100)
            if err: return err
            return _extract_ai_text_from_openai_response(r.json())
        except Exception as ex:
            return f"⚠️ 이미지 인식 오류: {_ai_mask(str(ex), api_key)[:160]}"
    return "⚠️ 지원하지 않는 AI 제공사입니다."


def _json_from_ai_text(text):
    import json, re
    if not text or str(text).startswith("⚠️"):
        return None
    t = str(text).strip()
    t = re.sub(r"^```(?:json)?\\s*", "", t, flags=re.I)
    t = re.sub(r"\\s*```$", "", t)
    # 앞뒤 설명이 붙어도 첫 JSON object/array를 최대한 복원
    candidates = [t]
    for left, right in (("{", "}"), ("[", "]")):
        if left in t and right in t:
            candidates.append(t[t.find(left):t.rfind(right)+1])
    for c in candidates:
        try:
            return json.loads(c)
        except Exception:
            pass
    return None


def image_to_dataframe(binary, mime_type):
    prompt = """이 이미지는 연구/조사 데이터 표입니다. 표의 글자와 숫자를 그대로 읽어 구조화하세요.
반드시 JSON만 출력하세요. 형식:
{"columns":["열1","열2"],"rows":[[값,값],[값,값]],"warnings":["애매한 셀 설명"]}
규칙: 1) 보이지 않는 값을 추측하지 말고 null, 2) 소수점/음수/단위를 특히 정확히, 3) 병합 머리글은 의미가 보존되도록 한 줄 열 이름으로 합치기, 4) 표가 여러 개면 가장 큰 데이터 표 하나를 우선."""
    raw = ai_multimodal_text(binary, mime_type, prompt, kind="image")
    js = _json_from_ai_text(raw)
    if not isinstance(js, dict):
        return None, [raw if raw else "표를 구조화하지 못했습니다."]
    cols, rows = js.get("columns") or [], js.get("rows") or []
    if not cols or not isinstance(rows, list):
        return None, ["열 또는 행을 찾지 못했습니다."]
    fixed = []
    for r in rows:
        if isinstance(r, dict):
            fixed.append([r.get(c) for c in cols])
        elif isinstance(r, list):
            fixed.append((r + [None] * len(cols))[:len(cols)])
    return clean_columns(pd.DataFrame(fixed, columns=cols)), list(js.get("warnings") or [])


# ---------------------------------------------------------------- 음성 문장 → 행 (AI 없이 규칙으로)
# "처리구 A, 반복 1, 초장 72.3, 수량 육백십오 점 사" 같은 문장에서 열 이름 뒤의 값을 바로 뽑는다.
# 실시간 받아쓰기 화면의 자바스크립트(_VOICE_LIVE_HTML 안 VP)와 같은 규칙이며,
# tests/test_voice_live.py가 두 쪽 결과가 같은지 확인한다.
_VP_DIG = {"영": 0, "공": 0, "일": 1, "이": 2, "삼": 3, "사": 4, "오": 5,
           "육": 6, "륙": 6, "칠": 7, "팔": 8, "구": 9}
_VP_POW = {"십": 10, "백": 100, "천": 1000}
_VP_LETTER = {"에이": "A", "비": "B", "씨": "C", "디": "D"}
_VP_NUM_RE = re.compile(r"^(-?\d+(?:\.\d+)?)\s*(?:킬로그램|킬로|kg|그램|g|센티미터|센티|cm|"
                        r"밀리미터|밀리|mm|미터|m|개|번|회|퍼센트|%|도|점)?$", re.I)
_VP_KNUM_RE = re.compile(r"(^|\s|-)([영공일이삼사오육륙칠팔구십백천만]+)"
                         r"(?:\s*점\s*([영공일이삼사오육륙칠팔구]+))?(?=$|\s)")
_VP_NEXT_RE = re.compile(r"(?:^|\s+)(?:다음\s*행|다음|엔터)(?=$|[\s,.!?])[.!?]?")
_VP_CANCEL_RE = re.compile(r"(?:^|\s+)취소(?=$|[\s,.!?])[.!?]?")


def _vp_sino(w):
    """한자어 수사 → 정수. '육백십오'→615, '일이삼'(자리 읽기)→123, 해석 불가면 None."""
    if not re.fullmatch(r"[영공일이삼사오육륙칠팔구십백천만]+", w or ""):
        return None
    if not re.search(r"[십백천만]", w):
        return int("".join(str(_VP_DIG[c]) for c in w))
    total, sec, cur = 0, 0, None
    for ch in w:
        if ch in _VP_DIG:
            if cur is not None:
                return None
            cur = _VP_DIG[ch]
        elif ch in _VP_POW:
            sec += (1 if cur is None else cur) * _VP_POW[ch]
            cur = None
        else:  # 만
            total += ((sec + (cur or 0)) or 1) * 10000
            sec, cur = 0, None
    return total + sec + (cur or 0)


def _vp_num(s):
    """'72.3', '72 점 3', '칠십이 점 삼', '615kg', '1,234' → 숫자. 숫자가 아니면 None."""
    t = re.sub(r"마이너스\s*", "-", str(s))
    t = re.sub(r"(\d),(\d{3})(?!\d)", r"\1\2", t)

    def rep(m):
        v = _vp_sino(m.group(2))
        if v is None:
            return m.group(0)
        out = str(v)
        if m.group(3):
            out += "." + "".join(str(_VP_DIG[c]) for c in m.group(3))
        return m.group(1) + out
    t = _VP_KNUM_RE.sub(rep, t)
    t = re.sub(r"(\d)\s*점\s*(\d)", r"\1.\2", t)
    t = re.sub(r"\s+", " ", t).strip()
    m = _VP_NUM_RE.match(t)
    if not m:
        return None
    x = m.group(1)
    return float(x) if "." in x else int(x)


def _vp_clean(seg):
    """열 이름 뒤 구간 → 값. 조사·어미·단위를 떼고, '615 아니 616'처럼 고쳐 말하면 뒤 값을 쓴다."""
    s = re.split(r"\s*아니(?:요|고|야)?[,\s]+", str(seg or ""))[-1]
    s = re.sub(r"^[\s,.:;·~]+", "", s)
    s = re.sub(r"[\s,.;:!?·]+$", "", s)
    if re.search(r"\S\s+\S", s):
        s = re.sub(r"^(은|는|이|가|을|를|의|도|요)\s+", "", s)
    s = re.sub(r"\s*(입니다|이에요|예요|이고요|이고|이요|고요|이며|요)$", "", s) or s
    s = s.strip()
    if not s:
        return None
    n = _vp_num(s)
    if n is not None:
        return n
    return _VP_LETTER.get(s, s)


def _vp_col_key(c):
    k = re.sub(r"\([^)]*\)|\[[^\]]*\]", "", str(c))
    k = re.sub(r"\s+", "", k)
    return k or re.sub(r"\s+", "", str(c))


def voice_split_rows(text):
    """'다음'으로 행을 나누고 '취소' 앞 내용은 버린다. 반환: (끝난 행 문장 목록, 이어지는 문장)."""
    def drop_cancelled(p):
        return _VP_CANCEL_RE.split(p)[-1].strip()
    pieces = _VP_NEXT_RE.split(str(text or ""))
    return [drop_cancelled(p) for p in pieces[:-1]], drop_cancelled(pieces[-1])


def voice_parse_local(text, columns=None):
    """음성 문장 한 행 → dict. 열을 주면 그 열 이름을 찾아 값을 채우고(못 찾으면 None),
    열이 없으면 '이름 값 이름 값' 순서로 짝을 짓는다."""
    text = str(text or "")
    cols = [str(c) for c in (columns or [])]
    if not cols:
        t = re.sub(r"(\d)\s*점\s*(\d)", r"\1.\2", text)
        toks = [x for x in re.split(r"[\s,]+", t) if x]
        row, i = {}, 0
        while i < len(toks):
            lab = toks[i]
            if _vp_num(lab) is not None or i + 1 >= len(toks):
                i += 1
                continue
            v, j = toks[i + 1], i + 2
            if j + 1 < len(toks) and toks[j] == "점":
                v, j = f"{v} 점 {toks[j + 1]}", j + 2
            cv = _vp_clean(v)
            if cv is not None:
                row[lab] = cv
            i = j
        return row
    spans = []
    for c in sorted(cols, key=lambda c: -len(_vp_col_key(c))):
        pat = r"\s*".join(re.escape(ch) for ch in _vp_col_key(c))
        for m in re.finditer(pat, text, flags=re.I):
            s, e = m.span()
            if e > s and not any(s < pe and e > ps for _, ps, pe in spans):
                spans.append((c, s, e))
    spans.sort(key=lambda x: x[1])
    row = {c: None for c in cols}
    for i, (c, s, e) in enumerate(spans):
        seg = text[e: spans[i + 1][1] if i + 1 < len(spans) else len(text)]
        v = _vp_clean(seg)
        if v is not None:
            row[c] = v
    return row


def voice_text_to_row(transcript, columns=None):
    cols = [str(c) for c in (columns or [])]
    # 열을 알고 있고 규칙으로 모든 열이 채워지면 AI를 다시 부르지 않는다(녹음 1건당 AI 호출 2번 → 1번).
    if cols:
        done, rest = voice_split_rows(transcript)
        local = voice_parse_local(" ".join(done + [rest]), cols)
        if all(local.get(c) not in (None, "") for c in cols):
            return local, []
    prompt = f"""다음은 연구자가 음성으로 말한 한 행의 조사 데이터입니다.
음성: {transcript}
현재 데이터 열: {cols if cols else '없음'}
반드시 JSON만 출력하세요.
현재 열이 있으면 {{"row": {{"열이름": 값, ...}}, "warnings": []}} 형식으로 해당 열 이름을 그대로 사용하세요.
현재 열이 없으면 {{"row": {{"처리구":"A", "반복":1, ...}}, "warnings": []}} 형태로 의미 있는 열을 만드세요.
말하지 않은 값은 null로 두고 숫자는 가능하면 숫자형으로 반환하세요. 추측하지 마세요."""
    raw = ai_call(prompt, max_tokens=1200, system="데이터 입력 도우미입니다. JSON만 출력합니다.")
    js = _json_from_ai_text(raw)
    if not isinstance(js, dict) or not isinstance(js.get("row"), dict):
        return None, [raw if raw else "음성을 행 데이터로 변환하지 못했습니다."]
    row = js["row"]
    if cols:
        row = {c: row.get(c, None) for c in cols}
    return row, list(js.get("warnings") or [])

def ai_disclaimer():
    st.warning("⚠️ **AI가 만든 초안입니다.** 논문·보고서에 넣기 전에 반드시 연구자가 "
               "수치와 해석이 맞는지 확인하고 수정하세요. AI는 없는 인과관계를 서술하거나 "
               "수치를 잘못 인용할 수 있습니다.")

def _json_safe(obj):
    """NaN·NumPy 타입을 JSON으로 안전하게 변환"""
    import math
    if obj is None:
        return None
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        v = float(obj)
        return None if (math.isnan(v) or math.isinf(v)) else round(v, 6)
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, (np.ndarray,)):
        return [_json_safe(x) for x in obj.tolist()]
    if isinstance(obj, pd.DataFrame):
        return [{str(k): _json_safe(v) for k, v in row.items()}
                for row in obj.to_dict(orient="records")]
    if isinstance(obj, pd.Series):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_json_safe(x) for x in obj]
    if pd.isna(obj) if np.isscalar(obj) else False:
        return None
    return obj if isinstance(obj, (str, int)) else str(obj)


def build_data_overview(df, max_cols=40):
    """AI에게 넘길 데이터 개요. 결측치·자료형을 '명시적으로' 적어 추측을 막는다.

    이전에는 describe() 결과만 넘겨서 AI가 결측치가 있는 열을 잘못 지목하는 일이
    있었다. 여기서는 열별 결측 개수를 문장으로 못 박아 전달한다.
    """
    if df is None or getattr(df, "empty", True):
        return "데이터가 없습니다."
    lines = [f"행 {len(df):,}개, 열 {len(df.columns)}개"]
    miss = df.isna().sum()
    has_miss = miss[miss > 0]
    lines.append("")
    lines.append("[열 정보]  형식 | 결측 | 고유값")
    for c in list(df.columns)[:max_cols]:
        kind = "숫자형" if pd.api.types.is_numeric_dtype(df[c]) else "문자형"
        lines.append(f"- {c} | {kind} | 결측 {int(miss[c])}개 | 고유 {int(df[c].nunique(dropna=True))}종")
    if len(df.columns) > max_cols:
        lines.append(f"- (이하 {len(df.columns)-max_cols}개 열 생략)")
    lines.append("")
    if has_miss.empty:
        lines.append("[결측치] 모든 열에 결측치가 없습니다. "
                     "어떤 열에도 '결측치가 있다'고 서술하지 마세요.")
    else:
        detail = ", ".join(f"'{c}' {int(v)}개" for c, v in has_miss.items())
        lines.append(f"[결측치] 결측치가 있는 열은 다음뿐입니다: {detail}. "
                     "여기에 없는 열은 결측치가 0개이므로 결측을 언급하지 마세요.")
    try:
        lines.append("")
        lines.append("[기술통계]")
        lines.append(df.describe().round(2).to_string())
    except Exception:
        pass
    return "\n".join(lines)


def build_group_profiles(df, question="", max_groups=15, max_numeric=12):
    """질문과 관련된 처리·품종별 평균/표준편차/n을 AI에 전달한다."""
    if df is None or df.empty:
        return {}
    nums = df.select_dtypes(include=np.number).columns.tolist()[:max_numeric]
    cats = [c for c in df.columns if c not in nums and 2 <= df[c].nunique(dropna=True) <= max_groups]
    q = str(question or "").lower()
    selected = []
    for c in cats:
        levels = [str(x) for x in df[c].dropna().unique()]
        if str(c).lower() in q or any(v.lower() in q for v in levels):
            selected.append(c)
    if not selected:
        selected = cats[:2]
    out = {}
    for c in selected:
        if not nums:
            continue
        g = df.groupby(c)[nums].agg(["mean", "std", "count"])
        out[str(c)] = _json_safe(g.reset_index())
    return out


def build_anova_context(**kw):
    """분산분석 결과를 AI에 넘길 구조화 JSON으로 정리"""
    ctx = {
        "analysis_type": kw.get("analysis_type", "분산분석"),
        "design": kw.get("design"),
        "treatment_column": kw.get("trt"),
        "block_column": kw.get("blk"),
        "response_variable": kw.get("yv"),
        "group_stats": kw.get("group_stats"),
        "anova_table": kw.get("anova_table"),
        "p_treatment": kw.get("p_treatment"),
        "p_block": kw.get("p_block"),
        "cv_percent": kw.get("cv"),
        "lsd": kw.get("lsd"),
        "mse": kw.get("mse"),
        "df_residual": kw.get("df_resid"),
        "posthoc_method": kw.get("posthoc"),
        "significance_letters": kw.get("letters"),
        "dunnett_table": kw.get("dunnett"),
        "assumption_tests": kw.get("assumptions"),
        "n_missing_excluded": kw.get("n_missing"),
        "cautions": kw.get("cautions", []),
    }
    return _json_safe({k: v for k, v in ctx.items() if v is not None})


def bootstrap_diff_ci(a, b, n_boot=2000, alpha=0.05, seed=0):
    """두 그룹 평균 차이(a−b)의 부트스트랩 신뢰구간. 소표본·비정규 자료용."""
    a = np.asarray(pd.to_numeric(pd.Series(a), errors="coerce").dropna(), dtype=float)
    b = np.asarray(pd.to_numeric(pd.Series(b), errors="coerce").dropna(), dtype=float)
    if len(a) < 2 or len(b) < 2:
        return None
    rng = np.random.default_rng(seed)
    diffs = np.empty(n_boot)
    for i in range(n_boot):
        diffs[i] = (rng.choice(a, len(a), replace=True).mean()
                    - rng.choice(b, len(b), replace=True).mean())
    lo, hi = np.percentile(diffs, [alpha / 2 * 100, (1 - alpha / 2) * 100])
    return {"diff": float(a.mean() - b.mean()), "low": float(lo), "high": float(hi),
            "n_boot": int(n_boot)}


def econ_metric_test(row_df, trt_col, value_col, control=None, blk_col=None):
    """반복별 소득·순수익 ANOVA와 모형 기반 대조구 비교.

    블록이 있으면 ANOVA와 Dunnett 모두 같은 RCBD 모형을 사용한다.
    부트스트랩 구간은 관측 평균 차이의 보조 정보로 별도 표시한다.
    """
    use_cols = [c for c in (trt_col, value_col, blk_col) if c and c in row_df.columns]
    d = row_df[use_cols].dropna()
    ok, _ = validate_anova_data(d, trt_col, value_col)
    if not ok:
        return None
    out = {"n_groups": int(d[trt_col].nunique()),
           "n_total": int(len(d)), "value": value_col,
           "block": blk_col if blk_col in d.columns else None}
    model = None
    try:
        f = safe_formula(value_col, [trt_col] + ([blk_col] if blk_col in d.columns else []))
        model = ols(f, data=d).fit()
        aov = sm.stats.anova_lm(model, typ=2)
        k = f"C({q_ref(trt_col)})"
        out["anova_p"] = float(aov.loc[k, "PR(>F)"]) if k in aov.index else None
        if blk_col in d.columns:
            bk = f"C({q_ref(blk_col)})"
            out["block_p"] = float(aov.loc[bk, "PR(>F)"]) if bk in aov.index else None
        out["model"] = f
    except Exception as ex:
        out["anova_p"] = None
        out["error"] = str(ex)[:120]

    str_levels = {str(x): x for x in d[trt_col].dropna().unique()}
    control_level = str_levels.get(str(control)) if control is not None else None
    if control_level is not None and model is not None:
        try:
            ph = posthoc_from_model(model, d, trt_col, "던넷(Dunnett)",
                                     control=control_level)
            tab = ph.get("table", pd.DataFrame()).copy()
            if not tab.empty:
                tab = tab.rename(columns={
                    "처리 평균(보정)": "평균(보정)",
                    "평균 차이": f"'{control}' 대비 차이",
                    "p(동시보정)": "p(보정)",
                    "95% 동시CI 하한": "95% 하한",
                    "95% 동시CI 상한": "95% 상한",
                })
                keep = [c for c in ["처리구", "평균(보정)", f"'{control}' 대비 차이",
                                     "p(보정)", "95% 하한", "95% 상한", "판정"]
                        if c in tab.columns]
                out["dunnett"] = tab[keep]
        except Exception as ex:
            out["dunnett_error"] = str(ex)[:120]

        # 비모수적 불확실성 참고: 원자료 평균차 부트스트랩
        g = d.assign(__trt=d[trt_col].astype(str)).groupby("__trt")[value_col]
        names = [n for n in g.groups.keys() if n != str(control)]
        boot = {}
        for n in names:
            r = bootstrap_diff_ci(g.get_group(n).values,
                                  g.get_group(str(control)).values)
            if r:
                boot[n] = r
        if boot:
            out["bootstrap"] = boot
    return out


def build_econ_context(**kw):
    """경제성 결과를 AI에 넘길 구조화 JSON으로 정리"""
    ctx = {
        "analysis_type": "경제성분석",
        "base_area": kw.get("base_area", "10a"),
        "control_treatment": kw.get("control"),
        "treatments": kw.get("treatments"),
        "price_assumptions": kw.get("prices"),
        "cost_columns_used": kw.get("cost_cols"),
        "cost_columns_excluded_for_duplication": kw.get("excluded_cols"),
        "sensitivity": kw.get("sensitivity"),
        "yield_statistical_test": kw.get("yield_test"),
        "income_statistical_test": kw.get("income_test"),
        "profit_statistical_test": kw.get("profit_test"),
        "cautions": kw.get("cautions", []),
    }
    return _json_safe({k: v for k, v in ctx.items() if v is not None})


# ---------------------------------------------------------------- 경제성 분석 길잡이(규칙 기반)
_ECON_MODE_PARTIAL = "📕 부분예산표 (손실적·이익적 요소)"
_ECON_MODE_INCOME = "📗 소득분석"
_ECON_MODE_MRR = "📘 신기술 경제성 (부분예산·한계수익률)"
_ECON_MODE_INVEST = "📙 시설·장기투자 경제성 (NPV·B/C·IRR)"


def recommend_economic_guide(goal, change, comparison, period, data_items=None):
    """초보자용 경제성 분석 길잡이의 순수 규칙 엔진.

    STEP 1~5 응답을 받아 현재 앱의 경제성 모듈 중 가장 적합한 것을 추천한다.
    AI/API를 쓰지 않으며, '잘 모르겠어요'가 포함되어도 나머지 답으로 판단한다.
    정책·공공사업 CBA는 기존 농가단위 모듈로 억지 연결하지 않는다.
    """
    data_items = list(data_items or [])
    values = [str(goal or ''), str(change or ''), str(comparison or ''), str(period or '')]
    unknown_count = sum('잘 모르' in v or '아직 모르' in v for v in values)
    if any('아직 거의 준비' in str(x) or '자료가 어떤' in str(x) for x in data_items):
        unknown_count += 1

    def has(text, *tokens):
        s = str(text or '')
        return any(t in s for t in tokens)

    scores = {
        _ECON_MODE_PARTIAL: 0.0,
        _ECON_MODE_INCOME: 0.0,
        _ECON_MODE_MRR: 0.0,
        _ECON_MODE_INVEST: 0.0,
    }
    reasons = []
    tags = []
    warnings = []

    # 정책·공공사업은 현재 농가단위 모듈 범위를 벗어난다.
    if has(goal, '정책', '사회적') or has(change, '사회적', '환경적', '공공사업'):
        return {
            'primary_mode': None,
            'title': '🏛️ 비용편익분석(CBA) — 현재 직접 계산 미지원',
            'confidence': '높음',
            'scores': scores,
            'reasons': [
                '정책·공공사업은 농가 개인의 수입·비용뿐 아니라 사회 전체의 편익·비용과 외부효과를 평가해야 합니다.',
                '현재 프로그램의 소득분석·부분예산·MRR은 농가 또는 기술대안 단위 분석이므로 범위가 다릅니다.',
            ],
            'needs': ['사회적 편익', '사회적 비용', '외부효과의 화폐가치', '분석기간', '사회적 할인율'],
            'together': ['재무성 분석과 경제성(CBA)을 구분', '비시장 편익·비용의 평가 근거 명시'],
            'tags': ['CBA'], 'warnings': [], 'ambiguous': False,
            'missing_reported': [], 'top_two': [],
        }

    # STEP 1: 연구 목적
    if has(goal, '기존 방식보다', '신품종', '신기술'):
        scores[_ECON_MODE_PARTIAL] += 7
        scores[_ECON_MODE_MRR] += 2
        reasons.append('기존 방식과 신기술의 차이를 평가하는 목적입니다.')
    elif has(goal, '현재 작목', '현재 처리', '수익성'):
        scores[_ECON_MODE_INCOME] += 8
        reasons.append('현재 한 해의 조수입·소득·순수익 자체가 핵심 질문입니다.')
    elif has(goal, '여러 대안', '가장 경제적', '무엇을 권'):
        scores[_ECON_MODE_MRR] += 8
        scores[_ECON_MODE_INCOME] += 2
        reasons.append('여러 대안 중 추가비용 대비 추가편익을 비교하려는 목적입니다.')
    elif has(goal, '시설', '농기계', '투자할 가치'):
        scores[_ECON_MODE_INVEST] += 10
        reasons.append('초기 투자비를 들여 여러 해 사용하는 자산의 투자 타당성이 핵심 질문입니다.')
    elif has(goal, '어느 가격', '어느 수량', '손해'):
        scores[_ECON_MODE_INCOME] += 8
        tags.append('손익분기점')
        reasons.append('현재 비용구조를 기준으로 손익이 0이 되는 가격·수량을 찾는 질문입니다.')
    elif has(goal, '가격', '수량', '유지', '위험'):
        scores[_ECON_MODE_INCOME] += 8
        tags.append('민감도 분석')
        reasons.append('기준 소득을 계산한 뒤 가격·수량 변동에 대한 위험을 확인하는 질문입니다.')
    elif has(goal, '여러 작형', '여러 품종', '경영성과'):
        scores[_ECON_MODE_INCOME] += 7
        scores[_ECON_MODE_PARTIAL] += 1
        reasons.append('같은 기간의 처리·작형별 경영성과를 동일 기준으로 비교하려는 목적입니다.')

    # STEP 2: 실제로 달라지는 것
    if has(change, '품종', '방제', '재배법', '재배기술'):
        scores[_ECON_MODE_PARTIAL] += 5
        scores[_ECON_MODE_MRR] += 1
        reasons.append('품종·방제·재배기술 변경은 기존 방식 대비 변화분 비교가 중요합니다.')
    elif has(change, '투입수준', '투입량', '비료량', '농약량', '노동량'):
        scores[_ECON_MODE_MRR] += 5
        scores[_ECON_MODE_PARTIAL] += 2
        reasons.append('투입수준에 따라 비용이 단계적으로 달라지는 구조입니다.')
    elif has(change, '시설', '농기계', '신규 투자'):
        scores[_ECON_MODE_INVEST] += 8
        reasons.append('시설·농기계의 신규 투자가 포함됩니다.')
    elif has(change, '판매가격', '상품수량', '상품률', '수량·가격'):
        scores[_ECON_MODE_INCOME] += 4
        tags.append('민감도 분석')
        reasons.append('가격·수량 변화가 수익성에 미치는 영향 확인이 필요합니다.')
    elif has(change, '특별한 변경 없음', '현재 경영성과'):
        scores[_ECON_MODE_INCOME] += 6
        reasons.append('특정 신기술의 변화분보다 현재 경영성과 자체를 평가하는 구조입니다.')

    # STEP 3: 비교 구조
    if has(comparison, '대조구 1개', '신기술 1', '신품종 1'):
        scores[_ECON_MODE_PARTIAL] += 6
        reasons.append('대조구와 신기술을 직접 비교하는 구조라 부분예산법과 잘 맞습니다.')
    elif has(comparison, '3개 이상', '비용이 다른', '여러 대안'):
        scores[_ECON_MODE_MRR] += 8
        reasons.append('비용이 다른 3개 이상 대안은 지배분석과 MRR로 단계적 채택 여부를 보기 좋습니다.')
    elif has(comparison, '여러 품종', '여러 작형', '한 해 성과'):
        scores[_ECON_MODE_INCOME] += 6
        reasons.append('여러 처리의 한 해 소득·순수익을 같은 기준으로 비교하는 구조입니다.')
    elif has(comparison, '비교대상 없음'):
        scores[_ECON_MODE_INCOME] += 3
        reasons.append('비교대상이 없으므로 우선 현재 수익성의 기준선을 만드는 것이 적합합니다.')

    # STEP 4: 분석기간
    if has(period, '한 작기', '1년'):
        scores[_ECON_MODE_PARTIAL] += 2
        scores[_ECON_MODE_INCOME] += 2
        scores[_ECON_MODE_MRR] += 2
        scores[_ECON_MODE_INVEST] -= 1
        reasons.append('경제효과를 한 작기·1년 기준으로 평가합니다.')
    elif has(period, '2년 이상'):
        scores[_ECON_MODE_INVEST] += 4
        warnings.append('여러 해 자료라도 매년 독립적인 재배기술 비교라면 연도별 부분예산/소득분석을 병행할 수 있습니다.')
        reasons.append('효과가 여러 해 지속되므로 시간가치를 확인할 필요가 있습니다.')
    elif has(period, '내용연수', '사용기간 전체'):
        scores[_ECON_MODE_INVEST] += 8
        reasons.append('시설·기계의 내용연수 전체를 보므로 할인현금흐름 분석이 필요합니다.')

    # STEP 5: 보유자료 — 추천을 뒤집기보다 실행가능성 판단에 가중치를 조금만 준다.
    items_text = ' | '.join(map(str, data_items))
    if has(items_text, '최초 투자비'):
        scores[_ECON_MODE_INVEST] += 2
    if has(items_text, '연도별 편익', '연간 편익'):
        scores[_ECON_MODE_INVEST] += 2
    if has(items_text, '할인율', '잔존가치'):
        scores[_ECON_MODE_INVEST] += 2
    if has(items_text, '달라지는 비용'):
        scores[_ECON_MODE_PARTIAL] += 1
        scores[_ECON_MODE_MRR] += 1
    if has(items_text, '항목별 경영비'):
        scores[_ECON_MODE_INCOME] += 1

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_mode, top_score = ranked[0]
    second_mode, second_score = ranked[1]
    margin = top_score - second_score

    # 모든 응답이 거의 미정이면 억지 추천하지 않는다.
    ambiguous = bool(top_score < 5 or (unknown_count >= 3 and margin < 3))
    if ambiguous:
        primary_mode = None
        title = '🧭 추천 보류 — 두 가지만 더 정리하면 정확히 고를 수 있어요'
        confidence = '낮음'
    else:
        primary_mode = top_mode
        confidence = '높음' if unknown_count <= 1 and margin >= 3 else ('중간' if margin >= 1.5 else '낮음')
        title_map = {
            _ECON_MODE_PARTIAL: '📕 부분예산법',
            _ECON_MODE_INCOME: '📗 소득분석',
            _ECON_MODE_MRR: '📘 신기술 경제성(MRR)',
            _ECON_MODE_INVEST: '📙 시설·장기투자 분석',
        }
        title = title_map[top_mode]

    meta = {
        _ECON_MODE_PARTIAL: {
            'needs': ['대조구·신기술구 구분', '조사면적과 수량(또는 판매수입)', '실제 판매가격', '신기술 때문에 달라진 비용: 종묘·비료·농약·자재·노동·위탁·임차 등 변화분만'],
            'together': ['반복시험이면 수량·소득의 통계검정', '가격 변동이 크면 민감도 분석'],
            'data_groups': [
                ('처리구/대조구 구분', ['처리구/대조구 구분']),
                ('수량·생산량', ['수량·생산량']),
                ('판매가격/판매액', ['판매가격/판매액']),
                ('변화 비용', ['신기술로 달라지는 비용만', '항목별 경영비']),
            ],
        },
        _ECON_MODE_INCOME: {
            'needs': ['처리구/작형·반복(비교 시)', '조사면적과 생산량', '실제 판매가격과 부산물수입(있으면)', '경영비: 종자·종묘, 비료, 농약, 수도광열, 재료, 소농구, 감가상각, 수선, 임차, 위탁영농, 고용노동 등 실제 발생 항목', '순수익까지 볼 때: 자가노동시간, 자본용역비, 자가토지 용역비'],
            'together': ['손익분기점', '가격·수량 민감도', '반복자료가 있으면 소득·순수익 통계검정'],
            'data_groups': [
                ('수량·생산량', ['수량·생산량']),
                ('판매가격/판매액', ['판매가격/판매액']),
                ('항목별 경영비', ['항목별 경영비']),
            ],
        },
        _ECON_MODE_MRR: {
            'needs': ['비용이 다른 여러 처리구(보통 3개 이상)와 대조구', '조사면적·처리별 수량', '실제 판매가격', '처리 수준에 따라 달라지는 가변비용: 비료·농약·노동·자재·위탁비 등', '수량 조정률 및 최소수용 MRR 기준'],
            'together': ['부분예산', '지배분석', '최소수용 MRR', '가격·수량 민감도'],
            'data_groups': [
                ('처리구/대조구 구분', ['처리구/대조구 구분']),
                ('수량·생산량', ['수량·생산량']),
                ('판매가격/판매액', ['판매가격/판매액']),
                ('가변비용', ['신기술로 달라지는 비용만', '항목별 경영비']),
            ],
        },
        _ECON_MODE_INVEST: {
            'needs': ['최초 투자비(설치·구입·부대공사 포함)', '분석기간/내용연수', '연도별 또는 연간 추가수입·비용절감 편익', '연간 운영·유지·수선비와 예상 교체비', '할인율', '잔존가치(있으면)'],
            'together': ['NPV', '할인 B/C', 'IRR', '단순·할인 회수기간', '편익·비용 민감도'],
            'data_groups': [
                ('최초 투자비', ['최초 투자비']),
                ('연도별 편익·운영비', ['연도별 편익·운영비']),
                ('분석기간·할인율', ['분석기간·할인율·잔존가치']),
            ],
        },
    }
    chosen_meta = meta.get(top_mode, meta[_ECON_MODE_INCOME])
    present = set(map(str, data_items))
    missing = []
    for label, alternatives in chosen_meta['data_groups']:
        if not any(a in present for a in alternatives):
            missing.append(label)

    # 목적별 보조 분석 태그
    if top_mode == _ECON_MODE_PARTIAL and '반복(블록) 자료' in present:
        tags.append('통계검정 병행')
    if top_mode == _ECON_MODE_MRR:
        tags.extend(['지배분석', 'MRR'])
    if top_mode == _ECON_MODE_INVEST:
        tags.extend(['NPV', '할인 B/C', 'IRR'])
    tags = list(dict.fromkeys(tags))

    if ambiguous:
        reasons = reasons[-4:] if reasons else [
            '연구목적·비교대상·분석기간 중 아직 정해지지 않은 항목이 많습니다.',
            '“기존 방식과 다른 처리가 있는지”와 “효과가 1년인지 여러 해인지”만 정하면 대부분의 경우 분석법을 고를 수 있습니다.'
        ]
    else:
        reasons = list(dict.fromkeys(reasons))[-5:]

    return {
        'primary_mode': primary_mode,
        'title': title,
        'confidence': confidence,
        'scores': scores,
        'reasons': reasons,
        'needs': chosen_meta['needs'],
        'together': chosen_meta['together'],
        'tags': tags,
        'warnings': warnings,
        'ambiguous': ambiguous,
        'missing_reported': missing,
        'top_two': [(ranked[0][0], ranked[0][1]), (ranked[1][0], ranked[1][1])],
    }


def parse_ai_json(text):
    """AI 응답에서 {verified_facts, interpretation, limitations, recommendation}
    구조를 찾아 파싱. 실패하면 (None, 원문)을 반환해 그대로 보여줌."""
    import json as _json
    import re as _re
    if not text:
        return None, ""
    t = str(text).strip()
    t = _re.sub(r"^```(?:json)?\s*|\s*```$", "", t, flags=_re.S).strip()
    m = _re.search(r"\{.*\}", t, _re.S)
    if not m:
        return None, str(text)
    try:
        obj = _json.loads(m.group(0))
    except Exception:
        return None, str(text)
    if not isinstance(obj, dict):
        return None, str(text)
    keys = ("verified_facts", "interpretation", "limitations", "recommendation")
    if not any(k in obj for k in keys):
        return None, str(text)
    out = {}
    for k in keys:
        v = obj.get(k, [])
        if isinstance(v, str):
            v = [v]
        elif not isinstance(v, list):
            v = [str(v)]
        out[k] = [strip_md(str(x)).strip() for x in v if str(x).strip()]
    return out, str(text)


def render_ai_json(parsed):
    """파싱된 AI 응답을 보기 좋게 표시하고 보고서용 평문을 반환"""
    labels = [("verified_facts", "확인된 사실"), ("interpretation", "해석"),
              ("limitations", "한계"), ("recommendation", "권장 사항")]
    lines = []
    for key, title in labels:
        items = parsed.get(key) or []
        if not items:
            continue
        st.markdown(f"**{title}**")
        for it in items:
            st.markdown(f"- {it}")
        lines.append(f"○ {title}")
        lines += [f"  - {it}" for it in items]
    return "\n".join(lines)


def ai_interpret_advanced(slot, kind, table_df, extra="", context=None, capture_slot=None):
    """분석 결과를 3가지 스타일(보고서·고찰·현장지도)로 해석. 결과는 화면에 계속 남음."""
    key = st.session_state.get("api_key")
    out_key = f"__ai_out_{slot}"
    STYLES = {
        "1️⃣ 보고서용": (
            "농촌진흥청 시험연구보고서 '주요 연구결과' 항목에 그대로 넣을 수 있게 작성하세요.\n"
            "형식: 주요 항목은 '○ '로 시작, 세부 내용은 '  - '로 시작.\n"
            "표의 실제 수치를 반드시 인용하고, p-value·CV%·사후검정 문자를 근거로 제시하세요.\n"
            "분량: 6~10줄."),
        "2️⃣ 논문 고찰용 (Discussion)": (
            "학술논문의 고찰(Discussion) 초안으로 작성하세요.\n"
            "결과의 통계적 의미를 먼저 정리하고, 관찰된 경향이 나타난 농학적 원인을 추정하되 "
            "'~로 추정된다', '~때문으로 판단된다'처럼 단정하지 않는 표현을 쓰세요.\n"
            "마지막에 본 시험의 한계와 후속 연구 방향을 1~2문장 제시하세요.\n"
            "분량: 6~10문장의 서술형 문단(불릿 없이)."),
        "4️⃣ 구조화(검증·해석·한계·권장)": (
            "다음 JSON 형식으로만 답하세요. 다른 설명은 붙이지 마세요.\n"
            '{"verified_facts": [], "interpretation": [], "limitations": [], '
            '"recommendation": []}\n'
            "- verified_facts: 제공된 JSON에서 그대로 확인되는 사실(수치 포함)\n"
            "- interpretation: 그 사실이 농업적으로 무엇을 뜻하는지\n"
            "- limitations: 이 결과로 말할 수 없는 것, 검정하지 않은 부분\n"
            "- recommendation: 다음에 확인하거나 시도할 것\n"
            "각 항목은 문자열 배열이며, 마크다운 기호는 쓰지 마세요."),
        "3️⃣ 현장 지도용 (3줄 요약)": (
            "농가·현장 지도용으로 통계를 모르는 사람도 이해할 수 있게 작성하세요.\n"
            "형식: 정확히 3줄. 각 줄은 '○ '로 시작.\n"
            "1줄=어떤 처리가 가장 좋았는지, 2줄=그 차이가 믿을 만한지, 3줄=현장에서 어떻게 하면 되는지.\n"
            "전문용어(p값, 유의수준, 변이계수) 대신 쉬운 말로 바꿔 쓰세요."),
    }
    with st.expander("🤖 AI 해석 (보고서·고찰·현장지도)"):
        if not key:
            st.info("**🧠 AI 도우미 → AI 연결 설정**에 API 키를 넣으면 "
                    "이 결과를 3가지 형태의 문장으로 바꿔 드립니다.")
            return
        want = st.radio("어떤 형태로 만들까요?", list(STYLES.keys()), key="aim_" + slot)
        if st.button("✨ AI 해석 생성", key="aib_" + slot):
            ctx = ""
            if context:
                import json as _json
                try:
                    ctx = ("\n\n[분석 결과 JSON — 이 안의 값만 사용하세요]\n"
                           + _json.dumps(_json_safe(context), ensure_ascii=False, indent=1))
                except Exception:
                    ctx = "\n\n[분석 맥락]\n" + "\n".join(f"- {k}: {v}" for k, v in context.items() if v)
            with st.spinner("AI가 해석 중..."):
                prompt = (f"다음은 '{kind}' 분석 결과입니다.\n\n"
                          f"{table_df.to_string(index=False)}\n{ctx}\n\n"
                          f"{extra}\n\n{STYLES[want]}\n\n"
                          "반드시 한국어로 작성하고, 마크다운 기호(**, ##, *, `, ---)는 "
                          "어떤 경우에도 사용하지 마세요. 표에 없는 수치는 만들어 내지 마세요.")
                raw = ai_call(prompt, key, st.session_state.get("ai_model_g"), max_tokens=1600)
                if want.startswith("4️⃣"):
                    _parsed, _orig = parse_ai_json(raw)
                    st.session_state[out_key + "_json"] = _parsed
                    st.session_state[out_key] = strip_md(_orig) if _parsed is None else ""
                    if _parsed is None:
                        st.warning("⚠️ AI가 요청한 JSON 형식으로 답하지 않아 원문을 그대로 표시합니다.")
                else:
                    st.session_state[out_key + "_json"] = None
                    st.session_state[out_key] = strip_md(raw)
                log_action(f"AI 해석 생성({kind} / {want.split()[-1]})")
        _pj = st.session_state.get(out_key + "_json")
        saved = st.session_state.get(out_key)
        if _pj:
            st.markdown("###### 생성된 해석")
            _plain = render_ai_json(_pj)
            saved = _plain
            with st.expander("보고서용 평문 보기"):
                st.code(_plain, language=None)
        elif saved:
            st.markdown("###### 생성된 문장")
            st.code(saved, language=None)
        if saved:
            ai_disclaimer()
            cap = st.session_state.get(capture_slot) if capture_slot else None
            b1, b2 = st.columns(2)
            if cap:
                if b1.button("➕ 분석 결과 + AI 해석 함께 담기", key="aiadd_" + slot,
                             help="표·그림과 AI 해석이 보고서에서 같은 항목으로 이어 붙습니다."):
                    merged = merge_ai_into_capture(cap, kind, saved)
                    st.session_state.report_items.append(merged)
                    st.success("분석 결과와 해석을 함께 담았습니다! "
                               f"(현재 {len(st.session_state.report_items)}개)")
            else:
                if b1.button("➕ 보고서에 담기", key="aiadd_" + slot):
                    st.session_state.report_items.append(
                        {"heading": f"{kind} 해석", "text": saved,
                         "table": None, "image": None})
                    st.success("보고서에 담았습니다!")
            if b2.button("🗑️ 지우기", key="aidel_" + slot):
                st.session_state[out_key] = None
                st.session_state[out_key + "_json"] = None
                st.rerun()

def merge_ai_into_capture(capture, kind, ai_text):
    """담아둔 분석 결과(표·그림)와 AI 해석을 하나의 보고서 항목으로 합친다.

    예전에는 해석이 별도 항목으로 붙어 보고서에서 표와 떨어져 나왔다.
    """
    import copy as _copy
    item = _copy.copy(capture or {})
    blocks = list(item.get("blocks") or [])
    if not blocks:
        blocks = [b for b in [
            {"text": item.get("text")} if item.get("text") else None,
            {"caption": item.get("heading", ""), "table": item.get("table")}
            if item.get("table") is not None else None,
            {"caption": item.get("heading", ""), "image": item.get("image")}
            if item.get("image") else None,
        ] if b]
    # AI가 '○ ...' 로 시작하는 제목 줄을 만들면 우리 제목과 한 줄로 합친다.
    lines = [ln for ln in str(ai_text).rstrip().split("\n")]
    head = f"○ AI 해석({kind})"
    first = lines[0].strip() if lines else ""
    if first.startswith(("○", "◦", "●")):
        head += " - " + first.lstrip("○◦● ").strip()
        lines = lines[1:]
    body = "\n".join([head] + lines)
    ai_block = {"text": body, "ai": True}
    # 보고서 관행상 '결과 문장 → 표·그림' 순서이므로, 해석문은 표 앞에 넣는다.
    pos = next((i for i, b in enumerate(blocks)
                if b.get("table") is not None or b.get("image")), len(blocks))
    blocks.insert(pos, ai_block)
    return {"heading": item.get("heading") or f"{kind} 분석",
            "text": None, "table": None, "image": None, "blocks": blocks}


# 이전 이름 호환
def ai_interpret_button(slot, kind, table_df, extra="", capture_slot=None):
    return ai_interpret_advanced(slot, kind, table_df, extra,
                                 capture_slot=capture_slot)

# ---------------------------------------------------------------- 추천/해석
_BLOCK_KEYS = ["반복", "블록", "구역", "block", "rep", "blk"]
_TRT_KEYS = ["처리", "시험구", "구분", "품종", "계통", "약제", "농도", "시비", "수준"]
# 숫자지만 '조사한 값'이 아닌 열 — 측정항목 후보에서 제외한다.
_ID_KEYS = ["연도", "년도", "year", "일자", "날짜", "date", "번호", "no.", "id", "코드"]


def split_code_columns(df):
    """숫자로 적혀 있지만 사실은 처리구·반복 코드인 열을 찾아낸다.

    엑셀에서 반복을 1, 2, 3으로 적는 경우가 매우 흔한데, 이것을 측정값으로
    오인하면 난괴법이 완전임의배치로 분석되어 결론이 뒤집힐 수 있다.
    반환: (측정값 후보, 범주형 후보, 숫자→범주로 승격된 열)
    """
    num = df.select_dtypes(include=np.number).columns.tolist()
    promoted = []
    for c in list(num):
        s = pd.to_numeric(df[c], errors="coerce").dropna()
        if s.empty:
            continue
        name = str(c).lower()
        name_hit = any(k in name for k in _BLOCK_KEYS + _TRT_KEYS)
        # 연도·번호처럼 보이는 열은 측정값이 아니므로 이름이 맞으면 그대로 승격
        try:
            is_int = bool(np.allclose(s.to_numpy(dtype=float),
                                      np.round(s.to_numpy(dtype=float))))
        except (TypeError, ValueError):
            is_int = False
        nu = int(s.nunique())
        vmin, vmax = float(s.min()), float(s.max())
        # 코드값은 보통 1,2,3... 또는 0,1,2...처럼 빈틈없이 이어진다.
        # 이 조건이 없으면 '폭우일(7,8,10,12일)' 같은 실제 측정값까지 코드로 오인한다.
        contiguous = is_int and vmin in (0.0, 1.0) and (vmax - vmin + 1) == nu
        code_like = contiguous and 2 <= nu <= 15 and len(s) >= nu * 2
        if name_hit or code_like:
            num.remove(c)
            promoted.append(c)
    cat = [c for c in df.columns if c not in num]
    return num, cat, promoted


def _v1_star(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ""


def _v1_target_var(cols):
    """보고서 문장의 기준이 될 결과 변수(수량 등)를 이름으로 추정한다."""
    for key in ("수량", "수확량", "생산량", "yield", "상품수량", "건물중", "생체중"):
        for c in cols:
            if key in str(c).lower():
                return c
    return None


def report_sentence_corr(pairs, n_range, method="Pearson", target=None, max_pairs=4):
    """상관분석 보고서 문장.
    pairs: [(변수1, 변수2, r, p), ...]   n_range: (최소 n, 최대 n)
    """
    sig = [(a, b, r, p) for a, b, r, p in pairs if p < .05 and np.isfinite(r)]
    n_txt = f"n={n_range[0]}" if n_range[0] == n_range[1] else f"n={n_range[0]}~{n_range[1]}"
    lines = [f"○ {method} 상관분석 결과 ({n_txt})"]
    if not sig:
        lines.append("  - 분석한 변수들 사이에 통계적으로 유의한 상관은 인정되지 않았다(p≥0.05).")
    else:
        def fmt(v, r, p):
            return f"{v}(r={r:.2f}{_v1_star(p)})"
        used = set()
        if target is not None:
            rel = [((b if a == target else a), r, p) for a, b, r, p in sig if target in (a, b)]
            pos = sorted([x for x in rel if x[1] > 0], key=lambda x: -abs(x[1]))
            neg = sorted([x for x in rel if x[1] < 0], key=lambda x: -abs(x[1]))
            parts = []
            if pos:
                parts.append(", ".join(fmt(v, r, p) for v, r, p in pos[:max_pairs]) + "와(과) 유의한 정(+)의 상관")
            if neg:
                parts.append(", ".join(fmt(v, r, p) for v, r, p in neg[:max_pairs]) + "와(과) 유의한 부(−)의 상관")
            if parts:
                lines.append(f"  - {target}은(는) " + "을, ".join(parts) + "을 보였다.")
                used = {frozenset((a, b)) for a, b, r, p in sig if target in (a, b)}
            else:
                lines.append(f"  - {target}과(와) 유의한 상관을 보인 변수는 없었다.")
        rest = sorted([x for x in sig if frozenset((x[0], x[1])) not in used], key=lambda x: -abs(x[2]))
        if rest:
            lab = "그 밖에 상관이 높은 변수 쌍은 " if target is not None else "상관이 높은 변수 쌍은 "
            lines.append("  - " + lab + ", ".join(f"{a}–{b}(r={r:.2f}{_v1_star(p)})" for a, b, r, p in rest[:max_pairs])
                         + "이었다.")
    lines.append("  - 상관계수는 두 변수가 함께 변하는 정도를 나타낼 뿐, 인과관계를 의미하지는 않는다.")
    return "\n".join(lines)


def report_sentence_reg(model, y, xs):
    """회귀분석 보고서 문장."""
    fp = float(model.f_pvalue) if np.isfinite(model.f_pvalue) else np.nan
    kind = "단순회귀분석" if len(xs) == 1 else "다중회귀분석"
    lines = [f"○ {y}에 대한 {kind} 결과 (n={int(model.nobs)})"]
    if np.isfinite(fp) and fp < .05:
        lines.append(f"  - 회귀식은 통계적으로 유의하였으며({fmt_p(fp)}), {y} 변동의 "
                     f"{model.rsquared*100:.1f}%를 설명하였다(R²={model.rsquared:.3f}"
                     + (f", 수정 R²={model.rsquared_adj:.3f}" if len(xs) > 1 else "") + ").")
    else:
        lines.append(f"  - 회귀식은 통계적으로 유의하지 않았다({fmt_p(fp)}, R²={model.rsquared:.3f}).")
    terms = " ".join(f"{'+' if model.params[x] >= 0 else '−'} {abs(model.params[x]):,.4g}×{x}" for x in xs)
    lines.append(f"  - 회귀식: {y} = {model.params['const']:,.4g} {terms}")
    sig = [x for x in xs if model.pvalues[x] < .05]
    if sig:
        lines.append("  - " + ", ".join(
            f"{x}(b={model.params[x]:,.4g}, {fmt_p(model.pvalues[x])})" for x in sig)
            + f"이(가) {y}에 유의한 영향을 주었다.")
        pos = [x for x in sig if model.params[x] > 0]
        neg = [x for x in sig if model.params[x] < 0]
        if pos:
            lines.append(f"  - {', '.join(pos)}이(가) 클수록 {y}이(가) 증가하는 경향이었다.")
        if neg:
            lines.append(f"  - {', '.join(neg)}이(가) 클수록 {y}이(가) 감소하는 경향이었다.")
    else:
        lines.append(f"  - 개별 변수 중 {y}에 유의한 영향을 준 변수는 없었다(p≥0.05).")
    return "\n".join(lines)


def reg_footnote(model, xs):
    return ("* p<0.05, ** p<0.01, *** p<0.001, ns: 유의하지 않음.\n"
            f"* R² = {model.rsquared:.3f}" + (f", 수정 R² = {model.rsquared_adj:.3f}" if len(xs) > 1 else "")
            + f", n = {int(model.nobs)}, 최소제곱법(OLS) 추정.")


def _v1_unit_of(name):
    m = re.search(r"\(([^()]*)\)\s*$", str(name))
    return m.group(1) if m else ""


def ml_grade(score, is_reg):
    """머신러닝 성능 등급(참고 기준)."""
    if is_reg:
        if score >= .7:
            return "좋음", "예측값이 실제값을 잘 따라갑니다."
        if score >= .5:
            return "보통", "경향은 맞추지만 개별 예측 오차가 큽니다."
        if score >= 0:
            return "약함", "이 변수들만으로는 예측이 어렵습니다. 참고용으로만 보세요."
        return "매우 약함", "평균값으로 찍는 것보다도 못합니다. 변수 구성을 다시 검토하세요."
    if score >= .85:
        return "좋음", "대부분을 맞게 분류합니다."
    if score >= .7:
        return "보통", "상당수를 맞히지만 틀리는 경우도 적지 않습니다."
    return "약함", "분류 정확도가 낮습니다. 참고용으로만 보세요."


def report_sentence_ml(tgt, algo, is_reg, score, n_train, n_test, mae=None, rmse=None,
                       top_vars=None, baseline=None):
    unit = _v1_unit_of(tgt)
    grade, _ = ml_grade(score, is_reg)
    lines = [f"○ {algo} 모형을 이용한 {tgt} 예측 결과 (학습 {n_train}개, 검증 {n_test}개)"]
    if is_reg:
        lines.append(f"  - 검증 자료에서 결정계수(R²)는 {score:.3f}로 예측력은 '{grade}' 수준이었으며, "
                     f"평균 절대오차(MAE)는 ±{mae:,.3g}{(' ' + unit) if unit else ''}"
                     f"(RMSE {rmse:,.3g})였다.")
    else:
        lines.append(f"  - 검증 자료의 분류 정확도는 {score*100:.1f}%로 '{grade}' 수준이었다"
                     + (f"(가장 많은 범주로만 찍었을 때 {baseline*100:.1f}%)." if baseline is not None else "."))
    if top_vars:
        lines.append(f"  - 예측에 가장 크게 기여한 변수는 {', '.join(top_vars[:3])} 순이었다.")
    lines.append("  - 머신러닝 결과는 변수 간 예측 관계를 보여 줄 뿐 처리 효과의 통계적 유의성을 검정한 것은 아니다.")
    return "\n".join(lines)


def report_sentence_likert(summ, alpha, scale_max, pos_col, n_total):
    v = summ.dropna(subset=["평균"])
    lines = [f"○ {scale_max}점 척도 문항 분석 결과 (응답자 {n_total}명)"]
    if len(v):
        top, low = v.loc[v["평균"].idxmax()], v.loc[v["평균"].idxmin()]
        lines.append(f"  - {len(v)}개 문항의 전체 평균은 {v['평균'].mean():.2f}점이었으며, "
                     f"'{top['문항']}'이 {top['평균']:.2f}점으로 가장 높고 "
                     f"'{low['문항']}'이 {low['평균']:.2f}점으로 가장 낮았다.")
        if pos_col in v.columns:
            tp = v.loc[v[pos_col].idxmax()]
            lines.append(f"  - 긍정 응답 비율은 '{tp['문항']}'이 {tp[pos_col]:.1f}%로 가장 높았다.")
    if np.isfinite(alpha):
        lv = "매우 높은" if alpha >= .9 else "높은" if alpha >= .8 else "양호한" if alpha >= .7 else "낮은"
        lines.append(f"  - 척도의 신뢰도(Cronbach's α)는 {alpha:.3f}로 {lv} 수준이었다.")
    return "\n".join(lines)


def report_sentence_mc(res):
    lines = ["○ 객관식 문항 응답 분포"]
    for q, g in res.groupby("문항", sort=False):
        g = g.sort_values("빈도", ascending=False)
        n = int(g["빈도"].sum())
        first = g.iloc[0]
        s_ = f"  - '{q}'(n={n})은 '{first['응답']}'이 {first['비율(%)']:.1f}%({int(first['빈도'])}명)로 가장 많았고"
        if len(g) > 1:
            sec = g.iloc[1]
            s_ += f", 다음은 '{sec['응답']}'({sec['비율(%)']:.1f}%) 순이었다."
        else:
            s_ += "."
        lines.append(s_)
    return "\n".join(lines)


def report_sentence_mr(col, t, n_resp):
    lines = [f"○ '{col}' 다중응답 결과 (응답자 {n_resp}명, 총 {int(t['응답 수'].sum())}건)"]
    top = t.head(3)
    lines.append("  - " + ", ".join(f"'{r['응답 항목']}'({r['응답률(%)']:.1f}%)" for _, r in top.iterrows())
                 + " 순으로 많이 선택되었다.")
    lines.append(f"  - 응답자 1인당 평균 {t['응답 수'].sum()/max(n_resp, 1):.1f}개 항목을 선택하였다.")
    return "\n".join(lines)


def report_sentence_crosstab(rowv, colv, ct, chi=None):
    """chi: (chi2, dof, p, low_expected_pct) 또는 None"""
    rp = ct.div(ct.sum(axis=1), axis=0) * 100
    lines = [f"○ {rowv}에 따른 {colv} 응답 비교 (n={int(ct.values.sum())})"]
    for r in ct.index:
        top = rp.loc[r].idxmax()
        lines.append(f"  - {r}(n={int(ct.loc[r].sum())})은 '{top}' 응답이 {rp.loc[r, top]:.1f}%로 가장 많았다.")
    if chi is not None:
        chi2, dof, p, low = chi
        lines.append(f"  - 카이제곱 검정 결과 {rowv}에 따라 {colv} 응답에 "
                     + ("유의한 차이가 있었다" if p < .05 else "유의한 차이는 없었다")
                     + f"(χ²={chi2:.2f}, df={dof}, {fmt_p(p)}).")
        if low > 20:
            lines.append(f"  - 다만 기대빈도 5 미만인 칸이 {low:.0f}%로 많아 검정 결과는 참고용으로 해석해야 한다.")
    return "\n".join(lines)


def _pdf_clean_table(rows):
    """pdfplumber 표(문자 목록)를 DataFrame으로: 첫 행 = 변수명, 빈 행·열 제거, 숫자 열은 숫자로."""
    rows = [[("" if c is None else re.sub(r"\s+", " ", str(c)).strip()) for c in r] for r in rows if r]
    rows = [r for r in rows if any(c for c in r)]
    if len(rows) < 2:
        return None
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    head, body = rows[0], rows[1:]
    d = pd.DataFrame(body, columns=[h or f"열{i+1}" for i, h in enumerate(head)])
    d = d.loc[:, [c for c in d.columns if d[c].astype(str).str.strip().ne("").any()]]
    if d.shape[1] < 2 or d.empty:
        return None
    for c in d.columns:
        s_ = d[c].astype(str).str.replace(",", "", regex=False).str.strip()
        conv = pd.to_numeric(s_.where(s_ != "", None), errors="coerce")
        if conv.notna().sum() and conv.notna().sum() == s_.ne("").sum():
            d[c] = conv
        else:
            d[c] = d[c].where(d[c].astype(str).str.strip() != "", None)
    return clean_columns(d)


def _pdf_text_tables(text):
    """테두리 없는 표: 같은 칸 수로 이어지는 줄 묶음을 표로 본다 (첫 줄 = 변수명)."""
    lines = [ln.split() for ln in str(text or "").splitlines() if ln.strip()]
    out, i = [], 0
    while i < len(lines):
        k = len(lines[i])
        j = i
        while j < len(lines) and len(lines[j]) == k:
            j += 1
        run = lines[i:j]
        if k >= 2 and len(run) >= 3:
            num_rows = sum(1 for r in run[1:] if any(re.fullmatch(r"[-+]?[\d,]*\.?\d+", c) for c in r))
            if num_rows >= max(2, (len(run) - 1) // 2):
                out.append(run)
        i = max(j, i + 1)
    return out


def pdf_extract_tables(pdf_bytes, max_pages=30):
    """글자가 선택되는 PDF에서 표를 뽑는다. 반환: (표 목록, 쪽 수, 글자 있는 쪽 수)
    표 목록 = [{"page": 쪽, "idx": 쪽 안 순서, "df": DataFrame}, ...]
    선이 있는 표는 선을 따라, 선이 없는 표는 같은 칸 수로 이어지는 줄을 표로 읽는다."""
    import pdfplumber
    out, n_pages, n_text = [], 0, 0
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        n_pages = len(pdf.pages)
        for pno, page in enumerate(pdf.pages[:max_pages], start=1):
            text = page.extract_text() or ""
            if text.strip():
                n_text += 1
            found = []
            for t in (page.extract_tables() or []):
                d = _pdf_clean_table(t)
                if d is not None and len(d) >= 2:
                    found.append(d)
            if not found and text.strip():
                for t in _pdf_text_tables(text):
                    d = _pdf_clean_table(t)
                    if d is not None and len(d) >= 2:
                        found.append(d)
            for ti, d in enumerate(found, start=1):
                out.append({"page": pno, "idx": ti, "df": d})
    return out, n_pages, n_text


def pdf_page_png(pdf_bytes, page_no, resolution=160):
    """스캔 PDF의 한 쪽을 그림(PNG)으로 바꿔 이미지 표 인식에 넘긴다."""
    import pdfplumber
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        img = pdf.pages[page_no - 1].to_image(resolution=resolution).original
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _v1_copy_box(title, text):
    st.markdown(f"###### 📋 {title}")
    st.code(text, language=None, wrap_lines=True)


def _v1_regression_table(model, y, xs):
    """OLS 결과를 연구자가 바로 읽을 수 있는 표로 정리한다 (계수·표준오차·p·95% 신뢰구간·해석)."""
    ci = model.conf_int()
    rows = []
    for name in model.params.index:
        b, se, t, p = (float(model.params[name]), float(model.bse[name]),
                       float(model.tvalues[name]), float(model.pvalues[name]))
        star = "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "ns"
        if name == "const":
            label, meaning = "절편(상수)", f"모든 X가 0일 때 {y}의 예측값"
        else:
            label = str(name)
            meaning = (f"{name}이(가) 1 늘면 {y}이(가) {abs(b):,.4g} {'증가' if b >= 0 else '감소'}"
                       + ("" if p < .05 else " (통계적으로 뚜렷하지 않음)"))
        rows.append({"변수": label, "계수(기울기)": round(b, 4), "표준오차": round(se, 4),
                     "t": round(t, 3), "p-value": round(p, 4), "유의성": star,
                     "95% 신뢰구간": f"{ci.loc[name, 0]:,.4g} ~ {ci.loc[name, 1]:,.4g}",
                     "해석": meaning})
    return pd.DataFrame(rows)


def _v1_render_regression(model, y, xs):
    """회귀분석 결과를 '한눈에 보기 → 회귀식 → 계수표 → (전공자용) 원문' 순서로 보여 준다."""
    fp = float(model.f_pvalue) if np.isfinite(model.f_pvalue) else np.nan
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("설명력 R²", f"{model.rsquared:.3f}", help="Y의 변동 중 X로 설명되는 비율 (1에 가까울수록 좋음)")
    c2.metric("수정 R²", f"{model.rsquared_adj:.3f}", help="X 개수를 고려해 보정한 R². 변수가 여러 개면 이 값을 봅니다.")
    c3.metric("모형 p-value", "< 0.001" if fp < .001 else f"{fp:.3f}",
              help="회귀식 전체가 의미 있는지 (0.05보다 작으면 유의)")
    c4.metric("관측 수", f"{int(model.nobs)}")
    terms = " ".join(f"{'+' if model.params[x] >= 0 else '−'} {abs(model.params[x]):,.4g} × {x}" for x in xs)
    st.markdown(f"**회귀식**: {y} = {model.params['const']:,.4g} {terms}")
    if np.isfinite(fp):
        if fp < .05:
            st.success(f"✅ 회귀식이 통계적으로 유의합니다 (p {'< 0.001' if fp < .001 else f'= {fp:.3f}'}). "
                       f"아래 표에서 p < 0.05(유의성 *)인 변수가 {y}에 뚜렷한 영향을 준 변수입니다.")
        else:
            st.warning(f"⚠️ 회귀식이 통계적으로 유의하지 않습니다 ({fmt_p(fp, sp=True, digits=3)}). "
                       f"선택한 변수로는 {y}을(를) 설명하기 어렵습니다.")
    smart_table(_v1_regression_table(model, y, xs), width="stretch", hide_index=True)
    st.caption("유의성: \\* p<0.05, \\*\\* p<0.01, \\*\\*\\* p<0.001, ns 유의하지 않음")
    with st.expander("📄 통계 프로그램 원문 출력 보기 (전공자용 · OLS Regression Results)"):
        st.text(model.summary())


def _v1_id_like_cols(df):
    """개체번호·시료번호처럼 값이 모두 다른 정수 번호 열(측정값이 아님)."""
    out = []
    for c in df.select_dtypes(include=np.number).columns:
        name = str(c).lower()
        if not re.search(r"번호|개체|시료|샘플|sample|\bid\b|^id|no\.?$|^no", name):
            continue
        s = pd.to_numeric(df[c], errors="coerce").dropna()
        if len(s) and s.is_unique and np.allclose(s, np.round(s)):
            out.append(c)
    return out


def detect_design(df):
    """데이터 구조를 보고 실험설계를 자동 판별.
    반환: dict(design, trt, blk, sub, ys, reason, confidence, promoted)"""
    num, cat, promoted = split_code_columns(df)
    res = {"design": "판별 불가", "trt": None, "blk": None, "sub": None,
           "ys": num, "reason": "", "confidence": "낮음", "promoted": promoted}
    if not num:
        res["reason"] = "숫자형 측정값 열이 없습니다."
        return res
    # 반복(블록) 후보: 이름 기반
    blk = next((c for c in cat if any(k in str(c).lower() for k in _BLOCK_KEYS)), None)
    # 처리구 후보: 반복이 아니면서 수준이 2~15개
    trt_cands = [c for c in cat if c != blk and 2 <= df[c].nunique() <= 15]
    # 응답자ID·이름 같은 열 제외
    trt_cands = [c for c in trt_cands if df[c].nunique() < len(df) * 0.9]
    if not trt_cands:
        res["reason"] = "처리구로 볼 만한 범주형 열이 없습니다."
        return res
    # 이름 우선순위로 처리구 선택
    trt = next((c for k in _TRT_KEYS for c in trt_cands if k in str(c)), trt_cands[0])
    others = [c for c in trt_cands if c != trt]
    res["trt"] = trt
    res["blk"] = blk
    # 균형 여부 확인
    def balanced(cols, strict=True):
        try:
            t = df.groupby(cols).size()
            if strict:
                return t.nunique() == 1
            return t.min() >= 1 and (t.max() - t.min()) <= 1
        except Exception:
            return False
    if blk and others:
        # 반복 + 요인 2개 → 요인배치/분할구. 단, 주 관심 요인을 '처리'로 우선
        res["sub"] = others[0]
        if balanced([trt, others[0], blk], strict=False):
            res["design"] = "난괴법 요인배치(2요인 × 반복)"
            res["reason"] = (f"반복('{blk}')이 있고 요인이 2개('{trt}', '{others[0]}')입니다. "
                             "→ 이원배치로 상호작용까지 보거나, 한 요인만 골라 난괴법으로 분석할 수 있습니다. "
                             "관수·경운처럼 큰 구역 요인이 있다면 **분할구법**을 쓰세요.")
            res["confidence"] = "높음"
        else:
            res["design"] = "이원배치(요인배치)"
            res["reason"] = f"두 요인('{trt}', '{others[0]}')이 있습니다."
            res["confidence"] = "중간"
    elif blk:
        if balanced([trt, blk], strict=False):
            res["design"] = "난괴법(RCBD)"
            n_rep = df[blk].nunique()
            res["reason"] = (f"처리구 '{trt}'({df[trt].nunique()}개)가 반복 '{blk}'"
                             f"({n_rep}반복)에 균형 있게 배치되어 있습니다.")
            res["confidence"] = "높음"
        else:
            res["design"] = "난괴법(RCBD, 불균형)"
            res["reason"] = f"반복 '{blk}'이 있으나 처리구별 반복 수가 고르지 않습니다."
            res["confidence"] = "중간"
    elif others:
        res["sub"] = others[0]
        res["design"] = "이원배치(요인배치)"
        res["reason"] = f"범주형 요인이 2개('{trt}', '{others[0]}') 있고 반복 열은 없습니다."
        res["confidence"] = "중간"
    else:
        res["design"] = "완전임의배치(CRD)"
        cnt = df.groupby(trt).size()
        res["reason"] = (f"처리구 '{trt}'({df[trt].nunique()}개)만 있고 반복 열이 없습니다. "
                         f"처리당 {cnt.min()}~{cnt.max()}개 관측치.")
        res["confidence"] = "높음" if cnt.min() >= 3 else "중간"
    # 연도·일련번호는 숫자지만 조사값이 아니므로 측정항목 후보에서 뺀다.
    ys = [c for c in num if not any(k in str(c).lower() for k in _ID_KEYS)]
    if not ys:
        ys = list(num)
    # 측정값 우선순위 정렬(수량류 먼저)
    res["ys"] = sorted(ys, key=lambda c: 0 if any(
        k in str(c) for k in ["수량", "수확", "생산량", "무게", "중"]) else 1)
    return res

def recommend_analysis(df):
    nc = df.select_dtypes(include=np.number).columns.tolist()
    cc = df.select_dtypes(exclude=np.number).columns.tolist()
    recs = []
    for c in cc:
        try:
            uniq = df[c].nunique()
            ng = int(uniq) if np.isscalar(uniq) else int(np.asarray(uniq).ravel()[0])
        except Exception:
            continue  # 중복 열 이름 등 비정상 구조는 건너뜀
        if 2 <= ng <= 15 and nc:
            recs.append((f"'{c}' 그룹이 {ng}개예요 → " +
                         ("**t-검정/ANOVA**" if ng == 2 else "**ANOVA + 사후검정(a,b,c)**") + " 이 적합합니다.", 3 if ng > 2 else 2))
    if len(cc) >= 2 and nc:
        recs.append(("범주형 변수가 2개 이상 → **이원배치 분산분석**으로 상호작용도 볼 수 있어요.", 2))
    if len(nc) >= 2:
        recs.append(("숫자형 변수가 여러 개 → **상관분석/히트맵**과 **회귀분석**이 가능합니다.", 2))
    seen, out = set(), []
    for msg, _ in sorted(recs, key=lambda x: -x[1]):
        if msg not in seen: seen.add(msg); out.append(msg)
    return out[:5] if out else ["데이터 구조상 뚜렷한 추천이 어려워요."]

def _josa(word, pair="이/가"):
    """받침 여부에 따라 조사 선택 (수비초가 / 청양이)"""
    a, b = pair.split("/")
    w = str(word).strip()
    if not w: return a
    ch = w[-1]
    if ch.isdigit():   # 숫자로 끝나면 읽는 소리로 판단 (1,3,6,7,8,0=받침 있음)
        return a if ch in "136078" else b
    if not ("가" <= ch <= "힣"):
        return a
    return a if (ord(ch) - 0xAC00) % 28 else b

def report_sentence_anova(gc, vc, pval, means, letters, ci=None, ph=""):
    """시험연구보고서 양식(○ / -)의 결과 문장 자동 작성"""
    order = means.sort_values("mean", ascending=False).index.tolist()
    top, low = order[0], order[-1]
    lines = [f"○ {gc}별 {vc} 분석 결과"]
    lines.append(f"  - {top}{_josa(top)} {means.loc[top,'mean']:.1f}로 가장 높았고, "
                 f"{low}{_josa(low)} {means.loc[low,'mean']:.1f}로 가장 낮았다.")
    if pval < 0.05:
        lines.append(f"  - 처리 간 유의한 차이가 인정되었다({fmt_p(pval)}).")
        by = {}
        for g, l in letters.items(): by.setdefault(l, []).append(str(g))
        same = [v for v in by.values() if len(v) > 1]
        if same:
            _grp = ', '.join(same[0])
            lines.append(f"  - 다만 {_grp}{_josa(same[0][-1], '은/는')} 같은 문자군에 속하여 "
                         "통계적으로 동등한 수준이었다.")
    else:
        lines.append(f"  - 처리 간 유의한 차이는 인정되지 않았다({fmt_p(pval)}).")
    if ci and not np.isnan(ci.get("CV", np.nan)):
        if ci["CV"] < 1:
            lines.append(f"  - 시험의 변이계수(CV)는 {ci['CV']:.1f}%로 매우 낮아, "
                         "반복별 원자료가 입력되었는지 확인이 필요하다.")
        else:
            lines.append(f"  - 시험의 변이계수(CV)는 {ci['CV']:.1f}%로 "
                         f"{cv_grade(ci['CV'])} 수준이었다.")
    if ph:
        lines.append(f"  - 평균 간 비교는 {ph}(p<0.05)으로 실시하였다.")
    return "\n".join(lines)

def interpret_anova(pval, letters):
    if pval < 0.001: s = "처리구 간 **매우 뚜렷한 차이**가 있습니다 (p < 0.001)."
    elif pval < 0.05: s = f"처리구 간 **통계적으로 유의한 차이**가 있습니다 ({fmt_p(pval, sp=True, digits=3)})."
    else: return f"처리구 간 유의한 차이가 **없습니다** ({fmt_p(pval, sp=True, digits=3)} ≥ 0.05)."
    by = {}
    for g, l in letters.items(): by.setdefault(l, []).append(g)
    same = [v for v in by.values() if len(v) > 1]
    if same: s += f" 같은 문자를 가진 처리구({', '.join(map(str, same[0]))})끼리는 차이가 없습니다."
    return s

def interpret_corr(corr, sel):
    pairs = []
    for i in range(len(sel)):
        for j in range(i+1, len(sel)):
            pairs.append((abs(corr.iloc[i, j]), sel[i], sel[j], corr.iloc[i, j]))
    if not pairs: return ""
    pairs.sort(reverse=True); _, a, b, r = pairs[0]
    s = "강한" if abs(r) >= 0.7 else ("뚜렷한" if abs(r) >= 0.4 else "약한")
    d = "양(+)의" if r > 0 else "음(-)의"
    t = "한 변수가 커질수록 다른 변수도 커집니다." if r > 0 else "한 변수가 커질수록 다른 변수는 작아집니다."
    return f"가장 관계가 큰 변수는 **'{a}'와 '{b}'** 로, {s} {d} 상관입니다 (r = {r:.2f}). {t}"

EXPLAIN = {
"sd_se": """둘 다 '±' 뒤에 붙는 값이지만 **뜻이 완전히 다릅니다.**

| | 표준편차 (SD) | 표준오차 (SE) |
|---|---|---|
| 무엇을 재나요 | **개체들이** 평균에서 얼마나 흩어져 있나 | **평균값 자체가** 얼마나 믿을 만한가 |
| 반복을 늘리면 | 거의 그대로 (자연적인 변이라서) | **작아집니다** (√반복수로 나누므로) |
| 계산 | 자료의 흩어짐 | SD ÷ √반복수 |
| 언제 쓰나요 | "이 품종은 개체 간 편차가 크다"를 보일 때 | "처리 평균의 차이"를 보일 때 |

**쉽게 말하면**
- SD: *"이 처리구의 고추 무게는 개체마다 얼마나 들쭉날쭉한가?"*
- SE: *"이 처리구의 평균 무게를 얼마나 믿어도 되나?"*

**포장시험에서는 어떤 걸?**
- 처리구 간 비교 그래프(막대 + 오차막대) → **SE**를 더 많이 씁니다. 오차막대가 짧을수록 평균이 안정적이라는 뜻이라 처리 간 차이를 보기 좋습니다.
- 품종·계통의 균일도, 개체 변이를 설명할 때 → **SD**.

> ⚠️ SE는 반복수가 많을수록 무조건 작아지므로, **오차막대가 짧다고 처리 효과가 크다는 뜻은 아닙니다.**
> 유의차 판단은 오차막대가 아니라 **사후검정 문자(a, b, c)** 나 LSD로 하세요.
>
> 논문·보고서에는 `평균 ± SD` 인지 `평균 ± SE` 인지, 그리고 반복수(n)를 **표 각주에 반드시 밝혀야** 합니다.""",

"prep": """**전처리**는 분석 전에 데이터를 정리하는 단계입니다. 여기서 빠뜨린 문제는 이후 모든 결과를 왜곡시킵니다.

**꼭 확인할 것**
- **결측치**: 조사 누락·측정 실패로 비어 있는 칸
- **이상값**: 입력 실수(예: 15.0을 150으로)나 극단적으로 튀는 값
- **중복 행**: 같은 자료가 두 번 입력된 경우
- **자료형**: 숫자여야 하는데 문자로 읽힌 열(엑셀에서 '12.5 ' 처럼 공백이 섞이면 발생)

**순서 권장**: 자료형 확인 → 중복 제거 → 이상값 확인 → 결측치 처리""",

"outlier": """**이상값(outlier)**은 다른 값들과 유난히 동떨어진 값입니다. 평균과 분산을 크게 흔들어 분석 결과를 왜곡합니다.

**두 가지 탐지 방법**
- **IQR(사분위수) 방법**: 자료를 크기순으로 줄 세워 가운데 50% 구간(IQR)을 구한 뒤, 그 범위의 1.5배를 벗어나면 이상값으로 봅니다. 분포가 치우쳐 있어도 잘 작동합니다.
- **Z-점수 방법**: 평균에서 표준편차의 3배 이상 떨어지면 이상값으로 봅니다. 정규분포에 가까울 때 적합합니다.

**처리 방법 고르기**
- 측정 실수·입력 오류가 확실 → **해당 행 삭제**
- 실제 값이지만 너무 극단적 → **경계값으로 대체(윈저화)**
- 판단 보류 → **결측치로 변경** 후 따로 검토

⚠️ 이상값이 항상 오류인 것은 아닙니다. 특이한 개체가 실제로 존재할 수 있으니, 지우기 전에 원본 조사표를 꼭 확인하세요.""",

"derive": """**파생변수**는 기존 열을 조합해 새로운 열을 만드는 기능입니다. 분석에 필요한 지표가 원자료에 없을 때 사용합니다.

**세 가지 방식**
1. **두 열 사칙연산** — 예: `생체중 ÷ 초장` = 단위 길이당 무게, `수량 × 단가` = 조수입
2. **조건 열** — 조건을 만족하면 1, 아니면 0. 예: `일 최고기온 ≥ 33` → 폭염일 표시
3. **그룹별 집계** — 연도·처리구별로 합계·평균 등을 계산

**활용 예: 연간 폭염일수 구하기**
① 조건 열로 `기온 ≥ 33` 만들기 → ② 그룹별 집계에서 '연도별 **합계**' → 연도마다 폭염일이 며칠인지 나옵니다.
(냉해일수는 `기온 ≤ 0`, 강우일수는 `강수량 ≥ 30` 등으로 같은 방식)""",

"corr": """**상관분석**은 두 변수가 함께 변하는 정도를 하나의 숫자(r)로 나타냅니다.

**상관계수 r 읽는 법** (−1 ~ +1)
- **+**: 한쪽이 커지면 다른 쪽도 커짐 (예: 생체중↑ → 수량↑)
- **−**: 한쪽이 커지면 다른 쪽은 작아짐
- **0에 가까움**: 뚜렷한 관계 없음

|절댓값|해석|
|---|---|
|0.7 이상|강한 상관|
|0.4~0.7|뚜렷한 상관|
|0.2~0.4|약한 상관|
|0.2 미만|거의 없음|

**Pearson vs Spearman**
- **Pearson**: 직선 관계를 봅니다. 자료가 정규분포에 가까울 때 사용.
- **Spearman**: 순위로 바꿔서 계산합니다. 정규분포가 아니거나, 등급·순위 자료(1등급·2등급 등)일 때 사용.

**히트맵**은 여러 변수의 상관을 색으로 한눈에 보여줍니다. 붉을수록 양(+), 푸를수록 음(−)의 상관입니다.

⚠️ **상관은 인과가 아닙니다.** 두 변수가 같이 움직인다고 해서 하나가 다른 하나의 원인이라는 뜻은 아닙니다.""",

"anova": """**분산분석(ANOVA)**은 세 개 이상 처리구의 평균이 서로 다른지 검정하는 방법입니다.
(두 개만 비교할 때는 t-검정을 쓰지만, ANOVA로도 같은 결론이 나옵니다)

**왜 필요한가?** 처리구가 4개일 때 t-검정을 6번 반복하면, 실제로는 차이가 없는데도 우연히 "차이 있다"고 나올 확률이 크게 올라갑니다. ANOVA는 한 번에 검정해 이 문제를 피합니다.

**결과 읽는 법**
- **p < 0.05**: "적어도 한 처리구는 다르다" → 사후검정으로 어느 것이 다른지 확인
- **p ≥ 0.05**: 처리 간 차이가 뚜렷하지 않음

---
**📐 실험 설계 고르기 (중요)**

- **완전임의배치(CRD)**: 처리를 완전히 무작위로 배치. 온실처럼 환경이 균일할 때.
- **난괴법(RCBD)**: 포장을 몇 개 블록(반복)으로 나누고 각 블록 안에 모든 처리를 배치. **우리 포장시험의 표준**입니다.
  - 👉 반복(블록)을 두었다면 **'반복(블록) 열'을 반드시 지정**하세요. 지정하지 않으면 블록 간 토양·경사 차이가 오차에 섞여, 실제로는 있는 처리 효과를 놓칠 수 있습니다.
- **이원배치**: 두 요인을 동시에 봅니다(예: 품종 × 시비량).
  - **상호작용이 유의하다** = "한 요인의 효과가 다른 요인에 따라 달라진다"는 뜻. 예를 들어 A품종은 시비를 늘리면 수량이 늘지만 B품종은 오히려 줄어드는 경우입니다. 이때는 주효과만 보면 안 되고 조합별로 해석해야 합니다.
- **여러 형질 한 표에(요약표)**: 초장·생체중·수량처럼 여러 조사 항목을 한 번에 분석해, 논문처럼 **평균과 유의성 문자(a, b, c)를 한 표**로 정리합니다.
- **분할구법 (고급)**: 관수·경운·재배양식처럼 큰 구역에만 줄 수 있는 요인(**주구**)과, 그 안을 나눠 배치한 품종·시비량 같은 요인(**세구**)이 함께 있을 때. 주구와 세구는 오차 크기가 달라 **따로 검정**해야 합니다.
- **반복측정 (고급)**: 같은 개체·같은 구를 **시기별로 여러 번** 조사했을 때(예: 정식 후 30·60·90일 초장). 같은 대상의 측정값끼리는 서로 독립이 아니므로 일반 분산분석 대신 반복측정 분석을 씁니다.

👉 각 설계를 고르면 그 설계에 맞는 **자세한 설명과 필요한 열**이 함께 나옵니다.

---
**✅ 가정 검정 (분석 전 자동 수행)**

ANOVA는 두 가지를 전제합니다.
- **정규성** (Shapiro-Wilk): 각 처리구 자료가 정규분포를 따르는가
- **등분산** (Levene): 처리구들의 흩어진 정도가 비슷한가

p ≥ 0.05면 가정을 만족합니다. 위배되면 **비모수검정(Kruskal-Wallis)** 을 쓰는 것이 안전합니다.

---
**🔤 사후검정과 유의성 문자(a, b, c)**

ANOVA는 "어딘가 다르다"까지만 알려줍니다. **어느 처리구끼리** 다른지는 사후검정으로 확인합니다.

- **같은 문자를 공유하면 차이 없음**, 문자가 완전히 다르면 차이 있음
- 예: 처리2(a), 처리1(ab), 대조구(b) → 처리2와 대조구는 차이 있지만, 처리1은 둘 중 어느 쪽과도 뚜렷한 차이가 없음

|방법|특징|
|---|---|
|**Tukey HSD**|국제 표준. 위양성을 잘 통제해 **논문 투고에 안전**|
|**던컨(DMRT)**|농업 논문 관행. 차이를 잘 잡아내지만 **위양성 위험이 큼**|
|**Bonferroni**|매우 엄격. 확실한 차이만 인정|

⚠️ 시비량·재식밀도처럼 **연속적인 수준**을 처리로 둔 경우에는 사후검정보다 **회귀분석**이 적절합니다.""",

"nonparam": """**비모수 검정**은 정규분포를 가정하지 않는 검정입니다.

**언제 쓰나요?**
- ANOVA의 정규성·등분산 가정이 깨졌을 때
- 표본이 매우 적을 때(처리당 5개 미만)
- 등급·순위처럼 간격이 일정하지 않은 자료(1=매우나쁨 ~ 5=매우좋음 등)
- 병해 발생 정도처럼 점수로 매긴 자료

**두 가지 방법 (자동 선택됩니다)**
- **Kruskal-Wallis**: 3개 이상 그룹 비교 → ANOVA의 비모수 버전
- **Mann-Whitney U**: 2개 그룹 비교 → t-검정의 비모수 버전

**결과 읽는 법**: p < 0.05면 그룹 간 차이가 있습니다. 평균 대신 **중앙값**으로 비교합니다(극단값의 영향을 덜 받기 때문).""",

"pca": """**주성분분석(PCA)**은 변수가 너무 많을 때, 정보를 최대한 유지하면서 **2개의 축으로 압축**해 그림 하나로 보여주는 방법입니다.

---
**🤔 왜 필요한가요?**

품종 10개에 대해 초장·엽수·생체중·과장·과경·당도·수량… 10가지 형질을 조사했다고 해봅시다.
"어떤 품종끼리 서로 비슷한가?"를 알고 싶은데, 형질이 10개면 그래프를 10차원으로 그려야 해서 눈으로 볼 수가 없습니다.
PCA는 이 10개 정보를 **가장 정보 손실이 적은 2개의 새 축**으로 요약해, 평면 위 산점도 하나로 보여줍니다.

**비유**: 사람을 여러 각도에서 찍을 수 있지만, 얼굴이 가장 잘 드러나는 각도 하나를 고르는 것과 비슷합니다. PCA는 데이터가 가장 잘 퍼져 보이는 각도를 수학적으로 찾아줍니다.

---
**📊 결과 읽는 법**

**① 설명분산비율 (가장 중요)**
- `PC1 45%, PC2 30% (누적 75%)` → 원래 정보의 75%를 이 그림 하나로 설명한다는 뜻
- **누적 70% 이상이면 신뢰할 만합니다.** 50% 미만이면 2차원 요약이 무리라는 뜻이니 해석에 주의하세요.

**② 산점도 (점들의 위치)**
- **가까운 점 = 서로 비슷한 개체/품종**
- 처리구별로 색을 나눴을 때 **무리가 뚜렷하게 갈리면**, 그 형질들로 처리구를 구분할 수 있다는 의미입니다.
- 반대로 색이 뒤섞여 있으면 처리 간 특성 차이가 크지 않다는 뜻입니다.

**③ 로딩표 (변수별 기여도)**
- 각 변수가 PC1·PC2를 만드는 데 얼마나 기여했는지 보여줍니다.
- **절댓값이 큰 변수**가 그 축의 의미를 결정합니다.
- 예: PC1에서 수량 0.52, 생체중 0.49, 초장 0.47처럼 크기 관련 형질이 모두 크면 → "PC1은 대체로 **식물체의 크기**를 나타내는 축"이라고 해석합니다.

---
**🌱 농업 연구에서 이렇게 씁니다**
- 여러 계통·품종을 형질 전체로 묶어 **유연관계 파악** (육종)
- 처리구가 여러 형질에서 **전체적으로 구분되는지** 확인
- 서로 비슷한(중복된) 형질을 찾아 **조사 항목 줄이기**

⚠️ 변수마다 단위가 달라도 괜찮습니다(자동 표준화됨). 다만 숫자형 변수가 **3개 이상** 필요하고, 표본이 너무 적으면(10개 미만) 결과가 불안정합니다.""",

"reg": """**회귀분석**은 한 변수(Y)를 다른 변수(X)로 **설명하거나 예측하는 식**을 만듭니다.

**ANOVA와 차이**: ANOVA는 "처리구별로 다른가?"(범주 비교), 회귀는 "X가 1 늘면 Y는 얼마나 변하나?"(수량적 관계)를 봅니다. 시비량처럼 **연속적인 수준**을 다룰 때는 회귀가 적합합니다.

**결과 읽는 법**
- **계수**: X가 1 증가할 때 Y의 변화량. 예: 계수 2.5 → 질소 1kg 증가 시 수량 2.5kg 증가
- **p-value**: 0.05 미만이면 그 변수가 의미 있게 기여함
- **R²(결정계수)**: 모델이 Y의 변동을 몇 % 설명하는지. 0.7이면 70% 설명

**VIF(다중공선성)** — 독립변수를 2개 이상 넣으면 자동 표시됩니다.
서로 너무 비슷한 변수(예: 초장과 생체중)를 함께 넣으면 계수가 뒤죽박죽이 됩니다.
**VIF 10 이상이면 경고**가 뜨니, 둘 중 하나를 빼세요.

**로지스틱 회귀**: Y가 **두 가지 값**일 때 사용합니다(발병/미발병, 합격/불합격 등).

⚠️ 관측 범위를 벗어난 예측은 위험합니다. 질소 0~30kg 자료로 만든 식을 60kg에 적용하면 안 됩니다.""",

"ml": """**머신러닝**은 데이터의 복잡한 패턴을 학습해 값을 예측하는 방법입니다.

**언제 쓰나요?**
- 변수가 많고 관계가 복잡해서 단순 회귀로 설명이 어려울 때
- **예측 자체**가 목적일 때(수량 예측, 등급 판정, 병해 발생 예측 등)
- 설문·센서·기상 등 **자료가 많을 때**

**알고리즘 고르기**
- **트리·앙상블**: 랜덤포레스트, Extra Trees, 그래디언트부스팅, 히스토그램 부스팅, AdaBoost, 의사결정나무
- **거리·경계 기반**: SVM(RBF), KNN — 변수 단위가 달라도 자동 표준화합니다.
- **회귀 전용 규제모형**: Ridge, Lasso, ElasticNet — 선형 관계와 다중공선성이 있을 때 유용합니다.
- **분류 전용 기본모형**: 로지스틱 회귀, GaussianNB

처음이라면 **랜덤포레스트**를 기준모형으로 먼저 돌리고, 다른 알고리즘과 테스트 성능을 비교하세요.

**결과 읽는 법**
- **R²**(회귀) / **정확도**(분류): 1에 가까울수록 잘 맞춤. 학습에 쓰지 않은 자료(테스트)로 평가한 값입니다.
- **변수 중요도**: 예측에 어떤 변수가 크게 기여했는지 순위

⚠️ **표본이 적으면 쓰지 마세요.** 포장시험처럼 반복이 3~4회뿐인 자료는 과적합(외운 것처럼 보이지만 새 자료에서는 틀림)이 일어납니다.
**처리 효과 검정은 반드시 분산분석**을 쓰고, 머신러닝은 참고용으로만 보세요.""",

"econ": """**경제성 분석**은 시험 결과를 '돈'으로 환산해, 그 처리가 실제로 농가에 이득인지 판단합니다.

**계산 체계** (농촌진흥청 농축산물 소득조사 기준)
- **총수입(조수입)** = 주산물가액(수량×단가) + **부산물가액**
- **경영비** = 생산에 투입된 경영비(종묘비·비료비·농약비·고용노력비·임차료·감가상각비 등). 현금지출만을 뜻하지는 않습니다.
- **생산비** = 경영비 + 자가노력비 + 유동자본용역비 + 고정자본용역비 + 자가토지 용역비
- **소득 = 총수입 − 경영비** → 경영비를 차감한 농업경영 성과
- **순수익 = 총수입 − 생산비** → 자기 노동·토지의 기회비용까지 뺀 순수 이익
- **소득률(%) = 소득 ÷ 총수입 × 100**

**지표 읽는 법**
- **소득률**: 고추는 대체로 50% 내외입니다(2024년 시설고추 56.3%).
- **단년도 총수입/생산비**: 1보다 크면 해당 연도의 입력 조건에서 총수입이 생산비보다 큼. 시설투자의 할인 B/C와는 다른 지표입니다.
- **손익분기수량**: (생산비 − 부산물가액 − 수량비례비) ÷ (단가 − 단위당 수량비례비)로 구합니다. 수확·선별·포장비처럼 수량에 비례하는 비용을 따로 지정하지 않으면 **(생산비 − 부산물가액) ÷ 단가**가 되어, "그해 들어간 비용을 회수하려면 몇 kg을 수확해야 하는가"를 뜻합니다. 실제 수량이 이보다 많아야 이익입니다.
- **가격 민감도**: 단가가 떨어져도 소득이 (+)로 유지되는 처리가 가격 위험에 강합니다.

**네 가지 분석 방식**
- **📕 부분예산표**: 기존 기술과 비교해 바뀌는 비용·수입만 계산
- **📗 소득분석**: 처리별 소득·순수익을 계산해 비교 (보고서·소득자료용)
- **📘 부분예산·MRR**: 지배분석 후 추가 비용 대비 순편익 증가율을 비교
- **📙 시설·장기투자**: 여러 해의 현금흐름을 할인해 NPV·할인 B/C·IRR·회수기간을 계산

MRR은 사용자가 정한 최소수용 기준과 자료 신뢰도·민감도를 함께 보고 판단합니다.""",

"survey": """**설문 분석**은 응답자 특성과 문항 응답을 함께 살펴봅니다.

**문항 유형별 분석 방법**
- **리커트 척도**(1~5점): 평균·표준편차, 긍정응답 비율, 신뢰도, 집단별 비교
- **객관식**(하나만 선택): 빈도·비율
- **다중응답**(모두 선택): 응답률(응답자 대비). 합계가 100%를 넘는 것이 정상입니다.
- **주관식**(자유 서술): 응답 목록, 주요 단어 빈도, AI 요약
- **교차분석**: 두 문항의 관계를 카이제곱 검정으로 확인

**크론바흐 알파(α) — 신뢰도**
여러 문항이 **같은 개념을 일관되게 측정하는지** 보는 지표입니다.

|α 값|해석|
|---|---|
|0.9 이상|매우 높음|
|0.8~0.9|높음|
|0.7~0.8|양호 (일반적 기준)|
|0.7 미만|낮음 — 문항 재검토 필요|

**'문항 제외 시 α'**를 보면, 어떤 문항을 뺐을 때 신뢰도가 크게 올라가는지 알 수 있습니다. 그 문항은 다른 문항들과 방향이 다르다는 뜻이니 재검토 대상입니다.

**🤖 자동 인식**을 쓰면 각 열의 값을 보고 문항 유형을 스스로 판별해 한 번에 분석합니다.""",

"report": """**자동 보고서**는 여러 분석 결과를 하나의 한글(hwpx) 문서로 만들어 줍니다.

**사용 순서**
1. 각 분석을 실행합니다.
2. 결과 아래 **'➕ 이 결과를 보고서에 담기'** 를 누릅니다.
3. 원하는 분석을 모두 담은 뒤, 이 화면에서 **'보고서 생성'** 을 누릅니다.

**보고서에 들어가는 것**: 소제목 · 해석 문장 · 결과표(`<표 1>` 캡션) · 그래프(`<그림 1>` 캡션, 가운데 정렬)

표 서식(글꼴·크기·음영·선 굵기·행 높이)은 사이드바 **⚙️ 출력 및 그래프 설정 → 문서**에서 미리 바꿀 수 있습니다.
**🕘 분석 이력**에는 언제 어떤 분석을 했는지 자동 기록되며, 이 기록도 보고서에 첨부할 수 있습니다.""",
}

# ================================================================ V1 간편형: 데이터 작성 가이드
_V1_TEMPLATES = {
    "일반 포장시험(처리×반복)": ["처리구", "반복", "초장(cm)", "생체중(g)", "수량(kg/10a)"],
    "두 요인 시험": ["품종", "처리", "반복", "수량(kg/10a)"],
    "반복측정 시험": ["개체번호", "처리구", "조사시기", "초장(cm)"],
    "상관·회귀·예측": ["개체번호", "초장(cm)", "생체중(g)", "착과수(개)", "수량(kg/10a)"],
}

# 양식에 들어가는 예시 행(회색). 사용자가 지우지 않고 올리면 데이터 점검에서 알려 준다.
_V1_TEMPLATE_EXAMPLES = {
    "일반 포장시험(처리×반복)": [
        ["대조구", 1, 72.3, 310.5, 615.4], ["대조구", 2, 70.8, 298.2, 602.1],
        ["처리1", 1, 75.6, 332.0, 648.7], ["처리1", 2, 76.1, 340.4, 655.0],
    ],
    "두 요인 시험": [
        ["품종A", "대조구", 1, 598.2], ["품종A", "처리1", 1, 640.5],
        ["품종B", "대조구", 1, 575.9], ["품종B", "처리1", 1, 622.3],
    ],
    "반복측정 시험": [
        [1, "대조구", "1차", 35.2], [1, "대조구", "2차", 52.8],
        [2, "처리1", "1차", 37.9], [2, "처리1", "2차", 58.4],
    ],
    "상관·회귀·예측": [
        [1, 72.3, 310.5, 18, 615.4], [2, 70.8, 298.2, 16, 602.1],
        [3, 75.6, 332.0, 21, 648.7], [4, 76.1, 340.4, 22, 655.0],
    ],
}
_V1_GUIDE_SHEETS = ("작성방법", "작성예시")    # 양식의 안내용 시트 — 업로드할 때 데이터로 읽지 않는다


def _v1_template_bytes(columns, examples=None):
    from openpyxl.styles import Font, PatternFill, Alignment
    out = io.BytesIO()
    examples = examples or []
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        pd.DataFrame(examples, columns=list(columns)).to_excel(writer, index=False, sheet_name="입력자료")
        pd.DataFrame({"작성방법": [
            "‘입력자료’ 시트의 회색 글씨(변수명·값)는 모두 예시입니다. 내 시험에 맞게 바꿔 입력하세요.",
            "변수명(첫 행)은 내 조사 항목 이름으로 바꾸고, 예시 값 행은 지운 뒤 실제 값을 입력합니다.",
            "첫 번째 행에는 변수명만 적습니다.",
            "한 열에는 한 가지 변수만 적습니다.",
            "한 행에는 한 조사단위만 적습니다.",
            "숫자 셀에는 숫자만 적고 단위는 열 이름에 적습니다.",
            "병합셀·중간제목·소계·합계행은 넣지 않습니다.",
            "반복1·반복2를 별도 열로 만들지 말고 반복 열 하나에 세로로 입력합니다.",
        ]}).to_excel(writer, index=False, sheet_name="작성방법")
        ws = writer.sheets["입력자료"]
        # 변수명도 예시이므로 값과 똑같이 회색 기울임으로 둔다(그대로 써야 하는 것처럼 보이지 않게).
        for cell in ws[1]:
            cell.font = Font(italic=True, color="8A8A8A")
            cell.alignment = Alignment(horizontal="center")
        for row in ws.iter_rows(min_row=2, max_row=1 + len(examples)):
            for cell in row:
                cell.font = Font(italic=True, color="8A8A8A")
        for i, col in enumerate(columns, start=1):
            ws.column_dimensions[ws.cell(1, i).column_letter].width = max(10, len(str(col)) * 2 + 2)
        ws.freeze_panes = "A2"
        wg = writer.sheets["작성방법"]
        wg.column_dimensions["A"].width = 80
        wg["A2"].font = Font(bold=True, color="C0392B")
    return out.getvalue()


def _v1_data_readiness(data):
    """업로드 직후 초보자가 고쳐야 할 자료 구조를 먼저 알려준다."""
    errors, warns, oks = [], [], []
    if data is None or getattr(data, "empty", True):
        return {"errors": ["데이터가 비어 있습니다."], "warns": [], "oks": []}
    if len(data.columns) < 2:
        errors.append("열이 1개뿐입니다. 처리구·반복·측정값을 각각 다른 열로 나눠 주세요.")
    else:
        oks.append(f"{len(data.columns)}개 변수(열)")
    oks.append(f"{len(data):,}개 관측값(행)")
    if len(data) < 3:
        warns.append("행이 3개 미만입니다. 대부분의 통계검정에는 관측값이 더 필요합니다.")
    numlike = find_numeric_like(data)
    if numlike:
        warns.append("숫자인데 문자로 저장된 열: " + ", ".join(map(str, numlike.keys()))
                     + ". `120kg`처럼 단위를 값에 붙이지 말고 `120`처럼 숫자만 적어 주세요.")
    n_miss = int(data.isna().sum().sum())
    if n_miss:
        warns.append(f"빈칸(결측치) {n_miss}개가 있습니다. 조사 누락인지 확인해 주세요.")
    n_dup = int(data.duplicated().sum())
    if n_dup:
        warns.append(f"완전히 같은 행이 {n_dup}개 있습니다. 중복 입력인지 확인해 주세요.")
    coltxt = [str(c).strip().lower() for c in data.columns]
    treat_header_hits = [c for c in coltxt if re.search(r"대조|처리\s*\d|처리[가-힣a-z]|품종\s*\d", c)]
    has_group_col = any(any(k in c for k in ("처리구", "처리", "품종", "그룹", "시험구")) for c in coltxt)
    if len(treat_header_hits) >= 2 and not has_group_col:
        warns.append("처리구가 여러 열로 가로로 펼쳐진 형태로 보입니다. `처리구 / 반복 / 측정값`처럼 세로형으로 바꾸는 것을 권장합니다.")
    repeat_wide = [c for c in coltxt if re.search(r"반복\s*[1-9]|rep\s*[1-9]", c)]
    if len(repeat_wide) >= 2:
        warns.append("`반복1`, `반복2`처럼 반복이 여러 열로 나뉜 것으로 보입니다. `반복` 열 하나에 1, 2, 3을 세로로 입력해 주세요.")
    dsg = detect_design(data)
    if dsg.get("trt"):
        oks.append(f"처리·그룹 후보: {dsg['trt']}")
        if dsg.get("blk"):
            oks.append(f"반복·블록 후보: {dsg['blk']}")
    else:
        warns.append("처리·품종 비교용 자료라면 `처리구` 또는 `품종` 열이 필요합니다. 상관·회귀·예측 자료라면 없어도 됩니다.")
    return {"errors": errors, "warns": warns, "oks": oks}

_V1_SUMMARY_ROW_RE = re.compile(r"^\s*(평균|합계|총계|소계|계|표준편차|표준오차|변이계수|cv|lsd|total|sum|mean|average|avg|sd|se)\s*$", re.I)
# '대조구 평균', '처리1 합계', '평균(대조구)'처럼 처리명이 붙은 요약 행
_V1_SUMMARY_SUFFIX_RE = re.compile(r"^\s*(?:.{1,20}?[\s(\[]*(평균|합계|총계|소계)[)\]]?|(평균|합계|소계)\s*[(\[].{1,20}[)\]])\s*$")


def _v1_is_summary_label(v):
    return isinstance(v, str) and bool(_V1_SUMMARY_ROW_RE.match(v) or _V1_SUMMARY_SUFFIX_RE.match(v))


_V1_NUM_WITH_UNIT_RE = re.compile(r"^\s*[-+]?\d[\d,]*(\.\d+)?\s*[A-Za-z가-힣%㎡㎏℃/().·]{0,8}\s*$")
_V1_PURE_NUM_RE = re.compile(r"^\s*[-+]?(\d[\d,]*)?(\.\d+)?\s*$")


def _v1_numeric_like(data, min_ratio=0.6):
    """'숫자+단위'(120kg, 1,200) 위주로 채워진 문자 열만 찾는다.

    find_numeric_like는 '처리1·처리2'처럼 이름 속 숫자까지 숫자로 보아 처리구 열을
    잘못 잡는 경우가 있어, 점검 화면에서는 값이 **숫자로 시작하는** 경우만 인정한다.
    반환: {열: 숫자로 볼 수 있는 비율(%)}
    """
    out = {}
    for c in data.columns:
        if pd.api.types.is_numeric_dtype(data[c]):
            continue
        ser = data[c].dropna().astype(str).str.strip()
        ser = ser[ser != ""]
        if ser.empty:
            continue
        ok = ser.str.match(_V1_NUM_WITH_UNIT_RE)
        if ok.mean() < min_ratio:
            continue
        # '1차·2차', '1회', '3반복', '2구'처럼 순서·구분을 나타내는 값은 측정값이 아니다.
        if ser[ok].str.contains(r"\d\s*(?:차|회|번|구|호|기|주차|반복|시기|년차)\s*$", regex=True).mean() >= 0.8:
            continue
        # '30대 이하·50대·5년 이상'처럼 나이대·기간 구간을 나타내는 설문 범주
        if ser.str.contains(r"\d\s*(?:대|세|살|년|개월)\s*(?:이하|이상|미만|초과|전후)?\s*$", regex=True).mean() >= 0.8:
            continue
        name = str(c).lower()
        if any(k in name for k in _BLOCK_KEYS + _TRT_KEYS + ["시기", "일자", "차수", "조사"]):
            continue
        out[c] = round(float(ok.mean()) * 100, 1)
    return out


def _v1_row_labels(data, idx_list, limit=5):
    """행 위치를 사용자가 엑셀에서 찾을 수 있는 번호로 바꾼다 (머리글 행 수 반영)."""
    idx_list = list(idx_list)
    hdr = int(st.session_state.get("hdr_rows", 1) or 1)
    simple = isinstance(data.index, pd.RangeIndex) and data.index.start == 0 and data.index.step == 1
    labs = [f"{int(i) + 1 + hdr}행" if simple else f"{i}번 행" for i in idx_list[:limit]]
    more = f" 외 {len(idx_list) - limit}곳" if len(idx_list) > limit else ""
    return ", ".join(labs) + more


def _v1_data_checkup(data):
    """업로드한 자료를 점검해 '무엇이 · 어디서 · 어떻게 고치는지'를 알려 준다.

    반환: [{"level": "error|warn|info|ok", "title": str, "detail": str, "fix": str}, ...]
    분석 결과에는 영향을 주지 않는 읽기 전용 점검이다.
    """
    out = []

    def add(level, title, detail="", fix=""):
        out.append({"level": level, "title": title, "detail": detail, "fix": fix})

    if data is None or getattr(data, "empty", True):
        add("error", "데이터가 비어 있습니다.", "", "파일에 값이 들어 있는지 확인해 주세요.")
        return out
    cols = [str(c) for c in data.columns]
    add("ok", f"{len(data):,}행 × {len(cols)}열을 읽었습니다.")

    # 1) 머리글(첫 행) 문제
    blank_hdr = [c for c in cols if re.fullmatch(r"열(_\d+)?", c)]
    num_hdr = [c for c in cols if re.fullmatch(r"-?\d+(\.\d+)?", c.strip())]
    if len(cols) < 2:
        add("error", "열이 1개뿐입니다.",
            "처리구·반복·측정값이 한 칸에 합쳐져 있거나, 구분 기호가 맞지 않는 CSV일 수 있습니다.",
            "처리구, 반복, 측정값을 각각 다른 열로 나눠 주세요.")
    if blank_hdr and len(blank_hdr) >= max(1, len(cols) // 2):
        add("error", "첫 행이 변수명이 아닌 것 같습니다.",
            f"이름 없는 열이 {len(blank_hdr)}개 있습니다. 표 위에 제목 행이 있거나 머리글이 병합셀일 가능성이 큽니다.",
            "엑셀에서 제목·빈 행을 지우고 **첫 행에 변수명만** 남겨 주세요. 머리글이 두 줄이면 "
            "📂 데이터 불러오기의 '변수명이 두 줄인 파일'을 켜 주세요.")
    elif blank_hdr:
        add("warn", f"이름 없는 열: {', '.join(blank_hdr)}",
            "머리글 칸이 비어 있는 열입니다.", "엑셀에서 해당 열의 첫 칸에 변수명을 적어 주세요.")
    if num_hdr and len(num_hdr) >= max(2, len(cols) // 2):
        add("error", "변수명 대신 숫자가 머리글로 읽혔습니다.",
            f"머리글: {', '.join(num_hdr[:6])}",
            "첫 행에 `처리구`, `반복`, `수량(kg/10a)`처럼 변수명을 넣어 주세요.")

    # 2) 숫자 열에 섞인 문자(단위·메모)
    numlike = _v1_numeric_like(data)
    for c, ratio in numlike.items():
        ser = data[c]
        txt = ser.dropna().astype(str).str.strip()
        bad = txt[~txt.str.match(_V1_PURE_NUM_RE) | (txt == "")]
        examples = ", ".join(f"{_v1_row_labels(data, [i])} '{v}'" for i, v in list(bad.items())[:3])
        add("warn", f"'{c}' 열에 숫자가 아닌 값이 섞여 있습니다.",
            (f"{len(bad)}칸: {examples}" + (" …" if len(bad) > 3 else "")) if len(bad) else
            "숫자가 문자 형식으로 저장되어 있습니다.",
            "숫자 칸에는 숫자만 적고 단위는 열 이름에 적어 주세요 (`120kg` ❌ → `120` ✅). "
            "통계분석 → 📋 데이터 점검의 '숫자로 자동 변환'으로 바로 고칠 수도 있습니다.")

    # 3) 빈칸
    miss = data.isna().sum()
    miss = miss[miss > 0]
    if len(miss):
        parts = []
        for c, n in miss.items():
            rows = data.index[data[c].isna()]
            parts.append(f"'{c}' {int(n)}칸({_v1_row_labels(data, rows, 3)})")
        add("warn", f"빈칸(결측) {int(miss.sum())}개가 있습니다.", " / ".join(parts[:4]) + (" …" if len(parts) > 4 else ""),
            "조사를 안 한 값이면 빈칸 그대로 두어도 됩니다. 입력을 빠뜨린 것이면 채워 주세요. "
            "'결측', '-', '없음' 같은 글자는 넣지 말고 빈칸으로 두세요.")

    # 4) 평균·합계 같은 요약 행
    obj_cols = [c for c in data.columns if not pd.api.types.is_numeric_dtype(data[c])]
    sum_rows = []
    if obj_cols:
        _hit = data[obj_cols].apply(
            lambda s_: s_.map(_v1_is_summary_label))
        sum_rows = list(data.index[_hit.any(axis=1)])
    if sum_rows:
        add("error", "평균·합계 같은 요약 행이 들어 있습니다.", _v1_row_labels(data, sum_rows),
            "요약 행은 앱이 계산합니다. 엑셀에서 해당 행을 지우고 **원자료만** 남겨 주세요.")

    # 5) 같은 처리명인데 띄어쓰기·대소문자만 다른 경우
    for c in obj_cols:
        vals = data[c].dropna().astype(str)
        if vals.nunique() > 50:
            continue
        groups = {}
        for v in vals.unique():
            groups.setdefault(re.sub(r"\s+", "", v).lower(), []).append(v)
        clash = [g for g in groups.values() if len(g) > 1]
        if clash:
            show = "; ".join(" / ".join(f"'{x}'" for x in g) for g in clash[:3])
            add("warn", f"'{c}' 열에 같은 이름이 다르게 적힌 값이 있습니다.", show,
                "띄어쓰기·대소문자가 다르면 서로 다른 처리로 계산됩니다. 한 가지로 통일해 주세요.")

    # 6) 중복 행
    dup = data.index[data.duplicated()]
    if len(dup):
        add("warn", f"완전히 같은 행이 {len(dup)}개 있습니다.", _v1_row_labels(data, dup),
            "같은 값을 두 번 붙여넣었는지 확인해 주세요. 실제로 같은 값이면 그대로 두어도 됩니다.")

    # 7) 가로로 펼친 자료
    coltxt = [c.lower() for c in cols]
    treat_header_hits = [c for c in coltxt if re.search(r"대조|처리\s*\d|처리[가-힣a-z]|품종\s*\d", c)]
    has_group_col = any(any(k in c for k in ("처리구", "처리", "품종", "그룹", "시험구")) and
                        not re.search(r"처리\s*\d|처리[가-힣a-z]", c.replace("처리구", "")) for c in coltxt)
    if len(treat_header_hits) >= 2 and not has_group_col:
        add("warn", "처리구가 여러 열로 가로로 펼쳐진 형태입니다.",
            f"열: {', '.join(treat_header_hits[:5])}",
            "`처리구 / 반복 / 측정값` 세 열로 세로로 입력해 주세요 (📘 데이터 작성 가이드 참고).")
    repeat_wide = [c for c in coltxt if re.search(r"반복\s*[1-9]|rep\s*[1-9]", c)]
    if len(repeat_wide) >= 2:
        add("warn", "반복이 여러 열로 나뉘어 있습니다.", f"열: {', '.join(repeat_wide[:5])}",
            "`반복` 열 하나에 1, 2, 3을 세로로 입력해 주세요.")

    # 8) 양식 예시 행이 남아 있는 경우
    ex_hits = []
    for _name, _rows in _V1_TEMPLATE_EXAMPLES.items():
        tcols = _V1_TEMPLATES[_name]
        if list(map(str, tcols)) != cols[:len(tcols)]:
            continue
        sub = data[data.columns[:len(tcols)]].astype(str).apply(lambda r: tuple(r.str.strip()), axis=1)
        exs = {tuple(str(v) for v in r) for r in _rows}
        ex_hits += [i for i, t in sub.items() if t in exs]
    if ex_hits:
        add("error", "엑셀 양식의 예시 행이 그대로 남아 있습니다.", _v1_row_labels(data, ex_hits),
            "회색 글씨 예시 행을 지우고 실제 조사값만 남겨 주세요.")

    # 9) 실험설계 · 반복 수
    if len(data) < 3:
        add("warn", "행이 3개 미만입니다.", "", "대부분의 통계검정에는 관측값이 더 필요합니다.")
    try:
        dsg = detect_design(data)
    except Exception:
        dsg = {}
    trt, blk = dsg.get("trt"), dsg.get("blk")
    if trt:
        cnt = data[trt].value_counts(dropna=True)
        cnt = cnt[[not _v1_is_summary_label(str(k)) for k in cnt.index]]   # 요약 행(평균·합계)은 위에서 따로 알림
        add("ok", f"처리(그룹) 열: '{trt}' — {len(cnt)}개 처리"
            + (f", 반복(블록) 열: '{blk}'" if blk else ""))
        ones = [str(k) for k, v in cnt.items() if v < 2]
        _low_cv = []
        for _y in (dsg.get("ys") or [])[:30]:
            try:
                _g = data.groupby(trt)[_y]
                _var = _g.var(ddof=1).dropna()
                _m = float(pd.to_numeric(data[_y], errors="coerce").mean())
                if len(_var) and _m and (_g.count() >= 2).all():
                    _cvw = float(np.sqrt(_var.mean())) / abs(_m) * 100
                    if _cvw < 1:
                        _low_cv.append(f"{_y}(CV {_cvw:.2f}%)")
            except Exception:
                pass
        if _low_cv:
            add("warn", "반복 간 값이 거의 같습니다.", ", ".join(_low_cv[:5]),
                "실제 포장시험에서 변이계수(CV) 1% 미만은 거의 나오지 않습니다. 평균값을 반복마다 복사해 넣지 않았는지, "
                "반복별 **원자료**를 입력했는지 확인해 주세요.")
        if ones:
            add("warn", "반복이 1개뿐인 처리가 있습니다.", ", ".join(f"'{o}'" for o in ones[:6]),
                "처리마다 반복이 2개 이상이어야 처리 간 차이를 검정할 수 있습니다.")
        elif cnt.nunique() > 1:
            add("info", "처리마다 반복(관측) 수가 다릅니다.",
                ", ".join(f"{k} {v}개" for k, v in list(cnt.items())[:6]),
                "누락된 조사값이 없는지 확인해 주세요. 불균형이어도 분석은 가능합니다.")
    elif dsg and numlike:
        # 측정값 열이 글자로 읽혀 처리 열을 판단하지 못한 경우 — 위의 '숫자가 아닌 값' 항목을 먼저 고치면 된다.
        add("info", "측정값 열이 글자로 읽혀 처리·품종 열을 아직 판단하지 못했습니다.", "",
            "위의 '숫자가 아닌 값' 항목을 고치면(또는 🔧 숫자로 자동 변환) 처리 열도 함께 인식됩니다.")
    elif dsg:
        add("info", "처리·품종 열을 찾지 못했습니다.", "",
            "처리 간 비교를 하려면 `처리구`나 `품종` 열이 필요합니다. 상관·회귀·예측만 할 거라면 없어도 됩니다.")
    _promoted = [c for c in (dsg.get("promoted") or []) if str(c).lower() not in treat_header_hits]
    if _promoted:
        add("ok", "숫자로 적힌 코드 열을 그룹으로 인식했습니다: " + ", ".join(map(str, _promoted)))

    # 10) 참고 사항
    numc = data.select_dtypes(include=np.number).columns
    neg = [str(c) for c in numc if (data[c] < 0).any()]
    if neg:
        add("info", f"음수가 있는 열: {', '.join(neg)}", "", "입력 실수가 아닌지 확인해 주세요.")
    const = [str(c) for c in data.columns if data[c].nunique(dropna=True) <= 1]
    if const:
        add("info", f"값이 모두 같은 열: {', '.join(const)}", "", "이 열은 분석에서 제외됩니다.")
    return out


def _v1_upload_sig(name):
    """불러온 원본(files[name])의 내용 서명 — 전처리로 바뀐 df가 아니라 올린 파일 자체를 기준으로 한다."""
    try:
        d = (st.session_state.get("files") or {}).get(name)
        return hash(dataframe_signature(d)) if d is not None else None
    except Exception:
        return None


def _v1_checkup_for(data):
    """점검 결과를 데이터가 바뀔 때만 다시 계산한다(버튼을 누를 때마다 다시 계산하지 않아 빠르다)."""
    if data is None:
        return _v1_data_checkup(data)
    try:
        key = (dataframe_signature(data), int(st.session_state.get("hdr_rows", 1) or 1))
    except Exception:
        return _v1_data_checkup(data)
    cache = st.session_state.setdefault("_checkup_cache", {})
    if key not in cache:
        if len(cache) >= 6:
            cache.pop(next(iter(cache)))
        cache[key] = _v1_data_checkup(data)
    return cache[key]


def _v1_checkup_counts(findings):
    return {lv: sum(1 for f in findings if f["level"] == lv) for lv in ("error", "warn", "info", "ok")}


def _v1_wrong_cases():
    """'자주 틀리는 작성 예시' — 잘못 쓴 표(앱이 읽은 모습) · 앱 경고 · 바르게 쓴 표.

    경고 문구는 여기 적지 않고 _v1_data_checkup 을 실제로 돌려서 보여 준다.
    (점검 기능이 바뀌어도 안내와 실제 경고가 어긋나지 않는다.)
    match: 점검 결과 중 이 사례를 대표하는 제목에 들어 있는 글자
    """
    right = pd.DataFrame({"처리구": ["대조구", "대조구", "처리1", "처리1"], "반복": [1, 2, 1, 2],
                          "수량": [600, 610, 650, 640]})
    _tpl = "일반 포장시험(처리×반복)"
    _ex = _V1_TEMPLATE_EXAMPLES[_tpl]
    return [
        {"name": "표 위에 제목 행·병합셀",
         "why": "엑셀 맨 위에 '2025 고추 시험 결과' 같은 제목을 넣거나 처리구 칸을 병합하면, 앱은 제목을 변수명으로 읽어요.",
         "wrong": pd.DataFrame([["처리구", "반복", "수량"], ["대조구", 1, 600], [None, 2, 610], [None, 3, 605]],
                               columns=["2025 결과", "열", "열_2"]),
         "wrong_cap": "앱이 읽은 모습 (제목이 변수명 자리에 들어감)",
         "match": "첫 행이 변수명", "right": right},
        {"name": "숫자 칸에 단위·글자",
         "why": "`610kg`, `결측`처럼 숫자 칸에 글자가 하나라도 섞이면 그 열 전체가 글자로 읽혀 계산할 수 없어요.",
         "wrong": pd.DataFrame({"처리구": ["대조구", "대조구", "대조구", "처리1", "처리1", "처리1"],
                                "수량": ["600", "610kg", "605", "650", "결측", "655"]}),
         "match": "숫자가 아닌 값",
         "right": pd.DataFrame({"처리구": ["대조구", "대조구", "대조구", "처리1", "처리1", "처리1"],
                                "수량": [600.0, 610.0, 605.0, 650.0, None, 655.0]})},
        {"name": "평균·합계 행을 같이 입력",
         "why": "처리별 평균이나 합계 행이 섞이면 그 행도 하나의 '처리'로 계산돼요.",
         "wrong": pd.DataFrame({"처리구": ["대조구", "대조구", "대조구 평균", "처리1", "처리1", "처리1 평균"],
                                "수량": [600, 610, 605, 650, 640, 645]}),
         "match": "요약 행", "right": right},
        {"name": "처리구를 가로로 펼침",
         "why": "처리구마다 열을 따로 만들면 앱이 어느 열이 처리인지 알 수 없어요.",
         "wrong": pd.DataFrame({"반복": [1, 2], "대조구": [600, 610], "처리1": [650, 640]}),
         "match": "가로로 펼쳐진", "right": right},
        {"name": "반복을 여러 열로 나눔",
         "why": "`반복1 수량`, `반복2 수량`처럼 나누면 반복 효과를 계산할 수 없어요.",
         "wrong": pd.DataFrame({"처리구": ["대조구", "처리1"], "반복1 수량": [600, 650], "반복2 수량": [610, 640]}),
         "match": "반복이 여러 열", "right": right},
        {"name": "같은 처리명을 다르게 씀",
         "why": "`대조구`와 `대조 구`, `대조구 `(뒤 공백)는 앱에서 서로 다른 처리로 나뉘어요.",
         "wrong": pd.DataFrame({"처리구": ["대조구", "대조 구", "처리1", "처리1"], "반복": [1, 2, 1, 2],
                                "수량": [600, 610, 650, 640]}),
         "match": "다르게 적힌", "right": right},
        {"name": "반복마다 평균값을 복사",
         "why": "반복별 원자료 대신 평균을 복사해 넣으면 오차가 0이 되어 결과를 믿을 수 없어요.",
         "wrong": pd.DataFrame({"처리구": ["대조구"] * 3 + ["처리1"] * 3, "반복": [1, 2, 3] * 2,
                                "수량": [605.0] * 3 + [645.0] * 3}),
         "match": "거의 같습니다", "right": right},
        {"name": "양식의 예시 행을 안 지움",
         "why": "엑셀 양식의 회색 예시 행을 남겨 두면 예시 값까지 분석에 들어가요.",
         "wrong": pd.DataFrame(_ex[:2] + [["처리2", 1, 78.2, 335.0, 690.0]], columns=_V1_TEMPLATES[_tpl]),
         "match": "예시 행", "right": None},
        {"name": "변수명이 위·아래 두 줄",
         "why": "`생육` 아래 `초장`·`경경`처럼 두 줄로 쓰면 아래 줄 이름을 못 읽어요. "
                "📂 데이터 불러오기의 **'변수명이 두 줄인 파일'**을 켜고 다시 올리면 `생육 초장(cm)`처럼 합쳐 읽어요.",
         "wrong": pd.DataFrame([[None, "초장(cm)", "경경(mm)"], ["대조구", 72.3, 14.1], ["처리1", 75.6, 14.8]],
                               columns=["처리구", "생육", "열"]),
         "wrong_cap": "앱이 읽은 모습 (아래 줄 이름이 값으로 들어감)",
         "match": "첫 행이 변수명", "right": None},
    ]


def _v1_render_checkup(findings, compact=False):
    """점검 결과를 '문제 → 위치 → 고치는 법' 순서로 보여 준다."""
    cnt = _v1_checkup_counts(findings)
    if cnt["error"]:
        st.error(f"❌ 분석 전에 꼭 고쳐야 할 문제 {cnt['error']}건" + (f", 확인할 항목 {cnt['warn']}건" if cnt["warn"] else ""))
    elif cnt["warn"]:
        st.warning(f"⚠️ 분석은 가능하지만 확인할 항목이 {cnt['warn']}건 있습니다.")
    else:
        st.success("✅ 데이터가 잘 정리되어 있습니다. 바로 분석할 수 있어요.")
    icon = {"error": "❌", "warn": "⚠️", "info": "ℹ️"}
    for f in findings:
        if f["level"] == "ok" or (compact and f["level"] == "info"):
            continue
        body = f"{icon[f['level']]} **{f['title']}**"
        if f["detail"]:
            body += f"  \n　📍 {f['detail']}"
        if f["fix"]:
            body += f"  \n　🔧 {f['fix']}"
        st.markdown(body)
    oks = [f["title"] for f in findings if f["level"] == "ok"]
    if oks and not compact:
        st.caption("✔ " + "  ·  ".join(oks))


# ================================================================ 세션
# 메뉴를 옮겨다녀도 각 화면의 선택 상태가 초기화되지 않도록 붙잡아 둔다.
# (스트림릿은 화면에 그려지지 않은 위젯의 상태를 자동으로 버린다)
# 화면(메뉴)이 바뀌면 스트림릿은 그려지지 않은 위젯의 상태를 버린다.
# 아래 키들은 각 메뉴 안에서만 그려지므로 값을 다시 써 넣어 유지한다.
# (사이드바 위젯은 매번 그려지므로 대상이 아니다)
_PINNED_DEFAULTS = {"ap_ph": "Tukey HSD", "ap_err": "표준편차(SD)"}
for _k, _v in _PINNED_DEFAULTS.items():
    st.session_state.setdefault(_k, _v)

# 전역 설정(글꼴·그래프·API키 등)과 데이터 그 자체 — 데이터가 바뀌어도 그대로 두는 키들.
_PIN_GLOBAL_EXACT = {
    "files", "df", "cur_key", "price_db", "report_items",
    "hdr_rows", "del_sel", "err_type", "round_n", "plot_color",
    "svy_type", "econ_mode", "stat_sub", "svy_chart",
    "menu_choice", "menu_main", "menu_support",
    "ap_ph", "ap_err",
    "_pin_store", "_pin_owner", "_pin_deny",
}
_PIN_GLOBAL_PREFIX = ("hwp_", "sup_", "fig_", "kamis_", "kosis_", "price_",
                      "pj_", "ai_", "api_", "dl_", "plan_", "report_",
                      "gen_report", "FormSubmitter", "$$", "uncaught",
                      # 로그인 세션·기기 기억·음성 입력·데이터 점검 상태는 데이터(시트)와 무관하다.
                      # 여기서 빠지면 데이터를 불러오거나 시트를 바꿀 때 로그아웃된다.
                      "auth_", "_auth_", "_ai_remember", "voice_", "_voice_",
                      "_checkup", "ssa_", "_home_")

# ★ 버튼·다운로드버튼 키는 st.session_state 로 값을 써 넣을 수 없다(스트림릿이 막는다).
#   여기 빠뜨리면 "Values for the widget with key '...' cannot be set using
#   st.session_state" 오류로 화면 전체가 멈추므로, 아래 목록 + 자동 학습(_pin_deny)으로
#   이중으로 막는다.
# st.file_uploader 도 session_state 로 값을 되돌릴 수 없다(ml_pf).
_PIN_BUTTON_EXACT = {
    "econ_selftest", "econ_test_run", "ml_predict1", "ml_predict2", "ml_dlpred",
    "pbd_fill", "pbd_clear", "fixnum", "sc", "price_up", "ml_pf",
    # 인증/이미지/카메라/음성 입력은 Streamlit이 값을 소유하는 비-settable 위젯이다.
    # 이 키를 _pin_sync가 session_state에 다시 쓰면 StreamlitValueAssignmentNotAllowedError가 난다.
    "auth_login_btn", "auth_signup_btn", "auth_reset_btn", "auth_logout_sidebar",
    "table_img_up", "table_cam", "img_parse_btn", "image_table_editor", "use_image_table",
    "voice_data_audio", "voice_parse_btn", "voice_rows_editor", "voice_append",
    "voice_new", "voice_clear",
    # 경제성 분석 길잡이 초기화 버튼은 버튼 상태를 session_state로 복원하면 안 된다.
    "econ_guide_reset", "econ_guide_home", "econ_switch_guide",
    # 로그인·음성 입력·데이터 점검에서 추가한 버튼/비-settable 위젯
    "auth_resend_verify", "voice_draft_import", "voice_draft_refresh",
    "voice_m_undo", "voice_m_clear", "voice_m_full", "voice_m_xlsx", "checkup_ack",
    "pdf_up", "use_pdf_table", "pdf_scan_btn", "pdf_scan_editor", "use_pdf_scan",
}
# 버튼뿐 아니라 st.data_editor 도 session_state 로 값을 써 넣을 수 없다.
# 이 앱의 해당 위젯 전부:
#   data_editor  → rank_*, pb_gain_*, pb_loss_*, price_editor
#   button       → __btn_*, btn_*, aib_*, aiadd_*, aidel_*, errai_*, list_models_*,
#                  p_*, pbd_*, ml_predict*, econ_selftest, econ_test_run,
#                  ai_conn_test, kamis_apply, kosis_*
#   download     → dl_*, ml_dlpred
# (price_*, ai_*, kamis_*, kosis_*, dl_* 는 이미 전역 목록에서 걸러진다)
_PIN_BUTTON_PREFIX = ("__btn_", "btn_", "aib_", "aiadd_", "aidel_", "errai_",
                      "list_models_", "rm_", "p_", "rank_",
                      "pb_gain_", "pb_loss_", "pbd_", "ml_predict", "ml_dl", "ms_plot_dl_",
                      "econ_entry_", "econ_g_",
                      "hwx_", "dcx_", "csv_", "xls_", "gai_",
                      "svyhwp_", "svyxls_",
                      "voice_m_audio_", "voice_m_editor_", "ssa_", "v1_tpl_", "pdf_editor_")

# 데이터와 무관하지만 '메뉴 안에서만' 그려지는 위젯들 — 데이터별로 나눌 필요는 없어도
# 매 실행마다 붙잡아 두지 않으면 다른 메뉴에 다녀올 때 기본값으로 돌아간다.
_PIN_TOUCH_GLOBAL = ("svy_type", "econ_mode", "stat_sub", "svy_chart", "ai_mode",
                     "ap_ph", "ap_err")


def _pin_scoped_keys():
    """데이터(시트)마다 따로 기억해야 하는 화면 선택 키 목록.

    경제성분석의 열 선택처럼 **열 이름에 묶인** 값들이다. 다른 데이터로 옮겼을 때
    그대로 남아 있으면 없는 열을 가리켜 위젯 오류가 나므로, 데이터별로 보관했다가
    돌아왔을 때 되돌려 준다.
    """
    out = []
    for k in list(st.session_state.keys()):
        if not isinstance(k, str):
            continue
        if k in _PIN_GLOBAL_EXACT or k.startswith(_PIN_GLOBAL_PREFIX):
            continue
        if k in _PIN_BUTTON_EXACT or k.startswith(_PIN_BUTTON_PREFIX):
            continue
        if k in st.session_state.get("_pin_deny", ()):   # 실행 중에 배운 버튼 키
            continue
        out.append(k)
    return out


def _pin_restore_defaults():
    """상태를 지운 뒤 기본값을 다시 채운다.

    `st.slider("...", 1, 15, key="ap_max")` 처럼 **value= 없이 key= 로만** 만든 위젯은
    세션에 값이 없으면 최솟값(1)으로 떨어진다. 원클릭 분석의 '한 번에 분석할
    조사항목 수'가 1이 되어 측정항목을 하나만 분석하던 원인이었다.
    """
    for k, v in _PINNED_DEFAULTS.items():
        st.session_state.setdefault(k, v)


def _pin_sync():
    """(1) 그려지지 않은 위젯의 값이 버려지지 않도록 매번 다시 써 넣고,
       (2) 분석할 데이터가 바뀌면 데이터별로 상태를 보관·복원한다.

    스트림릿은 '이번 실행에서 화면에 그려지지 않은 위젯'의 값을 버린다. 그래서
    경제성분석 → 설문조사 → 경제성분석 으로 메뉴를 옮기면 경제성 화면의 선택이
    전부 기본값으로 돌아가고, '단위 확인' 체크가 풀리면서 실행 버튼이 비활성화돼
    분석 결과까지 사라졌다. 시트를 바꿔 가며 쓰는 경우(경제성=②시트, 설문=③시트)도
    같은 문제가 생기므로 데이터별로 나눠서 보관한다.
    """
    for k in _PIN_TOUCH_GLOBAL:
        if k in st.session_state:
            try:
                st.session_state[k] = st.session_state[k]
            except Exception:
                pass
    cur = st.session_state.get("cur_key")
    store = st.session_state.setdefault("_pin_store", {})
    if "_pin_owner" not in st.session_state:
        st.session_state["_pin_owner"] = cur      # 첫 실행: 지금 상태를 현재 데이터 것으로 인정
    if st.session_state["_pin_owner"] != cur:
        prev = st.session_state["_pin_owner"]
        keys = _pin_scoped_keys()
        if prev is not None:
            store[prev] = {k: st.session_state[k] for k in keys}
        for k in keys:
            try:
                del st.session_state[k]
            except Exception:
                pass
        st.session_state["_pin_owner"] = cur
        for k, v in store.get(cur, {}).items():
            try:
                st.session_state[k] = v
            except Exception:
                pass
        _pin_restore_defaults()
        return
    for k in _pin_scoped_keys():
        try:
            st.session_state[k] = st.session_state[k]
        except Exception:
            pass
    _pin_restore_defaults()

if "files" not in st.session_state: st.session_state.files = {}
if "df" not in st.session_state: st.session_state.df = None
if "price_db" not in st.session_state: st.session_state["price_db"] = None
if "report_items" not in st.session_state: st.session_state.report_items = []

# ================================================================ 휴대폰 음성 입력 전용 화면 (?mode=voice)
# 앱 주소 뒤에 ?mode=voice 를 붙여 열면 사이드바 없이 큰 마이크 화면만 보여 준다.
# 홈 화면에 이 주소를 따로 추가해 두면 아이콘 한 번으로 바로 말하기 → 행 추가가 된다.
# 입력한 행은 로그인 계정 기준으로 Firestore(voice_drafts)에 저장돼 PC에서 이어서 불러올 수 있다.
_VOICE_PAGE_CSS = """
<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {display:none !important;}
.block-container {max-width:720px; padding-top:1.2rem !important;}
.v-hint {background:#F3FAF5; border:1px solid #CFE9D8; border-radius:12px;
         padding:.7rem .9rem; font-size:1rem; line-height:1.5; color:#24422F;}
.v-last {font-size:1.05rem; color:#17344B; margin:.4rem 0 .2rem 0;}
[data-testid="stAudioInput"] > div {min-height:84px;}
[data-testid="stAudioInput"] svg {width:34px !important; height:34px !important;}
[data-testid="stAudioInput"] button {min-width:64px; min-height:64px;}
</style>
"""

# 실시간 받아쓰기 부품. 브라우저 내장 음성 인식(크롬·사파리·엣지)으로 말하는 동안 바로 행을 채운다.
# AI 호출·API 키가 필요 없고, 행이 확정될 때마다 {"sid", "rows": 누적 행}을 파이썬으로 보낸다.
# VP(문장→행 규칙)는 파이썬 voice_parse_local과 같은 규칙이다(tests/test_voice_live.py에서 비교).
_VOICE_LIVE_HTML = r"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
:root{--ink:#17344B;--mute:#6B7C8A;--ok:#1E7A45;--okbg:#E8F6EE;--line:#D5E3EA;--card:#FFFFFF;
      --chip:#F7FAFC;--new:#FFF4C2;--go:#2F7D5B;--rec:#E8484D}
body.dark{--ink:#E8EEF2;--mute:#9DB0BE;--ok:#7FD9A5;--okbg:#183A2A;--line:#33444F;--card:#1B2630;
          --chip:#22313C;--new:#4A4220}
*{box-sizing:border-box}
html,body{margin:0;padding:0;background:transparent;color:var(--ink);
  font-family:"Pretendard","Noto Sans KR","Apple SD Gothic Neo","Malgun Gothic",sans-serif}
.wrap{padding:2px 2px 6px}
.mic{display:flex;align-items:center;gap:14px;width:100%;border:2px solid var(--line);background:var(--card);
  border-radius:18px;padding:12px 14px;cursor:pointer;color:var(--ink);text-align:left;font:inherit}
.mic .dot{flex:none;width:60px;height:60px;border-radius:50%;background:var(--go);display:flex;
  align-items:center;justify-content:center}
.mic .dot svg{width:30px;height:30px;fill:#fff}
.mic.on{border-color:var(--rec)}
.mic.on .dot{background:var(--rec);animation:pulse 1.4s infinite}
.mic.off{opacity:.55;cursor:not-allowed}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(232,72,77,.45)}70%{box-shadow:0 0 0 14px rgba(232,72,77,0)}
  100%{box-shadow:0 0 0 0 rgba(232,72,77,0)}}
.t1{display:block;font-size:1.08rem;font-weight:700}
.t2{display:block;font-size:.85rem;color:var(--mute);margin-top:2px}
.heard{min-height:1.5em;margin:10px 2px 8px;font-size:1.05rem;line-height:1.5;word-break:keep-all}
.heard .i{color:var(--mute)}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:10px}
.cap{font-size:.82rem;color:var(--mute);margin:0 0 6px}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{border:1px dashed var(--line);border-radius:10px;padding:5px 9px;min-width:70px;background:var(--chip)}
.chip b{display:block;font-size:.74rem;color:var(--mute);font-weight:600}
.chip span{font-size:1.05rem;font-weight:700}
.chip.f{border:1px solid #9AD3B1;background:var(--okbg)}
.chip.f span{color:var(--ok)}
.btns{display:flex;gap:8px;margin-top:8px}
.btns button{flex:1;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:10px;
  padding:9px;font:inherit;font-size:.95rem;cursor:pointer}
.btns button.p{background:var(--go);border-color:var(--go);color:#fff;font-weight:700}
.btns button:disabled{opacity:.4;cursor:default}
.tbl{overflow-x:auto;margin-top:10px}
table{width:100%;border-collapse:collapse;font-size:.88rem}
th,td{border-bottom:1px solid var(--line);padding:5px 6px;text-align:left;white-space:nowrap}
th{color:var(--mute);font-weight:600}
tr.new td{background:var(--new)}
.msg{margin-top:8px;padding:8px 10px;border-radius:10px;background:#FDECEC;color:#8A1F23;font-size:.9rem;
  line-height:1.45;display:none}
.tip{font-size:.8rem;color:var(--mute);margin-top:6px;line-height:1.45}
</style></head><body><div class="wrap">
<button id="mic" class="mic" type="button"><span class="dot"><svg viewBox="0 0 24 24"><path d="M12 14a3 3 0 0 0 3-3V5a3 3 0 1 0-6 0v6a3 3 0 0 0 3 3zm5-3a5 5 0 0 1-10 0H5a7 7 0 0 0 6 6.92V21h2v-3.08A7 7 0 0 0 19 11h-2z"/></svg></span><span><span class="t1" id="micT">눌러서 받아쓰기 시작</span><span class="t2" id="micS">말하는 동안 아래 칸이 바로 채워져요</span></span></button>
<div class="heard" id="heard"></div>
<div class="card">
  <p class="cap" id="cap">지금 말하는 행</p>
  <div class="chips" id="chips"></div>
  <div class="btns"><button id="bClear" type="button">✖ 이 행 지우기</button><button id="bCommit" class="p" type="button">✔ 이 행 넣기</button></div>
  <div class="tbl" id="tbl"></div>
</div>
<div class="msg" id="msg"></div>
<div class="tip">모든 열이 채워지면 자동으로 다음 행으로 넘어가요. 중간에 넘기려면 “<b>다음</b>”, 이 행을 다시 말하려면 “<b>취소</b>”, 숫자를 고치려면 “70 <b>아니</b> 71”처럼 말하세요.</div>
</div>
<script>
// ==== VOICE PARSER START
var VP = (function () {
  var DIG = {"영":0,"공":0,"일":1,"이":2,"삼":3,"사":4,"오":5,"육":6,"륙":6,"칠":7,"팔":8,"구":9};
  var POW = {"십":10,"백":100,"천":1000};
  var LETTER = {"에이":"A","비":"B","씨":"C","디":"D"};
  var NUM_RE = /^(-?\d+(?:\.\d+)?)\s*(?:킬로그램|킬로|kg|그램|g|센티미터|센티|cm|밀리미터|밀리|mm|미터|m|개|번|회|퍼센트|%|도|점)?$/i;
  var KNUM_RE = /(^|\s|-)([영공일이삼사오육륙칠팔구십백천만]+)(?:\s*점\s*([영공일이삼사오육륙칠팔구]+))?(?=$|\s)/g;
  var NEXT_RE = /(?:^|\s+)(?:다음\s*행|다음|엔터)(?=$|[\s,.!?])[.!?]?/;
  var CANCEL_RE = /(?:^|\s+)취소(?=$|[\s,.!?])[.!?]?/;
  function digits(w) { var s = ""; for (var i = 0; i < w.length; i++) s += DIG[w[i]]; return s; }
  function sino(w) {
    if (!/^[영공일이삼사오육륙칠팔구십백천만]+$/.test(w || "")) return null;
    if (!/[십백천만]/.test(w)) return parseInt(digits(w), 10);
    var total = 0, sec = 0, cur = null;
    for (var i = 0; i < w.length; i++) {
      var ch = w[i];
      if (ch in DIG) { if (cur !== null) return null; cur = DIG[ch]; }
      else if (ch in POW) { sec += (cur === null ? 1 : cur) * POW[ch]; cur = null; }
      else { total += ((sec + (cur || 0)) || 1) * 10000; sec = 0; cur = null; }
    }
    return total + sec + (cur || 0);
  }
  function num(s) {
    var t = String(s).replace(/마이너스\s*/g, "-").replace(/(\d),(\d{3})(?!\d)/g, "$1$2");
    t = t.replace(KNUM_RE, function (m, pre, a, b) {
      var v = sino(a); if (v === null) return m;
      return pre + String(v) + (b ? "." + digits(b) : "");
    });
    t = t.replace(/(\d)\s*점\s*(\d)/g, "$1.$2").replace(/\s+/g, " ").trim();
    var m = t.match(NUM_RE);
    return m ? Number(m[1]) : null;
  }
  function clean(seg) {
    var parts = String(seg || "").split(/\s*아니(?:요|고|야)?[,\s]+/);
    var s = parts[parts.length - 1];
    s = s.replace(/^[\s,.:;·~]+/, "").replace(/[\s,.;:!?·]+$/, "");
    if (/\S\s+\S/.test(s)) s = s.replace(/^(은|는|이|가|을|를|의|도|요)\s+/, "");
    s = s.replace(/\s*(입니다|이에요|예요|이고요|이고|이요|고요|이며|요)$/, "") || s;
    s = s.trim();
    if (!s) return null;
    var n = num(s);
    if (n !== null) return n;
    return LETTER.hasOwnProperty(s) ? LETTER[s] : s;
  }
  function colKey(c) {
    var k = String(c).replace(/\([^)]*\)|\[[^\]]*\]/g, "").replace(/\s+/g, "");
    return k || String(c).replace(/\s+/g, "");
  }
  function escRe(ch) { return ch.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"); }
  function splitRows(text) {
    var dropCancelled = function (p) { var a = p.split(CANCEL_RE); return a[a.length - 1].trim(); };
    var pieces = String(text || "").split(NEXT_RE);
    return { done: pieces.slice(0, -1).map(dropCancelled), rest: dropCancelled(pieces[pieces.length - 1]) };
  }
  function parse(text, cols) {
    text = String(text || "");
    cols = (cols || []).map(String);
    var row = {};
    if (!cols.length) {
      var t = text.replace(/(\d)\s*점\s*(\d)/g, "$1.$2");
      var toks = t.split(/[\s,]+/).filter(function (x) { return x; });
      var i = 0;
      while (i < toks.length) {
        var lab = toks[i];
        if (num(lab) !== null || i + 1 >= toks.length) { i++; continue; }
        var v = toks[i + 1], j = i + 2;
        if (j + 1 < toks.length && toks[j] === "점") { v = v + " 점 " + toks[j + 1]; j += 2; }
        var cv = clean(v);
        if (cv !== null) row[lab] = cv;
        i = j;
      }
      return row;
    }
    var spans = [];
    cols.slice().sort(function (a, b) { return colKey(b).length - colKey(a).length; }).forEach(function (c) {
      var re = new RegExp(Array.from(colKey(c)).map(escRe).join("\\s*"), "gi"), m;
      while ((m = re.exec(text)) !== null) {
        var s = m.index, e = s + m[0].length;
        if (e === s) { re.lastIndex++; continue; }
        if (!spans.some(function (p) { return s < p.e && e > p.s; })) spans.push({ c: c, s: s, e: e });
      }
    });
    spans.sort(function (a, b) { return a.s - b.s; });
    cols.forEach(function (c) { row[c] = null; });
    spans.forEach(function (p, k) {
      var v = clean(text.slice(p.e, k + 1 < spans.length ? spans[k + 1].s : text.length));
      if (v !== null) row[p.c] = v;
    });
    return row;
  }
  return { parse: parse, splitRows: splitRows, num: num };
})();
// ==== VOICE PARSER END

var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
var MOBILE = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
var S = { args: { columns: [], rows: [], total: 0, seen: {} },
          sid: "s" + Date.now().toString(36) + Math.random().toString(36).slice(2, 7),
          committed: [], finalBuf: "", interim: "", listening: false, rec: null,
          ignoreBelow: 0, lastLen: 0, done: {}, wake: null, flash: 0, auto: false, restored: false };
var STORE = "ssa_voice_live";
// 화면이 다시 그려져 이 부품이 새로 열려도(연결 끊김 등) 같은 접속이면 행·받아쓰기를 이어 간다.
function saveState() {
  try { sessionStorage.setItem(STORE, JSON.stringify({ token: S.args.token, sid: S.sid, committed: S.committed,
        finalBuf: S.finalBuf, listening: S.listening, t: Date.now() })); } catch (e) {}
}
function tryRestore() {
  if (S.restored) return;
  S.restored = true;
  var d = null;
  try { d = JSON.parse(sessionStorage.getItem(STORE) || "null"); } catch (e) {}
  if (!d || !S.args.token || d.token !== S.args.token || Date.now() - d.t > 6 * 3600 * 1000) { saveState(); return; }
  S.sid = d.sid; S.committed = d.committed || []; S.finalBuf = d.finalBuf || "";
  if (S.committed.length > ((S.args.seen || {})[S.sid] || 0)) send();   // 못 받은 행이 있으면 다시 보냄
  if (d.listening && SR) { S.auto = true; startRec(); }
}
var $ = function (id) { return document.getElementById(id); };

function post(type, extra) {
  var m = { isStreamlitMessage: true, type: type };
  for (var k in (extra || {})) m[k] = extra[k];
  window.parent.postMessage(m, "*");
}
var lastH = 0;
function height() {   // 내용 높이만 잰다(문서 높이는 틀 높이 이상이라 재면 계속 커짐)
  var h = Math.ceil(document.querySelector(".wrap").getBoundingClientRect().height) + 4;
  if (h !== lastH) { lastH = h; post("streamlit:setFrameHeight", { height: h }); }
}
function send() { post("streamlit:setComponentValue", { value: { sid: S.sid, rows: S.committed }, dataType: "json" }); }
function esc(v) {
  return String(v === null || v === undefined ? "" : v).replace(/[&<>"]/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; });
}
function cols() {
  var c = S.args.columns || [];
  if (c.length) return c;
  return S.committed.length ? Object.keys(S.committed[0]) : [];
}
function filled(v) { return v !== null && v !== undefined && v !== ""; }
function hasVal(r) { return Object.keys(r || {}).some(function (k) { return filled(r[k]); }); }
function full(r, c) { return c.length > 0 && c.every(function (k) { return filled(r[k]); }); }

function commitRow(r) {
  if (!hasVal(r)) return false;
  S.committed.push(r);
  S.flash = Date.now();
  send();
  saveState();
  try { if (navigator.vibrate) navigator.vibrate(40); } catch (e) {}
  return true;
}
function absorbFinal() {
  var sp = VP.splitRows(S.finalBuf);
  sp.done.forEach(function (t) { commitRow(VP.parse(t, cols())); });
  S.finalBuf = sp.rest;
  var c = cols();
  if (c.length) {
    var r = VP.parse(S.finalBuf, c);
    if (full(r, c)) { commitRow(r); S.finalBuf = ""; }
  }
}
function liveText() { return VP.splitRows((S.finalBuf + " " + S.interim).trim()).rest; }
function resetRow() { S.finalBuf = ""; S.interim = ""; S.ignoreBelow = S.lastLen; }

function showMsg(t) { var m = $("msg"); m.innerHTML = t || ""; m.style.display = t ? "block" : "none"; height(); }

function drawMic() {
  var b = $("mic");
  b.className = "mic" + (S.listening ? " on" : "") + (SR ? "" : " off");
  $("micT").textContent = S.listening ? "듣는 중… 누르면 멈춤" : "눌러서 받아쓰기 시작";
  $("micS").textContent = S.listening ? "한 행씩 말하세요. 예) 처리구 A 반복 1 초장 72.3"
                                      : "말하는 동안 아래 칸이 바로 채워져요";
}

function draw() {
  var c = cols(), lt = liveText(), r = VP.parse(lt, c);
  $("heard").innerHTML = S.finalBuf || S.interim
    ? esc(S.finalBuf) + ' <span class="i">' + esc(S.interim) + "</span>"
    : '<span class="i">' + (S.listening ? "듣고 있어요…" : "") + "</span>";
  var keys = c.length ? c : Object.keys(r);
  $("chips").innerHTML = keys.length ? keys.map(function (k) {
    var v = r[k];
    return '<div class="chip' + (filled(v) ? " f" : "") + '"><b>' + esc(k) + "</b><span>" +
           (filled(v) ? esc(v) : "—") + "</span></div>";
  }).join("") : '<span class="cap">예) “처리구 A, 반복 1, 초장 72.3, 수량 615.4”</span>';
  $("bCommit").disabled = !hasVal(r);
  $("bClear").disabled = !lt;

  var seen = (S.args.seen || {})[S.sid] || 0;
  var pending = S.committed.slice(seen);
  var base = S.args.rows || [];
  var all = base.concat(pending), shown = all.slice(-3);
  var total = (S.args.total || 0) + pending.length;
  var head = c.length ? c : (shown.length ? Object.keys(shown[0]) : []);
  var recent = Date.now() - S.flash < 6000;
  $("cap").textContent = "지금 말하는 행" + (total ? "  ·  표에 " + total + "행" : "");
  $("tbl").innerHTML = shown.length ? "<table><tr>" + head.map(function (h) { return "<th>" + esc(h) + "</th>"; }).join("") +
    "</tr>" + shown.map(function (row, i) {
      var isNew = recent && i === shown.length - 1;
      return '<tr class="' + (isNew ? "new" : "") + '">' + head.map(function (h) { return "<td>" + esc(row[h]) + "</td>"; }).join("") + "</tr>";
    }).join("") + "</table>" : "";
  height();
}

function keepAwake(on) {
  try {
    if (on && navigator.wakeLock && !S.wake) navigator.wakeLock.request("screen").then(function (w) { S.wake = w; }).catch(function () {});
    if (!on && S.wake) { S.wake.release(); S.wake = null; }
  } catch (e) {}
}

function startRec() {
  if (!SR) return;
  showMsg("");
  var rec = new SR();
  rec.lang = "ko-KR";
  rec.interimResults = true;
  rec.continuous = !MOBILE;          // 휴대폰은 한 번씩 끊어 듣고 자동으로 다시 시작(중복 인식 방지)
  rec.maxAlternatives = 1;
  rec.onstart = function () { S.ignoreBelow = 0; S.lastLen = 0; S.done = {}; };
  rec.onresult = function (e) {
    var inter = "";
    for (var i = e.resultIndex; i < e.results.length; i++) {
      var res = e.results[i], t = res[0].transcript;
      if (res.isFinal) {
        if (i < S.ignoreBelow || S.done[i]) continue;
        S.done[i] = 1;
        S.finalBuf = (S.finalBuf + " " + t).trim();
        absorbFinal();
      } else if (i >= S.ignoreBelow) {
        inter += t;
      }
    }
    S.interim = inter;
    S.lastLen = e.results.length;
    S.auto = false;
    saveState();
    draw();
  };
  rec.onerror = function (e) {
    var er = e.error || "";
    if ((er === "not-allowed" || er === "service-not-allowed") && S.auto) {
      S.listening = false; S.auto = false; saveState();
      showMsg("화면이 새로 그려져 받아쓰기가 멈췄어요. 마이크를 다시 눌러 주세요. 입력한 행은 그대로 있어요.");
    } else if (er === "not-allowed" || er === "service-not-allowed") {
      S.listening = false;
      showMsg("마이크를 쓸 수 없어요. 주소창 옆 자물쇠(또는 설정)에서 <b>마이크 허용</b>을 켠 뒤 다시 눌러 주세요." +
              (/iPhone|iPad/i.test(navigator.userAgent) ? "<br>아이폰은 설정 → Siri 및 검색에서 <b>Siri 받아쓰기</b>가 켜져 있어야 해요." : ""));
    } else if (er === "network") {
      S.listening = false;
      showMsg("인터넷 연결이 불안정해 받아쓰기가 멈췄어요. 잠시 후 다시 눌러 주세요.");
    } else if (er === "audio-capture") {
      S.listening = false;
      showMsg("마이크를 찾지 못했어요. 다른 앱이 마이크를 쓰고 있는지 확인해 주세요.");
    }
  };
  rec.onend = function () {
    if (S.interim) { S.finalBuf = (S.finalBuf + " " + S.interim).trim(); S.interim = ""; absorbFinal(); saveState(); }
    if (S.listening) {
      setTimeout(function () { if (S.listening) { try { rec.start(); } catch (x) {} } }, 120);
    } else {
      keepAwake(false);
    }
    drawMic(); draw();
  };
  S.rec = rec;
  S.listening = true;
  saveState();
  try { rec.start(); } catch (x) {}
  keepAwake(true);
  drawMic(); draw();
}
function stopRec() {
  S.listening = false;
  saveState();
  try { if (S.rec) S.rec.stop(); } catch (x) {}
  keepAwake(false);
  drawMic(); draw();
}

$("mic").onclick = function () {
  if (!SR) return;
  if (S.listening) stopRec(); else startRec();
};
$("bCommit").onclick = function () {
  if (commitRow(VP.parse(liveText(), cols()))) { resetRow(); saveState(); }
  draw();
};
$("bClear").onclick = function () { resetRow(); saveState(); draw(); };

window.addEventListener("message", function (e) {
  var d = e.data || {};
  if (d.type !== "streamlit:render") return;
  S.args = d.args || S.args;
  var th = d.theme || {};
  document.body.classList.toggle("dark", th.base === "dark");
  tryRestore();
  draw();
});
if (!SR) {
  showMsg("이 브라우저는 실시간 받아쓰기를 지원하지 않아요. 휴대폰은 <b>크롬(안드로이드)·사파리(아이폰)</b>, PC는 크롬·엣지에서 열어 주세요." +
          "<br>카카오톡 등 앱 안에서 열었다면 ‘다른 브라우저로 열기’를 눌러 주세요. 또는 위에서 <b>녹음 후 AI 정리</b>를 고르세요.");
}
drawMic(); draw();
post("streamlit:componentReady", { apiVersion: 1 });
</script></body></html>
"""


_VOICE_WAYS = ["⚡ 실시간 받아쓰기", "🎙️ 녹음 후 AI 정리"]


def _voice_columns_from_text(text):
    return [c.strip() for c in re.split(r"[,，/·]", str(text or "")) if c.strip()]


def _voice_uid():
    u = _current_auth_user()
    return (u or {}).get("id")


def _voice_draft_save():
    """휴대폰에서 입력한 행을 계정별로 저장한다(PC에서 이어서 불러오기용). 실패해도 입력은 계속된다."""
    import json
    uid = _voice_uid()
    if not uid:
        return
    rows = st.session_state.get("voice_rows") or []
    try:
        _fs_set("voice_drafts", uid, {
            "rows_json": json.dumps(rows, ensure_ascii=False, default=str),
            "columns": st.session_state.get("voice_cols_text", ""),
            "count": len(rows), "updated_at": _now_utc()})
    except Exception:
        pass
    st.session_state.pop("_voice_draft_cache", None)


def _voice_draft_peek(force=False):
    """저장된 휴대폰 입력 초안. {"rows": [...], "columns": str, "updated_at": str} 또는 None."""
    import json
    uid = _voice_uid()
    if not uid:
        return None
    if not force and "_voice_draft_cache" in st.session_state:
        return st.session_state["_voice_draft_cache"]
    d = _fs_get("voice_drafts", uid) or {}
    try:
        rows = json.loads(d.get("rows_json") or "[]")
    except Exception:
        rows = []
    out = {"rows": rows, "columns": d.get("columns", ""), "updated_at": d.get("updated_at", "")} if rows else None
    st.session_state["_voice_draft_cache"] = out
    return out


def _voice_process(binary, mime_type):
    """녹음 한 개 → (행 dict 또는 None, 인식 문장, 경고 목록). 네트워크 호출은 여기서만 한다."""
    tr = ai_multimodal_text(binary, mime_type or "audio/wav",
                            "한국어 음성을 정확히 전사하세요.", kind="audio")
    if str(tr).startswith("⚠️"):
        return None, "", [str(tr)]
    row, warn = voice_text_to_row(tr, _voice_target_columns())
    return row, tr, list(warn or [])


_VOICE_LIVE_LOADER = """from streamlit.components.v1 import declare_component


def make(path):
    return declare_component("ssa_voice_live", path=path)
"""


def _voice_live_declare(html):
    """부품 HTML을 임시 폴더에 써서 Streamlit 부품으로 등록한다(저장소에 폴더를 따로 올릴 필요 없음).

    declare_component는 호출한 모듈 이름으로 부품을 구분하므로, 작은 로더 모듈을 만들어 그 안에서 호출한다.
    """
    import hashlib, importlib.util, os, sys, tempfile
    d = os.path.join(tempfile.gettempdir(), "ssa_voice_live_" + hashlib.sha1(html.encode("utf-8")).hexdigest()[:10])
    page, loader = os.path.join(d, "index.html"), os.path.join(d, "ssa_voice_live_loader.py")
    if not os.path.exists(page) or not os.path.exists(loader):
        os.makedirs(d, exist_ok=True)
        for fp, text in ((page, html), (loader, _VOICE_LIVE_LOADER)):
            with open(fp, "w", encoding="utf-8") as f:
                f.write(text)
    mod = sys.modules.get("ssa_voice_live_loader")
    if mod is None or os.path.dirname(getattr(mod, "__file__", "")) != d:
        spec = importlib.util.spec_from_file_location("ssa_voice_live_loader", loader)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["ssa_voice_live_loader"] = mod
        spec.loader.exec_module(mod)
    return mod.make(d)


def _voice_records(df):
    """표 → 행 목록. 빈칸·NaN은 None으로(JSON·Firestore에 그대로 실을 수 있게)."""
    return df.astype(object).where(pd.notna(df), None).to_dict("records")


def _voice_jsonable(rows):
    """부품으로 보낼 행: NumPy 값은 파이썬 값으로, NaN·무한대는 None으로(JSON에 NaN이 섞이면 부품이 깨진다)."""
    import math

    def one(v):
        if hasattr(v, "item") and not isinstance(v, str):
            try:
                v = v.item()
            except Exception:
                v = str(v)
        if isinstance(v, float) and not math.isfinite(v):
            return None
        return v if v is None or isinstance(v, (str, int, float, bool)) else str(v)
    return [{str(k): one(v) for k, v in r.items()} for r in rows]


def _voice_target_columns():
    cols = _voice_columns_from_text(st.session_state.get("voice_cols_text"))
    rows = st.session_state.get("voice_rows") or []
    if not cols and rows:
        cols = list(rows[0].keys())          # 열 이름을 안 적었으면 첫 행의 열을 계속 사용
    return cols


def _voice_live_absorb(val):
    """실시간 부품이 보낸 누적 행 중 아직 표에 넣지 않은 행만 붙인다. 반환: 새로 붙인 행 수.

    부품은 확정된 행을 모두 다시 보내므로(중간 전송이 묶여도 빠지지 않게) 부품별(sid)로
    몇 행까지 받았는지 기억한다. 표를 비우거나 마지막 행을 취소해도 같은 행이 되살아나지 않는다.
    """
    if not isinstance(val, dict):
        return 0
    sid, rows = str(val.get("sid") or ""), val.get("rows")
    if not sid or not isinstance(rows, list):
        return 0
    seen = st.session_state.setdefault("_voice_live_seen", {})
    start = int(seen.get(sid, 0))
    seen[sid] = len(rows)
    new = [r for r in rows[start:] if isinstance(r, dict)]
    if not new:
        return 0
    cols = _voice_target_columns() or list(new[0].keys())
    new = [{c: r.get(c) for c in cols} for r in new]
    st.session_state.setdefault("voice_rows", []).extend(new)
    _voice_draft_save()
    _record_usage("음성 입력(실시간)")
    return len(new)


def _voice_live_widget():
    key = "voice_live_comp"
    _voice_live_absorb(st.session_state.get(key))       # 앞 실행에서 들어온 행을 먼저 반영
    rows = st.session_state.get("voice_rows") or []
    token = st.session_state.setdefault("_voice_live_token", __import__("uuid").uuid4().hex)
    args = {"token": token,
            "columns": _voice_target_columns(),
            "rows": _voice_jsonable(rows[-3:]),
            "total": len(rows),
            "seen": dict(st.session_state.get("_voice_live_seen") or {})}
    val = _voice_live_declare(_VOICE_LIVE_HTML)(key=key, default=None, height=330, **args)
    if _voice_live_absorb(val):
        st.rerun()                                       # 부품 아래 표에 새 행이 바로 보이도록


def _voice_ai_settings():
    providers = [p for p in _AI_PROVIDERS if not str(p).startswith("Claude")]
    if st.session_state.get("ai_provider") not in providers:
        st.session_state["ai_provider"] = providers[0]
    prov = st.selectbox("AI 제공사", providers, key="ai_provider",
                        help="음성 인식은 ChatGPT 또는 Gemini만 지원합니다.")
    st.caption(f"🔑 {_AI_PROVIDERS[prov]['key_hint']}")
    st.text_input("API 키", type="password", key="api_key")
    models = list(_AI_PROVIDERS[prov]["models"])
    if models and st.session_state.get("ai_model_g") not in models:
        st.session_state["ai_model_g"] = models[0]
    _ai_remember_widget()


def render_voice_mode():
    st.markdown(_VOICE_PAGE_CSS, unsafe_allow_html=True)
    st.markdown("### 🎤 음성 데이터 입력")

    # 첫 접속: PC/다른 기기에서 입력하던 행과 열 이름을 이어서 불러온다.
    if not st.session_state.get("_voice_draft_loaded"):
        st.session_state["_voice_draft_loaded"] = True
        d = _voice_draft_peek(force=True)
        if d and not st.session_state.get("voice_rows"):
            st.session_state["voice_rows"] = d["rows"]
        if d and d.get("columns") and not st.session_state.get("voice_cols_text"):
            st.session_state["voice_cols_text"] = d["columns"]

    way = st.radio("입력 방식", _VOICE_WAYS, key="voice_m_way", horizontal=True,
                   help="실시간: 말하는 동안 표가 바로 채워집니다(브라우저 음성 인식, API 키 불필요).\n\n"
                        "녹음 후 AI 정리: 시끄러운 곳이나 실시간 인식이 안 되는 브라우저에서 사용하세요(API 키 필요).")
    st.text_input("열 이름 (선택)", key="voice_cols_text",
                  placeholder="예) 처리구, 반복, 초장, 수량",
                  help="적어 두면 모든 행이 같은 열로 정리되고, 실시간 모드에서는 모든 열이 채워질 때 자동으로 다음 행으로 넘어갑니다. "
                       "비워 두면 첫 행을 기준으로 맞춥니다.")

    if way == _VOICE_WAYS[0]:
        # 실시간 부품 위에는 조건부 요소를 두지 않는다(위치가 바뀌면 부품이 새로 열려 받아쓰기가 끊김).
        _voice_live_widget()
    else:
        st.markdown('<div class="v-hint">마이크를 누르고 <b>한 행씩</b> 말한 뒤 다시 누르면 표에 추가됩니다.<br>'
                    '예) “처리구 A, 반복 1, 초장 72.3, 수량 615.4”</div>', unsafe_allow_html=True)
        need_key = not st.session_state.get("api_key") or str(st.session_state.get("ai_provider", "")).startswith("Claude")
        with st.expander("🔌 음성 인식 설정", expanded=need_key):
            _voice_ai_settings()
        n = st.session_state.setdefault("voice_rec_n", 0)
        aud = st.audio_input("🎙️ 눌러서 말하기", sample_rate=16000, key=f"voice_m_audio_{n}")
        if aud is not None:
            if not st.session_state.get("api_key"):
                st.error("위 '🔌 음성 인식 설정'에서 API 키를 먼저 넣어 주세요.")
            else:
                with st.spinner("듣고 표로 정리하는 중..."):
                    row, tr, warn = _voice_process(aud.getvalue(), getattr(aud, "type", None))
                st.session_state["voice_transcript"] = tr
                st.session_state["voice_warn"] = warn
                if row is not None:
                    st.session_state.setdefault("voice_rows", []).append(row)
                    _voice_draft_save()
                    _record_usage("음성 입력(휴대폰)")
                st.session_state["voice_rec_n"] = n + 1       # 다음 행을 위해 녹음기를 새로 만든다
                st.rerun()

    if way != _VOICE_WAYS[0] and st.session_state.get("voice_transcript"):
        st.markdown(f'<div class="v-last">🗣️ {st.session_state["voice_transcript"]}</div>',
                    unsafe_allow_html=True)
    for w in ((st.session_state.get("voice_warn") or [])[:3] if way != _VOICE_WAYS[0] else []):
        (st.error if str(w).startswith("⚠️") else st.warning)(w if str(w).startswith("⚠️") else f"확인 필요: {w}")

    rows = st.session_state.get("voice_rows") or []
    if rows:
        st.markdown(f"**입력한 데이터 {len(rows)}행** — 칸을 눌러 바로 고칠 수 있어요.")
        vdf = pd.DataFrame(rows)
        edited = st.data_editor(vdf, num_rows="dynamic", width="stretch",
                                key=f"voice_m_editor_{len(rows)}_{st.session_state.get('voice_rec_n', 0)}")
        # 빈칸(NaN)은 None으로 바꿔 비교·저장한다. NaN은 NaN과 같지 않아 매 실행마다 '바뀜'으로
        # 판정되어 저장이 반복되고, JSON에도 실을 수 없다.
        new_rows = _voice_records(edited)
        if new_rows != _voice_records(vdf):
            st.session_state["voice_rows"] = new_rows
            _voice_draft_save()
        c1, c2 = st.columns(2)
        if c1.button("↩️ 마지막 행 취소", width="stretch", key="voice_m_undo"):
            st.session_state["voice_rows"] = rows[:-1]
            _voice_draft_save()
            st.rerun()
        c2.download_button("📥 엑셀로 받기",
                           dataframe_to_styled_xlsx(clean_columns(pd.DataFrame(st.session_state["voice_rows"])),
                                                    "음성 입력 데이터", "음성입력"),
                           "음성입력데이터.xlsx", width="stretch", key="voice_m_xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        if _voice_uid() and _fs_session() is not None:
            st.caption("💻 PC에서 같은 계정으로 로그인하면 **📂 데이터 불러오기**에서 이 표를 바로 불러와 분석할 수 있어요.")
        with st.expander("🗑️ 표 비우기"):
            st.caption("입력한 행을 모두 지웁니다. 되돌릴 수 없어요.")
            if st.button("모두 지우기", width="stretch", key="voice_m_clear"):
                st.session_state["voice_rows"] = []
                st.session_state.pop("voice_transcript", None)
                _voice_draft_save()
                st.rerun()

    st.divider()
    if st.button("💻 전체 기능 화면으로", width="stretch", key="voice_m_full"):
        st.query_params.clear()
        st.rerun()


def _is_voice_mode():
    try:
        return str(st.query_params.get("mode", "")).strip().lower() == "voice"
    except Exception:
        return False


# Firebase가 설정되고 AUTH_REQUIRED=true이면 로그인한 사용자만 아래 앱을 렌더링합니다.
render_auth_gate()
_ai_remember_load()
if _is_voice_mode():
    render_voice_mode()
    st.stop()

# ================================================================ 사이드바
st.sidebar.markdown("""
<div class="v1-sidebar-brand">
  <div class="v1-sidebar-brand-title">스마트 통계 에이전트</div>
  <div class="v1-sidebar-brand-sub"><span class="v1-ver">Version 1</span><span class="v1-sub-txt">실험 데이터 자동 통계 분석</span></div>
</div>
""", unsafe_allow_html=True)

# 로그인 사용자의 소속을 사이드바에 표시한다.
_auth_u = _current_auth_user()
if _auth_u:
    _meta = _auth_u.get("user_metadata") or {}
    _who = _meta.get("name") or str(_auth_u.get("email", "")).split("@")[0]
    _org = _meta.get("organization") or "소속 미입력"
    st.sidebar.markdown(f"**👤 {_who}**  \n🏢 {_org}")
    if st.sidebar.button("로그아웃", width="stretch", key="auth_logout_sidebar"):
        _auth_logout()

st.sidebar.markdown("""
<style>
[data-testid="stSidebar"] .st-key-v1_guide_block [data-testid="stExpander"] details {
    border:2px solid #F2C94C !important; background:#FFFBEA !important; border-radius:12px !important;
}
[data-testid="stSidebar"] .st-key-v1_guide_block [data-testid="stExpander"] summary p {
    font-weight:800 !important; color:#7A5A00 !important; font-size:1rem !important;
}
[data-testid="stSidebar"] .st-key-v1_guide_block [data-testid="stExpander"] [data-testid="stExpander"] details {
    border:1px solid #E6D9A8 !important; background:#FFFFFF !important; border-radius:8px !important;
}
[data-testid="stSidebar"] .st-key-v1_guide_block [data-testid="stExpander"] [data-testid="stExpander"] summary p {
    font-weight:600 !important; color:#5B4A1A !important; font-size:.9rem !important;
}
</style>""", unsafe_allow_html=True)
with st.sidebar.container(key="v1_guide_block"), st.expander(
        "📘 데이터 작성 가이드 — 처음이면 꼭 보세요!", expanded=not bool(st.session_state.get("files"))):
    st.markdown("""
**기본 원칙**
- 첫 행에는 변수명만 입력
- 한 열 = 한 변수, 한 행 = 한 조사단위
- 숫자 셀에는 숫자만 입력 (`120kg` ❌ → `120` ✅)
- 단위는 열 이름에 입력 (`수량(kg/10a)`)
- 병합셀·중간제목·평균·합계행은 넣지 않기
""")
    st.markdown("**✅ 권장 예시**")
    smart_table(pd.DataFrame({
        "처리구": ["대조구", "대조구", "처리1", "처리1"],
        "반복": [1, 2, 1, 2],
        "수량(kg/10a)": [500, 510, 560, 555],
    }), hide_index=True, width="stretch")
    with st.expander("❌ 자주 틀리는 작성 예시"):
        # 사례를 하나씩 골라 보게 한다(사이드바가 길어지지 않게). 경고 문구는 실제 점검 기능의 결과다.
        _cases = _v1_wrong_cases()
        _pick = st.selectbox("사례 고르기", [f"{i}. {c['name']}" for i, c in enumerate(_cases, 1)],
                             key="sup_wrong_case")
        _c = _cases[int(_pick.split(".")[0]) - 1]
        st.markdown(_c["why"])
        st.markdown("**❌ 이렇게 쓰면**")
        if _c.get("wrong_cap"):
            st.caption(_c["wrong_cap"])
        def _guide_view(d):
            # 사이드바가 좁아서 앞의 3개 열만, 빈칸은 빈칸으로, 정수는 소수점 없이 보여 준다.
            v = d.iloc[:, :3].astype(object).where(d.iloc[:, :3].notna(), "")
            v = v.map(lambda x: int(x) if isinstance(x, float) and float(x).is_integer() else x)
            if d.shape[1] > 3:
                st.caption(f"(열 {d.shape[1]}개 중 앞의 3개만 표시)")
            smart_table(v, hide_index=True, width="stretch")
        _guide_view(_c["wrong"])
        _fs = [f for f in _v1_data_checkup(_c["wrong"])
               if f["level"] in ("error", "warn") and _c["match"] in f["title"]]
        if _fs:
            _f = _fs[0]
            st.markdown("**📋 앱에는 이렇게 떠요**")
            _msg = f"{'❌' if _f['level'] == 'error' else '⚠️'} **{_f['title']}**"
            if _f["fix"]:
                _msg += f"  \n🔧 {_f['fix']}"
            (st.error if _f["level"] == "error" else st.warning)(_msg)
        if _c.get("right") is not None:
            st.markdown("**✅ 이렇게 고쳐요**")
            _guide_view(_c["right"])
    st.markdown("**엑셀 양식 (예시 포함)**")
    st.caption("회색 글씨(변수명·값)는 예시입니다. 내 시험에 맞게 바꿔 입력하세요.")
    _tpl_name = "일반 포장시험(처리×반복)"
    st.download_button(
        "📥 엑셀 양식 받기", _v1_template_bytes(_V1_TEMPLATES[_tpl_name], _V1_TEMPLATE_EXAMPLES[_tpl_name]),
        file_name="스마트통계_데이터_양식.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="v1_tpl_main", width="stretch")

with st.sidebar.expander("📂 데이터 불러오기", expanded=True):
    # 휴대폰 음성 입력 화면(?mode=voice)에서 쌓아 둔 행이 있으면 바로 불러올 수 있게 한다.
    _vd = _voice_draft_peek() if (_voice_uid() and _fs_session() is not None) else None
    if _vd:
        st.info(f"📱 휴대폰 음성 입력 **{len(_vd['rows'])}행**이 있어요.")
        _vc1, _vc2 = st.columns([3, 1])
        if _vc1.button("📱 불러와서 분석", width="stretch", key="voice_draft_import"):
            _k = "휴대폰_음성입력"
            st.session_state.files[_k] = clean_columns(pd.DataFrame(_vd["rows"]))
            st.session_state.cur_key = _k
            st.session_state.df = st.session_state.files[_k].copy()
            st.session_state["voice_rows"] = list(_vd["rows"])
            st.rerun()
        if _vc2.button("🔄", width="stretch", key="voice_draft_refresh", help="휴대폰에서 방금 입력한 행 다시 확인"):
            _voice_draft_peek(force=True)
            st.rerun()
    _input_mode = st.radio("입력 방식", ["📁 Excel/CSV", "📷 이미지/사진", "📄 PDF", "🎤 음성"],
                           horizontal=False, key="data_input_mode")

    if _input_mode == "📁 Excel/CSV":
        ups = st.file_uploader("Excel / CSV 업로드 (여러 개 가능)",
                               type=["xlsx", "xls", "csv"], accept_multiple_files=True)
        st.session_state.setdefault("hdr_rows", 1)
        with st.expander("고급 · 변수명이 두 줄인 파일", expanded=False):
            _two_header = st.checkbox("변수명이 위·아래 두 줄로 나뉘어 있습니다",
                                      value=(int(st.session_state.get("hdr_rows", 1)) == 2),
                                      key="v1_two_header")
            st.session_state["hdr_rows"] = 2 if _two_header else 1
            st.caption("대부분의 파일은 끈 상태(머리글 1행)가 맞습니다.")
        hdr_rows = int(st.session_state.get("hdr_rows", 1))
        st.caption("엑셀에 시트가 여러 개면 시트별로 나뉘어 들어옵니다. "
                   "값을 바꾸면 올려둔 파일을 **자동으로 다시 읽습니다**(새로고침 불필요).")
        # 머리글 행 수를 바꾸면 이미 올린 파일을 다시 읽어 화면에도 즉시 반영한다.
        _hdr_changed = st.session_state.get("__hdr_prev") not in (None, hdr_rows)
        st.session_state["__hdr_prev"] = hdr_rows
        if ups:
            head = [0, 1] if hdr_rows == 2 else 0
            for uf in ups:
                try:
                    if uf.name.endswith(".csv"):
                        d = None
                        for _enc in ("utf-8-sig", "cp949", "euc-kr", "utf-8"):
                            try:
                                uf.seek(0)
                                d = pd.read_csv(uf, header=head, encoding=_enc)
                                break
                            except (UnicodeDecodeError, LookupError):
                                continue
                            except Exception:
                                uf.seek(0)
                                d = pd.read_csv(uf, header=head, encoding_errors="replace")
                                break
                        if d is None:
                            st.error(f"'{uf.name}' 파일의 문자 인코딩을 읽지 못했습니다. "
                                     "엑셀에서 'CSV UTF-8'로 다시 저장해 보세요.")
                            continue
                        if hdr_rows == 2:
                            d.columns = [" ".join([str(x) for x in c if "Unnamed" not in str(x)]).strip()
                                         for c in d.columns]
                        # 병합된 두 줄 헤더를 이어붙이면, 블록 사이의 빈 구분용 열까지 앞 헤더를
                        # 그대로 물려받아 "가격" 같은 이름이 중복 생성될 수 있다. 데이터가 전혀
                        # 없는(전부 결측) 열은 실제 문항이 아니라 이 구분용 유령 열이므로 제거한다.
                        d = d.dropna(axis=1, how="all")
                        st.session_state.files[uf.name] = clean_columns(d)
                    else:
                        xls = pd.ExcelFile(uf)
                        _data_sheets = [sh for sh in xls.sheet_names
                                        if str(sh).strip() not in _V1_GUIDE_SHEETS] or xls.sheet_names
                        for sh in _data_sheets:      # 시트별로 저장 (양식의 안내 시트는 제외)
                            d = pd.read_excel(xls, sheet_name=sh, header=head)
                            if hdr_rows == 2:
                                d.columns = [" ".join([str(x) for x in c if "Unnamed" not in str(x)]).strip()
                                             for c in d.columns]
                            # 위와 동일한 이유로, 병합헤더가 물려준 빈 구분용 열(전부 결측)은 제거
                            d = d.dropna(axis=1, how="all")
                            key = f"{uf.name} – {sh}" if len(_data_sheets) > 1 else uf.name
                            st.session_state.files[key] = clean_columns(d)
                except Exception as e:
                    st.error(f"{uf.name} 읽기 실패: {e}")
            if _hdr_changed:
                # 다시 읽은 결과를 현재 분석 화면에도 즉시 적용
                _cur = st.session_state.get("cur_key")
                if _cur in st.session_state.files:
                    st.session_state.df = st.session_state.files[_cur].copy()
                st.success(f"머리글 {hdr_rows}행 기준으로 다시 읽었습니다.")
        elif _hdr_changed:
            st.info("머리글 행 수를 바꿨습니다. 파일을 다시 올리면 새 기준으로 읽습니다.")

    elif _input_mode == "📷 이미지/사진":
        st.caption("엑셀 화면 캡처·조사표 사진을 AI가 표 데이터로 바꿉니다. 분석 전 반드시 값을 확인하세요.")
        _img = st.file_uploader("표 이미지 업로드", type=["png", "jpg", "jpeg", "webp"], key="table_img_up")
        _cam = st.camera_input("또는 카메라로 촬영", key="table_cam")
        _src = _cam or _img
        if _src is not None:
            st.image(_src, caption="인식할 이미지", width="stretch")
            if st.button("✨ AI로 표 인식", width="stretch", key="img_parse_btn"):
                with st.spinner("표의 행·열과 숫자를 읽는 중..."):
                    _bytes = _src.getvalue()
                    _mime = getattr(_src, "type", None) or ("image/png" if str(getattr(_src, "name", "")).lower().endswith("png") else "image/jpeg")
                    _idf, _warn = image_to_dataframe(_bytes, _mime)
                if _idf is None:
                    st.error("표 인식에 실패했습니다.")
                    for _w in _warn[:3]: st.caption(str(_w)[:180])
                else:
                    st.session_state["image_table_preview"] = _idf
                    st.session_state["image_table_warn"] = _warn
        if st.session_state.get("image_table_preview") is not None:
            st.markdown("**✅ 인식 결과 확인/수정**")
            _edited_img = st.data_editor(st.session_state["image_table_preview"], num_rows="dynamic",
                                         width="stretch", key="image_table_editor", height=240)
            for _w in st.session_state.get("image_table_warn", [])[:3]:
                st.warning(f"확인 필요: {_w}")
            if st.button("📌 이 표를 분석 데이터로 사용", type="primary", width="stretch", key="use_image_table"):
                _key = "이미지_인식데이터"
                st.session_state.files[_key] = clean_columns(_edited_img.copy())
                st.session_state.cur_key = _key
                st.session_state.df = st.session_state.files[_key].copy()
                st.success("이미지에서 읽은 표를 분석 데이터로 적용했습니다.")
                st.rerun()
        if not st.session_state.get("api_key"):
            st.info("이미지 표 인식은 `🧠 AI 도우미 → AI 연결 설정`에서 API 키를 설정한 뒤 사용할 수 있습니다.")

    elif _input_mode == "📄 PDF":
        st.caption("보고서·성적서 PDF 안의 표를 불러옵니다. 한글·엑셀에서 PDF로 저장한 파일은 AI 없이 바로 읽고, "
                   "종이를 스캔한 PDF는 AI 이미지 인식으로 읽습니다.")
        _pdf = st.file_uploader("PDF 업로드", type=["pdf"], key="pdf_up")
        if _pdf is not None:
            _pbytes = _pdf.getvalue()
            _psig = (getattr(_pdf, "name", ""), len(_pbytes))
            if st.session_state.get("pdf_sig") != _psig:
                try:
                    with st.spinner("PDF에서 표를 찾는 중..."):
                        _ptabs, _pn, _ptext = pdf_extract_tables(_pbytes)
                    st.session_state["pdf_found"] = {"tables": _ptabs, "pages": _pn, "text_pages": _ptext,
                                                     "name": getattr(_pdf, "name", "PDF")}
                except Exception as _pe:
                    st.session_state["pdf_found"] = {"tables": [], "pages": 0, "text_pages": 0,
                                                     "name": getattr(_pdf, "name", "PDF"), "error": str(_pe)[:160]}
                st.session_state["pdf_sig"] = _psig
            _pf = st.session_state.get("pdf_found") or {}
            if _pf.get("error"):
                st.error("PDF를 읽지 못했습니다. 암호가 걸려 있거나 손상된 파일일 수 있어요.")
                st.caption(_pf["error"])
            elif _pf.get("tables"):
                _labels = [f"{t['page']}쪽 표{t['idx']} ({t['df'].shape[0]}행×{t['df'].shape[1]}열)"
                           for t in _pf["tables"]]
                _pick = st.selectbox(f"찾은 표 {len(_labels)}개 중 선택", range(len(_labels)),
                                     format_func=lambda i: _labels[i], key="pdf_pick")
                st.caption("칸을 눌러 바로 고칠 수 있어요. 변수명(첫 행)이 맞는지 꼭 확인하세요.")
                _pedit = st.data_editor(_pf["tables"][_pick]["df"], num_rows="dynamic", width="stretch",
                                        key=f"pdf_editor_{_pick}", height=240)
                if st.button("📌 이 표를 분석 데이터로 사용", type="primary", width="stretch", key="use_pdf_table"):
                    _key = f"{_pf['name']} – {_pf['tables'][_pick]['page']}쪽 표{_pf['tables'][_pick]['idx']}"
                    st.session_state.files[_key] = clean_columns(_pedit.copy())
                    st.session_state.cur_key = _key
                    st.session_state.df = st.session_state.files[_key].copy()
                    st.success("PDF에서 읽은 표를 분석 데이터로 적용했습니다.")
                    st.rerun()
            else:
                if _pf.get("text_pages"):
                    st.warning("글자는 있지만 표 모양을 찾지 못했습니다. 표가 그림으로 들어가 있으면 아래 AI 인식을 이용하세요.")
                else:
                    st.info("글자를 읽을 수 없는 **스캔 PDF**로 보입니다. 아래에서 쪽을 골라 AI로 표를 인식하세요.")
                if _pf.get("pages"):
                    _pg = st.number_input("인식할 쪽", 1, int(_pf["pages"]), 1, key="pdf_scan_page")
                    if st.button("✨ 이 쪽을 AI로 표 인식", width="stretch", key="pdf_scan_btn"):
                        with st.spinner("쪽을 그림으로 바꾸고 표를 읽는 중..."):
                            try:
                                _idf, _warn = image_to_dataframe(pdf_page_png(_pbytes, int(_pg)), "image/png")
                            except Exception as _se:
                                _idf, _warn = None, [str(_se)]
                        if _idf is None:
                            st.error("표 인식에 실패했습니다.")
                            for _w in _warn[:3]: st.caption(str(_w)[:180])
                        else:
                            st.session_state["pdf_scan_preview"] = _idf
                            st.session_state["pdf_scan_warn"] = _warn
                    if st.session_state.get("pdf_scan_preview") is not None:
                        st.markdown("**✅ 인식 결과 확인/수정**")
                        _sedit = st.data_editor(st.session_state["pdf_scan_preview"], num_rows="dynamic",
                                                width="stretch", key="pdf_scan_editor", height=240)
                        for _w in st.session_state.get("pdf_scan_warn", [])[:3]:
                            st.warning(f"확인 필요: {_w}")
                        if st.button("📌 이 표를 분석 데이터로 사용", type="primary", width="stretch",
                                     key="use_pdf_scan"):
                            _key = f"{_pf.get('name', 'PDF')} – {int(_pg)}쪽 (AI 인식)"
                            st.session_state.files[_key] = clean_columns(_sedit.copy())
                            st.session_state.cur_key = _key
                            st.session_state.df = st.session_state.files[_key].copy()
                            st.session_state.pop("pdf_scan_preview", None)
                            st.success("PDF에서 읽은 표를 분석 데이터로 적용했습니다.")
                            st.rerun()
                    if not st.session_state.get("api_key"):
                        st.caption("AI 인식은 `🧠 AI 도우미 → AI 연결 설정`에서 API 키를 넣은 뒤 사용할 수 있습니다.")

    else:  # 음성
        st.caption("예: '처리구 A, 반복 1, 초장 72.3, 수량 615.4'처럼 한 행씩 말해 주세요.")
        _aud = st.audio_input("🎙️ 한 행 말하기", sample_rate=16000, key="voice_data_audio")
        if _aud is not None:
            st.audio(_aud)
            if st.button("📝 음성을 데이터 한 행으로 변환", width="stretch", key="voice_parse_btn"):
                with st.spinner("음성을 듣고 숫자와 변수명을 정리하는 중..."):
                    _tr = ai_multimodal_text(_aud.getvalue(), getattr(_aud, "type", None) or "audio/wav",
                                             "한국어 음성을 정확히 전사하세요.", kind="audio")
                if str(_tr).startswith("⚠️"):
                    st.error(_tr)
                else:
                    st.session_state["voice_transcript"] = _tr
                    _cols = list(st.session_state.df.columns) if isinstance(st.session_state.get("df"), pd.DataFrame) else []
                    _row, _warn = voice_text_to_row(_tr, _cols)
                    if _row is not None:
                        st.session_state.setdefault("voice_rows", [])
                        st.session_state["voice_rows"].append(_row)
                        st.session_state["voice_warn"] = _warn
        if st.session_state.get("voice_transcript"):
            st.caption("인식 문장: " + str(st.session_state["voice_transcript"]))
        if st.session_state.get("voice_rows"):
            _vdf = pd.DataFrame(st.session_state["voice_rows"])
            _ved = st.data_editor(_vdf, num_rows="dynamic", width="stretch", key="voice_rows_editor", height=220)
            for _w in st.session_state.get("voice_warn", [])[:3]: st.warning(f"확인 필요: {_w}")
            cva, cvb = st.columns(2)
            if cva.button("➕ 현재 데이터에 추가", width="stretch", key="voice_append"):
                if isinstance(st.session_state.get("df"), pd.DataFrame) and len(st.session_state.df.columns):
                    base = st.session_state.df.copy()
                    add = _ved.reindex(columns=base.columns)
                    st.session_state.df = pd.concat([base, add], ignore_index=True)
                    ck = st.session_state.get("cur_key") or "음성_추가데이터"
                    st.session_state.files[ck] = st.session_state.df.copy()
                    st.success(f"{len(add)}행을 현재 데이터에 추가했습니다.")
                else:
                    st.warning("먼저 기존 데이터를 불러오거나 '새 데이터로 사용'을 눌러 주세요.")
            if cvb.button("📌 새 데이터로 사용", width="stretch", key="voice_new"):
                key = "음성_입력데이터"
                st.session_state.files[key] = clean_columns(_ved.copy())
                st.session_state.cur_key = key
                st.session_state.df = st.session_state.files[key].copy()
                st.success("음성 입력 데이터를 새 분석 데이터로 적용했습니다.")
                st.rerun()
            if st.button("🗑️ 음성 입력 목록 비우기", width="stretch", key="voice_clear"):
                st.session_state["voice_rows"] = []
                st.session_state.pop("voice_transcript", None)
                st.rerun()
        if not st.session_state.get("api_key"):
            st.info("음성 인식은 `🧠 AI 도우미 → AI 연결 설정`에서 ChatGPT 또는 Gemini API 키를 설정한 뒤 사용할 수 있습니다.")

# 데이터 선택 + 삭제
if st.session_state.files:
    names = list(st.session_state.files.keys())
    opts = names + (["🔗 모두 세로로 합치기"] if len(names) > 1 else [])
    _cur_for_select = st.session_state.get("cur_key")
    _sel_idx = opts.index(_cur_for_select) if _cur_for_select in opts else 0
    choice = st.sidebar.selectbox("📌 분석할 데이터 선택", opts, index=_sel_idx)
    # 선택이 바뀔 때만 새로 불러옴 (전처리 결과가 유지되도록)
    if choice != st.session_state.get("cur_key"):
        st.session_state.cur_key = choice
        if choice == "🔗 모두 세로로 합치기":
            try:
                st.session_state.df = pd.concat(list(st.session_state.files.values()), ignore_index=True)
            except Exception as e:
                st.sidebar.error(f"합치기 실패: {e}")
        else:
            st.session_state.df = st.session_state.files[choice].copy()

    if st.sidebar.button("↩️ 원본 데이터로 되돌리기", width="stretch",
                         help="현재 선택한 데이터를 처음 불러온 상태로 다시 불러옵니다."):
        k = st.session_state.get("cur_key")
        if k in st.session_state.files:
            st.session_state.df = st.session_state.files[k].copy()
            st.sidebar.success("원본으로 되돌렸습니다.")
            st.rerun()

    _ready = _v1_checkup_counts(_v1_checkup_for(st.session_state.get("df")))
    if _ready["error"]:
        st.sidebar.error(f"❌ 고쳐야 할 문제 {_ready['error']}건")
    elif _ready["warn"]:
        st.sidebar.warning(f"⚠️ 데이터 점검 {_ready['warn']}건")
    else:
        st.sidebar.success("✅ 분석 준비 완료")
    st.sidebar.caption("자세한 내용: 통계분석 → 📋 데이터 점검")

    with st.sidebar.expander("🗑️ 데이터 삭제"):
        dels = st.multiselect("삭제할 데이터 선택", names, key="del_sel")
        if dels and st.button("선택한 데이터 삭제", width="stretch"):
            for d_ in dels: st.session_state.files.pop(d_, None)
            st.session_state.df = None
            st.rerun()

# 서버에 한글 폰트가 없으면 그래프 글자가 전부 □로 나온다 — 미리 알려 준다.
if _KOREAN_FONT is None:
    st.sidebar.warning("⚠️ 한글 폰트를 찾지 못해 그래프 글자가 □로 나옵니다. "
                       "서버라면 `packages.txt`에 `fonts-nanum`을 넣고 다시 배포하세요.")

# 메뉴를 옮겨 다니거나 시트를 바꿔도 화면 선택·분석 결과가 그대로 남게 한다.
_pin_sync()
if st.session_state.files and st.sidebar.button(
        "🔄 이 데이터의 화면 선택 초기화", width="stretch",
        help="열 선택이 꼬였을 때, 지금 선택한 데이터의 화면 선택만 처음 상태로 되돌립니다."):
    for _k in _pin_scoped_keys():
        try:
            del st.session_state[_k]
        except Exception:
            pass
    st.session_state.get("_pin_store", {}).pop(st.session_state.get("cur_key"), None)
    st.rerun()

# 메뉴 — V1은 분석 시작 3개만 강조, 보고서·AI·설명서는 보조 기능으로 작게 표시
_MAIN_MENU_OPTIONS = ["⚡ 원클릭 분석", "📊 통계분석", "📋 설문조사 분석"]
_SUPPORT_MENU_OPTIONS = ["📑 보고서", "🧠 AI 도우미", "📖 사용설명서"]
if _is_admin_user():
    _SUPPORT_MENU_OPTIONS.append("👑 관리자")
_all_menu_options = _MAIN_MENU_OPTIONS + _SUPPORT_MENU_OPTIONS
if st.session_state.get("menu_choice") not in _all_menu_options:
    st.session_state["menu_choice"] = _MAIN_MENU_OPTIONS[0]

def _menu_from_main():
    value = st.session_state.get("menu_main")
    if value:
        st.session_state["menu_choice"] = value

def _menu_from_support():
    value = st.session_state.get("menu_support")
    if value:
        st.session_state["menu_choice"] = value

st.sidebar.markdown("""
<style>
/* 클릭되지 않는 섹션 제목은 평문. 실제 radio option만 선택/hover 표현 */
[data-testid="stSidebar"] .v1-section-label {
    margin:.72rem 0 .18rem .18rem; color:#66786c; font-size:.76rem;
    font-weight:700; letter-spacing:.02em; background:transparent; border:0; box-shadow:none;
}
[data-testid="stSidebar"] .st-key-main_menu_block [data-testid="stRadio"] > label,
[data-testid="stSidebar"] .st-key-support_menu_block [data-testid="stRadio"] > label {display:none!important;}
[data-testid="stSidebar"] .st-key-main_menu_block [role="radiogroup"] {gap:.16rem;}
[data-testid="stSidebar"] .st-key-main_menu_block [role="radiogroup"] label {
    width:100%; padding:.48rem .58rem; border:0!important; border-radius:8px;
    background:transparent!important; box-shadow:none!important; font-size:.98rem; font-weight:720;
}
[data-testid="stSidebar"] .st-key-main_menu_block [role="radiogroup"] label:hover {background:#EEF6F0!important;}
[data-testid="stSidebar"] .st-key-main_menu_block [role="radiogroup"] label:has(input:checked) {
    background:#E4F1E7!important; box-shadow:inset 3px 0 0 #4F8060!important; color:#244A33!important;
}
[data-testid="stSidebar"] .st-key-support_menu_block [role="radiogroup"] {gap:.04rem;}
[data-testid="stSidebar"] .st-key-support_menu_block [role="radiogroup"] label {
    width:100%; padding:.28rem .58rem; border:0!important; border-radius:7px;
    background:transparent!important; box-shadow:none!important; color:#65756C!important;
    font-size:.82rem; font-weight:540;
}
[data-testid="stSidebar"] .st-key-support_menu_block [role="radiogroup"] label:hover {background:#F2F7F3!important;}
[data-testid="stSidebar"] .st-key-support_menu_block [role="radiogroup"] label:has(input:checked) {
    background:#EDF4EF!important; color:#334A3A!important; font-weight:680;
}
[data-testid="stSidebar"] .st-key-main_menu_block [role="radiogroup"] label > div:first-child,
[data-testid="stSidebar"] .st-key-support_menu_block [role="radiogroup"] label > div:first-child {display:none!important;}
</style>
""", unsafe_allow_html=True)

# ================================================================ V1 최종 시안 색감/캐릭터 테마
# 첨부 시안에서 빨간 네모로 표시한 4개 디자인 요소를 반영합니다.
# ① 좌측 상단 브랜드 ② 메인 상단 배너 ③ 좌측 하단 캐릭터 ④ 우측 하단 AI 버튼
# 통계 계산·그래프·Excel/HWPX/Word·분석 메뉴 기능 로직은 변경하지 않습니다.
_V1_MASCOT_TOP = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAG4AAABeCAYAAADCISFWAAAgAElEQVR4AYzBefjnB0Ef+Nf78/3NneM3ObmCA+G+HEVdtChpVTyKJd4Wu6VKW6RVqdvd5Y/t4/Fsn922u49ufGjts61ukUVtUQldDzw7EbyqQOQQAiZMyJ1MMr85Mr/z+3nv95jfTCYB6+uVu87saOuCIkE9RZEiEloUCeqCxEKrlmKpiLhULQW1EFLqvLpELbUWGtJaCEko4vMKGkutuSSUOC8oNRMLKYJGFRUhZkJLzMRcW4oQ1JMV0SJF1HmttDa3ttz1mXu86523esUrXix3ndnWooiFiKoLihBVc/H5tBUzCTETWnNBUSSRFkEtRdVcUJdqSy3FTFAtVRG7Eook2oqnSqIqQkpJQs1URVBzJaG1FBdVEgt1QVUSrUsk0VZL4oK2FhJVMVNOnzrjve/5TXcf/6zJJLa3d+SuM9vUTMxVBUVQcxXxRPVEQS20FhILCa25JKqWImZaEh0riaq5oAiKtiS0FlrJoK0qQlDETBELIaWIWEjFRUm0CEFL0CIuiKq5ELQihDqvxFLNBK2IWmqLSFzQltAiRHS6450/+16mO771W17rissP2djclrtObxPUpVpiJuaCulRdKv4KglLETNCg5iIatLSIKomFVs205iqozydmglpKXBBiKS6qpZippbgooYiFlDovpRYq4rygFmqmVMVFDWopMeCjH7nDz73zF73tf3yza687rCMjctfpbbsa1EIsBY2LWhIRdVFbSWgR1FxioYJaipaYCWqmJLSIhLbm6rzWXMSolKqEFikNrSpiSMR5CYIqElqGRFXQhBIltERcVMmgLUERtIi5hNYFiZkoWqLm2pLQIiiJucTCL777191z/F7/wz/5HitDTMtU5PipLVMloUVIqJkSklioSwQVVEMsRWhJUEvRlkRLYqaUJNpKYq6KoFoLQVtLQdVcFWMrrI7dObK+fW51c+ecweDgnoP2rexfGyYrx9usVcwlFuJSSWglUeeVhLYiGhfEUhFBLZRRBUm0iIWWWGqpWgohloL/+B9/1X133+eHfuhNEoqWbG5PbZetaW1ORxs7o50yZJDBRY25hNoVQsyVxELrghC0cVG1SMxFLUURVTOl5orQmisSC1Vji3F17dxjN/3BR297/afu/eiRrenjxu06uO9yz3nG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'
_V1_MASCOT_SIDE = 'data:image/png;base64,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'
_V1_MASCOT_BADGE = 'data:image/png;base64,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'

_V1_HERO_SCENE = 'data:image/png;base64,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'
_V1_HERO_STRIP = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAACaCAIAAAAbw56UAAAA8klEQVR42t1XQQ7DMAiDLOdd9v9n7b4H7DC16qSuTdgHcCRHtJGaq0UTbDBUn0sR7+RSzAeSqgskAQcCWZSNUPaOqwBZxNgII2mHEYHSwjyygpBsbDF0ZK4owjrykKA8eti1wxunQbvG6UG/ypAeSTSOXTucK7U4zXWc+wRa+BmmD7niPRE7Q2C10x11ilCRVQIE4XuQ1zx0CKOpRs+PoV0bucPxkxMWw6/OPjBtLx9Y9rcPVNvpVgvcyDRomWhdju5QI59rMELi/g0GfqpFe/WBtXx9YN4+CJh8YLP1cFviy2ekLTW2cNQ4pYL/2vvt4QJ/FIBODn7azPkAAAAASUVORK5CYII='

_V1_REFERENCE_THEME_CSS = """
<style>
/* ── 시안 배경: 하늘 → 민트 그라데이션 + 구름 + 언덕 3겹 ── */
.stApp {
    background-color:#F2F8F1 !important;
    background-image:
        /* 구름 */
        radial-gradient(ellipse 96px 24px at 17% 62%, rgba(255,255,255,.92) 0 99%, rgba(255,255,255,0) 100%),
        radial-gradient(ellipse 62px 18px at 24% 59%, rgba(255,255,255,.88) 0 99%, rgba(255,255,255,0) 100%),
        radial-gradient(ellipse 84px 22px at 74% 55%, rgba(255,255,255,.90) 0 99%, rgba(255,255,255,0) 100%),
        radial-gradient(ellipse 56px 16px at 80% 52%, rgba(255,255,255,.85) 0 99%, rgba(255,255,255,0) 100%),
        /* 언덕 3겹 */
        radial-gradient(ellipse 62% 210px at 86% 106%, #CDE9B4 0 99%, rgba(205,233,180,0) 100%),
        radial-gradient(ellipse 58% 190px at 50% 108%, #DDF1C9 0 99%, rgba(221,241,201,0) 100%),
        radial-gradient(ellipse 68% 225px at 10% 111%, #E8F6DA 0 99%, rgba(232,246,218,0) 100%),
        /* 하늘 → 민트 */
        linear-gradient(180deg,#E4F4FB 0%,#EEF9FC 16%,#F6FBF8 52%,#F1F8F0 100%) !important;
    background-repeat:no-repeat !important;
    background-attachment:fixed !important;
}
[data-testid="stAppViewContainer"] > .main {background:transparent !important;}
[data-testid="stHeader"] {background:transparent !important;}
[data-testid="stSidebar"] {
    background:linear-gradient(180deg,#EFF7F0 0%,#F5FDF7 55%,#FBFEFB 100%) !important;
    border-right:1px solid #DCECDF !important;
}

/* 좌측 상단: 시안의 캐릭터 + 한 줄 브랜드명 */
[data-testid="stSidebar"] .v1-sidebar-brand {
    position:relative; min-height:82px; padding:.42rem .10rem .30rem 4.35rem;
    margin:.02rem 0 .28rem 0; display:flex; flex-direction:column; justify-content:center;
}
[data-testid="stSidebar"] .v1-sidebar-brand::before {
    content:""; position:absolute; left:.05rem; top:.10rem; width:72px; height:76px;
    background-image:url('__BADGE_MASCOT__'); background-repeat:no-repeat;
    background-position:center; background-size:contain; pointer-events:none;
}
[data-testid="stSidebar"] .v1-sidebar-brand-title {
    color:#17344B; font-size:1.22rem; line-height:1.2; font-weight:850; letter-spacing:-.050em;
    white-space:nowrap;
}
[data-testid="stSidebar"] .v1-sidebar-brand-title span {color:#25A953;}
@media (max-width: 1180px) {
    [data-testid="stSidebar"] .v1-sidebar-brand-title {font-size:1.12rem;}
}
[data-testid="stSidebar"] .v1-sidebar-brand-sub {
    margin-top:.30rem; color:#5F6F66; font-size:.84rem; line-height:1.3; font-weight:600;
}
[data-testid="stSidebar"] .v1-sidebar-brand-sub .v1-ver {
    display:inline-block; color:#FFFFFF; background:#25A953; border-radius:999px;
    font-size:.72rem; font-weight:800; padding:.05rem .45rem; margin-right:.25rem; vertical-align:1px;
}
[data-testid="stSidebar"] .v1-sidebar-brand-sub .v1-sub-txt {display:block; margin-top:.18rem; white-space:nowrap;}
@media (max-width: 1180px) {
    [data-testid="stSidebar"] .v1-sidebar-brand-sub .v1-sub-txt {font-size:.78rem;}
}

/* 제목/본문 포인트 색 */
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
.main h1, .main h2, .main h3 {color:#17344B !important;}
.main a, [data-testid="stSidebar"] a {color:#259B4A !important;}
input[type="radio"], input[type="checkbox"] {accent-color:#2DBD60 !important;}

/* 버튼/입력창/카드 색감만 시안 계열로 */
[data-testid="stBaseButton-primary"] {
    background:#2FBE62 !important; border-color:#2FBE62 !important; color:#FFFFFF !important;
    box-shadow:0 3px 10px rgba(46,190,99,.18) !important;
}
[data-testid="stBaseButton-primary"]:hover {background:#27AD58 !important; border-color:#27AD58 !important;}
[data-testid="stBaseButton-secondary"], div.stDownloadButton > button {
    background:#FFFFFF !important; border-color:#C8E8D2 !important; color:#28593A !important;
}
[data-testid="stBaseButton-secondary"]:hover, div.stDownloadButton > button:hover {
    background:#F1FAF4 !important; border-color:#73CE8D !important; color:#1F7C3F !important;
}
[data-testid="stFileUploaderDropzone"] {background:#F7FCF8 !important; border-color:#BFE5CA !important;}
[data-testid="stExpander"] {border-color:#D7EBDD !important; background:rgba(255,255,255,.86) !important;}
button[data-baseweb="tab"][aria-selected="true"] {color:#219B4B !important;}
[data-baseweb="tab-highlight"] {background-color:#31BE63 !important;}
[data-baseweb="input"] > div:focus-within,
[data-baseweb="select"] > div:focus-within,
[data-baseweb="textarea"]:focus-within {
    border-color:#75CF90 !important; box-shadow:0 0 0 1px #75CF90 !important;
}

/* 기존 사이드바 메뉴 구조는 유지하고 선택 색만 시안처럼 */
[data-testid="stSidebar"] .v1-section-label {color:#6B7E72 !important;}
[data-testid="stSidebar"] .st-key-main_menu_block [role="radiogroup"] label:hover {background:#EDF9F1 !important;}
[data-testid="stSidebar"] .st-key-main_menu_block [role="radiogroup"] label:has(input:checked) {
    background:linear-gradient(90deg,#35BE62 0%,#48C96F 100%) !important;
    box-shadow:0 5px 12px rgba(46,174,86,.16) !important; color:#FFFFFF !important;
}
[data-testid="stSidebar"] .st-key-main_menu_block [role="radiogroup"] label:has(input:checked) p {color:#FFFFFF !important;}
[data-testid="stSidebar"] .st-key-support_menu_block [role="radiogroup"] label {color:#64766B !important;}
[data-testid="stSidebar"] .st-key-support_menu_block [role="radiogroup"] label:hover {background:#F1F9F3 !important;}
[data-testid="stSidebar"] .st-key-support_menu_block [role="radiogroup"] label:has(input:checked) {
    background:#EAF7EE !important; color:#2A6540 !important;
}

/* 메인 상단: 빨간 네모로 표시한 배너. 실제 콘텐츠는 아래에 그대로 이어짐. */
/* Streamlit 기본 상단 여백을 줄여 사이드바 브랜드 영역과 배너 시작 높이를 맞춘다. */
[data-testid="stMainBlockContainer"], .main .block-container {
    padding-top:3.15rem !important;
}
.v1-hero {
    position:relative; min-height:154px; overflow:hidden; margin:1.65rem 0 1.00rem 0;
    border:1px solid #DDEEE4; border-radius:15px;
    background-color:#EDF8EC;
    background-image:
      radial-gradient(circle at 69% 31%, #FFD85B 0 6px, transparent 7px),
      url('__HERO_STRIP__');
    background-repeat:no-repeat, repeat-x;
    background-position:center, left bottom;
    background-size:auto, auto 100%;
    box-shadow:0 5px 18px rgba(76,137,96,.08);
}
.v1-hero::before, .v1-hero::after {
    content:""; position:absolute; background:#FFFFFF; opacity:.93; border-radius:999px;
}
.v1-hero::before {width:70px; height:18px; left:31%; top:23px; box-shadow:22px 3px 0 -4px #fff, -19px 5px 0 -6px #fff;}
.v1-hero::after {width:54px; height:14px; right:31%; top:17px; box-shadow:18px 4px 0 -5px #fff;}
.v1-hero-copy {position:relative; z-index:3; padding:38px 320px 24px 30px;}
.v1-hero-title {color:#17344B; font-weight:900; font-size:1.72rem; letter-spacing:-.045em; line-height:1.12;}
.v1-hero-title span {color:#28A955;}
.v1-hero-sub {margin-top:.48rem; color:#567166; font-size:.87rem; font-weight:650; letter-spacing:-.02em;}
.v1-hero-mascot {
    position:absolute; z-index:4; right:0; left:0; top:0; bottom:0;
    background-image:url('__HERO_SCENE__'); background-repeat:no-repeat;
    background-position:right 42px bottom; background-size:auto 90%; pointer-events:none;
}

/* 좌측 하단 빨간 네모: 설정 바로 위에 실제 공간을 확보해 캐릭터가 절대 잘리지 않게 함 */
[data-testid="stSidebar"] .v1-side-mascot {
    width:100%; height:158px; margin:.50rem 0 .16rem 0;
    background-image:url('__SIDE_MASCOT__'); background-repeat:no-repeat;
    background-position:center bottom; background-size:130px auto; pointer-events:none;
}

/* 우측 하단 빨간 네모: 기존 AI 기능은 그대로 두고 캐릭터가 포함된 초록 말풍선 모양만 적용 */
div.st-key-gai_dock {right:1.15rem !important; bottom:1.05rem !important;}
div.st-key-gai_dock button {
    position:relative !important; min-height:52px !important; border-radius:999px !important;
    padding:.70rem 1.28rem .70rem 3.55rem !important; background:#31BE63 !important;
    border:1px solid #31BE63 !important; color:#FFFFFF !important;
    box-shadow:0 8px 22px rgba(42,161,81,.28) !important;
}
div.st-key-gai_dock button::before {
    content:""; position:absolute; left:5px; top:5px; width:41px; height:41px; border-radius:50%;
    background-color:#FFFFFF; background-image:url('__BADGE_MASCOT__'); background-repeat:no-repeat;
    background-position:center 54%; background-size:34px auto; box-shadow:0 1px 4px rgba(0,0,0,.08);
}
div.st-key-gai_dock button::after {
    content:"♥"; position:absolute; right:-4px; top:-12px; color:#FF9CB3; font-size:1.25rem;
    transform:rotate(11deg); text-shadow:0 1px 2px rgba(255,255,255,.9);
}
div.st-key-gai_dock button:hover {background:#27AC58 !important; border-color:#27AC58 !important;}

@media (max-width: 900px) {
    [data-testid="stMainBlockContainer"], .main .block-container {padding-top:3.05rem !important;}
    .v1-hero {min-height:132px;}
    .v1-hero-copy {padding:26px 255px 18px 20px;}
    .v1-hero-title {font-size:1.36rem;}
    .v1-hero-sub {font-size:.78rem;}
    .v1-hero-mascot {background-size:auto 92%;}
}
@media (max-width: 640px) {
    [data-testid="stMainBlockContainer"], .main .block-container {padding-top:2.95rem !important;}
    .v1-hero {min-height:118px;}
    .v1-hero-copy {padding-right:165px;}
    .v1-hero-mascot {background-size:auto 86%;}
    .v1-hero-title {font-size:1.18rem;}
    .v1-hero-sub {font-size:.72rem; max-width:72%;}
    [data-testid="stSidebar"] .v1-side-mascot {height:140px; background-size:112px auto;}
}
</style>
""".replace("__TOP_MASCOT__", _V1_MASCOT_TOP).replace("__SIDE_MASCOT__", _V1_MASCOT_SIDE).replace("__BADGE_MASCOT__", _V1_MASCOT_BADGE).replace("__HERO_SCENE__", _V1_HERO_SCENE).replace("__HERO_STRIP__", _V1_HERO_STRIP)
st.markdown(_V1_REFERENCE_THEME_CSS, unsafe_allow_html=True)

st.sidebar.markdown('<div class="v1-section-label">분석 시작</div>', unsafe_allow_html=True)
_current_menu = st.session_state.get("menu_choice")
with st.sidebar.container(key="main_menu_block"):
    _main_idx = (_MAIN_MENU_OPTIONS.index(_current_menu) if _current_menu in _MAIN_MENU_OPTIONS else None)
    st.radio("주요 기능", _MAIN_MENU_OPTIONS, index=_main_idx, key="menu_main",
             label_visibility="collapsed", on_change=_menu_from_main)

st.sidebar.markdown('<div class="v1-section-label">보조 기능</div>', unsafe_allow_html=True)
_current_menu = st.session_state.get("menu_choice")
with st.sidebar.container(key="support_menu_block"):
    _support_idx = (_SUPPORT_MENU_OPTIONS.index(_current_menu) if _current_menu in _SUPPORT_MENU_OPTIONS else None)
    st.radio("보조 기능", _SUPPORT_MENU_OPTIONS, index=_support_idx, key="menu_support",
             label_visibility="collapsed", on_change=_menu_from_support)

menu = st.session_state.get("menu_choice", _MAIN_MENU_OPTIONS[0])

st.sidebar.markdown('<div class="v1-side-mascot" aria-hidden="true"></div>', unsafe_allow_html=True)

with st.sidebar.expander("⚙️ 출력 및 그래프 설정", expanded=False):
    _set_doc, _set_graph = st.tabs(["문서", "그래프"])
    with _set_doc:
        _HWP_FONTS = ["휴먼명조", "함초롬바탕", "함초롬돋움", "바탕", "신명조",
                      "맑은 고딕", "나눔명조", "나눔고딕", "Noto Sans KR", "돋움", "굴림", "직접 입력…"]
        st.selectbox("표·보고서 글씨체", _HWP_FONTS, key="hwp_font",
                     help="한글(hwpx)로 내려받는 표와 보고서 본문에 적용됩니다.")
        if st.session_state.get("hwp_font") == "직접 입력…":
            st.text_input("사용할 글꼴 이름", key="hwp_font_custom",
                          placeholder="예) KoPub바탕체 Medium",
                          help="한글의 글꼴 목록에 표시되는 이름을 그대로 입력하세요.")
        st.caption(f"현재 적용 글꼴: **{_selected_hwp_font()}**")
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox("글자 크기(pt)", [8, 9, 10, 11, 12], index=2, key="hwp_size")
            st.color_picker("머리행 음영", "#D9D9D9", key="hwp_shade")
        with c2:
            st.selectbox("선 굵기", ["0.1 mm", "0.12 mm", "0.15 mm", "0.2 mm", "0.4 mm"], key="hwp_lw")
            st.color_picker("표 선 색", "#000000", key="hwp_line")
        st.checkbox("좌우 바깥 세로선 표시", value=False, key="hwp_sides",
                    help="끄면 논문에서 흔히 쓰는 형태(양쪽 세로선 없음)가 됩니다.")
        st.slider("행 높이(mm)", 4.0, 15.0, 6.5, 0.5, key="hwp_rowh",
                  help="값을 줄이면 표의 위아래 간격이 촘촘해집니다.")
        c3, c4 = st.columns(2)
        c3.slider("위첨자 크기(%)", 40, 90, 65, 5, key="sup_size")
        c4.slider("위첨자 올림(%)", 0, 70, 35, 5, key="sup_off",
                  help="값이 클수록 유의성 문자(a,b,c)가 더 위로 올라갑니다.")
        st.slider("줄글 표 자간(%)", -30, 0, -14, 1, key="hwp_tight",
                  help="부분예산표처럼 글이 긴 표에서 글자를 좁혀 한 줄에 담습니다. "
                       "0으로 두면 좁히지 않습니다.")
        st.color_picker("AI 해석 글자색", "#0000FF", key="hwp_aicolor",
                        help="AI가 만든 문장을 사람이 쓴 문장과 구분하기 위한 색입니다. "
                             "검정으로 바꾸면 구분 없이 나옵니다.")
        st.caption("한글에 설치된 글꼴이어야 정확히 표시됩니다.")
    with _set_graph:
        st.radio("오차막대 기준", ["표준편차(SD)", "표준오차(SE)"], key="err_type",
                 help="SD는 '개체들이 얼마나 흩어져 있나', SE는 '평균값이 얼마나 믿을 만한가'를 봅니다.")
        with st.expander("❓ 표준편차(SD)와 표준오차(SE), 뭐가 다른가요?"):
            st.markdown(EXPLAIN["sd_se"])
        st.selectbox("소수점 자릿수", [1, 2, 3, 4], index=2, key="round_n")
        st.selectbox("그래프 색상", ["파랑", "초록", "주황", "보라", "회색"], key="plot_color")
        c1, c2 = st.columns(2)
        c1.number_input("그래프 가로", 3.0, 16.0, 6.0, 0.5, key="fig_w")
        c2.number_input("그래프 세로", 2.0, 12.0, 4.0, 0.5, key="fig_h")
        st.checkbox("✨ 깔끔한 스타일 (그라데이션·값 표시)", value=True, key="fig_style",
                    help="막대에 옅은→진한 색을 입히고 값을 표시하며, 전체 그래프의 축·간격을 통일합니다.")
        st.checkbox("⬛ 막대·원형 조각 검은 테두리", value=True, key="fig_border",
                    help="그래프 전체 외곽선이 아니라 막대와 원형/도넛 조각의 경계선에만 검은색을 적용합니다.")
        st.checkbox("막대 위에 값 표시", value=True, key="fig_vlabel")
        st.checkbox("격자선 표시", value=False, key="fig_grid",
                    help="'깔끔한 스타일'을 켜면 가로 격자선은 자동으로 들어갑니다.")
        st.checkbox("그래프 제목 표시", value=True, key="fig_title")

# V2 전문형 안내: 캡션(작은 회색 글씨) 대신 읽기 쉬운 안내 카드로 보여 준다.
st.sidebar.divider()
st.sidebar.markdown("""
<div class="v1-v2-card">
  <div class="v1-v2-title">🔬 Version 2 전문형</div>
  <div class="v1-v2-desc">경제성 분석, PCA 등 고급 통계가 필요하면 전문형을 이용하세요.</div>
</div>
<style>
[data-testid="stSidebar"] .v1-v2-card {
    background:#F3FAF5; border:1px solid #CFE9D8; border-radius:12px;
    padding:.75rem .85rem; margin-bottom:.55rem;
}
[data-testid="stSidebar"] .v1-v2-title {
    color:#17344B; font-size:1rem; font-weight:800; margin-bottom:.3rem;
}
[data-testid="stSidebar"] .v1-v2-desc {
    color:#3F5247; font-size:.9rem; line-height:1.45;
}
[data-testid="stSidebar"] [data-testid^="stBaseLinkButton"] {
    background:#2FBE62 !important; border-color:#2FBE62 !important;
}
[data-testid="stSidebar"] [data-testid^="stBaseLinkButton"],
[data-testid="stSidebar"] [data-testid^="stBaseLinkButton"] * {
    color:#FFFFFF !important; font-weight:700 !important; font-size:.95rem !important;
}
</style>
""", unsafe_allow_html=True)
if V2_APP_URL:
    st.sidebar.link_button("↗ Version 2 전문형 열기", V2_APP_URL, width="stretch")
elif _is_admin_user():
    # 설정 안내는 관리자에게만 보인다(일반 사용자에게는 의미 없는 문구).
    st.sidebar.caption("관리자 안내: secrets에 `V2_APP_URL`을 넣으면 여기에 열기 버튼이 생깁니다.")

_PALETTE = {"파랑": "#6c8ebf", "초록": "#82b366", "주황": "#d79b00", "보라": "#9673a6", "회색": "#808080"}

# 옅은 색 → 진한 색 그라데이션. 값이 큰 막대일수록 진하게 칠해 한눈에 들어오게 한다.
_RAMP = {
    "파랑": ["#dce9f5", "#c2d9ee", "#a3c4e2", "#82acd3", "#6291c2", "#4576ab", "#2d5a8e", "#1f4569"],
    "초록": ["#e2eedd", "#cbe2c2", "#b0d2a3", "#93c083", "#76ad65", "#5c934c", "#457539", "#33582b"],
    "주황": ["#fdeadb", "#fbd7b9", "#f7bd8d", "#f2a061", "#e5833c", "#cd6a25", "#a95318", "#833f11"],
    "보라": ["#eae3f1", "#d9cce6", "#c3b0d7", "#ac93c7", "#9478b3", "#7a5e9a", "#5f487a", "#46345a"],
    "회색": ["#ececec", "#dadada", "#c2c2c2", "#a8a8a8", "#8d8d8d", "#727272", "#585858", "#3f3f3f"],
}


def pretty_on():
    return bool(st.session_state.get("fig_style", True))


def bar_colors(values=None, n=None):
    """막대 색을 옅은→진한 순으로 만든다.

    values 를 주면 **값이 큰 막대일수록 진하게** 칠한다(가장 좋은 처리가 눈에 띈다).
    '깔끔한 스타일'을 끄면 예전처럼 한 가지 색으로 돌아간다.
    """
    ramp = _RAMP.get(st.session_state.get("plot_color", "파랑"), _RAMP["파랑"])
    k = int(n if n is not None else (len(values) if values is not None else 1))
    if not pretty_on() or k <= 0:
        return [pcolor()] * max(k, 1)
    if k == 1:
        return [ramp[len(ramp) // 2 + 1]]
    lo, hi = 1, len(ramp) - 1                      # 너무 옅은 색은 빼서 인쇄해도 보이게
    picked = [ramp[round(lo + (hi - lo) * i / (k - 1))] for i in range(k)]
    if values is not None:
        try:
            import numpy as _np
            order = _np.argsort(_np.argsort(_np.asarray(values, dtype=float)))
            return [picked[int(r)] for r in order]   # 값이 클수록 진한 색
        except Exception:
            pass
    return picked


def bar_value_labels(ax, xs, values, errs=None, dec=None, offset=0.03):
    """막대 위에 값을 적는다(오차막대가 있으면 그 위로 올린다)."""
    if not (pretty_on() and st.session_state.get("fig_vlabel", True)):
        return 0.0
    import numpy as _np
    vals = _np.asarray(values, dtype=float)
    e = _np.zeros_like(vals) if errs is None else _np.nan_to_num(_np.asarray(errs, dtype=float))
    span = float(_np.nanmax(_np.abs(vals))) or 1.0
    d = rnd() if dec is None else dec
    finite = vals[_np.isfinite(vals)]
    if len(finite) and _np.allclose(finite, _np.round(finite)):
        d = 0                       # 도수(개수)처럼 정수뿐이면 '5.0' 대신 '5'
    elif span >= 100:
        d = min(d, 1)               # 큰 값은 소수점을 줄여야 글자가 겹치지 않는다
    for xi, v, ei in zip(xs, vals, e):
        if not _np.isfinite(v):
            continue
        ax.text(xi, v + ei + span * offset, f"{v:,.{d}f}", ha="center", va="bottom",
                fontsize=9, fontweight="bold", color="#33383d")
    return span * offset * 2.2                      # 글자가 차지한 높이(윗여백 확보용)



def bar_value_sig_labels(ax, xs, values, errs=None, sigs=None, dec=None, offset=0.03):
    """막대 위에 '평균값 + 유의성 문자'를 한 번에 표시한다.

    예: 105.7ᵃ
    값과 a/b/c를 별도의 ax.text로 두 번 찍으면 겹치기 쉬우므로 절대 분리하지 않는다.
    """
    if not (pretty_on() and st.session_state.get("fig_vlabel", True)):
        return 0.0
    import numpy as _np
    vals = _np.asarray(values, dtype=float)
    e = _np.zeros_like(vals) if errs is None else _np.nan_to_num(_np.asarray(errs, dtype=float))
    sigs = list(sigs or [""] * len(vals))
    span = float(_np.nanmax(_np.abs(vals))) or 1.0
    d = rnd() if dec is None else dec
    finite = vals[_np.isfinite(vals)]
    if len(finite) and _np.allclose(finite, _np.round(finite)):
        d = 0
    elif span >= 100:
        d = min(d, 1)
    ypad = span * offset
    for i, (xi, v, ei) in enumerate(zip(xs, vals, e)):
        if not _np.isfinite(v):
            continue
        sig = str(sigs[i] if i < len(sigs) else "").strip()
        # 배포 서버의 한글 폰트에는 Unicode 위첨자(ᵃ, ᵇ...)가 없는 경우가 있어 □로 깨진다.
        # Matplotlib mathtext의 영문 superscript를 사용하면 서버 폰트와 무관하게 안정적으로 보인다.
        _sig = "".join(ch for ch in sig if ch.isalpha() or ch == "*")
        label = f"{v:,.{d}f}" + (rf"$^{{{_sig}}}$" if _sig else "")
        ax.text(xi, v + ei + ypad, label,
                ha="center", va="bottom", fontsize=9,
                fontweight="bold", color="#33383d")
    return ypad * 2.6

def pcolor(): return _PALETTE.get(st.session_state.get("plot_color", "파랑"), "#6c8ebf")
def rnd(): return int(st.session_state.get("round_n", 3))
def figsize(w=None, h=None):
    return (w or float(st.session_state.get("fig_w", 6.0)),
            h or float(st.session_state.get("fig_h", 4.0)))
def deco(ax, title="", ylabel_top=True):
    """공통 그래프 마감: 전체 검은 프레임 없이 깔끔한 축/격자/제목만 적용."""
    ax.set_facecolor("white")
    ax.set_axisbelow(True)
    if pretty_on():
        ax.grid(axis="y", color="#DCE7F0", linewidth=.8, alpha=.95)
        ax.grid(axis="x", visible=False)
    elif st.session_state.get("fig_grid", False):
        ax.grid(alpha=.3, linestyle="--")

    # 전체 테두리는 사용하지 않는다. 논문형 좌·하단 축선만 옅게 유지한다.
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_visible(True)
        ax.spines[side].set_color("#AEBECD")
        ax.spines[side].set_linewidth(.8)

    ax.tick_params(colors="#4B5F73", length=3, labelsize=9, direction="out")
    ax.xaxis.label.set_color("#31485E")
    ax.yaxis.label.set_color("#31485E")
    _has_ylab = bool(ylabel_top and ax.get_ylabel())
    if pretty_on() and _has_ylab:
        ax.set_ylabel(ax.get_ylabel(), rotation=0, ha="left", va="bottom",
                      fontsize=9.5, color="#31485E")
        ax.yaxis.set_label_coords(-0.02, 1.025)
    if title and st.session_state.get("fig_title", True):
        ax.set_title(title, fontsize=11.5 if pretty_on() else None,
                     fontweight="bold" if pretty_on() else None,
                     color="#23394D" if pretty_on() else None,
                     pad=24 if (pretty_on() and _has_ylab) else 12)
    lg = ax.get_legend()
    if lg is not None:
        try:
            lg.get_frame().set_linewidth(0)
            lg.get_frame().set_facecolor("white")
        except Exception:
            pass
    return ax


# 위첨자 변환기는 sup_text/sup_display(파일 위쪽) 하나로 통일한다.
# (예전 _SUP 표는 a~h 까지만 있어서 처리구가 9개 이상이면 'i', 'j'가 '^i'로 그대로 보였다.)
sup_show = sup_text
sup_df = sup_display

def read_uploaded_text(f, limit=12000):
    """업로드 파일에서 텍스트 추출 (txt/csv/xlsx/hwpx/pdf/docx)"""
    name = f.name.lower()
    try:
        if name.endswith((".txt", ".md")):
            return f.getvalue().decode("utf-8", errors="ignore")[:limit]
        if name.endswith(".csv"):
            return pd.read_csv(f).to_string()[:limit]
        if name.endswith((".xlsx", ".xls")):
            return pd.read_excel(f).to_string()[:limit]
        if name.endswith(".hwpx"):
            import tempfile, os
            from hwpx import HwpxDocument
            t = tempfile.NamedTemporaryFile(delete=False, suffix=".hwpx"); t.write(f.getvalue()); t.close()
            d = HwpxDocument.open(t.name)
            txt = "\n".join(p.text for p in d.paragraphs if p.text)
            os.unlink(t.name)
            return txt[:limit]
        if name.endswith(".pdf"):
            try:
                from pypdf import PdfReader
            except Exception:
                return "⚠️ PDF를 읽으려면 pypdf가 필요합니다. (pip install pypdf)"
            r = PdfReader(io.BytesIO(f.getvalue()))
            return "\n".join((pg.extract_text() or "") for pg in r.pages)[:limit]
        if name.endswith(".docx"):
            try:
                import docx
            except Exception:
                return "⚠️ Word를 읽으려면 python-docx가 필요합니다. (pip install python-docx)"
            d = docx.Document(io.BytesIO(f.getvalue()))
            return "\n".join(p.text for p in d.paragraphs)[:limit]
        return "⚠️ 지원하지 않는 형식입니다. (txt, csv, xlsx, hwpx, pdf, docx)"
    except Exception as e:
        return f"⚠️ 파일을 읽는 중 오류: {e}"

# 리커트(동의/만족 정도)가 아니라 명목형 범주를 숫자 코드로 적은 열임을 강하게 시사하는 이름들.
# 값만 봐서는 "1,2,3"이 3점 리커트인지 '있다/없다/모르겠다' 같은 코드인지 구분할 수 없으므로
# 열 이름 힌트로 우선 걸러낸다 (economic_core의 반복/처리 열 판별과 같은 접근).
# '의향'은 넣지 않는다 — '재사용의향'·'추천의향'처럼 실제로는 거의 항상 리커트 문항이라,
# 이 힌트에 넣으면 리커트 문항이 명목 코드로 오분류된다(실제로 발생했던 문제).
_NOMINAL_CODE_HINTS = ["여부", "유무", "선택", "성별", "지역", "종류",
                       "품종", "구분", "방법", "코드", "처리구", "그룹"]


def _looks_like_nominal_code(colname):
    return any(k in str(colname) for k in _NOMINAL_CODE_HINTS)


def detect_question_types(df):
    """설문 문항의 유형을 자동으로 추정"""
    out = []
    n = len(df)
    for c in df.columns:
        ser = df[c].dropna()
        if ser.empty:
            out.append({"열 이름": c, "추정 유형": "빈 열", "근거": "-"}); continue
        nu = ser.nunique()
        if pd.api.types.is_numeric_dtype(ser):
            v = ser.astype(float)
            is_int = np.allclose(v, np.round(v))
            nominal_hint = _looks_like_nominal_code(c)
            if is_int and nu == 2:      # 이분형을 먼저 판정 (리커트로 오인 방지)
                out.append({"열 이름": c, "추정 유형": "이분형(예/아니오)",
                            "근거": f"값 2종({int(v.min())}, {int(v.max())})"})
            elif is_int and nominal_hint and nu <= 10:
                # 값 범위만 보면 리커트(3~10점)와 똑같아 보이지만, 열 이름이 '의향/여부/지역' 등
                # 명목 코드를 강하게 시사하므로 객관식(단일선택)으로 분류한다.
                out.append({"열 이름": c, "추정 유형": "객관식(단일선택)",
                            "근거": f"열 이름상 명목 코드로 추정, 보기 {nu}개"})
            elif is_int and 3 <= nu <= 10 and v.min() >= 0 and v.max() <= 10:
                out.append({"열 이름": c, "추정 유형": "리커트 척도",
                            "근거": f"{int(v.min())}~{int(v.max())}점 정수, 보기 {nu}개"})
            else:
                out.append({"열 이름": c, "추정 유형": "연속형 수치", "근거": f"평균 {v.mean():.1f}"})
            continue
        t = ser.astype(str).str.strip()
        avg_len = t.str.len().mean()
        if nu >= n * 0.9 and avg_len < 15:
            out.append({"열 이름": c, "추정 유형": "응답자 ID", "근거": "거의 모두 고유값"}); continue
        sep_found = None
        for sep in [";", ",", "/", "|"]:
            if t.str.contains(sep, regex=False).mean() > 0.3:
                sep_found = sep; break
        if sep_found:
            out.append({"열 이름": c, "추정 유형": "다중응답", "근거": f"구분기호 '{sep_found}'"})
        elif avg_len >= 15 or nu > n * 0.5:
            out.append({"열 이름": c, "추정 유형": "주관식(서술형)", "근거": f"평균 {avg_len:.0f}자"})
        else:
            out.append({"열 이름": c, "추정 유형": "객관식(단일선택)", "근거": f"보기 {nu}개"})
    return pd.DataFrame(out)

def guess_idx(cols, keys, default=0):
    """열 이름에 키워드가 있으면 그 위치를 기본 선택값으로"""
    for i, c in enumerate(cols):
        if any(k in str(c) for k in keys): return i
    return min(default, max(len(cols)-1, 0))


def reorder_by_rank(items, key, label="↕️ 표시 순서 바꾸기"):
    """멀티셀렉트는 고른 순서가 아니라 원래 열 순서대로 결과를 돌려주므로,
    표·그래프에 나오는 순서를 바꾸고 싶으면 여기서 순서 번호를 직접 매긴다."""
    if len(items) <= 1:
        return items
    with st.expander(label):
        rank_df = pd.DataFrame({"항목": items, "순서": range(1, len(items) + 1)})
        edited = st.data_editor(rank_df, key=f"rank_{key}_{hash(tuple(items))}", hide_index=True,
                                width="stretch", disabled=["항목"],
                                column_config={"순서": st.column_config.NumberColumn(min_value=1, step=1)})
    return edited.sort_values("순서", kind="stable")["항목"].tolist()

# 설문 그래프도 원클릭 보고서와 같은 블루 계열로 통일한다.
# 항목 수가 많아도 무지개색을 쓰지 않고 밝기 차이로만 구분해 전체 앱 분위기를 유지한다.
_SURVEY_COLORS = ["#DCE9F5", "#C2D9EE", "#A3C4E2", "#82ACD3", "#6291C2",
                  "#4576AB", "#2D5A8E", "#1F4569", "#7EA6C9", "#B5CEE3"]


def _survey_palette(k):
    if k <= 0:
        return []
    if k <= len(_SURVEY_COLORS):
        # 너무 옅은 색부터 시작하면 흰 배경에서 흐려 보이므로 중간 톤부터 순환
        base = _SURVEY_COLORS[2:] + _SURVEY_COLORS[:2]
        return base[:k]
    cmap = plt.get_cmap("Blues")
    return [cmap(0.35 + 0.55 * (i / max(k - 1, 1))) for i in range(k)]


def _autopct(vals, min_pct=5.0):
    def f(pct):
        n = int(round(pct/100.0*sum(vals)))
        return f"{pct:.1f}%\n({n}명)" if pct >= min_pct else ""
    return f

def pie_chart(counts, title, donut=False):
    """응답자 특성 → 원형/도넛 그래프 (보기 항목이 많으면 자동으로 범례로 전환)"""
    k = len(counts)
    many = k > 6
    fig, ax = plt.subplots(figsize=(figsize()[0] * (1.25 if many else 1.0), figsize()[1]))
    colors = _survey_palette(k)
    _pie_edge = "#111111" if st.session_state.get("fig_border", True) else "white"
    w = dict(width=0.45, edgecolor=_pie_edge, linewidth=0.7) if donut \
        else dict(edgecolor=_pie_edge, linewidth=0.7)
    # 조각이 완전히 붙어 보이지 않도록 아주 조금씩 띄운다.
    # (과한 explode는 보고서용 그래프에서 산만해 보이므로 2% 안팎만 적용)
    _explode = [0.008 if k > 6 else 0.012] * k
    wedges, *_ = ax.pie(counts.values,
                        labels=None if many else counts.index.astype(str),
                        autopct=_autopct(counts.values), startangle=90,
                        counterclock=False, colors=colors, wedgeprops=w,
                        explode=_explode,
                        pctdistance=0.72 if donut else 0.62,
                        textprops={"fontsize": 9, "color": "#2b2b2b"})
    if many:
        ax.legend(wedges, [f"{i} ({v}명)" for i, v in zip(counts.index.astype(str), counts.values)],
                  loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=8, frameon=False)
    if donut:
        ax.text(0, 0, f"n={int(counts.sum())}", ha="center", va="center",
                fontsize=12, fontweight="bold", color="#444")
    ax.set_title(title, fontsize=11, pad=10, fontweight="bold", color="#333")
    ax.axis("equal")
    plt.tight_layout()
    return fig

def break_even_qty(fixed_cost, variable_cost_total, qty, price):
    """손익분기수량 = 고정비 ÷ (판매단가 − 단위당 변동비).

    ★ 여기서 '변동비'는 **산출량(수량)에 비례하는** 비용만을 말한다. 10a 기준 작물
    예산에서는 종묘비·비료비·농약비·토지용역비·자가노력비처럼 대부분의 비용이
    '면적'에 대해 정해지며, 그해 수량이 줄어도 같이 줄지 않는다. 이런 비용까지
    변동비로 넣으면 단위당 변동비가 실제보다 훨씬 커지고 고정비는 거의 남지 않아
    손익분기수량이 터무니없이 작게 나온다(실제 318kg인데 23kg 같은 값).
    수량에 실제로 비례하는 비용(수확·선별·포장·운송비 등)이 없으면
    variable_cost_total = 0 이 되고, 이때 Q* = 고정비 ÷ 단가 가 된다.

    variable_cost_total은 해당 수량 qty를 생산하는 데 든 수량비례비 합계(단위당이 아님).
    단위당 수량비례비가 판매단가 이상이면(margin<=0) 아무리 팔아도 손익분기가 불가능하므로 NaN.
    """
    vc_unit = variable_cost_total / qty.where(qty != 0) if hasattr(qty, "where") \
        else (variable_cost_total / qty if qty else np.nan)
    margin = price - vc_unit
    if hasattr(margin, "where"):
        return fixed_cost / margin.where(margin > 0)
    return fixed_cost / margin if margin > 0 else np.nan


def crosstab_bar_label(v, pv, ymax):
    """교차분석 누적막대의 칸 안 글자를 정한다.

    칸이 넓으면 '9명\\n(30.0%)' 두 줄, 좁으면 '9명(30.0%)' 한 줄로 줄여서라도
    '명'과 '%'를 항상 남긴다. '명'·'%'를 통째로 빼고 숫자만 남기면 뭘 나타내는지
    알 수 없기 때문이다. 정말 작은 칸(전체의 5% 미만)만 아예 생략한다.

    반환: (문자열, 글자크기) 또는 표시할 수 없으면 None.
    """
    two_line, one_line = ymax * 0.11, ymax * 0.05
    if v >= two_line:
        return f"{int(v)}명\n({pv:.1f}%)", 7
    if v >= one_line:
        return f"{int(v)}명({pv:.1f}%)", 6.5
    return None


def likert_diverging(summ_counts, cats, title):
    """현대적인 블루/레드 다이버징 리커트 차트.

    부정은 부드러운 레드, 중립은 블루그레이, 긍정은 스마트 블루로 표시한다.
    """
    qs = list(summ_counts.keys())
    n_cat = len(cats)
    mid = n_cat // 2
    h = max(4.2, len(qs) * 0.62 + 1.8)
    w = max(8.8, figsize()[0] * 1.35)
    fig, ax = plt.subplots(figsize=(w, h))

    # 낮은 점수(부정) → 옅은~진한 레드 / 높은 점수(긍정) → 옅은~진한 블루
    neg_full = ["#F3D8D8", "#E8AAAA", "#C96767", "#A94D4D"]
    pos_full = ["#D6E7F4", "#9EC5E5", "#6291C2", "#2D5A8E"]
    neg = neg_full[max(0, len(neg_full)-mid):]
    pos = pos_full[max(0, len(pos_full)-mid):]
    neutral = [_SMART_CHART_NEUTRAL] if n_cat % 2 == 1 else []
    palette = neg + neutral + pos
    if len(palette) != n_cat:
        palette = [plt.get_cmap("RdBu")(0.18 + 0.64*i/max(n_cat-1,1)) for i in range(n_cat)]

    data = np.array([summ_counts[q] for q in qs], dtype=float)
    den = data.sum(axis=1, keepdims=True)
    den[den == 0] = 1
    pct = data / den * 100
    base = pct[:, :mid].sum(axis=1) + (pct[:, mid]/2 if n_cat % 2 == 1 else 0)
    starts = -base
    for i, cat in enumerate(cats):
        left_now = starts.copy()
        bars = ax.barh(qs, pct[:, i], left=left_now, color=palette[i], label=str(cat),
                       edgecolor="white", linewidth=.9, height=.58)
        for _b, _v, _l in zip(bars, pct[:, i], left_now):
            if _v >= 8.0:
                _is_dark = ((i < mid and i >= max(mid-1, 0)) or
                            (i >= mid + (1 if n_cat % 2 else 0) + max(len(pos)-2, 0)))
                # 홀수 척도의 중립 구간은 중심이 정확히 x=0이라 기준선과 글자가 겹친다.
                # 중립 라벨만 0선 오른쪽의 구간 안쪽으로 살짝 옮긴다.
                if n_cat % 2 == 1 and i == mid:
                    _half = float(_v) / 2.0
                    _x_text = min(max(3.5, float(_v) * 0.18), max(3.5, _half - 2.0))
                else:
                    _x_text = _l + _v/2
                ax.text(_x_text, _b.get_y()+_b.get_height()/2, f"{_v:.0f}%",
                        ha="center", va="center", fontsize=7.5, zorder=4,
                        color="white" if _is_dark else "#31485E", fontweight="bold")
        starts = starts + pct[:, i]

    ax.axvline(0, color="#71869A", lw=.65, zorder=1)
    ax.set_xlabel("응답 비율(%)")
    ax.invert_yaxis()
    ax.set_xlim(-105, 105)
    deco(ax, title, ylabel_top=False)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color="#E4EDF5", linewidth=.8)
    ax.legend(ncol=min(n_cat, 7), loc="upper center", bbox_to_anchor=(0.5, 1.14),
              fontsize=8, frameon=False, columnspacing=1.2, handlelength=1.4)
    fig.subplots_adjust(top=0.82, bottom=0.12, left=0.20 if len(qs) > 4 else 0.16, right=0.98)
    return fig

def build_stat_method_text(logs, extra=None):
    """분석 이력을 읽어 논문·보고서의 '통계처리' 문단을 자동 생성"""
    acts = " ".join(str(l.get("작업", "")) for l in logs)
    used = []
    if "난괴법" in acts or "블록" in acts or "ANOVA" in acts or "분산분석" in acts:
        used.append("분산분석(ANOVA)")
    if "반복측정" in acts: used.append("반복측정 분산분석")
    if "ANCOVA" in acts or "공분산" in acts: used.append("공분산분석(ANCOVA)")
    if "상관" in acts: used.append("상관분석")
    if "회귀" in acts: used.append("회귀분석")
    if "비모수" in acts or "Kruskal" in acts: used.append("비모수 검정")
    if "프로빗" in acts: used.append("프로빗 분석")
    if "PCA" in acts or "주성분" in acts: used.append("주성분분석")
    if "교차분석" in acts or "카이제곱" in acts: used.append("카이제곱 검정")
    if "크론바흐" in acts or "리커트" in acts or "설문" in acts: used.append("신뢰도 분석")
    extra = extra or {}
    # 원클릭 분석처럼 실제로 실행한 방법을 직접 넘겨받으면 작업 기록보다 우선한다.
    used = list(extra.get("methods") or []) + used

    _PH_LABELS = [("Tukey", "Tukey의 HSD 검정"), ("던컨", "던컨의 다중검정(DMRT)"),
                  ("Duncan", "던컨의 다중검정(DMRT)"), ("Bonferroni", "Bonferroni 보정"),
                  ("던넷", "Dunnett 검정(대조구 대비)"), ("Dunnett", "Dunnett 검정(대조구 대비)")]
    ph = None
    for src in (str(extra.get("posthoc") or ""), acts):
        for name, label in _PH_LABELS:
            if name in src:
                ph = label
                break
        if ph:
            break

    s = "모든 자료의 통계분석은 Python의 statsmodels, scipy 라이브러리를 이용하여 수행하였다."
    if used:
        s += " 분석 방법으로는 " + ", ".join(dict.fromkeys(used)) + "을(를) 적용하였다."
    if extra and extra.get("design"):
        s += f" 시험은 {extra['design']}으로 배치하였다."
    if ph:
        s += f" 처리 평균 간 비교는 {ph}(p<0.05)으로 실시하였다."
    if extra.get("err"):
        s += f" 표와 그림의 값은 평균±{extra['err']}로 나타내었다."
    if extra.get("letters"):
        s += " 같은 문자로 표시된 처리 간에는 5% 수준에서 유의한 차이가 없다."
    if extra.get("cv"):
        s += f" 시험의 변이계수(CV)는 {extra['cv']}%였다."
    s += " 유의수준은 5%로 하였다."
    return s

def build_abstract(items, meta=None):
    """보고서에 담긴 분석 결과를 읽어 '적요(요약)' 초안을 자동 작성"""
    meta = meta or {}
    lines = []
    title = meta.get("title")
    purpose = meta.get("purpose")
    design = meta.get("design")
    if purpose:
        lines.append(f"본 시험은 {purpose}"
                     + ("" if str(purpose).rstrip().endswith(("다.", "다", ".")) else "를 위하여 수행하였다."))
    elif title:
        lines.append(f"본 시험은 '{title}'을(를) 목적으로 수행하였다.")
    if design:
        lines.append(f"시험은 {design}으로 배치하였다.")

    # 담긴 분석에서 유의한 결과 추출
    findings, tables_seen = [], 0
    for it in items:
        blocks = it.get("blocks") or [{"text": it.get("text"), "table": it.get("table")}]
        for b in blocks:
            tb = b.get("table")
            if tb is None or not hasattr(tb, "columns"):
                continue
            cols = [str(c) for c in tb.columns]
            tables_seen += 1
            # 분산분석 요약형(측정 항목/유의성)
            if "측정 항목" in cols and "유의성" in cols:
                sig = tb[tb["유의성"].astype(str).str.contains("유의")]
                for _, r in sig.iterrows():
                    _pv = r.get("p-value")
                    _ptag = ""
                    if pd.notna(_pv):
                        try:
                            _pf = float(_pv)
                            _ptag = " (p<0.001)" if _pf < 0.001 else f" ({fmt_p(_pf)})"
                        except Exception:
                            _ptag = ""
                    findings.append(f"{r['측정 항목']}은 '{r.get('최고 처리구','')}'에서 "
                                    f"{r.get('최고 평균','')}로 가장 높아" + "||" + _ptag)
            # 평균+유의성형
            elif "유의성" in cols and "평균" in cols:
                try:
                    top = tb.sort_values("평균", ascending=False).iloc[0]
                    gcol = cols[0]
                    if str(top.get("유의성", "")).strip():
                        findings.append(f"{gcol} 중 '{top[gcol]}'의 평균이 {top['평균']}로 가장 높아||")
                except Exception:
                    pass
            # 경제성형
            elif "소득" in cols and "소득률(%)" in cols:
                try:
                    top = tb.sort_values("소득", ascending=False).iloc[0]
                    findings.append(f"'{top[cols[0]]}'의 소득이 "
                                    f"{int(top['소득']):,}원/10a(소득률 {float(top['소득률(%)']):.1f}%)으로 가장 높아||")
                except Exception:
                    pass
            # 증수형
            elif "증수율(%)" in cols and "소득증가액" in cols:
                try:
                    top = tb.sort_values("소득증가액", ascending=False).iloc[0]
                    if float(top["증수율(%)"]) > 0:
                        findings.append(f"'{top[cols[0]]}'은 대조구 대비 {top['증수율(%)']}% 증수되어 "
                                        f"소득증가액 {int(top['소득증가액']):,}원/10a을 나타내||")
                except Exception:
                    pass
    if findings:
        uniq = list(dict.fromkeys(findings))[:4]
        lines.append("주요 결과는 다음과 같다.")
        for u in uniq:
            _body, _sep, _tag = u.partition("||")
            lines.append("  - " + _body.replace("가장 높아", "가장 높았다")
                                       .replace("나타내", "나타내었다") + _tag)
    else:
        lines.append("분석 결과를 보고서에 담으면 주요 결과가 자동으로 요약됩니다.")
    if meta.get("cv"):
        lines.append(f"시험의 변이계수(CV)는 {meta['cv']}%로 시험 정밀도는 양호하였다.")
    lines.append("이상의 결과를 종합할 때, 본 시험에서 얻어진 결과는 "
                 "현장 적용 및 후속 연구의 기초 자료로 활용될 수 있을 것으로 판단된다.")
    return "\n".join(ln if ln.startswith("  -") else f"◦ {ln}" for ln in lines)

def set_df(new_df, memo=""):
    """데이터를 바꾸기 전에 현재 상태를 되돌리기 스택에 저장"""
    hist = st.session_state.setdefault("undo_stack", [])
    cur = st.session_state.get("df")
    if cur is not None:
        hist.append({"df": cur.copy(), "memo": memo})
        if len(hist) > 10:      # 최근 10단계만 유지
            hist.pop(0)
    st.session_state.df = new_df

def undo_df():
    hist = st.session_state.get("undo_stack", [])
    if hist:
        last = hist.pop()
        st.session_state.df = last["df"]
        return last["memo"]
    return None

def keep_running(key, label, **kw):
    """버튼을 누른 뒤 화면이 다시 그려져도 결과를 유지하되, 자료·유효성 변경 시 해제한다."""
    flag, sig_key = f"__ran_{key}", f"__sig_{key}"
    _d = st.session_state.get("df")
    try:
        cur_sig = dataframe_signature(_d) if _d is not None else None
    except Exception:
        cur_sig = (_d.shape, tuple(map(str, _d.columns))) if _d is not None else None
    # 검증 오류로 버튼이 비활성화되면 과거 실행 상태도 반드시 해제한다.
    # 입력이 '잠깐' 유효하지 않은 것일 수도 있으므로(메뉴를 옮겼다 와서 위젯이 초기화된
    # 직후 등) 실행 기록 자체는 지우지 않는다. 이번 화면에서만 결과를 감춘다.
    if kw.get("disabled", False):
        st.button(label, key=f"__btn_{key}", **kw)
        return False
    if st.button(label, key=f"__btn_{key}", **kw):
        st.session_state[flag] = True
        st.session_state[sig_key] = cur_sig
    # 자료가 바뀌면 결과를 감추되 기록은 남긴다 — 원래 자료로 돌아오면 다시 보인다.
    return bool(st.session_state.get(flag)) and st.session_state.get(sig_key) == cur_sig

def fmt_num(df, cols=None, dec=0):
    out = df.copy()
    if cols is None:
        cols = [c for c in out.columns if pd.api.types.is_numeric_dtype(out[c])]
    for c in cols:
        if c in out.columns and pd.api.types.is_numeric_dtype(out[c]):
            out[c] = out[c].map(lambda v: "-" if pd.isna(v) else f"{v:,.{dec}f}")
    return out

def show_money(df, money_cols, dec=0):
    """경제성 금액 표시: 내부 원값은 유지하고 ROUND_HALF_UP으로만 표시한다."""
    out = df.copy()
    for c in [c for c in money_cols if c in out.columns]:
        out[c] = out[c].map(
            lambda v: "-" if pd.isna(v) else f"{round_half_up(v, dec):,.{dec}f}")
    return out

# 공식 조사자료 기반 기준단가 (기준연도 명시 / 매년 갱신 필요)
_PRICE_DEFAULTS = [
    # 항목, 단가, 단위, 기준연도, 출처
    ("농업노임(남)", 153520, "원/일", "2025년",
     "통계청 농가판매·구입가격조사(KOSIS, 국가승인 306001)"),
    ("농업노임(여)", 121392, "원/일", "2025년",
     "통계청 농가판매·구입가격조사(KOSIS, 국가승인 306001)"),
    ("농업노임(남, 시간)", 19190, "원/시간", "2025년",
     "남자 일당 153,520원 ÷ 8시간 (소득조사 환산 기준)"),
    ("농업노임(여, 시간)", 15174, "원/시간", "2025년",
     "여자 일당 121,392원 ÷ 8시간 (소득조사 환산 기준)"),
    ("요소비료(20kg)", 17900, "원/포", "2026년",
     "농협 무기질비료 판매가 (보조금 적용 실구매가 16,250원)"),
    ("무기질비료(톤)", 871000, "원/톤", "2026년",
     "농협 무기질비료 평균 판매가격(전년 825,000원, +5.6%)"),
    ("토지용역비(논)", 275, "원/㎡", "2024년",
     "농지임차료실태조사(농식품부, 국가승인 114062) — 10a=1,000㎡"),
    ("토지용역비(밭)", 260, "원/㎡", "2024년",
     "농지임차료실태조사(농식품부) — 10a 환산 시 260,000원"),
    ("토지용역비(과수원)", 342, "원/㎡", "2024년",
     "농지임차료실태조사(농식품부)"),
    ("자본이자율", 5.0, "%", "관행",
     "농촌진흥청 소득조사 적용 이자율 — 소득자료집 원문 확인 권장"),
    ("농기계 임차료(경운기/일)", 0, "원/일", "-",
     "시군 농기계임대사업소 개별 고시 — 지역별로 다름"),
    ("위탁영농비", 0, "원/10a", "-",
     "농촌진흥청 소득자료집 작목별 경영비 항목 참고"),
]

def default_price_db():
    """⑫ 메타데이터를 모두 포함한 기준단가 표"""
    import datetime as _dt
    today = _dt.date.today().isoformat()
    return pd.DataFrame(
        [{"항목": a, "단가": b, "단위": c, "기준연도": d, "출처": e,
          "조회방식": "기본값", "갱신일": today, "환산식": "", "사용자수정": False}
         for a, b, c, d, e in _PRICE_DEFAULTS])


def price_db_warnings(db, current_year=None):
    """기준연도가 오래됐거나 단가가 비어 있는 항목을 찾아 경고 문구 목록 반환"""
    import datetime as _dt
    import re as _re
    if db is None or getattr(db, "empty", True):
        return []
    cy = current_year or _dt.date.today().year
    old_items, zero_items = [], []
    for _, r in db.iterrows():
        name = str(r.get("항목", "")).strip()
        if not name:
            continue
        try:
            val = float(r.get("단가", 0) or 0)
        except (TypeError, ValueError):
            val = 0.0
        if val <= 0:
            zero_items.append(name)
        yr_txt = str(r.get("기준연도", ""))
        m = _re.search(r"(19|20)\d{2}", yr_txt)
        if m and (cy - int(m.group(0))) >= 2:
            old_items.append(f"{name}({m.group(0)}년)")
    msgs = []
    if old_items:
        msgs.append("현재 분석에는 " + ", ".join(old_items[:5])
                    + (" 등" if len(old_items) > 5 else "")
                    + " 기준 단가가 사용되었습니다. 최신 지역 단가와 차이가 있을 수 있습니다.")
    if zero_items:
        msgs.append("단가가 0이거나 비어 있는 항목: " + ", ".join(zero_items[:6])
                    + (" 등" if len(zero_items) > 6 else "")
                    + " — 값을 채우기 전에는 계산에 자동 반영하지 않습니다.")
    return msgs

def _kamis_parse_unit(unit_text):
    """'20kg' → (20.0, '20kg') 처럼 kg 환산계수를 추출. 환산 불가면 (None, 원문)"""
    import re as _re
    if not unit_text:
        return None, ""
    t = str(unit_text).strip()
    m = _re.match(r"^\s*([\d.]+)?\s*(kg|g|톤|개|포|망|상자|단)\s*$", t, _re.I)
    if not m:
        return None, t
    num = float(m.group(1)) if m.group(1) else 1.0
    unit = m.group(2).lower()
    if unit == "kg":
        return num, t
    if unit == "g":
        return num / 1000.0, t
    if unit == "톤":
        return num * 1000.0, t
    return None, t          # 개·포·망 등은 kg 환산 불가


def _kamis_ssl_context(verify=True, legacy=True):
    """KAMIS(구형 국내 서버) 호환 SSLContext.

    OpenSSL 3.x 는 기본적으로
      - RFC5746 미지원 서버(레거시 재협상)
      - SECLEVEL 2 미만의 약한 키/암호군
      - TLS 1.0/1.1
    을 모두 거부한다. 국내 공공기관 서버는 이 중 하나에 걸리는 경우가 많아
    핸드셰이크 단계에서 SSLError 가 난다. 아래 컨텍스트는 검증(인증서 확인)은
    그대로 유지한 채 호환성 옵션만 풀어 준다.
    """
    import ssl as _ssl
    ctx = _ssl.create_default_context()
    if legacy:
        # OP_LEGACY_SERVER_CONNECT (0x4) : RFC5746 미지원 서버 허용
        ctx.options |= getattr(_ssl, "OP_LEGACY_SERVER_CONNECT", 0x4)
        try:
            import warnings as _w
            with _w.catch_warnings():
                _w.simplefilter("ignore", DeprecationWarning)
                ctx.minimum_version = _ssl.TLSVersion.TLSv1
        except Exception:
            pass
        for _cipher in ("DEFAULT@SECLEVEL=1", "ALL:@SECLEVEL=1"):
            try:
                ctx.set_ciphers(_cipher)
                break
            except Exception:
                continue
    if not verify:
        ctx.check_hostname = False
        ctx.verify_mode = _ssl.CERT_NONE
    return ctx


def _kamis_session(ssl_context=None):
    """지정한 SSLContext 를 http/https 양쪽에 적용한 requests 세션."""
    from requests.adapters import HTTPAdapter

    class _KamisAdapter(HTTPAdapter):
        def __init__(self, ssl_context=None, **kw):
            self._kamis_ctx = ssl_context
            super().__init__(**kw)

        def init_poolmanager(self, *a, **kw):
            if self._kamis_ctx is not None:
                kw["ssl_context"] = self._kamis_ctx
            return super().init_poolmanager(*a, **kw)

        def proxy_manager_for(self, *a, **kw):
            if self._kamis_ctx is not None:
                kw["ssl_context"] = self._kamis_ctx
            return super().proxy_manager_for(*a, **kw)

    sess = _requests.Session()
    adapter = _KamisAdapter(ssl_context=ssl_context, max_retries=0)
    sess.mount("https://", adapter)
    sess.mount("http://", adapter)
    return sess


def kamis_request(url, params, timeout=20):
    """KAMIS 공식 Open-API 호출 (다단계 폴백).

    공식 도메인은 ``www.kamis.or.kr`` 이고 공식 예제는 http/https 를 모두 쓴다.
    KAMIS 서버는 구형 TLS 설정을 쓰는 경우가 있어 OpenSSL 3.x 환경
    (Streamlit Cloud 등)에서 기본 설정만으로는 핸드셰이크가 실패할 수 있다.
    아래 순서대로 시도하고, 성공한 방식을 ``r._smart_transport`` 에 기록한다.

      1) https + 기본 설정                → 'https'
      2) http  (리다이렉트 시 레거시 컨텍스트) → 'http-fallback'
      3) https + 레거시 호환 컨텍스트(검증 유지) → 'https-legacy'
      4) https + 레거시 + 인증서 검증 생략   → 'https-insecure' (경고 표시)

    4단계는 인증서 검증을 끄므로 최후 수단이며, 성공해도 UI 에 경고를 띄운다.
    """
    if not _HAS_REQUESTS:
        raise RuntimeError("requests 라이브러리가 없습니다. pip install requests")

    raw_url = str(url).strip()
    if raw_url.startswith("http://"):
        https_url = "https://" + raw_url[len("http://"):]
    elif raw_url.startswith("https://"):
        https_url = raw_url
    else:
        https_url = "https://" + raw_url.lstrip("/")
    http_url = "http://" + https_url[len("https://"):]

    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/131.0 Safari/537.36'),
        'Accept': 'application/json, application/xml, text/xml, */*',
        'Connection': 'close',
    }

    attempts = []          # (라벨, 호출가능객체) 순서대로 시도
    attempts.append(("https", lambda: _requests.get(
        https_url, params=params, timeout=timeout, headers=headers)))

    def _legacy_http():
        sess = _kamis_session(_kamis_ssl_context(verify=True, legacy=True))
        try:
            return sess.get(http_url, params=params, timeout=timeout,
                            headers=headers)
        finally:
            try: sess.close()
            except Exception: pass
    attempts.append(("http-fallback", _legacy_http))

    def _legacy_https():
        sess = _kamis_session(_kamis_ssl_context(verify=True, legacy=True))
        try:
            return sess.get(https_url, params=params, timeout=timeout,
                            headers=headers)
        finally:
            try: sess.close()
            except Exception: pass
    attempts.append(("https-legacy", _legacy_https))

    def _insecure_https():
        try:
            import urllib3 as _u3
            _u3.disable_warnings(_u3.exceptions.InsecureRequestWarning)
        except Exception:
            pass
        sess = _kamis_session(_kamis_ssl_context(verify=False, legacy=True))
        try:
            return sess.get(https_url, params=params, timeout=timeout,
                            headers=headers, verify=False)
        finally:
            try: sess.close()
            except Exception: pass
    attempts.append(("https-insecure", _insecure_https))

    errors = []
    for label, call in attempts:
        try:
            r = call()
        except Exception as ex:
            errors.append(f"{label}: {_kamis_err_text(ex)}")
            continue
        try:
            r._smart_transport = label
        except Exception:
            pass
        return r

    raise RuntimeError(
        "KAMIS 서버에 연결하지 못했습니다. 시도한 방식과 원인:\n- "
        + "\n- ".join(errors))


def _kamis_err_text(ex, limit=200):
    """SSLError 등의 실제 원인(가장 안쪽 예외)까지 풀어서 문자열로 만든다."""
    parts, seen, cur = [], set(), ex
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        txt = str(cur).strip()
        if txt and txt not in parts:
            parts.append(txt)
        cur = getattr(cur, "__cause__", None) or getattr(cur, "__context__", None)
    # urllib3 는 원인을 reason 속성에 담아 두기도 한다
    reason = getattr(ex, "reason", None)
    if reason is not None and str(reason).strip() not in parts:
        parts.append(str(reason).strip())
    msg = " / ".join(parts) if parts else type(ex).__name__
    # 가장 유용한 [SSL: XXX] 코드가 있으면 앞으로 끌어올린다
    import re as _re
    m = _re.search(r"\[SSL:[^\]]+\][^\)\'\"]*", msg)
    head = f"{type(ex).__name__}"
    if m:
        return f"{head} {m.group(0).strip()} | {msg[:limit]}"
    return f"{head}: {msg[:limit]}"


KAMIS_ITEM_CATEGORY_MAP = {
    "111": "100", "211": "200", "225": "200", "231": "200", "245": "200",
    "258": "200", "312": "300", "411": "400",
}


def _normalize_kamis_date(year, regday):
    import re as _re
    y = str(year or "").strip()
    d = str(regday or "").strip().replace("/", "-").replace(".", "-")
    d = _re.sub(r"-+", "-", d).strip("-")
    if not d:
        return y
    if len(d.split("-")) == 2 and y:
        mm, dd = d.split("-", 1)
        return f"{y}-{int(mm):02d}-{int(dd):02d}"
    if len(d.split("-")) == 3:
        yy, mm, dd = d.split("-", 2)
        return f"{int(yy):04d}-{int(mm):02d}-{int(dd):02d}"
    return f"{y}-{d}".strip("-")


def kamis_fetch(cert_key, cert_id, item_code, kind_code, rank_code,
                days=7, country_code="", product_cls="02", category_code=None,
                market_type="도매", convert_kg=False, county_code=None):
    """KAMIS 기간별 품목가격 조회. 반환: (DataFrame|None, 오류메시지|None).

    county_code는 이전 버전 호출과의 호환용이며 실제 요청에는 공식 p_countrycode를 사용한다.
    """
    if county_code and not country_code:
        country_code = county_code
    missing = [n for n, v in [("인증키", cert_key), ("아이디", cert_id),
                              ("품목코드", item_code)] if not str(v or "").strip()]
    if missing:
        return None, f"{', '.join(missing)}을(를) 입력해 주세요."
    try:
        days = int(days)
        if not (1 <= days <= 365):
            return None, "조회 기간은 1~365일 사이여야 합니다."
    except (TypeError, ValueError):
        return None, "조회 기간이 올바르지 않습니다."
    item_code = str(item_code).strip()
    category_code = str(category_code or KAMIS_ITEM_CATEGORY_MAP.get(item_code, "")).strip()
    if not category_code:
        return None, "품목에 맞는 부류코드를 지정해 주세요(예: 채소 200, 특용작물 300)."
    if market_type not in ("도매", "소매"):
        return None, "시장 유형은 '도매' 또는 '소매'여야 합니다."

    import datetime as _dt
    end = _dt.date.today()
    start = end - _dt.timedelta(days=days)
    # KAMIS의 일별 품목별 도·소매 가격 API는 periodProductList 하나를 사용하고
    # p_productclscode로 도매(02)/소매(01)를 구분한다.
    action = "periodProductList"
    product_cls = "02" if market_type == "도매" else "01"
    url = "https://www.kamis.or.kr/service/price/xml.do"
    params = {"action": action,
              "p_cert_key": str(cert_key).strip(), "p_cert_id": str(cert_id).strip(),
              "p_returntype": "json", "p_startday": start.isoformat(),
              "p_endday": end.isoformat(), "p_productclscode": str(product_cls),
              "p_itemcategorycode": category_code, "p_itemcode": item_code,
              "p_kindcode": str(kind_code or ""), "p_productrankcode": str(rank_code or ""),
              "p_countrycode": str(country_code or ""),
              "p_convert_kg_yn": "Y" if convert_kg else "N"}
    try:
        r = kamis_request(url, params)
    except RuntimeError as ex:
        return None, str(ex)
    except Exception as ex:
        return None, f"KAMIS 연결 오류 - {_kamis_err_text(ex)}"
    if getattr(r, "status_code", 0) != 200:
        return None, f"KAMIS 서버 응답 오류(HTTP {getattr(r, 'status_code', '?')})"
    # KAMIS는 xml.do 주소에서 p_returntype=json을 써도 환경/오류 종류에 따라
    # XML을 돌려주는 경우가 있어 JSON과 XML을 모두 받을 수 있게 한다.
    js = None
    try:
        js = r.json()
    except Exception:
        try:
            import xml.etree.ElementTree as _ETK
            _root = _ETK.fromstring(getattr(r, "text", "") or "")
            def _xml_dict(el):
                children = list(el)
                if not children:
                    return (el.text or "").strip()
                out = {}
                for ch in children:
                    val = _xml_dict(ch)
                    if ch.tag in out:
                        if not isinstance(out[ch.tag], list): out[ch.tag] = [out[ch.tag]]
                        out[ch.tag].append(val)
                    else:
                        out[ch.tag] = val
                return out
            js = _xml_dict(_root)
        except Exception:
            _ct = str(getattr(r, "headers", {}).get("Content-Type", ""))[:80]
            return None, ("KAMIS 응답 형식을 해석하지 못했습니다. "
                          f"HTTP {getattr(r, 'status_code', '?')}, Content-Type={_ct or '미상'}")

    if isinstance(js, dict):
        condition = js.get("condition") or {}
        code = (condition.get("code") if isinstance(condition, dict) else None)
        code = code or js.get("error_code") or js.get("errCode")
        if code and str(code) not in ("000", "0"):
            msg = condition.get("message") if isinstance(condition, dict) else ""
            return None, f"KAMIS 오류({code}): {msg or '인증 정보 또는 조회 조건을 확인해 주세요.'}"
        data = js.get("data", js)
    else:
        data = js
    if isinstance(data, dict):
        _dcode = (data.get("error_code") or data.get("errCode") or
                  data.get("result_code") or data.get("resultCode"))
        if _dcode and str(_dcode) not in ("000", "0"):
            _dmsg = data.get("error_msg") or data.get("message") or data.get("result_msg") or ""
            return None, f"KAMIS 오류({_dcode}): {_dmsg or '인증 정보 또는 조회 조건을 확인해 주세요.'}"
    items = data.get("item") if isinstance(data, dict) else (data if isinstance(data, list) else None)
    if not items:
        return None, "조회 결과가 없습니다. 품목·품종·등급·지역·기간을 확인해 주세요."
    if isinstance(items, dict):
        items = [items]
    rows = []
    for it in items:
        if not isinstance(it, dict):
            continue
        date_s = _normalize_kamis_date(it.get("yyyy"), it.get("regday"))
        unit_raw = it.get("unit") or it.get("unitname") or ("1kg" if convert_kg else "")
        kg_factor, unit_text = _kamis_parse_unit(unit_raw)
        price_raw = str(it.get("price", "")).replace(",", "").strip()
        try:
            price = float(price_raw) if price_raw not in ("", "-") else float("nan")
        except ValueError:
            price = float("nan")
        rows.append({"기준일": date_s, "시장유형": market_type,
                     "품목": it.get("itemname", ""), "품종": it.get("kindname", ""),
                     "시장/지역": it.get("countyname", it.get("marketname", "")),
                     "가격": price, "단위": unit_text or "(단위 미상)",
                     "kg환산계수": kg_factor, "부류코드": category_code,
                     "품목코드": item_code, "출처": "KAMIS 농산물유통정보"})
    if not rows:
        return None, "조회 결과를 표로 만들지 못했습니다."
    _dfk = pd.DataFrame(rows)
    try:
        _dfk.attrs["kamis_transport"] = getattr(r, "_smart_transport", "https")
    except Exception:
        pass
    return _dfk, None


@st.cache_data(show_spinner=False, ttl=3600, max_entries=30)
def kosis_fetch_url(url):
    """KOSIS 오픈API URL을 그대로 호출해 표로 변환 (KOSIS 사이트에서 복사한 URL 사용)"""
    if not _HAS_REQUESTS:
        return None, "requests 라이브러리가 없습니다."
    if "kosis.kr" not in url:
        return None, "KOSIS 주소가 아닙니다. kosis.kr 로 시작하는 URL을 넣어 주세요."
    try:
        u = url.strip().replace("http://", "https://")
        if "format=" not in u:
            u += ("&" if "?" in u else "?") + "format=json&jsonVD=Y"
        r = _requests.get(u, timeout=30)
        if r.status_code != 200:
            return None, f"KOSIS 오류({r.status_code})"
        js = r.json()
        if isinstance(js, dict) and js.get("err"):
            return None, f"KOSIS 응답 오류: {js.get('errMsg', js.get('err'))}"
        if not isinstance(js, list) or not js:
            return None, "조회 결과가 없습니다. 통계표·시점 설정을 확인해 주세요."
        rows = []
        for it in js:
            rows.append({
                "시점": it.get("PRD_DE", ""),
                "항목": it.get("ITM_NM", ""),
                "분류1": it.get("C1_NM", ""),
                "분류2": it.get("C2_NM", ""),
                "값": it.get("DT", ""),
                "단위": it.get("UNIT_NM", ""),
                "통계표": it.get("TBL_NM", "")})
        return pd.DataFrame(rows), None
    except Exception as ex:
        return None, f"조회 실패: {str(ex)[:80]}"

def kosis_build_url(api_key, org_id, tbl_id, itm_id="ALL", obj_l1="ALL",
                    prd_se="Y", count=5):
    """파라미터로 KOSIS 요청 URL 만들기"""
    return ("https://kosis.kr/openapi/Param/statisticsParameterData.do"
            f"?method=getList&apiKey={api_key}&itmId={itm_id}&objL1={obj_l1}"
            f"&format=json&jsonVD=Y&prdSe={prd_se}&newEstPrdCnt={int(count)}"
            f"&orgId={org_id}&tblId={tbl_id}")

def get_price(item, default=0.0):
    """기준단가 DB에서 값을 읽음(없으면 default)"""
    db = st.session_state.get("price_db")
    if db is None or db.empty: return default
    row = db[db["항목"].astype(str) == item]
    if row.empty: return default
    try:
        v = float(row.iloc[0]["단가"])
        return v if v > 0 else default
    except Exception:
        return default

def run_autopilot_engine(df, ph="Tukey HSD", err_type=None, max_items=8,
                         trt_override=None, blk_override=None, selected_items=None):
    """원클릭 오토파일럿: 정제 → 설계인지 → 분석 → 그래프 → 문장 → 보고서까지 한 번에.
    반환: dict(ok, blocks, summary, abstract, design, msgs)"""
    msgs = []
    prog = st.progress(0.0, text="1/5 데이터 점검 중...")

    # ---------- 1단계: 숫자 정제 ----------
    with st.spinner("1/5 데이터를 점검하고 정리하는 중..."):
        work = clean_columns(df.copy())
        # 처리구·반복으로 쓸 열은 숫자 변환에서 제외 (이름이 숫자로 바뀌는 것 방지)
        _keep_text = set()
        _pre = detect_design(work)
        for _k in (trt_override, blk_override, _pre.get("trt"), _pre.get("blk"), _pre.get("sub")):
            if _k: _keep_text.add(_k)
        fixed = []
        for c, ratio in find_numeric_like(work).items():
            if c in _keep_text:
                continue
            conv = to_numeric_clean(work[c])
            if conv.notna().mean() >= 0.6:
                work[c] = conv
                fixed.append(c)
        if fixed:
            msgs.append(f"문자로 읽힌 열을 숫자로 변환했습니다: {', '.join(fixed)}")
        n_before = len(work)
        work = work.dropna(how="all")
        if len(work) < n_before:
            msgs.append(f"완전히 빈 행 {n_before - len(work)}개를 제외했습니다.")
    prog.progress(0.2, text="2/5 실험설계 인지 중...")

    # ---------- 2단계: 설계 자동 인지 ----------
    with st.spinner("2/5 처리구·반복·측정항목을 찾는 중..."):
        dsg = detect_design(work)
        if dsg.get("promoted"):
            msgs.append("숫자로 적혀 있지만 처리구·반복 코드로 보이는 열을 그룹으로 인식했습니다: "
                        + ", ".join(map(str, dsg["promoted"]))
                        + " (실제 측정값이라면 위 ⚙️ 설정에서 처리구·반복 열을 직접 지정하세요)")
        if not dsg.get("trt"):
            prog.empty()
            return {"ok": False, "msgs": msgs + ["처리구로 볼 만한 열을 찾지 못했습니다. "
                                                 "'분산분석' 화면에서 직접 선택해 주세요."]}
        trt = trt_override if trt_override in work.columns else dsg["trt"]
        blk = blk_override if blk_override in work.columns else dsg["blk"]
        if blk == trt: blk = None
        # 처리구·반복·부요인 및 '그룹처럼 보이는' 열은 측정항목에서 제외
        exclude = {trt, blk, dsg.get("sub")}
        orig_cat = set(df.columns) - set(df.select_dtypes(include=np.number).columns)
        ys = []
        for c in dsg["ys"]:
            if c in exclude or c is None:
                continue
            if c in orig_cat:          # 원래 문자였던 열(처리구 등)은 측정값이 아님
                continue
            uniq = work[c].nunique(dropna=True)
            if uniq <= 2 and len(work) > 6:   # 값이 2종류뿐이면 구분용 열일 가능성
                continue
            ys.append(c)
        if selected_items is not None:
            _selected = {str(c) for c in selected_items}
            ys = [c for c in ys if str(c) in _selected]
        elif max_items:
            ys = ys[:int(max_items)]
        if not ys:
            prog.empty()
            return {"ok": False, "msgs": msgs + ["분석할 숫자형 측정항목이 없습니다."]}
        msgs.append(f"실험설계: {dsg['design']} (확신도 {dsg['confidence']}) — "
                    f"처리구 '{trt}'" + (f", 반복 '{blk}'" if blk else ", 반복 없음"))
    prog.progress(0.4, text=f"3/5 {len(ys)}개 항목 분석 중...")

    # ---------- 3단계: 항목별 분산분석 + 사후검정 ----------
    use_se = (err_type or st.session_state.get("err_type", "표준편차(SD)")).startswith("표준오차")
    blocks, summary_rows, sentences = [], [], []
    _any_letters = False
    with st.spinner(f"3/5 {len(ys)}개 항목을 분석하고 그래프를 만드는 중..."):
        for k, yv in enumerate(ys):
            cols_need = [trt, yv] + ([blk] if blk else [])
            data = work[cols_need].dropna()
            ok_d, vmsg = validate_anova_data(data, trt, yv)
            if not ok_d:
                msgs.append(f"[{yv}] 건너뜀 — {vmsg[0] if vmsg else '자료 부족'}")
                continue
            try:
                formula = safe_formula(yv, [trt] + ([blk] if blk else []))
                model = ols(formula, data=data).fit()
                aov = sm.stats.anova_lm(model, typ=2)
                tkey = f"C({q_ref(trt)})"
                pval = float(aov.loc[tkey, "PR(>F)"]) if tkey in aov.index else float(aov["PR(>F)"].iloc[0])
                ci = calc_cv_lsd(model, data, trt, yv)
                _is_dunnett = str(ph).startswith(("던넷", "Dunnett"))
                _ctrl = st.session_state.get("dunnett_ctrl") if _is_dunnett else None
                _phres = posthoc_from_model(model, data, trt, ph, control=_ctrl)
                ns = _phres["not_sig"]
                means = data.groupby(trt)[yv].agg(["mean", "std", "count"])
                order = means.sort_values("mean", ascending=False).index.tolist()
                # 던넷(Dunnett)은 각 처리를 대조구와만 비교하므로, 전체 처리 쌍을 요구하는
                # 유의성 문자(a,b,c)를 만들 수 없다. 지금은 원클릭 사후검정 선택지에
                # 던넷이 없지만, 나중에 추가되더라도 여기서 막아 잘못된 문자가
                # 보고서에 실리지 않게 한다.
                letters = ({} if _is_dunnett
                           else (compact_letter_display(order, ns) if pval < .05 else {}))
                _any_letters = _any_letters or bool(letters)

                # 논문 표 형식: 평균값에 유의성 문자를 위첨자로 붙임 (예: 607.6^a)
                _dec = rnd()
                _se_v = (means["std"] / np.sqrt(means["count"]))
                res = pd.DataFrame({
                    trt: [str(g) for g in means.index],
                    f"{yv}": [f"{means.loc[g, 'mean']:.{_dec}f}"
                              + (f"^{letters[g]}" if letters.get(g) else "")
                              for g in means.index],
                    "표준편차": [round(float(means.loc[g, "std"]), _dec) for g in means.index],
                    "표준오차": [round(float(_se_v.loc[g]), _dec) for g in means.index],
                    "n": [int(means.loc[g, "count"]) for g in means.index]})
                res = res.set_index(trt).loc[[str(o) for o in order]].reset_index()

                # ---------- 4단계 일부: 그래프 ----------
                err = (means["std"] / np.sqrt(means["count"])) if use_se else means["std"]
                fig, ax = plt.subplots(figsize=figsize())
                mm, ee = means.loc[order], err.loc[order]
                _xs = [str(o) for o in order]
                ax.bar(_xs, mm["mean"], yerr=ee, capsize=4,
                       color=bar_colors(values=mm["mean"].tolist()),
                       edgecolor="none", width=.62 if pretty_on() else .8,
                       error_kw={"ecolor": "#5a6067", "elinewidth": 1.1})
                top = float(mm["mean"].max())
                _pad = bar_value_sig_labels(
                    ax, range(len(_xs)), mm["mean"].tolist(), ee.tolist(),
                    [letters.get(g, "") for g in order], dec=rnd())
                ax.set_ylabel(yv)
                ax.margins(y=.16 if pretty_on() else .05)
                deco(ax, f"{trt}별 {yv} (평균±{'표준오차' if use_se else '표준편차'})")
                plt.tight_layout()
                png = fig_to_png(fig, show=False)

                sent = report_sentence_anova(trt, yv, pval, means, letters, ci, ph)
                sentences.append(sent)
                blocks.append({"text": sent})
                blocks.append({"caption": f"{trt}별 {yv}", "table": res, "image": png})

                summary_rows.append({
                    "측정 항목": yv,
                    "최고 처리구": order[0],
                    "최고 평균": round(float(means.loc[order[0], "mean"]), rnd()),
                    "최저 처리구": order[-1],
                    "p-value": round(pval, 4),
                    "유의성": "유의(*)" if pval < .05 else "n.s.",
                    "CV(%)": round(ci["CV"], 1) if not np.isnan(ci["CV"]) else "-",
                    "LSD(0.05)": round(ci["LSD"], 2) if not np.isnan(ci["LSD"]) else "-"})
            except Exception as ex:
                msgs.append(f"[{yv}] 분석 실패: {str(ex)[:60]}")
            prog.progress(0.4 + 0.3 * (k + 1) / len(ys),
                          text=f"3/5 분석 중... ({k+1}/{len(ys)})")

    if not summary_rows:
        prog.empty()
        return {"ok": False, "msgs": msgs + ["분석 가능한 항목이 없었습니다."]}

    # ---------- 4단계: 요약표 · 통계처리 문구 ----------
    prog.progress(0.75, text="4/5 요약표와 문장을 정리하는 중...")
    with st.spinner("4/5 종합 요약을 만드는 중..."):
        summary = pd.DataFrame(summary_rows)
        n_sig = int((summary["유의성"] == "유의(*)").sum())
        head_txt = (f"◦ {dsg['design']}으로 배치된 시험 자료를 분석하였다.\n"
                    f"◦ 총 {len(summary)}개 측정항목 중 {n_sig}개 항목에서 "
                    "처리 간 유의한 차이가 인정되었다.")
        _cv_vals = [r["CV(%)"] for r in summary_rows if isinstance(r.get("CV(%)"), (int, float))]
        stat_line = build_stat_method_text(
            st.session_state.get("log", []),
            {"design": dsg["design"] if dsg.get("design") and "판별" not in str(dsg["design"]) else None,
             "methods": ["분산분석(ANOVA)"], "posthoc": ph,
             "err": "표준오차(SE)" if use_se else "표준편차(SD)",
             "letters": _any_letters,
             "cv": (f"{min(_cv_vals):.1f}~{max(_cv_vals):.1f}" if len(_cv_vals) > 1 and min(_cv_vals) != max(_cv_vals)
                    else (f"{_cv_vals[0]:.1f}" if _cv_vals else None))})
        head_blocks = [{"text": head_txt},
                       {"caption": "측정항목별 분석 종합", "table": summary}]

    # ---------- 5단계: 적요 + 보고서 파일 ----------
    prog.progress(0.9, text="5/5 보고서를 만드는 중...")
    with st.spinner("5/5 적요와 보고서 문서를 만드는 중..."):
        items_for_abs = [{"heading": "분석 종합", "blocks": head_blocks}]
        abstract = build_abstract(items_for_abs,
                                  {"design": dsg["design"] if blk else None})
        report_items = [
            {"heading": "적요(要約)", "text": abstract, "table": None, "image": None},
            {"heading": "분석 종합", "blocks": head_blocks + blocks},
            {"heading": "통계 처리", "text": stat_line, "table": None, "image": None}]
        try:
            hwpx = build_report_hwpx(report_items, "시험 통계 분석 보고서(초안)")
        except Exception as ex:
            hwpx = None; msgs.append(f"한글 보고서 생성 실패: {str(ex)[:60]}")
        docx_data = None
        if _HAS_DOCX:
            try:
                docx_data = build_report_docx(report_items, "시험 통계 분석 보고서(초안)")
            except Exception as ex:
                msgs.append(f"워드 보고서 생성 실패: {str(ex)[:60]}")
    prog.progress(1.0, text="완료!")
    prog.empty()
    return {"ok": True, "design": dsg, "summary": summary, "blocks": blocks,
            "head_blocks": head_blocks, "abstract": abstract, "stat_line": stat_line,
            "sentences": sentences, "report_items": report_items,
            "hwpx": hwpx, "docx": docx_data, "msgs": msgs, "ys": ys, "trt": trt, "blk": blk}

def two_way_sensitivity(base_qty, base_price, mgmt_cost, byproduct=0,
                        yield_variable_cost=0, q_range=(-20, 20), p_range=(-20, 20), step=10):
    """수량×단가 위험 매트릭스. 수량비례비용은 수량 변화에 함께 연동한다."""
    q_rates = list(range(int(q_range[0]), int(q_range[1]) + 1, int(step)))
    p_rates = list(range(int(p_range[0]), int(p_range[1]) + 1, int(step)))
    base_yvc = max(float(yield_variable_cost or 0), 0.0)
    fixed_like_mgmt = max(float(mgmt_cost) - base_yvc, 0.0)
    mat = np.zeros((len(q_rates), len(p_rates)))
    for i, qr in enumerate(q_rates):
        q_factor = 1 + qr/100
        for j, pr_ in enumerate(p_rates):
            revenue = base_qty * q_factor * base_price * (1 + pr_/100) + byproduct
            adjusted_cost = fixed_like_mgmt + base_yvc * q_factor
            mat[i, j] = revenue - adjusted_cost
    return pd.DataFrame(mat,
                        index=[f"{r:+d}%" for r in q_rates],
                        columns=[f"{r:+d}%" for r in p_rates])

def plot_sensitivity_heatmap(mat, title="수량·단가가 동시에 변할 때의 소득 변화"):
    """RdYlGn 히트맵 — 적자(빨강) ~ 흑자(초록)"""
    import seaborn as sns
    h = max(4.0, 0.55 * len(mat) + 1.6)
    w = max(5.5, 0.95 * len(mat.columns) + 2.2)
    fig, ax = plt.subplots(figsize=(w, h))
    disp = mat / 10000.0     # 만원 단위로 표시
    from matplotlib.colors import LinearSegmentedColormap
    _econ_cmap = LinearSegmentedColormap.from_list(
        "smart_econ_div", ["#C96767", "#F5E2E2", "#FFFFFF", "#D9EAF7", "#3D6F9F"])
    sns.heatmap(disp, annot=True, fmt=".0f", cmap=_econ_cmap, center=0,
                linewidths=.8, linecolor="white", ax=ax,
                cbar_kws={"label": "소득 (만원/10a)", "shrink": .82})
    ax.set_xlabel("단가 변동률"); ax.set_ylabel("수량 변동률")
    deco(ax, title + "  (단위: 만원/10a)", ylabel_top=False)
    ax.grid(False)
    for _sp in ax.spines.values():
        _sp.set_visible(False)
    try:
        _cb = ax.collections[0].colorbar
        if _cb is not None:
            _cb.outline.set_visible(False)
    except Exception:
        pass
    plt.tight_layout(pad=1.2)
    return fig

LABOR_HINTS = ("노동시간", "노력시간", "작업시간", "소요시간", "노동(시간", "시간")


def looks_like_hours(name):
    """'자가노동시간'처럼 값이 '원'이 아니라 '시간'인 열인지 이름으로 추정한다."""
    t = str(name).replace(" ", "")
    if any(k in t for k in ("시간당", "원/시간", "임률", "노임")):
        return False
    return any(k in t for k in LABOR_HINTS)


def partial_budget_from_data(data, trt_col, control, treated, qty_col, price,
                             cost_cols=(), area_a=10.0,
                             hour_cols=(), wage_per_hour=0.0):
    """올린 데이터에서 '대조구 → 신기술구'로 바뀐 것만 뽑아 부분예산표 두 장을 만든다.

    - 손실적 요소(A) = 늘어난 비용 + 줄어든 수익
    - 이익적 요소(B) = 늘어난 수익 + 줄어든 비용
    반복이 여러 개면 처리구 평균을 쓰고, 자료 기준면적을 10a로 환산한다.
    산출근거는 검산기가 읽을 수 있게 숫자와 사칙연산만 넣는다.

    hour_cols: 값이 '원'이 아니라 '시간'인 열(자가노동시간 등).
               늘어난 시간 × wage_per_hour 로 금액을 만들어 넣는다.
               (환산하지 않으면 '10시간'이 '10원'으로 들어가 버린다)
    """
    hour_cols = [c for c in (hour_cols or []) if c and c != qty_col]
    cost_cols = [c for c in (cost_cols or [])
                 if c and c != qty_col and c not in hour_cols]
    wage = float(wage_per_hour or 0.0)
    if hour_cols and wage <= 0:
        raise ValueError("노동시간 열을 금액으로 바꾸려면 시간당 노임을 입력해야 합니다.")
    if control == treated:
        raise ValueError("대조구와 신기술 처리구가 같습니다.")
    area = float(area_a)
    if not np.isfinite(area) or area <= 0:
        raise ValueError("자료 기준면적은 0보다 커야 합니다.")
    price = float(price)
    if not np.isfinite(price) or price < 0:
        raise ValueError("단가는 0 이상이어야 합니다.")
    need = [trt_col, qty_col] + cost_cols + hour_cols
    missing = [c for c in need if c not in data.columns]
    if missing:
        raise ValueError("자료에 없는 열: " + ", ".join(map(str, missing)))
    d = data[list(dict.fromkeys(need))].copy()
    d[trt_col] = d[trt_col].astype(str).str.strip()
    for c in [qty_col] + cost_cols + hour_cols:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=[qty_col])
    got = set(d[trt_col])
    for g in (control, treated):
        if str(g) not in got:
            raise ValueError(f"'{g}' 처리구가 자료에 없습니다.")
    m = d.groupby(trt_col).mean(numeric_only=True)
    factor = 10.0 / area

    loss, gain, detail = [], [], []

    def _row(name, basis, amount):
        return {"항목": name, "산출근거": basis, "금액(원)": float(round(amount))}

    q_c = float(m.loc[str(control), qty_col]) * factor
    q_t = float(m.loc[str(treated), qty_col]) * factor
    dq = q_t - q_c
    detail.append({"구분": "수량(10a)", "대조구": round(q_c, 1), "신기술구": round(q_t, 1),
                   "차이": round(dq, 1)})
    if abs(dq) > 1e-9 and price > 0:
        # 산출근거에 적힌 숫자와 금액이 정확히 맞아떨어져야 검산기를 통과한다
        dq_r, price_r = round(abs(dq), 1), round(price)
        basis = f"{price_r:,.0f} * {dq_r:,.1f}"
        if dq > 0:
            gain.append(_row("판매수익 증가", basis, dq_r * price_r))
        else:
            loss.append(_row("판매수익 감소(수량 감소)", basis, dq_r * price_r))

    for c in cost_cols:
        if c not in m.columns or pd.isna(m.loc[str(control), c]) or pd.isna(m.loc[str(treated), c]):
            continue
        c_c = round(float(m.loc[str(control), c]) * factor)
        c_t = round(float(m.loc[str(treated), c]) * factor)
        dc = c_t - c_c
        detail.append({"구분": f"{c}(10a)", "대조구": c_c, "신기술구": c_t, "차이": dc})
        if dc == 0:
            continue
        basis = f"{max(c_t, c_c):,.0f} - {min(c_t, c_c):,.0f}"
        if dc > 0:
            loss.append(_row(f"{c} 증가", basis, dc))
        else:
            gain.append(_row(f"{c} 절감", basis, abs(dc)))

    # 노동시간 열: 시간 차이 × 시간당 노임 → 금액
    for c in hour_cols:
        if c not in m.columns or pd.isna(m.loc[str(control), c]) or pd.isna(m.loc[str(treated), c]):
            continue
        h_c = round(float(m.loc[str(control), c]) * factor, 1)
        h_t = round(float(m.loc[str(treated), c]) * factor, 1)
        dh = round(h_t - h_c, 1)
        detail.append({"구분": f"{c}(10a, 시간)", "대조구": h_c, "신기술구": h_t, "차이": dh})
        if abs(dh) < 1e-9:
            continue
        w = round(wage)
        basis = f"{w:,.0f} * {abs(dh):,.1f}"
        amt = w * abs(dh)
        label = f"{abs(dh):g}시간"   # 표 칸이 좁으므로 짧게
        if dh > 0:
            loss.append(_row(f"자가노동비 증가({label})", basis, amt))
        else:
            gain.append(_row(f"자가노동비 절감({label})", basis, amt))

    cols = ["항목", "산출근거", "금액(원)"]
    empty = pd.DataFrame({"항목": [""], "산출근거": [""], "금액(원)": [None]})
    loss_df = pd.DataFrame(loss, columns=cols) if loss else empty.copy()
    gain_df = pd.DataFrame(gain, columns=cols) if gain else empty.copy()
    return loss_df, gain_df, pd.DataFrame(detail)


def money_table(df, dec_overrides=None):
    """경제성 표를 보고서·다운로드용으로 정리한다: 숫자 열을 반올림하고
    천 단위 콤마를 넣은 문자열로 바꾼다 (예: 3750000.333... → '3,750,000').

    소수 자릿수는 열 이름으로 추정한다:
    - '(%)'로 끝나면 1자리 (예: 소득률(%))
    - 'B/C'는 2자리
    - '손익분기수량'처럼 '수량'이 들어간 열은 1자리
    - 그 밖의 숫자 열(원 단위 금액)은 0자리
    dec_overrides={"열이름": 자릿수} 로 개별 지정할 수 있다.
    """
    out = df.copy()
    dec_overrides = dec_overrides or {}
    for c in out.columns:
        if not pd.api.types.is_numeric_dtype(out[c]):
            continue
        name = str(c)
        if name in dec_overrides:
            dec = dec_overrides[name]
        elif name.endswith("(%)"):
            dec = 1
        elif name in ("B/C", "단년도 총수입/생산비", "할인 B/C"):
            dec = 2
        elif "수량" in name:
            dec = 1
        else:
            dec = 0
        out[c] = out[c].map(
            lambda v, dec=dec: "-" if pd.isna(v) else f"{round_half_up(v, dec):,.{dec}f}")
    return out


def log_action(what):
    import datetime
    st.session_state.setdefault("log", []).append(
        {"시각": datetime.datetime.now().strftime("%H:%M:%S"), "작업": what})
    _record_usage(what)

def render_ai_connection_settings():
    """AI 공급사/API 설정은 V1에서 AI 도우미 화면 안에서만 노출한다."""
    with st.expander("🔌 AI 연결 설정", expanded=not bool(st.session_state.get("api_key"))):
        st.caption("여기는 **설정 칸**입니다. 키를 넣으면 각 분석 결과 아래에 "
                   "**🤖 AI 해석** 버튼이 생기고, 오른쪽 아래 **💬 AI에게 물어보기**도 함께 사용할 수 있어요. "
                   "키가 없어도 다른 기능은 모두 정상 작동합니다.")
        st.caption("📤 AI 기능(해석·질문·사진/스캔 PDF 인식·음성 인식)을 쓰면 해당 표·글·그림·음성이 "
                   "선택한 AI 회사 서버(해외)로 전송됩니다. 미공개 자료는 기관 보안 지침을 확인해 주세요.")
        provider = st.selectbox("AI 제공사", list(_AI_PROVIDERS.keys()), key="ai_provider")
        st.caption(f"🔑 {_AI_PROVIDERS[provider]['key_hint']}")
        st.text_input(f"{provider.split()[0]} API 키", type="password", key="api_key")
        _ai_remember_widget()
        _models = list(_AI_PROVIDERS[provider]["models"])
        if st.session_state.get("api_key"):
            if provider.startswith("Gemini"):
                _list_fn, _live_key, _btn_label = (
                    list_gemini_models, "gemini_models_live", "🔄 사용 가능한 Gemini 모델 조회")
            elif provider.startswith("ChatGPT"):
                _list_fn, _live_key, _btn_label = (
                    list_openai_models, "openai_models_live", "🔄 사용 가능한 OpenAI 모델 조회")
            else:
                _list_fn, _live_key, _btn_label = (
                    list_claude_models, "claude_models_live", "🔄 사용 가능한 Claude 모델 조회")
            if st.button(_btn_label, width="stretch", key=f"list_models_{_live_key}"):
                with st.spinner("제공사에서 모델 목록을 확인하는 중..."):
                    _live_models, _live_err = _list_fn(st.session_state.get("api_key"))
                if _live_err:
                    st.warning(_live_err)
                elif _live_models:
                    st.session_state[_live_key] = _live_models
                    st.success(f"사용 가능한 모델 {len(_live_models)}개를 확인했습니다.")
                else:
                    st.warning("사용 가능한 텍스트 모델을 찾지 못했습니다. 직접 입력을 이용해 주세요.")
            if st.session_state.get(_live_key):
                _models = list(st.session_state[_live_key])

        _labels = {}
        if len(_models) >= 1:
            _labels[_models[0]] = f"{_models[0]} (저렴·빠름)"
        if len(_models) >= 2:
            _labels[_models[1]] = f"{_models[1]} (정교함)"
        _opts = list(_models) + ["✏️ 직접 입력"]
        if not _models:
            st.caption("설정된 모델 목록이 없습니다. 모델명을 직접 입력해 주세요.")
            _sel = st.text_input("모델명 직접 입력", value="",
                                 placeholder="예) claude-sonnet-5")
        else:
            _sel = st.selectbox("모델", _opts, format_func=lambda m: _labels.get(m, m))
            if _sel == "✏️ 직접 입력":
                _sel = st.text_input("모델명 직접 입력", value=_models[0],
                                     help="새 모델이 나왔을 때 여기에 이름을 넣으면 바로 쓸 수 있습니다.")
        st.session_state["ai_model_g"] = _sel
        ai_model = _sel
        if st.session_state.get("api_key"):
            st.success(f"✅ {provider.split()[0]} 활성화됨 — 분석 결과 아래 'AI 해석'을 눌러보세요.")
            if st.button("🔌 API 연결 테스트", width="stretch", key="ai_conn_test"):
                with st.spinner("연결을 확인하는 중..."):
                    _r = test_ai_connection(provider, st.session_state.get("api_key"), _sel)
                if _r["ok"]:
                    st.success(f"✅ {_r['provider']} / {_r['model']} 연결 성공")
                    if _r.get("sample"):
                        st.caption("응답 예시: " + _r["sample"][:60])
                else:
                    st.error(f"❌ {_r['provider']} / {_r['model']} — {_r['message']}")
        else:
            st.info("키를 넣으면 AI 해석이 켜집니다.")

if not _HAS_DOCX:
    st.sidebar.caption("💡 워드(docx) 저장을 쓰려면: pip install python-docx")

st.sidebar.markdown("---")
_ct_org, _, _ct_person = CONTACT_NAME.rpartition(" ")
st.sidebar.caption(f"📮 **문의**  \n{_ct_org or CONTACT_NAME}  \n"
                   + (f"{_ct_person} · " if _ct_org else "") + f"[{CONTACT_EMAIL}](mailto:{CONTACT_EMAIL})")
st.sidebar.caption("스마트 통계 에이전트 얏호(*/ω＼*)")

# ================================================================ 떠 있는 AI 도우미
_ATT_LIMIT = 12000          # 첨부 전체에서 AI 에게 넘길 글자 수 상한


def _read_attachment(f, budget=6000):
    """올린 파일을 AI 가 읽을 수 있는 **글자**로 바꾼다.

    ai_call() 은 글자만 주고받으므로(제공사가 여러 곳이라 그림 전송 방식이 제각각),
    표·문서는 내용을 뽑아 넘기고 그림은 넘길 수 없음을 분명히 알린다.
    """
    name = getattr(f, "name", "첨부파일")
    ext = ("." + name.rsplit(".", 1)[-1].lower()) if "." in name else ""
    try:
        raw = f.getvalue()
    except Exception:
        raw = f.read()
    head = f"\n\n===== 첨부: {name} ({len(raw):,} bytes) =====\n"

    try:
        if ext in (".csv", ".tsv", ".txt", ".md", ".json"):
            if ext in (".csv", ".tsv"):
                d = pd.read_csv(io.BytesIO(raw), sep=None, engine="python")
                return head + _df_digest(d, budget)
            for enc in ("utf-8", "cp949", "utf-8-sig"):
                try:
                    return head + raw.decode(enc)[:budget]
                except UnicodeDecodeError:
                    continue
            return head + raw.decode("utf-8", "replace")[:budget]

        if ext in (".xlsx", ".xls", ".xlsm"):
            xls = pd.ExcelFile(io.BytesIO(raw))
            per = max(600, budget // max(1, len(xls.sheet_names)))
            out = [head + f"(시트 {len(xls.sheet_names)}개: {', '.join(xls.sheet_names)})"]
            for sh in xls.sheet_names:
                out.append(f"\n--- 시트: {sh} ---\n"
                           + _df_digest(pd.read_excel(xls, sh), per))
            return "".join(out)

        if ext == ".pdf":
            from pypdf import PdfReader
            rd = PdfReader(io.BytesIO(raw))
            txt = []
            for pg in rd.pages[:30]:
                txt.append(pg.extract_text() or "")
                if sum(map(len, txt)) > budget:
                    break
            body = "\n".join(txt).strip()
            return head + (f"(총 {len(rd.pages)}쪽)\n" + body[:budget] if body
                           else "⚠️ 글자를 뽑을 수 없는 PDF입니다(스캔본일 수 있음).")

        if ext == ".docx":
            import docx as _dx
            d = _dx.Document(io.BytesIO(raw))
            parts = [p.text for p in d.paragraphs if p.text.strip()]
            for t in d.tables:
                for r in t.rows:
                    parts.append(" | ".join(c.text.strip() for c in r.cells))
            return head + "\n".join(parts)[:budget]

        if ext == ".hwpx":
            import zipfile
            from lxml import etree as _et
            parts = []
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                for n in sorted(x for x in z.namelist()
                                if x.startswith("Contents/section") and x.endswith(".xml")):
                    root = _et.fromstring(z.read(n))
                    parts += [t.text for t in root.iter() if t.tag.endswith("}t") and t.text]
            return head + ("\n".join(parts)[:budget] or "⚠️ 내용을 읽지 못했습니다.")

        if ext in (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"):
            return head + ("⚠️ 그림 파일은 아직 AI에게 전달할 수 없습니다. "
                           "그림 속 표는 엑셀·CSV로, 문서는 PDF로 올려 주세요.")

        if ext == ".hwp":
            return head + ("⚠️ 옛 한글(.hwp)은 읽을 수 없습니다. "
                           "한글에서 **다른 이름으로 저장 → hwpx 또는 PDF**로 바꿔 올려 주세요.")

        return head + f"⚠️ 지원하지 않는 형식입니다({ext or '확장자 없음'})."
    except Exception as e:
        return head + f"⚠️ 읽기 실패: {type(e).__name__}: {e}"


def _df_digest(d, budget):
    """표를 '크기 + 열 목록 + 앞부분 + 기술통계'로 요약한다(통째로 넘기면 너무 길다)."""
    lines = [f"크기: {len(d):,}행 × {len(d.columns)}열",
             f"열: {', '.join(map(str, d.columns))}", "", "[앞부분]",
             d.head(20).to_string(index=False)]
    try:
        num = d.select_dtypes(include=np.number)
        if len(num.columns):
            lines += ["", "[기술통계]", num.describe().round(2).to_string()]
    except Exception:
        pass
    return "\n".join(lines)[:budget]


def _ai_panel(df, menu_name):
    """AI 질문 상자 본체. 떠 있는 창과 사이드바가 같은 내용을 공유한다."""
    if not st.session_state.get("api_key"):
        st.caption("`🧠 AI 도우미 → AI 연결 설정`에서 API 키를 연결하면 사용할 수 있어요.")
        return
    st.caption(f"지금 화면: **{menu_name}**"
               + (f" · 데이터: **{st.session_state.get('cur_key')}**"
                  if df is not None else " · (데이터 없음)"))
    for role, txt in st.session_state.get("gai_hist", [])[-6:]:
        with st.chat_message("user" if role == "q" else "assistant"):
            st.markdown(txt)
    q = st.text_area("궁금한 점", key="gai_q", height=80, label_visibility="collapsed",
                     placeholder="예) 지금 이 표에서 어떤 처리가 가장 좋아? / 이 화면 어떻게 쓰는 거야?")
    ups = st.file_uploader(
        "📎 파일 첨부 (선택)", key="gai_files", accept_multiple_files=True,
        type=["csv", "tsv", "txt", "md", "json", "xlsx", "xls", "xlsm",
              "pdf", "docx", "hwpx"],
        help="엑셀·CSV·PDF·워드·한글(hwpx)의 내용을 읽어 함께 물어봅니다. "
             "그림 파일과 옛 한글(.hwp)은 아직 읽을 수 없어요.")
    if ups:
        st.caption("첨부: " + ", ".join(getattr(f, "name", "?") for f in ups))
    b1, b2 = st.columns([3, 1])
    if b1.button("물어보기", key="gai_send", type="primary", width="stretch") and q.strip():
        _prompt = None
        try:
            ctx = ""
            if df is not None:
                # build_group_profiles() 는 문자열이 아니라 dict 를 돌려준다.
                # 그대로 + 로 이으면 TypeError 가 나므로 f-string 으로 문자열화한다.
                _prof = build_group_profiles(df, question=q)
                ctx = (f"{build_data_overview(df)}\n\n[처리·품종별 요약]\n{_prof}")
            att = ""
            if ups:
                per = max(1500, _ATT_LIMIT // len(ups))
                att = "".join(_read_attachment(f, per) for f in ups)[:_ATT_LIMIT]
            _prompt = (
                    "당신은 농업연구사를 돕는 통계 전문가이자 이 앱의 사용 안내자입니다. "
                    f"사용자는 지금 '{menu_name}' 화면을 보고 있습니다. "
                    "아래 실제 데이터 요약만 근거로 한국어로 쉽고 정확하게 답하세요. "
                    "입력에 없는 수치나 유의성은 추측하지 마세요. "
                    "앱 사용법을 묻는다면 화면 이름을 들어 안내하세요.\n\n"
                    + (ctx or "(현재 선택된 데이터가 없습니다.)")
                    + (f"\n\n[사용자가 올린 파일]{att}" if att else "")
                    + f"\n\n질문: {q}")
        except Exception as _ex:
            st.session_state["gai_hist"] = (st.session_state.get("gai_hist", [])
                                            + [("q", q), ("a", f"⚠️ 질문 준비 실패: {type(_ex).__name__}: {_ex}")])[-12:]
        if _prompt:
            _qlog = q + (("\n\n📎 " + ", ".join(getattr(f, "name", "?") for f in ups))
                         if ups else "")
            # 질문을 먼저 등록해 두면, 이 실행이 중간에 끊겨도 다음 실행에서 이어서 답을 받는다.
            st.session_state["gai_pending"] = {"prompt": _prompt, "qlog": _qlog}
    _pend = st.session_state.get("gai_pending")
    if _pend:
        with st.spinner("AI가 생각하는 중..."):
            try:
                ans = ai_call(_pend["prompt"], max_tokens=900)
            except Exception as _ex:
                ans = f"⚠️ AI 호출 실패: {type(_ex).__name__}: {_ex}"
            if not str(ans or "").strip():
                ans = "⚠️ AI 응답이 비어 있습니다. 다시 시도해 주세요."
            st.session_state["gai_hist"] = (st.session_state.get("gai_hist", [])
                                            + [("q", _pend["qlog"]), ("a", ans)])[-12:]
            st.session_state["gai_pending"] = None
        st.rerun()
    if b2.button("지우기", key="gai_clear", width="stretch"):
        st.session_state["gai_hist"] = []
        st.rerun()
    st.caption("⚠️ AI 답변은 초안입니다. 수치와 해석은 연구자가 확인해 주세요.")


def _dock_supported():
    """오른쪽 아래에 띄우려면 st.container(key=...) 가 필요하다(스트림릿 1.48 이상).

    옛 버전에서는 TypeError 가 나므로 미리 확인해서 사이드바로 대신 내보낸다.
    (예전에는 이 실패를 그냥 삼켜서 버튼이 아무 데도 안 보였다.)
    """
    try:
        import inspect as _isp
        return ("key" in _isp.signature(st.container).parameters
                and hasattr(st, "popover") and hasattr(st, "chat_message"))
    except Exception:
        return False


def floating_ai(df, menu_name):
    """어느 화면에서든 쓸 수 있는 AI 질문 상자.

    기본은 오른쪽 아래에 떠 있는 버튼이고, 스트림릿 버전이 낮아 그렇게 만들 수
    없으면 **사이드바 맨 위**에 같은 상자를 대신 넣는다. 어느 쪽이든 사라지지 않는다.
    """
    if not _dock_supported():
        with st.sidebar:
            with st.expander("💬 AI에게 물어보기", expanded=False):
                _ai_panel(df, menu_name)
                st.caption("ℹ️ 스트림릿 1.48 이상이면 화면 오른쪽 아래에 떠 있는 창으로 "
                           "쓸 수 있어요. (`pip install -U streamlit`)")
        return

    st.markdown("""<style>
      div.st-key-gai_dock { position: fixed !important; right: 1.5rem; bottom: 1.5rem;
          z-index: 9999; width: auto !important; }
      div.st-key-gai_dock button { border-radius: 2.2rem !important;
          padding: .95rem 1.9rem !important; font-weight: 700 !important;
          font-size: 1.12rem !important; line-height: 1.25 !important;
          box-shadow: 0 6px 22px rgba(0,0,0,.30) !important; }
      div.st-key-gai_dock button:hover { transform: translateY(-2px); }
      div.st-key-gai_dock button p { font-size: 1.12rem !important;
          font-weight: 700 !important; margin: 0 !important; }
      @media (max-width: 640px) { div.st-key-gai_dock { right: .6rem; bottom: .6rem; }
          div.st-key-gai_dock button { padding: .8rem 1.4rem !important;
              font-size: 1rem !important; } }
    </style>""", unsafe_allow_html=True)
    with st.container(key="gai_dock"):
        with st.popover("💬 AI에게 물어보기"):
            st.markdown("###### 💬 AI 도우미")
            _ai_panel(df, menu_name)


df = st.session_state.df
if df is not None and len(df.columns) != len(set(map(str, df.columns))):
    df = clean_columns(df)
    st.session_state.df = df
    st.info("ℹ️ 열 이름이 중복되어 자동으로 구분했습니다(예: 값, 값_2). "
            "원본 엑셀의 머리글을 확인해 보세요.")

try:
    floating_ai(df, menu)
except Exception as _gex:
    # 조용히 사라지면 원인을 알 수 없다 — 사이드바에 최소한의 대체 창을 남긴다.
    try:
        with st.sidebar.expander("💬 AI에게 물어보기", expanded=False):
            st.caption(f"떠 있는 창을 만들지 못했습니다 ({type(_gex).__name__}). "
                       "여기서 이용해 주세요.")
            _ai_panel(df, menu)
    except Exception:
        pass


st.markdown("""
<div class="v1-hero" aria-label="스마트 통계 에이전트 Version 1">
  <div class="v1-hero-copy">
    <div class="v1-hero-title">스마트 통계 에이전트 <span>Version 1</span></div>
    <div class="v1-hero-sub">농업 데이터를 쉽고 빠르게, 통계 분석을 더 간단하게!</div>
  </div>
  <div class="v1-hero-mascot" aria-hidden="true"></div>
</div>
""", unsafe_allow_html=True)


# ================================================================ 홈 화면 (데이터를 불러오기 전)
_V1_HOME_CSS = """
<style>
.h-wrap {max-width:1080px; padding-bottom:4.5rem;}
.h-lead {font-size:1.55rem; font-weight:800; color:#17344B; margin:.2rem 0 .25rem 0; letter-spacing:-.02em;}
.h-sub {font-size:1rem; color:#5F6F66; margin-bottom:1.1rem;}
.h-steps {display:flex; gap:.6rem; align-items:stretch; margin-bottom:1.5rem; flex-wrap:wrap;}
.h-step {flex:1 1 0; min-width:170px; background:#FFFFFF; border:1px solid #D7EBDD; border-radius:14px;
         padding:.85rem 1rem; box-shadow:0 2px 8px rgba(47,190,98,.06);}
.h-step .n {display:inline-flex; width:26px; height:26px; border-radius:50%; background:#2FBE62; color:#fff;
            font-weight:800; font-size:.9rem; align-items:center; justify-content:center; margin-right:.45rem;}
.h-step .t {font-weight:800; color:#17344B; font-size:1.02rem;}
.h-step .d {color:#5F6F66; font-size:.88rem; margin-top:.35rem; line-height:1.45;}
.h-arrow {display:flex; align-items:center; color:#9CCBAA; font-size:1.3rem; font-weight:700;}
.h-sec {font-size:1.12rem; font-weight:800; color:#17344B; margin:.3rem 0 .7rem 0;}
.h-tag {display:inline-block; font-size:.7rem; font-weight:700; color:#2B8A4B; background:#E6F6EC;
        border-radius:6px; padding:.05rem .4rem; margin-left:.3rem; vertical-align:middle;}
.h-tag.gray {color:#6B7A72; background:#EEF2EF;}
.h-v2 {display:flex; align-items:center; gap:1rem; background:linear-gradient(90deg,#EEF5FC 0%,#F7FBFF 100%);
        border:1.5px solid #BCD6EE; border-radius:14px; padding:.95rem 1.2rem; margin-bottom:1.1rem;}
.h-v2 .i {font-size:1.9rem;}
.h-v2 .tt {font-weight:800; color:#1F4E79; font-size:1.08rem;}
.h-v2 .tt span {font-size:.72rem; font-weight:800; color:#fff; background:#3D6F9F; border-radius:999px; padding:.1rem .5rem; margin-left:.4rem; vertical-align:middle;}
.h-v2 .ds {color:#3F5A73; font-size:.9rem; margin-top:.25rem; line-height:1.45;}
.h-v2 .bt {margin-left:auto; white-space:nowrap; background:#3D6F9F; color:#fff !important; font-weight:800; font-size:.92rem;
           padding:.6rem 1.1rem; border-radius:10px; text-decoration:none !important;}
.h-tips {display:flex; gap:.6rem; flex-wrap:wrap;}
.h-tip {background:#F3FAF5; border:1px dashed #BFE3CB; border-radius:10px; padding:.55rem .8rem; font-size:.88rem; color:#24422F;}
/* B안: 표 */
.h-table {width:100%; border-collapse:separate; border-spacing:0; background:#fff; border:1px solid #E1EDE5;
          border-radius:14px; overflow:hidden; margin-bottom:1.2rem;}
.h-table th {background:#F3FAF5; color:#3F5247; font-weight:700; text-align:left; font-size:.88rem; padding:.6rem .9rem; border-bottom:1px solid #E1EDE5;}
.h-table td {padding:.62rem .9rem; border-bottom:1px solid #F0F4F1; font-size:.93rem; color:#24422F; vertical-align:top;}
.h-table tr:last-child td {border-bottom:none;}
.h-table td.m {font-weight:800; color:#17344B; white-space:nowrap;}
.h-table tr.grp td {background:#FBFDFB; color:#8A9A90; font-size:.78rem; font-weight:700; padding:.35rem .9rem;}
@media (max-width: 900px) {
  .h-arrow {display:none;} .h-v2 {flex-wrap:wrap;} .h-v2 .bt {margin-left:0;}
  .h-table td.m {white-space:normal;}
}
@media (max-width: 640px) {
  .h-table th:nth-child(3), .h-table td:nth-child(3) {display:none;}
}
</style>
"""

_V1_HOME_STEPS = """
<div class="h-steps">
  <div class="h-step"><span class="n">1</span><span class="t">데이터 준비</span>
    <div class="d">형식이 헷갈리면 왼쪽 <b>📘 데이터 작성 가이드</b>의 예시와 양식을 참고하세요.</div></div>
  <div class="h-arrow">›</div>
  <div class="h-step"><span class="n">2</span><span class="t">파일 올리기</span>
    <div class="d">왼쪽 <b>📂 데이터 불러오기</b>에 올리면 <b>자동으로 점검</b>해 드려요.</div></div>
  <div class="h-arrow">›</div>
  <div class="h-step"><span class="n">3</span><span class="t">분석 고르기</span>
    <div class="d">처음이라면 <b>⚡ 원클릭 분석</b> 한 번이면 충분해요.</div></div>
  <div class="h-arrow">›</div>
  <div class="h-step"><span class="n">4</span><span class="t">결과 저장</span>
    <div class="d">표·그래프·보고서 문장을 <b>한글·워드·엑셀</b>로 받아요.</div></div>
</div>
"""

_V1_HOME_TIPS = """
<div class="h-tips">
  <div class="h-tip">💡 처음이라면 <b>⚡ 원클릭 분석</b>부터 해 보세요</div>
  <div class="h-tip">📱 밭에서는 휴대폰으로 <b>말해서 입력</b>할 수 있어요 (주소 뒤에 <code>?mode=voice</code>)</div>
  <div class="h-tip">📖 자세한 방법은 <b>사용설명서</b>에 있어요</div>
</div>
"""




def render_v1_home():
    """처음 들어온 사람이 무엇을 해야 할지 바로 알 수 있는 홈 화면 (단계 안내 + 메뉴 한눈에 보기)."""
    import html as _html
    _picked = st.session_state.get("menu_choice")
    # 사용자가 메뉴를 직접 바꿨을 때만 안내한다(첫 화면의 기본 선택이나 화면 새로고침에는 띄우지 않는다).
    _prev = st.session_state.get("_home_menu")
    if _prev is not None and _picked != _prev:
        st.session_state["_home_hint"] = _picked
    st.session_state["_home_menu"] = _picked
    if (_picked in ("⚡ 원클릭 분석", "📊 통계분석", "📋 설문조사 분석")
            and st.session_state.get("_home_hint") == _picked):
        st.info(f"**{_picked}**을(를) 쓰려면 먼저 왼쪽 **📂 데이터 불러오기**에서 데이터를 올려 주세요.")
    v2_btn = (f'<a class="bt" href="{_html.escape(V2_APP_URL, quote=True)}" target="_blank" rel="noopener">Version 2 열기 ↗</a>'
              if V2_APP_URL else "")
    st.markdown(_V1_HOME_CSS + """
<div class="h-wrap">
<div class="h-lead">처음 오셨나요? 4단계면 끝나요 🌱</div>
<div class="h-sub">실험 데이터를 올리면 통계분석부터 그래프·보고서 문장까지 자동으로 만들어 드려요.</div>
""" + _V1_HOME_STEPS + """
<div class="h-sec">메뉴 한눈에 보기</div>
<table class="h-table">
  <tr><th style="width:190px">메뉴</th><th>이런 때 사용합니다</th><th style="width:330px">할 수 있는 것</th></tr>
  <tr class="grp"><td colspan="3">분석 시작</td></tr>
  <tr><td class="m">⚡ 원클릭 분석 <span class="h-tag">추천</span></td><td>처리구·반복이 정리된 실험자료를 버튼 하나로 분석</td><td>분산분석 · 사후검정(a,b,c) · 그래프 · 보고서</td></tr>
  <tr><td class="m">📊 통계분석</td><td>분석 방법을 직접 골라 자세히 볼 때</td><td>데이터 점검 · 분산분석 · 상관 · 회귀 · 머신러닝 예측</td></tr>
  <tr><td class="m">📋 설문조사 분석</td><td>농가·교육생 설문 결과를 정리할 때</td><td>만족도 · 객관식 · 다중응답 · 교차분석</td></tr>
  <tr class="grp"><td colspan="3">보조 기능</td></tr>
  <tr><td class="m">📑 보고서</td><td>담아 둔 표·그래프를 문서로 만들 때</td><td>한글(hwpx) · 워드(docx)</td></tr>
  <tr><td class="m">🧠 AI 도우미 <span class="h-tag gray">API 키</span></td><td>결과 해석·고찰 문장, 통계 질문</td><td>AI 해석 · 질문하기</td></tr>
  <tr><td class="m">📖 사용설명서</td><td>데이터 작성법과 사용법을 확인할 때</td><td>메뉴별 설명 · 자주 틀리는 예시</td></tr>
</table>
<div class="h-v2"><div class="i">🔬</div>
  <div><div class="tt">Version 2 전문형<span>고급</span></div>
  <div class="ds">경제성 분석(소득·부분예산·MRR) · 주성분분석(PCA) · 공분산분석(ANCOVA) · 프로빗(LC50) · 전처리·파생변수까지<br>더 깊은 분석이 필요하면 전문형을 이용하세요.</div></div>
  """ + v2_btn + """</div>
""" + _V1_HOME_TIPS + "</div>", unsafe_allow_html=True)

# ================================================================ 공통 가드
if df is None and menu not in ("📑 보고서", "📖 사용설명서", "🧠 AI 도우미"):
    render_v1_home()
    st.stop()

if df is not None:
    num_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(exclude=np.number).columns.tolist()
else:
    num_cols, cat_cols = [], []

# 새 데이터를 불러오면 어느 화면에 있든 점검 결과를 한 번 보여 준다.
# 같은 이름으로 고친 파일을 다시 올리면(내용이 바뀌면) 다시 보여 준다.
_ck_name = st.session_state.get("cur_key")
_ck_seen = st.session_state.setdefault("_checkup_seen", set())
_ck_sigs = st.session_state.setdefault("_checkup_seen_sig", {})
_ck_sig = _v1_upload_sig(_ck_name)
_ck_is_new = bool(_ck_name) and (_ck_name not in _ck_seen
                                 or (_ck_name in _ck_sigs and _ck_sigs[_ck_name] != _ck_sig))
_ck_on_check_tab = (menu == "📊 통계분석" and st.session_state.get("stat_sub", "📋 데이터 점검") == "📋 데이터 점검")
if df is not None and _ck_is_new and not _ck_on_check_tab:
    _ck_find = _v1_checkup_for(df)
    _ck_cnt = _v1_checkup_counts(_ck_find)
    if _ck_cnt["error"] or _ck_cnt["warn"]:
        with st.container(border=True):
            st.markdown(f"#### 📋 방금 불러온 '{_ck_name}' 데이터를 점검했어요")
            _v1_render_checkup(_ck_find, compact=True)
            st.caption("자세한 내용과 '숫자로 자동 변환'은 **📊 통계분석 → 📋 데이터 점검**에서 볼 수 있어요.")
            if st.button("확인했어요", key="checkup_ack"):
                _ck_seen.add(_ck_name)
                _ck_sigs[_ck_name] = _ck_sig
                st.rerun()
    else:
        _ck_seen.add(_ck_name)
        _ck_sigs[_ck_name] = _ck_sig
        st.toast(f"✅ '{_ck_name}' 데이터 점검 완료 — 바로 분석할 수 있어요.")

# ================================================================ 통계분석
# ================================================================ 원클릭 오토파일럿
if menu == "⚡ 원클릭 분석":
    st.title("⚡ 원클릭 분석")
    st.caption("데이터만 올리면 **데이터 점검 → 설계 인지 → 분석 → 그래프 → 문장 → 보고서**까지 "
               "한 번에 만들어 드립니다.")
    st.info("💡 결과물은 **초안**입니다. 연구 목적과 고찰은 연구자가 확인·보완해 주세요. "
            "세부 조정이 필요하면 '📊 통계분석' 메뉴에서 직접 분석할 수 있습니다.")

    if df is None:
        st.warning("먼저 왼쪽에서 데이터를 올려 주세요.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("행", f"{len(df):,}"); c2.metric("열", len(df.columns))
        c3.metric("숫자형 항목", len(df.select_dtypes(include=np.number).columns))
        _pre = detect_design(df)
        if _pre.get("trt"):
            st.caption(f"🔬 자동 인지: **{_pre['design']}** — 처리구 '{_pre['trt']}'"
                       + (f", 반복 '{_pre['blk']}'" if _pre.get("blk") else ", 반복 없음"))
        with st.expander("⚙️ 설정 (필요할 때만)"):
            _allc = df.columns.tolist()
            _bopts = ["(자동)"] + _allc
            # index= 와 key= 를 함께 쓰면 스트림릿이 경고를 띄우므로,
            # 기본값은 session_state에만 넣고 위젯은 key로만 만든다.
            if st.session_state.get("ap_trt") not in _allc:
                st.session_state["ap_trt"] = (_pre["trt"] if _pre.get("trt") in _allc
                                              else (_allc[0] if _allc else None))
            if st.session_state.get("ap_blk") not in _bopts:
                st.session_state["ap_blk"] = "(자동)"
            st.selectbox("처리구 열 (자동 인지 결과를 바꾸려면)", _allc, key="ap_trt")
            st.selectbox("반복(블록) 열", _bopts, key="ap_blk")
            ap_ph = st.selectbox("사후검정", ["Tukey HSD", "던컨(Duncan)", "Bonferroni"], key="ap_ph")
            ap_err = st.radio("오차막대", ["표준편차(SD)", "표준오차(SE)"], horizontal=True, key="ap_err",
                              help="SD=자료가 흩어진 정도, SE=평균의 정확도. 아래 설명을 참고하세요.")
            with st.expander("❓ 표준편차(SD)와 표준오차(SE), 뭐가 다른가요?"):
                st.markdown(EXPLAIN["sd_se"])

        _auto_items = list((_pre or {}).get("ys") or [])
        if len(_auto_items) > 8:
            st.markdown("**분석할 조사항목 선택**")
            st.caption(f"숫자형 조사항목이 {len(_auto_items)}개라 필요한 항목만 선택해 주세요. 기본으로 앞의 8개를 선택했습니다.")
            _auto_selected = st.multiselect("조사항목", _auto_items, default=_auto_items[:8], key="ap_items")
        else:
            _auto_selected = _auto_items

        if st.button("🚀 원클릭 분석 시작", type="primary", width="stretch"):
            _bsel = st.session_state.get("ap_blk", "(자동)")
            res = run_autopilot_engine(df, ph=st.session_state.get("ap_ph", "Tukey HSD"),
                                       err_type=st.session_state.get("ap_err"),
                                       max_items=None, selected_items=_auto_selected,
                                       trt_override=st.session_state.get("ap_trt"),
                                       blk_override=(None if _bsel == "(자동)" else _bsel))
            st.session_state["autopilot"] = res
            if res.get("ok"):
                st.markdown(
                    "<div style='text-align:center;font-size:2.1rem;letter-spacing:.35rem;"
                    "padding:.5rem 0'>🌱 🌾 🌶️ 🍃 🌾 🌱</div>"
                    "<div style='text-align:center;color:#4b7d3a;font-weight:600;"
                    "padding-bottom:.6rem'>분석이 잘 마무리되었습니다</div>",
                    unsafe_allow_html=True)
                log_action(f"원클릭 분석 생성({len(res['summary'])}개 항목)")

        ap = st.session_state.get("autopilot")
        if ap and not ap.get("ok"):
            for m in ap.get("msgs", []): st.warning(m)
        elif ap and ap.get("ok"):
            st.success(f"✅ 완료! {len(ap['summary'])}개 항목을 분석해 보고서를 만들었습니다.")
            d1, d2 = st.columns(2)
            if ap.get("hwpx"):
                d1.download_button("📘 보고서 내려받기 — 한글(hwpx)", ap["hwpx"],
                                   "통계분석_초안.hwpx", type="primary", width="stretch")
            if ap.get("docx"):
                d2.download_button("📝 보고서 내려받기 — 워드(docx)", ap["docx"],
                                   "통계분석_초안.docx", type="primary", width="stretch")
            elif not _HAS_DOCX:
                d2.caption("워드 저장: pip install python-docx 후 사용 가능")
            try:
                _xl = make_xlsx_multi(
                    [{"caption": "분석 종합", "table": ap["summary"]}]
                    + [b for b in ap["blocks"] if b.get("table") is not None],
                    "원클릭 분석 결과")
                if _xl:
                    st.download_button("📈 엑셀(xlsx) — 스마트 블루 항목별 시트 + 편집 가능한 그래프",
                                       _xl, "통계분석_초안.xlsx", width="stretch",
                                       key="xls_autopilot",
                                       help="조사항목마다 시트가 하나씩 만들어지고, 각 시트에 "
                                            "엑셀 기본 차트가 들어갑니다. 막대 색·글꼴·축 범위·"
                                            "차트 종류를 원하는 대로 바꿀 수 있습니다.")
            except Exception as _e:
                st.caption(f"엑셀 파일 생성 실패 ({type(_e).__name__})")
            if st.button("➕ 이 결과를 '📑 보고서'에도 담기", width="stretch"):
                st.session_state.report_items.extend(ap["report_items"])
                st.success("보고서 메뉴에 담았습니다! 다른 분석과 합쳐서 편집할 수 있어요.")

            st.markdown("---")
            for m in ap.get("msgs", []): st.caption("• " + m)

            st.markdown("### 📋 분석 종합")
            smart_table(ap["summary"], width="stretch", hide_index=True)

            st.markdown("### 📄 적요(초안)")
            st.code(ap["abstract"], language=None)

            st.markdown("### 📈 항목별 결과")
            _tables = [b for b in ap["blocks"] if b.get("table") is not None]
            _texts = [b for b in ap["blocks"] if b.get("text")]
            for i, blk in enumerate(_tables):
                with st.expander(f"{blk['caption']}", expanded=(i == 0)):
                    if i < len(_texts):
                        st.code(_texts[i]["text"], language=None)
                    smart_table(sup_display(blk["table"]), width="stretch", hide_index=True)
                    if blk.get("image"):
                        st.image(blk["image"], width=640)

            st.markdown("### 🧾 통계 처리 문구")
            st.caption("보고서 '재료 및 방법 — 통계처리'에 그대로 붙여 쓸 수 있어요. 오른쪽 위 📋 버튼으로 복사하세요.")
            st.code(str(ap["stat_line"]).replace(". ", ".\n"), language=None, wrap_lines=True)

elif menu == "📊 통계분석":
    # 기본 선택값 정리: 반복·처리 코드(1,2,3)나 개체번호가 '측정값' 기본값으로 잡히지 않게
    # 실제 측정값을 앞으로 보내고, 숫자로 적힌 반복·처리 코드는 그룹 목록에서도 고를 수 있게 한다.
    _ys_all, _cats_all, _promoted_all = split_code_columns(df)
    _id_like = _v1_id_like_cols(df)
    _measure_cols = [c for c in num_cols if c not in _promoted_all and c not in _id_like]
    num_cols = _measure_cols + [c for c in num_cols if c not in _measure_cols]
    cat_cols = cat_cols + [c for c in _promoted_all if c not in cat_cols]
    _measure_default = _measure_cols if len(_measure_cols) >= 2 else num_cols
    st.title("실험 데이터 자동 통계 분석")
    st.markdown("### 분석 방법 추천")
    st.caption("현재 데이터 구조를 바탕으로 가능한 분석을 안내합니다. 아래 문장은 버튼이 아니라 안내문입니다.")
    for rec in recommend_analysis(df):
        st.markdown(f"- {rec}")
    st.divider()

    _SUB = ["📋 데이터 점검", "🌱 분산분석 (처리 간 차이)", "🔗 상관분석 (변수 간 관계)",
            "📈 회귀분석 (영향 요인)", "🤖 머신러닝 예측"]
    if st.session_state.get("stat_sub") not in _SUB:
        st.session_state["stat_sub"] = _SUB[0]
    sub = st.radio("분석 선택", _SUB, horizontal=True, key="stat_sub",
                   label_visibility="collapsed")
    st.markdown("---")

    class _Show:
        """선택된 화면만 그리도록 (숨은 화면은 계산하지 않아 훨씬 빠릅니다)"""
        def __init__(self, name): self.on = (sub == name)
        def __enter__(self): return self
        def __exit__(self, *a): return False
    
    tab_data = _Show("📋 데이터 점검"); tab_prep = _Show("__V2_전처리__")
    tab_derive = _Show("__V2_파생변수__"); tab_corr = _Show("🔗 상관분석 (변수 간 관계)")
    tab_anova = _Show("🌱 분산분석 (처리 간 차이)"); tab_np = _Show("__V2_비모수__")
    tab_pca = _Show("__V2_PCA__"); tab_reg = _Show("📈 회귀분석 (영향 요인)")
    tab_ml = _Show("🤖 머신러닝 예측")

    if tab_data.on:
        st.subheader("데이터 점검")
        st.caption("올린 자료에 문제가 없는지 먼저 확인합니다. 📍 위치와 🔧 고치는 법을 함께 알려 드려요.")
        _v1_render_checkup(_v1_checkup_for(df))
        if st.session_state.get("cur_key"):
            _ckn = st.session_state["cur_key"]
            st.session_state.setdefault("_checkup_seen", set()).add(_ckn)
            st.session_state.setdefault("_checkup_seen_sig", {})[_ckn] = _v1_upload_sig(_ckn)
        numlike = _v1_numeric_like(df)
        # 실험설계 추정 (숫자로 적힌 반복·처리 코드도 함께 인식)
        _ys_c, catc, _promoted_c = split_code_columns(df)
        design_msg = None
        for cand in catc:
            if any(k in str(cand).lower() for k in _BLOCK_KEYS):
                other = [c for c in catc if c != cand]
                if other:
                    tab = df.groupby([other[0], cand]).size()
                    balanced = tab.nunique() == 1
                    design_msg = (f"'{other[0]}' × '{cand}' 구조가 감지되었습니다 → "
                                  + ("**난괴법(RCBD)**으로 보입니다. 분산분석에서 반복(블록) 열로 "
                                     f"'{cand}'을 꼭 지정하세요." if balanced
                                     else "반복 수가 고르지 않습니다(불균형). 결측을 확인하세요."))
                break
        if design_msg:
            st.success("🔬 " + design_msg)
        if numlike:
            st.markdown("###### 🔧 숫자로 자동 변환")
            fixcols = st.multiselect("변환할 열", list(numlike.keys()),
                                     default=list(numlike.keys()), key="fixnum")
            st.caption("쉼표(1,200)·단위(120kg)·공백이 섞인 값에서 숫자만 뽑아냅니다. "
                       "변환할 수 없는 값은 결측치가 됩니다.")
            if fixcols and st.button("숫자로 변환하기"):
                d2 = df.copy()
                report = []
                for c in fixcols:
                    conv = to_numeric_clean(d2[c])
                    report.append({"열": c, "변환 성공": int(conv.notna().sum()),
                                   "변환 실패(결측)": int(conv.isna().sum() - d2[c].isna().sum())})
                    d2[c] = conv
                set_df(d2, "숫자 변환")
                smart_table(pd.DataFrame(report), width="stretch")
                log_action(f"숫자 변환: {', '.join(fixcols)}")
                st.success("변환했습니다!"); st.rerun()

        st.markdown("#### 데이터 미리보기")
        smart_table(df, width="stretch")
        c1, c2, c3 = st.columns(3)
        c1.metric("행 개수", df.shape[0]); c2.metric("열 개수", df.shape[1])
        c3.metric("결측치 개수", int(df.isna().sum().sum()))
        if len(df) > 20000:
            st.warning(f"⚠️ 행이 {len(df):,}개로 많습니다. 분석·그래프가 느려질 수 있어요. "
                       "필요한 기간·처리만 걸러서 사용하시길 권장합니다.")

        st.write("**기술통계**"); smart_table(df.describe(), width="stretch")

    # ---------- 전처리 ----------
    if tab_prep.on:
        st.subheader("데이터 전처리")
        with st.expander("ℹ️ 전처리가 뭔가요?"):
            st.markdown(EXPLAIN["prep"])
        st.markdown("###### 📋 현재 데이터 (작업 결과가 즉시 반영됩니다)")
        pc1, pc2, pc3 = st.columns(3)
        pc1.metric("행", f"{len(df):,}"); pc2.metric("열", len(df.columns))
        pc3.metric("결측치", f"{int(df.isna().sum().sum()):,}")
        smart_table(df.head(20), width="stretch")
        st.caption(f"열 목록: {', '.join(map(str, df.columns))}")
        _stack = st.session_state.get("undo_stack", [])
        u1, u2 = st.columns([1, 3])
        if u1.button(f"↩️ 실행취소 ({len(_stack)})", width="stretch",
                     disabled=not _stack, help="바로 전 전처리 작업을 되돌립니다."):
            memo = undo_df()
            log_action(f"실행취소: {memo}")
            st.success(f"'{memo}' 작업을 되돌렸습니다."); st.rerun()
        if _stack:
            u2.caption(f"되돌릴 수 있는 작업: {' → '.join(h['memo'] for h in _stack[-3:])}"
                       + (" (최근 3개)" if len(_stack) > 3 else ""))
        else:
            u2.caption("전처리를 실행하면 되돌리기가 활성화됩니다. (최근 10단계까지)")
        pmode = st.radio("작업 선택",
                         ["결측치 처리", "이상값 처리", "중복 행 제거", "자료형 변환", "열 삭제/이름변경", "표준화·정규화"])

        if pmode == "결측치 처리":
            miss = df[df.isna().any(axis=1)]
            if len(miss) == 0:
                st.success("결측치가 없습니다.")
            else:
                st.warning(f"결측치가 있는 행: 총 {len(miss)}개")
                smart_table(miss.style.highlight_null(color="#FFF3B0"), width="stretch")
                st.caption(f"행 번호: {list(miss.index)}")
            m = st.radio("처리 방법", ["행 삭제", "평균 대체", "중앙값 대체", "0으로 대체"], horizontal=True)
            if st.button("적용", key="p_miss"):
                d = st.session_state.df.copy(); aff = list(miss.index)
                if m == "행 삭제": d = d.dropna()
                elif m == "평균 대체":
                    for c in d.select_dtypes(include=np.number).columns: d[c] = d[c].fillna(d[c].mean())
                elif m == "중앙값 대체":
                    for c in d.select_dtypes(include=np.number).columns: d[c] = d[c].fillna(d[c].median())
                else: d = d.fillna(0)
                set_df(d, "전처리")
                st.success(f"{len(aff)}개 행 처리 완료. 처리된 행 번호: {aff}")
                smart_table(d, width="stretch")

        elif pmode == "이상값 처리":
            with st.expander("ℹ️ 이상값이 뭔가요?"):
                st.markdown(EXPLAIN["outlier"])
            if not num_cols:
                st.warning("숫자형 변수가 필요합니다.")
            else:
                c1, c2 = st.columns(2)
                ocols = c1.multiselect("검사할 열", num_cols, default=num_cols)
                omethod = c2.radio("탐지 방법", ["IQR (1.5배)", "Z-점수 (±3)"])
                if ocols:
                    mask = pd.Series(False, index=df.index)
                    info = []
                    for c in ocols:
                        s = df[c]
                        if omethod.startswith("IQR"):
                            q1, q3 = s.quantile(.25), s.quantile(.75); iqr = q3 - q1
                            lo, hi = q1 - 1.5*iqr, q3 + 1.5*iqr
                        else:
                            mu, sd = s.mean(), s.std()
                            lo, hi = mu - 3*sd, mu + 3*sd
                        m_ = (s < lo) | (s > hi)
                        mask |= m_.fillna(False)
                        info.append({"변수": c, "하한": round(lo, 2), "상한": round(hi, 2), "이상값 수": int(m_.sum())})
                    smart_table(pd.DataFrame(info), width="stretch")
                    out_rows = df[mask]
                    if len(out_rows) == 0:
                        st.success("이상값이 없습니다.")
                    else:
                        st.warning(f"이상값이 포함된 행: {len(out_rows)}개 (행 번호: {list(out_rows.index)})")
                        smart_table(out_rows, width="stretch")
                    fig, ax = plt.subplots(figsize=(min(12, 1.5*len(ocols)+2), 4))
                    df[ocols].plot(kind="box", ax=ax); ax.set_title("상자그림(이상값 확인)")
                    plt.xticks(rotation=30); show_plot(fig); plt.close(fig)
                    act = st.radio("처리 방법", ["해당 행 삭제", "경계값으로 대체(윈저화)", "결측치로 변경"], horizontal=True)
                    if st.button("적용", key="p_out"):
                        d = st.session_state.df.copy()
                        if act == "해당 행 삭제":
                            d = d[~mask]
                        else:
                            for c in ocols:
                                s = d[c]
                                if omethod.startswith("IQR"):
                                    q1, q3 = s.quantile(.25), s.quantile(.75); iqr = q3-q1
                                    lo, hi = q1-1.5*iqr, q3+1.5*iqr
                                else:
                                    mu, sd = s.mean(), s.std(); lo, hi = mu-3*sd, mu+3*sd
                                if act.startswith("경계값"): d[c] = s.clip(lo, hi)
                                else: d[c] = s.where((s >= lo) & (s <= hi))
                        set_df(d, "전처리")
                        st.success(f"이상값 처리 완료. (영향 행: {list(out_rows.index)})")
                        smart_table(d, width="stretch")

        elif pmode == "중복 행 제거":
            dup = df[df.duplicated(keep=False)]
            st.write(f"중복 행: {len(dup)}개")
            if len(dup): smart_table(dup, width="stretch")
            if st.button("중복 제거", key="p_dup"):
                set_df(st.session_state.df.drop_duplicates().reset_index(drop=True), "중복 제거")
                st.success("중복 행을 제거했습니다."); smart_table(st.session_state.df, width="stretch")

        elif pmode == "자료형 변환":
            c1, c2 = st.columns(2)
            col = c1.selectbox("열 선택", df.columns.tolist(), key="t_col")
            to = c2.radio("변환", ["숫자형으로", "문자형으로"], horizontal=True)
            st.caption(f"현재 자료형: {df[col].dtype}")
            if st.button("변환", key="p_type"):
                d = st.session_state.df.copy()
                if to == "숫자형으로":
                    d[col] = pd.to_numeric(d[col].astype(str).str.replace(",", "").str.strip(), errors="coerce")
                    st.info(f"변환 실패(결측 처리)된 값: {int(d[col].isna().sum() - df[col].isna().sum())}개")
                else:
                    d[col] = d[col].astype(str)
                set_df(d, "자료형 변환"); st.success("변환 완료"); smart_table(d.head(), width="stretch")

        elif pmode == "열 삭제/이름변경":
            c1, c2 = st.columns(2)
            with c1:
                drops = st.multiselect("삭제할 열", df.columns.tolist())
                if drops and st.button("열 삭제", key="p_drop"):
                    set_df(st.session_state.df.drop(columns=drops), "열 삭제")
                    st.success(f"{len(drops)}개 열 삭제"); st.rerun()
            with c2:
                oldc = st.selectbox("이름 바꿀 열", df.columns.tolist(), key="rn")
                newc = st.text_input("새 이름", value=str(oldc))
                if st.button("이름 변경", key="p_rn"):
                    st.session_state.df = st.session_state.df.rename(columns={oldc: newc})
                    st.success("변경 완료"); st.rerun()

        else:  # 표준화·정규화
            sc = st.multiselect("변환할 열", num_cols, default=num_cols, key="sc")
            how = st.radio("방법", ["표준화(Z-점수)", "정규화(0~1)"], horizontal=True)
            st.caption("단위가 다른 변수들을 비교하거나 머신러닝에 넣을 때 사용합니다. 새 열로 추가됩니다.")
            if sc and st.button("적용", key="p_sc"):
                d = st.session_state.df.copy()
                arr = (StandardScaler() if how.startswith("표준화") else MinMaxScaler()).fit_transform(d[sc])
                suffix = "_표준화" if how.startswith("표준화") else "_정규화"
                for i, c in enumerate(sc): d[c + suffix] = arr[:, i].round(4)
                st.session_state.df = d; st.success("완료"); smart_table(d.head(), width="stretch")

    # ---------- 파생변수 ----------
    if tab_derive.on:
        st.subheader("파생변수 생성")
        with st.expander("ℹ️ 이 기능이 뭔가요?"): st.markdown(EXPLAIN["derive"])
        st.markdown("###### 📋 현재 데이터 (새 열이 추가되면 바로 보입니다)")
        dc1, dc2 = st.columns(2)
        dc1.metric("행", f"{len(df):,}"); dc2.metric("열", len(df.columns))
        smart_table(df.head(20), width="stretch")
        st.caption(f"열 목록: {', '.join(map(str, df.columns))}")
        kind = st.radio("만들 방식", ["두 열 사칙연산", "조건 열 (예: 기온≥33)", "그룹별 집계"])
        if kind == "두 열 사칙연산":
            if not num_cols: st.warning("숫자형 변수가 필요합니다.")
            else:
                c1, c2, c3 = st.columns(3)
                a = c1.selectbox("열 A", num_cols, key="d_a")
                op = c2.selectbox("연산", ["+", "-", "×", "÷"], key="d_op")
                b = c3.selectbox("열 B", num_cols, key="d_b")
                nm = st.text_input("새 열 이름", value=f"{a}_{op}_{b}")
                if st.button("새 열 만들기"):
                    d = st.session_state.df.copy()
                    d[nm] = {"+": d[a]+d[b], "-": d[a]-d[b], "×": d[a]*d[b],
                             "÷": d[a]/d[b].replace(0, np.nan)}[op]
                    st.session_state.df = d; st.success(f"'{nm}' 생성"); smart_table(d.head(), width="stretch")
        elif kind.startswith("조건"):
            if not num_cols: st.warning("숫자형 변수가 필요합니다.")
            else:
                c1, c2, c3 = st.columns(3)
                col = c1.selectbox("기준 열", num_cols, key="d_col")
                cond = c2.selectbox("조건", ["≥", ">", "≤", "<", "="], key="d_cond")
                thr = c3.number_input("임계값", value=float(round(df[col].mean(), 1)))
                nm = st.text_input("새 열 이름", value=f"{col}_{cond}{thr}")
                st.caption("조건 만족 시 1, 아니면 0. 이후 '그룹별 집계 → 합계'로 '해당일 수'를 구할 수 있어요.")
                if st.button("조건 열 만들기"):
                    d = st.session_state.df.copy(); s = d[col]
                    flag = {"≥": s >= thr, ">": s > thr, "≤": s <= thr, "<": s < thr, "=": s == thr}[cond]
                    d[nm] = flag.astype(int); st.session_state.df = d
                    st.success(f"'{nm}' 생성 (1의 개수: {int(d[nm].sum())})"); smart_table(d.head(), width="stretch")
        else:
            if not num_cols: st.warning("숫자형 값 열이 필요합니다.")
            else:
                c1, c2, c3 = st.columns(3)
                g = c1.selectbox("그룹 열 (예: 연도)", df.columns.tolist(), key="agg_g")
                v = c2.selectbox("값 열", num_cols, key="agg_v")
                f = c3.selectbox("집계", ["합계", "평균", "최대", "최소", "개수"], key="agg_f")
                if keep_running("agg", "집계표 만들기"):
                    fmap = {"합계": "sum", "평균": "mean", "최대": "max", "최소": "min", "개수": "count"}
                    agg = df.groupby(g)[v].agg(fmap[f]).round(3).reset_index()
                    agg.columns = [g, f"{v}_{f}"]
                    smart_table(agg, width="stretch")
                    dl_table(agg, f"{g}별 {v} {f}", "aggregate1", "aggregate")
                    st.session_state.files[f"집계_{g}_{v}_{f}"] = agg
                    st.info("사이드바 '분석할 데이터 선택'에서 이 집계표를 고를 수 있어요.")

    # ---------- 상관 ----------
    if tab_corr.on:
        st.subheader("상관분석 & 히트맵")
        with st.expander("ℹ️ 이 분석이 뭔가요?"): st.markdown(EXPLAIN["corr"])
        if len(num_cols) < 2: st.warning("숫자형 변수가 2개 이상 필요합니다.")
        else:
            c1, c2 = st.columns([3, 1])
            sel = c1.multiselect("분석할 변수 선택", num_cols, default=_measure_default,
                                 help="개체번호·반복 같은 번호 열은 기본 선택에서 뺐습니다. 필요하면 추가하세요.")
            cmethod = c2.selectbox("상관계수", ["Pearson(선형)", "Spearman(순위)"],
                                   help="정규분포가 아니거나 순위·등급 자료면 Spearman을 쓰세요.")
            if len(sel) >= 2:
                corr = df[sel].corr(method="pearson" if cmethod.startswith("Pearson") else "spearman")
                # 숫자만 있는 상관행렬 표는 아래 '유의성 별표 포함' 표와 내용이 같아 화면에서는 하나만 보여 준다.
                # (숫자형 상관행렬은 아래 '상관분석 결과표' 저장·보고서 담기에 그대로 쓰인다)
                # ---- 유의성 별표 표기 (논문 관행) ----
                _meth = stats.pearsonr if cmethod.startswith("Pearson") else stats.spearmanr
                star_tbl = pd.DataFrame(index=corr.index, columns=corr.columns, dtype=object)
                n_pairs = 0
                _pairs, _ns = [], []
                for a in sel:
                    for b in sel:
                        if a == b:
                            star_tbl.loc[a, b] = "1"
                            continue
                        sub = df[[a, b]].dropna()
                        if len(sub) < 3:
                            star_tbl.loc[a, b] = "-"
                            continue
                        try:
                            r_, p_ = _meth(sub[a], sub[b])
                            mark = "***" if p_ < .001 else "**" if p_ < .01 else "*" if p_ < .05 else ""
                            star_tbl.loc[a, b] = f"{r_:.3f}{mark}"
                            if mark and a < b: n_pairs += 1
                            if sel.index(a) < sel.index(b):
                                _pairs.append((a, b, float(r_), float(p_)))
                                _ns.append(len(sub))
                        except Exception:
                            star_tbl.loc[a, b] = "-"
                st.markdown("###### 📋 상관계수표 (유의성 별표 포함)")
                star_out = star_tbl.reset_index().rename(columns={"index": "변수"})
                smart_table(star_out, width="stretch")
                st.caption("\\* p<0.05, \\*\\* p<0.01, \\*\\*\\* p<0.001 "
                           f"／ 유의한 상관을 보인 변수쌍 {n_pairs}개")
                _corr_num = corr.round(3).reset_index().rename(columns={"index": "변수"})
                _corr_heat = xl_chart("heatmap", _corr_num, "상관계수 히트맵", value_range=(-1, 1))
                dl_table(star_out, f"{'Pearson' if cmethod.startswith('Pearson') else 'Spearman'} 상관분석표",
                         "corrstar", "상관분석표", xlsx_chart=_corr_heat)
                txt = interpret_corr(corr, sel); st.info("💡 " + txt)
                _mname = "Pearson" if cmethod.startswith("Pearson") else "Spearman"
                _n_rng = (min(_ns), max(_ns)) if _ns else (len(df), len(df))
                _corr_foot = ("* p<0.05, ** p<0.01, *** p<0.001.\n"
                              f"* {_mname} 상관계수, n = "
                              + (f"{_n_rng[0]}" if _n_rng[0] == _n_rng[1] else f"{_n_rng[0]}~{_n_rng[1]}") + ".")
                _corr_sent = report_sentence_corr(_pairs, _n_rng, _mname, target=_v1_target_var(sel))
                _v1_copy_box("표 각주 (복사해서 표 아래에 붙이세요)", _corr_foot)
                fig, ax = plt.subplots(figsize=(1.2*len(sel), 1.0*len(sel)))
                from matplotlib.colors import LinearSegmentedColormap
                _corr_cmap = LinearSegmentedColormap.from_list(
                    "smart_corr", ["#C96767", "#F5E2E2", "#FFFFFF", "#D9EAF7", "#3D6F9F"])
                sns.heatmap(corr, annot=True, fmt=".2f", cmap=_corr_cmap, center=0, ax=ax,
                            linewidths=.6, linecolor="white", square=True,
                            cbar_kws={"shrink": .82})
                deco(ax, "상관계수 히트맵", ylabel_top=False); ax.grid(False)
                for _sp in ax.spines.values():
                    _sp.set_visible(False)
                try:
                    _cb = ax.collections[0].colorbar
                    if _cb is not None:
                        _cb.outline.set_visible(False)
                except Exception:
                    pass
                png = fig_to_png(fig)
                st.download_button("🖼️ 히트맵 다운로드", png, "heatmap.png", "image/png")
                out = corr.round(3).reset_index().rename(columns={"index": "변수"})
                dl_table(out, "상관계수 행렬(숫자만)", "corr2", "corr", xlsx_chart=_corr_heat)
                log_action(f"상관분석: {len(sel)}개 변수")
                ai_interpret_button("corr", f"{_mname} 상관분석", star_out,
                                    "상관계수표입니다. 별표(*)는 유의성입니다. 상관은 인과관계가 아니므로 "
                                    "'영향을 준다'가 아니라 '함께 변한다'로 서술하세요.",
                                    capture_slot="cap_corr")
                _v1_copy_box("보고서용 결과 문장", _corr_sent)
                report_capture("cap_corr", "상관분석", None,
                               blocks=[{"text": _corr_sent},
                                       {"caption": f"{_mname} 상관분석표", "table": star_out, "image": png,
                                        "xlsx_chart": _corr_heat},
                                       {"text": _corr_foot}])
        report_button("cap_corr")

    # ---------- 분산분석 ----------
    if tab_anova.on:
        st.subheader("분산분석(ANOVA)")
        with st.expander("ℹ️ 이 분석이 뭔가요?"): st.markdown(EXPLAIN["anova"])
        # 기본 설계는 크게, 고급 설계(분할구법·반복측정)는 같은 목록 아래에 작은 글씨로 둔다.
        _anova_modes = ["일원배치 (요인 1개)", "이원배치 (요인 2개 + 상호작용)",
                        "📊 여러 형질 한 표에 (요약표)",
                        "🌾 분할구법 (Split-plot)", "🔁 반복측정 (같은 개체 시기별 조사)"]
        _anova_labels = {
            "일원배치 (요인 1개)": "**일원배치** (요인 1개)",
            "이원배치 (요인 2개 + 상호작용)": "**이원배치** (요인 2개 + 상호작용)",
            "📊 여러 형질 한 표에 (요약표)": "📊 **여러 형질 한 표에** (요약표)",
            "🌾 분할구법 (Split-plot)": ":small[:gray[고급 · 🌾 분할구법 (Split-plot)]]",
            "🔁 반복측정 (같은 개체 시기별 조사)": ":small[:gray[고급 · 🔁 반복측정 (같은 개체 시기별 조사)]]",
        }
        mode = st.radio("시험 형태", _anova_modes, key="anova_mode_v1",
                        format_func=lambda m: _anova_labels.get(m, m))
        if mode.startswith("📊"):
            st.caption("여러 측정 항목을 한 번에 분석해, 논문 양식처럼 **하나의 표**로 만듭니다. "
                       "각 수치 옆에 유의성 문자(a, b, c)가 위첨자로 붙습니다.")
            if not cat_cols or not num_cols:
                st.warning("그룹(범주형)과 측정(숫자형) 변수가 필요합니다.")
            else:
                c1, c2 = st.columns(2)
                gc = c1.selectbox("처리구(그룹)", cat_cols, key="ms_g")
                ph = c2.selectbox("사후검정", ["Tukey HSD", "던컨(Duncan)", "Bonferroni"], key="ms_ph")
                traits = st.multiselect("측정 항목(형질) 선택 — 여러 개", num_cols,
                                        default=_measure_default, key="ms_t")
                c3, c4 = st.columns(2)
                dec = c3.selectbox("소수점 자릿수", [0, 1, 2, 3], index=1, key="ms_dec")
                show_ns = c4.checkbox("유의차 없으면 문자 생략", value=True,
                                      help="ANOVA에서 p≥0.05인 항목은 문자를 붙이지 않습니다.")
                if traits and keep_running("summary", "요약표 만들기"):
                    rows, notes = [], []
                    groups_order = None
                    result = {}
                    # 여러 형질 모드도 표만 만들고 끝내지 않고, 항목별 그래프를 함께 만든다.
                    # 각 그래프에는 평균값 + SD/SE 오차막대 + 유의성 문자(a,b,c)를 표시한다.
                    plot_records = []
                    for tr in traits:
                        data = df[[gc, tr]].dropna()
                        if data[gc].nunique() < 2: continue
                        try:
                            model = ols(safe_formula(tr, [gc]), data=data).fit()
                            pval = sm.stats.anova_lm(model, typ=2)["PR(>F)"].iloc[0]
                        except Exception:
                            pval = np.nan
                        means = data.groupby(gc)[tr].mean()
                        if groups_order is None:
                            groups_order = list(df[gc].dropna().unique())
                        letters = {}
                        if not (show_ns and (np.isnan(pval) or pval >= .05)):
                            try:
                                _phres = posthoc_from_model(model, data, gc, ph)
                                ns = _phres["not_sig"]
                                order = means.sort_values(ascending=False).index.tolist()
                                letters = compact_letter_display(order, ns)
                            except Exception:
                                letters = {}
                        col = {}
                        for g in groups_order:
                            if g in means.index:
                                v = f"{means[g]:.{dec}f}"
                                if letters.get(g): v += "^" + letters[g]
                                col[g] = v
                            else:
                                col[g] = "-"
                        result[tr] = col
                        notes.append({"항목": tr, "p-value": ("-" if np.isnan(pval) else round(pval, 4)),
                                      "유의성": "-" if np.isnan(pval) else ("**" if pval < .01 else "*" if pval < .05 else "n.s.")})

                        # ---- 여러 형질 모드: 항목별 화면 그래프 ----
                        try:
                            _stats = data.groupby(gc)[tr].agg(["mean", "std", "count"])
                            _order = [g for g in groups_order if g in _stats.index]
                            _use_se = st.session_state.get("err_type", "표준편차(SD)").startswith("표준오차")
                            _err = (_stats["std"] / np.sqrt(_stats["count"])) if _use_se else _stats["std"]
                            _elabel = "표준오차" if _use_se else "표준편차"
                            _m = _stats.loc[_order]
                            _e = _err.loc[_order].fillna(0)
                            _fig, _ax = plt.subplots(figsize=(min(6.2, max(4.8, len(_order) * 0.90)),
                                                             min(4.0, figsize()[1])))
                            _ax.bar(_order, _m["mean"], yerr=_e, capsize=4,
                                    color=bar_colors(values=_m["mean"].tolist()),
                                    edgecolor="none", width=.62 if pretty_on() else .8,
                                    error_kw={"ecolor": "#5a6067", "elinewidth": 1.1})
                            bar_value_sig_labels(
                                _ax, range(len(_order)), _m["mean"].tolist(), _e.tolist(),
                                [letters.get(g, "") for g in _order], dec=dec)
                            _ax.margins(y=.20 if pretty_on() else .10)
                            _ax.set_ylabel(tr); _ax.set_xlabel(gc)
                            deco(_ax, f"{gc}별 {tr} (평균±{_elabel}, {ph})")
                            _png = fig_to_png(_fig, show=False)
                            plot_records.append({"trait": tr, "png": _png, "error_label": _elabel})
                        except Exception:
                            # 표 계산은 정상인데 특정 그래프만 실패한 경우 전체 요약분석을 중단하지 않는다.
                            pass
                    summary = pd.DataFrame(result)
                    summary.index.name = gc
                    summary = summary.reset_index()
                    st.markdown("#### 처리구별 형질 요약표")
                    smart_table(sup_df(summary), width="stretch")
                    st.markdown("#### 항목별 분산분석 유의성")
                    ndf = pd.DataFrame(notes)
                    smart_table(ndf, width="stretch")

                    if plot_records:
                        st.markdown("#### 📊 항목별 그래프")
                        st.caption("막대는 처리 평균, 오차막대는 선택한 SD/SE이며, 숫자 뒤 a·b·c는 사후검정 유의성 그룹입니다. "
                                   "ANOVA가 유의하지 않은 항목은 문자를 생략합니다.")
                        _cols = st.columns(2)
                        for _i, _pr in enumerate(plot_records):
                            with _cols[_i % 2]:
                                st.markdown(f"**{_pr['trait']}**")
                                st.image(_pr["png"], width="stretch")
                                st.download_button(
                                    f"🖼️ {_pr['trait']} 그래프 PNG", _pr["png"],
                                    f"anova_multi_{_i+1}.png", "image/png",
                                    key=f"ms_plot_dl_{_i}", width="stretch")

                    txt = (f"{gc}에 따라 {len(traits)}개 형질을 {ph}로 분석했습니다. "
                           "같은 문자를 가진 처리구끼리는 통계적 차이가 없습니다. "
                           f"(유의: {(ndf['유의성'] != 'n.s.').sum()}개 항목)")
                    st.info("💡 " + txt)
                    dl_table(summary, f"{gc}별 생산력 검정 결과 ({ph})", "summary_table3", "summary_table")
                    log_action(f"요약표 생성: {gc} × {len(traits)}개 형질 ({ph})")

                    _ms_blocks = [
                        {"caption": "처리구별 형질 요약표", "table": summary},
                        {"caption": "항목별 분산분석 유의성", "table": ndf},
                    ]
                    _ms_blocks += [
                        {"caption": f"{_pr['trait']} 처리구별 평균±{_pr['error_label']}",
                         "image": _pr["png"]}
                        for _pr in plot_records
                    ]
                    report_capture("cap_ms", f"{gc}별 형질 요약표", text=txt, blocks=_ms_blocks)
                    ai_interpret_button("ms", f"{gc}별 여러 형질 요약표", summary,
                                        "각 수치 옆 a,b,c는 처리 간 유의성 그룹입니다.",
                                        capture_slot="cap_ms")
                report_button("cap_ms")
        elif mode.startswith("일원배치"):
            if not cat_cols or not num_cols: st.warning("그룹(범주형)과 측정(숫자형) 변수가 필요합니다.")
            else:
                c1, c2, c3 = st.columns(3)
                gc = c1.selectbox("처리구(그룹)", cat_cols, key="aov_g")
                vc = c2.selectbox("측정값", num_cols, key="aov_v")
                ph = c3.selectbox("사후검정", ["Tukey HSD", "던컨(Duncan)", "Bonferroni",
                                            "던넷(Dunnett, 대조구 대비)"], key="aov_ph")
                if ph.startswith("던넷"):
                    _lvls = df[gc].dropna().astype(str).unique().tolist()
                    _ci = guess_idx(_lvls, ["대조", "관행", "무처리", "control", "CK"])
                    st.selectbox("대조구(비교 기준)", _lvls, index=_ci, key="dunnett_ctrl")
                    st.caption("던넷 검정은 **모든 처리를 대조구와만** 비교합니다. "
                               "신품종 vs 대비품종처럼 기준이 뚜렷할 때 검정력이 가장 높습니다.")
                blk_opts = ["(없음 · 완전임의배치)"] + [c for c in df.columns if c not in (gc, vc)]
                blk = st.selectbox("반복(블록) 열 — 난괴법이면 반드시 선택", blk_opts,
                                   index=guess_idx(blk_opts, ["반복", "블록", "구역", "block", "rep"]),
                                   key="aov_b")
                if ph == "던컨(Duncan)":
                    st.caption("⚠️ 던컨(DMRT)은 검정력이 높지만 위양성(제1종 오류)을 통제하지 못합니다. "
                               "논문 투고 시에는 Tukey HSD가 더 안전합니다.")
                if blk.startswith("(없음"):
                    st.caption("💡 포장시험에서 반복(블록)을 두었다면 반드시 지정하세요. "
                               "지정하지 않으면 블록 간 변이가 오차에 섞여 처리 효과를 놓칠 수 있습니다.")
                if keep_running("anova", "ANOVA 분석 실행"):
                    use_blk = not blk.startswith("(없음")
                    cols_need = [gc, vc] + ([blk] if use_blk else [])
                    data = df[cols_need].dropna()
                    # ---- 사전 검증 (분석 가능한 자료인지) ----
                    ok_to_run, msgs = validate_anova_data(data, gc, vc)
                    for m in msgs: st.warning(m)
                    if not ok_to_run:
                        st.stop()
                    st.markdown("#### 1) 가정 검정")
                    nrows, nok = [], True
                    for g in data[gc].unique():
                        v = data[data[gc] == g][vc]
                        if len(v) >= 3:
                            w, p = stats.shapiro(v)
                            nrows.append({"그룹": g, "W": round(w, 3), "p": round(p, 3),
                                          "정규성": "만족" if p >= .05 else "위배"})
                            if p < .05: nok = False
                    lp = np.nan
                    try:
                        samples = [data[data[gc] == g][vc] for g in data[gc].unique()]
                        samples = [s for s in samples if len(s) >= 2]
                        if len(samples) >= 2:
                            ls, lp = stats.levene(*samples)
                    except Exception:
                        lp = np.nan
                    if nrows:
                        smart_table(pd.DataFrame(nrows), width="stretch")
                    else:
                        st.caption("각 처리구의 반복이 3개 미만이라 정규성 검정을 생략했습니다.")
                    if not np.isnan(lp):
                        st.write(f"등분산(Levene): 통계량={ls:.3f}, {fmt_p(lp, digits=3)} → {'만족' if lp >= .05 else '위배'}")
                    else:
                        st.caption("반복이 부족해 등분산 검정을 생략했습니다.")
                    if nok and (np.isnan(lp) or lp >= .05):
                        st.success("가정을 모두 만족합니다. ANOVA 결과를 신뢰할 수 있어요.")
                    else:
                        st.warning("가정이 일부 위배되었습니다. 아래 **비모수 검정 결과**를 함께 확인하세요.")
                        # ---- 비모수 자동 전환 (원클릭) ----
                        try:
                            _grps = [g[vc].values for _, g in data.groupby(gc)]
                            if len(_grps) == 2:
                                _st, _p = stats.mannwhitneyu(*_grps)
                                _nm = "Mann-Whitney U 검정"
                            else:
                                _st, _p = stats.kruskal(*_grps)
                                _nm = "Kruskal-Wallis 검정"
                            _med = data.groupby(gc)[vc].median().round(rnd())
                            with st.expander(f"🧪 비모수 대안: {_nm} 결과 보기", expanded=True):
                                k1, k2 = st.columns(2)
                                k1.metric("검정 통계량", f"{_st:.3f}")
                                k2.metric("p-value", f"{_p:.4f}",
                                          "유의함" if _p < .05 else "유의하지 않음")
                                smart_table(pd.DataFrame({gc: _med.index.astype(str),
                                                           f"{vc} 중앙값": _med.values}),
                                             width="stretch")
                                st.caption("정규성·등분산 가정을 쓰지 않는 방법입니다. "
                                           "평균 대신 **중앙값**으로 비교합니다. "
                                           "아래 ANOVA 결과와 결론이 다르면 비모수 결과를 우선하세요.")
                        except Exception:
                            st.caption("비모수 검정을 자동 수행하지 못했습니다. '비모수검정' 탭을 이용하세요.")
                    st.markdown("#### 2) 분산분석 결과")
                    formula = safe_formula(vc, [gc] + ([blk] if use_blk else []))
                    model = ols(formula, data=data).fit()
                    aov = sm.stats.anova_lm(model, typ=2)
                    smart_table(aov.round(4), width="stretch")
                    st.caption("설계: " + ("**난괴법(RCBD)** — 반복(블록) 효과를 모형에 포함했습니다."
                                          if use_blk else "**완전임의배치(CRD)** — 블록 없음"))
                    tkey = f"C({q_ref(gc)})"
                    pval = aov.loc[tkey, "PR(>F)"] if tkey in aov.index else aov["PR(>F)"].iloc[0]
                    if use_blk:
                        bkey = f"C({q_ref(blk)})"
                        if bkey in aov.index:
                            bp = aov.loc[bkey, "PR(>F)"]
                            st.caption(f"블록('{blk}') 효과 {fmt_p(bp, sp=True)} → "
                                       + ("블록 간 차이가 있어 난괴법이 적절했습니다."
                                          if bp < .05 else "블록 간 차이는 뚜렷하지 않았습니다."))
                    _ctrl_for_ph = st.session_state.get("dunnett_ctrl") if ph.startswith("던넷") else None
                    _phres = posthoc_from_model(model, data, gc, ph, control=_ctrl_for_ph)
                    ns = _phres["not_sig"]
                    means = data.groupby(gc)[vc].agg(["mean", "std", "count"])
                    order = means.sort_values("mean", ascending=False).index.tolist()
                    # 전체 ANOVA가 유의하지 않으면 모든 처리에 'a'를 붙이지 않는다.
                    # 화면 메시지(유의차 없음)와 그래프/표가 서로 모순되어 보이는 것을 방지한다.
                    letters = ({} if float(pval) >= 0.05 or ph.startswith("던넷")
                               else compact_letter_display(order, ns))
                    # ---- CV% · LSD (시험연구보고서 필수 지표) ----
                    st.markdown("#### 3) 시험 정밀도 지표")
                    ci = calc_cv_lsd(model, data, gc, vc)
                    m1, m2, m3 = st.columns(3)
                    m1.metric("CV (변이계수)", f"{ci['CV']:.1f} %", cv_grade(ci["CV"]))
                    m2.metric("LSD (p<0.05)", f"{ci['LSD']:.2f}")
                    m3.metric("오차평균제곱(MSE)", f"{ci['MSE']:.2f}")
                    if np.isfinite(ci["CV"]) and ci["CV"] < 1:
                        st.warning(f"⚠️ CV가 {ci['CV']:.1f}%로 너무 낮습니다. 실제 포장시험에서는 거의 나오지 않는 값이라, "
                                   "평균값을 반복마다 복사해 넣었거나 같은 값을 붙여넣지 않았는지 원자료를 확인해 주세요.")
                    st.caption("CV%는 시험의 정밀도를 나타냅니다(포장시험 10~20% 양호, 20% 초과 시 재검토). "
                               f"두 처리 평균의 차이가 LSD({ci['LSD']:.2f})보다 크면 유의한 차이로 봅니다.")
                    if ci["CV"] > 30:
                        st.warning("⚠️ CV%가 30%를 넘습니다. 포장 불균일·조사 오차·이상값을 점검해 보세요.")
                    if ph.startswith("던넷"):
                        _c0 = st.session_state.get("dunnett_ctrl", "")
                        txt = (f"[{ph}] " + ("처리구 간 유의한 차이가 있습니다"
                                             if pval < .05 else "처리구 간 유의한 차이가 없습니다")
                               + f" ({fmt_p(pval, sp=True)}). 대조구 '{_c0}'와의 개별 비교는 아래 표를 보세요.")
                    else:
                        txt = f"[{ph}] " + interpret_anova(pval, letters)
                    st.info("💡 " + txt)
                    # ---- 던넷: 적합모형 기반 대조구 대비 전용 표 ----
                    if ph.startswith("던넷"):
                        _c = _phres.get("control")
                        dn_df = _phres.get("table", pd.DataFrame()).copy()
                        if not dn_df.empty:
                            for _cnum in ["대조구 평균(보정)", "처리 평균(보정)", "평균 차이",
                                          "t 통계량", "p(동시보정)", "95% 동시CI 하한", "95% 동시CI 상한"]:
                                if _cnum in dn_df.columns:
                                    dn_df[_cnum] = pd.to_numeric(dn_df[_cnum], errors="coerce").round(rnd())
                            st.markdown(f"###### 던넷 검정: '{_c}' 대비 모형 기반 비교")
                            smart_table(dn_df, width="stretch", hide_index=True)
                            st.caption("ANOVA와 같은 적합모형의 잔차·블록 보정을 사용한 동시비교입니다. "
                                       "95% 동시신뢰구간이 0을 포함하지 않으면 대조구와 유의한 차이가 있습니다.")
                            _sig = dn_df[dn_df["판정"].astype(str).str.startswith("유의")]["처리구"].tolist()
                            st.caption(f"대조구 '{_c}'와 유의한 차이를 보인 처리: "
                                       + (", ".join(map(str, _sig)) if _sig else "없음"))
                            dl_table(dn_df, f"{_c} 대비 모형 기반 던넷 검정", "dunnett1", "dunnett")
                        else:
                            st.warning("던넷 비교표를 만들 수 없습니다. 대조구와 처리 수준을 확인하세요.")
                    if ph.startswith("던넷"):
                        letters = {}   # 던넷은 문자(a,b,c) 표기를 쓰지 않음
                        st.info("ℹ️ 던넷 검정은 대조구와의 비교만 수행하므로 "
                                "유의성 문자(a, b, c)는 표기하지 않습니다. 위 표를 사용하세요.")
                    res = means.copy(); res["유의성"] = [letters.get(g, "") for g in res.index]
                    res = res.rename(columns={"mean": "평균", "std": "표준편차", "count": "n"}).round(rnd()).reset_index()
                    # 논문용 '평균±표준오차' 결합 표기 컬럼 추가
                    _se = (means["std"] / np.sqrt(means["count"])).round(rnd())
                    res["평균±SE"] = [f"{means.loc[g,'mean']:.{rnd()}f}±{_se.loc[g]:.{rnd()}f}"
                                     + (letters.get(g, "") and f"^{letters.get(g,'')}")
                                     for g in res[gc]]
                    smart_table(sup_display(res), width="stretch")
                    use_se = st.session_state.get("err_type", "표준편차(SD)").startswith("표준오차")
                    err = (means["std"] / np.sqrt(means["count"])) if use_se else means["std"]
                    elabel = "표준오차" if use_se else "표준편차"
                    fig, ax = plt.subplots(figsize=(min(6.6, max(5.0, len(order)*0.92)), min(4.2, figsize()[1])))
                    m = means.loc[order]; e_ = err.loc[order]
                    ax.bar(order, m["mean"], yerr=e_, capsize=4,
                           color=bar_colors(values=m["mean"].tolist()),
                           edgecolor="none", width=.62 if pretty_on() else .8,
                           error_kw={"ecolor": "#5a6067", "elinewidth": 1.1})
                    bar_value_sig_labels(
                        ax, range(len(order)), m["mean"].tolist(), e_.tolist(),
                        [letters.get(g, "") for g in order], dec=rnd())
                    ax.margins(y=.20 if pretty_on() else .07)
                    ax.set_ylabel(vc); ax.set_xlabel(gc)
                    deco(ax, f"{gc}별 {vc} (평균±{elabel}, {ph})")
                    png = fig_to_png(fig)
                    st.download_button("🖼️ 그래프 다운로드", png, "anova.png", "image/png")
                    # ---- 표 각주 자동 생성 ----
                    _phname = {"Tukey HSD": "Tukey의 HSD 검정", "던컨(Duncan)": "던컨의 다중검정(DMRT)",
                               "Bonferroni": "Bonferroni 보정 t-검정"}.get(ph, ph)
                    if ph.startswith("던넷"):
                        # ⑭ 던넷은 문자를 쓰지 않으므로 각주도 다르게
                        _c1 = st.session_state.get("dunnett_ctrl", "대조구")
                        footnote = (f"* 던넷 검정으로 대조구 '{_c1}'와 각 처리를 비교하였음"
                                    "(다중비교 보정 p값, 5% 수준).\n"
                                    f"* CV(%) = {ci['CV']:.1f}, 평균±{elabel} "
                                    f"(n = {int(means['count'].min())})")
                    else:
                        footnote = (f"* 같은 열의 다른 문자는 {_phname}으로 5% 수준에서 "
                                    "유의차가 있음을 나타냄.\n"
                                    f"* CV(%) = {ci['CV']:.1f}, LSD(0.05) = {ci['LSD']:.2f}, "
                                    f"평균±{elabel} (n = {int(means['count'].min())})")
                    st.markdown("###### 📋 표 각주 (복사해서 표 아래에 붙이세요)")
                    st.code(footnote, language=None)
                    dl_table(res, f"{gc}별 {vc} 분산분석 ({ph})", "anova4", "anova")
                    log_action(f"일원배치 ANOVA: {gc} × {vc} ({ph})")
                    _anova_ctx = build_anova_context(
                        design=("난괴법(RCBD)" if use_blk else "완전임의배치(CRD)"),
                        trt=gc, blk=(blk if use_blk else None), yv=vc,
                        group_stats=res, anova_table=aov.reset_index(),
                        p_treatment=pval,
                        p_block=(float(aov.loc[f"C({q_ref(blk)})", "PR(>F)"])
                                 if use_blk and f"C({q_ref(blk)})" in aov.index else None),
                        cv=ci.get("CV"), lsd=ci.get("LSD"), mse=ci.get("MSE"),
                        df_resid=ci.get("dfe"), posthoc=ph,
                        letters=(None if ph.startswith("던넷") else letters),
                        dunnett=(dn_df if (ph.startswith("던넷") and "dn_df" in dir()) else None),
                        assumptions={"normality": nrows, "levene_p": (None if np.isnan(lp) else lp)},
                        n_missing=int(len(df) - len(data)),
                        cautions=(["던넷 검정은 대조구 대비 비교만 수행하며 문자(a,b,c)를 쓰지 않음"]
                                  if ph.startswith("던넷") else []))
                    ai_interpret_advanced("anova", f"{gc}별 {vc} 분산분석({ph})", res,
                                          "유의성 문자가 같으면 처리 간 차이가 없다는 의미입니다.",
                                          context=_anova_ctx, capture_slot="cap_anova")
                    _rep_txt = report_sentence_anova(gc, vc, pval, means, letters, ci, ph)
                    st.markdown("###### 📋 보고서용 결과 문장")
                    st.code(_rep_txt, language=None)
                    report_capture("cap_anova", f"{gc}별 {vc} 분산분석", None,
                                   blocks=[{"text": _rep_txt},
                                           {"caption": f"{gc}별 {vc} 분산분석 ({ph})", "table": res,
                                            "image": png},
                                           {"text": footnote}])
                report_button("cap_anova")
        elif mode.startswith("이원배치"):
            if len(cat_cols) < 2 or not num_cols: st.warning("범주형 변수 2개와 측정값 1개가 필요합니다.")
            else:
                c1, c2, c3 = st.columns(3)
                f1 = c1.selectbox("요인 A", cat_cols, key="tw_a")
                f2 = c2.selectbox("요인 B", [c for c in cat_cols if c != f1], key="tw_b")
                yv = c3.selectbox("측정값", num_cols, key="tw_y")
                if keep_running("twoway", "이원배치 ANOVA 실행"):
                    data = df[[f1, f2, yv]].dropna()
                    model = ols(safe_formula(yv, [f1, f2], interactions=[(f1, f2)]),
                                data=data).fit()
                    aov = sm.stats.anova_lm(model, typ=2); out = aov.round(4)
                    smart_table(out, width="stretch")
                    terms = {f"C({q_ref(f1)})": f"요인A({f1})",
                             f"C({q_ref(f2)})": f"요인B({f2})",
                             f"C({q_ref(f1)}):C({q_ref(f2)})": "상호작용"}
                    txt = " / ".join(f"**{lab}**: {'유의' if aov.loc[k,'PR(>F)']<.05 else '비유의'}({fmt_p(aov.loc[k,'PR(>F)'], digits=3)})"
                                     for k, lab in terms.items() if k in aov.index)
                    st.info("💡 " + txt)
                    fig, ax = plt.subplots(figsize=figsize())
                    for lv in data[f2].unique():
                        s = data[data[f2] == lv].groupby(f1)[yv].mean()
                        ax.plot(s.index, s.values, marker="o", label=f"{f2}={lv}")
                    ax.set_xlabel(f1); ax.set_ylabel(yv); deco(ax, "상호작용 그래프"); ax.legend()
                    png = fig_to_png(fig)
                    out2 = out.reset_index().rename(columns={"index": "요인"})
                    _tw_means = (data.groupby([f1, f2])[yv].mean().unstack(f2).round(rnd())
                                 .reset_index())
                    _tw_means.columns = [str(f1)] + [f"{f2}={c}" for c in _tw_means.columns[1:]]
                    _tw_chart = xl_chart("line", _tw_means, "상호작용 그래프 (조합별 평균)", y_title=str(yv))
                    dl_table(out2, f"{yv} 이원배치 분산분석", "twoway5", "twoway", xlsx_chart=_tw_chart)
                    report_capture("cap_tw", f"{yv} 이원배치 분산분석", txt, out2, png, xlsx_chart=_tw_chart)
                report_button("cap_tw")

        # ---------- 반복측정 ANOVA ----------
        # ---------- 분할구법 (Split-plot) ----------
        elif mode.startswith("🌾"):
            with st.expander("ℹ️ 분할구법이란?"):
                st.markdown("""
**관수·경운·재배법처럼 작은 구역에 나누기 어려운 요인**이 있을 때 쓰는 설계입니다.

- **주구(主區, Main plot)**: 큰 구역에 배치하는 요인 (예: 관수 방법, 경운 방법, 재배 양식)
- **세구(細區, Sub plot)**: 주구를 쪼개서 배치하는 요인 (예: 품종, 시비량)

**왜 따로 분석해야 하나요?**
주구와 세구는 **오차의 크기가 다릅니다.** 주구는 큰 구역이라 오차가 크고, 세구는 작아서 오차가 작습니다.
일반 이원배치로 분석하면 주구 효과가 **실제보다 과대평가**됩니다.
분할구 분석은 **주구오차(반복×주구)** 와 **세구오차**를 분리해 각각 올바른 검정을 합니다.

**필요한 열**: 반복(블록) · 주구 요인 · 세구 요인 · 측정값
""")
            if len(cat_cols) < 3 or not num_cols:
                st.warning("반복·주구·세구 3개의 범주형 열과 측정값 1개가 필요합니다.")
            else:
                allc = df.columns.tolist()
                c1, c2 = st.columns(2)
                rep_c = c1.selectbox("반복(블록) 열", cat_cols,
                                     index=guess_idx(cat_cols, ["반복", "블록", "block", "rep"]), key="sp_r")
                yv = c2.selectbox("측정값", num_cols, key="sp_y")
                c3, c4 = st.columns(2)
                main_c = c3.selectbox("주구(큰 구역) 요인", [c for c in cat_cols if c != rep_c],
                                      index=guess_idx([c for c in cat_cols if c != rep_c],
                                                      ["관수", "경운", "재배", "처리"]), key="sp_m")
                sub_opts = [c for c in cat_cols if c not in (rep_c, main_c)]
                sub_c = c4.selectbox("세구(작은 구역) 요인", sub_opts,
                                     index=guess_idx(sub_opts, ["품종", "계통", "시비"]), key="sp_s")
                if keep_running("splitplot", "분할구 분산분석 실행"):
                    data = df[[rep_c, main_c, sub_c, yv]].dropna()
                    ok_sp, msgs = validate_anova_data(data, main_c, yv)
                    for m in msgs: st.warning(m)
                    if not ok_sp: st.stop()
                    try:
                        f_full = safe_formula(yv, [rep_c, main_c, sub_c],
                                              interactions=[(rep_c, main_c),
                                                            (main_c, sub_c)])
                        mfull = ols(f_full, data=data).fit()
                        a = sm.stats.anova_lm(mfull, typ=2)
                        k_rep, k_main = f"C({q_ref(rep_c)})", f"C({q_ref(main_c)})"
                        k_erra = f"C({q_ref(rep_c)}):C({q_ref(main_c)})"
                        k_sub = f"C({q_ref(sub_c)})"
                        k_int = f"C({q_ref(main_c)}):C({q_ref(sub_c)})"
                        ms = lambda k: a.loc[k, "sum_sq"] / a.loc[k, "df"]
                        ms_errb = a.loc["Residual", "sum_sq"] / a.loc["Residual", "df"]
                        # 주구는 주구오차로, 세구·상호작용은 세구오차로 검정
                        F_main = ms(k_main) / ms(k_erra)
                        p_main = 1 - stats.f.cdf(F_main, a.loc[k_main, "df"], a.loc[k_erra, "df"])
                        F_sub = ms(k_sub) / ms_errb
                        p_sub = 1 - stats.f.cdf(F_sub, a.loc[k_sub, "df"], a.loc["Residual", "df"])
                        F_int = ms(k_int) / ms_errb
                        p_int = 1 - stats.f.cdf(F_int, a.loc[k_int, "df"], a.loc["Residual", "df"])
                        rows = [
                            {"요인": f"반복({rep_c})", "자유도": int(a.loc[k_rep, "df"]),
                             "제곱합": round(a.loc[k_rep, "sum_sq"], 3), "평균제곱": round(ms(k_rep), 3),
                             "F": "-", "p": "-"},
                            {"요인": f"주구: {main_c}", "자유도": int(a.loc[k_main, "df"]),
                             "제곱합": round(a.loc[k_main, "sum_sq"], 3), "평균제곱": round(ms(k_main), 3),
                             "F": f"{F_main:.3f}", "p": f"{p_main:.4f}"},
                            {"요인": "주구오차(Ea)", "자유도": int(a.loc[k_erra, "df"]),
                             "제곱합": round(a.loc[k_erra, "sum_sq"], 3), "평균제곱": round(ms(k_erra), 3),
                             "F": "-", "p": "-"},
                            {"요인": f"세구: {sub_c}", "자유도": int(a.loc[k_sub, "df"]),
                             "제곱합": round(a.loc[k_sub, "sum_sq"], 3), "평균제곱": round(ms(k_sub), 3),
                             "F": f"{F_sub:.3f}", "p": f"{p_sub:.4f}"},
                            {"요인": f"{main_c}×{sub_c}", "자유도": int(a.loc[k_int, "df"]),
                             "제곱합": round(a.loc[k_int, "sum_sq"], 3), "평균제곱": round(ms(k_int), 3),
                             "F": f"{F_int:.3f}", "p": f"{p_int:.4f}"},
                            {"요인": "세구오차(Eb)", "자유도": int(a.loc["Residual", "df"]),
                             "제곱합": round(a.loc["Residual", "sum_sq"], 3), "평균제곱": round(ms_errb, 3),
                             "F": "-", "p": "-"},
                        ]
                        sp_tbl = pd.DataFrame(rows)
                        st.markdown("#### 분할구 분산분석표")
                        smart_table(sp_tbl, width="stretch")
                        st.caption("주구는 **주구오차(Ea)**로, 세구와 상호작용은 **세구오차(Eb)**로 검정합니다. "
                                   "일반 이원배치로 분석하면 주구 효과가 과대평가됩니다.")
                        cva = np.sqrt(ms(k_erra)) / data[yv].mean() * 100
                        cvb = np.sqrt(ms_errb) / data[yv].mean() * 100
                        m1, m2 = st.columns(2)
                        m1.metric("CV(a) 주구", f"{cva:.1f} %", cv_grade(cva))
                        m2.metric("CV(b) 세구", f"{cvb:.1f} %", cv_grade(cvb))
                        parts = []
                        parts.append(f"주구인 '{main_c}'의 효과는 " +
                                     (f"유의하였다({fmt_p(p_main)})." if p_main < .05 else f"유의하지 않았다({fmt_p(p_main)})."))
                        parts.append(f"세구인 '{sub_c}'의 효과는 " +
                                     (f"유의하였다({fmt_p(p_sub)})." if p_sub < .05 else f"유의하지 않았다({fmt_p(p_sub)})."))
                        parts.append("두 요인의 상호작용은 " +
                                     (f"유의하여 조합별 해석이 필요하다({fmt_p(p_int)})." if p_int < .05
                                      else f"유의하지 않았다({fmt_p(p_int)})."))
                        txt = " ".join(parts)
                        st.info("💡 " + txt)
                        piv = data.pivot_table(index=main_c, columns=sub_c, values=yv, aggfunc="mean").round(rnd())
                        st.markdown("#### 주구 × 세구 평균")
                        smart_table(piv.reset_index(), width="stretch")
                        fig, ax = plt.subplots(figsize=figsize())
                        for sname in piv.columns:
                            ax.plot(piv.index.astype(str), piv[sname], marker="o", label=str(sname))
                        ax.set_xlabel(main_c); ax.set_ylabel(yv)
                        ax.legend(title=sub_c, fontsize=8); deco(ax, f"{main_c} × {sub_c}")
                        plt.tight_layout(); png = fig_to_png(fig)
                        st.download_button("🖼️ 그래프 다운로드", png, "splitplot.png", "image/png")
                        dl_table(sp_tbl, f"{main_c}(주구) × {sub_c}(세구) 분할구 분산분석", "sp1", "splitplot")
                        log_action(f"분할구 분산분석: {main_c} × {sub_c}")
                        ai_interpret_button("sp", f"{main_c}(주구)×{sub_c}(세구) 분할구 분산분석", sp_tbl,
                                            "주구는 주구오차로, 세구는 세구오차로 검정한 결과입니다.", capture_slot="cap_sp")
                        report_capture("cap_sp", f"{main_c}×{sub_c} 분할구 분산분석", None,
                                       blocks=[{"text": txt},
                                               {"caption": "분할구 분산분석표", "table": sp_tbl},
                                               {"caption": "주구×세구 평균", "table": piv.reset_index(),
                                                "image": png}])
                    except Exception as ex:
                        st.error(f"분할구 분석 실패: {ex}\n\n반복·주구·세구가 모두 갖춰진 균형 자료인지 확인해 주세요.")
                report_button("cap_sp")

        elif mode.startswith("🔁"):
            with st.expander("ℹ️ 반복측정 분산분석이란?"):
                st.markdown("""
**같은 개체를 여러 시기에 반복해서 조사한 자료**에 사용합니다.
(예: 같은 고추 개체의 초장을 정식 후 2·4·6·8주에 계속 측정)

**왜 일반 ANOVA를 쓰면 안 되나요?**
일반 ANOVA는 모든 관측치가 서로 **독립**이라고 가정합니다. 그런데 같은 개체를 반복 측정하면,
원래 잘 자라던 개체는 모든 시기에 계속 크게 나옵니다. 즉 관측치들이 서로 얽혀 있습니다.
이를 무시하면 **오차를 실제보다 작게 평가**해서, 차이가 없는데도 있다고 판단하기 쉽습니다.
반복측정 ANOVA는 '개체마다 원래 다른 정도'를 따로 분리해 이 문제를 해결합니다.

**자료 형태 (긴 형식)** — 한 행 = 한 개체의 한 시점

| 개체번호 | 조사시기 | 초장(cm) |
|---|---|---|
| P01 | 2주 | 18.2 |
| P01 | 4주 | 27.5 |
| P02 | 2주 | 16.9 |

**필요한 열**: 개체 번호 · 조사 시기 · 측정값
**조건**: 모든 개체가 **같은 시기에 빠짐없이** 측정되어 있어야 합니다(균형 자료).

**결과 읽는 법**: p < 0.05면 시기에 따라 측정값이 유의하게 변했다는 뜻입니다.

⚠️ 시기가 3개 이상이면 **구형성(sphericity)** 가정이 필요합니다. 결과가 p≈0.05 근처로 애매하면 해석에 주의하세요.
""")
            if len(df.columns) < 3:
                st.warning("개체·시기·측정값 3개 열이 필요합니다.")
            else:
                allc = df.columns.tolist()
                c1, c2, c3 = st.columns(3)
                subj = c1.selectbox("개체(반복 단위) 열", allc,
                                    index=guess_idx(allc, ["개체", "번호", "ID", "포기", "주"]), key="rm_s")
                within = c2.selectbox("조사 시기 열", allc,
                                      index=guess_idx(allc, ["시기", "일자", "주차", "조사", "date"]), key="rm_w")
                yv = c3.selectbox("측정값 열", num_cols, key="rm_y")
                _rm_dup = len({subj, within, yv}) < 3
                if _rm_dup:
                    st.warning("개체 열 · 조사 시기 열 · 측정값 열은 서로 다른 열로 골라 주세요.")
                if keep_running("rm", "반복측정 ANOVA 실행", disabled=_rm_dup):
                    data = df[[subj, within, yv]].dropna()
                    cnt = data.groupby([subj, within]).size()
                    _balance = validate_repeated_measure_balance(data, subj, within)
                    if _balance["duplicate_subjects"]:
                        st.error("⚠️ 같은 개체·같은 시기의 중복 자료가 있습니다: "
                                 + ", ".join(map(str, _balance["duplicate_subjects"][:8]))
                                 + ". 중복을 확인·정리한 뒤 다시 분석하세요.")
                    if _balance["bad_subjects"]:
                        st.error("⚠️ 개체마다 조사 시기 구성이 다릅니다. 반복측정 ANOVA는 "
                                 "**모든 개체가 동일한 시기 집합**을 가져야 합니다.\n\n"
                                 f"문제 개체({len(_balance['bad_subjects'])}개): "
                                 + ", ".join(map(str, _balance["bad_subjects"][:8]))
                                 + (" ..." if len(_balance["bad_subjects"]) > 8 else "")
                                 + f"\n\n전체 시기: {', '.join(map(str, _balance['expected_times']))}")
                    if _balance["ok"]:
                        try:
                            from statsmodels.stats.anova import AnovaRM
                            aovrm = AnovaRM(data, yv, subj, within=[within],
                                            aggregate_func="mean" if (cnt > 1).any() else None).fit()
                            tbl = aovrm.anova_table.round(4)
                            st.markdown("#### 반복측정 분산분석표")
                            smart_table(tbl, width="stretch")
                            p = float(tbl["Pr > F"].iloc[0])
                            txt = ("조사 시기에 따라 " +
                                   (f"측정값이 **유의하게 변화**했습니다 ({fmt_p(p, sp=True)})."
                                    if p < .05 else f"유의한 변화가 없었습니다 ({fmt_p(p, sp=True)})."))
                            st.info("💡 " + txt)
                            st.caption("※ 구형성(sphericity) 가정이 필요합니다. 시기 수가 3개 이상이고 "
                                       "결과가 경계값(p≈0.05)이면 해석에 주의하세요.")
                            g = data.groupby(within)[yv].agg(["mean", "std", "count"])
                            use_se = st.session_state.get("err_type", "표준편차(SD)").startswith("표준오차")
                            err = (g["std"]/np.sqrt(g["count"])) if use_se else g["std"]
                            res = g.rename(columns={"mean": "평균", "std": "표준편차", "count": "n"}).round(rnd()).reset_index()
                            smart_table(res, width="stretch")
                            fig, ax = plt.subplots(figsize=figsize())
                            ax.errorbar(g.index.astype(str), g["mean"], yerr=err, marker="o",
                                        capsize=4, color=pcolor(), lw=2)
                            ax.set_xlabel(within); ax.set_ylabel(yv)
                            deco(ax, f"시기별 {yv} 변화 (평균±{'표준오차' if use_se else '표준편차'})")
                            plt.tight_layout(); png = fig_to_png(fig)
                            st.download_button("🖼️ 그래프 다운로드", png, "rm.png", "image/png")
                            _rm_chart = xl_chart("line", res[[within, "평균"]], f"시기별 {yv} 변화", y_title=str(yv))
                            dl_table(res, f"시기별 {yv} 반복측정 분석", "rm6", "rm", xlsx_chart=_rm_chart)
                            log_action(f"반복측정 ANOVA: {within} × {yv}")
                            ai_interpret_button("rm", f"{yv} 반복측정 분산분석", res, "시기에 따른 변화를 나타냅니다.", capture_slot="cap_rm")
                            report_capture("cap_rm", f"{yv} 반복측정 분산분석", txt, res, png, xlsx_chart=_rm_chart)
                        except Exception as ex:
                            st.error(f"분석 실패: {ex}\n\n자료가 균형적인지(모든 개체 × 모든 시기) 확인해 주세요.")
                report_button("cap_rm")

        # ---------- ANCOVA ----------
        elif mode.startswith("🎚️"):
            with st.expander("ℹ️ 공분산분석(ANCOVA)이란?"):
                st.markdown("""
**출발선이 달랐던 것을 보정하고, 순수한 처리 효과만** 보는 방법입니다.

**이런 상황에서 씁니다**
시비 시험을 했는데, 하필 처리2 구역의 묘가 정식 당시부터 조금 더 컸다고 해봅시다.
나중에 처리2의 수량이 높게 나왔을 때, 이게 **비료 효과인지 원래 묘가 좋아서인지** 구분이 안 됩니다.
ANCOVA는 '정식 당시 묘 크기'를 **공변량**으로 넣어 그 영향을 통계적으로 걷어냅니다.

**공변량(covariate)이란?**
- 처리를 하기 **전부터** 존재하던 연속형 변수
- 예: 정식 시 묘 크기, 토양 유기물 함량, 초기 경경, 시험 전 수량
- ⚠️ 처리의 **결과로 생긴 변수**를 공변량으로 넣으면 안 됩니다(처리 효과까지 지워버림)

**결과 읽는 법**
- **원평균**: 보정 전, 실제 관측된 평균
- **보정평균(adjusted mean)**: 모든 처리구의 공변량이 **똑같았다면** 나왔을 평균 → 이 값으로 비교합니다
- 두 값의 차이가 클수록 초기 조건 차이가 컸다는 뜻입니다

**자동 점검**: 실행하면 '처리 × 공변량' 상호작용을 먼저 검사합니다.
이것이 유의하면(p<0.05) 처리구마다 공변량의 영향이 다르다는 뜻이라, ANCOVA 해석에 주의가 필요합니다.

**장점**: 공변량이 종속변수와 관련이 클수록 오차가 줄어 **검정력이 올라갑니다.**
""")
            if not cat_cols or len(num_cols) < 2:
                st.warning("그룹(범주형) 1개와 숫자형 2개(종속변수·공변량)가 필요합니다.")
            else:
                c1, c2, c3 = st.columns(3)
                gc = c1.selectbox("처리구(그룹)", cat_cols, key="an_g")
                yv = c2.selectbox("종속변수", num_cols, key="an_y")
                cov = c3.selectbox("공변량(보정할 변수)", [c for c in num_cols if c != yv], key="an_c")
                if keep_running("ancova", "ANCOVA 실행"):
                    data = df[[gc, yv, cov]].dropna()
                    m_int = ols(f"{q_ref(yv)} ~ C({q_ref(gc)}) * {q_ref(cov)}", data=data).fit()
                    a_int = sm.stats.anova_lm(m_int, typ=2)
                    ikey = [i for i in a_int.index if ":" in i]
                    p_int = a_int.loc[ikey[0], "PR(>F)"] if ikey else np.nan
                    if not np.isnan(p_int) and p_int < .05:
                        st.warning(f"⚠️ 처리×공변량 상호작용이 유의합니다 ({fmt_p(p_int)}). "
                                   "회귀기울기 동일 가정이 깨져 ANCOVA 해석에 주의가 필요합니다.")
                    else:
                        st.success(f"회귀기울기 동일 가정을 만족합니다 (상호작용 {fmt_p(p_int, digits=3)}).")
                    model = ols(safe_formula(yv, [gc], covars=[cov]), data=data).fit()
                    aov = sm.stats.anova_lm(model, typ=2)
                    st.markdown("#### 공분산분석표")
                    smart_table(aov.round(4), width="stretch")
                    tkey = f"C({q_ref(gc)})"
                    p = aov.loc[tkey, "PR(>F)"] if tkey in aov.index else aov["PR(>F)"].iloc[0]
                    grand = data[cov].mean()
                    pred = data[[gc]].drop_duplicates().assign(**{cov: grand})
                    pred["보정평균"] = model.predict(pred).round(rnd())
                    raw = data.groupby(gc)[yv].mean().round(rnd()).rename("원평균").reset_index()
                    res = raw.merge(pred[[gc, "보정평균"]], on=gc)
                    st.markdown("#### 원평균 vs 보정평균")
                    smart_table(res, width="stretch")
                    st.caption(f"보정평균은 모든 처리구의 '{cov}'가 전체 평균({grand:.2f})으로 같다고 가정했을 때의 값입니다.")
                    txt = (f"'{cov}'를 보정한 결과 처리구 간 " +
                           (f"유의한 차이가 있습니다 ({fmt_p(p, sp=True)})." if p < .05
                            else f"유의한 차이가 없습니다 ({fmt_p(p, sp=True)})."))
                    st.info("💡 " + txt)
                    fig, ax = plt.subplots(figsize=figsize())
                    for lv in data[gc].unique():
                        sub = data[data[gc] == lv]
                        ax.scatter(sub[cov], sub[yv], alpha=.7, label=str(lv))
                    ax.set_xlabel(cov); ax.set_ylabel(yv); ax.legend(fontsize=8)
                    deco(ax, f"{cov} 보정 전 관계")
                    plt.tight_layout(); png = fig_to_png(fig)
                    dl_table(res, f"{yv} 공분산분석 보정평균", "ancova7", "ancova")
                    log_action(f"ANCOVA: {gc} × {yv} (공변량 {cov})")
                    report_capture("cap_ac", f"{yv} 공분산분석", txt, res, png)
                report_button("cap_ac")

    # ---------- 비모수 ----------
    if tab_np.on:
        st.subheader("비모수 검정")
        with st.expander("ℹ️ 이 분석이 뭔가요?"): st.markdown(EXPLAIN["nonparam"])
        if not cat_cols or not num_cols: st.warning("그룹(범주형)과 측정(숫자형) 변수가 필요합니다.")
        else:
            c1, c2 = st.columns(2)
            g = c1.selectbox("그룹 변수", cat_cols, key="np_g")
            v = c2.selectbox("측정값", num_cols, key="np_v")
            if keep_running("nonparam", "비모수 검정 실행"):
                data = df[[g, v]].dropna()
                grp = [data[data[g] == x][v] for x in data[g].unique()]
                if len(grp) >= 3:
                    h, p = stats.kruskal(*grp)
                    st.write(f"**Kruskal-Wallis** (그룹 {len(grp)}개)")
                    c1, c2 = st.columns(2); c1.metric("H", f"{h:.3f}"); c2.metric("p", f"{p:.4f}")
                    txt = "Kruskal-Wallis 결과 " + ("그룹 간 유의한 차이가 있습니다." if p < .05 else "차이가 없습니다.")
                elif len(grp) == 2:
                    u, p = stats.mannwhitneyu(grp[0], grp[1])
                    st.write("**Mann-Whitney U**")
                    c1, c2 = st.columns(2); c1.metric("U", f"{u:.1f}"); c2.metric("p", f"{p:.4f}")
                    txt = "Mann-Whitney U 결과 " + ("두 그룹 간 유의한 차이가 있습니다." if p < .05 else "차이가 없습니다.")
                else: txt = ""
                st.info("💡 " + txt)
                med = data.groupby(g)[v].median().round(3).reset_index(); med.columns = [g, "중앙값"]
                smart_table(med, width="stretch")
                dl_table(med, f"{g}별 {v} 중앙값(비모수)", "np8", "np")
                report_capture("cap_np", f"{g}별 {v} 비모수 검정", txt, med, None)
            report_button("cap_np")

    # ---------- PCA ----------
    if tab_pca.on:
        st.subheader("주성분분석 (PCA)")
        with st.expander("ℹ️ 이 분석이 뭔가요?"): st.markdown(EXPLAIN["pca"])
        if len(num_cols) < 3: st.warning("숫자형 변수가 3개 이상 필요합니다.")
        else:
            feats = st.multiselect("분석할 변수", num_cols, default=num_cols, key="pca_f")
            cby = st.selectbox("색상 구분(선택)", ["(없음)"] + cat_cols, key="pca_c")
            if len(feats) >= 3 and keep_running("pca", "PCA 실행"):
                data = df[feats].dropna()
                Xs = StandardScaler().fit_transform(data)
                pca = PCA(n_components=2).fit(Xs); sc_ = pca.transform(Xs); evr = pca.explained_variance_ratio_
                txt = f"주성분 2개가 원본 정보의 {evr.sum()*100:.1f}%를 설명합니다 (PC1 {evr[0]*100:.1f}%, PC2 {evr[1]*100:.1f}%)."
                st.info("💡 " + txt)
                fig, ax = plt.subplots(figsize=figsize(h=float(st.session_state.get("fig_h",4.0))+1))
                if cby != "(없음)":
                    cats = df.loc[data.index, cby]
                    for lv in cats.unique():
                        m_ = (cats == lv).values
                        ax.scatter(sc_[m_, 0], sc_[m_, 1], label=str(lv), alpha=.7)
                    ax.legend()
                else:
                    ax.scatter(sc_[:, 0], sc_[:, 1], alpha=.7, color="#6c8ebf")
                ax.set_xlabel(f"PC1 ({evr[0]*100:.1f}%)"); ax.set_ylabel(f"PC2 ({evr[1]*100:.1f}%)")
                deco(ax, "PCA 산점도"); ax.axhline(0, color="gray", lw=.5); ax.axvline(0, color="gray", lw=.5)
                png = fig_to_png(fig)
                st.download_button("🖼️ PCA 그래프", png, "pca.png", "image/png")
                load = pd.DataFrame(pca.components_.T, columns=["PC1", "PC2"], index=feats).round(3).reset_index().rename(columns={"index": "변수"})
                smart_table(load, width="stretch")
                dl_table(load, "PCA 로딩 결과", "pca9", "pca")
                report_capture("cap_pca", "주성분분석(PCA)", txt, load, png)
            report_button("cap_pca")

    # ---------- 회귀 ----------
    if tab_reg.on:
        st.subheader("회귀분석")
        with st.expander("ℹ️ 이 분석이 뭔가요?"): st.markdown(EXPLAIN["reg"])
        rt = st.radio("분석 종류", ["단순/다중 회귀분석", "로지스틱 회귀분석"])
        if rt.startswith("단순"):
            if len(num_cols) < 2: st.warning("숫자형 변수가 2개 이상 필요합니다.")
            else:
                if st.session_state.get("lin_y") not in num_cols:
                    st.session_state["lin_y"] = (_measure_cols or num_cols)[
                        guess_idx(_measure_cols or num_cols, ["수량", "수확량", "yield"])]
                y = st.selectbox("종속변수 (Y)", num_cols, key="lin_y")
                xs = st.multiselect("독립변수 (X)", [c for c in num_cols if c != y], key="lin_x")
                if xs and keep_running("reg", "회귀분석 실행"):
                    data = df[[y]+xs].dropna()
                    model = sm.OLS(data[y], sm.add_constant(data[xs])).fit()
                    txt = f"이 모델은 '{y}'의 변동을 약 {model.rsquared*100:.1f}% 설명합니다 (R²={model.rsquared:.3f})."
                    st.info("💡 " + txt)
                    _v1_render_regression(model, y, xs)
                    coef = pd.DataFrame({"변수": model.params.index, "계수": model.params.values.round(4),
                                         "p-value": model.pvalues.values.round(4)})
                    if len(xs) >= 2:
                        try:
                            from statsmodels.stats.outliers_influence import variance_inflation_factor
                            Xv = sm.add_constant(data[xs])
                            vif = pd.DataFrame({"변수": xs,
                                "VIF": [round(variance_inflation_factor(Xv.values, i+1), 2) for i in range(len(xs))]})
                            st.markdown("**다중공선성 진단 (VIF)**")
                            smart_table(vif, width="stretch")
                            hi = vif[vif["VIF"] >= 10]["변수"].tolist()
                            if hi:
                                st.warning(f"⚠️ VIF가 10 이상인 변수: {', '.join(hi)} — "
                                           "변수들이 서로 너무 비슷해 계수 해석이 불안정합니다. 일부를 빼는 것이 좋습니다.")
                            else:
                                st.caption("VIF가 모두 10 미만이라 다중공선성 문제는 크지 않습니다.")
                        except Exception:
                            pass
                    png = None
                    if len(xs) == 1:
                        fig, ax = plt.subplots(figsize=figsize())
                        ax.scatter(data[xs[0]], data[y], alpha=.6, color=pcolor())
                        xl = np.linspace(data[xs[0]].min(), data[xs[0]].max(), 100)
                        ax.plot(xl, model.params.iloc[0]+model.params.iloc[1]*xl, color="red")
                        ax.set_xlabel(xs[0]); ax.set_ylabel(y); deco(ax, f"단순회귀: R²={model.rsquared:.3f}")
                        png = fig_to_png(fig)
                    # ---- 잔차 진단 (논문 부록·모형 타당성 확인용) ----
                    with st.expander("🔍 잔차 진단 (회귀모형이 적절한지 확인)"):
                        st.caption("**잔차**는 실제값과 예측값의 차이입니다. 회귀분석이 타당하려면 "
                                   "잔차가 특정 패턴 없이 0을 중심으로 고르게 흩어져야 합니다.")
                        resid = model.resid; fitted = model.fittedvalues
                        fg, axs = plt.subplots(1, 2, figsize=(figsize()[0]*2, figsize()[1]))
                        axs[0].scatter(fitted, resid, alpha=.6, color=pcolor())
                        axs[0].axhline(0, color="red", ls="--", lw=1)
                        axs[0].set_xlabel("예측값"); axs[0].set_ylabel("잔차")
                        deco(axs[0], "잔차 vs 예측값")
                        stats.probplot(resid, dist="norm", plot=axs[1])
                        axs[1].set_title("정규 Q-Q 도표", fontsize=11)
                        plt.tight_layout(); show_plot(fg, max_width=920); plt.close(fg)
                        try:
                            _w, _p = stats.shapiro(resid)
                            st.caption(f"잔차 정규성(Shapiro-Wilk) {fmt_p(_p, sp=True)} → "
                                       + ("만족 ✅ 모형이 적절합니다."
                                          if _p >= .05 else
                                          "위배 ⚠️ 변수 변환이나 다른 모형을 고려해 보세요."))
                        except Exception:
                            pass
                        st.caption("왼쪽 그림에서 깔때기·곡선 모양이 보이면 등분산·선형성 가정이 "
                                   "깨진 것입니다. 오른쪽 점들이 직선에 가까울수록 정규성이 좋습니다.")
                    _reg_tbl = _v1_regression_table(model, y, xs)
                    _reg_foot = reg_footnote(model, xs)
                    _reg_sent = report_sentence_reg(model, y, xs)
                    _reg_chart = (xl_chart("scatter", data[[xs[0], y]], f"단순회귀: {y} ~ {xs[0]}")
                                  if len(xs) == 1 else [])
                    _v1_copy_box("표 각주 (복사해서 표 아래에 붙이세요)", _reg_foot)
                    dl_table(_reg_tbl, f"{y} 회귀분석 결과", "reg10", "reg", xlsx_chart=_reg_chart)
                    log_action(f"회귀분석: {y} ~ {', '.join(xs)}")
                    ai_interpret_button("reg", f"{y} 회귀분석", _reg_tbl,
                                        f"R²={model.rsquared:.3f}, 모형 {fmt_p(model.f_pvalue)}. "
                                        "계수는 X가 1 증가할 때 Y의 변화량입니다. 회귀는 인과를 증명하지 않습니다.",
                                        capture_slot="cap_reg")
                    _v1_copy_box("보고서용 결과 문장", _reg_sent)
                    report_capture("cap_reg", f"{y} 회귀분석", None,
                                   blocks=[{"text": _reg_sent},
                                           {"caption": f"{y} 회귀분석 결과", "table": _reg_tbl, "image": png,
                                            "xlsx_chart": _reg_chart},
                                           {"text": _reg_foot}])
                report_button("cap_reg")
        elif rt.startswith("로지스틱"):
            if not num_cols: st.warning("숫자형 독립변수가 필요합니다.")
            else:
                y = st.selectbox("종속변수 (Y, 2범주)", df.columns.tolist(), key="log_y")
                xs = st.multiselect("독립변수 (X)", [c for c in num_cols if c != y], key="log_x")
                if xs and keep_running("logit", "로지스틱 회귀 실행"):
                    data = df[[y]+xs].dropna()
                    if data[y].nunique() != 2: st.error("종속변수는 2개의 범주여야 합니다.")
                    else:
                        yb = pd.factorize(data[y])[0]
                        clf = LogisticRegression(max_iter=1000).fit(data[xs], yb)
                        st.metric("정확도(훈련)", f"{accuracy_score(yb, clf.predict(data[xs])):.3f}")
                        coef = pd.DataFrame({"변수": xs, "계수": clf.coef_[0].round(4)})
                        smart_table(coef, width="stretch")
                        dl_table(coef, f"{y} 로지스틱 회귀", "logit11", "logit")

        # ---------- 프로빗 (LC50 / LD50) ----------
        else:
            with st.expander("ℹ️ 프로빗 분석이란?"):
                st.markdown("""
농도를 높일수록 얼마나 더 죽는지(**농도-사충률 관계**)를 분석해
**LC50**(반수치사농도) 또는 **LD50**(반수치사량)을 구하는 표준 방법입니다.

**LC50이란?** 시험 개체의 **절반(50%)이 죽는 농도**입니다.
- LC50이 **작을수록** 낮은 농도에서도 효과가 나타남 = 약효가 강하거나 해충이 민감함
- LC50이 **클수록** 많이 써야 효과가 남 = 저항성이 생겼을 가능성

**어디에 쓰나요?**
- 살충제·살균제 **감수성 검정**
- 지역별·계통별 **저항성 발달 여부** 비교
- 천연물·친환경 자재의 **살충 효과 평가**

**자료 형태** — 한 행 = 한 농도 처리

| 계통 | 농도(ppm) | 공시충수 | 사충수 |
|---|---|---|---|
| 감수성계통 | 10 | 30 | 9 |
| 감수성계통 | 20 | 30 | 16 |

**필요한 열**: 농도 · 공시충수(총 개체수) · 사충수(죽은 개체수)
**권장 조건**: 농도 **5수준 이상**, 각 농도당 30마리 내외, 사충률이 0%와 100% 사이에 골고루 분포

**결과 읽는 법**
- **LC50 / LC90**: 50%, 90%가 죽는 농도
- **95% 신뢰구간**: 두 계통의 신뢰구간이 **서로 겹치지 않으면** 감수성이 통계적으로 다르다고 봅니다
- **저항성비(RR)** = 저항성계통 LC50 ÷ 감수성계통 LC50 → 10 이상이면 저항성이 상당히 발달한 것으로 해석합니다
- **기울기**: 클수록 농도가 조금만 올라가도 사충률이 급격히 증가

⚠️ 농도는 0보다 커야 합니다(로그 변환을 사용). 무처리구(농도 0)는 제외하고, 자연사충률이 높으면 Abbott 보정을 먼저 하세요.
""")
            if len(num_cols) < 3:
                st.warning("농도·총개체수·사충수 3개의 숫자형 열이 필요합니다.")
            else:
                c1, c2, c3 = st.columns(3)
                dose = c1.selectbox("농도(처리량) 열", num_cols,
                                    index=guess_idx(num_cols, ["농도", "처리량", "dose", "conc"]), key="pb_d")
                ntot = c2.selectbox("총 개체수(공시충수) 열", num_cols,
                                    index=guess_idx(num_cols, ["공시", "총개체", "총충", "n"], 1), key="pb_n")
                nres = c3.selectbox("사충수(반응 개체수) 열", num_cols,
                                    index=guess_idx(num_cols, ["사충", "사망", "반응", "death"], 2), key="pb_r")
                grp_opts = ["(없음)"] + cat_cols
                gsel = st.selectbox("계통·약제별 구분 열 (선택)", grp_opts, key="pb_g")
                if keep_running("probit", "프로빗 분석 실행"):
                    need = [dose, ntot, nres] + ([gsel] if gsel != "(없음)" else [])
                    d0 = df[need].dropna().copy()
                    # ---------- 입력 검증 ----------
                    _err = []
                    _bad_dead = d0[pd.to_numeric(d0[nres], errors="coerce")
                                   > pd.to_numeric(d0[ntot], errors="coerce")]
                    if len(_bad_dead):
                        _err.append(f"사충수가 공시충수보다 큰 행이 {len(_bad_dead)}개 있습니다. "
                                    "입력을 확인해 주세요.")
                    if (pd.to_numeric(d0[nres], errors="coerce") < 0).any():
                        _err.append("사충수에 음수가 있습니다.")
                    if (pd.to_numeric(d0[ntot], errors="coerce") <= 0).any():
                        _err.append("공시충수가 0 이하인 행이 있습니다.")
                    if (pd.to_numeric(d0[dose], errors="coerce") <= 0).any():
                        _err.append("농도가 0 이하인 행이 있습니다(로그 변환 불가). "
                                    "무처리구(농도 0)는 제외해 주세요.")
                    if _err:
                        for _m in _err: st.error("⚠️ " + _m)
                        st.stop()
                    d0 = d0[(d0[dose] > 0) & (d0[ntot] > 0)]
                    if d0.empty:
                        st.error("농도가 0보다 크고 총 개체수가 있는 자료가 필요합니다.")
                    else:
                        groups = d0[gsel].unique() if gsel != "(없음)" else ["전체"]
                        rows, curves = [], {}
                        for g in groups:
                            sub = d0 if gsel == "(없음)" else d0[d0[gsel] == g]
                            sub = sub.copy()
                            sub["logd"] = np.log10(sub[dose].astype(float))
                            sub["dead"] = sub[nres].astype(float)
                            sub["alive"] = (sub[ntot].astype(float) - sub["dead"]).clip(lower=0)
                            _nlev = sub[dose].nunique()
                            if _nlev < 3:
                                rows.append({"구분": g, "LC50": "계산불가", "LC90": "-",
                                             "기울기": "-",
                                             "비고": f"고유 농도 {_nlev}수준(3수준 이상 필요)"})
                                continue
                            if sub["dead"].sum() == 0:
                                rows.append({"구분": g, "LC50": "계산불가", "LC90": "-",
                                             "기울기": "-", "비고": "사충 반응이 전혀 없음"})
                                continue
                            if (sub["alive"] <= 0).all():
                                rows.append({"구분": g, "LC50": "계산불가", "LC90": "-",
                                             "기울기": "-", "비고": "모든 농도에서 100% 사충"})
                                continue
                            try:
                                X = sm.add_constant(sub[["logd"]])
                                gm = sm.GLM(sub[["dead", "alive"]], X,
                                            family=sm.families.Binomial(
                                                link=sm.families.links.Probit())).fit()
                                b0, b1 = float(gm.params.iloc[0]), float(gm.params.iloc[1])
                                if abs(b1) < 1e-9:
                                    raise ValueError("기울기가 0에 가까움")
                                lc50 = 10 ** (-b0 / b1)
                                lc90 = 10 ** ((stats.norm.ppf(0.90) - b0) / b1)
                                # LC50 신뢰구간 — 절편·기울기의 공분산을 반영 (델타법)
                                _cov = np.asarray(gm.cov_params())
                                v00, v01, v11 = float(_cov[0, 0]), float(_cov[0, 1]), float(_cov[1, 1])
                                m = -b0 / b1
                                # Var(m) = (1/b1²)·V00 + (2·b0/b1³)·V01 + (b0²/b1⁴)·V11
                                var_m = (v00 / b1**2) + (2 * b0 * v01 / b1**3) + (b0**2 * v11 / b1**4)
                                se_m = float(np.sqrt(var_m)) if var_m > 0 else float("nan")
                                if np.isnan(se_m):
                                    lo = hi = float("nan")
                                else:
                                    lo, hi = 10 ** (m - 1.96*se_m), 10 ** (m + 1.96*se_m)
                                rows.append({"구분": g, "LC50": round(lc50, 3),
                                             "95% 하한": round(lo, 3), "95% 상한": round(hi, 3),
                                             "LC90": round(lc90, 3), "기울기": round(b1, 3),
                                             "n(농도수)": len(sub)})
                                curves[g] = (sub, b0, b1, lc50)
                            except Exception as ex:
                                rows.append({"구분": g, "LC50": "계산불가", "LC90": "-",
                                             "기울기": "-", "비고": str(ex)[:30]})
                        res = pd.DataFrame(rows)
                        st.markdown("#### 프로빗 분석 결과")
                        smart_table(res, width="stretch")
                        st.caption("LC50이 작을수록 낮은 농도에서 효과가 나타남을 의미합니다. "
                                   "95% 신뢰구간이 서로 겹치지 않으면 두 계통·약제의 감수성이 다르다고 봅니다.")
                        if curves:
                            fig, ax = plt.subplots(figsize=figsize())
                            for g, (sub, b0, b1, lc50) in curves.items():
                                obs = sub["dead"] / (sub["dead"] + sub["alive"]) * 100
                                ax.scatter(sub[dose], obs, alpha=.7, label=f"{g} (관측)")
                                xs = np.linspace(sub[dose].min()*0.8, sub[dose].max()*1.2, 200)
                                ys = stats.norm.cdf(b0 + b1*np.log10(xs)) * 100
                                ax.plot(xs, ys, lw=2, label=f"{g} LC50={lc50:.2f}")
                            ax.axhline(50, color="gray", ls="--", lw=.8)
                            ax.set_xscale("log"); ax.set_xlabel(f"{dose} (로그 눈금)")
                            ax.set_ylabel("사충률(%)"); ax.set_ylim(-5, 105)
                            ax.legend(fontsize=7); deco(ax, "농도-사충률 곡선")
                            plt.tight_layout(); png = fig_to_png(fig)
                            st.download_button("🖼️ 그래프 다운로드", png, "probit.png", "image/png")
                        else:
                            png = None
                        ok = res[res["LC50"] != "계산불가"]
                        txt = ("프로빗 분석 결과 LC50은 " +
                               ", ".join(f"{r['구분']} {r['LC50']}" for _, r in ok.iterrows()) +
                               " 입니다." if len(ok) else "LC50을 계산할 수 있는 자료가 없습니다.")
                        st.info("💡 " + txt)
                        dl_table(res, "프로빗 분석 (LC50/LD50)", "probit12", "probit")
                        log_action("프로빗 분석(LC50) 실행")
                        report_capture("cap_pr", "프로빗 분석(LC50)", txt, res, png)
                        ai_interpret_button("pr", "프로빗 분석(LC50/LD50)", res, "LC50이 작을수록 약효가 강하거나 해충이 민감합니다.", capture_slot="cap_pr")
                report_button("cap_pr")

    # ---------- 머신러닝 ----------
    if tab_ml.on:
        st.subheader("머신러닝")
        with st.expander("ℹ️ 이 분석이 뭔가요?"): st.markdown(EXPLAIN["ml"])
        if len(num_cols) < 2: st.warning("숫자형 변수가 2개 이상 필요합니다.")
        else:
            allc = df.columns.tolist()
            _ml_default = (_measure_cols or num_cols)[-1] if num_cols else None
            tgt = st.selectbox("예측 대상(Y)", allc,
                               index=(allc.index(_ml_default) if _ml_default in allc else 0), key="ml_y")
            fts = st.multiselect("입력 변수(X)", [c for c in num_cols if c != tgt], key="ml_x")
            y_is_num = tgt in num_cols
            n_uni = int(df[tgt].nunique())
            auto_cls = (not y_is_num) or n_uni <= 10
            task = st.radio("문제 유형", ["회귀(연속값 예측)", "분류(범주 예측)"],
                            index=1 if auto_cls else 0)
            if not y_is_num:
                st.info(f"'{tgt}'은 문자(범주)형이므로 **분류**만 가능합니다.")
            elif n_uni <= 10:
                st.caption(f"'{tgt}'의 값이 {n_uni}종류뿐이라 분류가 자연스럽습니다.")
            _reg_algos = [
                "랜덤포레스트", "Extra Trees", "그래디언트부스팅", "히스토그램 부스팅",
                "AdaBoost", "의사결정나무", "SVM(RBF)", "KNN", "Ridge", "Lasso", "ElasticNet"]
            _clf_algos = [
                "랜덤포레스트", "Extra Trees", "그래디언트부스팅", "히스토그램 부스팅",
                "AdaBoost", "의사결정나무", "SVM(RBF)", "KNN", "로지스틱 회귀", "GaussianNB"]
            _is_reg_choice = task.startswith("회귀")
            _algo_options = _reg_algos if _is_reg_choice else _clf_algos
            if st.session_state.get("ml_algo") not in _algo_options:
                st.session_state["ml_algo"] = "랜덤포레스트"
            algo = "랜덤포레스트"
            st.caption("기본 예측모형: **랜덤포레스트**")
            with st.expander("고급 · 다른 예측 알고리즘 사용", expanded=False):
                algo = st.selectbox("알고리즘", _algo_options, key="ml_algo")
            _algo_help = {
                "랜덤포레스트": "여러 나무의 결과를 평균/투표합니다. 비선형 관계에 강하고 기본 선택으로 무난합니다.",
                "Extra Trees": "랜덤포레스트보다 분할을 더 무작위화한 앙상블입니다. 빠르고 변수 관계가 복잡할 때 유용합니다.",
                "그래디언트부스팅": "앞선 모형의 오차를 순차적으로 보완합니다. 중소형 표형 데이터에서 강한 편입니다.",
                "히스토그램 부스팅": "연속값을 구간화해 빠르게 부스팅합니다. 관측치가 많은 표형 자료에 유리합니다.",
                "AdaBoost": "틀린 관측치에 더 가중치를 주며 약한 모형을 결합합니다.",
                "의사결정나무": "규칙을 나무 형태로 나눠 설명하기 쉽지만 과적합에 주의해야 합니다.",
                "SVM(RBF)": "비선형 경계를 학습합니다. 변수 단위의 영향을 줄이기 위해 자동 표준화합니다.",
                "KNN": "비슷한 관측치 주변의 값을 이용합니다. 자동 표준화하며 표본이 너무 적으면 불안정할 수 있습니다.",
                "Ridge": "다중공선성이 있는 여러 연속형 변수의 회귀에 유용한 L2 규제 선형모형입니다.",
                "Lasso": "덜 중요한 변수의 계수를 0으로 줄일 수 있는 L1 규제 회귀입니다.",
                "ElasticNet": "Ridge와 Lasso를 함께 사용하는 규제 회귀입니다.",
                "로지스틱 회귀": "분류확률을 추정하는 기본 선형 분류모형입니다. 자동 표준화합니다.",
                "GaussianNB": "각 변수의 분포를 이용하는 매우 빠른 확률 분류모형입니다.",
            }
            st.caption("💡 " + _algo_help.get(algo, ""))

            if fts and keep_running("ml", "모델 학습"):
                is_reg = task.startswith("회귀")
                if is_reg and not y_is_num:
                    st.error(f"⚠️ '{tgt}'은 문자(범주)형이라 회귀 예측을 할 수 없습니다. "
                             "문제 유형을 '분류(범주 예측)'로 바꾸거나 숫자형 열을 선택하세요.")
                    st.stop()
                data = df[[tgt] + fts].dropna().copy()
                if len(data) < 10:
                    st.error("⚠️ 결측치를 제외한 학습자료가 10개 미만입니다. 머신러닝 결과를 신뢰하기 어렵습니다.")
                    st.stop()
                if len(data) < 30:
                    st.warning(f"⚠️ 사용 가능한 자료가 {len(data)}개뿐입니다. 머신러닝 결과는 탐색적으로만 해석하세요.")
                X = data[fts].astype(float)

                if is_reg:
                    y = pd.to_numeric(data[tgt], errors="coerce")
                    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=.3, random_state=0)
                    _kn = max(1, min(5, len(Xtr)))
                    mreg = {
                        "랜덤포레스트": RandomForestRegressor(n_estimators=300, random_state=0),
                        "Extra Trees": ExtraTreesRegressor(n_estimators=300, random_state=0),
                        "그래디언트부스팅": GradientBoostingRegressor(random_state=0),
                        "히스토그램 부스팅": HistGradientBoostingRegressor(random_state=0),
                        "AdaBoost": AdaBoostRegressor(n_estimators=200, random_state=0),
                        "의사결정나무": DecisionTreeRegressor(random_state=0),
                        "SVM(RBF)": Pipeline([("scale", StandardScaler()), ("model", SVR(kernel="rbf"))]),
                        "KNN": Pipeline([("scale", StandardScaler()), ("model", KNeighborsRegressor(n_neighbors=_kn))]),
                        "Ridge": Pipeline([("scale", StandardScaler()), ("model", Ridge(alpha=1.0))]),
                        "Lasso": Pipeline([("scale", StandardScaler()), ("model", Lasso(alpha=0.01, max_iter=5000))]),
                        "ElasticNet": Pipeline([("scale", StandardScaler()), ("model", ElasticNet(alpha=0.01, l1_ratio=0.5, max_iter=5000))]),
                    }
                    model = mreg[algo].fit(Xtr, ytr)
                    pred = model.predict(Xte)
                    s_ = r2_score(yte, pred)
                    _mae = float(np.mean(np.abs(np.asarray(yte) - pred)))
                    _rmse = float(np.sqrt(np.mean((np.asarray(yte) - pred) ** 2)))
                    _unit = _v1_unit_of(tgt)
                    _grade, _gmsg = ml_grade(s_, True)
                    _m1, _m2, _m3 = st.columns(3)
                    _m1.metric("R² (테스트)", f"{s_:.3f}", help="1에 가까울수록 예측이 정확합니다.")
                    _m2.metric("평균 오차 (MAE)", f"±{_mae:,.3g}{(' ' + _unit) if _unit else ''}",
                               help="예측값이 실제값과 평균적으로 이만큼 차이 납니다.")
                    _m3.metric("예측력", _grade)
                    st.caption(f"💡 {_gmsg}  (참고 기준: R² 0.7 이상 좋음 · 0.5~0.7 보통 · 0.5 미만 약함)")
                    txt = f"[{algo}] 테스트 R²는 {s_:.3f}입니다."
                    _baseline = None
                    _saved_classes = None
                else:
                    y_codes, y_levels = pd.factorize(data[tgt])
                    y = pd.Series(y_codes, index=data.index)
                    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=.3, random_state=0)
                    _kn = max(1, min(5, len(Xtr)))
                    mclf = {
                        "랜덤포레스트": RandomForestClassifier(n_estimators=300, random_state=0),
                        "Extra Trees": ExtraTreesClassifier(n_estimators=300, random_state=0),
                        "그래디언트부스팅": GradientBoostingClassifier(random_state=0),
                        "히스토그램 부스팅": HistGradientBoostingClassifier(random_state=0),
                        "AdaBoost": AdaBoostClassifier(n_estimators=200, random_state=0),
                        "의사결정나무": DecisionTreeClassifier(random_state=0),
                        "SVM(RBF)": Pipeline([("scale", StandardScaler()), ("model", SVC(kernel="rbf", probability=True, random_state=0))]),
                        "KNN": Pipeline([("scale", StandardScaler()), ("model", KNeighborsClassifier(n_neighbors=_kn))]),
                        "로지스틱 회귀": Pipeline([("scale", StandardScaler()), ("model", LogisticRegression(max_iter=3000, random_state=0))]),
                        "GaussianNB": GaussianNB(),
                    }
                    model = mclf[algo].fit(Xtr, ytr)
                    pred = model.predict(Xte)
                    s_ = accuracy_score(yte, pred)
                    _baseline = float(pd.Series(ytr).value_counts(normalize=True).max()) if len(ytr) else None
                    _mae = _rmse = None
                    _grade, _gmsg = ml_grade(s_, False)
                    _m1, _m2 = st.columns(2)
                    _m1.metric("정확도 (테스트)", f"{s_:.3f}")
                    _m2.metric("예측력", _grade)
                    st.caption(f"💡 {_gmsg}  (참고: 가장 많은 범주로만 찍어도 정확도 "
                               f"{(_baseline or 0)*100:.1f}% — 이보다 높아야 의미가 있습니다)")
                    txt = f"[{algo}] 테스트 정확도는 {s_:.3f}입니다."
                    _saved_classes = list(y_levels)

                # 모든 알고리즘에서 가능한 한 변수 중요도/영향도를 제공한다.
                # 트리계열은 내장 중요도, 선형계열은 계수 절댓값, 그 외는 테스트셋 permutation importance를 사용한다.
                png, imp = None, None
                _base_model = model.named_steps.get("model") if isinstance(model, Pipeline) else model
                _imp_vals = None
                _imp_method = None
                if hasattr(_base_model, "feature_importances_"):
                    _imp_vals = np.asarray(_base_model.feature_importances_, dtype=float)
                    _imp_method = "모형 내장 중요도"
                elif hasattr(_base_model, "coef_"):
                    _coef = np.asarray(_base_model.coef_, dtype=float)
                    _imp_vals = np.abs(_coef).mean(axis=0) if _coef.ndim > 1 else np.abs(_coef)
                    _imp_method = "표준화 계수 절댓값"
                else:
                    try:
                        _perm = permutation_importance(model, Xte, yte, n_repeats=12, random_state=0,
                                                       scoring=("r2" if is_reg else "accuracy"))
                        _imp_vals = np.clip(np.asarray(_perm.importances_mean, dtype=float), 0, None)
                        _imp_method = "순열 중요도"
                    except Exception:
                        _imp_vals = None

                if _imp_vals is not None and len(_imp_vals) == len(fts):
                    imp = (pd.DataFrame({"변수": fts, "중요도": np.round(_imp_vals, 4)})
                           .sort_values("중요도", ascending=False).reset_index(drop=True))
                    if len(imp) and float(imp["중요도"].max()) > 0:
                        st.info(f"💡 [{algo}] {_imp_method} 기준 가장 영향이 큰 변수는 **'{imp.iloc[0]['변수']}'** 입니다.")
                    else:
                        st.info(f"💡 [{algo}] {_imp_method}를 계산했지만 변수 간 중요도 차이가 거의 없었습니다.")
                    fig, ax = plt.subplots(figsize=figsize())
                    _vals = imp["중요도"].astype(float).to_numpy()
                    _bars = ax.barh(imp["변수"], _vals, color=bar_colors(values=_vals.tolist()))
                    ax.invert_yaxis()
                    _vmax = float(np.nanmax(_vals)) if len(_vals) else 0.0
                    _pad = (_vmax * 0.025) if _vmax > 0 else 0.01
                    for _bar, _v in zip(_bars, _vals):
                        ax.text(float(_v) + _pad, _bar.get_y() + _bar.get_height() / 2,
                                f"{float(_v):.3f}", va="center", ha="left", fontsize=9,
                                fontweight="bold", color="#33383d", clip_on=False)
                    if _vmax > 0: ax.set_xlim(0, _vmax * 1.18)
                    deco(ax, f"변수 중요도 ({algo})")
                    png = fig_to_png(fig)
                    st.caption(f"※ 중요도 산출 방식: {_imp_method}. 알고리즘 간 중요도 값의 절대크기를 직접 비교하지 마세요.")
                    dl_table(imp, f"{tgt} 예측 변수 중요도", "ml13", "ml",
                             xlsx_chart=xl_chart("barh", imp, f"변수 중요도 ({algo})"))
                else:
                    st.info("💡 " + txt)

                _ml_sent = report_sentence_ml(
                    tgt, algo, is_reg, s_, len(Xtr), len(Xte), mae=_mae, rmse=_rmse,
                    top_vars=(imp["변수"].astype(str).tolist() if imp is not None and len(imp)
                              and float(imp["중요도"].max()) > 0 else None),
                    baseline=_baseline)
                log_action(f"머신러닝 예측: {tgt} ({algo})")
                ai_interpret_button("ml", f"{tgt} 예측 머신러닝({algo})",
                                    imp if imp is not None else pd.DataFrame({"지표": ["점수"], "값": [s_]}),
                                    f"{'R²' if is_reg else '정확도'}={s_:.3f}, 학습 {len(Xtr)}개·검증 {len(Xte)}개. "
                                    "표본이 적으면 결과가 불안정하다는 점과, 변수 중요도는 인과가 아니라는 점을 함께 언급하세요.",
                                    capture_slot="cap_ml")
                _v1_copy_box("보고서용 결과 문장", _ml_sent)
                report_capture("cap_ml", f"{tgt} 예측 머신러닝({algo})", None,
                               blocks=[{"text": _ml_sent},
                                       {"caption": f"{tgt} 예측 변수 중요도", "table": imp, "image": png,
                                        "xlsx_chart": (xl_chart("barh", imp, f"변수 중요도 ({algo})")
                                                       if imp is not None else [])}])
                st.session_state["ml_model"] = {
                    "model": model, "feats": fts, "target": tgt, "is_reg": is_reg,
                    "algo": algo, "classes": _saved_classes,
                    "ranges": {f: (float(data[f].min()), float(data[f].max()), float(data[f].mean())) for f in fts}}
            report_button("cap_ml")

            # ---- 새 데이터로 실제 예측 ----
            saved = st.session_state.get("ml_model")
            if saved:
                st.divider()
                st.markdown("#### 🔮 새 데이터로 예측하기")
                st.caption(f"학습된 [{saved['algo']}] 모델로 '{saved['target']}'을(를) 예측합니다. "
                           "아래에 값을 입력하세요.")
                pmode = st.radio("입력 방식", ["직접 입력", "엑셀/CSV 업로드"], horizontal=True, key="ml_pmode")
                if pmode == "직접 입력":
                    vals = {}
                    pcols = st.columns(min(3, len(saved["feats"])))
                    for i, f in enumerate(saved["feats"]):
                        lo, hi, mean = saved["ranges"][f]
                        with pcols[i % len(pcols)]:
                            vals[f] = st.number_input(f, value=round(mean, 2),
                                                      help=f"학습 데이터 범위: {lo:.1f} ~ {hi:.1f}",
                                                      key=f"pv_{f}")
                    if st.button("예측 실행", key="ml_predict1"):
                        Xnew = pd.DataFrame([vals])[saved["feats"]]
                        pred = saved["model"].predict(Xnew)[0]
                        oob = [f for f in saved["feats"]
                               if not (saved["ranges"][f][0] <= vals[f] <= saved["ranges"][f][1])]
                        if saved["is_reg"]:
                            st.success(f"### 예측 결과: {saved['target']} ≈ **{pred:.2f}**")
                        else:
                            label = saved["classes"][int(pred)] if saved["classes"] else pred
                            st.success(f"### 예측 결과: {saved['target']} = **{label}**")
                            m = saved["model"]
                            if hasattr(m, "predict_proba"):
                                proba = m.predict_proba(Xnew)[0]
                                pr = pd.DataFrame({"분류": saved["classes"],
                                                   "확률(%)": (proba*100).round(1)}).sort_values("확률(%)", ascending=False)
                                smart_table(pr, width="stretch")
                        if oob:
                            st.warning(f"⚠️ {', '.join(oob)} 값이 학습 데이터 범위를 벗어났습니다. "
                                       "범위 밖 예측은 신뢰도가 떨어질 수 있어요.")
                        log_action(f"머신러닝 예측: {saved['target']}")
                else:
                    st.caption(f"예측할 파일에 **{', '.join(saved['feats'])}** 열이 있어야 합니다.")
                    pf = st.file_uploader("예측할 데이터 (xlsx/csv)", type=["xlsx", "csv"], key="ml_pf")
                    if pf is not None:
                        newdf = pd.read_csv(pf) if pf.name.endswith(".csv") else pd.read_excel(pf)
                        miss = [f for f in saved["feats"] if f not in newdf.columns]
                        if miss:
                            st.error(f"필요한 열이 없습니다: {', '.join(miss)}")
                        elif st.button("일괄 예측 실행", key="ml_predict2"):
                            Xnew = newdf[saved["feats"]].dropna()
                            preds = saved["model"].predict(Xnew)
                            out = newdf.loc[Xnew.index].copy()
                            if saved["is_reg"]:
                                out[f"{saved['target']}_예측"] = np.round(preds, 2)
                            else:
                                out[f"{saved['target']}_예측"] = [saved["classes"][int(p)]
                                                                if saved["classes"] else p for p in preds]
                            st.success(f"{len(out)}건 예측 완료!")
                            smart_table(out, width="stretch")
                            csv = out.to_csv(index=False).encode("utf-8-sig")
                            st.download_button("📥 예측 결과 CSV 다운로드", csv, "예측결과.csv", key="ml_dlpred")
                            log_action(f"머신러닝 일괄 예측: {len(out)}건")

    # ---------- AI 도우미 ----------

# ================================================================ AI 도우미
elif menu == "🧠 AI 도우미":
    st.subheader("🧠 AI 도우미")
    render_ai_connection_settings()
    if st.session_state.get("api_key"):
        st.success("AI가 연결되어 있습니다. 오른쪽 아래 **💬 AI에게 물어보기**에서도 같은 연결을 사용합니다.")
    else:
        st.info("AI 기능은 선택 사항입니다. API 키가 없어도 통계분석·설문·보고서는 사용할 수 있습니다.")
    if df is None:
        st.markdown("### 데이터 없이 질문하기")
        _gq = st.text_area("통계나 앱 사용법을 물어보세요", key="ai_free_q",
                           placeholder="예) 난괴법 3반복 데이터는 엑셀을 어떻게 작성해?")
        _new = None
        if st.button("AI에게 질문", type="primary", key="ai_free_btn") and _gq.strip():
            if not st.session_state.get("api_key"):
                st.warning("위 AI 연결 설정에서 API 키를 먼저 연결해 주세요.")
            else:
                _new = "농업연구 통계 초보자에게 쉽고 정확하게 한국어로 답하세요. 질문: " + _gq
        _ans = ai_job_run("free", _new)
        if _ans:
            st.markdown(_ans)
            ai_disclaimer()
        st.stop()
    amode = st.radio("기능", ["결과를 자연어로 질문", "📝 데이터 자동 요약(초록 초안)",
                             "연구계획서 기반 통계 추천"], key="ai_mode")
    summary = build_data_overview(df)
    # 처리구·품종별 실제 평균을 함께 전달해 AI가 전체 describe()만 보고 추측하지 않게 한다.
    _general_profiles = build_group_profiles(df)

    if amode.startswith("📝"):
        st.caption("현재 데이터의 특징을 AI가 살펴보고, 연구 초록(Abstract) 초안이나 핵심 요약을 만들어 줍니다.")
        purpose = st.text_input("연구 목적/배경 (한 줄, 선택)",
                                placeholder="예) 고추 신품종의 생육·수량 특성 비교")
        want = st.radio("형태", ["핵심 요약 (불릿)", "결과 요약 문단"], horizontal=True)
        _new = None
        if st.button("AI 요약 생성"):
            fmt = {"핵심 요약 (불릿)": "핵심 발견을 불릿 5개 이내로",
                   "연구 초록 초안": "학술논문 초록 형식(목적·방법·결과·결론)으로 200자 내외",
                   "결과 요약 문단": "결과를 서술한 한 문단으로"}[want]
            _new = (f"연구 목적: {purpose or '(미기재)'}\n\n{summary}\n\n"
                    f"[처리·품종별 요약]\n{_general_profiles}\n\n"
                    f"위 데이터를 {fmt} 한국어로 정리해 주세요. 데이터에 근거한 내용만 쓰고, "
                    "통계 검정을 따로 하진 않았으니 단정적 유의성 주장은 피하세요.")
            log_action("AI 데이터 요약 생성")
        _ans = ai_job_run("summary", _new, max_tokens=1000, spinner="AI가 데이터를 살펴보는 중...")
        if _ans:
            st.markdown(_ans)
            ai_disclaimer()
    elif amode.startswith("결과"):
        with st.expander("💬 이렇게 물어보세요 (예시)"):
            st.markdown("""
- 처리구별 수량 차이를 보고서에 쓸 문장으로 정리해줘
- 이 데이터로 어떤 분석을 하면 좋을지 알려줘
- 유의성 문자 a, b, c가 무슨 뜻인지 쉽게 설명해줘
- 상관계수 0.93이면 어느 정도로 강한 관계인지 설명해줘
- 이 결과를 비전공자인 상사에게 보고할 때 어떻게 말하면 좋을까?
- 처리2가 가장 좋은 이유를 데이터 근거로 설명해줘
""")
        q = st.text_area("궁금한 점", key="ai_ask_q", placeholder="예) 처리구별 수량 차이를 쉽게 설명해줘")
        _new = None
        if st.button("AI에게 물어보기", key="ai_ask_btn"):
            if not q.strip():
                st.warning("궁금한 점을 먼저 적어 주세요.")
            else:
                _question_profiles = build_group_profiles(df, question=q)
                _new = ("당신은 농업연구사를 돕는 통계 전문가입니다. 아래 실제 데이터 요약만 참고해 "
                        "질문에 쉽고 정확하게 한국어로 답해주세요. 입력에 없는 수치나 유의성을 "
                        f"추측하지 마세요.\n\n{summary}\n\n"
                        f"[질문 관련 처리·품종별 요약]\n{_question_profiles}\n\n질문: {q}")
        _ans = ai_job_run("ask", _new, spinner="AI가 분석 중...")
        if _ans:
            st.markdown(_ans)
            ai_disclaimer()
    else:
        with st.expander("💬 이렇게 입력하세요 (예시)"):
            st.markdown("""
연구계획서의 **시험 목적·처리 내용·반복 수·조사 항목**을 붙여넣으면 가장 정확합니다.

> 예시) 고추 '청양' 품종을 대상으로 질소 시비량 4수준(0, 10, 20, 30kg/10a)을 난괴법 3반복으로 배치하여
> 초장, 착과수, 상품수량, 당도를 조사하고자 함. 시험은 2개 지역(영양, 안동)에서 동시 수행함.
""")
        plan_file = st.file_uploader("📎 연구계획서 파일 첨부 (선택)",
                                     type=["txt", "md", "csv", "xlsx", "hwpx", "pdf", "docx"],
                                     key="plan_file")
        file_text = ""
        if plan_file is not None:
            file_text = read_uploaded_text(plan_file)
            if file_text.startswith("⚠️"):
                st.warning(file_text); file_text = ""
            else:
                st.success(f"'{plan_file.name}'에서 {len(file_text):,}자를 읽었습니다.")
                with st.expander("읽어온 내용 확인"):
                    st.text(file_text[:2000] + ("..." if len(file_text) > 2000 else ""))
        plan = st.text_area("연구계획서 내용 (직접 입력하거나 위 파일 첨부)",
                            value=file_text, height=180,
                            placeholder="시험 목적, 처리 내용, 반복 수, 조사 항목 등")
        _new = None
        if st.button("통계 방법 추천받기"):
            _new = ("당신은 농업 실험설계·통계 전문가입니다. 아래 연구계획서와 데이터 구조를 보고 "
                    "가장 적합한 통계 분석 방법(분산분석 종류, 사후검정, 상관/회귀, 비모수 등)을 "
                    f"이유와 함께 한국어로 단계별 추천해주세요.\n\n[데이터]\n{summary}\n\n[연구계획서]\n{plan}")
            log_action("AI 연구계획서 기반 통계 추천")
        _ans = ai_job_run("plan", _new, max_tokens=1300, spinner="AI가 연구계획을 분석 중...")
        if _ans:
            st.markdown(_ans)
            ai_disclaimer()
    st.caption("※ AI 응답은 참고용이며, 호출 시 사용량만큼 소액 비용이 발생할 수 있어요.")

# ================================================================ 설문 분석
elif menu == "📋 설문조사 분석":
    st.title("📋 설문조사 분석")
    with st.expander("ℹ️ 설문 분석이 뭔가요?"): st.markdown(EXPLAIN["survey"])
    stype = st.radio("분석 유형", ["🤖 자동 인식 (문항 유형 자동 판별)", "📊 리커트 척도(점수형)",
                                 "🔘 객관식(단일선택)", "☑️ 다중응답",
                                 "✍️ 주관식(서술형)", "🔀 교차분석(집단 비교)"],
                     key="svy_type")

    # ---------- 자동 인식 ----------
    if stype.startswith("🤖"):
        st.caption("각 열의 값을 보고 문항 유형을 자동으로 판별한 뒤, 유형에 맞는 그래프와 분석을 한 번에 만듭니다.")
        det = detect_question_types(df)
        st.markdown("#### 📋 문항 유형 자동 판별 결과")
        smart_table(det, width="stretch", hide_index=True)
        likert = det[det["추정 유형"] == "리커트 척도"]["열 이름"].tolist()
        single = det[det["추정 유형"] == "객관식(단일선택)"]["열 이름"].tolist()
        multi = det[det["추정 유형"] == "다중응답"]["열 이름"].tolist()
        openq = det[det["추정 유형"] == "주관식(서술형)"]["열 이름"].tolist()

        # 판별이 틀렸을 때 사용자가 직접 유형을 옮길 수 있게 한다.
        # 데이터가 바뀌면(새 파일 업로드 등) 자동판별 값으로 초기화한다.
        _dsig = dataframe_signature(df)
        if st.session_state.get("_svy_auto_sig") != _dsig:
            st.session_state["_svy_auto_sig"] = _dsig
            st.session_state["_svy_likert_ov"] = likert
            st.session_state["_svy_single_ov"] = single
            st.session_state["_svy_multi_ov"] = multi
            st.session_state["_svy_openq_ov"] = openq
        with st.expander("🛠️ 판별이 잘못됐으면 여기서 유형을 고쳐 주세요", expanded=False):
            st.caption("예: 이름에 '의향'이 들어간 문항이 실제로는 5점 척도인데 객관식으로 분류된 경우 "
                       "여기서 '📊 리커트 척도'로 옮기면 됩니다. 응답자 ID·빈 열은 목록에서 빠집니다.")
            _id_like = det[det["추정 유형"].isin(["응답자 ID", "빈 열"])]["열 이름"].tolist()
            _classifiable = [c for c in df.columns if c not in _id_like]
            ov1, ov2 = st.columns(2)
            likert = ov1.multiselect("📊 리커트 척도", _classifiable, key="_svy_likert_ov")
            single = ov2.multiselect("🔘 객관식(단일선택)", _classifiable, key="_svy_single_ov")
            ov3, ov4 = st.columns(2)
            multi = ov3.multiselect("☑️ 다중응답", _classifiable, key="_svy_multi_ov")
            openq = ov4.multiselect("✍️ 주관식(서술형)", _classifiable, key="_svy_openq_ov")
            _dup = [c for c, n in Counter(likert + single + multi + openq).items() if n > 1]
            if _dup:
                st.warning("⚠️ 같은 열이 두 유형 이상에 겹쳐 선택되었습니다: " + ", ".join(_dup)
                           + " — 그래프가 중복으로 나올 수 있으니 한 곳에서만 고르세요.")

        # 객관식이라고 전부 '응답자 특성'인 것은 아니다. 성별·경력·지역처럼 응답자를
        # 설명하는 항목만 응답자 특성으로 묶고, '가장 효과적인 기술'처럼 내용을 묻는
        # 객관식 문항은 '문항별 응답 결과'로 따로 정리한다.
        _DEMO_HINT = ["성별", "연령", "나이", "경력", "학력", "소득", "지역", "시군",
                      "시도", "소속", "직업", "직급", "구분", "유형", "규모", "면적",
                      "거주", "응답자", "농가", "재배형태", "작목"]
        if st.session_state.get("_svy_demo_sig") != _dsig:
            st.session_state["_svy_demo_sig"] = _dsig
            st.session_state["_svy_demo_ov"] = [c for c in single
                                                if any(k in str(c) for k in _DEMO_HINT)]
        # 위 '유형 고치기'에서 객관식 목록이 바뀌면 없는 열이 남지 않도록 정리한다.
        st.session_state["_svy_demo_ov"] = [
            c for c in st.session_state.get("_svy_demo_ov", []) if c in single]
        demo_q = st.multiselect(
            "👥 객관식 중 '응답자 특성'인 항목", single, key="_svy_demo_ov",
            help="성별·경력·지역처럼 응답자를 설명하는 항목만 고르세요. "
                 "여기서 뺀 객관식은 '문항별 응답 결과'로 따로 정리됩니다.")
        demo_q = [c for c in single if c in demo_q]
        single_q = [c for c in single if c not in demo_q]

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("📊 리커트", len(likert)); c2.metric("👥 응답자 특성", len(demo_q))
        c3.metric("🔘 객관식 문항", len(single_q))
        c4.metric("☑️ 다중응답", len(multi)); c5.metric("✍️ 주관식", len(openq))
        chart_style = st.radio("응답자 특성 그래프", ["도넛", "원형", "막대"],
                               horizontal=True, key="svy_chart")
        st.caption("판별이 잘못되었으면 위 탭에서 유형을 직접 골라 분석하세요.")

        if keep_running("autoan", "🚀 자동 분석 실행"):
            rep_blocks = []

            # 1) 응답자 특성 · 객관식 문항 (원형/도넛) — 같은 그리기 방식을 나눠서 쓴다
            def _draw_choice(cols_list, heading, cap_prefix):
                if not cols_list:
                    return
                st.markdown(heading)
                cols_ = st.columns(min(3, len(cols_list)))
                for i, c in enumerate(cols_list):
                    vc = df[c].value_counts()
                    with cols_[i % len(cols_)]:
                        if chart_style == "막대":
                            fig, ax = plt.subplots(figsize=(4.2, 3.4))
                            # 설문 화면은 문항별 색 구분(_survey_palette)이 이미 있어
                            # 그대로 둔다. 값 표시·격자 정리는 아래 deco 가 맡는다.
                            _bs = ax.bar(vc.index.astype(str), vc.values,
                                         color=_survey_palette(len(vc)), width=.62,
                                         edgecolor="white", linewidth=1.0)
                            for _b, _v in zip(_bs, vc.values):
                                ax.text(_b.get_x()+_b.get_width()/2, _v,
                                        f"{_v}명\n({_v/vc.sum()*100:.1f}%)",
                                        ha="center", va="bottom", fontsize=8, color="#333")
                            ax.set_ylim(0, max(vc.values)*1.3)
                            ax.set_ylabel("응답자 수(명)", fontsize=9)
                            for _s in ("top", "right"):
                                ax.spines[_s].set_visible(False)
                            ax.spines["left"].set_color("#bbb")
                            ax.spines["bottom"].set_color("#bbb")
                            ax.tick_params(colors="#555", labelsize=8)
                            ax.set_title(f"{c}  (n={int(vc.sum())})", fontsize=11,
                                         fontweight="bold", color="#333")
                            plt.xticks(rotation=20, fontsize=8)
                            plt.tight_layout()
                        else:
                            fig = pie_chart(vc, c, donut=(chart_style == "도넛"))
                        show_plot(fig); plt.close(fig)
                        _t = pd.DataFrame({c: vc.index.astype(str), "빈도(명)": vc.values,
                                           "비율(%)": (vc.values/vc.sum()*100).round(1)})
                        smart_table(_t, width="stretch", hide_index=True)
                        rep_blocks.append({"caption": f"{cap_prefix} - {c}",
                                           "table": _t,
                                           "image": fig_to_png(fig, show=False)})

            _draw_choice(demo_q, "## 👥 응답자 특성", "응답자 특성")
            _draw_choice(single_q, "## 🔘 문항별 응답 결과", "문항 응답")

            # 2) 리커트 (요약 + 다이버징 + 평균 막대)
            if likert:
                st.markdown("## 📊 리커트 문항 분석")
                sdat = df[likert]  # 문항별 기술통계는 문항 각자의 결측만 제외 (교집합 아님)
                cc = sdat.dropna()  # 크론바흐 α는 문항 간 상관을 봐야 하므로 전 문항 응답한 사람만
                smax = int(sdat.max().max())
                _pos_cut, _neg_cut = likert_cutoffs(smax)
                _pos_col = f"긍정({_pos_cut}점↑)%"
                _neg_col = f"부정({_neg_cut}점↓)%"
                summ = pd.DataFrame({
                    "문항": likert,
                    "응답자(명)": [int(sdat[q].notna().sum()) for q in likert],
                    "평균": [round(sdat[q].dropna().mean(), 2) for q in likert],
                    "표준편차": [round(sdat[q].dropna().std(), 2) for q in likert],
                    "긍정 응답(명)": [int((sdat[q].dropna() >= _pos_cut).sum()) for q in likert],
                    _pos_col: [round((sdat[q].dropna() >= _pos_cut).mean()*100, 1) for q in likert],
                    "부정 응답(명)": [int((sdat[q].dropna() <= _neg_cut).sum()) for q in likert],
                    _neg_col: [round((sdat[q].dropna() <= _neg_cut).mean()*100, 1) for q in likert]})
                a_ = cronbach_alpha(cc)
                lvl = (("매우 높음" if a_ >= .9 else "높음" if a_ >= .8 else "양호" if a_ >= .7 else "낮음")
                       if np.isfinite(a_) else "산출 불가")
                m1, m2, m3 = st.columns(3)
                m1.metric("문항 수", len(likert))
                m2.metric("평균 만족도", f"{pd.concat([sdat[q].dropna() for q in likert]).mean():.2f}")
                m3.metric("크론바흐 α", f"{a_:.3f}" if np.isfinite(a_) else "-", lvl)
                if len(cc) < len(df):
                    st.caption(f"※ 크론바흐 α는 {len(likert)}개 문항에 모두 응답한 {len(cc)}명 기준입니다. "
                               f"(문항별 응답자 수는 위 표의 '응답자(명)' 참고)")
                counts = {q: [int((sdat[q].dropna() == v).sum()) for v in range(1, smax+1)] for q in likert}
                st.markdown("##### 응답 분포 (다이버징 차트)")
                figd = likert_diverging(counts, [f"{v}점" for v in range(1, smax+1)], "문항별 응답 분포")
                dv_png = fig_to_png(figd)
                col_a, col_b = st.columns(2)
                _sv_h = max(3.8, len(likert) * 0.48 + 1.4)
                with col_a:
                    fig, ax = plt.subplots(figsize=(max(5.2, figsize()[0]), _sv_h))
                    order = summ.sort_values("평균")
                    _vals = order["평균"].astype(float).tolist()
                    bars = ax.barh(order["문항"], order["평균"],
                                   color=bar_colors(values=_vals), height=.58, edgecolor="none")
                    ax.set_xlim(0, smax); ax.set_xlabel("평균 점수"); deco(ax, "문항별 평균", ylabel_top=False)
                    ax.grid(axis="y", visible=False)
                    for bar, v in zip(bars, order["평균"]):
                        ax.text(min(float(v)+0.05, smax-0.02), bar.get_y()+bar.get_height()/2,
                                f"{v:.2f}", va="center", fontsize=8.5, color="#33495C")
                    show_plot(fig); plt.close(fig)
                with col_b:
                    fig, ax = plt.subplots(figsize=(max(5.2, figsize()[0]), _sv_h))
                    _bp = ax.barh(summ["문항"], summ[_pos_col], color="#4576AB",
                                      label="긍정", height=.58)
                    _bn = ax.barh(summ["문항"], -summ[_neg_col], color="#C96767",
                                      label="부정", height=.58)
                    _lim = max(25.0, float(max(summ[_pos_col].max(), summ[_neg_col].max()))) * 1.30
                    ax.set_xlim(-_lim, _lim)
                    ax.axvline(0, color="#000000", lw=.9); ax.set_xlabel("← 부정 응답률(%)     긍정 응답률(%) →")
                    ax.invert_yaxis(); deco(ax, "긍정·부정 응답률", ylabel_top=False)
                    ax.grid(axis="y", visible=False)
                    for _b, _v in zip(_bp, summ[_pos_col]):
                        ax.text(float(_v)+_lim*.025, _b.get_y()+_b.get_height()/2, f"{float(_v):.1f}%",
                                va="center", ha="left", fontsize=8, color="#31485E")
                    for _b, _v in zip(_bn, summ[_neg_col]):
                        ax.text(-float(_v)-_lim*.025, _b.get_y()+_b.get_height()/2, f"{float(_v):.1f}%",
                                va="center", ha="right", fontsize=8, color="#7A3F3F")
                    ax.legend(fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.16),
                              ncol=2, frameon=False, borderaxespad=0)
                    fig.subplots_adjust(bottom=.23, top=.88, left=.27, right=.97)
                    show_plot(fig); plt.close(fig)
                smart_table(summ, width="stretch")
                rep_blocks.append({"caption": "리커트 문항 요약", "table": summ, "image": dv_png})

            # 3) 다중응답 (가로 막대)
            if multi:
                st.markdown("## ☑️ 다중응답 문항")
                for c in multi:
                    ser = df[c].dropna().astype(str)
                    sep = next((x for x in [";", ",", "/", "|"]
                                if ser.str.contains(x, regex=False).mean() > 0.3), ";")
                    items = []
                    for v in ser: items += [x.strip() for x in v.split(sep) if x.strip()]
                    vc = pd.Series(items).value_counts()
                    t = pd.DataFrame({"응답 항목": vc.index, "응답 수": vc.values,
                                      "응답률(%)": (vc.values/len(ser)*100).round(1)})
                    cc1, cc2 = st.columns([1, 1])
                    with cc1:
                        st.write(f"**{c}** (응답자 {len(ser)}명)")
                        smart_table(t, width="stretch")
                    with cc2:
                        fig, ax = plt.subplots(figsize=figsize())
                        _vals = t["응답률(%)"][::-1].tolist()
                        _bars = ax.barh(t["응답 항목"][::-1], t["응답률(%)"][::-1],
                                        color=bar_colors(values=_vals))
                        for _b, _v, _n in zip(_bars, t["응답률(%)"][::-1], t["응답 수"][::-1]):
                            ax.text(_v + 1, _b.get_y() + _b.get_height()/2,
                                    f"{_v}% ({int(_n)}명)", va="center", fontsize=8)
                        ax.set_xlim(0, max(t["응답률(%)"]) * 1.25)
                        ax.set_xlabel("응답률(%)"); deco(ax, c)
                        show_plot(fig); plt.close(fig)
                    rep_blocks.append({"caption": f"다중응답 - {c}", "table": t,
                                       "image": fig_to_png(fig, show=False)})

            # 4) 주관식 (의견 목록)
            if openq:
                st.markdown("## ✍️ 주관식 의견")
                for c in openq:
                    ser = df[c].dropna().astype(str).str.strip(); ser = ser[ser != ""]
                    st.write(f"**{c}** — 응답 {len(ser)}건 "
                             f"(전체 {len(df)}명 중 {len(ser)/max(len(df),1)*100:.1f}%)")
                    op_tbl = pd.DataFrame({"번호": range(1, len(ser)+1), "의견": ser.values})
                    smart_table(op_tbl, width="stretch", hide_index=True, height=260)
                    _lim = st.number_input(
                        f"보고서에 담을 '{c}' 의견 수", 1, max(len(ser), 1), max(len(ser), 1),
                        key=f"svy_openlim_{c}",
                        help="의견이 많으면 한글 문서에서 표가 여러 쪽에 걸칩니다. "
                             "표는 쪽을 넘길 때 자동으로 나뉘고 머리행이 반복됩니다. "
                             "줄여서 담고 싶으면 여기서 건수를 조절하세요.")
                    rep_blocks.append({"caption": f"주관식 의견 - {c}",
                                       "table": op_tbl.head(int(_lim))})
                    st.session_state["subj_text"] = "\n".join(f"- {v}" for v in ser.tolist()[:100])

            txt = (f"문항 유형을 자동 판별해 리커트 {len(likert)}개, "
                   f"응답자 특성 {len(demo_q)}개, 객관식 문항 {len(single_q)}개, "
                   f"다중응답 {len(multi)}개, 주관식 {len(openq)}개를 그래프와 함께 분석했습니다.")
            st.success("✅ " + txt)
            if rep_blocks:
                log_action("설문 자동 인식 분석(그래프)")
                report_capture("cap_auto", "설문조사 자동 분석",
                               text=txt, blocks=[{"text": txt}] + rep_blocks)
                _ai_tbl = next((b["table"] for b in rep_blocks
                                if b.get("table") is not None), None)
                if _ai_tbl is not None:
                    ai_interpret_button("svyauto", "설문조사 자동 분석", _ai_tbl,
                                        "설문 응답 분포표입니다. 통계 검정 결과가 아니므로 "
                                        "'유의하다'는 표현은 쓰지 마세요.",
                                        capture_slot="cap_auto")
        report_button("cap_auto")
        survey_download_panel("cap_auto", "auto", "설문_자동분석")

    # ---------- 리커트 ----------
    # ---------- 리커트 ----------
    elif stype.startswith("📊"):
        c1, c2 = st.columns(2)
        demo = c1.multiselect("응답자 특성 열", df.columns.tolist(),
                              default=[c for c in cat_cols if c != "응답자ID"][:3], key="s_d")
        # 응답자번호 같은 일련번호나 점수 범위를 벗어난 열(나이·금액 등)은 기본 선택에서 뺀다.
        _id_cols = set(_v1_id_like_cols(df))
        def _scale_like(c):
            v = pd.to_numeric(df[c], errors="coerce").dropna()
            return len(v) > 0 and v.min() >= 0 and v.max() <= 10 and bool((v == v.round()).all())
        qs = c2.multiselect("문항 열 (숫자형)", num_cols,
                            default=[c for c in num_cols if not _looks_like_nominal_code(c)
                                     and c not in _id_cols and _scale_like(c)], key="s_q")
        demo = reorder_by_rank(demo, "s_d", "↕️ 응답자 특성 표시 순서 바꾸기")
        qs = reorder_by_rank(qs, "s_q", "↕️ 문항 표시 순서 바꾸기")
        scale_max = st.number_input("척도 최대값 (5점 척도면 5)", 2, 10, 5)
        _pos_cut, _neg_cut = likert_cutoffs(scale_max)
        _pos_col = f"긍정({_pos_cut}점↑)%"
        _neg_col = f"부정({_neg_cut}점↓)%"
        if qs and keep_running("svlikert", "리커트 분석 실행"):
            s = df[qs]  # 문항별 기술통계는 문항 각자의 결측만 제외 (교집합으로 자르지 않음)
            cc = s.dropna()  # 크론바흐 α·문항 제외 α는 전 문항 응답자만 필요
            st.markdown("#### 1) 응답자 특성")
            if demo:
                for d_ in demo:
                    vc = df[d_].value_counts()
                    st.write(f"**{d_}** (n={int(vc.sum())})")
                    smart_table(pd.DataFrame({d_: vc.index.astype(str), "빈도": vc.values,
                                               "비율(%)": (vc.values/vc.sum()*100).round(1)}),
                                 width="stretch")
            else:
                st.caption("응답자 특성 열을 선택하면 빈도표가 표시됩니다.")

            st.markdown("#### 2) 문항별 기술통계")
            summ = pd.DataFrame({
                "문항": qs,
                "응답자(명)": [int(s[q].notna().sum()) for q in qs],
                "평균": [round(s[q].dropna().mean(), 2) for q in qs],
                "표준편차": [round(s[q].dropna().std(), 2) for q in qs],
                "중앙값": [round(s[q].dropna().median(), 1) for q in qs],
                "긍정 응답(명)": [int((s[q].dropna() >= _pos_cut).sum()) for q in qs],
                _pos_col: [round((s[q].dropna() >= _pos_cut).mean()*100, 1) for q in qs],
                "부정 응답(명)": [int((s[q].dropna() <= _neg_cut).sum()) for q in qs],
                _neg_col: [round((s[q].dropna() <= _neg_cut).mean()*100, 1) for q in qs]})
            smart_table(summ, width="stretch")

            st.markdown("#### 3) 신뢰도 분석")
            a_ = cronbach_alpha(cc)
            lvl = (("매우 높음" if a_ >= .9 else "높음" if a_ >= .8 else "양호" if a_ >= .7 else "낮음")
                   if np.isfinite(a_) else "산출 불가")
            c1, c2 = st.columns(2)
            c1.metric("크론바흐 α", f"{a_:.3f}" if np.isfinite(a_) else "-"); c2.metric("신뢰도 수준", lvl)
            if len(cc) < len(df):
                st.caption(f"※ 크론바흐 α는 {len(qs)}개 문항에 모두 응답한 {len(cc)}명 기준입니다.")
            drop = pd.DataFrame({"제외 문항": qs,
                                 "제외 시 α": [round(cronbach_alpha(cc.drop(columns=[q])), 3) for q in qs]})
            st.write("**문항 제외 시 신뢰도** (α가 크게 올라가면 그 문항은 재검토 대상)")
            smart_table(drop, width="stretch")

            st.markdown("#### 4) 응답 분포")
            dist = pd.DataFrame({q: [int((s[q].dropna() == v).sum()) for v in range(1, scale_max+1)] for q in qs},
                                index=[f"{v}점" for v in range(1, scale_max+1)]).T
            # 인원과 비율을 함께 보여준다 (예: 12명 (20.0%))
            _dist_show = dist.copy().astype(object)
            for q in qs:
                _tot = max(int(dist.loc[q].sum()), 1)
                for v in range(1, scale_max+1):
                    _cnt = int(dist.loc[q, f"{v}점"])
                    _dist_show.loc[q, f"{v}점"] = f"{_cnt}명 ({_cnt/_tot*100:.1f}%)"
            _dist_show["합계"] = [f"{int(dist.loc[q].sum())}명 (100.0%)" for q in qs]
            smart_table(_dist_show.reset_index().rename(columns={"index": "문항"}),
                         width="stretch")
            st.caption("각 칸은 **응답 인원(명)과 비율(%)** 입니다.")
            st.markdown("##### 다이버징 차트 (중립 기준 좌우 분리)")
            counts_d = {q: [int((s[q].dropna() == v).sum()) for v in range(1, scale_max+1)] for q in qs}
            figd = likert_diverging(counts_d, [f"{v}점" for v in range(1, scale_max+1)], "문항별 응답 분포")
            png = fig_to_png(figd)
            _lk_h = max(4.2, len(qs) * 0.55 + 1.5)
            fig, axes = plt.subplots(1, 2, figsize=(max(11.5, figsize()[0]*2), _lk_h))
            _avg_vals = summ["평균"].astype(float).tolist()
            axes[0].barh(summ["문항"], summ["평균"],
                         color=bar_colors(values=_avg_vals), height=.58)
            axes[0].invert_yaxis(); axes[0].set_xlim(0, scale_max)
            axes[0].set_xlabel("평균 점수"); deco(axes[0], "문항별 평균", ylabel_top=False)
            axes[0].grid(axis="y", visible=False)
            bottom = np.zeros(len(qs))
            _mid = scale_max // 2
            _neg_full = ["#F3D8D8", "#E8AAAA", "#C96767", "#A94D4D", "#8F3E3E"]
            _pos_full = ["#D6E7F4", "#9EC5E5", "#6291C2", "#4576AB", "#2D5A8E"]
            if scale_max % 2 == 1:
                _lk_cols = (_neg_full[-_mid:] + ["#E3E9EF"] + _pos_full[:_mid])
            else:
                _lk_cols = (_neg_full[-_mid:] + _pos_full[:_mid])
            for v in range(1, scale_max+1):
                vals = dist[f"{v}점"].values
                _bars = axes[1].barh(qs, vals, left=bottom, label=f"{v}점",
                                     color=_lk_cols[v-1], height=.58, edgecolor="white", linewidth=.7)
                for _b, _vv, _left, _q in zip(_bars, vals, bottom, qs):
                    _tot = max(float(dist.loc[_q].sum()), 1.0)
                    if float(_vv) / _tot >= .10:
                        axes[1].text(float(_left)+float(_vv)/2, _b.get_y()+_b.get_height()/2,
                                     f"{float(_vv)/_tot*100:.0f}%", ha="center", va="center",
                                     fontsize=7, color="#23394D", fontweight="bold")
                bottom += vals
            axes[1].invert_yaxis(); deco(axes[1], "응답 분포(누적)", ylabel_top=False)
            axes[1].grid(axis="y", visible=False)
            axes[1].legend(fontsize=7.5, ncol=min(scale_max, 5), loc="upper center",
                           bbox_to_anchor=(0.5, -0.12), frameon=False, borderaxespad=0)
            fig.subplots_adjust(bottom=.20, top=.90, left=.10, right=.98, wspace=.34)
            show_plot(fig); plt.close(fig)

            st.markdown("#### 5) 집단별 비교")
            cmp_df = pd.DataFrame()
            if demo:
                rows = []
                for d_ in demo:
                    for q in qs:
                        sub = df[[d_, q]].dropna()
                        grp = [sub[sub[d_] == lv][q] for lv in sub[d_].unique()]
                        if len(grp) == 2: stat, p = stats.ttest_ind(*grp); tname = "t-검정"
                        elif len(grp) > 2: stat, p = stats.f_oneway(*grp); tname = "ANOVA"
                        else: continue
                        rows.append({"특성": d_, "문항": q, "검정": tname,
                                     "통계량": round(stat, 3), "p": round(p, 4),
                                     "유의성": "*" if p < .05 else "n.s."})
                cmp_df = pd.DataFrame(rows)
                smart_table(cmp_df, width="stretch")
                sig = cmp_df[cmp_df["유의성"] == "*"]
                st.info(f"💡 응답자 특성에 따라 차이가 유의한 항목 {len(sig)}개"
                        + (": " + ", ".join(f"{r['특성']}×{r['문항']}" for _, r in sig.head(3).iterrows()) if len(sig) else ""))
            else:
                st.caption("응답자 특성을 선택하면 집단별 차이 검정을 수행합니다.")

            valid_summ = summ.dropna(subset=["평균"])
            if valid_summ.empty:
                st.warning("⚠️ 선택한 문항 중 유효한 응답이 있는 열이 없습니다. "
                           "빈 열이 섞여 있지 않은지 '문항 열' 선택을 확인해 주세요.")
                top = low = "-"
            else:
                top = valid_summ.loc[valid_summ["평균"].idxmax(), "문항"]
                low = valid_summ.loc[valid_summ["평균"].idxmin(), "문항"]
            txt = (f"평균이 가장 높은 문항은 '{top}', 가장 낮은 문항은 '{low}'입니다. "
                   f"전체 신뢰도(크론바흐 α)는 {a_:.3f}로 {lvl} 수준입니다.")
            st.download_button("🖼️ 그래프 다운로드", png, "survey.png", "image/png")
            log_action("설문 리커트 분석")
            blocks = [{"text": txt},
                      {"caption": "문항별 기술통계", "table": summ, "image": png},
                      {"caption": "문항 제외 시 신뢰도", "table": drop}]
            if demo and len(cmp_df):
                blocks.append({"caption": "응답자 특성별 차이 검정", "table": cmp_df})
            _lk_sent = report_sentence_likert(summ, a_, scale_max, _pos_col, int(summ["응답자(명)"].max()) if len(summ) else len(df))
            _lk_foot = (f"* {scale_max}점 척도(1=전혀 그렇지 않다 ~ {scale_max}=매우 그렇다), 평균·표준편차는 문항별 응답자 기준.\n"
                        f"* 긍정 = {_pos_cut}점 이상, 부정 = {_neg_cut}점 이하 응답 비율."
                        + (f" 신뢰도 Cronbach's α = {a_:.3f} (n = {len(cc)})." if np.isfinite(a_) else ""))
            _v1_copy_box("표 각주 (복사해서 표 아래에 붙이세요)", _lk_foot)
            _v1_copy_box("보고서용 결과 문장", _lk_sent)
            blocks[0] = {"text": _lk_sent}
            blocks[1]["xlsx_chart"] = [
                xl_chart("barh", summ[["문항", "평균"]], "문항별 평균", y_title="평균 점수"),
                xl_chart("stacked100", dist.reset_index().rename(columns={"index": "문항"}), "응답 분포(누적 %)")]
            blocks.insert(2, {"text": _lk_foot})
            for _b in blocks:   # 화면에 그래프가 없는 표는 엑셀에도 그래프를 넣지 않는다
                if _b.get("caption") in ("문항 제외 시 신뢰도", "응답자 특성별 차이 검정"):
                    _b["xlsx_chart"] = []
            report_capture("cap_survey", "설문조사 분석(리커트)", text=txt, blocks=blocks)
            ai_interpret_button("svylk", "설문 리커트 척도 분석", summ,
                                "평균·표준편차·긍정률과 크론바흐 알파가 있는 표입니다. "
                                "알파 0.7 이상이면 신뢰할 만하다는 기준을 함께 언급하세요.",
                                capture_slot="cap_survey")
        report_button("cap_survey")
        survey_download_panel("cap_survey", "likert", "설문_리커트분석")

    # ---------- 객관식 ----------
    elif stype.startswith("🔘"):
        st.caption("성별·소속·사용목적처럼 하나만 고르는 문항의 빈도와 비율을 분석합니다.")
        cols = st.multiselect("객관식 문항 열", df.columns.tolist(),
                              default=[c for c in cat_cols if c != "응답자ID"][:3], key="sc_q")
        if cols and keep_running("svmc", "객관식 분석 실행"):
            all_tbl = []
            for c in cols:
                vc = df[c].value_counts()
                t = pd.DataFrame({"문항": c, "응답": vc.index.astype(str), "빈도": vc.values,
                                  "비율(%)": (vc.values/vc.sum()*100).round(1)})
                all_tbl.append(t)
                cc1, cc2 = st.columns([1, 1])
                with cc1:
                    st.write(f"**{c}** (n={int(vc.sum())})")
                    smart_table(t.drop(columns=["문항"]), width="stretch")
                with cc2:
                    fig = pie_chart(vc, c, donut=True)
                    show_plot(fig); plt.close(fig)
            res = pd.concat(all_tbl, ignore_index=True)
            top = res.loc[res["빈도"].idxmax()]
            txt = f"가장 많은 응답은 '{top['문항']}'의 '{top['응답']}'({top['비율(%)']}%)입니다."
            st.info("💡 " + txt)
            png = fig_to_png(fig, show=False)
            log_action("설문 객관식 분석")
            _mc_sent = report_sentence_mc(res)
            _mc_foot = "* 비율(%)은 각 문항에 응답한 사람(n) 대비 비율입니다."
            _v1_copy_box("표 각주 (복사해서 표 아래에 붙이세요)", _mc_foot)
            _v1_copy_box("보고서용 결과 문장", _mc_sent)
            _mc_charts = [xl_chart("donut", g[["응답", "빈도"]], str(q)) for q, g in res.groupby("문항", sort=False)]
            report_capture("cap_mc", "설문 객관식 분석", None,
                           blocks=[{"text": _mc_sent},
                                   {"caption": "설문 객관식 분석", "table": res, "image": png, "xlsx_chart": _mc_charts},
                                   {"text": _mc_foot}])
            ai_interpret_button("svymc", "설문 객관식 응답 분포", res,
                                "빈도(명)와 비율(%)만 있는 표입니다. 통계 검정 결과가 아니므로 "
                                "'유의하다'는 표현은 쓰지 말고, 응답이 몰린 항목과 그 뜻을 서술하세요.",
                                capture_slot="cap_mc")
        report_button("cap_mc")
        survey_download_panel("cap_mc", "mc", "설문_객관식분석")

    # ---------- 다중응답 ----------
    elif stype.startswith("☑️"):
        st.caption("'해당되는 것을 모두 고르세요' 문항처럼 한 칸에 여러 답이 들어간 경우를 분석합니다.")
        c1, c2 = st.columns(2)
        mcol = c1.selectbox("다중응답 열", df.columns.tolist(), key="mr_c")
        sep = c2.selectbox("구분 기호", [";", ",", "/", "|", " "], key="mr_s")
        if keep_running("svmr", "다중응답 분석 실행"):
            ser = df[mcol].dropna().astype(str)
            n_resp = len(ser)
            items = []
            for v in ser: items += [x.strip() for x in v.split(sep) if x.strip()]
            vc = pd.Series(items).value_counts()
            t = pd.DataFrame({"응답 항목": vc.index, "응답 수": vc.values,
                              "응답률(%)": (vc.values/n_resp*100).round(1),
                              "구성비(%)": (vc.values/vc.sum()*100).round(1)})
            st.write(f"응답자 {n_resp}명 / 총 응답 {int(vc.sum())}건 (1인 평균 {vc.sum()/n_resp:.1f}개)")
            smart_table(t, width="stretch")
            fig, ax = plt.subplots(figsize=figsize())
            ax.barh(t["응답 항목"], t["응답률(%)"], color=bar_colors(values=t["응답률(%)"].tolist())); ax.invert_yaxis()
            ax.set_xlabel("응답률(%)"); deco(ax, f"{mcol} 다중응답")
            png = fig_to_png(fig)
            txt = (f"가장 많이 선택된 항목은 '{t.iloc[0]['응답 항목']}'로 응답자의 "
                   f"{t.iloc[0]['응답률(%)']}%가 선택했습니다. (응답률 합계가 100%를 넘는 것은 정상입니다)")
            st.info("💡 " + txt)
            log_action("설문 다중응답 분석")
            _mr_sent = report_sentence_mr(mcol, t, n_resp)
            _mr_foot = (f"* 응답률 = 해당 항목을 고른 응답자 ÷ 전체 응답자({n_resp}명). 여러 개를 고를 수 있어 합계가 100%를 넘습니다.\n"
                        "* 구성비 = 해당 항목 응답 수 ÷ 전체 응답 수.")
            _v1_copy_box("표 각주 (복사해서 표 아래에 붙이세요)", _mr_foot)
            _v1_copy_box("보고서용 결과 문장", _mr_sent)
            report_capture("cap_mr", "설문 다중응답 분석", None,
                           blocks=[{"text": _mr_sent},
                                   {"caption": "설문 다중응답 분석", "table": t, "image": png,
                                    "xlsx_chart": xl_chart("barh", t[["응답 항목", "응답률(%)"]], f"{mcol} 다중응답", y_title="응답률(%)")},
                                   {"text": _mr_foot}])
            ai_interpret_button("svymr", "설문 다중응답 분석", t,
                                "다중응답이므로 응답률 합계가 100%를 넘는 것이 정상입니다. "
                                "이를 오류로 지적하지 마세요.",
                                capture_slot="cap_mr")
        report_button("cap_mr")
        survey_download_panel("cap_mr", "mr", "설문_다중응답분석")

    # ---------- 주관식 ----------
    elif stype.startswith("✍️"):
        st.caption("자유롭게 적은 의견을 모아 응답 목록·주요 단어를 확인하고, AI로 요약할 수 있습니다.")
        tcol = st.selectbox("주관식 열", df.columns.tolist(), key="tx_c")
        if keep_running("svtx", "주관식 분석 실행"):
            ser = df[tcol].dropna().astype(str).str.strip()
            ser = ser[ser != ""]
            c1, c2 = st.columns(2)
            c1.metric("응답 건수", f"{len(ser)}건")
            c2.metric("응답률", f"{len(ser)/max(len(df),1)*100:.1f} %")
            st.markdown("#### 의견 목록")
            op_tbl = pd.DataFrame({"번호": range(1, len(ser)+1), "의견": ser.values})
            smart_table(op_tbl, width="stretch", hide_index=True, height=320)
            txt = (f"주관식 문항 '{tcol}'에 대해 전체 {len(df)}명 중 {len(ser)}명"
                   f"({len(ser)/max(len(df),1)*100:.1f}%)이 의견을 제시하였다.")
            st.info("💡 " + txt)
            st.session_state["subj_text"] = "\n".join(f"- {v}" for v in ser.tolist()[:100])
            log_action("설문 주관식 분석")
            report_capture("cap_tx", "설문 주관식 의견", txt, op_tbl, None)
        if st.session_state.get("subj_text"):
            st.markdown("#### 🧠 AI로 의견 요약하기 (선택)")
            if st.button("AI 요약 실행"):
                with st.spinner("AI가 의견을 정리하는 중..."):
                    st.markdown(ai_call(
                        "다음은 설문조사의 주관식 응답입니다. 주요 의견을 3~5개 주제로 묶어 "
                        "각 주제별 핵심 내용과 대표 의견을 한국어로 정리해 주세요. "
                        "마지막에 개선 우선순위를 제안해 주세요.\n\n" + st.session_state["subj_text"],
                        st.session_state.get("api_key"), st.session_state.get("ai_model_g"), max_tokens=1200))
                    log_action("AI 주관식 의견 요약")
        report_button("cap_tx")
        survey_download_panel("cap_tx", "text", "설문_주관식분석")

    # ---------- 교차분석 ----------
    else:
        st.caption("두 범주형 문항의 관계를 교차표와 카이제곱 검정으로 확인합니다. (예: 소속 × 재사용 의향)")
        c1, c2 = st.columns(2)
        rowv = c1.selectbox("행 변수", df.columns.tolist(), key="ct_r")
        colv = c2.selectbox("열 변수", [c for c in df.columns if c != rowv], key="ct_c")
        if keep_running("svct", "교차분석 실행"):
            sub = df[[rowv, colv]].dropna()
            ct = pd.crosstab(sub[rowv], sub[colv])
            # 집단마다 응답자 수가 다르므로 '집단 안에서의 비율'(행 기준 %)로 비교한다.
            pct_tbl = (ct.div(ct.sum(axis=1), axis=0)*100).round(1)
            # 인원(빈도)과 비율(%)을 한 칸에 함께 표시 (예: 12명 (33.3%))
            show = ct.astype(object).copy()
            for r in ct.index:
                for c in ct.columns:
                    show.loc[r, c] = f"{int(ct.loc[r, c])}명 ({pct_tbl.loc[r, c]:.1f}%)"
            show["합계"] = [f"{int(ct.loc[r].sum())}명 (100.0%)" for r in ct.index]
            st.caption(f"※ %는 각 **{rowv}** 안에서의 비율입니다 (가로 합계 100%). "
                       "집단마다 응답자 수가 달라도 비율로 바로 비교할 수 있습니다.")
            smart_table(show, width="stretch")
            with st.expander(f"다른 방향으로 보기 — 각 '{colv}' 응답을 고른 사람의 구성 비율"):
                _col_pct = (ct.div(ct.sum(axis=0), axis=1)*100).round(1)
                _show_c = ct.astype(object).copy()
                for r in ct.index:
                    for c in ct.columns:
                        _show_c.loc[r, c] = f"{int(ct.loc[r, c])}명 ({_col_pct.loc[r, c]:.1f}%)"
                smart_table(_show_c, width="stretch")
                st.caption(f"※ 여기서 %는 각 '{colv}' 응답 안에서의 비율입니다 (세로 합계 100%).")
            _chi = None
            try:
                chi2, p, dof, exp = stats.chi2_contingency(ct)
                low = (exp < 5).sum() / exp.size * 100
                _chi = (chi2, dof, p, low)
                if low > 20:
                    st.warning(f"⚠️ 기대빈도가 5 미만인 칸이 {low:.0f}%입니다(기준 20%). "
                               "카이제곱 결과가 부정확할 수 있으니 범주를 합치거나 Fisher 정확검정을 고려하세요.")
                c1, c2, c3 = st.columns(3)
                c1.metric("카이제곱", f"{chi2:.3f}"); c2.metric("자유도", dof); c3.metric("p-value", f"{p:.4f}")
                txt = (f"'{rowv}'와 '{colv}' 사이에 "
                       + ("통계적으로 유의한 관련성이 있습니다" if p < .05 else "유의한 관련성이 없습니다")
                       + f" (χ²={chi2:.2f}, {fmt_p(p)}).")
                st.info("💡 " + txt)
            except Exception as e:
                txt = "교차표를 생성했습니다."; st.warning(f"카이제곱 검정 불가: {e}")
            row_pct = (ct.div(ct.sum(axis=1), axis=0)*100).round(1)  # 막대 라벨은 항상 행 기준 %로 표기
            _w, _h = figsize()
            fig, ax = plt.subplots(figsize=(_w + 1.2, _h))
            bottoms = np.zeros(len(ct))
            # 칸이 좁은데 '9명\n(30.0%)'를 두 줄로 넣으면 글씨가 서로 겹친다.
            # 그렇다고 '명'이나 '%'를 통째로 빼면 뭘 나타내는 숫자인지 알기 어려우므로,
            # 세로 공간이 부족하면 '9명(30.0%)'처럼 한 줄로 합쳐서라도 단위·비율을 남긴다.
            _ymax = float(ct.sum(axis=1).max()) or 1.0
            _hidden = 0
            _ct_cols = _survey_palette(len(ct.columns))
            for _ci, col in enumerate(ct.columns):
                vals = ct[col].values
                ax.bar(ct.index.astype(str), vals, bottom=bottoms, label=str(col),
                       color=_ct_cols[_ci], edgecolor="white", linewidth=.6)
                for x, (v, b, pv) in enumerate(zip(vals, bottoms, row_pct[col].values)):
                    if v <= 0:
                        continue
                    lab_fs = crosstab_bar_label(v, pv, _ymax)
                    if lab_fs is None:
                        _hidden += 1
                        continue
                    lab, fs = lab_fs
                    ax.text(x, b + v/2, lab, ha="center", va="center",
                            fontsize=fs, color="white")
                bottoms += vals
            ax.set_ylabel("응답 수"); deco(ax, f"{rowv} × {colv}")
            ax.set_ylim(0, _ymax * 1.05)
            plt.xticks(rotation=20)
            # 범례를 그림 밖으로 빼서 막대·숫자를 가리지 않게 한다
            ax.legend(title=str(colv), fontsize=7, title_fontsize=8,
                      loc="upper left", bbox_to_anchor=(1.01, 1.0), borderaxespad=0)
            plt.tight_layout(); png = fig_to_png(fig)
            if _hidden:
                st.caption(f"※ 칸이 너무 좁은 {_hidden}곳은 글씨가 겹쳐 숫자를 생략했습니다. "
                           "정확한 값은 위 교차표를 보세요.")
            out = show.reset_index()
            log_action(f"교차분석: {rowv} × {colv}")
            _ct_chart = xl_chart("stacked", ct.reset_index().rename(columns={rowv: str(rowv)}),
                                 f"{rowv} × {colv} (응답 수)", y_title="응답 수")
            _ct_sent = report_sentence_crosstab(rowv, colv, ct, _chi)
            _ct_foot = (f"* 값은 응답자 수(명)와 각 {rowv} 안에서의 비율(%)."
                        + (f"\n* 카이제곱 검정: χ² = {_chi[0]:.2f}, df = {_chi[1]}, {fmt_p(_chi[2])}." if _chi else ""))
            _v1_copy_box("표 각주 (복사해서 표 아래에 붙이세요)", _ct_foot)
            _v1_copy_box("보고서용 결과 문장", _ct_sent)
            report_capture("cap_ct", f"{rowv} × {colv} 교차분석", None,
                           blocks=[{"text": _ct_sent},
                                   {"caption": f"{rowv} × {colv} 교차분석", "table": out, "image": png,
                                    "xlsx_chart": _ct_chart},
                                   {"text": _ct_foot}])
            ai_interpret_button("svyct", f"{rowv} × {colv} 교차분석", out,
                                f"카이제곱 검정 결과는 다음과 같습니다: {txt} "
                                "표의 값은 '인원(비율%)' 형식이며 비율은 행 기준입니다.",
                                capture_slot="cap_ct")
        report_button("cap_ct")
        survey_download_panel("cap_ct", "cross", "설문_교차분석")

# ================================================================ 사용설명서
elif menu == "👑 관리자":
    render_admin_dashboard()

elif menu == "📖 사용설명서":
    st.title("📖 사용설명서")
    _MANUAL = r"""# 스마트 통계 에이전트 Version 1 — 사용설명서

Version 1은 통계를 처음 접하는 연구자도 **데이터 준비 → 파일 올리기 → 분석 고르기 → 결과 저장** 4단계로 쓸 수 있게 만든 간편형입니다.

---

## 1. 처음 사용한다면

1. **데이터 준비**: 형식이 헷갈리면 왼쪽 `📘 데이터 작성 가이드`의 예시와 엑셀 양식을 참고하세요. 쓰던 엑셀·CSV를 그대로 올려도 됩니다.
2. **파일 올리기**: 왼쪽 `📂 데이터 불러오기`에 올리면 **자동으로 점검**해서 고칠 곳을 알려 줍니다.
3. **분석 고르기**: 처음이라면 `⚡ 원클릭 분석` 한 번이면 충분합니다.
4. **결과 저장**: 표·그래프·보고서 문장을 한글(hwpx)·워드(docx)·엑셀(xlsx)로 받습니다.

---

## 2. 데이터는 이렇게 작성하세요

1. 첫 번째 행에는 변수명만 적습니다.
2. 한 열에는 한 가지 변수만 적습니다.
3. 한 행에는 한 조사단위만 적습니다. 포장시험이면 보통 `처리구 × 반복` 한 칸이 한 행입니다.
4. 숫자 셀에는 숫자만 적습니다. `120kg`, `약 15`, `30개`처럼 문자나 단위를 붙이지 않습니다.
5. 단위는 열 이름에 적습니다. 예: `초장(cm)`, `수량(kg/10a)`.
6. 병합셀, 중간 제목, 소계·합계행, 빈 구분행은 넣지 않습니다.

### ❌ 잘못된 예: 처리구를 가로로 펼침

| 반복 | 대조구 | 처리1 | 처리2 |
|---|---:|---:|---:|
| 1 | 100 | 120 | 130 |
| 2 | 105 | 118 | 128 |

### ✅ 권장 예: 처리구·반복·측정값을 각각 열로 입력

| 처리구 | 반복 | 수량 |
|---|---:|---:|
| 대조구 | 1 | 100 |
| 대조구 | 2 | 105 |
| 처리1 | 1 | 120 |
| 처리1 | 2 | 118 |
| 처리2 | 1 | 130 |
| 처리2 | 2 | 128 |

### 자주 틀리는 형식과 앱에 뜨는 안내
| 이렇게 쓰면 | 앱에 이렇게 떠요 | 고치는 법 |
|---|---|---|
| 표 위에 제목 행, 병합셀 | ❌ 첫 행이 변수명이 아닌 것 같습니다 | 제목·빈 행을 지우고 첫 행에 변수명만, 병합은 풀고 모든 행에 처리명 입력 |
| `120kg`, `약 15`, `결측` | ⚠️ 열에 숫자가 아닌 값이 섞여 있습니다 (몇 행인지 표시) | 숫자만 입력, 결측은 빈칸. `🔧 숫자로 자동 변환`으로 바로 고칠 수도 있음 |
| `대조구 평균`, `합계`, `소계` 행 | ❌ 평균·합계 같은 요약 행이 들어 있습니다 | 실제 관측값 행만 남기기 (평균은 앱이 계산) |
| 처리구마다 열을 따로 만듦 | ⚠️ 처리구가 여러 열로 가로로 펼쳐진 형태입니다 | `처리구 / 반복 / 측정값` 세 열로 세로 입력 |
| `반복1 수량`, `반복2 수량` | ⚠️ 반복이 여러 열로 나뉘어 있습니다 | `반복` 열 하나와 `수량` 열 하나로 |
| `대조구` / `대조 구` / `대조구 ` | ⚠️ 같은 이름이 다르게 적힌 값이 있습니다 | 처리명을 하나로 통일 (띄어쓰기·공백 주의) |
| 반복마다 평균값을 복사 | ⚠️ 반복 간 값이 거의 같습니다 (CV 1% 미만) | 반복별 **실제 조사값(원자료)** 입력 |
| 양식의 회색 예시 행을 남겨 둠 | ❌ 엑셀 양식의 예시 행이 그대로 남아 있습니다 | 예시 행 삭제 |
| 변수명이 위·아래 두 줄 | ❌ 첫 행이 변수명이 아닌 것 같습니다 (또는 ⚠️ 이름 없는 열) | `고급 · 변수명이 두 줄인 파일`을 켜고 다시 올리기 |

왼쪽 `📘 데이터 작성 가이드 → ❌ 자주 틀리는 작성 예시`에서 사례별로 잘못 쓴 표와 실제 경고, 고친 표를 볼 수 있습니다.

### 엑셀 양식
왼쪽 `📘 데이터 작성 가이드`의 **📥 엑셀 양식 받기**로 예시가 들어 있는 양식을 받을 수 있습니다. **회색 글씨(변수명·값)는 예시**이므로 내 시험에 맞게 변수명을 바꾸고, 예시 행은 지운 뒤 실제 값을 입력하세요. 예시 행을 지우지 않고 올리면 데이터 점검에서 알려 드립니다. 양식의 `작성방법` 시트는 올릴 때 자동으로 제외됩니다.

---

## 3. 데이터 불러오기

왼쪽 `📂 데이터 불러오기`에서 입력 방식을 고릅니다.

- **📁 Excel/CSV**: 일반적인 분석 파일. 시트가 여러 개면 시트별로 나뉘어 들어옵니다. 변수명이 두 줄이면 `고급 · 변수명이 두 줄인 파일`을 켜세요.
- **📷 이미지/사진**: 조사야장·표 사진이나 엑셀 화면 캡처를 AI가 표로 읽습니다. 적용 전에 미리보기에서 값을 꼭 확인하세요.
- **📄 PDF**: 보고서·성적서 PDF 안의 표를 불러옵니다. 한글·엑셀에서 PDF로 저장한 파일은 AI 없이 바로 읽고, 표가 여러 개면 골라서 씁니다. 종이를 스캔한 PDF는 쪽을 골라 AI로 읽습니다.
- **🎤 음성**: `처리구 A, 반복 1, 초장 72.3, 수량 615.4`처럼 한 행씩 말해 표로 추가합니다.

이미지·스캔 PDF·음성 인식은 `🧠 AI 도우미 → AI 연결 설정`에서 API 키를 연결해야 합니다. 음성 인식은 ChatGPT 또는 Gemini에서만 됩니다.

### 📱 휴대폰 음성 입력 (밭·하우스에서)
앱 주소 뒤에 `?mode=voice`를 붙여 열면 큰 마이크 화면만 나옵니다 (예: `https://앱주소/?mode=voice`).
- 마이크를 누르고 한 행을 말한 뒤 다시 누르면 **자동으로 표에 한 행이 추가**됩니다.
- `열 이름`에 `처리구, 반복, 초장, 수량`처럼 적어 두면 모든 행이 같은 열로 정리됩니다.
- 입력한 표는 계정에 저장되어, PC에서 같은 계정으로 로그인하면 `📂 데이터 불러오기` 맨 위의 **📱 불러와서 분석**으로 이어서 분석할 수 있습니다.
- `이 기기에 API 키 기억`을 체크하면 그 휴대폰에서는 키를 다시 넣지 않아도 됩니다.

---

## 4. 데이터 점검

파일을 올리면 어느 화면에 있든 점검 결과가 한 번 표시되고, `📊 통계분석 → 📋 데이터 점검`에서 언제든 다시 볼 수 있습니다. 문제마다 **📍 위치(엑셀 몇 행)**와 **🔧 고치는 법**을 알려 줍니다.

- ❌ 꼭 고쳐야 할 문제: 첫 행이 변수명이 아님(제목 행·병합셀), 평균·합계 행, 지우지 않은 양식 예시 행
- ⚠️ 확인할 항목: 숫자 칸의 단위·글자(`620kg`, `결측`), 빈칸, 띄어쓰기만 다른 처리명(`대조구`/`대조구 `), 중복 행, 가로로 펼친 자료, 반복이 1개뿐인 처리, 반복 간 값이 거의 같은 경우(CV 1% 미만)
- ℹ️ 참고: 음수·값이 모두 같은 열, 처리마다 반복 수가 다른 경우

엑셀에서 고친 파일을 **같은 이름으로 다시 올려도** 내용이 바뀌었으면 다시 점검합니다. 숫자에 단위가 섞인 열은 `🔧 숫자로 자동 변환`으로 바로 고칠 수 있습니다.

---

## 5. 메뉴 한눈에 보기

| 메뉴 | 이런 때 사용합니다 | 할 수 있는 것 |
|---|---|---|
| ⚡ **원클릭 분석** | 처리구·반복이 정리된 실험자료를 버튼 하나로 분석 | 분산분석 · 사후검정(a,b,c) · 그래프 · 보고서 |
| 📊 **통계분석** | 분석 방법을 직접 골라 자세히 볼 때 | 데이터 점검 · 분산분석 · 상관 · 회귀 · 머신러닝 예측 |
| 📋 **설문조사 분석** | 농가·교육생 설문 결과를 정리할 때 | 만족도 · 객관식 · 다중응답 · 교차분석 |
| 📑 **보고서** | 담아 둔 표·그래프를 문서로 만들 때 | 한글(hwpx) · 워드(docx) |
| 🧠 **AI 도우미** | 결과 해석·고찰 문장, 통계 질문 | AI 해석 · 질문하기 (API 키 필요) |
| 📖 **사용설명서** | 데이터 작성법과 사용법을 확인할 때 | 메뉴별 설명 · 자주 틀리는 예시 |

---

## 6. 원클릭 분석

처리구·반복·측정 항목을 자동으로 찾아 **항목별 분산분석 → 사후검정 → 그래프 → 적요·결과 문장**까지 한 번에 만듭니다. 맨 아래 **🧾 통계 처리 문구**는 실제로 사용한 설계·분석 방법·사후검정·평균±SD(SE)·변이계수를 담아, 보고서의 `재료 및 방법 — 통계처리`에 그대로 붙여 쓸 수 있습니다 (오른쪽 위 📋 버튼으로 복사).

---

## 7. 통계분석

### 📋 데이터 점검
위 4번 항목의 점검 결과, 숫자 자동 변환, 데이터 미리보기와 기술통계를 봅니다.

### 🌱 분산분석 (처리 간 차이)
`처리구나 품종의 평균이 서로 다른가?`를 확인합니다. 시험 형태는 **일원배치 · 이원배치 · 여러 형질 한 표에(요약표)**가 기본이고, 같은 목록 아래쪽 작은 글씨로 **분할구법 · 반복측정(고급)**이 있습니다. 각 설계의 뜻은 `ℹ️ 이 분석이 뭔가요?`에 정리되어 있습니다.

- 반복(블록) 열은 자동으로 잡히며, 포장시험에서 반복을 두었다면 **반드시 지정**되어 있는지 확인하세요.
- 측정값이 `반복`·`개체번호` 같은 번호 열로 잘못 잡히지 않게 실제 측정값이 먼저 선택됩니다.
- `p < 0.05`: 처리 간 차이가 우연으로 보기 어려움 (0.001 미만은 `p<0.001`로 표기)
- 같은 유의성 문자를 공유하면 통계적으로 뚜렷한 차이가 없음 (`a`, `ab`, `b`)
- CV가 1% 미만이면 원자료가 맞는지 확인하라는 경고가 나옵니다.
- 결과 아래의 **📋 표 각주**와 **📋 보고서용 결과 문장**은 복사해서 바로 쓸 수 있고, **🤖 AI 해석**으로 보고서·고찰·현장지도용 문장을 받을 수 있습니다.

### 🔗 상관분석 (변수 간 관계)
`초장이 큰 개체가 수량도 높은가?`처럼 숫자형 변수들이 함께 변하는 정도를 봅니다 (Pearson 또는 Spearman). 개체번호·반복 같은 번호 열은 기본 선택에서 빠집니다. 유의성 별표(\*)가 붙은 상관계수표, 히트맵, **표 각주·보고서용 결과 문장·AI 해석**이 나옵니다. 수량 같은 결과 변수가 있으면 그 변수 기준으로 문장을 정리합니다. 상관은 인과관계를 증명하지 않습니다.

### 📈 회귀분석 (영향 요인)
결과값(Y)을 어떤 변수(X)들이 설명하는지 확인합니다. 결과는 **설명력 R² · 수정 R² · 모형 p-value · 회귀식 · 계수표(X가 1 늘면 Y가 얼마나 변하는지 해석 포함)** 순서로 보여 줍니다. 통계 프로그램의 원문 출력(OLS Regression Results)은 `📄 통계 프로그램 원문 출력 보기 (전공자용)`에 있습니다. X가 2개 이상이면 다중공선성(VIF)도 확인합니다.

### 🤖 머신러닝 예측
기본 모형은 **랜덤포레스트**이고 다른 알고리즘은 고급 옵션에 있습니다. 결과에는 **예측력 등급(R² 0.7 이상 좋음 · 0.5~0.7 보통 · 0.5 미만 약함)**과 **평균 오차(예: ±12.3 kg/10a)**가 함께 나옵니다. 분류 문제는 가장 많은 범주로만 찍었을 때의 정확도와 비교해 보여 줍니다. 자료가 30개 미만이면 결과를 탐색적으로만 보라는 경고가 나오며, 포장시험의 처리효과 검정은 머신러닝보다 분산분석이 우선입니다.

---

## 8. 설문조사 분석

- **자동 인식**: 문항 유형을 자동으로 판별해 한 번에 분석합니다.
- **리커트 척도**: 문항별 평균·긍정 비율·응답 분포와 신뢰도(Cronbach's α)
- **객관식**: 문항별 응답 빈도·비율(도넛 그래프)
- **다중응답**: 응답률(응답자 대비)과 구성비(전체 응답 대비). 여러 개를 고를 수 있어 응답률 합계는 100%를 넘는 것이 정상입니다.
- **주관식**: 의견 목록과 AI 요약
- **교차분석**: 두 문항의 관계와 카이제곱 검정. 표의 %는 **각 집단(행) 안에서의 비율**이라 집단 크기가 달라도 바로 비교할 수 있습니다. 반대 방향 비율은 `다른 방향으로 보기`에 있습니다.

유형마다 **📋 표 각주 · 📋 보고서용 결과 문장 · 🤖 AI 해석**이 함께 나옵니다.

---

## 9. 결과 저장 (한글 · 워드 · 엑셀)

- **한글(hwpx)·워드(docx)**: 표와 그래프를 묶은 보고서 파일입니다.
- **엑셀(xlsx)**: 표와 함께 **실제 엑셀 차트**가 들어갑니다(그림이 아님). 숫자를 고치면 그래프가 바로 따라 바뀌고, 차트를 눌러 색·글꼴·축·종류를 직접 바꿀 수 있습니다. 화면과 같은 종류로 들어갑니다: 분산분석·요약표(막대), 교차분석(누적 막대), 이원배치·반복측정(꺾은선), 회귀분석(산점도+추세선), 객관식(도넛), 다중응답·변수 중요도·리커트(가로 막대), 상관분석(칸 색칠 히트맵).

---

## 10. 보고서

각 분석에서 `➕ 이 결과를 보고서에 담기`를 누른 뒤 `📑 보고서`에서 한글·워드 문서를 만듭니다. 표지·재료 및 방법을 채우면 보고서 맨 앞에 자동으로 들어가고, 통계처리 문구는 분석 이력을 바탕으로 자동 작성됩니다(복사 가능).

---

## 11. AI 도우미

API 설정은 `🧠 AI 도우미 → AI 연결 설정`에서 합니다. 연결하면 각 분석의 **🤖 AI 해석**과 오른쪽 아래 **💬 AI에게 물어보기**를 함께 쓸 수 있습니다. `이 기기에 API 키 기억`을 체크하면 그 브라우저에서는 키를 다시 넣지 않아도 되며, 로그아웃하면 지워집니다. AI 해석은 초안이므로 숫자와 결론을 연구자가 꼭 확인하세요.

---

## 12. 로그인

- **회원가입**: 이메일·비밀번호와 이름·기관 유형·소속기관을 입력합니다. 소속이 없으면 기관 유형에서 `개인 (소속 없음)`을 고르세요.
- **이메일 인증**: 가입하면 인증 메일이 옵니다. 링크는 **처음 한 번만** 누르면 되고, 이후에는 이메일·비밀번호로 로그인합니다. 메일이 안 보이면 스팸함을 확인하세요.
- **로그인 상태 유지(30일)**: 체크하면 그 브라우저에서는 창을 닫았다 열어도 바로 들어갑니다. **공용 PC에서는 체크하지 마세요.**
- **비밀번호 찾기**: `🔑 비밀번호 찾기`에서 재설정 메일을 받아 새 비밀번호를 정합니다.
- **로그아웃**: 사이드바의 `로그아웃`을 누르면 로그인 유지와 기억한 API 키가 함께 지워집니다.

---

## 13. 휴대폰·바탕화면에서 앱처럼 쓰기

- **PC(엣지)**: 주소창 오른쪽 `⋯ → 앱 → 이 사이트를 앱으로 설치`. 크롬은 `⋮ → 전송, 저장, 공유 → 바로가기 만들기`에서 '창으로 열기'를 체크하세요.
- **안드로이드(크롬)**: `⋮ → 홈 화면에 추가`
- **아이폰(사파리)**: `공유 → 홈 화면에 추가`

일반 주소와 `?mode=voice` 주소를 각각 홈 화면에 추가해 두면, 전체 기능과 음성 입력을 아이콘 하나로 바로 열 수 있습니다.

---

## 14. Version 1과 Version 2

Version 1은 자주 쓰는 분석과 쉬운 선택에 집중합니다. **경제성 분석(소득·부분예산·MRR) · 주성분분석(PCA) · 공분산분석(ANCOVA) · 프로빗(LC50) · 전처리·파생변수 등 고급 기능은 Version 2 전문형**에서 사용합니다.

- Version 2 주소: https://smart-stats-agent-v2.streamlit.app/
- 홈 화면의 `Version 2 열기 ↗`, 사이드바의 `↗ Version 2 전문형 열기` 버튼으로도 바로 열 수 있습니다.

---

## 15. 올린 자료는 어떻게 처리되나요

- 올린 엑셀·CSV·PDF·사진은 **분석하는 동안만 서버 메모리에** 있고, 따로 저장하지 않습니다. 창을 닫거나 오래 쓰지 않으면 지워집니다.
- 계정에 저장되는 것은 **회원 정보(이름·이메일·소속)**, **로그인·기능 이용 기록**(어떤 분석을 했는지), **휴대폰 음성 입력으로 만든 표**(PC에서 이어 쓰기용)뿐입니다.
- **AI 기능**(AI 해석·질문, 사진·스캔 PDF 인식, 음성 인식)을 쓰면 해당 표·글·그림·음성이 선택한 AI 회사(OpenAI·Google·Anthropic)의 해외 서버로 전송됩니다. AI를 쓰지 않으면 외부로 보내지 않습니다.
- 앱 서버는 해외 클라우드(Streamlit Community Cloud)에서 운영됩니다. **미공개 시험 자료는 소속 기관의 정보보안 지침을 확인한 뒤** 사용해 주세요.

---

## 16. 꼭 기억할 것

1. 분석 전에 데이터 점검 결과를 먼저 확인하세요.
2. 포장시험의 반복을 두었다면 반복(블록) 열이 지정되어 있는지 확인하세요.
3. p-value만 보지 말고 평균·오차·사후검정을 함께 보세요.
4. 이미지·PDF·음성 인식 결과는 분석 전에 사람이 확인하세요.
5. AI 해석과 자동 문장은 초안입니다. 숫자와 결론을 연구자가 다시 확인하세요.

---

## 17. 문의

사용 중 오류가 나거나 궁금한 점이 있으면 아래로 연락해 주세요. 오류라면 화면을 캡처해 함께 보내 주시면 빠르게 확인할 수 있습니다.

- **경상북도농업기술원 영양고추연구소 이효진**
- 이메일: hyo99@korea.kr
"""
    st.download_button("📄 설명서 내려받기 (텍스트)", _MANUAL.encode("utf-8"),
                       "사용설명서.txt", mime="text/plain")
    st.markdown(_MANUAL)
    st.divider()
    st.markdown("### Version 2 전문형")
    st.caption("경제성 분석·PCA 등 고급 기능이 필요하면 Version 2 전문형을 이용하세요.")
    if V2_APP_URL:
        st.link_button("↗ Version 2 전문형 열기", V2_APP_URL, width="stretch")
    else:
        st.info("Version 2 배포 주소가 정해지면 `V2_APP_URL` 설정값만 입력하면 버튼이 연결됩니다.")

# ================================================================ 보고서
else:
    st.title("📑 자동 보고서 생성")
    with st.expander("ℹ️ 이 기능이 뭔가요?"): st.markdown(EXPLAIN["report"])

    logs = st.session_state.get("log", [])
    with st.expander(f"🕘 분석 이력 ({len(logs)}건)"):
        if logs:
            log_df = pd.DataFrame(logs)
            smart_table(log_df, width="stretch")
            c1, c2 = st.columns(2)
            if c1.button("➕ 이력을 보고서에 담기", width="stretch"):
                st.session_state.report_items.append(
                    {"heading": "분석 수행 이력", "table": log_df,
                     "text": f"본 보고서 작성 과정에서 수행한 분석 {len(logs)}건의 기록입니다.",
                     "image": None})
                st.success("보고서에 담았습니다.")
            if c2.button("🗑️ 이력 지우기", width="stretch"):
                st.session_state.log = []; st.rerun()
        else:
            st.caption("아직 수행한 분석이 없습니다. 분석을 실행하면 자동으로 기록됩니다.")

    with st.expander("📝 표지 · 재료 및 방법 만들기 (시험연구보고서 표준 양식)", expanded=False):
        st.caption("아래를 채우면 보고서 맨 앞에 **표지**와 **재료 및 방법** 항목이 자동으로 만들어집니다. "
                   "빈칸은 생략됩니다.")
        st.markdown("###### 1) 표지 정보")
        cc1, cc2 = st.columns(2)
        pj_title = cc1.text_input("과제명", key="pj_title",
                                  placeholder="예) 고추 신품종의 생육 및 수량 특성 비교")
        pj_org = cc2.text_input("소속 기관", key="pj_org", placeholder="예) OO도농업기술원")
        cc3, cc4, cc5 = st.columns(3)
        pj_author = cc3.text_input("연구자", key="pj_author")
        pj_period = cc4.text_input("연구 기간", key="pj_period", placeholder="예) 2026. 1. ~ 2026. 12.")
        pj_keyword = cc5.text_input("색인용어", key="pj_kw", placeholder="예) 고추, 신품종, 수량")

        st.markdown("###### 2) 재료 및 방법")
        mm1, mm2 = st.columns(2)
        m_site = mm1.text_input("시험 장소", key="m_site", placeholder="예) OO연구소 시험포장")
        m_variety = mm2.text_input("공시 품종·재료", key="m_var", placeholder="예) 청양, 수비초 등 4품종")
        mm3, mm4 = st.columns(2)
        m_design = mm3.selectbox("실험 설계",
                                 ["(선택 안 함)", "난괴법(RCBD) 3반복", "난괴법(RCBD) 4반복",
                                  "완전임의배치(CRD) 3반복", "완전임의배치(CRD) 4반복",
                                  "분할구법(Split-plot) 3반복", "요인배치법"], key="m_design")
        m_area = mm4.text_input("구당 면적", key="m_area", placeholder="예) 10㎡ (3.3m × 3m)")
        m_treat = st.text_area("처리 내용", key="m_treat", height=80,
                               placeholder="예) 1. 대조구(관행)  2. 처리1(질소 20% 증시)  3. 처리2(질소 40% 증시)")
        m_manage = st.text_area("재배 관리", key="m_manage", height=80,
                                placeholder="예) 정식 5월 10일, 시비량 N-P-K = 19-11-14kg/10a, 관행 방제")
        m_survey = st.text_area("조사 항목 및 방법", key="m_survey", height=80,
                                placeholder="예) 초장·엽수는 정식 후 30일 간격 5주 조사, 수량은 수확기별 전량 계량")

        st.markdown("###### 3) 통계처리 문구 (자동 생성)")
        auto_cv = st.text_input("CV(%) — 분산분석에서 확인한 값 (선택)", key="m_cv", placeholder="예) 12.3")
        stat_text = build_stat_method_text(
            logs, {"design": None if m_design.startswith("(") else m_design,
                   "cv": auto_cv.strip() or None})
        st.code(str(stat_text).replace(". ", ".\n"), language=None, wrap_lines=True)
        st.caption("분석 이력을 바탕으로 자동 작성되었습니다. 오른쪽 위 📋 버튼으로 복사해 필요하면 수정하세요.")

        if st.button("➕ 표지·재료및방법을 보고서 맨 앞에 넣기", width="stretch"):
            new_items = []
            if pj_title or pj_org or pj_author:
                cover = []
                if pj_title: cover.append(f"◦ 과제명 : {pj_title}")
                if pj_org: cover.append(f"◦ 소속 : {pj_org}")
                if pj_author: cover.append(f"◦ 연구자 : {pj_author}")
                if pj_period: cover.append(f"◦ 연구기간 : {pj_period}")
                if pj_keyword: cover.append(f"◦ 색인용어 : {pj_keyword}")
                new_items.append({"heading": "시험연구", "text": "\n".join(cover),
                                  "table": None, "image": None})
            mm_parts = []
            if m_site: mm_parts.append(("시험 장소", m_site, False))
            if m_variety: mm_parts.append(("공시 품종·재료", m_variety, False))
            if not m_design.startswith("("): mm_parts.append(("시험 설계", m_design, False))
            if m_area: mm_parts.append(("구당 면적", m_area, False))
            if m_treat: mm_parts.append(("처리 내용", m_treat, True))
            if m_manage: mm_parts.append(("재배 관리", m_manage, True))
            if m_survey: mm_parts.append(("조사 항목 및 방법", m_survey, True))
            mm_parts.append(("통계 처리", stat_text, True))
            _KOR = "가나다라마바사아자차"
            mm_lines = []
            for _i, (t, v, nl) in enumerate(mm_parts):
                head = _KOR[_i] if _i < len(_KOR) else str(_i+1)
                if nl:
                    mm_lines.append(f"{head}. {t}")
                    for _ln in strip_md(v).split("\n"):
                        if _ln.strip():
                            _c = _ln.strip()
                            mm_lines.append(_c if _c.startswith(("○", "-", "•")) else f"  ○ {_c}")
                else:
                    mm_lines.append(f"{head}. {t} : {v}")
            new_items.append({"heading": "Ⅰ. 재료 및 방법", "text": "\n".join(mm_lines),
                              "table": None, "image": None})
            for it in reversed(new_items):
                st.session_state.report_items.insert(0, it)
            log_action("표지·재료및방법 작성")
            st.success("보고서 맨 앞에 넣었습니다!")
            st.rerun()

    with st.expander("📎 연구계획서·결과보고서 첨부 (보고서 앞부분에 넣기)"):
        st.caption("계획서나 기존 보고서 파일을 올리면 그 내용을 이 보고서 맨 앞에 넣을 수 있어요. "
                   "(hwpx·docx·pdf·txt·csv·xlsx 지원)")
        planf = st.file_uploader("파일 첨부", type=["hwpx", "docx", "pdf", "txt", "md", "csv", "xlsx"],
                                 key="report_plan")
        if planf is not None:
            ptext = read_uploaded_text(planf, limit=20000)
            if ptext.startswith("⚠️"):
                st.warning(ptext)
            else:
                st.success(f"'{planf.name}'에서 {len(ptext):,}자를 읽었습니다.")
                mode_p = st.radio("어떻게 넣을까요?",
                                  ["원문 그대로", "AI로 핵심만 정리 (키 필요)"], horizontal=True)
                sec_title = st.text_input("섹션 제목", value="Ⅰ. 연구 개요")
                with st.expander("읽어온 내용 미리보기"):
                    st.text(ptext[:2000] + ("..." if len(ptext) > 2000 else ""))
                if st.button("➕ 계획서 내용을 보고서 앞에 넣기"):
                    content = ptext
                    if mode_p.startswith("AI"):
                        with st.spinner("AI가 계획서를 정리하는 중..."):
                            content = ai_call(
                                "다음은 농업 연구계획서(또는 결과보고서)입니다. 시험 목적, 처리 내용, "
                                "조사 항목, 방법을 보고서 서두에 넣을 수 있도록 간결한 개요로 한국어로 "
                                "정리해 주세요. 없는 내용은 지어내지 마세요.\n\n" + ptext,
                                st.session_state.get("api_key"),
                                st.session_state.get("ai_model_g"),
                                max_tokens=1500)
                    st.session_state.report_items.insert(
                        0, {"heading": sec_title, "text": content, "table": None, "image": None})
                    st.success("보고서 맨 앞에 넣었습니다!")
                    log_action("계획서를 보고서에 첨부")
                    st.rerun()

    items = st.session_state.report_items

    with st.expander("📄 적요(요약) 자동 초안 만들기"):
        st.caption("보고서에 담긴 분석 결과를 읽어 시험연구보고서의 **적요** 초안을 만듭니다. "
                   "결과를 먼저 담은 뒤 눌러 주세요.")
        ab_purpose = st.text_input("시험 목적 (선택)", key="ab_purpose",
                                   placeholder="예) 고추 신품종의 생육 및 수량 특성을 구명하고자")
        ab1, ab2 = st.columns(2)
        ab_design = ab1.text_input("시험 설계 (선택)", key="ab_design",
                                   value=st.session_state.get("m_design", "") if not str(
                                       st.session_state.get("m_design", "")).startswith("(") else "",
                                   placeholder="예) 난괴법 3반복")
        ab_cv = ab2.text_input("CV(%) (선택)", key="ab_cv", placeholder="예) 8.5")
        draft = build_abstract(items, {"purpose": ab_purpose.strip() or None,
                                       "design": ab_design.strip() or None,
                                       "cv": ab_cv.strip() or None})
        st.markdown("###### 자동 생성된 적요 초안")
        st.code(draft, language=None)
        cbtn1, cbtn2 = st.columns(2)
        if cbtn1.button("➕ 적요를 보고서 맨 앞에 넣기", width="stretch"):
            st.session_state.report_items.insert(
                0, {"heading": "적요(要約)", "text": draft, "table": None, "image": None})
            log_action("적요 자동 생성")
            st.success("보고서 맨 앞에 넣었습니다!"); st.rerun()
        if st.session_state.get("api_key"):
            if cbtn2.button("✨ AI로 다듬기", width="stretch"):
                with st.spinner("AI가 문장을 다듬는 중..."):
                    polished = ai_call(
                        "다음은 농업 시험연구보고서의 적요 초안입니다. 학술 보고서 문체("
                        "'~하였다', '~로 나타났다')로 자연스럽게 다듬어 주세요. "
                        "새로운 사실을 추가하지 말고, 있는 내용만 정리하세요.\n\n" + draft,
                        st.session_state.get("api_key"), st.session_state.get("ai_model_g"),
                        max_tokens=900)
                    st.markdown(polished)
                    ai_disclaimer()
        else:
            cbtn2.caption("AI 키를 넣으면 문장을 더 다듬을 수 있어요.")

    if not items:
        st.info("아직 담긴 분석이 없어요. 각 분석에서 '➕ 이 결과를 보고서에 담기'를 눌러 추가하세요.")
    else:
        st.write(f"**현재 담긴 분석: {len(items)}개**")
        for i, it in enumerate(items):
            c1, c2 = st.columns([6, 1])
            blks = it.get("blocks")
            if blks:
                nt = sum(1 for b in blks if b.get("table") is not None)
                ni = sum(1 for b in blks if b.get("image"))
                info = f"　📊표 {nt}개" + (f"　🖼️그림 {ni}개" if ni else "")
            else:
                info = ("　📊표" if it.get("table") is not None else "") + \
                       ("　🖼️그림" if it.get("image") else "")
            c1.write(f"{i+1}. {it['heading']}{info}")
            if c2.button("삭제", key=f"rm_{i}"):
                st.session_state.report_items.pop(i); st.rerun()
        _tabs, _figs = collect_captions(items)
        if _tabs or _figs:
            with st.expander(f"📑 표·그림 목차 미리보기 (표 {len(_tabs)}개, 그림 {len(_figs)}개)"):
                if _tabs:
                    st.markdown("**표 목차**")
                    st.text("\n".join(_tabs))
                if _figs:
                    st.markdown("**그림 목차**")
                    st.text("\n".join(_figs))
                if st.button("➕ 목차를 보고서 앞에 넣기", width="stretch"):
                    toc = ""
                    if _tabs: toc += "표 목차\n" + "\n".join(_tabs) + "\n\n"
                    if _figs: toc += "그림 목차\n" + "\n".join(_figs)
                    st.session_state.report_items.insert(
                        0, {"heading": "표·그림 목차", "text": toc.strip(),
                            "table": None, "image": None})
                    log_action("표·그림 목차 생성")
                    st.success("넣었습니다!"); st.rerun()
        rtitle = st.text_input("보고서 제목", value="2026 실험 통계 분석 보고서")
        st.caption("한글이 안 열리는 컴퓨터에서는 워드(docx)로 받으세요.")
        if not _HAS_DOCX:
            st.warning("⚠️ 현재 배포 서버에서 워드(docx) 저장 기능이 비활성화되어 있습니다. "
                       "한글(hwpx)을 이용하거나 관리자에게 문의하세요.")
        gen = st.checkbox("📄 보고서 파일 만들기", key="gen_report",
                          help="체크하면 문서를 생성합니다. (체크 전에는 만들지 않아 화면이 빠릅니다)")
        c1, c2, c3 = st.columns(3)
        if gen:
            with st.spinner("보고서를 만드는 중..."):
                with c1:
                    st.download_button("📘 한글(hwpx)", build_report_hwpx(items, rtitle),
                                       "통계분석.hwpx", width="stretch")
                with c2:
                    if _HAS_DOCX:
                        st.download_button("📝 워드(docx)", build_report_docx(items, rtitle),
                                           "통계분석.docx", width="stretch")
                    else:
                        st.caption("워드(docx): 현재 배포 환경에서 비활성화")
        with c3:
            if st.button("🗑️ 전체 비우기", width="stretch"):
                st.session_state.report_items = []; st.rerun()
