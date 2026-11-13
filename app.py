# -*- coding: utf-8 -*-
"""
고추 쑥쑥이 (고추 작황·기상 진단판)
경북 북부 6개 시군 노지고추 — 영양고추연구소 「고추 생산 변동 요인 분석」 연구 활용 앱

실행: Anaconda Prompt에서 이 파일이 있는 폴더로 이동 후  streamlit run app.py

app.py와 같은 폴더에 아래 파일을 넣어두면 자동으로 찾습니다.
(파일 이름 앞뒤에 ♥♡★☆ 같은 기호가 붙어 있어도 괜찮습니다)
  - 농업기상_6개지역_정제본.csv     (없으면 5개지역 파일)
  - ASOS_안동_2010_2025.csv         (이름에 'ASOS'가 들어간 csv) ★ 일사량 최종 보정에 필요
  - 상반기 작황조사 정리본 .xlsx    (이름에 '상반기'가 들어간 xlsx)
  - 하반기 작황조사 취합 .xlsx      (이름에 '하반기'가 들어간 xlsx)
  - 6개시군_생산량_20102024.csv     (이름에 '생산량'이 들어간 csv)

올해(시즌 중) 기상은 앱 왼쪽 '올해 기상자료 넣기'에서 CSV를 올리면 됩니다.
  - 기상자료개방포털 ASOS·AWS 일자료 CSV, 농업기상 관측 CSV 모두 열 이름으로 자동 인식
  - 같은 폴더에 이름에 '올해기상'이 들어간 CSV를 두면 자동으로 읽음

연구 요약·자료 품질 점검 탭은 앱 주소 뒤에 ?mode=research 를 붙였을 때만 보입니다.
  (예: http://localhost:8501/?mode=research — 발표 때는 이 주소로 여는 것을 권함)

2026-11-13 갱신 사항 (3차)
  - 착과 전 고온 기준을 관측소 33℃로 전환 (포장 센서 34℃ 상당: 2021~2025 평균 일수 일치).
    '포장 평년 +2.7일' 보정 제거(이중 보정 방지), 감수 범위 상한을 센서 34℃ 총수확량 3.2%/일로 교체
  - 자료 품질 점검 탭을 연구자 화면(?mode=research)으로 이동
  - 기준일을 10월 31일까지 선택 가능 (평년 비교 그래프도 10월 말까지. 판정 집계 창은 그대로)
  - '왜 하필 7/3~7/28인가' 창 민감도·기준 온도 재표집 설명 추가 (11/13 분석)
  - 올해 값이 API 수신분일 때 관측망 차이 안내 한 줄 표시
  - 관수 × 고온 p값을 사전 지정 검정 값(0.65)으로 정정, 조기예측 역변환 미보정 한계 명시
  - 내 포장 비교 판정을 P10/중앙/P90 형식으로
  - 탭-본문 간격 축소, 설명서 내려받기 버튼 간격·'이 앱을 쓰는 세 가지 때' 표 정리

2026-11-12 갱신 사항 (2차)
  - 기상청 API허브 자동 갱신: .streamlit/secrets.toml 에 KMA_API_KEY = "발급키" 를 넣으면
    앱이 열릴 때 기본 자료 이후의 올해 일자료를 자동으로 받아옵니다 (6시간마다 갱신)
    · ASOS(안동 136, 봉화 271, 청송군 276, 의성 278): 종관 일자료 kma_sfcdd3.php
    · AWS(영양·예천): 지상·AWS 일통계 sfc_aws_day.php (최고·최저기온, 강수량.
      평균기온은 (최고+최저)/2, 일사량 없음. 지점번호는 지점정보에서 자동으로 찾음)
  - 오늘의 진단 보고용 요약에 남은 기간 전망(과거 패턴 기준) 한 줄 추가
  - 내 포장 비교(하반기) 입력값을 수확량 조기예측 7월 말 식으로 불러오는 버튼 추가

2026-11-12 갱신 사항
  - 앱 이름을 '고추 쑥쑥이'로 변경
  - 화면 구성(농가·지도사용/연구자용) 구분 제거: 대시보드·자료 품질 점검 탭은 항상 표시,
    연구 요약 탭만 주소에 ?mode=research 를 붙였을 때 표시
  - 사이드바 정리: 기상자료 파일명 표시·일사량 구성 칸 제거, 자료실은 토글 없이 바로 표시
  - 설명 문구 다듬기(연구 방법 관련 문장 정리), 표 첫 칸 줄바꿈 방지
  - 내 포장 비교: 노지1열·노지2열만 비교(터널 제외), 재식밀도 설명 칸 제거
  - 생육량 지수 보기: 입력(표준편차 슬라이더)을 맨 위로 이동

2026-11-09 갱신 사항
  - 첫 탭 '오늘의 진단': 기준일에 맞춘 판정, 남은 기간 전망, 할 일, 포장 온도계 입력, 보고용 요약
  - 올해 기상자료 넣기 (시즌 중 진단이 되도록)
  - 화면 구성 전환(농가·지도사용 / 연구자용), 병해충 발생 위험·평년 탭 (11/2 오후판 기능 복원)
  - 농가 정밀조사 2026 포함 재분석 수치 반영 (착과 전 고온, 생육량 지수, 조기예측, 위성)
  - 착과 전 고온 영향은 kg/10a 대신 감수 범위(1일당 0.5~6.3%)로 표시
  - 관수 × 고온 완화(3년 자료에서 소멸), 생육량-비상품과 상충(소멸) 삭제

2026-10-23 갱신 사항
  - 일사량 최종 구성 반영: 봉화 ×0.899 / 안동 전 기간 ASOS 실측 / 예천 2016~2019 안동ASOS ×0.919
  - 착과 전 고온일(7/3~7/28, 34℃) 지표 추가
  - 일사량 × 강수량 보완관계 추가 (연도 고정효과를 통과한 유일한 기상 결과)
  - 수확량 전망 탭을 생육 조사 기반 조기예측 모형으로 교체
  - 재식밀도 비교 제거 (측정 변동 때문에 비교 불가)
  - 관수 구분에서 분사호스와 스프링클러 분리
"""
import html as _html
import io
import os
import re
from datetime import date, timedelta

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
import streamlit.components.v1 as components

# ─────────────────────────────────────────────
# 설정
# ─────────────────────────────────────────────
HERE = os.path.dirname(os.path.abspath(__file__))
WEATHER_KEYS = ["농업기상_6개지역_정제본", "농업기상_5개지역_정제본"]
SIGUN_ORDER = ["영양군", "안동시", "봉화군", "의성군", "청송군", "예천군"]
SEASON_START = (5, 1)   # 화면 진단용 생육기 시작 (정식기)
SEASON_END = (10, 31)   # 화면 기준일 선택 상한 (판정 집계 창은 지표별 고정, 최대 9/30)
# 회귀 분석 패널의 '생육기' 창. 일사량·강수량 파생변수는 이 창으로 만들었다.
# 이 창으로 계산하면 보고서의 강수량 4분위(762 / 886 / 1041mm)가 그대로 재현된다.
PANEL_WINDOW = ("04-01", "10-31")
LAT = 36.9              # 청천지수 계산용 위도 (경북 북부)

COL = {
    "tavg": "평균기온 (1.5m)",
    "tmax": "최고기온 (1.5m)",
    "tmin": "최저기온 (1.5m)",
    "rh": "평균습도 (1.5m)",
    "rain": "강수량 (mm)",
    "solar": "일사량 (MJ/m²)",
    "dew": "결로시간 (분)",
}

C_THIS = "#2a78d6"     # 선택 연도 / 내 포장
C_MEAN = "#6f6e69"     # 평년 평균선
C_BAND = "rgba(140,139,133,0.22)"  # 평년 범위
C_OTHER = "#c9c8c2"    # 다른 연도 막대
C_ALERT = "#e34948"    # 문제 구간 표시
C_OK = "#1baf7a"
SIGUN_COLOR = {        # 시군 색은 항상 고정
    "영양군": "#2a78d6", "안동시": "#eb6834", "봉화군": "#1baf7a",
    "의성군": "#eda100", "청송군": "#e87ba4", "예천군": "#008300",
}

# ── 일사량 최종 구성 (기상자료_최종구성_확정_261018 문서 4번 항목) ──
# 봉화: 자신의 정상 구간 청천지수에 맞춘 비율 보정
SOLAR_RATIO_FIX = [("봉화군", "2016-01-01", "2017-05-30", 0.899)]
# 안동: 관측값에 계통 오차가 있어 전 기간 ASOS 실측으로 대체
ASOS_REPLACE = {"안동시": "안동"}
# 예천: 2016~2019 일사량이 안동 복제 구간 → 안동 ASOS에 실측 비율을 곱해 환산
YECHEON_PROXY = ("예천군", "안동", "2019-12-31", 0.919)

# ── 연구 결과 계수 (보고서 수치가 바뀌면 여기만 고치면 됨) ──
# 착과 전 고온일 (7/3~7/28, 최고 34℃ 이상)
HEAT_PRE = {
    "창": "7월 3일~28일", "임계": 33.0,   # 관측소 기준. 포장 센서 34℃ 상당 (2021~2025 평균 일수 일치)
    "시군계수": -1.516, "시군SE": 0.264, "시군p": "<0.001",  # 단수 kg/10a/일, grp within + 일사량 통제, 연도 클러스터
    # 농가 센서 (17농가 59행, 2021·2023~2026, 농가+연도 FE, WCR p) — 농가패널_2018_2026_재분석_261103
    "센서표본": "17농가 59행(2021, 2023~2026)",
    "센서과수": -3.0, "센서과수p": "0.013",                  # 34℃ 주당 수확과수 %/일
    "센서총량": -3.2, "센서총량p": "0.031~0.062",            # 34℃ 주당 총수확량 (경계 수준)
    "센서과수33": -3.9, "센서과수33p": "0.002",              # 33℃ 주당 수확과수
    "센서총량33": -6.3, "센서총량33p": "0.003",              # 33℃ 주당 총수확량
    "센서과중": -0.2, "센서과중p": "0.836",                  # 34℃ 평균 과중
    "센서과중33": -2.4, "센서과중33p": "0.083",              # 33℃ 평균 과중 (경계, 비유의)
    "연도제외": "-2.6~-4.1%", "연도제외주의": "2021년을 빼면 p=0.25, 2025년을 빼면 p=0.09",
    "분지수": -0.40, "분지수p": "0.013",                     # 고온일 1일당 8월 말 분지수
    "생육통제": -1.7, "생육통제p": "0.15",                   # 분지수·초장 통제 후 수확과수
    # 시군 관측소와 같은 행 비교 (2021~2025 48행, 2026 시군 기상 없음)
    "관측소과수": 0.7, "관측소과수p": "0.772",
    # 포장 해발 100m당 (센서 17농가, 연도 FE, 2021~2025) — 농가포장_해발_지대분석_261101
    "해발기온": -0.56, "해발일수": -2.0,
    "센서기온차": 0.96, "센서일수차": 2.7,                    # 포장 센서 - 시군 관측소 (2021~2025)
}
# 착과 전 고온일이 평년보다 n일 많을 때 감수 범위 (영농기술정보 A 경제성 표와 같은 식)
#   앱의 고온일은 관측소 33℃ 기준(포장 센서 34℃ 상당)이라 센서 34℃ 계수와 짝을 맞춘다
#   하한: 시군 단수 계수 1.52 ÷ 6개 시군 평균 단수 300.6 = 1일당 약 0.5% (관측소 34℃ 기준 계수, 참고)
#   상한: 포장 센서 34℃ 총수확량 -3.2%/일 → 1 - 0.968^n
LOSS_LOW_PER_DAY = 0.5
LOSS_HIGH_KEEP = 0.968


def loss_range(n_days):
    """평년보다 많은 고온일 수 → (하한 %, 상한 %)"""
    n = max(0.0, float(n_days))
    return LOSS_LOW_PER_DAY * n, (1 - LOSS_HIGH_KEEP ** n) * 100
# 일사량 × 강수량 (시군+연도 2-way FE, 시군 클러스터 p=0.0008)
SOLAR_RAIN = {
    "교호계수": 0.0407, "중심강수": 886.0, "중심효과": 22.9,
    "분위": [(762.0, 17.9, -1.0, 37.4, "0.068"),
             (886.0, 22.9, 2.7, 42.3, "0.024"),
             (1041.0, 29.2, 8.2, 50.8, "0.007")],
}
# 일사량 주효과 (2변수 편회귀, grp within + 연도 클러스터)
SOLAR_MAIN = {"계수": 11.038, "SE": 4.687, "p": "0.019"}
# 조기예측 모형 (농가 패널, 연도 단위 교차검증)
#   8월 말: 2021~2026 75행 19농가 (농가패널_2018_2026_재분석_261103, 조기예측_조사일점검_261109)
#   6월 말·7월 말: 2021~2025 63행 식 (2026 포함 계수가 문서에 없어 그대로 둠, 오차는 2026 포함값)
MODEL_EARLY = {
    "6월 말": dict(const=5.589, b_h=0.0180, b_f=0.0, b_c=0.0,
                  vars=["초장"], mape=22.3, r2=0.34, src="2021~2025 63행 식"),
    "7월 말": dict(const=4.730, b_h=0.0166, b_f=0.172, b_c=0.0,
                  vars=["초장", "착과수"], mape=22.0, r2=0.38, src="2021~2025 63행 식"),
    "8월 말": dict(const=1.780, b_h=0.0056, b_f=0.206, b_c=0.587,
                  vars=["초장", "착과수", "누적수확"], mape=12.6, r2=0.75, src="2021~2026 75행 식"),
}
MAPE_BASE = 29.5        # 아무 정보가 없을 때 (다른 해 평균으로 예측)
EARLY_CHECK = {         # 8월 말 모형 검증 보강 (조기예측_조사일점검_농가연도제외검증_261109)
    "기준선": 17.1,           # 8/31까지 누적 수확량만 쓴 모형
    "농가연도제외": 12.8,     # 농가와 연도를 함께 빼고 검증
    "사전예측": 8.2,          # 2021~2025로 식을 만들어 2026년을 예측 (편향 -2.7%)
    "사전편향": -2.7,
    "편향범위": "-9.4~+7.8%", # 연도별 평균 편향 (2025 -9.4%, 2024 +7.8%)
    "9월중순": 7.8,
}
# 조기예측 입력 기본값. 식의 초장·착과수는 '그 시점 직전 마지막 조사값'이다.
#   7월 말은 하반기 작황조사 7월 말 중앙값(초장 101.3, 착과수 44) 근처
EARLY_DEFAULTS = {
    "6월 말": dict(초장=60.0),
    "7월 말": dict(초장=100.0, 착과수=44.0),
    "8월 말": dict(초장=100.0, 착과수=25.0, 누적수확=400.0),
}
# 생육량 지수 (8월말 초장·주경장·줄기굵기·분지수·착과수 표준화 단순평균)
#   반복조사 19농가 81행 (2018~2026), 농가·연도 FE, WCR — 생육량지수_시점별지표_2026포함_재계산_261109
IDX_EFFECT = {
    "표본": "19농가 81행",
    "수량_ln": 0.231,       # → +26.0% (95% CI 16.8~35.9, WCR p<0.001)
    "과수_ln": 0.154,       # → +16.6% (WCR p=0.002)
    "과중": 8.0, "과중p": "0.068",
    "환산": [("초장", 11.8, "cm"), ("주경장", 3.5, "cm"), ("줄기굵기", 1.6, "mm"),
             ("분지수", 2.0, "개"), ("착과수", 11.6, "개")],
    "최대초장": 1.35, "최대초장범위": "+1.18~+1.59",
}
# 시점별 지표 1 표준편차당 주당수확량 변화 (%, WCR p)
IDX_TIMING = [
    ("초장", "+24.2%", "0.001", "+10.4%", "0.156"),
    ("주경장", "+5.9%", "0.353", "+6.7%", "0.359"),
    ("줄기굵기", "+16.6%", "0.002", "+13.9%", "0.033"),
    ("분지수", "+9.2%", "0.022", "+5.0%", "0.098"),
    ("착과수", "+12.2%", "0.002", "+5.7%", "0.252"),
]
# 위성 식생지수 (조사포장 필지, 농가·연도 FE, 17농가 71행) — 위성식생지수_2026포함_재분석_261109
SAT = {"NDVI": 176.2, "NDVIp": "0.009", "NDRE": 239.7, "NDREp": "0.002",
       "농가제외": "17/17 유의 (143~211g)", "연도제외": "7번 중 6번 유의",
       "생육량r": 0.39, "고온NDVIp": "0.19", "고온남음": 87}

# ── 병해충 발생 위험 판정 기준 (영농기술정보 B와 같은 기준, 사이드바 조정과 관계없이 고정) ──
#   조사 전(7/31까지) 날씨로 판정. 작황조사 54사례(6개 시군 × 2016~2024)로 정한 기준이다.
PEST_TH = dict(hot_pre=33.0, rain_wet=1.0, tan_use_tmax=False, tan_tmax=25.0, hot=30.0,
               heat=33.0, cold=13.0, rain_good=5.0, rain_dry=1.0)
PEST_RULES = {
    "탄저": dict(name="탄저병", start="06-15", cut=20, high_bad=True, col="탄저병(개)",
                rule="6월 15일~7월 31일 비(1mm 이상) 온 날 20일 이상",
                note="기준을 넘은 해 발생 포장 28.1%, 넘지 않은 해 8.7%(약 3배). 시군 평년보다 뚜렷이 "
                     "많았던 8사례 중 7사례가 이 기준에 들었으나, 기준을 넘은 해의 절반가량은 평년 수준이었습니다. "
                     "'다발 확정'이 아니라 **예찰·방제 강화 신호**입니다."),
    "고온": dict(name="담배나방", start="06-01", cut=35, high_bad=True, col="담배나방(개)",
                rule="6월 1일~7월 31일 최고 30℃ 이상인 날 35일 이상",
                note="고온일이 많은 해에 담배나방 발생 포장이 많았습니다(시군 내 상관 0.43)."),
    "건조": dict(name="석회결핍", start="05-01", cut=15, high_bad=False, col="석회결핍(개)",
                rule="5월 1일~7월 31일 비다운 비(5mm 이상) 온 날 15일 이하",
                note="비다운 비가 적은 해에 석회결핍 발생 포장이 많았습니다(시군 내 상관 -0.44). "
                     "가문 해에는 점적관수 포장에서도 발생이 줄지 않았습니다."),
}
PEST_END = "07-31"
# 평년 발생 포장 비율 (작황조사 파일에서 계산): (화면 이름, 열 이름, 발생 판정)
PEST_LIST_H = [("탄저병", "탄저병(개)", "개"), ("담배나방", "담배나방(개)", "개"),
               ("석회결핍", "석회결핍(개)", "개"), ("바이러스", "바이러스(1-9)", "등급"),
               ("총채벌레", "총채벌레(1-9)", "등급"), ("세균반점", "세균반점(1-9)", "등급")]
PEST_LIST_S = [("시들음", "시들음유무"), ("진딧물", "진딧물 유무"), ("총채벌레", "총채벌레 유무"),
               ("파밤나방", "파밤나방 유무"), ("세균반점", "세균반점 유무")]

# 기상 효과를 수확량 전망에 직접 곱하지 않는 이유는 아래 주석 참고.
#   착과 전 고온 효과(-3.0%/일)는 농가 포장 센서 기준이다. 같은 행(2021~2025 48행)에 시군 관측소 값을
#   넣으면 +0.7%(p=0.772)로 효과가 0이다. 이 앱은 시군 관측소 자료를 쓰므로,
#   센서 계수를 관측소 일수에 곱하면 근거 없는 숫자가 된다.
#   시군 단수 모형의 -1.52 kg/10a/일은 '참고 영향'으로만 보여준다.
WEATHER_EFFECTS = {}

# 수확 종료 기준 (원특원 재배작기 영농정보: 평균기온 12℃ 이하 첫날)
#   경북 북부 농가 실제 끝수확일과 r=0.57 (69건, 2018~2025), 농가가 평균 5일 일찍 끝냄
HARVEST_END = {"임계": 12.0, "r": 0.57, "n": 69, "차이": 5}

# 작황조사 검증 창: 하반기 조사가 7월 말~8월 초 1회라, 검증은 조사 전 날씨(7/31까지)로만 한다
VALID_END = "07-31"
VALID_BINS = {   # 영농기술정보_후보검토_261029 6번 항목의 구간
    "탄저": [(0, 15), (16, 19), (20, 999)],
    "고온": [(0, 25), (26, 34), (35, 999)],
    "건조": [(0, 15), (16, 20), (21, 999)],
}

st.set_page_config(page_title="고추 쑥쑥이", page_icon="🌶️", layout="wide")


# ─────────────────────────────────────────────
# 디자인 (화면 스타일)
#   색: 고추 빨강(제목·탭 강조), 잎 초록(보조), 따뜻한 미색 바탕
#   CSS 안에는 물결표를 쓰지 않는다 (_keep_tilde가 바꿔버림)
# ─────────────────────────────────────────────
BRAND = {"red": "#9C3F30", "red2": "#B8604A", "green": "#2F6B3A", "ink": "#1F1B18",
         "muted": "#6B6560", "line": "#E8E1D8", "bg": "#FAF8F5", "card": "#FFFFFF", "side": "#F3EEE7"}
FONT = "'Pretendard', 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif"

APP_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css');
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background: %(bg)s; }
.stApp { color: %(ink)s; font-family: %(font)s; }
.stApp p, .stApp li, .stApp label, .stApp td, .stApp th,
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp input, .stApp textarea { font-family: %(font)s; }
[data-testid="stHeader"] { background: rgba(250, 248, 245, .9); }
.block-container { padding-top: 3.4rem; padding-bottom: 4rem; max-width: 1240px; }

/* 머리 배너 */
.hero { background: linear-gradient(135deg, rgba(110, 43, 36, .80) 0%%, rgba(156, 63, 48, .74) 50%%, rgba(184, 96, 74, .68) 100%%);
        color: #fff; border-radius: 20px; padding: 26px 32px 22px; margin-bottom: 16px;
        box-shadow: 0 6px 20px rgba(110, 43, 36, .10); position: relative; overflow: hidden;
        min-height: 150px; }
.hero-text { position: relative; z-index: 1; max-width: calc(100%% - 190px); }
.hero-mascot { position: absolute; right: 34px; top: 50%%; transform: translateY(-50%%) rotate(-8deg);
               width: 152px; height: 152px; border-radius: 50%%; background: #FAF8F5;
               display: flex; align-items: center; justify-content: center; z-index: 1;
               box-shadow: 0 6px 18px rgba(0,0,0,.15); }
.hero-mascot svg { width: 126px !important; height: 144px !important; max-width: none !important; flex: none; }
@media (max-width: 820px) { .hero-mascot { display: none; } .hero-text { max-width: 100%%; } }
.hero::after { content: ""; position: absolute; right: -60px; top: -60px; width: 240px; height: 240px;
               border-radius: 50%%; background: rgba(255,255,255,.08); }
.hero-badge { display: inline-block; font-size: .78rem; font-weight: 600; letter-spacing: .02em;
              background: rgba(255,255,255,.16); padding: 4px 10px; border-radius: 999px; margin-bottom: 10px; }
.hero-title { font-size: 2.05rem; font-weight: 800; line-height: 1.25; margin: 0 0 6px;
               text-shadow: 0 1px 2px rgba(80, 25, 20, .25); }
.hero-sub { font-size: .98rem; opacity: .92; margin-bottom: 14px; }
.hero-chips span { display: inline-block; font-size: .8rem; font-weight: 600; margin: 0 6px 6px 0;
                   padding: 5px 11px; border-radius: 999px; background: #fff; color: %(red)s; }
.hero-guide { font-size: .82rem; opacity: .9; margin-top: 4px; }

/* 탭: 글자 + 밑줄만 */
.stTabs [data-baseweb="tab-list"] { gap: 6px; border-bottom: 1px solid %(line)s; flex-wrap: wrap; }
.stTabs [data-baseweb="tab"] { padding: 10px 6px; font-weight: 600; color: #8A847E; background: transparent; }
.stTabs [data-baseweb="tab"]:hover { color: %(red)s; }
.stTabs [aria-selected="true"] { color: %(ink)s !important; }
.stTabs [data-baseweb="tab-highlight"] { background-color: %(red)s; height: 2px; }
.stTabs [data-baseweb="tab-border"] { display: none; }

/* 소제목 */
.stApp h3 { font-weight: 700; color: %(ink)s; letter-spacing: -.01em; margin-top: .6rem; }
.stApp h4 { font-weight: 700; color: %(ink)s; }

/* 지표 카드: 얇은 선 하나 */
[data-testid="stMetric"] { background: #FFFFFF; border: 1px solid %(line)s; border-radius: 12px;
                           padding: 14px 16px 12px; }
[data-testid="stMetricLabel"] p { font-size: .85rem; font-weight: 600; color: %(muted)s; }
[data-testid="stMetricValue"] { font-weight: 700; color: %(ink)s; letter-spacing: -.01em; }

/* 펼침·표·알림 */
[data-testid="stExpander"] details { border: 1px solid %(line)s !important; border-radius: 10px; background: #FFFFFF; }
[data-testid="stExpander"] summary p { font-weight: 600; color: #3A3530; }
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
[data-testid="stAlert"] { border-radius: 10px; }

/* 사이드바 */
[data-testid="stSidebar"] { background: %(side)s; border-right: 1px solid %(line)s; }
[data-testid="stSidebar"] h2 { font-size: 1.05rem; font-weight: 700; color: %(ink)s; }

.stDownloadButton button, .stButton button { border-radius: 8px; font-weight: 600; }
hr { border-color: #EEEBE7; }

/* 마크다운 표: 첫 칸(지표·용어 이름)이 두 줄로 꺾이지 않게 */
.stMarkdown table td:first-child, .stMarkdown table th:first-child { white-space: nowrap; }

/* 탭과 본문 사이 간격 줄이기 */
.stTabs [data-baseweb="tab-panel"] { padding-top: 0.35rem; }

/* 사용 설명서 '이 앱을 쓰는 세 가지 때' 표: 둘째 칸(누가)도 한 줄로 */
.st-key-uses_tbl table td:nth-child(2), .st-key-uses_tbl table th:nth-child(2) { white-space: nowrap; }
</style>
""" % dict(BRAND, font=FONT)

# 그래프 글꼴·색을 화면과 맞춤
pio.templates["gochu"] = go.layout.Template(layout=dict(
    font=dict(family=FONT.replace("'", ""), size=13, color="#3A3430"),
    hoverlabel=dict(font=dict(family=FONT.replace("'", ""))),
    legend=dict(font=dict(size=12)),
))
pio.templates.default = "plotly_white+gochu"


def apply_design():
    st.markdown(APP_CSS, unsafe_allow_html=True)


MASCOT_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 140 160" width="126" height="144" preserveAspectRatio="xMidYMid meet"> <ellipse cx="70" cy="150" rx="30" ry="5" fill="#000" opacity=".12"/> <path d="M66 30 C64 18, 70 10, 82 7" stroke="#3F7D3A" stroke-width="7" fill="none" stroke-linecap="round"/> <path d="M40 120 C24 96, 26 60, 38 38 C52 30, 86 30, 100 38 C110 62, 104 100, 84 128 C76 140, 60 142, 52 136 C46 132, 44 126, 40 120 Z" fill="#E25A43"/> <path d="M38 38 C46 46, 58 42, 64 36 C70 44, 82 46, 90 38 C96 44, 100 40, 100 38 C92 28, 48 26, 38 38 Z" fill="#58A84F"/> <path d="M48 52 C42 70, 44 92, 52 108" stroke="#fff" stroke-opacity=".38" stroke-width="6" fill="none" stroke-linecap="round"/> <circle cx="58" cy="74" r="5.2" fill="#3A221E"/><circle cx="82" cy="74" r="5.2" fill="#3A221E"/> <circle cx="59.8" cy="72.2" r="1.7" fill="#fff"/><circle cx="83.8" cy="72.2" r="1.7" fill="#fff"/> <ellipse cx="50" cy="85" rx="6" ry="3.6" fill="#FF9F8E" opacity=".9"/> <ellipse cx="90" cy="85" rx="6" ry="3.6" fill="#FF9F8E" opacity=".9"/> <path d="M63 84 Q70 91 77 84" stroke="#3A221E" stroke-width="3" fill="none" stroke-linecap="round"/> </svg>"""


def hero(chips):
    chip_html = "".join(f"<span>{c}</span>" for c in chips)
    st.markdown(f"""
<div class="hero">
  <div class="hero-text">
    <div class="hero-badge">경상북도농업기술원 영양고추연구소 · 고추 생산 변동 요인 분석</div>
    <div class="hero-title">고추 쑥쑥이</div>
    <div class="hero-sub">경북 북부 노지고추 주산지의 기상·작황조사·농가 정밀조사 자료로 만든 현장 진단 도구</div>
    <div class="hero-chips">{chip_html}</div>
    <div class="hero-guide">📖 처음이라면 맨 오른쪽 <b>사용 설명서</b> 탭부터 보세요</div>
  </div>
  <div class="hero-mascot">{MASCOT_SVG}</div>
</div>
""", unsafe_allow_html=True)


# 마크다운에서 '2016~2017 ... 2016~2018'처럼 물결표가 두 번 나오면 취소선이 되어서,
# 화면에 글을 쓰는 함수들은 물결표를 그대로 보이게 바꿔서 씀
def _keep_tilde(fn):
    fn = getattr(fn, "_original", fn)   # 화면을 새로 그릴 때마다 겹겹이 감싸지 않도록

    def wrapped(body, *args, **kwargs):
        if isinstance(body, str):
            body = body.replace("\\~", "~").replace("~", "\\~")
        return fn(body, *args, **kwargs)
    wrapped._original = fn
    return wrapped


for _name in ["markdown", "caption", "info", "success", "warning", "error", "subheader"]:
    setattr(st, _name, _keep_tilde(getattr(st, _name)))


# ─────────────────────────────────────────────
# 공통 도우미
# ─────────────────────────────────────────────
def find_file(include, ext, exclude=()):
    """app.py 폴더에서 이름에 include 단어가 모두 들어간 파일을 찾음"""
    try:
        files = os.listdir(HERE)
    except OSError:
        return None
    hits = sorted(f for f in files
                  if f.lower().endswith(ext)
                  and all(k in f for k in include)
                  and not any(k in f for k in exclude)
                  and not f.startswith("~$"))
    return os.path.join(HERE, hits[0]) if hits else None


def show_chart(fig):
    # Streamlit 버전에 따라 너비 인자 이름이 달라서 둘 다 대응
    try:
        st.plotly_chart(fig, width="stretch", theme=None)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, theme=None)


def show_table(df, **kw):
    try:
        st.dataframe(df, width="stretch", **kw)
    except TypeError:
        st.dataframe(df, use_container_width=True, **kw)


def base_layout(fig, height=320, ytitle=None, top=10):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=top, b=10),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      yaxis_title=ytitle)
    fig.update_yaxes(gridcolor="rgba(128,128,128,0.18)")
    fig.update_xaxes(showgrid=False)
    return fig


def md(m, d):
    return f"{m:02d}-{d:02d}"


# ─────────────────────────────────────────────
# 데이터 불러오기
# ─────────────────────────────────────────────
@st.cache_data
def load_weather(src):
    df = pd.read_csv(src, encoding="utf-8-sig")
    df.columns = [c.strip().lstrip("﻿") for c in df.columns]
    df["일시"] = pd.to_datetime(df["일시"])
    df["연도"] = df["일시"].dt.year
    df["월일"] = df["일시"].dt.strftime("%m-%d")
    # 그래프 x축용: 모든 연도를 2000년 날짜로 맞춤 (윤년 포함 연도)
    df["x날짜"] = pd.to_datetime("2000-" + df["월일"])
    return df.sort_values(["지역", "일시"]).reset_index(drop=True)


@st.cache_data
def load_survey(src):
    df = pd.read_excel(src)
    df.columns = [str(c).strip() for c in df.columns]
    # 단위 표기(㎝/cm) 통일
    df.columns = [c.replace("㎝", "cm") for c in df.columns]
    df["시군"] = df["시군"].astype(str).str.strip()
    return df


@st.cache_data
def load_production(src):
    df = pd.read_csv(src, encoding="utf-8-sig")
    df.columns = [str(c).strip().lstrip("﻿") for c in df.columns]
    df = df[[c for c in df.columns if not c.startswith("Unnamed")]]
    df = df.rename(columns={"노지_면적(ha)": "면적", "노지_생산량(t)": "생산량"})
    df["시군"] = df["시군"].astype(str).str.strip()
    df.loc[df["면적"] <= 0, "면적"] = np.nan
    df["단수"] = df["생산량"] / df["면적"] * 100   # kg/10a
    return df


@st.cache_data
def load_asos_solar(src):
    """ASOS 일자료에서 지점명·일시·합계 일사량만 뽑음"""
    try:
        df = pd.read_csv(src, encoding="utf-8-sig", low_memory=False)
    except UnicodeDecodeError:
        df = pd.read_csv(src, encoding="cp949", low_memory=False)
    df.columns = [str(c).strip().lstrip("﻿") for c in df.columns]
    sol = next((c for c in df.columns
                if "일사량" in c and "최다" not in c and "시각" not in c), None)
    if not ({"지점명", "일시"} <= set(df.columns)) or sol is None:
        return None
    d = df[["지점명", "일시", sol]].copy()
    d.columns = ["지점명", "일시", "일사량"]
    d["지점명"] = d["지점명"].astype(str).str.strip()
    d["일시"] = pd.to_datetime(d["일시"], errors="coerce")
    d["일사량"] = pd.to_numeric(d["일사량"], errors="coerce")
    return d.dropna(subset=["일시"])


def find_weather_file():
    for key in WEATHER_KEYS:
        p = find_file([key], ".csv")
        if p:
            return p
    return find_file(["농업기상", "정제본"], ".csv")


# ── 올해 기상자료 넣기 ──
#   기상자료개방포털 ASOS·AWS 일자료, 농업기상 관측 CSV를 열 이름으로 알아봄
def _pick_col(cols, must, avoid=()):
    for c in cols:
        cc = c.replace(" ", "")
        if all(m in cc for m in must) and not any(a in cc for a in avoid):
            return c
    return None


def station_to_sigun(name):
    """지점명(안동, 봉화, 청송군, 영양 등)을 시군 이름으로"""
    s = str(name).strip()
    for sg in SIGUN_ORDER:
        if sg in s or sg[:-1] in s:
            return sg
    return None


@st.cache_data(show_spinner=False)
def parse_extra_weather(raw, fname, force_sigun=None):
    """올린 CSV → 앱 기상 형식. (표, 알림 목록) 반환. 못 읽으면 표는 None."""
    df = None
    for enc in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            df = pd.read_csv(io.BytesIO(raw), encoding=enc)
            break
        except (UnicodeDecodeError, pd.errors.ParserError):
            continue
    if df is None or df.empty:
        return None, [f"{fname}: 파일을 읽지 못했어요."]
    df.columns = [str(c).strip().lstrip("﻿") for c in df.columns]
    cols = list(df.columns)
    msgs = []

    # 이미 앱 형식이면 그대로
    if {"지역", "일시"} <= set(cols) and COL["tmax"] in cols:
        out = df.copy()
    else:
        c_date = _pick_col(cols, ["일시"]) or _pick_col(cols, ["일자"]) or _pick_col(cols, ["날짜"]) \
            or _pick_col(cols, ["관측일"])
        c_st = _pick_col(cols, ["지점명"]) or _pick_col(cols, ["지역"]) or _pick_col(cols, ["관측지점"])
        c_tavg = _pick_col(cols, ["평균기온"])
        c_tmax = _pick_col(cols, ["최고기온"], ["시각"])
        c_tmin = _pick_col(cols, ["최저기온"], ["시각"])
        c_rain = (_pick_col(cols, ["일강수량"]) or _pick_col(cols, ["강수량"], ["최다", "시각", "계속"])
                  or _pick_col(cols, ["강우량"], ["최다", "시각"]))
        c_rh = _pick_col(cols, ["평균", "습도"])
        c_sol = _pick_col(cols, ["일사"], ["최다", "시각", "1시간"])
        need = {"날짜": c_date, "최고기온": c_tmax, "최저기온": c_tmin, "강수량": c_rain}
        lack = [k for k, v in need.items() if v is None]
        if lack:
            return None, [f"{fname}: {', '.join(lack)} 열을 찾지 못했어요. 열 이름을 확인해 주세요."]
        out = pd.DataFrame({
            "지역": df[c_st].astype(str) if c_st else "",
            "일시": df[c_date],
            COL["tavg"]: pd.to_numeric(df[c_tavg], errors="coerce") if c_tavg else np.nan,
            COL["tmax"]: pd.to_numeric(df[c_tmax], errors="coerce"),
            COL["tmin"]: pd.to_numeric(df[c_tmin], errors="coerce"),
            COL["rh"]: pd.to_numeric(df[c_rh], errors="coerce") if c_rh else np.nan,
            COL["rain"]: pd.to_numeric(df[c_rain], errors="coerce"),
            COL["solar"]: pd.to_numeric(df[c_sol], errors="coerce") if c_sol else np.nan,
        })
        # 기상청 일자료는 비가 안 온 날 일강수량 칸이 비어 있음 → 0
        n_blank = int(out[COL["rain"]].isna().sum())
        out[COL["rain"]] = out[COL["rain"]].fillna(0.0)
        if n_blank:
            msgs.append(f"{fname}: 강수량 빈칸 {n_blank}일은 비가 오지 않은 날로 봤어요(기상청 일자료 방식).")
        if c_tavg is None:
            out[COL["tavg"]] = (out[COL["tmax"]] + out[COL["tmin"]]) / 2
            msgs.append(f"{fname}: 평균기온 열이 없어 (최고+최저)/2로 채웠어요.")
        if c_sol is None:
            msgs.append(f"{fname}: 일사량 열이 없어요. 일사량 그래프·일사×강수 그림에는 빠집니다.")

    out["일시"] = pd.to_datetime(out["일시"], errors="coerce")
    out = out.dropna(subset=["일시"])
    if force_sigun:
        out["지역"] = force_sigun
    else:
        out["지역"] = out["지역"].map(station_to_sigun)
        if out["지역"].isna().all():
            return None, [f"{fname}: 지점 이름으로 시군을 알 수 없어요. 아래에서 시군을 골라 주세요."]
        n_drop = int(out["지역"].isna().sum())
        if n_drop:
            msgs.append(f"{fname}: 6개 시군이 아닌 지점 {n_drop}행은 뺐어요.")
        out = out.dropna(subset=["지역"])
    out = out.drop_duplicates(["지역", "일시"], keep="last")
    return out, msgs


def merge_weather(base, extra):
    """기본 기상자료에 올린 자료를 덧붙임. 같은 시군·날짜는 올린 자료가 우선."""
    if extra is None or extra.empty:
        return base
    e = extra.copy()
    e["연도"] = e["일시"].dt.year
    e["월일"] = e["일시"].dt.strftime("%m-%d")
    e["x날짜"] = pd.to_datetime("2000-" + e["월일"])
    key = set(zip(e["지역"], e["일시"]))
    keep = ~pd.Series([k in key for k in zip(base["지역"], base["일시"])], index=base.index)
    return (pd.concat([base[keep], e], ignore_index=True)
            .sort_values(["지역", "일시"]).reset_index(drop=True))


# ── 기상청 API허브 자동 갱신 (올해 일자료) ──
#   키는 .streamlit/secrets.toml 의 KMA_API_KEY (Streamlit Cloud는 앱 Settings → Secrets).
#   ASOS(안동·봉화·청송군·의성): 종관 일자료 kma_sfcdd3.php
#   AWS(영양·예천): 지상·AWS 일통계 sfc_aws_day.php — 요소별(ta_max, ta_min, rn_day) 조회라
#   평균기온은 (최고+최저)/2로 채우고 습도·일사량은 비움. 지점번호는 지점정보(stn_inf)에서
#   이름으로 찾고, 실패하면 군청 좌표에서 가장 가까운 지점을 씁니다.
KMA_API_BASE = "https://apihub.kma.go.kr/api/typ01/url"
API_ASOS_STN = {"안동시": 136, "봉화군": 271, "청송군": 276, "의성군": 278}
API_AWS_NAME = {"영양군": "영양", "예천군": "예천"}
API_AWS_NEAR = {"영양군": (36.667, 129.112), "예천군": (36.658, 128.453)}  # (위도, 경도) 군청 부근
_SFCDD_FIELDS = (
    "TM STN WS_AVG WR_DAY WD_MAX WS_MAX WS_MAX_TM WD_INS WS_INS WS_INS_TM "
    "TA_AVG TA_MAX TA_MAX_TM TA_MIN TA_MIN_TM TD_AVG TS_AVG TG_MIN HM_AVG HM_MIN "
    "HM_MIN_TM PV_AVG EV_S EV_L FG_DUR PA_AVG PS_AVG PS_MAX PS_MAX_TM PS_MIN "
    "PS_MIN_TM CA_TOT SS_DAY SS_DUR SS_CMB SI_DAY SI_60M_MAX SI_60M_MAX_TM RN_DAY RN_D99 "
    "RN_DUR RN_60M_MAX RN_60M_MAX_TM RN_10M_MAX RN_10M_MAX_TM RN_POW_MAX RN_POW_MAX_TM "
    "SD_NEW SD_NEW_TM SD_MAX SD_MAX_TM TE_05 TE_10 TE_15 TE_30 TE_50").split()


def kma_api_key():
    try:
        k = st.secrets.get("KMA_API_KEY", "")
    except Exception:
        k = ""
    return str(k or os.environ.get("KMA_API_KEY", "")).strip()


def _api_text(key, path, **params):
    import urllib.parse
    import urllib.request
    q = dict(params)
    q["authKey"] = key
    url = f"{KMA_API_BASE}/{path}?" + urllib.parse.urlencode(q)
    with urllib.request.urlopen(url, timeout=30) as r:
        txt = r.read().decode("euc-kr", errors="replace")
    if "START7777" not in txt:
        head = next((ln.strip() for ln in txt.splitlines() if ln.strip()), "빈 응답")
        raise RuntimeError(re.sub(r"<[^>]+>", " ", head)[:150])
    return txt


def _api_rows(txt):
    rows = []
    for ln in txt.splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        s = s.rstrip("=").strip()
        if s:
            rows.append(s.split(",") if "," in s else s.split())
    return rows


def _api_header(txt, needed):
    """주석 줄에서 열 이름 목록을 찾음 (없으면 None)"""
    for ln in txt.splitlines():
        if ln.strip().startswith("#") and all(k in ln for k in needed):
            toks = ln.strip("# ").replace(",", " ").split()
            if all(k in toks for k in needed):
                return toks
    return None


def _api_num(v, rain=False):
    try:
        x = float(v)
    except (TypeError, ValueError):
        return np.nan
    if rain:
        # 일통계에서 -9는 '강수 없음'
        return 0.0 if -10 < x < 0 else (np.nan if x <= -90 else x)
    return np.nan if x <= -50 else x


def _parse_sfcdd(txts, names):
    need = ["TM", "STN", "TA_AVG", "TA_MAX", "TA_MIN", "HM_AVG", "SI_DAY", "RN_DAY"]
    if not all(k in names for k in ("TM", "STN", "TA_MAX", "TA_MIN", "RN_DAY")):
        return pd.DataFrame()
    idx = {k: names.index(k) for k in need if k in names}
    sig = {str(v): k for k, v in API_ASOS_STN.items()}
    recs = []
    for t in txts:
        for c in _api_rows(t):
            if len(c) <= max(idx.values()) or c[idx["STN"]] not in sig:
                continue

            def g(k, rain=False, c=c):
                return _api_num(c[idx[k]], rain) if k in idx else np.nan

            recs.append({"지역": sig[c[idx["STN"]]], "일시": c[idx["TM"]][:8],
                         COL["tavg"]: g("TA_AVG"), COL["tmax"]: g("TA_MAX"), COL["tmin"]: g("TA_MIN"),
                         COL["rh"]: g("HM_AVG"), COL["solar"]: g("SI_DAY"), COL["rain"]: g("RN_DAY", True)})
    return pd.DataFrame(recs)


def _sane_temps(df):
    d = df.dropna(subset=[COL["tmax"], COL["tmin"]])
    if d.empty:
        return False
    ok = ((d[COL["tmax"]] >= d[COL["tmin"]] - 0.5) & d[COL["tmax"]].between(-40, 50)).mean()
    return ok >= 0.8


def _fetch_asos_api(key, d1, d2):
    stn = ":".join(str(s) for s in API_ASOS_STN.values())
    txts, cur = [], d1
    while cur <= d2:
        end = min(cur + timedelta(days=180), d2)
        txts.append(_api_text(key, "kma_sfcdd3.php", tm1=cur.strftime("%Y%m%d"),
                              tm2=end.strftime("%Y%m%d"), stn=stn, help=1))
        cur = end + timedelta(days=1)
    header = next((h for h in (_api_header(t, ("TM", "TA_MAX", "RN_DAY")) for t in txts) if h), None)
    for names in ([header] if header else []) + [_SFCDD_FIELDS]:
        df = _parse_sfcdd(txts, names)
        if len(df) and _sane_temps(df):
            return df
    raise RuntimeError("ASOS 일자료 응답 형식이 예상과 다릅니다")


def _aws_station_map(key, tm):
    """영양·예천 AWS 지점번호: 지점정보에서 이름으로 → 실패 시 좌표로"""
    ids = {}
    try:
        txt = _api_text(key, "stn_inf.php", inf="AWS", stn=0, help=0)
        for row in _api_rows(txt):
            for sg, nm in API_AWS_NAME.items():
                if sg not in ids and nm in row:
                    ids[sg] = row[0]
    except Exception:
        pass
    if len(ids) < len(API_AWS_NAME):
        try:
            txt = _api_text(key, "sfc_aws_day.php", tm1=tm.strftime("%Y%m%d"),
                            tm2=tm.strftime("%Y%m%d"), obs="ta_max", stn=0, disp=0, help=0)
            rows = [r for r in _api_rows(txt) if len(r) >= 6]
            for sg, (la, lo) in API_AWS_NEAR.items():
                if sg in ids:
                    continue
                best, bd = None, 0.25
                for r in rows:
                    try:
                        rlo, rla = float(r[2]), float(r[3])
                    except ValueError:
                        continue
                    d = abs(rla - la) + abs(rlo - lo)
                    if d < bd:
                        best, bd = r[1], d
                if best:
                    ids[sg] = best
        except Exception:
            pass
    return ids


def _fetch_aws_api(key, d1, d2, ids):
    sig = {str(v): k for k, v in ids.items()}
    stn = ":".join(str(v) for v in ids.values())
    data = {}
    for obs, field, rain in [("ta_max", COL["tmax"], False), ("ta_min", COL["tmin"], False),
                             ("rn_day", COL["rain"], True)]:
        cur = d1
        while cur <= d2:
            end = min(cur + timedelta(days=180), d2)
            txt = _api_text(key, "sfc_aws_day.php", tm1=cur.strftime("%Y%m%d"),
                            tm2=end.strftime("%Y%m%d"), obs=obs, stn=stn, disp=0, help=0)
            for r in _api_rows(txt):
                if len(r) < 6 or r[1] not in sig:
                    continue
                data.setdefault((sig[r[1]], r[0][:8]), {})[field] = _api_num(r[5], rain=rain)
            cur = end + timedelta(days=1)
    recs = []
    for (sg, tm), v in data.items():
        tmax, tmin = v.get(COL["tmax"], np.nan), v.get(COL["tmin"], np.nan)
        recs.append({"지역": sg, "일시": tm, COL["tavg"]: (tmax + tmin) / 2,
                     COL["tmax"]: tmax, COL["tmin"]: tmin, COL["rh"]: np.nan,
                     COL["solar"]: np.nan, COL["rain"]: v.get(COL["rain"], np.nan)})
    return pd.DataFrame(recs)


@st.cache_data(ttl=6 * 3600, show_spinner="기상청 API허브에서 올해 기상자료를 받는 중...")
def fetch_kma_api(key, d1_iso, d2_iso):
    """기본 자료 다음 날부터 어제까지 받아 (표, 알림 목록)을 돌려줌. 6시간마다 다시 받음."""
    d1, d2 = date.fromisoformat(d1_iso), date.fromisoformat(d2_iso)
    msgs, parts = [], []
    if d1 > d2:
        return None, ["파일 기상자료가 이미 최신이라 받아올 날이 없어요."]
    try:
        a = _fetch_asos_api(key, d1, d2)
        if len(a):
            parts.append(a)
            msgs.append(f"ASOS(안동·봉화·청송군·의성) {len(a):,}건 받음")
    except Exception as e:
        msgs.append(f"⚠ ASOS 갱신 실패: {e}")
    try:
        ids = _aws_station_map(key, d2)
        missing = [sg for sg in API_AWS_NAME if sg not in ids]
        if missing:
            msgs.append("⚠ AWS 지점번호를 찾지 못했어요: " + ", ".join(missing))
        if ids:
            w = _fetch_aws_api(key, d1, d2, ids)
            if len(w) and _sane_temps(w):
                parts.append(w)
                msgs.append("AWS(" + " · ".join(f"{sg} 지점 {v}" for sg, v in ids.items())
                            + f") {len(w):,}건 받음. 평균기온은 (최고+최저)/2이고 습도·일사량은 없어요.")
            elif len(w):
                msgs.append("⚠ AWS 일통계 응답 형식이 예상과 달라 쓰지 않았어요.")
    except Exception as e:
        msgs.append(f"⚠ AWS 갱신 실패: {e}")
    if not parts:
        return None, msgs
    out = pd.concat(parts, ignore_index=True)
    out["일시"] = pd.to_datetime(out["일시"], format="%Y%m%d", errors="coerce")
    out = out.dropna(subset=["일시"]).drop_duplicates(["지역", "일시"], keep="last")
    msgs.insert(0, f"자동 갱신 구간: {d1:%Y-%m-%d} ~ {d2:%Y-%m-%d} (어제까지)")
    return out, msgs


@st.cache_data
def apply_final_solar(wx, asos):
    """일사량을 최종 구성으로 바꿈. 원값은 '일사량_원값'에 남겨 품질 점검에 씀."""
    w = wx.copy()
    if "일사량_원값" not in w.columns:
        w["일사량_원값"] = w[COL["solar"]]
    notes, done = [], []

    for sg, s, e, k in SOLAR_RATIO_FIX:
        m = (w["지역"] == sg) & (w["일시"] >= s) & (w["일시"] <= e)
        if m.any():
            w.loc[m, COL["solar"]] = w.loc[m, "일사량_원값"].values * k
            notes.append(f"{sg} {s[:7].replace('-', '.')}~{e[:7].replace('-', '.')} "
                         f"농업기상 원값 × {k}")
            done.append(sg)

    if asos is None:
        notes.append("⚠ ASOS 파일을 찾지 못해 안동·예천 일사량은 **원값 그대로**입니다 (최종 구성 아님)")
        return w, notes, False

    ok = True
    for sg, station in ASOS_REPLACE.items():
        ser = asos[asos["지점명"] == station].set_index("일시")["일사량"]
        ser = ser[~ser.index.duplicated()]
        m = w["지역"] == sg
        if not m.any():
            continue
        if ser.empty:
            notes.append(f"⚠ ASOS에 '{station}' 지점이 없어 {sg}는 원값 그대로입니다")
            ok = False
            continue
        rep = w.loc[m, "일시"].map(ser)
        n_na = int(rep.isna().sum())
        w.loc[m, COL["solar"]] = rep.fillna(w.loc[m, "일사량_원값"]).values
        notes.append(f"{sg} 전 기간 ASOS({station}) 실측 대체"
                     + (f" · 결측 {n_na}일은 원값 유지" if n_na else ""))
        done.append(sg)

    sg, station, upto, ratio = YECHEON_PROXY
    ser = asos[asos["지점명"] == station].set_index("일시")["일사량"]
    ser = ser[~ser.index.duplicated()]
    m = (w["지역"] == sg) & (w["일시"] <= upto)
    if m.any() and not ser.empty:
        rep = w.loc[m, "일시"].map(ser) * ratio
        w.loc[m, COL["solar"]] = rep.fillna(w.loc[m, "일사량_원값"]).values
        y0 = int(w.loc[m, "연도"].min())
        notes.append(f"{sg} {y0}~{upto[:4]} 안동 ASOS × {ratio} 환산 "
                     f"({int(upto[:4]) + 1}년부터 실측)")
        done.append(sg)
    return w, notes, ok


# ─────────────────────────────────────────────
# 탭 1·기상 시나리오: 위험 지표 계산
# ─────────────────────────────────────────────
# 지표 정의
#   high_bad=True  → 값이 많을수록 위험
#   high_bad=False → 값이 적을수록 위험 (예: 비다운 비가 온 날이 적으면 가뭄)
IND = {
    "착과전고온": dict(name="착과 전 고온일", start=(7, 3), end=(7, 28), high_bad=True),
    "탄저": dict(name="탄저병 위험: 비 온 날", start=(6, 15), end=(9, 30), high_bad=True),
    "고온": dict(name="고온일", start=(6, 1), end=(8, 31), high_bad=True),
    "폭염": dict(name="폭염일", start=(6, 1), end=(8, 31), high_bad=True),
    "저온": dict(name="저온일", start=(6, 1), end=(8, 31), high_bad=True),
    "건조": dict(name="가뭄: 비다운 비 온 날", start=(5, 1), end=(8, 31), high_bad=False),
}
CARD_KEYS = ["착과전고온", "탄저", "고온", "저온", "건조"]


def ind_sub(key, th):
    """카드 아래 짧은 설명 (현재 기준값 반영)"""
    if key == "착과전고온":
        return f"7/3~7/28, 최고 {th['hot_pre']:g}℃ 이상"
    if key == "탄저":
        t = f" + 최고 {th['tan_tmax']:g}℃ 이상" if th["tan_use_tmax"] else ""
        return f"6/15~9/30, 비 {th['rain_wet']:g}mm 이상 온 날{t}"
    if key == "고온":
        return f"6~8월, 최고 {th['hot']:g}℃ 이상"
    if key == "폭염":
        return f"6~8월, 최고 {th['heat']:g}℃ 이상"
    if key == "저온":
        return f"6~8월, 최저 {th['cold']:g}℃ 이하"
    if key == "건조":
        return f"5~8월, 비 {th['rain_good']:g}mm 이상 온 날 (적을수록 가뭄)"
    return ""


def window(df_year, start_md, end_md):
    return df_year[(df_year["월일"] >= start_md) & (df_year["월일"] <= end_md)]


def longest_run(mask):
    best = cur = 0
    for v in mask:
        cur = cur + 1 if v else 0
        best = max(best, cur)
    return best


def ind_value(df_year, key, th, end_md="09-30"):
    """한 시군·한 연도의 지표 하나. 기간이 아직 시작 전이면 None."""
    spec = IND[key]
    s, e = md(*spec["start"]), md(*spec["end"])
    if end_md < s:
        return None
    w = window(df_year, s, min(e, end_md))
    if w.empty:
        return None
    if key == "착과전고온":
        m = w[COL["tmax"]] >= th["hot_pre"]
    elif key == "탄저":
        m = w[COL["rain"]] >= th["rain_wet"]
        if th["tan_use_tmax"]:
            m = m & (w[COL["tmax"]] >= th["tan_tmax"])
    elif key == "고온":
        m = w[COL["tmax"]] >= th["hot"]
    elif key == "폭염":
        m = w[COL["tmax"]] >= th["heat"]
    elif key == "저온":
        m = w[COL["tmin"]] <= th["cold"]
    else:  # 건조
        m = w[COL["rain"]] >= th["rain_good"]
    return int(m.sum())


def indicators(df_year, end_md, th):
    out = {k: ind_value(df_year, k, th, end_md) for k in IND}
    w = window(df_year, md(5, 1), min(md(8, 31), end_md))
    out["무강수"] = longest_run((w[COL["rain"]] < th["rain_dry"]).tolist()) if not w.empty else None
    return out


def all_years(df_sigun, end_md, th):
    rows = []
    for y, g in df_sigun.groupby("연도"):
        # 기준일까지 자료가 다 있는 연도만 비교에 씀
        if g["월일"].max() < end_md:
            continue
        r = indicators(g, end_md, th)
        r["연도"] = y
        rows.append(r)
    return pd.DataFrame(rows).set_index("연도")


def judge(value, others, high_bad=True):
    """평년(선택 연도 제외) 평균 ± 1표준편차로 판정"""
    if value is None or len(others) < 3:
        return "판정 불가", "⚪"
    m, sd = np.mean(others), np.std(others, ddof=1)
    if sd == 0:
        sd = 1e-9
    if value > m + sd:
        return "평년보다 많음", ("🔴" if high_bad else "🟢")
    if value < m - sd:
        return "평년보다 적음", ("🟢" if high_bad else "🔴")
    return "평년 수준", "🟡"


SERIES_OPTS = ["누적 비 온 날 (6/15부터)", "누적 강수량 (mm)",
               "최고기온 (℃, 7일 이동평균)", "일평균기온 (℃, 7일 이동평균)",
               "누적 일사량 (MJ/m²)"]


def daily_series(df_sigun, var, th):
    d = df_sigun.copy()
    d = d[(d["월일"] >= md(*SEASON_START)) & (d["월일"] <= md(*SEASON_END))]
    if var == "누적 강수량 (mm)":
        d["값"] = d.groupby("연도")[COL["rain"]].cumsum()
    elif var == "누적 일사량 (MJ/m²)":
        d["값"] = d.groupby("연도")[COL["solar"]].cumsum()
    elif var == "일평균기온 (℃, 7일 이동평균)":
        d["값"] = d.groupby("연도")[COL["tavg"]].transform(lambda s: s.rolling(7, min_periods=1).mean())
    elif var == "최고기온 (℃, 7일 이동평균)":
        d["값"] = d.groupby("연도")[COL["tmax"]].transform(lambda s: s.rolling(7, min_periods=1).mean())
    else:  # 누적 비 온 날
        flag = (d[COL["rain"]] >= th["rain_wet"]) & (d["월일"] >= md(6, 15))
        if th["tan_use_tmax"]:
            flag = flag & (d[COL["tmax"]] >= th["tan_tmax"])
        d["값"] = flag.astype(int).groupby(d["연도"]).cumsum()
    return d


def year_span(yrs):
    yrs = sorted(int(y) for y in yrs)
    if not yrs:
        return "-"
    if yrs == list(range(yrs[0], yrs[-1] + 1)):
        return f"{yrs[0]}~{yrs[-1]}년, {len(yrs)}개년"
    return ", ".join(str(y) for y in yrs) + f"년, {len(yrs)}개년"


def season_chart(d, year, end_md, var):
    this = d[(d["연도"] == year) & (d["월일"] <= end_md)]
    others = d[d["연도"] != year]
    band = others.groupby("x날짜")["값"].agg(["min", "max", "mean"]).reset_index()
    yrs = sorted(others["연도"].unique())

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=band["x날짜"], y=band["max"], mode="lines",
                             line=dict(width=0), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=band["x날짜"], y=band["min"], mode="lines", line=dict(width=0),
                             fill="tonexty", fillcolor=C_BAND, hoverinfo="skip",
                             name=f"평년 범위 ({year_span(yrs)})"))
    fig.add_trace(go.Scatter(x=band["x날짜"], y=band["mean"], mode="lines",
                             line=dict(color=C_MEAN, width=2, dash="dot"), name="평년 평균",
                             hovertemplate="평년 평균 %{y:.1f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=this["x날짜"], y=this["값"], mode="lines",
                             line=dict(color=C_THIS, width=2.5), name=f"{year}년",
                             hovertemplate=f"{year}년 " + "%{y:.1f}<extra></extra>"))
    base_layout(fig, 380, var)
    fig.update_layout(hovermode="x unified", legend=dict(orientation="h", y=1.08, x=0))
    fig.update_xaxes(tickformat="%m/%d", dtick="M1")
    return fig


def year_bar(tbl, key, year, label):
    s = tbl[key].dropna()
    colors = [C_THIS if y == year else C_OTHER for y in s.index]
    fig = go.Figure(go.Bar(x=[str(y) for y in s.index], y=s.values, marker_color=colors,
                           hovertemplate="%{x}년 %{y}일<extra></extra>"))
    if len(s.drop(year, errors="ignore")) > 0:
        m = s.drop(year, errors="ignore").mean()
        fig.add_hline(y=m, line_dash="dot", line_color=C_MEAN)
        fig.update_layout(title=dict(text=f"점선: 평년 평균 {m:.1f}일", font=dict(size=13, color=C_MEAN),
                                     x=0, xanchor="left"))
    base_layout(fig, 300, label, top=36)
    fig.update_layout(bargap=0.35)
    fig.update_xaxes(type="category")
    return fig


# ── 작황조사로 지표 검증 ──
# (기상 지표, 하반기 작황조사 결과 열, 결과 이름)
VALID_PAIRS = [
    ("탄저", "탄저병(개)", "탄저병 발생 포장 비율"),
    ("고온", "담배나방(개)", "담배나방 발생 포장 비율"),
    ("건조", "석회결핍(개)", "석회결핍 발생 포장 비율"),
]


@st.cache_data
def season_table(wx, th, skip_regions=(), end_md="09-30"):
    """시군 × 연도별 지표 (end_md까지). 작황조사 검증은 VALID_END(7/31, 조사 전)로 부른다"""
    rows = []
    for (sg, y), g in wx.groupby(["지역", "연도"]):
        if sg in skip_regions or g["월일"].max() < end_md:
            continue
        r = indicators(g, end_md, th)
        r["시군"], r["연도"] = sg, y
        rows.append(r)
    return pd.DataFrame(rows).set_index(["시군", "연도"])


@st.cache_data
def season_solar_rain(wx):
    """시군 × 연도별 생육기(4/1~10/31) 평균 일사량과 누적 강수량.
    회귀 분석에 쓴 파생변수와 같은 창이다. 창이 다 차지 않은 연도는 뺀다."""
    a, b = PANEL_WINDOW
    w = wx[(wx["월일"] >= a) & (wx["월일"] <= b)]
    g = w.groupby(["지역", "연도"]).agg(일사량=(COL["solar"], "mean"),
                                       강수량=(COL["rain"], "sum"),
                                       일수=(COL["solar"], "size"))
    return g[g["일수"] >= 200].drop(columns="일수")


def valid_window(k):
    """검증 창 표시 (지표 시작일 ~ 7/31)"""
    sm, sd = IND[k]["start"]
    return f"{sm}/{sd}~7/31"


def bin_label(lo, hi):
    return f"{hi}일 이하" if lo == 0 else (f"{lo}일 이상" if hi >= 999 else f"{lo}~{hi}일")


def bin_table(joined, k, oname):
    rows = []
    for lo, hi in VALID_BINS[k]:
        m = (joined[k] >= lo) & (joined[k] <= hi)
        if m.sum():
            rows.append({"구간": bin_label(lo, hi), "사례 수": int(m.sum()),
                         "평균 발생 포장 비율": f"{joined.loc[m, oname].mean():.1f}%"})
    return pd.DataFrame(rows)


def harvest_end_day(df_year, thr=12.0):
    """9월 1일 이후 일평균기온이 처음으로 thr 이하가 된 날 (없으면 None)"""
    w = df_year[(df_year["월일"] >= "09-01")]
    hit = w[w[COL["tavg"]] <= thr]
    return None if hit.empty else hit["일시"].iloc[0].date()


def survey_rates(hv):
    """하반기 작황조사 → 시군 × 연도별 발생 포장 비율(%)"""
    out = {}
    for _, col, name in VALID_PAIRS:
        if col in hv.columns:
            out[name] = (hv[col] > 0).groupby([hv["시군"], hv["년도"]]).mean() * 100
    df = pd.DataFrame(out)
    df.index.names = ["시군", "연도"]
    return df


def within_fit(x, y, groups):
    """시군 평균을 뺀 뒤의 상관계수와 기울기 (시군 간 수준 차이 제거)"""
    d = pd.DataFrame({"x": x, "y": y, "g": groups}).dropna()
    if len(d) < 8:
        return np.nan, np.nan, 0
    d["x"] = d["x"] - d.groupby("g")["x"].transform("mean")
    d["y"] = d["y"] - d.groupby("g")["y"].transform("mean")
    if d["x"].std() == 0:
        return np.nan, np.nan, len(d)
    r = d["x"].corr(d["y"])
    slope = (d["x"] * d["y"]).sum() / (d["x"] ** 2).sum()
    return r, slope, len(d)


def marginal_solar(rain_mm):
    """강수량 수준에서의 일사량 1 MJ당 단수 효과 (2-way FE 교호 모형)"""
    return SOLAR_RAIN["중심효과"] + SOLAR_RAIN["교호계수"] * (rain_mm - SOLAR_RAIN["중심강수"])


# ── 기상 시나리오 ──
def shift_weather(df, dT=0.0, rmul=1.0):
    d = df.copy()
    for c in (COL["tavg"], COL["tmax"], COL["tmin"]):
        d[c] = d[c] + dT
    d[COL["rain"]] = d[COL["rain"]] * rmul
    return d


@st.cache_data
def remaining_scenarios(df_s, year, cut_md, dT, rmul, th):
    """선택 연도의 기준일까지 실측 + 기준일 이후를 다른 해 날씨로 채운 시나리오"""
    obs = df_s[(df_s["연도"] == year) & (df_s["월일"] <= cut_md)]
    rows = []
    for y2, g in df_s.groupby("연도"):
        if y2 == year or g["월일"].max() < "09-30":
            continue
        rest = shift_weather(g[g["월일"] > cut_md], dT, rmul)
        r = indicators(pd.concat([obs, rest]), "09-30", th)
        r["시나리오"] = y2
        rows.append(r)
    return pd.DataFrame(rows).set_index("시나리오")


@st.cache_data
def finish_outlook(df_s, year, cut_md, key, th, end_md):
    """기준일까지 실측 + 그 뒤를 다른 해 날씨로 채웠을 때 end_md 시점 지표 {다른 해: 값}"""
    obs = df_s[(df_s["연도"] == year) & (df_s["월일"] <= cut_md)]
    out = {}
    for y2, g in df_s.groupby("연도"):
        if y2 == year or g["월일"].max() < end_md:
            continue
        v = ind_value(pd.concat([obs, g[g["월일"] > cut_md]]), key, th, end_md)
        if v is not None:
            out[int(y2)] = v
    return out


def md_date(mdv, y=2001):
    return date(y, int(mdv[:2]), int(mdv[3:]))


def pest_status(v, r, end_md, outlook):
    """병해충 판정: (상태, 아이콘, 한 줄 설명)"""
    cut = r["cut"]
    if v is None:
        return "집계 전", "⚪", f"{int(r['start'][:2])}월 {int(r['start'][3:])}일부터 셉니다."
    done = end_md >= PEST_END
    n_out = len(outlook)
    if r["high_bad"]:
        hit = sum(1 for x in outlook.values() if x >= cut)
        if v >= cut:
            return "다발 위험", "🔴", f"이미 기준({cut}일)을 넘었습니다."
        if done:
            return "기준 미만", "🟢", f"7월 31일까지 {v}일로 기준({cut}일)에 못 미쳤습니다."
        left = (md_date(PEST_END) - md_date(end_md)).days
        if v + left < cut:
            return "기준 미만 (확정)", "🟢", f"남은 {left}일이 모두 해당해도 기준({cut}일)에 못 미칩니다."
        icon = "🟠" if n_out and hit >= n_out / 2 else "🟡"
        return "집계 중", icon, (f"기준까지 {cut - v}일 남음. 남은 기간이 과거 각 해처럼 흐르면 "
                                 f"**{n_out}개 해 중 {hit}개 해**에서 기준을 넘습니다.")
    # 적을수록 위험 (석회결핍)
    hit = sum(1 for x in outlook.values() if x <= cut)
    if v > cut:
        return "위험 낮음 (확정)", "🟢", f"비다운 비가 이미 {v}일로 기준({cut}일 이하)을 벗어났습니다."
    if done:
        return "다발 위험", "🔴", f"7월 31일까지 {v}일로 기준({cut}일 이하)에 들었습니다."
    icon = "🟠" if n_out and hit >= n_out / 2 else "🟡"
    return "집계 중", icon, (f"지금 {v}일. 남은 기간이 과거 각 해처럼 흐르면 "
                             f"**{n_out}개 해 중 {hit}개 해**에서 7월 31일까지 {cut}일 이하로 끝납니다.")


TIMELINE = [  # (이름, 시작, 끝, 색)
    ("석회결핍: 비다운 비 집계", "05-01", "07-31", "#1baf7a"),
    ("담배나방: 30℃ 고온일 집계", "06-01", "07-31", "#eda100"),
    ("탄저병: 비 온 날 집계", "06-15", "07-31", "#2a78d6"),
    ("착과 전 고온 (33℃)", "07-03", "07-28", "#e34948"),
    ("다발 위험 판정", "07-31", "08-01", "#6f6e69"),
    ("8월 말 생육조사 → 조기예측", "08-25", "09-03", "#8a3ffc"),
]


def timeline_chart(end_md, harvest_md=None):
    items = TIMELINE + ([("수확 종료 기준일 (평년)", harvest_md, harvest_md, "#9C3F30")] if harvest_md else [])
    fig = go.Figure()
    for name, a, b, colr in items:
        x0, x1 = pd.Timestamp("2000-" + a), pd.Timestamp("2000-" + b)
        if x1 <= x0:
            x1 = x0 + pd.Timedelta(days=1)
        fig.add_trace(go.Scatter(x=[x0, x1], y=[name, name], mode="lines",
                                 line=dict(color=colr, width=14), showlegend=False,
                                 hovertemplate=f"{name}: {int(a[:2])}/{int(a[3:])}~{int(b[:2])}/{int(b[3:])}<extra></extra>"))
    xd = pd.Timestamp("2000-" + end_md)
    fig.add_shape(type="line", x0=xd, x1=xd, yref="paper", y0=0, y1=1,
                  line=dict(color=C_ALERT, width=2, dash="dot"))
    fig.add_annotation(x=xd, y=1.04, yref="paper", text="기준일", showarrow=False,
                       font=dict(color=C_ALERT, size=12))
    base_layout(fig, 250, None, top=24)
    fig.update_xaxes(tickformat="%m/%d", dtick="M1", range=[pd.Timestamp("2000-04-25"),
                                                             pd.Timestamp("2000-11-05")],
                     showgrid=True, gridcolor="rgba(128,128,128,0.15)")
    fig.update_yaxes(autorange="reversed", showgrid=False)
    return fig


def occ_rates_h(hv):
    """하반기 작황조사 → 포장별 발생 여부 표 (개 > 0, 등급 3 이상)"""
    out = pd.DataFrame({"시군": hv["시군"], "년도": hv["년도"]})
    for name, col, kind in PEST_LIST_H:
        if col in hv.columns:
            v = pd.to_numeric(hv[col], errors="coerce")
            out[name] = np.where(v.isna(), np.nan, (v > 0) if kind == "개" else (v >= 3)).astype(float)
    return out


def occ_rates_s(sv):
    out = pd.DataFrame({"시군": sv["시군"], "년도": sv["년도"]})
    for name, col in PEST_LIST_S:
        if col in sv.columns:
            v = pd.to_numeric(sv[col], errors="coerce")
            out[name] = np.where(v.isna(), np.nan, v > 0).astype(float)
    return out


def normal_table(occ, names):
    """시군별 평년 발생 포장 비율 (조사 포장 전체 합산, %)"""
    names = [n for n in names if n in occ.columns]
    t = occ.groupby("시군")[names].mean() * 100
    t = t.reindex([s for s in SIGUN_ORDER if s in t.index])
    t.loc["6개 시군 전체"] = occ[names].mean() * 100
    yrs = occ["년도"].dropna().astype(int)
    return t.round(1), (int(yrs.min()), int(yrs.max())) if len(yrs) else (None, None)


def year_vs_normal(occ, sg, yr, names):
    """그해 발생 포장 비율 vs 그해를 뺀 연도별 비율의 평균 ± 1SD (5%p 이상 차이일 때만 많음·적음)"""
    g = occ[occ["시군"] == sg]
    rows = []
    for n in [n for n in names if n in occ.columns]:
        by = g.groupby("년도")[n].mean() * 100
        if yr not in by.index or len(by.drop(yr)) < 3:
            continue
        v, o = by[yr], by.drop(yr)
        m, sd = o.mean(), o.std(ddof=1)
        if v > m + sd and v - m >= 5:
            j = "🔴 평년보다 많음"
        elif v < m - sd and m - v >= 5:
            j = "🟢 평년보다 적음"
        else:
            j = "🟡 평년 수준"
        rows.append({"병해충": n, f"{yr}년": f"{v:.0f}%", "평년": f"{m:.0f}%", "판정": j})
    return pd.DataFrame(rows)


@st.cache_data
def climate_scenarios(df_s, th, dTs, rmul, end_md="09-30"):
    """과거 각 해 날씨에 기온 +dT, 강수 ×rmul을 적용했을 때 지표 (해마다)"""
    rows = []
    for dT in dTs:
        for y, g in df_s.groupby("연도"):
            if g["월일"].max() < end_md:
                continue
            r = indicators(shift_weather(g, dT, rmul), end_md, th)
            r["dT"], r["연도"] = dT, y
            rows.append(r)
    return pd.DataFrame(rows)


# ── 미래 기후 (기상청 SSP 시나리오) ──
# 자료: 기상청 기후정보포털 'SSP 시나리오 남한상세 행정구역' (5개 모델 평균, 2024년 6월 행정구역)
#   월자료: TA 평균기온, TAMAX 최고, TAMIN 최저, RN 강수량(월합), SI 일사량
#   연자료: HW33 폭염일수, TR25 열대야, SU25 여름일수, FD0 서리일수, GSL 식물성장기간,
#           CDD 최대무강수지속기간, SDII 강수강도
# 방법: 시군·월마다 '미래 10년 평균 - 2021~2030 평균'(강수·일사는 비율)을 관측 일자료에 적용 (월별 델타 방법)
SSP_FILE_KEY = "SSP"
SSP_NAMES = {"SSP2-4.5": "SSP2-4.5 · 중간 (감축 정책이 어느 정도 실현)",
             "SSP5-8.5": "SSP5-8.5 · 고탄소 (지금처럼 배출)"}
SSP_COLOR = {"SSP2-4.5": "#eda100", "SSP5-8.5": "#c23b2b"}
SSP_BASE = (2021, 2030)
SSP_DECADES = [(a, a + 9) for a in range(2031, 2100, 10)]


def dec_label(d):
    return f"{d[0]}–{d[1]}"


@st.cache_data
def load_ssp(src):
    d = pd.read_csv(src, encoding="utf-8-sig")
    d.columns = [c.strip().lstrip("\ufeff") for c in d.columns]
    return d


def ssp_delta(ssp, scen, sigun_m, dec):
    """시군·월별 변화량: 기온은 차이(℃), 강수·일사는 비율"""
    m = ssp[(ssp["시나리오"] == scen) & (ssp["시군"] == sigun_m) & (ssp["월"] > 0)]
    cols = ["TA", "TAMAX", "TAMIN", "RN", "SI"]
    b = m[m["연도"].between(*SSP_BASE)].groupby("월")[cols].mean()
    f = m[m["연도"].between(*dec)].groupby("월")[cols].mean()
    return pd.DataFrame({"dTA": f["TA"] - b["TA"], "dTX": f["TAMAX"] - b["TAMAX"],
                         "dTN": f["TAMIN"] - b["TAMIN"],
                         "rRN": (f["RN"] / b["RN"]).replace([np.inf, -np.inf], 1.0).fillna(1.0),
                         "rSI": (f["SI"] / b["SI"]).fillna(1.0)})


def apply_monthly_delta(df, delta):
    d = df.copy()
    mo = d["일시"].dt.month
    d[COL["tavg"]] = d[COL["tavg"]] + mo.map(delta["dTA"]).fillna(0).values
    d[COL["tmax"]] = d[COL["tmax"]] + mo.map(delta["dTX"]).fillna(0).values
    d[COL["tmin"]] = d[COL["tmin"]] + mo.map(delta["dTN"]).fillna(0).values
    d[COL["rain"]] = d[COL["rain"]] * mo.map(delta["rRN"]).fillna(1).values
    return d


def heat33_jja(df_year):
    """기상청 폭염일수와 같은 기준(최고 33℃ 이상)으로 6~8월 일수"""
    w = window(df_year, "06-01", "08-31")
    return int((w[COL["tmax"]] >= 33.0).sum())


@st.cache_data
def ssp_runs(df_s, th, ssp, sigun_m):
    """관측 연도마다: 지금(변화 없음) + 시나리오 × 시기별 지표"""
    rows = []
    years = [(y, g) for y, g in df_s.groupby("연도") if g["월일"].max() >= "09-30"]
    combos = [("관측", None, None)] + [(sc, dec, ssp_delta(ssp, sc, sigun_m, dec))
                                      for sc in SSP_NAMES for dec in SSP_DECADES]
    for sc, dec, delta in combos:
        for y, g in years:
            gg = g if delta is None else apply_monthly_delta(g, delta)
            r = indicators(gg, "09-30", th)
            r["폭염33"] = heat33_jja(gg)
            r["시나리오"], r["시기"], r["연도"] = sc, (dec_label(dec) if dec else "지금"), y
            rows.append(r)
    return pd.DataFrame(rows)


def ssp_index_table(ssp, sigun_m, dec):
    """기상청이 직접 계산한 연 극한기후지수: 2021~2030 vs 선택 시기"""
    a = ssp[(ssp["시군"] == sigun_m) & (ssp["월"] == 0)]
    mo = ssp[(ssp["시군"] == sigun_m) & (ssp["월"] > 0)]
    rn_y = mo.groupby(["시나리오", "연도"])["RN"].sum()
    a = a.set_index(["시나리오", "연도"]).copy()
    a["WETD"] = rn_y.reindex(a.index) / a["SDII"]
    items = [("HW33", "폭염일수 (최고 33℃ 이상)", "일"), ("TR25", "열대야일수 (최저 25℃ 이상)", "일"),
             ("SU25", "여름일수 (최고 25℃ 이상)", "일"), ("WETD", "비 온 날 수 (1mm 이상, 연)", "일"),
             ("CDD", "최대무강수지속기간", "일"), ("FD0", "서리일수 (최저 0℃ 미만)", "일"),
             ("GSL", "식물성장기간", "일")]
    rows = []
    for k, name, unit in items:
        r = {"지수 (1년 기준)": name}
        for sc in SSP_NAMES:
            v = a.loc[sc, k]
            b = v[(v.index >= SSP_BASE[0]) & (v.index <= SSP_BASE[1])].mean()
            f = v[(v.index >= dec[0]) & (v.index <= dec[1])].mean()
            if sc == "SSP2-4.5":
                r[f"{SSP_BASE[0]}–{SSP_BASE[1]}"] = f"{b:.1f}"
            r[f"{sc} {dec_label(dec)}"] = f"{f:.1f} ({f - b:+.1f})"
        rows.append(r)
    return pd.DataFrame(rows)


def ssp_window_change(ssp, scen, sigun_m, dec):
    """생육기(4~10월) 일사량 평균·강수량 합의 변화율 (%)"""
    m = ssp[(ssp["시나리오"] == scen) & (ssp["시군"] == sigun_m) & (ssp["월"].between(4, 10))]
    g = m.groupby("연도").agg(SI=("SI", "mean"), RN=("RN", "sum"))
    b = g.loc[SSP_BASE[0]:SSP_BASE[1]].mean()
    f = g.loc[dec[0]:dec[1]].mean()
    return (f["SI"] / b["SI"] - 1) * 100, (f["RN"] / b["RN"] - 1) * 100, b["RN"], f["RN"]


# ─────────────────────────────────────────────
# 탭 2: 내 포장 비교
# ─────────────────────────────────────────────
def percentile_of(values, x):
    v = np.asarray(values, dtype=float)
    v = v[~np.isnan(v)]
    if len(v) == 0:
        return np.nan
    return (np.sum(v < x) + 0.5 * np.sum(v == x)) / len(v) * 100


def position_text(p):
    """P10 미만 = 지역 포장 10곳 중 하위 1곳 수준, P90 초과 = 상위 1곳 수준"""
    if np.isnan(p):
        return "비교 불가", "⚪"
    if p > 90:
        return f"상위 {100 - p:.0f}% (P90 초과)", "🔵"
    if p < 10:
        return f"하위 {p:.0f}% (P10 미만)", "🟠"
    return f"P10~P90 안 (상위 {100 - p:.0f}%)", "⚪"


def dist_chart(values, mine, unit):
    v = pd.Series(values, dtype=float).dropna()
    q10, q90 = float(v.quantile(0.10)), float(v.quantile(0.90))
    lo, hi = v.quantile(0.005), v.quantile(0.995)
    lo, hi = min(lo, mine), max(hi, mine)
    v = v[(v >= lo) & (v <= hi)]
    fig = go.Figure(go.Histogram(x=v, nbinsx=30, marker_color=C_OTHER,
                                 hovertemplate=f"%{{x}} {unit}<br>%{{y}}개 포장<extra></extra>"))
    fig.add_vline(x=q10, line_color=C_MEAN, line_dash="dash", opacity=0.55)
    fig.add_vline(x=q90, line_color=C_MEAN, line_dash="dash", opacity=0.55)
    fig.add_vline(x=mine, line_color=C_THIS, line_width=3)
    fig.add_vline(x=float(v.median()), line_color=C_MEAN, line_dash="dot")
    base_layout(fig, 180, "포장 수")
    fig.update_layout(bargap=0.05, showlegend=False, margin=dict(l=10, r=10, t=4, b=10))
    fig.update_xaxes(title=unit)
    return fig


# ─────────────────────────────────────────────
# 탭 3: 자료 품질 점검
# ─────────────────────────────────────────────
def extraterrestrial(dates, lat=LAT):
    """FAO-56 대기외 일사량 Ra (MJ/m²/일)"""
    J = pd.DatetimeIndex(dates).dayofyear.values
    phi = np.radians(lat)
    dr = 1 + 0.033 * np.cos(2 * np.pi * J / 365)
    de = 0.409 * np.sin(2 * np.pi * J / 365 - 1.39)
    ws = np.arccos(-np.tan(phi) * np.tan(de))
    return 24 * 60 / np.pi * 0.0820 * dr * (ws * np.sin(phi) * np.sin(de)
                                            + np.cos(phi) * np.cos(de) * np.sin(ws))


@st.cache_data
def add_kt(wx):
    w = wx[["지역", "일시", "연도", COL["solar"]]].copy()
    if "일사량_원값" in wx.columns:
        w["일사량_점검"] = wx["일사량_원값"]
    else:
        w["일사량_점검"] = wx[COL["solar"]]
    w["Ra"] = extraterrestrial(w["일시"])
    w["KT"] = w["일사량_점검"] / w["Ra"]
    w["KT_최종"] = w[COL["solar"]] / w["Ra"]
    return w


@st.cache_data
def monthly_means(wx, cols):
    """시군 × 월 평균표 {변수: 표(행=월, 열=시군)}"""
    out = {}
    for c in cols:
        out[c] = wx.set_index("일시").groupby("지역")[c].resample("MS").mean().unstack(0)
    return out


def detect_step(mtab, region, var, min_seg=6):
    """해당 시군 월평균 - 나머지 시군 월평균 차이에서 가장 큰 계단 하나를 찾음"""
    m = mtab[var]
    if region not in m.columns or m.shape[1] < 2:
        return None
    # 나머지 시군은 중앙값으로 묶음 (다른 시군 하나의 계단이 섞여 들어오지 않게)
    d = (m[region] - m.drop(columns=region).median(axis=1)).dropna()
    x = d.values
    n = len(x)
    best = None
    for k in range(min_seg, n - min_seg):
        a, b = x[:k], x[k:]
        s = np.sqrt((((a - a.mean()) ** 2).sum() + ((b - b.mean()) ** 2).sum()) / (n - 2))
        if s == 0:
            continue
        t = abs(a.mean() - b.mean()) / (s * np.sqrt(1 / k + 1 / (n - k)))
        if best is None or t > best["t"]:
            best = {"t": t, "k": k, "날짜": d.index[k], "이전": a.mean(), "이후": b.mean()}
    if best:
        best["series"] = d
    return best


def step_grade(t):
    if t >= 10:
        return "뚜렷한 계단", "🔴"
    if t >= 6:
        return "계단 의심", "🟡"
    return "뚜렷한 계단 없음", "🟢"


@st.cache_data
def range_checks(wx):
    rows = []
    w = wx.copy()
    kt = add_kt(wx)["KT"].values
    for sg, g in w.groupby("지역"):
        idx = g.index
        checks = {
            "최저기온 > 최고기온": (g[COL["tmin"]] > g[COL["tmax"]]),
            "평균기온이 최저~최고 밖": ((g[COL["tavg"]] < g[COL["tmin"]]) | (g[COL["tavg"]] > g[COL["tmax"]])),
            "기온 -30℃ 미만 또는 45℃ 초과": ((g[COL["tmin"]] < -30) | (g[COL["tmax"]] > 45)),
            "습도 0% 미만 또는 100% 초과": ((g[COL["rh"]] < 0) | (g[COL["rh"]] > 100)),
            "강수량 음수": (g[COL["rain"]] < 0),
            "일사량이 물리 상한 초과 (청천지수 0.80 초과)": pd.Series(kt[idx] > 0.80, index=idx),
            "일사량 30MJ 이상이면서 그날 비 10mm 이상": ((g["일사량_원값"] if "일사량_원값" in g else g[COL["solar"]]) >= 30) & (g[COL["rain"]] >= 10),
        }
        for name, mask in checks.items():
            mask = mask.fillna(False)
            if mask.sum() > 0:
                yrs = g.loc[mask, "연도"].value_counts().sort_index()
                rows.append({"시군": sg, "점검 항목": name, "건수": int(mask.sum()),
                             "해당 연도": ", ".join(f"{y}({c})" for y, c in yrs.items())})
        if COL["dew"] in g.columns:
            gs = g[g["일시"].dt.month.between(5, 9)]
            zero = (gs[COL["dew"]] == 0).groupby(gs["연도"]).mean()
            bad = zero[zero >= 0.5]
            if len(bad):
                rows.append({"시군": sg, "점검 항목": "생육기 결로시간 0분인 날이 절반 이상",
                             "건수": int(len(bad)),
                             "해당 연도": ", ".join(f"{y}({v:.0%})" for y, v in bad.items())})
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────
# 자료실 · 작황조사 대시보드
# ─────────────────────────────────────────────
def list_docs():
    """app.py 폴더와 그 안의 '자료실' 폴더에 있는 PDF 목록"""
    found = []
    for folder in [HERE, os.path.join(HERE, "자료실")]:
        if os.path.isdir(folder):
            for f in sorted(os.listdir(folder)):
                if f.lower().endswith(".pdf") and not f.startswith("~$"):
                    found.append(os.path.join(folder, f))
    return found


def doc_label(path):
    name = os.path.splitext(os.path.basename(path))[0]
    name = name.lstrip("♥♡★☆ _-")
    mb = os.path.getsize(path) / 1e6
    return f"{name} ({mb:.1f}MB)"


@st.cache_resource
def read_bytes(path, mtime):
    with open(path, "rb") as f:
        return f.read()


@st.cache_data
def read_text(path, mtime):
    with open(path, encoding="utf-8") as f:
        return f.read()


# ─────────────────────────────────────────────
# 화면 시작
# ─────────────────────────────────────────────
apply_design()

# 연구 요약 탭은 앱 주소 뒤에 ?mode=research 를 붙였을 때만 보인다
try:
    _mode = st.query_params.get("mode")
except AttributeError:   # 예전 Streamlit
    _mode = (st.experimental_get_query_params().get("mode") or [None])[0]
RESEARCH = _mode == "research"

wpath = find_weather_file()
if wpath is None:
    up = st.file_uploader("농업기상 정제본 CSV를 올려주세요", type="csv")
    if up is None:
        st.stop()
    wx_raw, wname = load_weather(up), up.name
else:
    wx_raw, wname = load_weather(wpath), os.path.basename(wpath)

# ── 기상청 API허브 자동 갱신 ──
API_KEY = kma_api_key()
API_NOTES = []
API_YEARS = set()          # API로 받아온 연도 (관측망 차이 안내용)
_base_last = wx_raw["일시"].max().date()
_kst_today = (pd.Timestamp.utcnow() + pd.Timedelta(hours=9)).date()
if API_KEY:
    try:
        _api_df, API_NOTES = fetch_kma_api(API_KEY, (_base_last + timedelta(days=1)).isoformat(),
                                           (_kst_today - timedelta(days=1)).isoformat())
    except Exception as _e:
        _api_df, API_NOTES = None, [f"⚠ API 갱신 실패: {_e}"]
    if _api_df is not None and len(_api_df):
        wx_raw = merge_weather(wx_raw, _api_df)
        API_YEARS = set(int(y) for y in _api_df["일시"].dt.year.unique())

# ── 올해 기상자료 넣기 (시즌 중 진단용) ──
EXTRA_NOTES = []
_extra_parts = []
_auto_extra = sorted(f for f in os.listdir(HERE)
                     if "올해기상" in f.replace(" ", "") and f.lower().endswith(".csv")) \
    if os.path.isdir(HERE) else []
for _f in _auto_extra:
    with open(os.path.join(HERE, _f), "rb") as _fh:
        _d, _m = parse_extra_weather(_fh.read(), _f)
    EXTRA_NOTES += _m
    if _d is not None:
        _extra_parts.append(_d)
with st.sidebar:
    _wx_last = wx_raw["일시"].max().date()
    with st.expander("📥 올해 기상자료 넣기", expanded=(date.today().year > _wx_last.year)):
        if API_KEY:
            st.markdown("**🔄 기상청 API 자동 갱신**")
            for _n in API_NOTES:
                st.caption("· " + _n)
            if st.button("지금 다시 받기", key="api_refresh",
                         help="보통은 6시간마다 알아서 다시 받아요"):
                fetch_kma_api.clear()
                st.rerun()
            st.divider()
        else:
            st.caption("🔑 기상청 API허브(apihub.kma.go.kr) 인증키를 설정하면 올해 일자료가 자동으로 "
                       "갱신됩니다. app.py 폴더 안 `.streamlit/secrets.toml` 파일에 "
                       '`KMA_API_KEY = "발급키"` 한 줄을 넣으세요(Streamlit Cloud는 앱 Settings의 '
                       "Secrets에 같은 줄). 키가 든 파일은 GitHub에 올리면 안 됩니다.")
            st.divider()
        st.caption(f"기상자료는 지금 **{_wx_last:%Y년 %m월 %d일}**까지 있습니다. "
                   "일자료 CSV를 직접 올려도 됩니다. 여러 시군 파일을 한꺼번에 올려도 되고, "
                   "같은 날짜는 올린 파일이 API 자료보다 우선합니다.")
        ups = st.file_uploader("일자료 CSV (기상자료개방포털 ASOS·AWS, 농업기상)", type="csv",
                               accept_multiple_files=True, key="extra_wx")
        for _i, _u in enumerate(ups or []):
            _raw = _u.getvalue()
            _d, _m = parse_extra_weather(_raw, _u.name)
            if _d is None:
                _sg = st.selectbox(f"'{_u.name}'은 어느 시군 자료인가요?", ["고르세요"] + SIGUN_ORDER,
                                   key=f"extra_sg_{_i}")
                if _sg != "고르세요":
                    _d, _m = parse_extra_weather(_raw, _u.name, _sg)
            EXTRA_NOTES += _m
            if _d is not None:
                _extra_parts.append(_d)
        if _extra_parts:
            _e = pd.concat(_extra_parts)
            st.success("넣은 자료: " + ", ".join(
                f"{sg} {g['일시'].min():%m/%d}~{g['일시'].max():%m/%d}({g['일시'].dt.year.iloc[0]}년)"
                for sg, g in _e.groupby("지역")))
        for _n in EXTRA_NOTES:
            st.caption("· " + _n)
        st.caption("기상자료개방포털(data.kma.go.kr) → 기후통계분석/자료 → 종관기상관측(ASOS) 또는 "
                   "방재기상관측(AWS) → 일자료 → CSV 내려받기. 평년(2016년 이후)은 농업기상 관측망 자료라, "
                   "다른 관측망 자료를 넣으면 지점 차이만큼 판정이 달라질 수 있어요. "
                   "앱 폴더에 이름에 '올해기상'이 들어간 CSV를 두면 매번 올리지 않아도 됩니다.")
if _extra_parts:
    wx_raw = merge_weather(wx_raw, pd.concat(_extra_parts))

apath = find_file(["ASOS"], ".csv", exclude=("올해기상",))
asos = load_asos_solar(apath) if apath else None
wx, SOLAR_NOTES, SOLAR_FINAL = apply_final_solar(wx_raw, asos)

_y0, _y1 = int(wx["연도"].min()), int(wx["연도"].max())
hero([f"{wx['지역'].nunique()}개 시군", f"기상 {_y0}–{_y1}", "작황조사 2016–2024", "농가 정밀조사 19농가 (2018–2026)"])

regions = list(wx["지역"].unique())
yecheon_substitute = False
if "예천군" not in regions and "안동시" in regions:
    regions.append("예천군")
    yecheon_substitute = True
regions = [r for r in SIGUN_ORDER if r in regions] + [r for r in regions if r not in SIGUN_ORDER]

# ── 사이드바 ──
with st.sidebar:
    st.header("조건 선택")
    sigun = st.selectbox("시군", regions, key="sigun")
    data_sigun = "안동시" if (sigun == "예천군" and yecheon_substitute) else sigun
    df_s = wx[wx["지역"] == data_sigun]
    years = sorted(df_s["연도"].unique())
    year = st.selectbox("연도", years[::-1], key="year")

    last_day = df_s[df_s["연도"] == year]["일시"].max().date()
    season_end = date(year, *SEASON_END)
    default_end = max(min(last_day, season_end), date(year, *SEASON_START))
    end_day = st.date_input("기준일 (이 날까지 진단)", value=default_end,
                            min_value=date(year, *SEASON_START), max_value=default_end,
                            help="지난 해를 고르고 기준일을 7월 중순 등으로 당기면, 그해 시즌 중에 이 앱을 "
                                 "썼다면 무엇이 보였을지 그대로 재현됩니다(시연용)")
    end_md = end_day.strftime("%m-%d")
    if last_day < date(year, *SEASON_START):
        st.warning(f"{year}년 자료가 {last_day:%m월 %d일}까지만 있어 아직 진단할 수 없어요.")

    with st.expander("위험일 기준값 조정"):
        th = {
            "hot_pre": st.number_input("착과 전 고온일: 최고기온 (℃ 이상)", value=33.0, step=0.5,
                                       help="기본 기준은 관측소 33℃ (포장 센서 34℃ 상당). 시군 자료는 기준을 "
                                            "31~37℃로 바꿔도 같은 방향이고 33℃ 이상에서 유의했어요"),
            "rain_wet": st.number_input("탄저병: 비 온 날 기준 (mm 이상)", value=1.0, step=0.5),
            "tan_use_tmax": st.checkbox("탄저병: 기온 조건도 같이 걸기", value=False,
                                        help="작황조사와 대조해보면, 기온 조건을 걸면 실제 탄저병 발생과 오히려 덜 맞았어요"),
            "tan_tmax": st.number_input("탄저병: 최고기온 (℃ 이상)", value=25.0, step=0.5),
            "hot": st.number_input("고온일: 최고기온 (℃ 이상)", value=30.0, step=0.5),
            "heat": st.number_input("폭염일: 최고기온 (℃ 이상)", value=33.0, step=0.5),
            "cold": st.number_input("저온일: 최저기온 (℃ 이하)", value=13.0, step=0.5),
            "rain_good": st.number_input("가뭄: 비다운 비 기준 (mm 이상)", value=5.0, step=1.0),
            "rain_dry": st.number_input("무강수일: 강수량 (mm 미만)", value=1.0, step=0.5),
        }
    docs = list_docs()
    if docs:
        st.divider()
        st.markdown("**📚 자료실**")
        for i, dp in enumerate(docs):
            st.download_button("⬇️ " + doc_label(dp), data=read_bytes(dp, os.path.getmtime(dp)),
                               file_name=os.path.basename(dp).lstrip("♥♡★☆ _-"),
                               mime="application/pdf", key=f"doc_{i}")
    if sigun == "예천군" and yecheon_substitute:
        st.info("예천군은 기상 실측자료가 없어 안동시 자료로 대체해 보여줍니다.")

TAB_DEF = [  # (키, 이름, ?mode=research 에서만)
    ("home", "🗓️ 오늘의 진단", False),
    ("t1", "생육기 기상 위험 진단", False),
    ("pest", "병해충 발생 위험·평년", False),
    ("sc", "기상 시나리오", False),
    ("t2", "내 포장 비교", False),
    ("y", "수확량 조기예측", False),
    ("db", "작황조사 대시보드", False),
    ("t3", "자료 품질 점검", True),
    ("t4", "연구 요약", True),
    ("man", "📖 사용 설명서", False),
]
_shown = [(k, n) for k, n, r in TAB_DEF if RESEARCH or not r]
_tabs = dict(zip([k for k, _ in _shown], st.tabs([n for _, n in _shown])))
tab_home, tab1, tab_pest, tab_sc, tab2, tab_y, tab_db, tab3, tab4, tab_man = \
    [_tabs.get(k) for k, _, _ in TAB_DEF]

# ══════════════════════════════════════════════
# 탭 1: 생육기 기상 위험 진단
# ══════════════════════════════════════════════
hpath_all = find_file(["하반기"], ".xlsx")
spath_all = find_file(["상반기"], ".xlsx")
yr_df = df_s[df_s["연도"] == year]
fin_tbl = all_years(df_s, PEST_END, PEST_TH)          # 지난 해마다 7/31 시점 값 (판정 기준 고정)
fin_base = fin_tbl.drop(year, errors="ignore")
same_base = all_years(df_s, end_md, PEST_TH).drop(year, errors="ignore")  # 같은 날까지 평년


def harvest_normal_md(df_s, year):
    doys = []
    for y, g in df_s.groupby("연도"):
        if y == year:
            continue
        d_end = harvest_end_day(g, HARVEST_END["임계"])
        if d_end is not None:
            doys.append(d_end.timetuple().tm_yday)
    if not doys:
        return None
    return (date(2001, 1, 1) + timedelta(days=int(round(np.mean(doys))) - 1)).strftime("%m-%d")


HARVEST_MD = harvest_normal_md(df_s, year)

# ══════════════════════════════════════════════
# 탭: 오늘의 진단 (첫 화면)
# ══════════════════════════════════════════════
with tab_home:
    today = date.today()
    st.subheader(f"{sigun} · {year}년 {end_day.month}월 {end_day.day}일 기준")
    if year < today.year and wx["연도"].max() < today.year:
        st.warning(f"**올해({today.year}년) 기상자료가 아직 없습니다.** 지금 화면은 {year}년을 "
                   f"{end_day.month}월 {end_day.day}일 시점에서 다시 본 것입니다. "
                   "시즌 중에 쓰려면 왼쪽 **📥 올해 기상자료 넣기**에서 CSV를 올려 주세요.")
    elif today > date(year, 9, 30) and end_md >= "09-30":
        st.info(f"**{year}년 판정 집계가 모두 끝나(9월 30일 마감) 시즌 최종 진단을 보여줍니다.** "
                "판정 항목은 모두 9월 30일까지만 셉니다(착과 전 고온 7/28, 고온·저온·가뭄 8/31, "
                "탄저병 9/30 마감). 그래서 기준일을 더 뒤로 옮겨도 숫자는 바뀌지 않습니다. "
                "시즌 중(5~9월)에는 기준일이 오늘 날짜를 따라갑니다."
                + (f" 기상자료는 {last_day:%m월 %d일}까지 들어와 있습니다."
                   if last_day > end_day else "")
                + " 수확이 언제 끝날지는 **생육기 기상 위험 진단** 탭의 '🍂 수확은 언제쯤 끝날까'에서 "
                  "기준일과 관계없이 볼 수 있습니다.")
    elif year == today.year and (today - last_day).days > 3 and today.month <= 10:
        st.info(f"{sigun} 기상자료는 {last_day:%m월 %d일}까지입니다. 최신 일자료를 넣으면 판정이 갱신됩니다.")
    st.caption("판정 기준은 영농기술정보 A·B와 같은 고정값입니다(왼쪽 기준값 조정과 무관). "
               f"평년 = {year}년을 뺀 {year_span(fin_base.index)}. 시군 관측소 자료 기준입니다."
               + (f" {year}년 값은 기상청 관측소(ASOS·AWS) 자동 수신분이고 평년은 농업기상 관측망이라, "
                  "지점 차이만큼 경계에 걸친 판정은 1~2일 다를 수 있습니다." if year in API_YEARS else ""))

    show_chart(timeline_chart(end_md, HARVEST_MD))

    # ── 판정 카드 ──
    report = {}
    hc, p1, p2, p3 = st.columns(4)

    # 1) 착과 전 고온
    with hc:
        st.markdown("**🌡️ 7월 전후 고온 점검 (7/3~7/28)**")
        v = ind_value(yr_df, "착과전고온", PEST_TH, end_md)
        m_h = float(fin_base["착과전고온"].mean()) if len(fin_base) else np.nan
        sd_h = float(fin_base["착과전고온"].std(ddof=1)) if len(fin_base) > 2 else np.nan
        if v is None:
            st.metric(f"관측소 {PEST_TH['hot_pre']:g}℃ 이상", "집계 전")
            st.markdown(f"⚪ 7월 3일부터 셉니다 · 평년 {m_h:.1f}일")
            heat_line = f"착과 전 고온일: 집계 전(7/3부터), 평년 {m_h:.1f}일"
        else:
            fixed = end_md >= "07-28"
            m_same = float(same_base["착과전고온"].mean()) if len(same_base) else m_h
            st.metric(f"관측소 {PEST_TH['hot_pre']:g}℃ 이상", f"{v}일",
                      delta=f"{v - (m_h if fixed else m_same):+.1f}일 ({'평년' if fixed else '같은 날 평년'} 대비)",
                      delta_color="inverse")
            if fixed:
                label, icon = judge(v, fin_base["착과전고온"].dropna().tolist(), True)
                st.markdown(f"{icon} **{label}** (확정) · 평년 {m_h:.1f}일")
                final_v = v
                vals = []
            else:
                ol = finish_outlook(df_s, year, end_md, "착과전고온", PEST_TH, "07-28")
                vals = list(ol.values())
                st.markdown(f"🟡 **집계 중** · 평년 {m_h:.1f}일")
                if vals:
                    st.caption(f"남은 기간이 과거 각 해처럼 흐르면 7/28에 **{min(vals)}~{max(vals)}일** "
                               f"(중앙 {np.median(vals):.0f}일)")
                final_v = np.median(vals) if vals else v
            d_more = final_v - m_h
            if d_more >= 1:
                lo, hi = loss_range(d_more)
                st.caption(f"평년보다 {d_more:.0f}일 많으면 수량 약 **{lo:.1f}~{hi:.1f}% 감소**(예측이 아닌 참고 범위)")
            heat_line = (f"착과 전 고온일(7/3~7/28, 관측소 최고 {PEST_TH['hot_pre']:g}℃ 이상): {v}일"
                         f"{'' if fixed else '(집계 중)'}, 평년 {m_h:.1f}일")
            if not fixed and vals:
                heat_line += (f" · 남은 기간이 과거 각 해처럼 흐르면 7/28에 "
                              f"{min(vals)}~{max(vals)}일(중앙 {np.median(vals):.0f}일)")
        st.caption(f"관측소 {PEST_TH['hot_pre']:g}℃ 일수는 포장 센서 34℃ 일수와 평균이 같습니다(2021~2025). "
                   "저지대 포장일수록 고온일이 더 많아요.")
        report["heat"] = heat_line

    # 2~4) 병해충 다발 위험
    for col, key in zip([p1, p2, p3], ["탄저", "고온", "건조"]):
        r = PEST_RULES[key]
        with col:
            st.markdown(f"**{'🍂' if key == '탄저' else ('🐛' if key == '고온' else '💧')} {r['name']} 다발 위험**")
            v = ind_value(yr_df, key, PEST_TH, min(end_md, PEST_END))
            ol = finish_outlook(df_s, year, min(end_md, PEST_END), key, PEST_TH, PEST_END) \
                if v is not None and end_md < PEST_END else {}
            status, icon, txt = pest_status(v, r, end_md, ol)
            unit = "비 온 날" if key == "탄저" else ("30℃ 이상" if key == "고온" else "비다운 비")
            m_p = float(fin_base[key].mean()) if len(fin_base) else np.nan
            st.metric(unit, "집계 전" if v is None else f"{v}일",
                      delta=None if v is None else f"기준 {'≥' if r['high_bad'] else '≤'} {r['cut']}일",
                      delta_color="off")
            st.markdown(f"{icon} **{status}** · 7/31 평년 {m_p:.1f}일")
            if v is not None and end_md < PEST_END and len(same_base):
                st.caption(f"같은 날 평년 {same_base[key].mean():.1f}일. " + txt)
            else:
                st.caption(txt)
            report[key] = (f"{r['name']}: {r['rule']} 기준 → 지금 {'-' if v is None else str(v) + '일'}, "
                           f"{status} (7/31 평년 {m_p:.1f}일)")
            if v is not None and end_md < PEST_END and ol:
                hit = sum(1 for x in ol.values()
                          if (x >= r["cut"] if r["high_bad"] else x <= r["cut"]))
                report[key] += (f" · 남은 기간이 과거 각 해처럼 흐르면 "
                                f"{len(ol)}개 해 중 {hit}개 해 기준 도달")

    st.caption("🔴 다발 위험 · 🟠 집계 중이지만 과거 날씨 절반 이상에서 기준 도달 · 🟡 집계 중 · 🟢 위험 낮음 · ⚪ 집계 전. "
               "다발 위험은 '다발 확정'이 아니라 예찰·방제를 강화하라는 신호입니다. "
               "근거와 평년 발생 수준은 **병해충 발생 위험·평년** 탭에 있습니다.")

    # ── 지금 할 일 ──
    st.markdown("### 지금 할 일")
    todo = []
    if end_md < "07-03":
        todo.append("🌡️ **포장 온도계(또는 센서)를 7월 3일 전에 설치하세요.** 착과 전 고온 피해는 포장 센서에서만 "
                    "보이고 시군 관측소로는 보이지 않았습니다. 위성·잎 상태로도 판단할 수 없습니다. "
                    "차광 기구 안 1.5m 높이가 표준입니다.")
    elif end_md <= "07-28":
        todo.append("🌡️ **지금이 착과 전 고온 창(7/3~7/28)입니다.** 포장 최고기온 34℃ 이상인 날을 기록하세요. "
                    f"1일당 주당 수확과수가 약 {abs(HEAT_PRE['센서과수']):.1f}% 줄었습니다(포장 센서 "
                    f"{HEAT_PRE['센서표본']}). 저지대 포장(해발 100m 낮을수록 약 2일 더 많음)은 더 주의하세요.")
    if "06-01" <= end_md <= "08-31":
        tan = ind_value(yr_df, "탄저", PEST_TH, min(end_md, PEST_END))
        if tan is not None and tan >= PEST_RULES["탄저"]["cut"]:
            todo.append("🍂 **탄저병 다발 위험 기준을 넘었습니다.** 병든 과실을 바로 따내고 예찰·방제 간격을 "
                        "좁히세요. 병든 과실 제거가 약제만 뿌리는 것보다 효과가 크고(재배전서 243~244쪽, 표 9-8), "
                        "발생 뒤 살포는 효과가 낮습니다(표 9-7).")
        elif end_md < PEST_END:
            todo.append("🍂 탄저병은 **발생 전 예방 위주 살포**가 효과적입니다(발생 전부터 살포 시 방제효과 90% "
                        "이상, 재배전서 244쪽 표 9-7). 비 온 날이 기준(7/31까지 20일)에 가까워지면 예찰을 늘리세요.")
    if "05-01" <= end_md <= "08-15":
        dry = ind_value(yr_df, "건조", PEST_TH, min(end_md, PEST_END))
        if dry is not None and dry <= PEST_RULES["건조"]["cut"]:
            todo.append("💧 **비다운 비가 적은 편입니다.** 토양이 마르지 않게 관리하세요(재배전서 244쪽). "
                        "가문 해에는 점적관수 포장에서도 석회결핍 발생이 줄지 않았습니다. 증상이 보이면 "
                        "염화칼슘 또는 인산제1칼슘 0.3%액 살포가 응급 대책입니다(재배전서 222쪽).")
    if "07-25" <= end_md <= "09-05":
        todo.append("📏 **8월 말~9월 초(늦어도 9월 3일)에 초장·착과수를 재고, 8월 31일까지 수확량을 기록하세요.** "
                    f"수확량 조기예측 탭에서 최종 주당 수확량을 평균 오차 {MODEL_EARLY['8월 말']['mape']:.1f}%로 "
                    "가늠할 수 있습니다.")
    if end_md >= "08-15" and HARVEST_MD:
        todo.append(f"🍂 이 지역 수확 종료 기준일(일평균 12℃ 이하 첫날)은 평년 **{int(HARVEST_MD[:2])}월 "
                    f"{int(HARVEST_MD[3:])}일**쯤입니다. 농가는 보통 이보다 5일쯤 먼저 끝냈습니다. "
                    "수확이 끝나면 병든 과실·고춧대를 밭에서 치워 다음 해 탄저병 전염원을 없애세요(재배전서 243쪽).")
    if not todo:
        todo.append("지금 시기에는 판정할 항목이 없습니다. 기준일을 바꿔 보세요.")
    for t in todo:
        st.markdown("- " + t)

    # ── 내 포장 온도계로 보기 ──
    with st.expander("🌡️ 내 포장 온도계로 센 일수로 보기 (관측소보다 정확)"):
        st.markdown("착과 전 고온 결과는 **포장 센서**에서 나온 것입니다. 포장에서 직접 센 일수를 넣으면 "
                    "관측소 일수보다 실제 노출에 가깝게 볼 수 있어요.")
        c1, c2 = st.columns([1, 2])
        n_field = c1.number_input("7/3~7/28 포장 최고 34℃ 이상인 날 (일)", min_value=0, max_value=26,
                                  value=0, step=1, key="field_heat")
        # 관측소 33℃ 평년 = 포장 센서 34℃ 평년 (2021~2025 평균 일수 일치)
        field_norm = m_h
        with c2:
            if n_field > 0 and not np.isnan(field_norm):
                d_f = n_field - field_norm
                fruit = (1 - (1 + HEAT_PRE["센서과수"] / 100) ** max(d_f, 0)) * 100
                st.markdown(f"포장 34℃ 평년 추정 **{field_norm:.1f}일**(관측소 {PEST_TH['hot_pre']:g}℃ "
                            f"평년과 같다고 봄) 대비 **{d_f:+.1f}일**")
                if d_f > 0:
                    st.markdown(f"→ 주당 수확과수 약 **{fruit:.0f}% 감소** 예상 "
                                f"(1일당 {HEAT_PRE['센서과수']:.1f}%, WCR p={HEAT_PRE['센서과수p']})")
                else:
                    st.markdown("→ 평년보다 적거나 비슷합니다. 착과 전 고온 피해 걱정은 적은 해입니다.")
                report["field"] = f"포장 온도계 착과 전 34℃ 이상 {n_field}일 (포장 평년 추정 {field_norm:.1f}일)"
            else:
                st.caption("일수를 넣으면 결과가 나옵니다.")
        st.caption(f"근거: 농가 포장 센서 {HEAT_PRE['센서표본']}, 농가·연도 고정효과. 연도를 하나씩 빼면 "
                   f"{HEAT_PRE['연도제외']}로 방향은 같지만 {HEAT_PRE['연도제외주의']}로 약해집니다. "
                   "포장 34℃ 평년은 관측소 33℃ 평년과 같다고 봅니다(2021~2025년 두 일수의 평균이 같음).")

    # ── 6개 시군 한눈에 ──
    with st.expander("🗺️ 6개 시군 같은 날 비교"):
        rows = []
        for sg in [s for s in SIGUN_ORDER if s in wx["지역"].unique()]:
            g = wx[wx["지역"] == sg]
            gy = g[g["연도"] == year]
            if gy.empty or gy["월일"].max() < end_md:
                continue
            ft = all_years(g, PEST_END, PEST_TH).drop(year, errors="ignore")
            row = {"시군": sg}
            vh = ind_value(gy, "착과전고온", PEST_TH, end_md)
            row["착과 전 고온 (평년)"] = "집계 전" if vh is None else f"{vh}일 ({ft['착과전고온'].mean():.1f})"
            for key in ["탄저", "고온", "건조"]:
                r = PEST_RULES[key]
                vv = ind_value(gy, key, PEST_TH, min(end_md, PEST_END))
                stt, ic, _ = pest_status(vv, r, end_md, {})
                row[f"{r['name']} (기준 {'≥' if r['high_bad'] else '≤'}{r['cut']})"] = \
                    "집계 전" if vv is None else f"{ic} {vv}일"
            rows.append(row)
        if rows:
            show_table(pd.DataFrame(rows).set_index("시군"))
            st.caption("괄호는 착과 전 고온 평년(선택 연도 제외). 집계 중인 칸의 색은 지금까지 값만 본 것이며 "
                       "남은 기간 전망은 각 시군을 골라 위 카드에서 보세요.")
        else:
            st.caption("같은 날 자료가 있는 시군이 없어요.")

    # ── 보고용 요약 ──
    st.markdown("### 보고용 요약")
    rep_txt = "\n".join(
        [f"[고추 쑥쑥이] {sigun} {year}년 {end_day.month}월 {end_day.day}일 기준",
         "- " + report.get("heat", "")]
        + ["- " + report[k] for k in ["탄저", "고온", "건조"] if k in report]
        + (["- " + report["field"]] if "field" in report else [])
        + ([f"- 수확 종료 기준일(일평균 12℃ 이하 첫날) 평년: {int(HARVEST_MD[:2])}월 {int(HARVEST_MD[3:])}일"]
           if HARVEST_MD else [])
        + [f"※ 고온일은 시군 관측소 {PEST_TH['hot_pre']:g}℃ 기준(포장 센서 34℃ 상당, 2021~2025 평균 일수 일치).",
           "※ 다발 위험은 예찰·방제 강화 신호이며 발생 확정이 아님.",
           "자료: 경상북도농업기술원 영양고추연구소 「고추 생산 변동 요인 분석」, 고추 쑥쑥이"])
    st.text_area("작황 보고·문자 안내에 붙여 쓰세요", rep_txt, height=210,
                 key=f"rep_txt_{sigun}_{year}_{end_md}_{st.session_state.get('field_heat', 0)}")
    st.download_button("⬇️ 요약 내려받기 (메모장·한글에서 열림)", rep_txt.encode("utf-8-sig"),
                       file_name=f"고추진단요약_{sigun}_{year}{end_md.replace('-', '')}.txt",
                       mime="text/plain", key="dl_rep")

# ══════════════════════════════════════════════
# 탭: 병해충 발생 위험·평년 (영농기술정보 B)
# ══════════════════════════════════════════════
with tab_pest:
    st.subheader("병해충 발생 위험과 평년 발생 수준")
    st.caption("하반기 작황조사(7월 말~8월 초) 전의 날씨로 판정하고, 기준값은 왼쪽 조정과 관계없이 고정입니다.")

    st.markdown(f"#### {sigun} {year}년 다발 위험 판정 ({end_day.month}월 {end_day.day}일 기준)")
    prow = []
    for key, r in PEST_RULES.items():
        v = ind_value(yr_df, key, PEST_TH, min(end_md, PEST_END))
        ol = finish_outlook(df_s, year, min(end_md, PEST_END), key, PEST_TH, PEST_END) \
            if v is not None and end_md < PEST_END else {}
        status, icon, txt = pest_status(v, r, end_md, ol)
        prow.append({"병해충": r["name"], "판정 기준": r["rule"],
                     "지금까지": "집계 전" if v is None else f"{v}일",
                     "7/31 평년": f"{fin_base[key].mean():.1f}일" if len(fin_base) else "-",
                     "판정": f"{icon} {status}", "설명": re.sub(r"\*\*", "", txt)})
    show_table(pd.DataFrame(prow), hide_index=True)
    for key, r in PEST_RULES.items():
        st.caption(f"**{r['name']}** — {r['note']}")

    st.markdown("#### 시기별 활용 절차")
    st.markdown("""
| 시기 | 할 일 | 이 앱에서 |
|---|---|---|
| 5월~6월 중순 | 가뭄(비다운 비) 집계 시작. 탄저병 전염원(병든 잔재물) 정리 | 오늘의 진단 카드 |
| 6월 15일~7월 하순 | 비 온 날이 기준(20일)에 가까워지는지 매주 확인. 발생 전 예방 위주 살포 | 카드의 '과거 날씨로 본 전망' |
| 7월 31일 | 세 가지 다발 위험 판정 확정 → 예찰·방제 강화 대상 시군 안내 | 이 표, 보고용 요약 |
| 8월 | 다발 위험 시군 예찰 강화, 병든 과실 즉시 제거 | - |
| 수확 후 | 그해 작황조사 결과를 평년과 비교해 기준 점검 | 아래 '그해 작황조사와 평년' |
""")

    hv_all = load_survey(hpath_all) if hpath_all else None
    sv_all = load_survey(spath_all) if spath_all else None

    # 조사 전 날씨 구간별 실제 발생 포장 비율 (작황조사로 계산)
    if hv_all is not None:
        skip = ("예천군",) if yecheon_substitute else ()
        jp = season_table(wx, PEST_TH, skip, VALID_END).join(survey_rates(hv_all), how="inner")
        if not jp.empty:
            st.markdown("#### 조사 전 날씨 구간별 실제 발생 포장 비율 (작황조사로 계산)")
            bcols = st.columns(len(VALID_PAIRS))
            for bc, (k, _, oname) in zip(bcols, VALID_PAIRS):
                if oname not in jp.columns:
                    continue
                with bc:
                    st.markdown(f"**{PEST_RULES[k]['name']}** ({valid_window(k)})")
                    show_table(bin_table(jp, k, oname).rename(
                        columns={"평균 발생 포장 비율": "발생 포장 비율"}), hide_index=True)
            st.caption(f"6개 시군 × {int(jp.index.get_level_values(1).min())}~"
                       f"{int(jp.index.get_level_values(1).max())}년 {len(jp)}사례, 구간별 시군-연도 평균. "
                       "같은 해에는 시군 날씨가 비슷하게 움직여 독립 정보는 연도 수(약 9년)에 가깝습니다.")

    # 시군별 평년 발생 포장 비율 (상반기 왼쪽, 하반기 오른쪽)
    st.markdown("#### 시군별 평년 발생 포장 비율")
    cS, cH = st.columns([1, 1.3])
    if hv_all is not None:
        occ_h = occ_rates_h(hv_all)
        nt, (a, b) = normal_table(occ_h, [n for n, _, _ in PEST_LIST_H])
        with cH:
            st.markdown(f"**하반기 (7월 말 조사, {a}~{b}년, %)**")
            show_table(nt)
            st.caption("탄저병·담배나방·석회결핍은 1개 이상 관찰된 포장, 바이러스·총채벌레·세균반점은 "
                       "등급 3 이상인 포장의 비율(조사 포장 전체 합산). 탄저병은 2023년 일부·2024년 조사 주수가 "
                       "10주에서 3주로 줄어 그 뒤 비교에 주의하세요.")
    if sv_all is not None:
        occ_s = occ_rates_s(sv_all)
        ns, (a, b) = normal_table(occ_s, [n for n, _ in PEST_LIST_S])
        with cS:
            st.markdown(f"**상반기 (5월 말 조사, {a}~{b}년, %)**")
            show_table(ns)
            st.caption("발생 유무 1인 포장의 비율(조사 포장 전체 합산).")
    if hv_all is None and sv_all is None:
        st.info("작황조사 파일이 있으면 평년 발생 수준이 나와요.")

    # 그해 작황조사와 평년
    if hv_all is not None:
        st.markdown(f"#### 그해 작황조사와 평년 — {sigun}")
        yrs_h = sorted(hv_all["년도"].dropna().astype(int).unique())
        yy = st.selectbox("작황조사 연도", yrs_h[::-1],
                          index=(yrs_h[::-1].index(year) if year in yrs_h else 0), key="pest_yy")
        yv = year_vs_normal(occ_rates_h(hv_all), sigun, yy, [n for n, _, _ in PEST_LIST_H])
        if len(yv):
            show_table(yv, hide_index=True)
            st.caption("평년 = 그해를 뺀 연도별 발생 포장 비율의 평균. 평균 ± 1표준편차를 벗어나고 5%p 이상 "
                       "차이일 때만 많음·적음으로 판정합니다.")
            tan_v = fin_tbl.loc[yy, "탄저"] if yy in fin_tbl.index else None
            if tan_v is not None:
                st.caption(f"{sigun} {yy}년 6/15~7/31 비 온 날 {int(tan_v)}일 "
                           f"({'기준 20일 이상 → 다발 위험이었음' if tan_v >= 20 else '기준 미만'}).")
        else:
            st.caption("이 시군·연도 작황조사가 없어요.")

    with st.expander("🔎 탄저병 기준(비 온 날 20일)의 근거"):
        st.markdown("""
| 항목 | 값 |
|---|---|
| 기준에 든 사례 | 54사례 중 16사례 (2017·2020·2021·2023·2024년) |
| 발생 포장 비율 | 기준에 든 해 28.1% / 아닌 해 8.7% (약 3배) |
| 시군 평년보다 뚜렷이 많았던 해(8사례)를 잡은 비율 | 7/8 (놓친 1건: 청송 2021, 비 온 날 18일) |
| 기준에 든 해 중 실제로 뚜렷이 많았던 해 | 7/16 (나머지는 평년 수준) |
| 기준 일수 민감도 (잡은 비율 / 맞힌 비율) | 18일 100 / 31% · 20일 88 / 44% · 22일 63 / 63% |

- **다른 강우 지표와 비교**: 누적 기간 1~14일, 기준량 1~200mm로 바꾼 50개 지표를 함께 봤지만, 연도를 바꿔도
  비 온 날 수보다 일관되게 나은 지표는 없었습니다. **큰비의 횟수보다 비가 자주 오는 정도**가 탄저병과 더 잘 맞습니다.
- **조사 주수**: 2023년 일부와 2024년은 3주 조사입니다. 3주 조사 포장을 빼도 구간별 발생 포장 비율은
  6.7 / 13.9 / 25.5%, 시군 내 상관 0.61로 결론이 같았습니다.
- **한계**: 뚜렷이 많았던 해가 2020·2023년에 몰려 있고(8건 중 7건), 2023년을 빼면 상관이 0.43으로 낮아집니다.
""")

with tab1:
    tbl = all_years(df_s, end_md, th)
    cur = indicators(df_s[df_s["연도"] == year], end_md, th)
    others = tbl.drop(year, errors="ignore")

    st.subheader(f"{sigun} {year}년 생육기 진단  ·  5월 1일 ~ {end_day.month}월 {end_day.day}일")
    st.caption(f"평년 = 같은 기간의 {year_span(others.index)} 평균 · "
               f"평균 ± 1표준편차를 벗어나면 많음/적음으로 판정")

    cols = st.columns(len(CARD_KEYS))
    for c, k in zip(cols, CARD_KEYS):
        spec = IND[k]
        with c:
            v = cur.get(k)
            if v is None:
                st.metric(spec["name"], "기간 전")
                st.caption(ind_sub(k, th))
                continue
            o = others[k].dropna().tolist()
            label, icon = judge(v, o, spec["high_bad"])
            m = np.mean(o) if o else np.nan
            st.metric(spec["name"], f"{v}일", delta=f"{v - m:+.1f}일",
                      delta_color="inverse" if spec["high_bad"] else "normal")
            st.markdown(f"{icon} **{label}** · 평년 {m:.1f}일")
            extra = f" · 최장 무강수 {cur['무강수']}일" if k == "건조" and cur.get("무강수") is not None else ""
            st.caption(ind_sub(k, th) + extra)

    st.caption("병해충 **다발 위험 판정**(작황조사 전 7월 31일까지의 고정 기준)은 '오늘의 진단'과 "
               "'병해충 발생 위험·평년' 탭에서 봅니다. 위 카드는 시즌 전체 위험을 평년과 비교하는 진단용입니다.")

    # ── 착과 전 고온 영향 (이 연구의 주 결과) ──
    v_pre = cur.get("착과전고온")
    o_pre = others["착과전고온"].dropna().tolist()
    pre_at_base = abs(th["hot_pre"] - HEAT_PRE["임계"]) < 1e-9
    if v_pre is not None and o_pre and not pre_at_base:
        st.info(f"**착과 전 고온 감수 범위**는 기본 기준 {HEAT_PRE['임계']:g}℃(포장 34℃ 상당)에서만 계산합니다. "
                f"근거 계수가 그 기준의 일수에 맞춘 값이라 {th['hot_pre']:g}℃ 일수에 곱하면 맞지 않아요. "
                "지금 화면의 일수는 위험 신호로만 보세요.")
    if v_pre is not None and o_pre and pre_at_base:
        m_pre = float(np.mean(o_pre))
        d_pre = v_pre - m_pre
        if d_pre >= 1:
            lo, hi = loss_range(d_pre)
            st.warning(f"**착과 전 고온 참고 영향** — {year}년 {v_pre}일은 평년 {m_pre:.1f}일보다 {d_pre:+.1f}일입니다. "
                       f"늘어난 고온일만큼 수량이 약 **{lo:.1f}~{hi:.1f}%** 줄어드는 범위입니다"
                       f"(하한: 시군 단수 1일당 약 {LOSS_LOW_PER_DAY}%, 상한: 포장 센서 총수확량 1일당 "
                       f"{abs(HEAT_PRE['센서총량']):.1f}% — 관측소 {PEST_TH['hot_pre']:g}℃는 포장 34℃ 상당). "
                       "저지대 포장일수록 상한 쪽에 가깝다고 보세요.")
        else:
            st.success(f"**착과 전 고온 참고 영향** — {year}년 {v_pre}일은 평년 {m_pre:.1f}일보다 {d_pre:+.1f}일로, "
                       "평년보다 많지 않습니다.")

    with st.expander("🌡️ 착과 전 고온이 왜 중요한가 — 그리고 이 숫자를 믿을 때 주의할 점"):
        st.markdown(f"""
**왜 착과 전 {HEAT_PRE['창']}인가**

고추재배전서 197쪽: "수정 능력이 없는 화분은 개화 전 13~17일의 평균기온과 밀접한 관계가 있으며
30℃ 이상에서는 50% 이상의 높은 비율의 이상 화분을 나타낸다". 주 착과기 7/20~8/10의 13~17일 전이
**{HEAT_PRE['창']}**입니다.

**확인된 것**

| 자료 | 종속변수 | 1일당 효과 | p |
|---|---|---|---|
| 시군 패널 (6개 시군 2016~2024, n=53) | 단수 | {HEAT_PRE['시군계수']:.2f} kg/10a | {HEAT_PRE['시군p']} |
| 농가 패널 + 포장 센서 ({HEAT_PRE['센서표본']}), 34℃ | 주당 수확과수 | {HEAT_PRE['센서과수']:.1f}% | {HEAT_PRE['센서과수p']} |
| 34℃ | 주당 총수확량 | {HEAT_PRE['센서총량']:.1f}% | {HEAT_PRE['센서총량p']} (경계 수준) |
| 33℃ | 주당 수확과수 | {HEAT_PRE['센서과수33']:.1f}% | {HEAT_PRE['센서과수33p']} |
| 33℃ | 주당 총수확량 | {HEAT_PRE['센서총량33']:.1f}% | {HEAT_PRE['센서총량33p']} |

시군 패널은 기준 온도를 31~37℃로 바꿔도
계수가 모두 음(-)이었고 33℃ 이상에서 유의했습니다(31℃ 경계 수준 p=0.066, 32℃ p=0.105).

평균 과중은 34℃에서 변화가 없었고({HEAT_PRE['센서과중']:+.1f}%, p={HEAT_PRE['센서과중p']}), 33℃에서도
유의하지 않았습니다({HEAT_PRE['센서과중33']:+.1f}%, p={HEAT_PRE['센서과중33p']}). 고온은 **과실 수를 줄이는 방식으로**
수량을 깎습니다. 고온일 1일당 8월 말 분지수가 {HEAT_PRE['분지수']:.2f}개 줄었고(p={HEAT_PRE['분지수p']}),
분지수·초장을 통제하면 수확과수 감소가 {HEAT_PRE['생육통제']:.1f}%(p={HEAT_PRE['생육통제p']})로 줄어
**피해의 상당 부분이 생육 감소와 함께** 나타납니다. 고온은 위성 식생지수(잎의 양)를 바꾸지 않아,
잎을 보고는 피해를 알 수 없습니다.

**왜 하필 7월 3일~28일인가** — 기간의 시작일과 길이를 바꿔 가며 같은 모형을 다시 적합해 봤습니다(시군·농가
자료 모두). 고온일과 수량의 음(-)의 관계는 **7월 초에 시작하는 기간에서만** 나타났고, 6월 기간과 8월 하순
이후 기간에서는 나타나지 않았습니다. 고온일이 가장 많은 7월 하순~8월 중순 기간에서도 관계가 없어, 고온일의
수보다 **시기가 중요합니다.** 경계를 며칠 옮겨도 결과가 비슷해서, 7/3~7/28은 '분석에 쓴 기간'이지 생물학적으로
정확한 경계는 아닙니다. 기준 온도도 30~37℃로 바꿔 가며 적합하면 33~34℃에서 가장 잘 맞지만, 재표집 95%
구간이 30.5~36.5℃로 넓어 0.5℃ 단위로 특정하지는 않습니다.

**이 앱의 숫자를 읽을 때 주의할 점 — 관측소는 포장보다 시원하다**

| 비교 | 차이 |
|---|---|
| 포장 센서 - 시군 관측소 착과 전 평균최고기온 | **+{HEAT_PRE['센서기온차']:.2f}℃** |
| 포장 센서 - 시군 관측소 34℃ 이상 일수 | **+{HEAT_PRE['센서일수차']:.1f}일** |
| 같은 해 농가 간 편차의 센서-관측소 상관 | 0.56 |

**포장 해발도 고온 노출을 바꿉니다.** 조사포장(117~431m) 센서로 보면 해발 100m 높을수록 착과 전 평균최고기온이
{HEAT_PRE['해발기온']:.2f}℃, 34℃ 이상 일수가 {HEAT_PRE['해발일수']:.1f}일 적었습니다. 고온 1일당 피해 크기가 해발에 따라
다른지는 확인되지 않았습니다. **저지대 포장일수록 착과기 고온 대응이 더 필요합니다.**

→ 그래서 이 앱은 관측소 자료로 셀 때 **33℃ 이상 일수**를 씁니다. 2021~2025년에 포장 센서 34℃ 이상 일수와
관측소 33℃ 이상 일수는 평균이 같았습니다(각 6.5일). 포장 온도계로 직접 센 일수가 있으면 '오늘의 진단' 탭의
**내 포장 온도계로 보기**에 넣으세요(그쪽은 포장 기준 34℃).

**여름 전체가 더웠는지보다, 더운 날이 착과 전 창(7/3~7/28)에 들었는지가 중요합니다.**
예를 들어 2024년은 시즌 전체 폭염일수(5~9월, 33℃ 이상)가 시군에 따라 34~61일로 2018년(27~46일)보다
많았지만, 착과 전 창 안의 33℃ 고온일은 0~10일로 2018년(14~19일)보다 훨씬 적었습니다.
그래서 "더 더웠던" 2024년보다 2018년 쪽이 착과 피해가 큰 해였습니다.
""")

    st.divider()
    var = st.radio("평년과 비교할 항목", SERIES_OPTS, horizontal=True, key="var")
    d = daily_series(df_s, var, th)
    show_chart(season_chart(d, year, end_md, var))

    names = {IND[k]["name"]: k for k in CARD_KEYS + ["폭염"]}
    pick = st.selectbox("연도별 비교 지표", list(names.keys()), key="pick")
    key = names[pick]
    show_chart(year_bar(tbl, key, year, f"{pick} (일)"))

    # ── 일사량 × 강수량 보완관계 ──
    with st.expander("☀️💧 일사량은 비가 와야 수량으로 간다", expanded=False):
        sr = season_solar_rain(wx)
        key_sg = data_sigun
        st.markdown(f"""
생육기 일사량과 강수량의 교호항이 유의한 양(+)입니다
(+{SOLAR_RAIN['교호계수']:.4f}, 시군·연도 고정효과, 시군 클러스터 p=0.0008).

아래 일사량·강수량은 회귀 분석에 쓴 것과 같은 창(**4월 1일~10월 31일**)으로 계산했습니다.
화면 위쪽 위험 지표의 생육기(5~9월)와는 창이 다릅니다.
""")
        rain_grid = np.linspace(600, 1300, 60)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=rain_grid, y=[marginal_solar(r) for r in rain_grid],
                                 mode="lines", line=dict(color=C_THIS, width=3),
                                 name="일사량 1 MJ당 단수 효과",
                                 hovertemplate="강수 %{x:.0f}mm → %{y:+.1f} kg/10a<extra></extra>"))
        qx = [q[0] for q in SOLAR_RAIN["분위"]]
        fig.add_trace(go.Scatter(x=qx, y=[q[1] for q in SOLAR_RAIN["분위"]], mode="markers",
                                 marker=dict(size=11, color=C_THIS, line=dict(width=2, color="white")),
                                 error_y=dict(type="data", symmetric=False,
                                              array=[q[3] - q[1] for q in SOLAR_RAIN["분위"]],
                                              arrayminus=[q[1] - q[2] for q in SOLAR_RAIN["분위"]],
                                              color="rgba(42,120,214,0.45)"),
                                 name="보고 지점 (95% 신뢰구간)",
                                 text=[f"p={q[4]}" for q in SOLAR_RAIN["분위"]],
                                 hovertemplate="강수 %{x:.0f}mm → %{y:+.1f} (%{text})<extra></extra>"))
        fig.add_hline(y=0, line_color=C_ALERT, line_dash="dot")
        if (key_sg, year) in sr.index:
            r_now = float(sr.loc[(key_sg, year), "강수량"])
            fig.add_vline(x=r_now, line_color=C_MEAN, line_dash="dash")
        base_layout(fig, 360, "일사량 1 MJ 증가당 단수 (kg/10a)", top=30)
        fig.update_xaxes(title="생육기(4~10월) 강수량 (mm)", showgrid=True,
                         gridcolor="rgba(128,128,128,0.18)")
        fig.update_layout(legend=dict(orientation="h", y=1.14, x=0))
        show_chart(fig)

        if (key_sg, year) in sr.index:
            r_now = float(sr.loc[(key_sg, year), "강수량"])
            s_now = float(sr.loc[(key_sg, year), "일사량"])
            st.markdown(f"**{sigun} {year}년** 생육기(4~10월) 강수량 {r_now:,.0f}mm, "
                        f"평균 일사량 {s_now:.2f} MJ/m²/일 "
                        f"(회색 세로 점선) → 이 강수 조건에서 일사량 1 MJ 증가의 효과는 "
                        f"**{marginal_solar(r_now):+.1f} kg/10a**입니다.")
        else:
            st.caption(f"{year}년은 4~10월 자료가 아직 다 들어오지 않아 이 그림에 표시하지 않았습니다. "
                       "시즌이 끝나면 자동으로 나타납니다.")
        st.caption("강수량 762mm(하위 25%)에서는 일사량 효과가 10% 수준에서만 유의하고(p=0.068) "
                   "5% 기준으로는 0과 구분되지 않습니다. "
                   "1041mm(상위 25%)에서는 +29.2(p=0.007)로 커집니다. 광합성에 광량과 수분이 함께 "
                   "요구되는 보완관계로 해석합니다. 같은 관계가 ASOS 10개 시군 패널(n=130)에서 "
                   "일조시간 × 강수량 교호항으로도 재현됩니다(p=0.005). "
                   "현장 메시지는 **비가 적은 해에는 햇빛이 많아도 수량으로 가지 않는다**입니다.")
        if len(sr):
            st.markdown("**시군 × 연도 생육기(4~10월) 일사량·강수량**")
            show_table(sr.round({"일사량": 2, "강수량": 0}))
            st.caption("회귀 분석 패널은 2016~2024년에서 청송 2017년을 뺀 53개 사례입니다. "
                       "이 표에는 그 뒤 들어온 연도까지 들어 있습니다.")

    # ── 작황조사로 검증 ──
    with st.expander("✅ 이 지표들이 실제 작황과 맞을까? — 작황조사로 검증", expanded=False):
        if hpath_all is None:
            st.info("하반기 작황조사 파일이 있으면 검증 결과가 나와요.")
        else:
            hv = load_survey(hpath_all)
            rates = survey_rates(hv)
            skip = ("예천군",) if yecheon_substitute else ()
            stab = season_table(wx, th, skip, VALID_END)
            joined = stab.join(rates, how="inner")
            if joined.empty:
                st.info("기상자료와 작황조사가 겹치는 시군·연도가 없어요.")
            else:
                st.caption(f"시군 × 연도 {len(joined)}개 사례(작황조사 {int(joined.index.get_level_values(1).min())}~"
                           f"{int(joined.index.get_level_values(1).max())}년). 시군마다 원래 발생 수준이 달라서 "
                           "시군 평균을 뺀 뒤의 상관을 봤어요(+1에 가까울수록 같이 움직임, −1이면 반대로 움직임).")
                st.caption("하반기 작황조사는 7월 말~8월 초에 한 번 합니다. 그래서 검증은 **조사 전(7월 31일까지) 날씨**로만 "
                           "합니다. 시즌 전체(9월까지)로 계산하면 상관이 더 높게 나오지만(탄저 0.64, 담배나방 0.54, "
                           "석회결핍 -0.51), 조사 뒤의 날씨가 섞여 '그런 해는 계속 그렇다'가 들어간 값입니다. "
                           "위쪽 카드는 시즌 전체 위험을 보여주는 진단용이라 원래 창을 그대로 씁니다.")
                rows = []
                for k, _, oname in VALID_PAIRS:
                    if oname not in joined.columns:
                        continue
                    r, slope, n = within_fit(joined[k], joined[oname], joined.index.get_level_values(0))
                    rows.append({"기상 지표": IND[k]["name"], "검증 창 (조사 전)": valid_window(k),
                                 "작황조사 결과": oname,
                                 "상관계수": round(r, 2) if not np.isnan(r) else None, "사례 수": n})
                show_table(pd.DataFrame(rows), hide_index=True)

                st.markdown("**조사 전 날씨 구간별 실제 발생 포장 비율** (사례 전체 평균)")
                bcols = st.columns(len(VALID_PAIRS))
                cur_v = indicators(df_s[df_s["연도"] == year], VALID_END, th) \
                    if df_s[df_s["연도"] == year]["월일"].max() >= VALID_END else None
                for bc, (k, _, oname) in zip(bcols, VALID_PAIRS):
                    if oname not in joined.columns:
                        continue
                    with bc:
                        st.markdown(f"{IND[k]['name']} ({valid_window(k)})")
                        bt = bin_table(joined, k, oname)
                        show_table(bt.rename(columns={"평균 발생 포장 비율": oname.replace(" 발생 포장 비율", " 발생")}),
                                   hide_index=True)
                        if cur_v is not None and cur_v.get(k) is not None:
                            v = cur_v[k]
                            band = [bin_label(lo, hi) for lo, hi in VALID_BINS[k] if lo <= v <= hi]
                            st.caption(f"{sigun} {year}년: {v}일 → **{band[0] if band else '-'}** 구간")
                st.caption("탄저병은 2023년 영향이 큽니다. 연도를 하나씩 빼고 보면 상관이 0.43(2023년 제외)~0.65입니다. "
                           "20일 이상 구간은 사례가 적어(주로 2020·2023년) 그 이상으로 나눌 수 없습니다. "
                           "탄저병은 2023년 일부(봉화·예천 전체, 안동·영양 일부)와 2024년 전체가 3주 조사입니다. "
                           "3주 조사 포장을 빼도 구간별 발생 포장 비율 6.7 / 13.9 / 25.5%, 시군 내 상관 0.61로 결론이 같았습니다.")

                vp = st.selectbox("산점도로 볼 지표", [f"{IND[k]['name']} ↔ {o}" for k, _, o in VALID_PAIRS
                                                   if o in joined.columns], key="vpick")
                k = [kk for kk, _, o in VALID_PAIRS if vp.endswith(o)][0]
                oname = vp.split(" ↔ ")[1]
                fig = go.Figure()
                for sg in [s for s in SIGUN_ORDER if s in joined.index.get_level_values(0)]:
                    g = joined.loc[sg]
                    fig.add_trace(go.Scatter(x=g[k], y=g[oname], mode="markers", name=sg,
                                             marker=dict(size=10, color=SIGUN_COLOR.get(sg),
                                                         line=dict(width=1.5, color="white")),
                                             text=[str(y) for y in g.index],
                                             hovertemplate=f"{sg} " + "%{text}년<br>지표 %{x}일 · 발생 %{y:.0f}%<extra></extra>"))
                base_layout(fig, 360, f"{oname} (%)")
                fig.update_xaxes(title=f"{IND[k]['name']}, {valid_window(k)} (일)", showgrid=True,
                                 gridcolor="rgba(128,128,128,0.18)")
                fig.update_layout(legend=dict(orientation="h", y=1.1, x=0))
                show_chart(fig)
                st.caption("주의: 같은 해에는 모든 시군의 날씨가 비슷하게 움직여서, 실제로 독립적인 정보는 "
                           "연도 수(약 9년)에 가깝습니다. 인과관계가 아니라 '같이 움직이는 경향'으로 읽어야 해요. "
                           "탄저병 지표는 원래 '최고 29℃ 이상 + 비'로 만들었다가, 이 검증에서 상관이 0.2 수준에 "
                           "그쳐 '비 온 날 수'로 바꿨습니다.")

    with st.expander("🍂 수확은 언제쯤 끝날까 — 가을 기온 기준 (참고)"):
        he_rows = []
        for y, g in df_s.groupby("연도"):
            d_end = harvest_end_day(g, HARVEST_END["임계"])
            if d_end is not None:
                he_rows.append({"연도": int(y), "날짜": d_end, "doy": d_end.timetuple().tm_yday})
            elif g["월일"].max() >= "11-30":
                he_rows.append({"연도": int(y), "날짜": None, "doy": np.nan})
        he = pd.DataFrame(he_rows)
        cur_end = harvest_end_day(df_s[df_s["연도"] == year], HARVEST_END["임계"])
        if he.empty:
            st.info("가을 기온 자료가 없어요.")
        else:
            base_doy = he[he["연도"] != year]["doy"].dropna()
            mdoy = int(round(base_doy.mean())) if len(base_doy) else None
            mdate = (date(2001, 1, 1) + pd.Timedelta(days=mdoy - 1)).strftime("%m월 %d일") if mdoy else "-"
            if cur_end is not None:
                diff = cur_end.timetuple().tm_yday - mdoy if mdoy else 0
                st.markdown(f"**{sigun} {year}년 수확 종료 기준일(일평균 {HARVEST_END['임계']:g}℃ 이하 첫날): "
                            f"{cur_end.month}월 {cur_end.day}일** "
                            f"(평년 {mdate}, {diff:+d}일)")
            else:
                st.markdown(f"**{sigun} {year}년은 아직 일평균기온 {HARVEST_END['임계']:g}℃ 이하인 날이 없었습니다** "
                            f"(평년 {mdate}).")
            st.caption(f"국립원예특작과학원 재배작기 영농정보의 수확 종료 기준(일평균기온 {HARVEST_END['임계']:g}℃ 이하인 "
                       f"첫날)을 이 지역에 맞춰본 결과, 농가 실제 끝수확일과 해마다 같이 움직였습니다"
                       f"(r={HARVEST_END['r']}, {HARVEST_END['n']}건, 2018~2025). 농가는 이 날보다 평균 "
                       f"{HARVEST_END['차이']}일쯤 먼저 수확을 끝냈습니다. 같은 자료의 정식 기준(평균기온 13℃)은 "
                       "실제 정식일과 맞지 않았습니다(농가는 기온보다 관행 날짜에 맞춰 심음).")
            hh = he.dropna(subset=["doy"])
            if len(hh):
                fig = go.Figure(go.Bar(x=[str(y) for y in hh["연도"]], y=hh["doy"],
                                       marker_color=[C_THIS if y == year else C_OTHER for y in hh["연도"]],
                                       text=[d.strftime("%m/%d") for d in hh["날짜"]],
                                       hovertemplate="%{x}년 %{text}<extra></extra>"))
                base_layout(fig, 240, "수확 종료 기준일")
                ticks = list(range(int(hh["doy"].min()) - 3, int(hh["doy"].max()) + 4, 7))
                fig.update_yaxes(range=[hh["doy"].min() - 5, hh["doy"].max() + 5], tickvals=ticks,
                                 ticktext=[(date(2001, 1, 1) + pd.Timedelta(days=t - 1)).strftime("%m/%d")
                                           for t in ticks])
                fig.update_layout(bargap=0.35)
                fig.update_xaxes(type="category")
                show_chart(fig)

    with st.expander("판정 기준과 근거"):
        st.markdown(f"""
| 지표 | 기간 | 기준 (현재 설정) | 근거 |
|---|---|---|---|
| 착과 전 고온일 | 7월 3일 ~ 28일 | 최고기온 {th['hot_pre']:g}℃ 이상 | 개화 13~17일 전 화분 형성기 고온이 이상 화분을 만듦 (고추재배전서 197쪽). **이 연구에서 직접 추정**: 시군 단수 1일당 {HEAT_PRE['시군계수']:.2f} kg/10a (p{HEAT_PRE['시군p'] if HEAT_PRE['시군p'].startswith('<') else '=' + HEAT_PRE['시군p']}), 농가 센서 주당 수확과수 {HEAT_PRE['센서과수']:.1f}%/일 (p={HEAT_PRE['센서과수p']}). 기본 33℃는 포장 센서 34℃ 상당(2021~2025 평균 일수 일치) |
| 탄저병 위험: 비 온 날 | 6월 15일 ~ 9월 30일 | 강수 {th['rain_wet']:g}mm 이상인 날{(' + 최고 ' + format(th['tan_tmax'], 'g') + '℃ 이상') if th['tan_use_tmax'] else ''} | 6월 하순 장마와 함께 발병, 포자가 빗방울·비바람으로 전염 (고추재배전서 241~243쪽). 작황조사 탄저병 발생 포장 비율과 가장 잘 맞는 지표 |
| 고온일 | 6월 ~ 8월 | 최고기온 {th['hot']:g}℃ 이상 | 30℃ 이상에서 화분 이상으로 착과 불량·단위결과·낙과 (고추재배전서 197쪽). 작황조사에서 담배나방 발생 포장 비율과 같이 움직임 |
| 폭염일 | 6월 ~ 8월 | 최고기온 {th['heat']:g}℃ 이상 | 고온·건조가 겹치면 석회결핍·소과·일소과 증가 (고추재배전서 197~198쪽). **단수와의 관계는 계절 총량으로는 확인되지 않음**(p=0.156) |
| 저온일 | 6월 ~ 8월 | 최저기온 {th['cold']:g}℃ 이하 | 야온 13℃에서 단위결과 78~100%, 18℃ 이상에서 정상 착과 (고추재배전서 201~202쪽, 표 7-10) |
| 가뭄: 비다운 비 온 날 | 5월 ~ 8월 | 강수 {th['rain_good']:g}mm 이상인 날 (적을수록 가뭄) | 단수 7일에도 수확과수 10~18% 감소 (고추재배전서 193쪽, 표 7-3). 작황조사에서 비다운 비가 적은 해에 석회결핍 발생 포장이 많음 |

- 근거 문헌: 경상북도농업기술원 영양고추연구소, 「고추재배전서」 개정증보판
- 착과 전 고온일을 뺀 나머지는 **기상 조건상의 위험 신호**이며, 실제 발병·수량을 예측하는 값은 아닙니다.
- 생육기 전체 고온일(33℃)은 1일당 수확과수 -1.3%, 착과 전 창은 -3.1%로 **하루당 피해가 약 2.3배**입니다
  (둘 다 p 0.07 내외, 경계 수준). 계절 총량에는 피해와 무관한 고온일이 섞여 효과가 희석됩니다.
- 병해충 다발 위험 판정은 이 표의 카드 창(시즌 전체)이 아니라 **작황조사 전(7월 31일까지)** 고정 기준으로 합니다.
""")

    with st.expander("연도별 지표 표 보기"):
        show = tbl.rename(columns={k: IND[k]["name"] for k in IND} | {"무강수": "최장 무강수(일)"})
        show_table(show)
        st.download_button("CSV로 내려받기", show.to_csv(encoding="utf-8-sig"),
                           file_name=f"기상위험지표_{sigun}_{end_md}.csv", mime="text/csv")

# ══════════════════════════════════════════════
# 탭: 기상 시나리오
# ══════════════════════════════════════════════
SC_KEYS = ["착과전고온", "탄저", "고온", "폭염", "저온", "건조"]


def strip_chart(base_vals, scen_vals, actual=None, cur_val=None):
    """한 줄짜리 그림: 회색 띠 = 평년 범위, 점선 = 평년 평균, 파란 점 = 시나리오, 빨간 마름모 = 실제"""
    fig = go.Figure()
    if len(base_vals):
        lo, hi, m = min(base_vals), max(base_vals), float(np.mean(base_vals))
        fig.add_shape(type="rect", x0=lo, x1=hi, y0=-0.5, y1=0.5, fillcolor=C_BAND, line_width=0)
        fig.add_vline(x=m, line_dash="dot", line_color=C_MEAN)
    fig.add_trace(go.Scatter(x=list(scen_vals.values), y=[0] * len(scen_vals), mode="markers",
                             marker=dict(size=11, color=C_THIS, opacity=0.75, line=dict(width=1.5, color="white")),
                             text=[f"{y}년 날씨" for y in scen_vals.index],
                             hovertemplate="%{text}로 이어지면 %{x}일<extra></extra>", showlegend=False))
    if actual is not None:
        fig.add_trace(go.Scatter(x=[actual], y=[0], mode="markers",
                                 marker=dict(size=14, symbol="diamond", color=C_ALERT,
                                             line=dict(width=1.5, color="white")),
                                 hovertemplate="실제 결과 %{x}일<extra></extra>", showlegend=False))
    fig.update_layout(height=90, margin=dict(l=10, r=10, t=6, b=24),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    fig.update_yaxes(visible=False, range=[-0.8, 0.8])
    fig.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.18)", zeroline=False)
    return fig


with tab_sc:
    st.subheader("기상 시나리오")
    sc_part = st.radio("보기", ["① 올해 남은 기간 시나리오", "② 극한 기온 시나리오",
                              "③ 미래 기후 (기상청 SSP 시나리오)"],
                       horizontal=True, key="sc_part")

    base_tbl = all_years(df_s, "09-30", th)   # 시군의 해마다 생육기 전체 지표

    # ── ① 남은 기간 시나리오 ──
    if sc_part.startswith("①"):
        st.caption("기준일까지는 실제 관측값을 쓰고, 그 뒤는 과거 각 해의 날씨가 그대로 이어진다고 가정해 "
                   "시나리오를 만듭니다. 날짜별 날씨를 맞히는 예보가 아니라, **과거에 실제로 있었던 날씨 범위 안에서 "
                   "올해가 어디까지 갈 수 있나**를 보는 것입니다.")
        last_obs = df_s[df_s["연도"] == year]["일시"].max().date()
        cut_max = min(date(year, 9, 29), last_obs)
        cut_default = min(date(year, 7, 31), cut_max)
        c1, c2, c3 = st.columns(3)
        cut = c1.date_input("기준일 (이 날까지는 실측)", value=cut_default,
                            min_value=date(year, 5, 1), max_value=cut_max, key=f"sc_cut_{sigun}_{year}")
        dT_r = c2.select_slider("남은 기간 기온 가정", options=[-2.0, -1.0, 0.0, 1.0, 2.0, 3.0], value=0.0,
                                format_func=lambda v: "과거 그대로" if v == 0 else f"{v:+.0f}℃", key="sc_dT")
        rm_r = c3.select_slider("남은 기간 강수 가정", options=[0.5, 0.75, 1.0, 1.25, 1.5], value=1.0,
                                format_func=lambda v: "과거 그대로" if v == 1 else f"×{v}", key="sc_rm")
        cut_md = cut.strftime("%m-%d")
        sc = remaining_scenarios(df_s, year, cut_md, dT_r, rm_r, th)
        if sc.empty:
            st.info("시나리오를 만들 과거 자료가 없어요.")
        else:
            base = base_tbl.drop(year, errors="ignore")
            year_complete = df_s[df_s["연도"] == year]["월일"].max() >= "09-30"
            so_far = indicators(df_s[(df_s["연도"] == year)], cut_md, th)
            st.markdown(f"**{sigun} {year}년 · {cut.month}월 {cut.day}일까지 실측 + 이후 {len(sc)}개 시나리오**")
            st.caption("회색 띠: 평년 범위 · 점선: 평년 평균 · 파란 점: 시나리오(점에 마우스를 올리면 어느 해 날씨인지 나와요)"
                       + (" · 빨간 마름모: 실제 결과" if year_complete else ""))
            if cut.month * 100 + cut.day >= 728:
                st.caption("착과 전 고온일(7/3~7/28)은 기준일이 7월 28일을 넘으면 이미 확정된 값이라 "
                           "시나리오 사이에 차이가 없습니다.")
            for k in SC_KEYS:
                spec = IND[k]
                vals = sc[k].dropna()
                bvals = base[k].dropna().tolist()
                if not len(bvals) or not len(vals):
                    continue
                bm, bsd = np.mean(bvals), np.std(bvals, ddof=1)
                if spec["high_bad"]:
                    n_bad = int((vals > bm + bsd).sum())
                    bad_txt = "평년보다 많아지는"
                else:
                    n_bad = int((vals < bm - bsd).sum())
                    bad_txt = "평년보다 적어지는"
                lc, rc = st.columns([1.3, 3])
                with lc:
                    st.markdown(f"**{spec['name']}**")
                    st.caption(ind_sub(k, th))
                    sf = so_far.get(k)
                    st.markdown(f"지금까지 {sf if sf is not None else 0}일 → 시즌 끝 **{int(vals.min())}~{int(vals.max())}일** "
                                f"(중앙값 {vals.median():.0f}일)")
                    icon = "🔴" if n_bad >= len(vals) / 2 else ("🟡" if n_bad > 0 else "🟢")
                    st.markdown(f"{icon} {bad_txt} 시나리오 **{n_bad}/{len(vals)}**")
                with rc:
                    act = base_tbl.loc[year, k] if (year_complete and year in base_tbl.index) else None
                    show_chart(strip_chart(bvals, vals, act))
            if year_complete:
                st.info(f"{year}년은 이미 끝난 해라서 실제 결과(빨간 마름모)와 비교해볼 수 있어요. "
                        "올해 자료가 들어오면 같은 화면이 시즌 중 전망으로 쓰입니다.")

    # ── ② 극한 기온 시나리오 ──
    elif sc_part.startswith("②"):
        st.caption("과거 각 해(" + year_span(base_tbl.index) + ")의 날씨에 기온을 일정하게 더하거나 빼고 강수량을 "
                   "배율로 바꿔서, 생육기 위험 지표가 어떻게 달라지는지 봅니다. 기후변화 영향 평가에서 쓰는 "
                   "'델타 방법'과 같은 방식입니다. 특정 해를 예측하는 것이 아니라 **이만큼 더워지면(추워지면) "
                   "이 정도 달라진다**는 민감도입니다.")
        c1, c2 = st.columns(2)
        dT = c1.slider("기온 변화 (℃)", min_value=-3.0, max_value=4.0, value=2.0, step=0.5, key="cl_dT",
                       format="%+.1f℃",
                       help="평균·최고·최저기온에 모두 같은 값을 더합니다")
        rmul = c2.slider("강수량 배율", min_value=0.5, max_value=1.5, value=1.0, step=0.1, key="cl_rm",
                         format="×%.1f",
                         help="1.0 = 과거 그대로, 0.7 = 30% 감소")
        dTs = tuple(np.round(np.arange(-3.0, 4.01, 0.5), 1))
        cs = climate_scenarios(df_s, th, dTs, rmul)
        cs0 = climate_scenarios(df_s, th, (0.0,), 1.0)
        now = cs0.set_index("연도")
        scen = cs[np.isclose(cs["dT"], dT)].set_index("연도")
        n_y = len(now)

        label = ("기온 " + (f"{dT:+.1f}℃" if dT else "그대로") + " · 강수 " +
                 ("그대로" if rmul == 1 else f"×{rmul:.1f}"))
        st.markdown(f"**{sigun} · {label} 가정 시 생육기 지표 (과거 {n_y}개년 평균)**")
        mcols = st.columns(len(SC_KEYS))
        for c, k in zip(mcols, SC_KEYS):
            spec = IND[k]
            b, s = now[k].mean(), scen[k].mean()
            if spec["high_bad"]:
                worst_y = now[k].idxmax()
                worse = int((scen[k] > now[k].max()).sum())
            else:
                worst_y = now[k].idxmin()
                worse = int((scen[k] < now[k].min()).sum())
            with c:
                if abs(s - b) < 0.05:
                    st.metric(spec["name"], f"{s:.1f}일", delta="변화 없음", delta_color="off")
                else:
                    st.metric(spec["name"], f"{s:.1f}일", delta=f"{s - b:+.1f}일",
                              delta_color="inverse" if spec["high_bad"] else "normal")
                    st.caption(f"지금 {b:.1f}일")
                st.caption(ind_sub(k, th))
                st.caption(f"과거 가장 심했던 {worst_y}년({int(now.loc[worst_y, k])}일)보다 심한 해: "
                           f"**{worse}/{n_y}**")

        # 착과 전 고온일 변화 → 단수 참고 영향 (계수가 기본 기준의 일수에 맞춘 값이라 그때만 계산)
        d_pre = scen["착과전고온"].mean() - now["착과전고온"].mean()
        if abs(d_pre) >= 0.05 and abs(th["hot_pre"] - HEAT_PRE["임계"]) >= 1e-9:
            st.info(f"착과 전 고온일이 평균 {d_pre:+.1f}일 달라집니다. kg/10a 참고 영향은 기준 "
                    f"{HEAT_PRE['임계']:g}℃에서만 계산합니다(사이드바 기준 {th['hot_pre']:g}℃).")
        elif d_pre >= 0.5:
            lo, hi = loss_range(d_pre)
            st.warning(f"**착과 전 고온 참고 영향** — 이 가정에서 착과 전 고온일이 평균 {d_pre:+.1f}일 늘어납니다. "
                       f"수량으로는 약 **{lo:.1f}~{hi:.1f}% 감소** 범위입니다(1일당 하한 {LOSS_LOW_PER_DAY}%, "
                       f"상한 {abs(HEAT_PRE['센서총량']):.1f}%). 관측된 범위 밖으로 외삽한 값이라 방향과 규모만 참고하세요.")
        elif d_pre <= -0.5:
            st.success(f"이 가정에서 착과 전 고온일이 평균 {d_pre:+.1f}일 줄어듭니다.")

        # 민감도 그래프
        st.markdown("**기온 변화에 따른 지표 변화** (과거 각 해 평균)")
        sens = cs.groupby("dT")[["착과전고온", "고온", "폭염", "저온"]].mean()
        fig = go.Figure()
        for k, colr in [("착과전고온", "#8a3ffc"), ("고온", "#eb6834"),
                        ("폭염", "#e34948"), ("저온", "#2a78d6")]:
            fig.add_trace(go.Scatter(x=sens.index, y=sens[k], mode="lines+markers", name=IND[k]["name"],
                                     line=dict(color=colr, width=2.5), marker=dict(size=7),
                                     hovertemplate=f"{IND[k]['name']} " + "기온 %{x:+.1f}℃ → %{y:.1f}일<extra></extra>"))
        fig.add_vline(x=dT, line_dash="dot", line_color=C_MEAN)
        base_layout(fig, 340, "일수 (일)")
        fig.update_xaxes(title="기온 변화 (℃)", dtick=1, ticksuffix="℃", showgrid=True,
                         gridcolor="rgba(128,128,128,0.18)")
        fig.update_layout(legend=dict(orientation="h", y=1.1, x=0), hovermode="x unified")
        show_chart(fig)
        if len(sens) > 2 and 0.0 in sens.index and 1.0 in sens.index:
            st.caption(f"기온이 1℃ 오르면 {sigun}의 착과 전 고온일은 평균 "
                       f"{sens.loc[1.0, '착과전고온'] - sens.loc[0.0, '착과전고온']:+.1f}일, "
                       f"고온일은 {sens.loc[1.0, '고온'] - sens.loc[0.0, '고온']:+.1f}일, "
                       f"폭염일은 {sens.loc[1.0, '폭염'] - sens.loc[0.0, '폭염']:+.1f}일, "
                       f"저온일은 {sens.loc[1.0, '저온'] - sens.loc[0.0, '저온']:+.1f}일 달라집니다.")

        # 작황조사 관계를 적용한 참고 영향
        hp = find_file(["하반기"], ".xlsx")
        if hp is not None:
            hv = load_survey(hp)
            skip = ("예천군",) if yecheon_substitute else ()
            joined = season_table(wx, th, skip, VALID_END).join(survey_rates(hv), how="inner")
            now_v = climate_scenarios(df_s, th, (0.0,), 1.0, VALID_END).set_index("연도")
            scen_v = climate_scenarios(df_s, th, (float(dT),), rmul, VALID_END).set_index("연도")
            rows = []
            for k, _, oname in VALID_PAIRS:
                if oname not in joined.columns:
                    continue
                r, slope, n = within_fit(joined[k], joined[oname], joined.index.get_level_values(0))
                if np.isnan(r) or abs(r) < 0.3:
                    continue
                b, s = now_v[k].mean(), scen_v[k].mean()
                if abs(s - b) < 0.05:
                    continue   # 이 가정에서는 지표가 변하지 않음
                lo, hi = joined[k].min(), joined[k].max()
                if s < lo or s > hi:
                    eff = "관측된 적 없는 수준이라 생략"
                else:
                    eff = f"{slope * (s - b):+.1f}%p"
                rows.append({"작황조사 결과": oname, "연결된 기상 지표": f"{IND[k]['name']} ({valid_window(k)})",
                             "지표 변화": f"{s - b:+.1f}일", "예상 변화 (참고값)": eff,
                             "근거 상관": round(r, 2)})
            if rows:
                st.markdown("**작황조사에서 확인된 관계를 그대로 적용하면** (참고값)")
                show_table(pd.DataFrame(rows), hide_index=True)
                st.caption("작황조사(시군 × 연도)에서 조사 전(7월 31일까지) 기상 지표와 발생 포장 비율이 같이 움직인 "
                           "기울기를 그대로 곱한 값입니다. 지표 변화도 같은 창으로 셉니다. "
                           "약 9년치 자료에서 나온 관계라 큰 변화일수록 불확실하고, 인과관계를 뜻하지 않습니다. "
                           "탄저병 지표(비 온 날)는 기온만 바꾸면 변하지 않아요.")

    # ── ③ 미래 기후 (기상청 SSP) ──
    else:
        sp = find_file([SSP_FILE_KEY], ".csv")
        ssp = load_ssp(sp) if sp else None
        if ssp is None:
            st.info("app.py 폴더에 이름에 'SSP'가 들어간 기후전망 CSV(SSP_기후전망_6개시군.csv)를 넣으면 이 화면이 열립니다.")
        elif sigun not in set(ssp["시군"]):
            st.info(f"{sigun}은 기후전망 파일에 없어요.")
        else:
            st.caption("기상청 기후정보포털의 **SSP 남한상세 행정구역 자료**(1km 상세화, 5개 모델 평균)를 씁니다. "
                       f"시군·월마다 **{SSP_BASE[0]}~{SSP_BASE[1]}년 대비 미래 10년이 얼마나 변하나**(기온은 ℃ 차이, "
                       "강수는 비율)를 구해, 우리 관측소의 과거 각 해 일자료에 더하고 곱했습니다(월별 델타 방법). "
                       "② 극한 기온 시나리오가 '모든 날 +2℃'라면, 여기는 **달마다 기상청이 전망한 만큼**만 바뀝니다.")
            c1, c2 = st.columns([1.2, 2])
            scen = c1.radio("배출 시나리오", list(SSP_NAMES), format_func=lambda k: SSP_NAMES[k], key="ssp_sc")
            dlabs = [dec_label(d) for d in SSP_DECADES]
            dsel = c2.select_slider("시기 (10년 평균)", options=dlabs, value="2051–2060", key="ssp_dec")
            dec = SSP_DECADES[dlabs.index(dsel)]

            runs = ssp_runs(df_s, th, ssp, sigun)
            now = runs[runs["시나리오"] == "관측"].set_index("연도")
            scn = runs[(runs["시나리오"] == scen) & (runs["시기"] == dsel)].set_index("연도")
            n_y = len(now)
            delta = ssp_delta(ssp, scen, sigun, dec)

            # 월별 변화량
            st.markdown(f"**{sigun} · {scen} · {dsel}년: 기상청 전망 변화량** ({SSP_BASE[0]}~{SSP_BASE[1]}년 대비)")
            dt = delta.loc[5:9]
            show_table(pd.DataFrame({
                "월": [f"{m}월" for m in dt.index],
                "최고기온": [f"{v:+.1f}℃" for v in dt["dTX"]],
                "최저기온": [f"{v:+.1f}℃" for v in dt["dTN"]],
                "평균기온": [f"{v:+.1f}℃" for v in dt["dTA"]],
                "강수량": [f"{(v - 1) * 100:+.0f}%" for v in dt["rRN"]],
                "일사량": [f"{(v - 1) * 100:+.1f}%" for v in dt["rSI"]],
            }), hide_index=True)

            # 지표 카드
            st.markdown(f"**이 변화가 우리 관측 날씨({year_span(now.index)})에 더해지면 생육기 지표는**")
            mcols = st.columns(len(SC_KEYS))
            for c, k in zip(mcols, SC_KEYS):
                spec = IND[k]
                b, s_ = now[k].mean(), scn[k].mean()
                with c:
                    if abs(s_ - b) < 0.05:
                        st.metric(spec["name"], f"{s_:.1f}일", delta="변화 없음", delta_color="off")
                    else:
                        st.metric(spec["name"], f"{s_:.1f}일", delta=f"{s_ - b:+.1f}일",
                                  delta_color="inverse" if spec["high_bad"] else "normal")
                        st.caption(f"지금 {b:.1f}일")
                    st.caption(ind_sub(k, th))

            d_pre = scn["착과전고온"].mean() - now["착과전고온"].mean()
            if abs(d_pre) >= 0.05 and abs(th["hot_pre"] - HEAT_PRE["임계"]) >= 1e-9:
                st.info(f"착과 전 고온일이 평균 {d_pre:+.1f}일 달라집니다. kg/10a 참고 영향은 기준 "
                        f"{HEAT_PRE['임계']:g}℃에서만 계산합니다(사이드바 기준 {th['hot_pre']:g}℃).")
            elif d_pre >= 0.5:
                lo, hi = loss_range(d_pre)
                st.warning(f"**착과 전 고온 참고 영향** — {scen} {dsel}년에는 착과 전 고온일이 평균 {d_pre:+.1f}일 "
                           f"늘어납니다. 수량으로는 약 **{lo:.1f}~{hi:.1f}% 감소** 범위입니다. 품종·재배법·정식 시기가 "
                           "지금과 같다고 본 값이고, 관측된 범위 밖으로 외삽한 것이라 방향과 규모만 참고하세요.")

            # 시기별 흐름
            st.markdown("**시기별 흐름** (관측 각 해에 적용한 평균)")
            kk = st.selectbox("지표", SC_KEYS, format_func=lambda k: IND[k]["name"], key="ssp_k")
            fig = go.Figure()
            for sc in SSP_NAMES:
                t = runs[runs["시나리오"] == sc].groupby("시기")[kk].mean().reindex(dlabs)
                fig.add_trace(go.Scatter(x=dlabs, y=t.values, mode="lines+markers", name=sc,
                                         line=dict(color=SSP_COLOR[sc], width=2.5), marker=dict(size=7),
                                         hovertemplate=sc + " %{x}: %{y:.1f}일<extra></extra>"))
            fig.add_hline(y=now[kk].mean(), line_dash="dot", line_color=C_MEAN,
                          annotation_text=f"지금 {now[kk].mean():.1f}일", annotation_position="top left")
            fig.add_vline(x=dsel, line_dash="dot", line_color="rgba(0,0,0,0.25)")
            base_layout(fig, 320, "일수 (일)")
            fig.update_layout(legend=dict(orientation="h", y=1.1, x=0), hovermode="x unified")
            fig.update_xaxes(type="category")
            fig.update_yaxes(rangemode="tozero")
            show_chart(fig)

            # 기상청 지수와 교차 확인
            with st.expander("🔎 기상청이 직접 계산한 극한기후지수와 맞춰보기"):
                obs33 = now["폭염33"].mean()
                kma = ssp[(ssp["시나리오"] == scen) & (ssp["시군"] == sigun) & (ssp["월"] == 0)].set_index("연도")["HW33"]
                k_b = kma.loc[SSP_BASE[0]:SSP_BASE[1]].mean()
                k_f = kma.loc[dec[0]:dec[1]].mean()
                our_d = scn["폭염33"].mean() - obs33
                st.markdown(f"""
**폭염일(최고 33℃ 이상)로 두 방법 비교** — {sigun}, {scen}

| | 지금 수준 | {dsel}년 변화 |
|---|---|---|
| 우리 관측 + 월별 델타 (6~8월) | {obs33:.1f}일 ({year_span(now.index)}) | {our_d:+.1f}일 |
| 기상청 폭염일수 (1년) | {k_b:.1f}일 ({SSP_BASE[0]}~{SSP_BASE[1]}년) | {k_f - k_b:+.1f}일 |
""")
                st.caption("지금 수준이 비슷하면 시군 평균 자료와 우리 관측소가 잘 맞는다는 뜻입니다. "
                           "기상청 값이 더 크게 늘면, 월 평균 변화만 더하는 델타 방법이 극단 고온의 증가를 덜 잡는다는 뜻입니다. "
                           "기상청 지수는 1년 전체, 우리 값은 6~8월이라 조금 차이가 날 수 있어요.")
                st.markdown(f"**{sigun} 극한기후지수** (괄호 안은 {SSP_BASE[0]}~{SSP_BASE[1]}년 대비 변화)")
                show_table(ssp_index_table(ssp, sigun, dec), hide_index=True)
                si_c, rn_c, rn_b, rn_f = ssp_window_change(ssp, scen, sigun, dec)
                st.caption(f"비 온 날 수는 연 강수량을 강수강도로 나눈 값입니다. 월별 델타 방법은 비의 양만 바꾸고 "
                           f"비 오는 날 수는 거의 못 바꾸므로, 탄저 위험의 변화는 이 줄을 같이 보세요. "
                           f"생육기(4~10월) 기준으로 {scen} {dsel}년에는 일사량 {si_c:+.1f}%, 강수량 {rn_c:+.0f}%"
                           f"(시군 평균 {rn_b:,.0f} → {rn_f:,.0f}mm)입니다. 이 연구에서 일사량의 단수 효과는 "
                           "비가 많은 해일수록 컸습니다(일사량 × 강수 교호항).")

            st.caption("한계 — 5개 모델 평균의 **월 평균 변화만** 반영합니다. 더운 날이 더 더워지는 식의 변동 폭 변화, "
                       "비 오는 날 수의 변화는 들어가지 않습니다. 날씨의 순서와 패턴은 우리 관측 기간의 것을 그대로 씁니다. "
                       "품종·재배법·정식 시기가 지금과 같다고 가정합니다.")

# ══════════════════════════════════════════════
# 탭 2: 내 포장 비교
# ══════════════════════════════════════════════
SURVEY_VARS = {
    "상반기": [  # (화면 이름, 파일 열 이름, 단위, 소수 자리)
        ("초장", "초장(cm)", "cm", 1),
        ("주경장", "주경장(cm)", "cm", 1),
        ("분지수", "분지수(개)", "개", 1),
    ],
    "하반기": [
        ("초장", "초장(cm)", "cm", 1),
        ("주경장", "주경장(cm)", "cm", 1),
        ("분지수", "분지수(개/주)", "개/주", 1),
        ("착과수", "착과수(개/주)", "개/주", 1),
    ],
}
PEST_VARS = [  # 하반기 병해충: (화면 이름, 판정 열)
    ("탄저병", "탄저병(개)"),
    ("담배나방", "담배나방(개)"),
    ("석회결핍", "석회결핍(개)"),
]
SURVEY_DATE = {"상반기": (5, 31), "하반기": (7, 31)}   # 작황조사 시기 (대략)

MEASURE_GUIDE = """
**공통**
- **언제**: 작황조사와 같은 시기에 재야 비교가 됩니다. 상반기는 **5월 말**, 하반기는 **7월 말**.
- **어떤 포기를**: 포장 가장자리 2~3줄과 두둑 양 끝 포기는 빼고, 포장 안쪽에서 생육이 평균적인 포기 **10주**를 골라 재고 평균을 냅니다. 결주나 병든 포기는 건너뜁니다.

**초장 (cm)**
- 땅에 닿는 줄기 밑동(지제부)부터 줄기 맨 끝(가장 위 잎이 달린 생장점)까지의 길이.
- 줄기를 곧게 세운 상태에서 줄자로 잽니다. 처진 가지가 아니라 **원줄기** 기준입니다.
- 세부실행계획서: "지체부에서 최첨단 엽까지의 길이"

**주경장 (cm)**
- 지제부부터 줄기가 처음 갈라지는 곳(방아다리, 제1화방)까지의 길이.
- 세부실행계획서: "지체부에서 제1화방까지의 길이"

**분지수 (개)**
- 가장 길게 자란 줄기 하나를 골라, 방아다리부터 꽃망울이 달린 끝까지 줄기가 갈라진 횟수를 셉니다.
- 세부실행계획서: "생육기 가장 긴 줄기 선택, 방아다리에서 꽃망울이 있는 곳까지의 분지수"

**착과수 (개/주)** — 하반기
- 조사한 포기에 달린 과실 수. 풋고추·붉은 고추 모두 세고, 꽃과 꽃망울은 뺍니다.

**열간 (cm)**
- **두둑 가운데에서 옆 두둑 가운데까지**의 거리(고랑 포함). 2열 재배도 두둑 가운데~가운데로 잽니다.
- 두둑 하나만 재면 오차가 커서, 5두둑 폭을 한 번에 재고 5로 나누는 것이 좋습니다.

**주간 (cm)**
- 같은 줄에서 포기와 포기 사이 거리.
- 11포기의 처음부터 끝까지를 재고 10으로 나누면 오차가 줄어듭니다.
"""


def irrigation_group(s):
    """두상관수_하위유형_분해검증_261012 결정에 따라 분사호스와 스프링클러를 분리"""
    s = str(s)
    if "점적" in s:
        return "점적관수"
    if "분사" in s:
        return "분사호스"
    if "스프링" in s or "분수" in s:
        return "스프링클러"
    if "무관수" in s:
        return "무관수"
    return None   # 미조사 등


IRR_OPTS = ["전체", "무관수", "점적관수", "분사호스", "스프링클러"]

with tab2:
    spath = find_file(["상반기"], ".xlsx")
    hpath = find_file(["하반기"], ".xlsx")
    if not spath and not hpath:
        st.warning("작황조사 파일을 찾지 못했어요. app.py 폴더에 이름에 '상반기', '하반기'가 들어간 "
                   "작황조사 엑셀 파일을 넣거나 아래에 올려주세요.")
        c1, c2 = st.columns(2)
        up_s = c1.file_uploader("상반기 작황조사 xlsx", type="xlsx", key="up_s")
        up_h = c2.file_uploader("하반기 작황조사 xlsx", type="xlsx", key="up_h")
        spath, hpath = up_s, up_h

    st.subheader("내 포장은 같은 지역 조사포장 중 어디쯤일까?")
    st.caption("경북 작황조사에서 매년 무작위로 뽑아 조사한 포장들과 내 포장 생육을 비교합니다. "
               "같은 농가를 매년 따라간 자료가 아니라, 해마다 다른 포장을 조사한 표본입니다.")

    with st.expander("📏 재는 방법 (초장·주경장·분지수·착과수·열간·주간)"):
        st.markdown(MEASURE_GUIDE)

    c1, c2, c3, c4 = st.columns([1, 1, 1.4, 1.4])
    period = c1.radio("조사 시기", ["상반기", "하반기"], horizontal=True, key="period",
                      help="상반기: 5월 말 조사 / 하반기: 7월 말 조사")
    src = spath if period == "상반기" else hpath
    if src is None:
        st.info(f"{period} 작황조사 파일이 없어요.")
    else:
        sv = load_survey(src).copy()
        # 터널·막덮기 재배는 비교에서 제외 (노지1열·노지2열만 비교)
        if "재배법" in sv.columns:
            sv = sv[sv["재배법"].astype(str).isin(["노지1열", "노지2열"])]
        has_irr = "관수방법" in sv.columns
        if has_irr:
            sv["관수구분"] = sv["관수방법"].map(irrigation_group)

        scope = c2.radio("비교 대상", ["같은 시군", "6개 시군 전체"], horizontal=True, key="scope")
        methods = ["전체"] + sorted(sv["재배법"].dropna().astype(str).unique().tolist()) \
            if "재배법" in sv.columns else ["전체"]
        method = c3.selectbox("재배법", methods, key="method",
                              help="1열·2열 재배는 생육 조건이 달라서 같은 재배법끼리 비교하는 것이 좋아요")
        irr = "전체"
        if has_irr:
            avail = [o for o in IRR_OPTS
                     if o == "전체" or (sv["관수구분"] == o).sum() >= 10]
            irr = c4.selectbox("관수 방식", avail, key="irr",
                               help="관수 방식은 2020년 이후 조사분에만 기록되어 있어요. "
                                    "분사호스와 스프링클러는 살수 방식이 달라 따로 봅니다")

        grp = sv if scope == "6개 시군 전체" else sv[sv["시군"] == sigun]
        if method != "전체":
            grp = grp[grp["재배법"].astype(str) == method]
        if irr != "전체":
            grp = grp[grp["관수구분"] == irr]
        yrs = grp["년도"] if len(grp) else sv["년도"]
        st.caption(f"비교 포장: {'6개 시군' if scope == '6개 시군 전체' else sigun} · "
                   f"{'전 재배법' if method == '전체' else method}"
                   f"{'' if irr == '전체' else ' · ' + irr} · {int(yrs.min())}~{int(yrs.max())}년 · "
                   f"**{len(grp):,}개 포장**")

        if len(grp) < 20:
            st.warning("비교할 포장이 20개 미만이에요. 비교 대상을 넓혀주세요.")
        else:
            vars_ = [v for v in SURVEY_VARS[period] if v[1] in grp.columns]
            st.markdown("**내 포장 값 입력** (처음엔 비교 포장의 중앙값이 들어가 있어요)")

            sm, sd_ = SURVEY_DATE[period]
            mday = st.columns([1, 3])[0].date_input("측정한 날", value=date(date.today().year, sm, sd_),
                                                    key=f"mday_{period}")
            gap = (mday - date(mday.year, sm, sd_)).days
            if abs(gap) > 10:
                st.warning(f"작황조사 시기({sm}월 {sd_}일 무렵)와 {abs(gap)}일 차이가 나요. "
                           f"고추는 이 시기에 빠르게 자라서, {'일찍' if gap < 0 else '늦게'} 재면 "
                           f"초장·분지수가 {'작게' if gap < 0 else '크게'} 나와 비교가 어긋날 수 있어요.")

            in_cols = st.columns(len(vars_))
            mine = {}
            for i, (name, col, unit, dec) in enumerate(vars_):
                med = float(grp[col].median())
                mine[name] = in_cols[i].number_input(f"{name} ({unit})", value=float(round(med, dec)),
                                                     step=1.0 if dec == 0 else 0.5, format="%.1f",
                                                     key=f"in_{period}_{name}")

            st.divider()
            res_cols = st.columns(len(vars_))
            for c, (name, col, unit, dec) in zip(res_cols, vars_):
                with c:
                    x = mine.get(name, np.nan)
                    p = percentile_of(grp[col], x)
                    label, icon = position_text(p)
                    med = grp[col].median()
                    q10v, q90v = grp[col].quantile(0.10), grp[col].quantile(0.90)
                    val = f"{x:,.{dec}f} {unit}" if not np.isnan(x) else "-"
                    st.metric(name, val)
                    st.markdown(f"{icon} **{label}**")
                    st.caption(f"비교 포장 P10 {q10v:,.{dec}f} · 중앙 {med:,.{dec}f} · "
                               f"P90 {q90v:,.{dec}f} {unit}")
                    if not np.isnan(x):
                        show_chart(dist_chart(grp[col], x, unit))
            st.caption("회색 막대: 비교 포장 분포 · 파란 선: 내 포장 · 점선: 중앙값 · 긴 점선: P10과 P90. "
                       "P10 미만이면 지역 포장 10곳 중 하위 1곳 수준, P90 초과면 상위 1곳 수준입니다. "
                       "위치일 뿐 좋고 나쁨이 아니에요(초장이 너무 크면 웃자람일 수도 있어요).")

            # 상반기(5월 말) 크기는 같은 농가 안에서 수량과 무관했음 → 위치 안내까지만
            if period == "상반기":
                st.info("**5월 말 크기는 '지역 평년 대비 위치'까지만 보세요.** 같은 농가를 해마다 비교하면 "
                        "6월 말 초장은 수량과 관계가 보이지 않았고(p=0.16), 수량과 이어진 것은 8월 말·시즌 최대 초장"
                        f"(1cm당 +{IDX_EFFECT['최대초장']:.2f}%)입니다. 초기에 작아도 7·8월에 잘 자라면 수량은 따라옵니다.")
            else:
                st.info("**7월 말 초장·착과수를 넣으면 수확량 조기예측 탭에서 주당 수확량 범위를 볼 수 있어요.** "
                        "다만 이 화면(작황조사, 포장 간 비교)과 조기예측(농가 정밀조사, 같은 농가의 해마다 차이)은 "
                        "자료가 달라서, 다른 포장보다 크다고 수량이 그만큼 더 나온다는 뜻은 아닙니다.")
                if "초장" in mine and "착과수" in mine:
                    if st.button("↪️ 이 초장·착과수를 수확량 조기예측(7월 말 식)에 넣기", key="to_early"):
                        st.session_state["y_h_7월 말"] = float(mine["초장"])
                        st.session_state["y_f_7월 말"] = float(mine["착과수"])
                        st.session_state["y_when"] = "7월 말"
                        st.success("넣었습니다. **수확량 조기예측** 탭을 열면 7월 말 식에 이 값이 "
                                   "들어가 있어요.")

            if period == "하반기":
                st.divider()
                st.markdown(f"**{'6개 시군' if scope == '6개 시군 전체' else sigun} 연도별 병해 발생 포장 비율**")
                pv = [(n, c) for n, c in PEST_VARS if c in grp.columns]
                if pv:
                    pc = st.columns(len(pv))
                    for c, (n, colname) in zip(pc, pv):
                        r = (grp[colname] > 0).groupby(grp["년도"]).mean() * 100
                        fig = go.Figure(go.Bar(x=[str(y) for y in r.index], y=r.values,
                                               marker_color=C_THIS,
                                               hovertemplate="%{x}년 %{y:.0f}%<extra></extra>"))
                        base_layout(fig, 240, "발생 포장 비율 (%)", top=30)
                        fig.update_layout(title=dict(text=n, x=0, font=dict(size=14)), bargap=0.35)
                        fig.update_xaxes(type="category")
                        with c:
                            show_chart(fig)
                    st.caption("발생 포장 비율 = 조사 포장 중 해당 병해가 1개 이상 관찰된 포장의 비율. "
                               "원 조사값(개)을 기준으로 계산하며 10주환산 열은 쓰지 않습니다.")

# ══════════════════════════════════════════════
# 탭: 수확량 조기예측
# ══════════════════════════════════════════════
with tab_y:
    st.subheader("생육 조사로 수확량 미리 보기")
    st.caption("농가 정밀조사 패널에서 생육 조사 항목만으로 최종 주당 수확량을 예측한 모형입니다. "
               "**연도 단위 교차검증**으로 평가했습니다 — 한 해를 통째로 빼고 나머지 해로 식을 만들어 그 해를 "
               "맞혀본, 실제 예측 상황과 같은 평가입니다.")

    yp = st.radio("보기", ["① 시점별 조기예측", "② 생육량 지수로 보기"], horizontal=True, key="yp")

    # ── ① 시점별 조기예측 ──
    if yp.startswith("①"):
        st.session_state.setdefault("y_when", "8월 말")
        when = st.radio("예측 시점", list(MODEL_EARLY.keys()), horizontal=True, key="y_when",
                        help="8월 말이 가장 정확합니다. 6월 말·7월 말은 정보가 없을 때보다 조금 나은 수준이에요")
        mdl = MODEL_EARLY[when]

        dflt = EARLY_DEFAULTS[when]
        day = {"6월 말": "6월 말", "7월 말": "7월 말", "8월 말": "8월 말~9월 초(늦어도 9월 3일)"}[when]
        left, right = st.columns([1, 1.2])
        with left:
            st.markdown("**조사값 입력** (조사포장 10주 평균)")
            # 시점마다 칸을 따로 둬서, 시점을 바꾸면 그 시점의 값으로 다시 시작함
            # 값은 session_state 기본값으로 둔다 (내 포장 비교에서 넘겨받을 수 있게)
            st.session_state.setdefault(f"y_h_{when}", dflt["초장"])
            h = st.number_input(f"{when} 초장 (cm)", step=1.0, format="%.1f", key=f"y_h_{when}")
            f = 0.0
            cum = 0.0
            if "착과수" in mdl["vars"]:
                st.session_state.setdefault(f"y_f_{when}", dflt["착과수"])
                f = st.number_input(f"{when} 착과수 (개/주)", step=1.0, format="%.1f",
                                    key=f"y_f_{when}")
            if "누적수확" in mdl["vars"]:
                cum = st.number_input("8월 31일까지 주당 수확량 (g)", value=dflt["누적수확"], step=10.0,
                                      format="%.0f", key="y_c")
            st.caption(f"초장·착과수는 **{day}에 잰 값**입니다. 시즌 중 가장 클 때의 초장이 아니라 그 시점의 값을 "
                       "넣어야 식이 맞습니다. 처음 들어 있는 값은 예시입니다.")
            n_plant = st.number_input("재식주수 (주/10a, 모르면 0)", value=0.0, step=100.0,
                                      format="%.0f", key="y_np",
                                      help="단수로 환산해 보려면 넣으세요. 재식주수 조사 자체에 "
                                           "측정 변동이 커서 환산값은 참고용입니다")

        ln_y = mdl["const"] + mdl["b_h"] * h
        if "착과수" in mdl["vars"]:
            ln_y += mdl["b_f"] * np.log1p(f)
        if "누적수확" in mdl["vars"]:
            ln_y += mdl["b_c"] * np.log1p(cum)
        y_hat = float(np.exp(ln_y))
        mape = mdl["mape"]
        lo, hi = y_hat * (1 - mape / 100), y_hat * (1 + mape / 100)

        with right:
            st.markdown("**예측 결과 — 주당 총수확량**")
            st.metric(f"{when} 기준 예측", f"{y_hat:,.0f} g/주")
            st.markdown(f"평균적으로 **±{mape:.1f}%** 빗나갑니다 → 대략 **{lo:,.0f} ~ {hi:,.0f} g/주**")
            st.caption("평균 절대 오차를 위아래로 붙인 폭입니다. 신뢰구간이 아니라서 실제 수확량이 "
                       "이 폭 밖으로 나가는 해도 절반 가까이 됩니다.")
            if "누적수확" in mdl["vars"] and cum > 0:
                st.caption(f"8월 31일까지 수확한 양이 예측 최종량의 약 {cum / y_hat * 100:.0f}%입니다. "
                           "수확이 늦게까지 이어지는 해(2025년처럼)는 과소 예측되는 경향이 있었습니다.")
            if n_plant > 0:
                st.markdown(f"재식주수 {n_plant:,.0f}주/10a 기준 → 단수 약 "
                            f"**{y_hat * n_plant / 1000:,.0f} kg/10a** "
                            f"(대략 {lo * n_plant / 1000:,.0f} ~ {hi * n_plant / 1000:,.0f})")

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=[lo, hi], y=[0, 0], mode="lines",
                                     line=dict(color=C_THIS, width=10), opacity=0.35,
                                     hoverinfo="skip", showlegend=False))
            fig.add_trace(go.Scatter(x=[y_hat], y=[0], mode="markers",
                                     marker=dict(size=16, color=C_THIS, line=dict(width=2, color="white")),
                                     hovertemplate="%{x:,.0f} g/주<extra></extra>", showlegend=False))
            fig.update_layout(height=110, margin=dict(l=10, r=10, t=6, b=28),
                              plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
            fig.update_xaxes(ticksuffix=" g", showgrid=True,
                             gridcolor="rgba(128,128,128,0.18)", zeroline=False)
            fig.update_yaxes(visible=False, range=[-0.8, 0.8])
            show_chart(fig)
            st.markdown(f"**쓰는 식** ({mdl['src']}) — ln(주당 g) = {mdl['const']:.3f} + {mdl['b_h']:.4f} × 초장"
                        + (f" + {mdl['b_f']:.3f} × ln(1+착과수)" if "착과수" in mdl["vars"] else "")
                        + (f" + {mdl['b_c']:.3f} × ln(1+8/31까지 수확 g)" if "누적수확" in mdl["vars"] else ""))

        st.divider()
        st.markdown("**시점이 늦어질수록 정확해집니다**")
        mrows = [{"시점": "아무 정보 없음 (다른 해 평균)", "쓰는 변수": "-",
                  "표본 외 설명력": "-0.10", "평균 오차": f"{MAPE_BASE:.1f}%"}]
        for w, m in MODEL_EARLY.items():
            mrows.append({"시점": w, "쓰는 변수": ", ".join(m["vars"]),
                          "표본 외 설명력": f"{m['r2']:.2f}", "평균 오차": f"{m['mape']:.1f}%"})
        mrows.insert(3, {"시점": "8/31 누적 수확량만 (기준선)", "쓰는 변수": "누적수확",
                         "표본 외 설명력": "-", "평균 오차": f"{EARLY_CHECK['기준선']:.1f}%"})
        mrows.append({"시점": "9월 15일", "쓰는 변수": "초장, 착과수, 누적수확",
                      "표본 외 설명력": "0.91", "평균 오차": f"{EARLY_CHECK['9월중순']:.1f}%"})
        c1, c2 = st.columns([1.3, 1])
        with c1:
            show_table(pd.DataFrame(mrows), hide_index=True)
            st.caption("농가 패널 2021~2026년 75행(19농가), 연도 단위 교차검증. 8월 말 모형은 "
                       f"**농가와 연도를 함께 빼고 검증해도 {EARLY_CHECK['농가연도제외']:.1f}%**로 거의 같았고, "
                       f"2021~2025년으로 만든 식으로 **2026년을 미리 예측하면 오차 {EARLY_CHECK['사전예측']:.1f}%"
                       f"(편향 {EARLY_CHECK['사전편향']:+.1f}%)**였습니다. 생육조사(초장·착과수)를 더하면 누적 수확량만 "
                       f"쓴 기준선보다 오차가 {EARLY_CHECK['기준선'] - MODEL_EARLY['8월 말']['mape']:.1f}%p 줄어듭니다.")
        with c2:
            fig = go.Figure(go.Bar(
                x=["정보 없음", "6월 말", "7월 말", "8/31 누적만", "8월 말", "2026 사전예측", "9월 중순"],
                y=[MAPE_BASE, MODEL_EARLY["6월 말"]["mape"], MODEL_EARLY["7월 말"]["mape"],
                   EARLY_CHECK["기준선"], MODEL_EARLY["8월 말"]["mape"], EARLY_CHECK["사전예측"],
                   EARLY_CHECK["9월중순"]],
                marker_color=[C_OTHER, C_THIS, C_THIS, C_OTHER, C_THIS, C_OK, C_OK],
                hovertemplate="%{x} 평균 오차 %{y:.1f}%<extra></extra>"))
            fig.add_hline(y=10, line_dash="dot", line_color=C_ALERT,
                          annotation_text="오차 10%", annotation_position="top right",
                          annotation_font_color=C_ALERT)
            base_layout(fig, 260, "평균 절대 오차 (%)")
            fig.update_layout(bargap=0.35)
            fig.update_xaxes(type="category")
            show_chart(fig)

        with st.expander("이 예측의 근거와 한계", expanded=False):
            st.markdown(f"""
**근거**

- 자료: 농가 정밀조사 2021~2026년 75행(19농가). 2018~2020년은 시점별 항목 결측이 많아 제외.
- 목표: 주당 총수확량(g). 재식밀도와 분리되는 지표입니다.
- 검증: 연도 단위 교차검증(모형을 만들 때 그 해 자료를 전혀 쓰지 않음), 농가와 연도를 함께 빼는 검증,
  2026년 사전 예측까지 세 가지로 확인했습니다.
- 예측 시점: **8월 말~9월 초(늦어도 9월 3일) 생육조사, 수확량은 8월 31일까지 누적**입니다.
  조사일이 9월 초로 1~3일 늦은 행이 절반쯤인데, 그 행의 오차가 오히려 커서 늦은 조사가 예측을 좋게 만든
  흔적은 없었습니다.

**한계**

1. **조사포장 수확량입니다.** 농가 실수확량의 절대 예측으로 쓰면 안 됩니다.
   같은 조사 방식 안에서의 상대 예측입니다.
2. **농가 이력은 도움이 안 됩니다.** 그 농가의 다른 해 평균으로 예측하면 전체 평균보다 나쁩니다.
   작년에 잘 된 농가가 올해도 잘 된다고 보기 어렵습니다.
3. **복잡한 모형은 이득이 없습니다.** 시점별 생육 4종, 정식일, 시군 기상(착과 전 고온일,
   7월 일사·강수)을 모두 넣으면 오히려 나빠집니다. 변수 2~3개의 단순 회귀가 가장 낫습니다.
   **시군 기상 변수는 예측력을 더하지 않았습니다.**
4. **연도별 편향**: 8월 말 모형의 연도별 평균 편향은 {EARLY_CHECK['편향범위']}입니다.
   수확이 늦게까지 이어지는 해(2025년 -9.4%)는 과소 예측됩니다.
5. **조사 종료일이 해마다 다릅니다**(2023년 9/11~10/16, 2025년 10/20~10/27).
   "최종 수확량"의 일부는 작물이 아니라 조사가 언제 끝났는지에 좌우됩니다.
6. **6월 말·7월 말 식**은 2021~2025년 63행으로 만든 식입니다(오차는 2026년 포함 검증값).
   정보가 없을 때({MAPE_BASE:.1f}%)보다 7%p쯤 나은 수준이라 참고로만 보세요.
7. **위성 식생지수**(8~9월 NDVI·NDRE)는 그해 다른 농가 수준을 알 때 8월 말부터 오차를 7~11% 줄였지만,
   8월 말 생육조사와 담는 정보가 거의 같아 이 식에는 넣지 않았습니다.
8. 예측값은 로그 식을 지수로 되돌린 값이며 역변환 보정(약 +잔차분산/2)은 하지 않았습니다.
   평균 오차 ±12.6% 폭에 비하면 작은 차이이고, 약간 낮은(보수적인) 쪽의 값입니다.
""")

        st.info("**기상 변수를 넣지 않은 이유** — 예측력을 더하지 않았습니다. "
                "착과 전 고온 효과는 농가 포장 센서에서만 나타나고, 같은 행에 시군 관측소 값을 넣으면 "
                f"{HEAT_PRE['관측소과수']:+.1f}%(p={HEAT_PRE['관측소과수p']})로 0입니다. 이 앱이 쓰는 시군 관측소 "
                "기상으로는 수확량 예측의 근거가 약합니다. 기상 위험은 '오늘의 진단'과 '생육기 기상 위험 진단' "
                "탭에서 지표로만 보여줍니다.")

    # ── ② 생육량 지수 ──
    else:
        st.markdown("""
8월 말 생육조사 5개 지표(초장, 주경장, 줄기굵기, 분지수, 착과수)를 각각 표준화해서
단순평균한 값을 **생육량 지수**라고 부릅니다. 개별 지표를 따로 쓰는 것보다 수량과 훨씬 잘 맞습니다.
""")
        st.caption("이 결과는 농가·연도 고정효과 모형이라 **같은 농가 안에서 해마다 생육이 달랐을 때**의 "
                   "차이입니다. 다른 농가와 비교한 값이 아닙니다.")
        z = st.slider("같은 포장에서 생육량이 평소보다 몇 표준편차 좋았나", min_value=-2.0, max_value=2.0,
                      value=0.0, step=0.25, key="idx_z",
                      format="%+.2f 표준편차")
        c1, c2, c3 = st.columns(3)
        dy = (np.exp(IDX_EFFECT["수량_ln"] * z) - 1) * 100
        dn = (np.exp(IDX_EFFECT["과수_ln"] * z) - 1) * 100
        dw = ((1 + IDX_EFFECT["과중"] / 100) ** z - 1) * 100
        c1.metric("주당 수확량", f"{dy:+.1f}%", delta=None)
        c1.caption("같은 포장의 평소 해 대비")
        c2.metric("주당 수확과수", f"{dn:+.1f}%")
        c2.caption("수량 증가는 주로 과실 수에서 나옵니다")
        c3.metric("평균 과중", f"{dw:+.1f}%")
        c3.caption(f"p={IDX_EFFECT['과중p']}, 유의하지 않음")

        st.divider()
        irows = [{"지표 (1 표준편차당 주당수확량)": n, "8월 말": a, "WCR p (8월 말)": ap,
                  "6월 말": b, "WCR p (6월 말)": bp} for n, a, ap, b, bp in IDX_TIMING]
        irows.append({"지표 (1 표준편차당 주당수확량)": "생육량 지수 (5개 단순평균)",
                      "8월 말": f"+{(np.exp(IDX_EFFECT['수량_ln']) - 1) * 100:.1f}%", "WCR p (8월 말)": "<0.001",
                      "6월 말": "-", "WCR p (6월 말)": "-"})
        c1, c2 = st.columns([1.4, 1])
        with c1:
            show_table(pd.DataFrame(irows), hide_index=True)
            st.caption(f"농가 FE + 연도 FE, 반복조사 {IDX_EFFECT['표본']}(2018~2026), p는 소표본 보정(WCR). "
                       "실제 증가율(%)로 적었습니다. 생육량 지수 +26.0%의 95% 신뢰구간은 +16.8~+35.9%입니다. "
                       "6월 말 조사값은 줄기굵기(+13.9%, p=0.033)를 빼면 수량과 유의하지 않았고, 줄기굵기도 "
                       "단일 지표 결과라 참고로만 봅니다. 6월 말 조사는 평균 6월 30일, 8월 말 조사는 평균 "
                       "8월 31일(수확 시작 후 평균 35일)에 했습니다.")
        with c2:
            st.markdown("**지수 1 표준편차 = 5개 지표가 동시에 이만큼**")
            show_table(pd.DataFrame([{"지표": n, "1 표준편차": f"{v:g} {u}"}
                                     for n, v, u in IDX_EFFECT["환산"]]), hide_index=True)

        st.markdown("### 중요한 것은 6월 말 크기가 아니라 여름 동안의 생육")
        st.markdown(f"""
같은 농가 안에서 비교하면 **6월 말 초장은 수량과 관계가 보이지 않고**(p=0.16), 8월 말·최대 초장은 분명히
이어집니다. 최대 초장은 1cm당 주당수확량 **+{IDX_EFFECT['최대초장']:.2f}%**(WCR p<0.001)이고,
연도를 하나씩 빼도 {IDX_EFFECT['최대초장범위']}%로 유지됩니다.

- 6월 말에 작아도 7·8월에 잘 자라면 수량은 따라옵니다.
- 반대로 6월 말에 크다고 안심할 근거는 없습니다.
- 최대 초장은 정식 후 관리, 수분, 기상이 누적된 **생육 활력 지표**입니다.
  직접 조절하는 관리 변수가 아니라 결과 지표로 읽어야 합니다.
- 착과 전 고온일이 많으면 8월 말 분지수가 줄었습니다(1일당 {HEAT_PRE['분지수']:.2f}개).

**WCR p** = wild cluster restricted bootstrap으로 구한 p값입니다. 농가가 19개뿐이라
보통의 클러스터 표준오차는 p값을 너무 작게 내놓습니다. 자료를 농가 단위로 수천 번
다시 섞어 실제 분포에서 p를 구하는 방법이며, 소표본에서 이 값이 더 믿을 만합니다.
""")

# ══════════════════════════════════════════════
# 탭: 작황조사 대시보드 (따로 만든 HTML 대시보드를 그대로 띄움)
# ══════════════════════════════════════════════
if tab_db is not None:
    with tab_db:
        dpath = find_file(["대시보드"], ".html")
        if dpath is None:
            st.info("작황조사 대시보드 HTML 파일을 app.py 폴더에 넣으면 여기에 나와요 "
                    "(파일 이름에 '대시보드'가 들어가면 자동으로 찾아요).")
        else:
            html = read_text(dpath, os.path.getmtime(dpath))
            c1, c2 = st.columns([3, 1])
            c1.caption(f"파일: {os.path.basename(dpath)} · 상반기·하반기 작황조사를 시군 × 연도로 묶어 본 통합 대시보드입니다. "
                       "대시보드 안에서 엑셀을 올려 갱신한 내용은 이 브라우저에만 저장돼요.")
            c2.download_button("⬇️ 대시보드 파일 내려받기", data=html.encode("utf-8"),
                               file_name=os.path.basename(dpath).lstrip("♥♡★☆ _-"), mime="text/html",
                               key="dl_dash")
            st.caption("⚠️ 하반기 병해충의 **개수(강도)** 그래프는 연도 간 직접 비교에 주의하세요. 탄저병 조사 주수가 "
                       "2013~2022년 10주에서 2023년(일부 조) 이후 3주로 바뀌었고, 10주환산 열에는 연도마다 다른 배수가 "
                       "들어 있습니다. 연도 비교는 **발생 포장 비율**로 보는 것이 안전합니다.")
            if "cdn.jsdelivr.net/npm/chart.js" in html:
                st.caption("이 대시보드는 그래프 도구를 인터넷에서 불러와요. 인터넷이 없으면 그래프가 안 보일 수 있으니, "
                           "발표장에서는 오프라인판을 쓰세요.")
            # 최신 Streamlit은 st.iframe, 예전 버전은 components.html
            if hasattr(st, "iframe"):
                st.iframe(html, height=2400)
            else:
                components.html(html, height=2400, scrolling=True)

# ══════════════════════════════════════════════
# 탭 3: 자료 품질 점검
# ══════════════════════════════════════════════
if tab3 is not None:
    with tab3:
        st.subheader("자료 품질 점검")
        st.caption("이 연구에서 분석보다 먼저 한 일은 자료를 의심하는 것이었습니다. "
                   "생산량 통계와 기상 관측값에서 찾은 문제를 그대로 보여주고, 같은 점검을 다른 자료에도 돌릴 수 있게 했습니다.")

        part = st.radio("보기", ["① 생산량 통계", "② 일사량 관측 오차", "③ 기상자료 자동 점검"],
                        horizontal=True, key="qc_part")

        # ── ① 생산량 통계 ──
        if part == "① 생산량 통계":
            ppath = find_file(["생산량"], ".csv")
            if ppath is None:
                ppath = st.file_uploader("6개시군 생산량 CSV를 올려주세요", type="csv", key="up_p")
            prod = load_production(ppath) if ppath is not None else None
        if part == "① 생산량 통계" and prod is not None:
            sg_list = [s for s in SIGUN_ORDER if s in prod["시군"].unique()]

            st.markdown("#### 시군 단수 통계 (kg/10a = 생산량 ÷ 면적)")
            from_2010 = st.checkbox("2010년부터 보기 (기본은 분석 기간인 2016년부터)", value=False, key="from2010")
            y0 = int(prod["연도"].min()) if from_2010 else 2016
            fig = go.Figure()
            for sg in sg_list:
                g = prod[(prod["시군"] == sg) & (prod["연도"] >= y0)].sort_values("연도")
                fig.add_trace(go.Scatter(x=g["연도"], y=g["단수"], mode="lines+markers", name=sg,
                                         line=dict(color=SIGUN_COLOR.get(sg), width=2),
                                         marker=dict(size=7),
                                         hovertemplate=f"{sg} " + "%{x}년 %{y:.0f} kg/10a<extra></extra>"))
            marks = [("안동시", 2020, "안동 2020 계단"), ("청송군", 2017, "청송 2017"), ("영양군", 2019, "영양 2019")]
            for sg, y, txt in marks:
                r = prod[(prod["시군"] == sg) & (prod["연도"] == y)]
                if len(r) and not np.isnan(r["단수"].iloc[0]):
                    fig.add_annotation(x=y, y=r["단수"].iloc[0], text=txt, showarrow=True, arrowhead=0,
                                       ax=0, ay=-34, font=dict(size=12, color=C_ALERT),
                                       arrowcolor=C_ALERT)
            base_layout(fig, 400, "단수 (kg/10a)")
            fig.update_layout(legend=dict(orientation="h", y=1.1, x=0), hovermode="closest")
            fig.update_xaxes(dtick=1)
            show_chart(fig)

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**구간별 단수 평균과 변동계수(CV)**")
                rows = []
                for sg in sg_list:
                    g = prod[prod["시군"] == sg].set_index("연도")["단수"]
                    a, b = g.loc[2016:2019].dropna(), g.loc[2020:2024].dropna()
                    rows.append({"시군": sg,
                                 "2016~19 평균": round(a.mean()), "2016~19 CV(%)": round(a.std() / a.mean() * 100, 1),
                                 "2020~24 평균": round(b.mean()), "2020~24 CV(%)": round(b.std() / b.mean() * 100, 1)})
                show_table(pd.DataFrame(rows).set_index("시군"))
                st.caption("노지고추 단수가 4~5년 연속 1% 안쪽으로만 움직이는 것은 기상·병해충 변동을 생각하면 "
                           "실측 변동으로 보기 어렵습니다. 안동은 두 개의 고정값과 2020년 계단입니다.")
            with c2:
                st.markdown("**면적과 생산량의 상관 (2018~2024)**")
                rows = []
                for sg in sg_list:
                    g = prod[(prod["시군"] == sg) & prod["연도"].between(2018, 2024)].dropna(subset=["면적"])
                    rows.append({"시군": sg, "상관계수": round(g["면적"].corr(g["생산량"]), 3)})
                show_table(pd.DataFrame(rows).set_index("시군"))
                st.caption("상관이 0.96을 넘으면 생산량이 면적에 거의 고정된 단수를 곱해 산출되고 있다는 뜻입니다. "
                           "그러면 단수 통계에는 연도별 작황 변동이 거의 남지 않습니다.")

            st.markdown("#### 재배면적 — 2024년 급감")
            fig = go.Figure()
            for sg in sg_list:
                g = prod[(prod["시군"] == sg) & (prod["연도"] >= 2016)].sort_values("연도")
                fig.add_trace(go.Scatter(x=g["연도"], y=g["면적"], mode="lines+markers", name=sg,
                                         line=dict(color=SIGUN_COLOR.get(sg), width=2), marker=dict(size=7),
                                         hovertemplate=f"{sg} " + "%{x}년 %{y:,.0f} ha<extra></extra>"))
            base_layout(fig, 320, "노지 면적 (ha)")
            fig.update_layout(legend=dict(orientation="h", y=1.12, x=0))
            fig.update_xaxes(dtick=1)
            show_chart(fig)
            chg = prod[prod["연도"].isin([2023, 2024])].pivot(index="시군", columns="연도", values="면적")
            if 2023 in chg.columns and 2024 in chg.columns:
                chg["변화(%)"] = ((chg[2024] / chg[2023] - 1) * 100).round(1)
                big = chg[chg["변화(%)"].abs() >= 10]
                if len(big):
                    st.caption("2023→2024 면적 변화가 10% 넘는 시군: " +
                               ", ".join(f"{i} {v:+.1f}%" for i, v in big["변화(%)"].items()) +
                               " · 다른 시군은 거의 그대로여서 조사 표본·방식 변경이 의심됩니다.")

        # ── ② 일사량 관측 오차 ──
        if part == "② 일사량 관측 오차":
            st.markdown("#### 청천지수(KT)로 본 일사량 관측 오차")
            st.caption("청천지수 = 실측 일사량 ÷ 대기 밖 일사량. 맑은 날에도 0.75~0.78이 상한이고, "
                       "0.80을 넘으면 물리적으로 불가능한 값입니다. 연도별 상위 5% 값(95퍼센타일)을 비교했습니다.")
            kt = add_kt(wx)
            p95 = kt.groupby(["연도", "지역"])["KT"].quantile(0.95).unstack()
            fig = go.Figure()
            for sg in [s for s in SIGUN_ORDER if s in p95.columns]:
                fig.add_trace(go.Scatter(x=p95.index, y=p95[sg], mode="lines+markers", name=sg,
                                         line=dict(color=SIGUN_COLOR.get(sg), width=2), marker=dict(size=7),
                                         hovertemplate=f"{sg} " + "%{x}년 %{y:.3f}<extra></extra>"))
            fig.add_hrect(y0=0.80, y1=max(0.86, float(np.nanmax(p95.values)) + 0.01),
                          fillcolor=C_ALERT, opacity=0.08, line_width=0)
            fig.add_hline(y=0.80, line_dash="dot", line_color=C_ALERT,
                          annotation_text="물리적 상한 0.80", annotation_position="top left",
                          annotation_font_color=C_ALERT)
            base_layout(fig, 380, "청천지수 95퍼센타일 (원값)")
            fig.update_layout(legend=dict(orientation="h", y=1.1, x=0))
            fig.update_xaxes(dtick=1)
            show_chart(fig)

            over = (kt["KT"] > 0.80).groupby([kt["지역"], kt["연도"]]).sum().unstack(fill_value=0)
            over = over.loc[over.sum(axis=1) > 0]
            if len(over):
                st.markdown("**청천지수 0.80을 넘은 날 수 (원값 기준)**")
                show_table(over)
            bad2 = kt[kt["KT_최종"] > 0.80]
            over2 = bad2.groupby(["지역", "연도"]).size().unstack(fill_value=0)
            st.markdown("**최종 구성 적용 후 남은 0.80 초과일**")
            if len(over2):
                show_table(over2)
                in_season = int(bad2["일시"].dt.month.between(5, 9).sum())
                if in_season == 0:
                    st.success(f"남은 {len(bad2)}일은 **모두 생육기(5~9월) 밖**입니다 "
                               f"(겨울철 적설 반사 등). 분석에 쓰는 구간에는 물리 상한을 넘는 값이 없습니다.")
                else:
                    st.warning(f"남은 {len(bad2)}일 중 **{in_season}일이 생육기(5~9월)** 안에 있습니다. "
                               "해당 시군·연도를 확인하세요.")
                st.caption("생육기 일사량이 33 MJ/m²를 넘는 날: "
                           f"{int((wx[COL['solar']] > 33).sum())}건 "
                           "(중간평가 자료의 안동 2024-08-14 39.7 MJ는 ASOS 대체로 해소되었습니다)")
            else:
                st.success("최종 구성에서는 청천지수 0.80을 넘는 날이 없습니다.")

            st.markdown("#### 최종 구성")
            st.markdown("""
| 시군 | 일사량 | 기온·강수·습도 |
|---|---|---|
| 봉화군 | 농업기상 × 0.899 (2016.1.1~2017.5.30) | 실측 |
| 안동시 | **ASOS 실측 전 기간 대체** | 실측 |
| 예천군 | 2016~2019 안동 ASOS × 0.919 / 2020년부터 실측 | **실측** |
| 영양군 | 농업기상 원값 | 실측 |
| 의성군 | 농업기상 원값 | 실측 |
| 청송군 | 농업기상 원값 | 실측 |

예천군은 오랫동안 "안동 자료 복제"로 알려져 있었지만 변수별로 확인하니 **일사량만** 복제였습니다
(2016~2019년 365/365일 동일). 기온·습도·강수·결로는 모두 실측입니다.
예천/안동 생육기 일사량 실측 비율 0.919(2020~2025)를 안동 ASOS에 곱해 환산했습니다.

습도는 분석에서 제외했습니다. 청송은 같은 시군 두 관측망의 연도별 습도 상관이 0.008입니다
(기온은 전 시군 0.957~0.993). 냉해일도 제외했습니다. 봄·가을 서리가 한 변수에 섞여 있고
연도 고정효과를 넣으면 사라집니다.
""")
            if not SOLAR_FINAL:
                st.error("지금 이 앱에는 ASOS 파일이 없어서 위 표의 안동·예천 처리가 **적용되지 않았습니다.** "
                         "app.py 폴더에 이름에 'ASOS'가 들어간 일자료 CSV를 넣어주세요.")

            st.markdown("#### 보정 전후 생육기(5~9월) 평균 일사량")
            fx = kt[kt["일시"].dt.month.between(5, 9)]
            targets = [s for s in ["봉화군", "안동시", "예천군"] if s in fx["지역"].unique()]
            if targets:
                cc = st.columns(len(targets))
                for c, sg in zip(cc, targets):
                    g = fx[fx["지역"] == sg].groupby("연도")[["일사량_점검", COL["solar"]]].mean()
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=g.index, y=g["일사량_점검"], name="원값", mode="lines+markers",
                                             line=dict(color=C_ALERT, width=2, dash="dot"), marker=dict(size=7)))
                    fig.add_trace(go.Scatter(x=g.index, y=g[COL["solar"]], name="최종 구성", mode="lines+markers",
                                             line=dict(color=C_THIS, width=2.5), marker=dict(size=7)))
                    base_layout(fig, 260, "MJ/m²", top=30)
                    fig.update_layout(title=dict(text=sg, x=0, font=dict(size=14)),
                                      legend=dict(orientation="h", y=-0.2, x=0))
                    fig.update_xaxes(dtick=1)
                    with c:
                        show_chart(fig)

            st.success("**일사량 효과는 살아 있습니다.** 2026년 9월 1차 진단에서는 "
                       "\"오차를 바로잡으니 일사량 효과가 사라졌다\"고 보았으나, 이것은 KT 비율보정만 적용한 "
                       "중간 단계의 판정이었습니다. ASOS 실측 대체와 예천 실측 반영까지 마친 최종 구성에서 "
                       f"일사량은 단수와 유의한 양의 관계를 유지합니다(β +{SOLAR_MAIN['계수']:.1f} kg/10a, "
                       f"p={SOLAR_MAIN['p']}). 계수는 전 구성에서 +9.9~+11.3으로 안정적입니다.")
            st.warning("**대신 폭염일이 유의성을 잃었습니다.** 중간평가에서 10% 수준으로 유의했던 폭염일이 "
                       "예천 실측을 반영하자 p=0.060에서 0.156이 되었습니다. 중간평가 그림 7의 폭염일(생육기 33℃ 총일수)은 **계절 총량으로는 "
                       "살릴 수 없고**, 착과 전(7/3~7/28)으로 창을 좁히면 살아납니다"
                       f"(1일당 {HEAT_PRE['시군계수']:.2f} kg/10a, p={HEAT_PRE['시군p']}). "
                       "표 10의 기상 순기여도 +2.1%p에서 +0.9%p로 내려갑니다.")

        # ── ③ 기상자료 자동 점검 ──
        if part == "③ 기상자료 자동 점검":
            st.markdown("#### 기상자료 자동 점검")
            st.caption("기본은 지금 앱이 쓰는 기상자료입니다. 같은 형식(지역, 일시, 기온·습도·강수·일사량 열)의 "
                       "다른 CSV를 올리면 그 자료를 점검합니다.")
            up_q = st.file_uploader("점검할 기상 CSV (선택)", type="csv", key="up_q")
            qwx = load_weather(up_q) if up_q is not None else wx
            missing = [v for v in [COL["tavg"], COL["tmax"], COL["tmin"], COL["rh"], COL["rain"], COL["solar"]]
                       if v not in qwx.columns]
            if missing:
                st.error("필요한 열이 없어요: " + ", ".join(missing))
        if part == "③ 기상자료 자동 점검" and not missing:
            st.markdown("**1. 값 범위·논리 점검**")
            rc = range_checks(qwx)
            if rc.empty:
                st.success("범위·논리 오류가 없어요.")
            else:
                show_table(rc, hide_index=True)

            st.markdown("**2. 계단(불연속) 탐지** — 한 시군의 월평균에서 나머지 시군 중앙값을 뺀 차이가 "
                        "어느 시점에 갑자기 바뀌는지 찾습니다. 관측소 이전, 센서 교체가 이런 흔적을 남깁니다.")
            var_opts = {"평균기온": COL["tavg"], "최고기온": COL["tmax"], "최저기온": COL["tmin"],
                        "평균습도": COL["rh"], "일사량": COL["solar"]}
            q_regions = [s for s in SIGUN_ORDER if s in qwx["지역"].unique()] + \
                        [s for s in qwx["지역"].unique() if s not in SIGUN_ORDER]

            mtab = monthly_means(qwx, list(var_opts.values()))
            summary = []
            first_flag = None
            for sg in q_regions:
                row = {"시군": sg}
                for vn, vc in var_opts.items():
                    r = detect_step(mtab, sg, vc)
                    if r is None:
                        row[vn] = "-"
                        continue
                    if r["t"] >= 10 and first_flag is None:
                        first_flag = (sg, vn)
                    g, icon = step_grade(r["t"])
                    row[vn] = f"{icon} {r['날짜']:%Y.%m} ({r['이후'] - r['이전']:+.1f})" if r["t"] >= 6 else f"{icon}"
                summary.append(row)
            show_table(pd.DataFrame(summary).set_index("시군"))
            st.caption("🔴 뚜렷한 계단 · 🟡 계단 의심 · 🟢 뚜렷한 계단 없음 · 괄호는 계단 시점(연.월)과 "
                       "나머지 시군 대비 차이의 변화량(기온 ℃, 습도 %p, 일사량 MJ/m²). "
                       "이 앱이 쓰는 자료는 일사량이 이미 최종 구성으로 바뀐 상태라, 일사량 열의 계단은 "
                       "보정 뒤에도 남은 것만 보입니다.")

            c1, c2 = st.columns(2)
            f_sg, f_var = first_flag if first_flag else (q_regions[0], "평균기온")
            q_sg = c1.selectbox("자세히 볼 시군", q_regions, index=q_regions.index(f_sg), key="q_sg")
            q_var = c2.selectbox("변수", list(var_opts.keys()), index=list(var_opts.keys()).index(f_var), key="q_var")
            r = detect_step(mtab, q_sg, var_opts[q_var])
            if r is not None:
                s = r["series"]
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=s.index, y=s.values, mode="lines", name="월별 차이",
                                         line=dict(color=C_MEAN, width=1.5),
                                         hovertemplate="%{x|%Y.%m} %{y:+.2f}<extra></extra>"))
                fig.add_trace(go.Scatter(x=[s.index[0], r["날짜"]], y=[r["이전"]] * 2, mode="lines",
                                         name="계단 이전 평균", line=dict(color=C_THIS, width=3)))
                fig.add_trace(go.Scatter(x=[r["날짜"], s.index[-1]], y=[r["이후"]] * 2, mode="lines",
                                         name="계단 이후 평균", line=dict(color=C_ALERT, width=3)))
                fig.add_hline(y=0, line_color="rgba(128,128,128,0.5)")
                base_layout(fig, 340, f"{q_sg} − 나머지 시군 중앙값")
                fig.update_layout(legend=dict(orientation="h", y=1.1, x=0))
                show_chart(fig)
                g, icon = step_grade(r["t"])
                st.markdown(f"{icon} **{g}** · {r['날짜']:%Y년 %m월} 전후로 나머지 시군 대비 차이가 "
                            f"{r['이전']:+.2f} → {r['이후']:+.2f} 로 바뀜 (계단 강도 {r['t']:.1f})")
                st.caption("계단 강도 10 이상은 뚜렷한 계단, 6~10은 의심. 관측소 이력(이전·센서 교체)으로 확인이 필요합니다. "
                           "실제 날씨가 지역마다 달라서 생기는 차이와는 달리, 계단은 어느 시점부터 계속 유지됩니다.")

# ══════════════════════════════════════════════
# 탭 4: 연구 요약
# ══════════════════════════════════════════════
if tab4 is not None:
    with tab4:
        st.subheader("이 연구가 확인한 것과 어디에 쓰이는가")
        st.caption("2026년 11월 9일 분석 기준(농가 정밀조사 2026년 포함) · 결과보고서 최종본에서 수치가 바뀔 수 있습니다. "
                   "이 앱에서 '유의'는 5% 기준(p<0.05)이며, 0.05~0.10은 '경계 수준'으로 따로 적습니다.")

        st.markdown("### 1. 시군 단수 통계는 해마다의 작황 변동을 담지 못한다")
        c1, c2 = st.columns([3, 2])
        with c1:
            fig = go.Figure()
            cats = ["시군 통계<br>(2021~2024)", "농가 정밀조사<br>(2021~2026)"]
            fig.add_trace(go.Bar(y=cats, x=[98.3, 44.1], orientation="h", name="고정된 차이 (지역·농가 간)",
                                 marker_color=C_OTHER, text=["98.3%", "44.1%"], textposition="inside",
                                 hovertemplate="%{x}%<extra>고정된 차이</extra>"))
            fig.add_trace(go.Bar(y=cats, x=[0.3, 14.7], orientation="h", name="모든 지역·농가 공통 연도 변동",
                                 marker_color=C_THIS, text=["0.3%", "14.7%"], textposition="inside",
                                 hovertemplate="%{x}%<extra>공통 연도 변동</extra>"))
            fig.add_trace(go.Bar(y=cats, x=[1.3, 41.2], orientation="h", name="지역·농가별로 따로 움직인 연도 변동",
                                 marker_color="#8a3ffc", text=["1.3%", "41.2%"], textposition="inside",
                                 hovertemplate="%{x}%<extra>개별 연도 변동</extra>"))
            base_layout(fig, 240, None, top=30)
            fig.update_layout(barmode="stack", legend=dict(orientation="h", y=1.3, x=0), bargap=0.4)
            fig.update_xaxes(range=[0, 100], ticksuffix="%")
            fig.update_yaxes(autorange="reversed", showgrid=False)
            show_chart(fig)
        with c2:
            st.markdown("""
단수(수확량) 변동을 **고정된 차이**, **모두에게 공통인 연도 변동**,
**각자 따로 움직인 연도 변동**으로 나눠 봤습니다.

- 시군 통계는 최근 4년 변동의 **98.3%가 지역 차이**, 연도 변동은 1.6%뿐
- 4개 시군에서 면적-생산량 상관이 0.96 이상 → 고정 단수 × 면적으로 산출되는 구조
- 농가 정밀조사는 연도 변동이 **55.9%**
- 그 연도 변동 중 모든 농가가 함께 움직인 부분은 **14.7%**이고,
  **41.2%는 농가마다 따로** 움직였습니다 (주당 수확량 기준으로도 약 4할)
""")
        st.info("1차 분석의 \"기상의 순기여가 작다\"는 결과는 기상이 영향을 안 줘서가 아니라, "
                "종속변수인 시군 통계가 해마다 거의 움직이지 않아서였습니다. "
                "농가 자료로 바꿔도 연도 변동의 대부분은 **지역 전체에 공통인 요인이 아니라 "
                "포장마다 다른 요인**입니다. 포장 미기상, 관리, 병해, 조사 오차가 여기에 해당합니다. "
                "시군 관측소 기상만으로 수량 변동을 설명하는 데 한계가 있다는 근거입니다. "
                "2026년은 일부 농가의 재식 방식이 바뀌어 단수 기준 고정 차이가 커졌습니다.")

        st.markdown("### 2. 기상 요인처럼 보였던 것 중 일부는 관측 오차였다 — 그러나 일사량은 살아남았다")
        st.markdown(f"""
- 1차 분석에서 지역 차이를 통제해도 남은 유일한 기상 요인은 **8~9월 일사량**이었습니다.
- 청천지수로 점검하니 봉화(2016~2017, 과대)와 안동(2016~2018 초, 과소)에 **관측 오차**가 있었고,
  예천은 2016~2019년 일사량이 **안동 자료 복제**였습니다.
- 2026년 9월 1차 진단에서는 "보정하니 일사량 효과가 사라졌다"고 보았지만, 그것은 KT 비율보정만
  적용한 중간 단계였습니다. **ASOS 실측 대체와 예천 실측 반영까지 마친 최종 구성에서 일사량 효과는
  유지됩니다**(β +{SOLAR_MAIN['계수']:.1f} kg/10a, p={SOLAR_MAIN['p']}). 전 구성에서 +9.9~+11.3으로 안정적입니다.
- 대신 **폭염일이 유의성을 잃었습니다**(경계 수준이었던 p=0.060 → 0.156). 표 10의 기상 순기여도 +2.1%p → +0.9%p.
- **습도와 냉해일은 분석에서 제외**했습니다. 습도는 ASOS와 연도 변동이 어긋나고(청송 상관 0.008),
  냉해일은 봄·가을 서리가 한 변수에 섞여 연도 효과에서 사라집니다. → **자료 품질 점검** 탭
""")

        st.markdown("### 3. 남은 기상 결과 세 가지")
        st.markdown(f"""
| 결과 | 연도 고정효과 통과 | 크기 | 비고 |
|---|---|---|---|
| **일사량 × 강수량** | **예** | 교호 +0.041 (p=0.0008) | 유일하게 통과. ASOS 10개 시군(n=130)에서 재현(p=0.005) |
| 착과 전 고온일 34℃ | 시군: 아니오 / **농가 센서: 예** | 단수 -1.52 kg/10a/일 (p<0.001) | 31~37℃ 전 구간 음(-), 33℃ 이상 유의. 농가 센서 {HEAT_PRE['센서표본']}에서 연도 FE 아래 재현 |
| 일사량 (주효과) | 아니오 | +11.0 kg/10a (p=0.019) | 중간평가 결과 유지 |
""")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
**비가 적은 해에는 햇빛이 많아도 수량으로 가지 않는다**

| 생육기 강수량 | 일사량 1 MJ 증가당 단수 | p |
|---|---|---|
| 762mm (하위 25%) | +17.9 | 0.068 |
| 886mm (중앙) | +22.9 | 0.024 |
| 1041mm (상위 25%) | +29.2 | 0.007 |

광합성에 광량과 수분이 함께 요구되는 보완관계입니다.
중간평가 일사량 효과가 연도별로 불안정했던 이유를 설명합니다.
→ **생육기 기상 위험 진단** 탭
""")
        with c2:
            st.markdown(f"""
**착과 전 고온은 과실 수를 줄인다** (농가 센서 {HEAT_PRE['센서표본']})

| 기준 | 수확과수 | 총수확량 | 평균 과중 |
|---|---|---|---|
| 34℃ 이상 1일당 | **{HEAT_PRE['센서과수']:.1f}%** (p={HEAT_PRE['센서과수p']}) | {HEAT_PRE['센서총량']:.1f}% (경계) | {HEAT_PRE['센서과중']:+.1f}% (p={HEAT_PRE['센서과중p']}) |
| 33℃ 이상 1일당 | **{HEAT_PRE['센서과수33']:.1f}%** (p={HEAT_PRE['센서과수33p']}) | **{HEAT_PRE['센서총량33']:.1f}%** (p={HEAT_PRE['센서총량33p']}) | {HEAT_PRE['센서과중33']:+.1f}% (p={HEAT_PRE['센서과중33p']}) |

같은 행에 **시군 관측소 값을 넣으면 효과가 0**({HEAT_PRE['관측소과수']:+.1f}%, p={HEAT_PRE['관측소과수p']})인데,
포장 센서가 관측소보다 평균 {HEAT_PRE['센서기온차']:.2f}℃ 높고 34℃ 이상 일수가 {HEAT_PRE['센서일수차']:.1f}일 많기 때문입니다.
고온일 1일당 8월 말 분지수가 {HEAT_PRE['분지수']:.2f}개 줄고, 생육을 통제하면 효과가
{HEAT_PRE['생육통제']:.1f}%(p={HEAT_PRE['생육통제p']})로 줄어 **피해의 상당 부분이 생육 감소와 함께** 나타납니다.
포장 해발 100m마다 착과 전 34℃ 고온일이 {abs(HEAT_PRE['해발일수']):.1f}일 줄어 **저지대 포장이 더 노출**됩니다.
위성 식생지수는 고온에 줄지 않아(p={SAT['고온NDVIp']}) 잎을 보고는 피해를 알 수 없습니다.
""")
        st.caption("기각된 기상변수: 평균습도, 냉해일, 무상기간, 8월 평균기온, 폭염일(연간 총량), "
                   "강수량 24개 형태, 일교차 18개 형태, 야간 고온(열대야·적산도일·호흡지수) 28개 형태 이상, "
                   "교호항 10개, 착과수와 조사 전 강우(누적 기간 1~14일 × 기준량 135개 지표, 연도 효과·다중비교 고려 시 "
                   "관계 없음). 관수 × 고온 완화는 2년 자료에서 보였으나 3년 자료의 사전 지정 검정에서 확인되지 않았습니다(고온기 관수 × 고온, p=0.65).")

        st.markdown("### 4. 생육량은 수량과 분명히 이어진다 — 경로는 과실 수")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
**생육량 → 수량** (반복조사 {IDX_EFFECT['표본']}, 농가·연도 고정효과)

| 지표 | 1 표준편차당 | p |
|---|---|---|
| 생육량 지수 → 주당 수확량 | **+26.0%** | <0.001 |
| 생육량 지수 → 주당 수확과수 | +16.6% | 0.002 |
| 생육량 지수 → 평균 과중 | +8.0% | 0.068 (경계) |

실제 증가율(%), p는 소표본 보정(WCR)입니다.
최대 초장 1cm당 주당 수확량 +{IDX_EFFECT['최대초장']:.2f}%(p<0.001)이며
연도를 하나씩 빼도 {IDX_EFFECT['최대초장범위']}%로 유지됩니다.
""")
        with c2:
            st.markdown(f"""
**6월 말 크기보다 여름 동안의 생육**

- 6월 말 조사값은 줄기굵기(+13.9%, p=0.033)를 빼면 수량과 유의하지 않았습니다(초장 p=0.16).
- 8월 말 초장(+24.2%)·줄기굵기(+16.6%)·착과수(+12.2%)·분지수(+9.2%)가 유의했습니다.
- 2025년까지 보였던 생육량과 비상품과율의 상충은 2026년을 더하면 사라졌습니다(p=0.57).

고온도, 생육량도 모두 **과실 수**를 통해 작동합니다.
이 지역 노지고추의 수량 변동은 과실 비대가 아니라
**착과 단계에서 결정된다**는 공통 결론으로 묶입니다.
""")

        st.markdown("### 5. 생육 조사로 수확량을 미리 볼 수 있다")
        c1, c2 = st.columns([1.2, 1])
        with c1:
            st.markdown(f"""
| 시점 | 쓰는 변수 | 평균 오차 |
|---|---|---|
| 아무 정보 없음 | - | {MAPE_BASE:.1f}% |
| 6월 말 | 초장 | {MODEL_EARLY['6월 말']['mape']:.1f}% |
| 7월 말 | 초장, 착과수 | {MODEL_EARLY['7월 말']['mape']:.1f}% |
| 8/31 누적 수확량만 (기준선) | 누적수확 | {EARLY_CHECK['기준선']:.1f}% |
| 8월 말~9월 초 | 초장, 착과수, 8/31까지 수확량 | **{MODEL_EARLY['8월 말']['mape']:.1f}%** |
| 같은 식으로 2026년 사전 예측 | 같음 | **{EARLY_CHECK['사전예측']:.1f}%** |
| 9월 중순 | 같음 | {EARLY_CHECK['9월중순']:.1f}% |

2021~2026년 75행(19농가), 연도 단위 교차검증. 농가와 연도를 함께 빼도 {EARLY_CHECK['농가연도제외']:.1f}%.
→ **수확량 조기예측** 탭
""")
        with c2:
            st.markdown("""
**예측에 도움이 안 된 것**

- **농가 과거 수량**: 그 농가의 다른 해 평균으로 예측하면
  전체 평균보다 나쁩니다. 작년에 잘 된 농가가 올해도 잘 된다고 보기 어렵습니다.
- **시군 기상 변수**: 예측력을 더하지 않았습니다.
- **복잡한 모형**: 변수를 다 넣으면 오히려 나빠집니다.
  변수 2~3개의 단순 회귀가 가장 낫습니다.
""")
        st.warning(f"**연도별 편향** — 8월 말 모형의 연도별 평균 편향은 {EARLY_CHECK['편향범위']}입니다. "
                   "수확이 늦게까지 이어진 2025년은 과소 예측되었습니다. 조사 종료일이 해마다 달라"
                   "(2023년 9/11~10/16, 2025년 10/20~10/27) \"최종 수확량\"의 일부는 작물이 아니라 조사 일정에 좌우됩니다.")

        st.markdown("### 6. 위성은 시군 평균이 아니라 포장 단위에서 작황을 잡는다")
        c1, c2 = st.columns([1.2, 1])
        with c1:
            st.markdown(f"""
| 비교 | 결과 |
|---|---|
| 시군 농경지 평균 식생지수 ↔ 시군 단수 | 관계 없음 (49개 변수 중 우연 수준) |
| 조사포장 8~9월 NDVI 0.1 ↔ 주당 수확량 | **+{SAT['NDVI']:.0f}g** (p={SAT['NDVIp']}, 17농가 71행, 농가·연도 고정효과) |
| 조사포장 8~9월 NDRE 0.1 ↔ 주당 수확량 | **+{SAT['NDRE']:.0f}g** (p={SAT['NDREp']}) |
| 농가 / 연도를 하나씩 빼고 다시 추정 | {SAT['농가제외']} / {SAT['연도제외']} |
| 8~9월 NDVI ↔ 8월 말 생육량 지수 | 같은 농가·연도 안에서 r = {SAT['생육량r']} |
| 착과 전 고온 → NDVI | 변화 없음 (p={SAT['고온NDVIp']}), NDVI를 통제해도 고온 효과 {SAT['고온남음']}% 남음 |

Sentinel-2(10m)로 조사포장 필지 경계 안 값을 뽑았습니다(2018~2026, 94 농가-연도).
""")
        with c2:
            st.markdown("""
**읽는 법**

- 시군 평균이 안 맞는 것은 농경지 대부분이 벼라서입니다(고추 비중 2~25%).
- 포장 단위로 보면 잎이 무성한 해에 수량이 많고, 그 경로는 **과실 수**입니다. 9개 연도 모두 같은 방향입니다.
- 위성은 8월 말 현장 생육조사와 거의 같은 정보를 담습니다. 조사하지 않은 포장에도 쓸 수 있는 **보조 지표**입니다.
- 그해 다른 농가 수준을 알면 8월 말부터 농가 간 순위 오차를 7~11% 줄이지만(NDRE가 더 큼), 단독 수량 예측 도구로는 부족합니다.
""")

        st.markdown("### 7. 병해충 다발 위험 기준은 작황조사로 검증해서 정했다")
        hp4 = find_file(["하반기"], ".xlsx")
        vrows = []
        if hp4 is not None:
            _skip = ("예천군",) if yecheon_substitute else ()
            _j = season_table(wx, PEST_TH, _skip, VALID_END).join(survey_rates(load_survey(hp4)), how="inner")
            for k, _, oname in VALID_PAIRS:
                if oname in _j.columns:
                    r, _, n = within_fit(_j[k], _j[oname], _j.index.get_level_values(0))
                    vrows.append({"기상 지표": IND[k]["name"], "검증 창 (조사 전)": valid_window(k),
                                  "작황조사 결과": oname, "상관계수": round(r, 2), "사례 수(시군×연도)": n,
                                  "다발 위험 기준": PEST_RULES[k]["rule"]})
        if vrows:
            show_table(pd.DataFrame(vrows), hide_index=True)
        st.markdown("""
- 하반기 작황조사(7월 말~8월 초) **전의 날씨만** 써서 검증했습니다. 시즌 전체로 세면 상관이 더 높게 나오지만
  조사 뒤 날씨가 섞인 값이라 쓰지 않습니다.
- 탄저병: 6/15~7/31 비 온 날 20일 이상인 해의 발생 포장 비율은 28.1%로 그렇지 않은 해(8.7%)의 약 3배였고,
  시군 평년보다 뚜렷이 많았던 8사례 중 7사례를 잡았습니다. 기준을 넘은 해의 절반가량은 평년 수준이어서
  **예찰·방제 강화 신호**로 씁니다.
- 누적 기간 1~14일, 기준량 1~200mm의 50개 강우 지표 중 비 온 날 수보다 일관되게 나은 지표는 없었습니다.
  **큰비의 횟수보다 비가 자주 오는 정도**가 탄저병과 맞습니다.
- 같은 해에는 시군 날씨가 비슷하게 움직여 독립 정보는 약 9년치입니다. 경향으로 읽고, 인과로 단정하지 않습니다.
""")

        st.markdown("### 8. 이 앱에서 지금 할 수 있는 것")
        st.markdown("""
| 탭 | 하는 일 | 쓰는 사람 |
|---|---|---|
| 오늘의 진단 | 기준일에 맞춰 착과 전 고온·탄저병·담배나방·석회결핍 판정, 남은 기간 전망, 할 일, 보고용 요약 | 농가, 지도사 |
| 생육기 기상 위험 진단 | 올해 기상을 평년과 비교. 일사량 × 강수량 보완관계, 가을 기온으로 본 수확 종료 시기 | 지도사, 연구자 |
| 병해충 발생 위험·평년 | 다발 위험 판정 근거, 시군별 평년 발생 포장 비율, 그해 작황조사와 평년 비교 | 지도사 |
| 기상 시나리오 | 남은 기간이 과거 각 해처럼 흘러가면, 기온이 오르면, 기상청 SSP 전망으로 2030~2090년대 위험일 | 지도사, 정책 담당 |
| 내 포장 비교 | 내 포장 생육이 같은 지역 조사포장 중 어디쯤인지 (재배법·관수 방식별) | 농가, 지도사 |
| 수확량 조기예측 | 8월 말~9월 초 생육조사로 주당 수확량 예측 (평균 오차 12.6%) | 지도사, 연구자 |
| 작황조사 대시보드 | 상반기→하반기 생육·병해충 흐름을 시군·읍면·연도별로 | 연구자 |
| 자료 품질 점검 | 생산량 통계·기상 관측의 불연속을 자동으로 찾아냄 | 연구자, 통계 담당 |
""")

        st.markdown("### 9. 조사 체계 개선 제안")
        st.markdown("""
1. **조사 종료일 통일** — 지금은 해마다 9월 11일부터 10월 27일까지 흩어져 있어, "최종 수확량"의 일부가
   조사 일정에 좌우됩니다.
2. **재식거리 조사 표준화** — 18농가 중 17농가에서 이랑폭·주간거리가 해마다 바뀝니다(농가내 CV 0.120).
   적정 재식밀도 추정이 불가능하고, 단수 통계의 잡음도 여기서 나옵니다.
3. **포장 온도 센서 조사 확대** — 착과 전 고온 효과는 포장 센서에서만 보입니다. 설치 표준(차광 기구 안 1.5m)을
   통일하면 관측소와의 차이에서 설치 편차를 걷어낼 수 있습니다.
4. **주 단위 생육조사 유지** — 2026년은 격주 조사여서 화분 형성기 고온과 착과의 시차를 나눠 볼 수 없었습니다.
5. **관수량 항목 표준 서식 편입** — 관수 횟수가 2024년부터만 조사되어 고온 완화 효과를 판단할 표본이 부족합니다.
6. **8월 말 착과수를 숙도별로 기록** — 적과·청과·소과 구분이 있으면 남은 수확량 추정이 가능해집니다.
7. **조사 서식 표준화** — 병해충 척도가 2023년에 백분율→등급으로 바뀌었고, 탄저병 조사 주수가
   10주에서 3주로 바뀌었으며(2023년은 조마다 다름), 시비량 결측 20~31%, 분지수 정의 불일치가 있습니다.
8. **기상 관측소 이력 관리** — 센서 교체·이전 시점을 기록하고, 이 앱의 자동 점검처럼 매년 불연속을 확인합니다.
9. **작황조사 포장 위치 기록** — 필지 주소(지번)만 남겨도 위성 식생지수를 포장 1,000개 이상으로 넓혀
   시군 단위 고추밭 작황을 다시 볼 수 있습니다.
""")


# ══════════════════════════════════════════════
# 탭: 사용 설명서
# ══════════════════════════════════════════════
MANUAL_QUICK = """
**처음 쓰신다면 이 순서로 보세요**

1. 왼쪽 **조건 선택**에서 시군과 연도를 고릅니다. 기준일을 바꾸면 그 날짜 시점의 진단이 나옵니다.
2. 첫 탭 **🗓️ 오늘의 진단**에서 지금 시기에 중요한 판정 네 가지와 할 일을 봅니다.
3. 시즌 중이라면 왼쪽 **📥 올해 기상자료 넣기**에 올해 일자료 CSV를 올려야 올해 진단이 됩니다.
4. 내 포장 생육을 재 왔다면 **내 포장 비교**와 **수확량 조기예측** 탭에 숫자를 넣어 봅니다.
"""

MANUAL_USES = """
**이 앱을 쓰는 세 가지 때**

| 언제 | 누가 | 무엇을 |
|---|---|---|
| 6월 중순~7월 말, 매주 | 지도사 | 올해 기상자료를 넣고 오늘의 진단 → 탄저병·석회결핍·담배나방이 기준에 다가가는지, 착과 전 고온이 평년보다 많은지 확인. 보고용 요약을 작황 보고나 문자 안내에 붙임 |
| 7월 31일 | 지도사, 연구소 | 세 가지 다발 위험 판정 확정 → 예찰·방제 강화 시군 안내. 6개 시군 같은 날 비교 |
| 8월 말~9월 초 | 조사 담당, 지도사 | 초장·착과수·8/31까지 수확량으로 최종 수확량 가늠 (평균 오차 12.6%) |

지난 해를 고르고 기준일을 당기면 그해 시즌 중에 이 앱이 무엇을 보여줬을지 그대로 재현됩니다. 발표·교육 때 쓰세요.
"""

MANUAL_TABS = [
    ("① 오늘의 진단", "지금 시기에 무엇을 봐야 하나?", """
**이럴 때 씁니다** — 시즌 중에 "지금 우리 시군은 괜찮은가, 무엇을 해야 하나"를 한 화면에서 보고 싶을 때.

**보는 법**
- 맨 위 **시기표**: 각 판정을 언제부터 언제까지 세는지와 기준일(빨간 점선)이 나옵니다.
- **판정 카드 네 장**
  - 착과 전 고온(7/3~7/28, 관측소 최고 33℃ 이상 — 포장 센서 34℃ 상당): 평년보다 많으면 감수 범위(1일당 0.5~3.2%)를 함께 보여줍니다.
  - 탄저병(6/15~7/31 비 온 날 20일 이상), 담배나방(6/1~7/31 30℃ 이상 35일 이상), 석회결핍(5/1~7/31 비다운 비 15일 이하): 7월 31일에 확정되는 다발 위험 판정입니다.
- 집계 중이면 **"남은 기간이 과거 각 해처럼 흐르면 9개 해 중 몇 개 해에서 기준을 넘는지"**가 나옵니다. 절반 이상이면 🟠입니다.
- **지금 할 일**: 기준일과 판정에 맞춰 바뀝니다. 고추재배전서 근거와 이 연구 결과만 적었습니다.
- **내 포장 온도계로 보기**: 포장에서 직접 센 34℃ 이상 일수를 넣으면 포장 기준으로 다시 판정합니다.
- **6개 시군 같은 날 비교**, **보고용 요약**(복사하거나 내려받기).

**주의** — 다발 위험은 '다발 확정'이 아니라 예찰·방제 강화 신호입니다. 기준을 넘은 해의 절반가량은 평년 수준이었습니다.
"""),
    ("② 생육기 기상 위험 진단", "올해 날씨가 고추에 위험한 쪽인가?", """
**이럴 때 씁니다** — 올해 날씨를 평년과 자세히 비교하고 싶을 때.

**보는 법**
- 맨 위 **카드 다섯 장**은 시즌 전체(9월까지) 위험 일수입니다. 화살표 숫자는 평년과의 차이입니다.
- 🔴 평년보다 나쁨 · 🟡 평년 수준 · 🟢 평년보다 좋음. 평년 평균에서 1표준편차 넘게 벗어나면 색이 바뀝니다.
- 왼쪽 **위험일 기준값 조정**으로 기준을 바꿔 볼 수 있습니다(다발 위험 판정 기준은 바뀌지 않음).

| 카드 | 무엇을 세나 | 왜 보나 |
|---|---|---|
| 착과 전 고온일 | 7/3~7/28 최고 33℃ 이상인 날 (포장 34℃ 상당) | 이 시기 고온이 과실 수를 줄임 (이 연구의 핵심 결과) |
| 탄저병 위험 | 6/15~9/30 비 1mm 이상 온 날 | 탄저병은 기온보다 비 온 날 수를 따라감 |
| 고온일 | 6~8월 최고 30℃ 이상인 날 | 화분 이상으로 착과 불량 |
| 저온일 | 6~8월 최저 13℃ 이하인 날 | 야간 저온으로 단위결과 |
| 가뭄 | 5~8월 비 5mm 이상 온 날 | **적을수록** 가뭄. 석회결핍과 연결 |

- **착과 전 고온 참고 영향**: 평년보다 늘어난 고온일만큼 수량이 줄어드는 범위입니다. 하한은 시군 단수 결과(1일당 약 0.5%), 상한은 포장 센서 결과(1일당 3.2%)입니다.
- **✅ 작황조사로 검증** 칸: 조사 전(7월 31일까지) 날씨 구간별로 실제 발생 포장 비율이 얼마였는지 보여줍니다.
- **🍂 수확 종료 시기** 칸: 가을에 일평균기온이 처음 12℃ 이하로 내려간 날입니다. 농가는 보통 이 날보다 5일쯤 먼저 수확을 끝냈습니다.

**주의** — 시군 관측소 자료라서 내 포장의 실제 기온과는 다릅니다. 농가 포장 센서는 관측소보다 착과 전 평균최고기온이 1℃쯤 높아서, 이 앱은 관측소 자료로 셀 때 33℃ 이상 일수(포장 34℃ 상당)를 씁니다. 포장이 낮은 곳에 있을수록 더 덥습니다(해발 100m 낮으면 착과 전 34℃ 이상 일수 약 2일 증가).
"""),
    ("③ 병해충 발생 위험·평년", "올해 탄저병·담배나방·석회결핍이 많을까?", """
**이럴 때 씁니다** — 7월 말에 다발 위험을 판정하고, 우리 시군의 평년 발생 수준을 알고 싶을 때.

- **다발 위험 판정 표**: 오늘의 진단 카드와 같은 기준입니다. 영농기술정보와 같은 고정 기준입니다.
- **시기별 활용 절차**: 5월부터 수확 후까지 언제 무엇을 보는지 정리했습니다.
- **조사 전 날씨 구간별 실제 발생 포장 비율**: 작황조사 파일로 그 자리에서 계산합니다.
- **시군별 평년 발생 포장 비율**: 하반기 6종, 상반기 5종.
- **그해 작황조사와 평년**: 수확 뒤 그해 발생이 평년보다 많았는지 확인합니다(평년 ± 1표준편차, 5%p 이상 차이일 때만 많음·적음).
"""),
    ("④ 기상 시나리오", "앞으로 남은 기간은 어떻게 될 수 있나?", """
**이럴 때 씁니다** — 7월 말쯤 "이대로 가면 어떻게 될까", "더워지면 어떻게 되나"가 궁금할 때.

**① 남은 기간 시나리오**
- 기준일까지는 실제 날씨, 그 뒤는 **과거 각 해의 날씨가 그대로 반복된다고 가정**해 9~10개 경우를 만듭니다.
- 파란 점 하나가 한 경우입니다. 점에 마우스를 올리면 몇 년 날씨인지 나옵니다.
- 지난 해를 고르면 빨간 마름모(실제 결과)와 맞춰볼 수 있습니다.

**② 극한 기온 시나리오**
- 과거 날씨에 기온을 몇 도 더하거나 비를 늘리고 줄여서 위험일이 얼마나 변하는지 봅니다.
- **예보가 아니라 민감도**입니다. "2℃ 더워지면 고온일이 이만큼 는다"로 읽으세요.

**③ 미래 기후 (기상청 SSP 시나리오)**
- 기상청 기후변화 시나리오로 **2030년대~2090년대**의 위험일을 봅니다.
- 시군·월마다 기상청이 전망한 만큼만 우리 관측 날씨에 더합니다. ②처럼 모든 날에 같은 값을 더하는 것보다 현실적입니다.
- **주의**: 월 평균 변화만 반영해서 극단 고온의 증가는 덜 잡힙니다. 비 오는 날 수의 변화도 들어가지 않습니다.
"""),
    ("⑤ 내 포장 비교", "내 고추가 다른 포장보다 큰 편인가?", """
**이럴 때 씁니다** — 내 포장 생육을 재 와서 같은 지역 다른 포장과 비교해 보고 싶을 때.

**쓰는 법**
1. 조사 시기(상반기 5월 말 / 하반기 7월 말)를 고릅니다.
2. 비교 대상(같은 시군 / 6개 시군 전체), 재배법, 관수 방식을 고릅니다.
3. 측정한 날과 초장·주경장·분지수(하반기는 착과수까지)를 넣습니다.

**보는 법**
- P10/중앙값/P90과 함께 **위치**를 알려줍니다(P10 미만 = 10곳 중 하위 1곳 수준, P90 초과 = 상위 1곳 수준). 회색 막대는 다른 포장들, 파란 선이 내 포장입니다.
- 크다고 좋은 것은 아닙니다. 5월 말 크기는 같은 농가 안에서 수량과 관계가 보이지 않았습니다.
- 재는 방법은 "📏 재는 방법" 칸에 있습니다. 작황조사 시기와 10일 넘게 차이 나면 경고가 뜹니다.
"""),
    ("⑥ 수확량 조기예측", "지금 생육으로 보면 수확량이 얼마쯤?", """
**이럴 때 씁니다** — 8월 말~9월 초에 생육을 재고 최종 수확량을 미리 가늠해 보고 싶을 때.

**쓰는 법**
1. 예측 시점을 고릅니다. 기본은 **8월 말**입니다(가장 정확).
2. **그 시점에 잰** 초장·착과수와 8월 31일까지 주당 수확량을 넣습니다. 시즌 중 가장 클 때의 초장이 아닙니다.
3. 주당 수확량(g)이 나옵니다. 재식주수를 넣으면 10a당으로도 환산합니다(참고용).

**보는 법**
- 8월 말 평균 오차 12.6%, 같은 식으로 2026년을 미리 예측했을 때 8.2%였습니다. 6월 말·7월 말은 22% 안팎이라 참고만 하세요.
- "평균적으로 ±12.6% 빗나갑니다"는 평균이 그렇다는 뜻입니다. 그보다 더 빗나가는 해도 있습니다.
- **조사포장 기준**의 예측입니다. 농가가 실제로 판 양과는 다를 수 있습니다.

**② 생육량 지수** 보기는 같은 포장에서 생육이 좋았던 해에 수량·과실 수·과중이 얼마나 달라졌는지 보여줍니다.
"""),
    ("⑦ 작황조사 대시보드", "작황조사 전체 흐름을 한눈에", """
- 상반기→하반기 생육과 병해충 흐름을 시군·읍면·연도별로 봅니다.
- 따로 만든 대시보드를 그대로 띄운 것이라, 안에서 필터를 바꾸면 됩니다.
"""),
]

MANUAL_TERMS = """
| 용어 | 뜻 |
|---|---|
| 평년 | 선택한 해를 뺀 나머지 해(2016년 이후)의 평균 |
| 표준편차 | 해마다 얼마나 들쭉날쭉한지. 평년 ± 1표준편차 안이면 "평년 수준" |
| 다발 위험 | 작황조사 전(7월 31일까지) 날씨가 고정 기준을 넘은 상태. 발생 확정이 아니라 예찰·방제 강화 신호 |
| 기준일 | 이 날까지의 날씨로 진단. 지난 해에 기준일을 당기면 그해 시즌 중 상황을 재현 |
| 포장 평년 | 포장 센서 34℃ 일수의 평년. 관측소 33℃ 일수의 평년과 평균이 같아 그 값을 그대로 씀 |
| 감수 범위 | 평년보다 늘어난 착과 전 고온일만큼 수량이 줄어드는 범위. 1일당 하한 0.5%, 상한 3.2% |
| 백분위·상위 % | 100개 포장을 줄 세웠을 때의 위치. 상위 20% = 앞에서 20번째쯤 |
| 시군 평균을 뺀 상관 | 시군마다 원래 수준이 다른 것을 빼고, 해마다 같이 오르내리는지만 본 값. +1에 가까울수록 같이 움직임 |
| 착과 전 창 | 7월 3일~28일. 주 착과기(7/20~8/10) 13~17일 전, 화분이 만들어지는 시기 |
| 델타 방법 | 과거 날씨에 기온을 일정하게 더해 "더워지면 어떻게 되나"를 보는 방법 |
| SSP 시나리오 | IPCC 6차 보고서의 기후변화 시나리오. SSP2-4.5는 중간, SSP5-8.5는 지금처럼 배출하는 고탄소 경로 |
| 청천지수 | 실제 일사량 ÷ 대기 밖 일사량. 0.80을 넘으면 관측 오류 |
| 연도 고정효과 | 그해 모든 지역에 공통인 영향(전국적인 날씨 등)을 빼고 본다는 뜻 |
| WCR p | 농가 수가 적을 때 쓰는, 더 믿을 만한 p값 계산법 |
| 유의 (이 앱의 기준) | p가 0.05보다 작으면 "유의". 0.05~0.10은 "경계 수준"으로 따로 적고, 참고 결과로 봄 |
| 조사포장 수확량 | 조사 시료로 환산한 수확량. 농가 실제 판매량과 다를 수 있음 |
| 조사 전 창 | 하반기 작황조사(7월 말~8월 초) 전까지의 날씨. 기상 지표를 작황조사로 검증할 때 이 기간만 씀 |
| NDVI·NDRE | 위성으로 본 잎의 무성한 정도. 높을수록 잎이 많고 푸름 |
"""

MANUAL_FAQ = """
**Q. 올해 기상 자동 갱신(API)은 어떻게 켜나요?**
기상청 API허브(apihub.kma.go.kr)에 회원가입하고 마이페이지에서 인증키를 발급받습니다. 내 컴퓨터에서는
app.py 폴더 안에 `.streamlit` 폴더를 만들고, 그 안에 `secrets.toml` 파일을 만들어
`KMA_API_KEY = "발급받은 키"` 한 줄을 적습니다(따옴표 포함). Streamlit Cloud에 올린 앱은
share.streamlit.io의 앱 관리 화면 → Settings → Secrets에 같은 줄을 넣습니다.
키가 있으면 앱이 열릴 때 기본 자료 이후의 올해 일자료를 자동으로 받아오고, 6시간마다 다시 받습니다.
**키가 든 파일은 GitHub에 올리면 안 됩니다.**

**Q. 올해 진단이 안 나오고 작년 것만 보여요.**
기본 기상 파일에 올해 자료가 없기 때문입니다. 기상자료개방포털(data.kma.go.kr)에서 우리 시군 지점의 일자료를
CSV로 내려받아 왼쪽 **📥 올해 기상자료 넣기**에 올리세요. ASOS(안동·봉화·의성·청송군)와 AWS(영양·예천 등)
모두 됩니다. 앱 폴더에 이름에 `올해기상`이 들어간 CSV로 두면 매번 올리지 않아도 됩니다.

**Q. 올린 자료로 본 판정은 믿을 만한가요?**
평년(2016년 이후)은 농업기상 관측망 자료입니다. 기상청 ASOS·AWS 자료를 넣으면 지점 위치 차이만큼 일수가
조금 다를 수 있습니다. 경계에 걸친 판정(기준 ± 1~2일)은 보수적으로 읽으세요.

**Q. 화면이 검은 바탕으로 나와요.**
컴퓨터가 다크 모드라서 그렇습니다. 오른쪽 위 ⋮ → Settings → Theme에서 Light를 고르세요.

**Q. 처음 화면에 "CSV를 올려주세요"가 떠요.**
기상 파일을 못 찾은 것입니다. app.py와 같은 폴더에 이름에 `농업기상_6개지역_정제본`이 들어간 CSV가 있는지 확인하세요.

**Q. 일사량 구성에 "ASOS 파일을 찾지 못해"가 떠요.**
이름에 `ASOS`가 들어간 일자료 CSV를 app.py 폴더에 넣으면 안동·예천 일사량이 최종 구성으로 바뀝니다.
없어도 다른 기능은 다 됩니다.

**Q. 숫자가 결과보고서와 조금 달라요.**
화면은 넣어 둔 자료로 그 자리에서 계산합니다. 자료 파일 판이 다르면 조금 다를 수 있습니다.
연구 결과 계수는 2026년 11월 9일 분석 기준입니다.

**Q. 이 앱으로 올해 수확량을 정확히 맞힐 수 있나요?**
아닙니다. 기상은 위험 신호로, 생육 조사는 범위로 보여줍니다. 시군 관측소 기상은 수확량 예측력을 더하지 않았습니다.
"""

MANUAL_FILES = """
**app.py와 같은 폴더에 두는 파일** (이름 앞뒤에 ♥♡ 같은 기호가 붙어도 됩니다)

| 파일 | 이름에 들어가야 하는 말 | 없으면 |
|---|---|---|
| 농업기상 정제본 CSV | `농업기상_6개지역_정제본` | 앱이 시작하지 않고 업로드 창이 뜸 |
| 올해 기상 일자료 CSV | `올해기상` | 왼쪽에서 올리면 됨 (없으면 지난 해까지만 진단) |
| ASOS 일자료 CSV | `ASOS` | 안동·예천 일사량이 원값 그대로 |
| 상반기 작황조사 xlsx | `상반기` | 내 포장 비교(상반기), 상반기 평년 발생 안 됨 |
| 하반기 작황조사 xlsx | `하반기` | 내 포장 비교(하반기), 지표 검증, 평년 발생 안 됨 |
| 생산량 CSV | `생산량` | 자료 품질 점검 ①에서 업로드 창이 뜸 |
| 기후전망 CSV | `SSP` | 기상 시나리오 ③(미래 기후)이 안 열림 |
| 대시보드 HTML | `대시보드` | 대시보드 탭이 비어 있음 |
| `자료실` 폴더 안 PDF | (아무 이름) | 자료실 버튼이 안 생김 |

같은 종류 파일이 두 개 있으면 이름순으로 첫 번째를 씁니다. 종류마다 하나씩만 두세요.
(`올해기상` 파일은 여러 개 둬도 모두 읽습니다. 시군별로 따로 둬도 됩니다.)

**실행**: Anaconda Prompt에서 `cd /d "폴더 주소"` → `streamlit run app.py`
**끄기**: Anaconda Prompt 창에서 Ctrl + C
**기준값 바꾸기**: app.py 맨 위 `HEAT_PRE`, `MODEL_EARLY`, `PEST_RULES` 같은 상수에 연구 계수가 모여 있습니다. 보고서 수치가 바뀌면 여기만 고치면 됩니다.
"""


# ── 설명서 내려받기용 변환 (앱 화면과 같은 글을 Word·HTML로) ──

def _md_blocks(md):
    """설명서에 쓴 간단한 마크다운을 블록 목록으로 나눔: 제목, 문단, 글머리, 번호, 표"""
    blocks, para, table = [], [], []

    def flush():
        if para:
            blocks.append(("p", para[:]))
            para.clear()
        if table:
            rows = [[c.strip() for c in r.strip().strip("|").split("|")] for r in table
                    if not re.match(r"^\s*\|?\s*:?-{3,}", r)]
            blocks.append(("table", rows))
            table.clear()

    for line in md.strip("\n").split("\n"):
        t = line.strip()
        if t.startswith("|"):
            if para:
                blocks.append(("p", para[:]))
                para.clear()
            table.append(t)
            continue
        if table:
            flush()
        if not t:
            flush()
        elif t.startswith("### "):
            flush()
            blocks.append(("h", t[4:]))
        elif t.startswith("- "):
            flush()
            blocks.append(("li", t[2:]))
        elif re.match(r"^\d+\. ", t):
            flush()
            blocks.append(("ol", t))
        elif line.startswith("  ") and blocks and blocks[-1][0] in ("li", "ol"):
            blocks[-1] = (blocks[-1][0], blocks[-1][1] + " " + t)
        else:
            para.append(t)
    flush()
    return blocks


def _manual_sections():
    secs = [("빠른 시작", MANUAL_QUICK), ("언제 쓰나", MANUAL_USES)]
    for title, question, body in MANUAL_TABS:
        secs.append((f"{title} — {question}", body))
    secs += [("용어 풀이", MANUAL_TERMS), ("자주 묻는 질문", MANUAL_FAQ),
             ("파일 준비와 실행 (관리자용)", MANUAL_FILES)]
    return secs


MANUAL_NOTE = "이 설명서는 앱 화면 기준으로 작성했습니다."
MANUAL_TITLE = "고추 쑥쑥이 사용 설명서"


def _inline_html(t):
    t = _html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", t)


@st.cache_data(show_spinner=False)
def manual_html():
    out = []
    for i, (sec, md) in enumerate(_manual_sections()):
        out.append(f"<h2>{_html.escape(sec)}</h2>")
        for kind, val in _md_blocks(md):
            if kind == "h":
                out.append(f"<h3>{_inline_html(val)}</h3>")
            elif kind == "p":
                out.append("<p>" + "<br>".join(_inline_html(x) for x in val) + "</p>")
            elif kind in ("li", "ol"):
                out.append(f'<p class="{kind}">' + ("• " if kind == "li" else "") + _inline_html(val) + "</p>")
            elif kind == "table":
                rows = "".join("<tr>" + "".join((f"<th>{_inline_html(c)}</th>" if r == 0 else
                                                f"<td>{_inline_html(c)}</td>") for c in row) + "</tr>"
                               for r, row in enumerate(val))
                out.append(f"<table>{rows}</table>")
    css = ("body{font-family:'Pretendard','Malgun Gothic','맑은 고딕',sans-serif;color:#1F1B18;background:#FAF8F5;"
           "max-width:860px;margin:32px auto;padding:0 20px;line-height:1.65;font-size:15px}"
           "h1{color:#9C3F30;font-size:26px;border-bottom:3px solid #9C3F30;padding-bottom:8px}"
           "h2{color:#9C3F30;font-size:19px;margin-top:34px;border-left:5px solid #B8604A;padding-left:10px}"
           "h3{font-size:16px}p{margin:6px 0}p.li,p.ol{margin:3px 0 3px 14px}"
           "table{border-collapse:collapse;width:100%;margin:10px 0;background:#fff}"
           "th,td{border:1px solid #E8E1D8;padding:6px 9px;text-align:left;vertical-align:top}"
           "th{background:#F3EEE7}code{background:#F3EEE7;padding:1px 5px;border-radius:4px}"
           ".note{color:#6B6560;font-size:13px;margin-top:30px}"
           "@media print{body{background:#fff;margin:0}h2{break-after:avoid}table{break-inside:avoid}}")
    return ("<!doctype html><html lang='ko'><head><meta charset='utf-8'>"
            f"<title>{MANUAL_TITLE}</title><style>{css}</style></head><body>"
            f"<h1>{MANUAL_TITLE}</h1><p class='note'>경상북도농업기술원 영양고추연구소 · 고추 생산 변동 요인 분석</p>"
            + "".join(out) + f"<p class='note'>{MANUAL_NOTE}</p></body></html>").encode("utf-8")


@st.cache_data(show_spinner=False)
def manual_docx():
    """python-docx가 있으면 Word 파일, 없으면 None"""
    try:
        from docx import Document
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.oxml.ns import qn
        from docx.shared import Pt, RGBColor
    except ImportError:
        return None
    red = RGBColor(0x9C, 0x3F, 0x30)
    doc = Document()
    for name in ["Normal", "Heading 1", "Heading 2", "Heading 3", "Title"]:
        stl = doc.styles[name]
        stl.font.name = "맑은 고딕"
        stl.element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), "맑은 고딕")
    doc.styles["Normal"].font.size = Pt(10.5)

    def runs(par, text, size=None, bold=False):
        for j, piece in enumerate(re.split(r"(\*\*.+?\*\*|`.+?`)", text)):
            if not piece:
                continue
            if piece.startswith("**") and piece.endswith("**"):
                r = par.add_run(piece[2:-2])
                r.bold = True
            elif piece.startswith("`") and piece.endswith("`"):
                r = par.add_run(piece[1:-1])
                r.font.color.rgb = red
            else:
                r = par.add_run(piece)
                r.bold = bold or None
            if size:
                r.font.size = Pt(size)

    h = doc.add_heading(MANUAL_TITLE, level=0)
    for r in h.runs:
        r.font.color.rgb = red
    doc.add_paragraph("경상북도농업기술원 영양고추연구소 · 고추 생산 변동 요인 분석")
    for sec, md in _manual_sections():
        hh = doc.add_heading(sec, level=1)
        for r in hh.runs:
            r.font.color.rgb = red
        for kind, val in _md_blocks(md):
            if kind == "h":
                doc.add_heading(val, level=2)
            elif kind == "p":
                par = doc.add_paragraph()
                for k, x in enumerate(val):
                    if k:
                        par.add_run().add_break()
                    runs(par, x)
            elif kind == "li":
                runs(doc.add_paragraph(style="List Bullet"), val)
            elif kind == "ol":
                runs(doc.add_paragraph(), val)
            elif kind == "table":
                ncol = max(len(r) for r in val)
                tb = doc.add_table(rows=len(val), cols=ncol)
                tb.style = "Table Grid"
                tb.alignment = WD_TABLE_ALIGNMENT.CENTER
                for ri, row in enumerate(val):
                    for ci in range(ncol):
                        cell = tb.cell(ri, ci)
                        cell.text = ""
                        runs(cell.paragraphs[0], row[ci] if ci < len(row) else "", size=9.5, bold=(ri == 0))
                doc.add_paragraph()
    note = doc.add_paragraph()
    runs(note, MANUAL_NOTE, size=9)
    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


with tab_man:
    st.subheader("사용 설명서")

    d1, d2, _ = st.columns([1, 1.35, 3.2])
    word = manual_docx()
    if word is not None:
        d1.download_button("⬇️ Word 파일로 내려받기", data=word, file_name="고추쑥쑥이_사용설명서.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           key="dl_man_docx")
    d2.download_button("⬇️ 웹 문서로 내려받기 (인쇄·PDF용)", data=manual_html(),
                       file_name="고추쑥쑥이_사용설명서.html", mime="text/html", key="dl_man_html")
    st.caption("웹 문서는 인터넷 창에서 열리고, Ctrl + P → 'PDF로 저장'을 고르면 PDF가 됩니다."
               + ("" if word is not None else
                  " Word 버튼은 python-docx가 설치돼 있어야 보입니다(Anaconda Prompt에서 pip install python-docx)."))

    st.info(MANUAL_QUICK)
    try:
        _uses_box = st.container(key="uses_tbl")   # CSS로 '누가' 칸 줄바꿈 방지
    except TypeError:                              # 예전 Streamlit
        _uses_box = st.container()
    with _uses_box:
        st.markdown(MANUAL_USES)

    st.markdown("### 탭별 안내")
    for title, question, body in MANUAL_TABS:
        with st.expander(f"{title} — {question}"):
            st.markdown(body)

    st.markdown("### 용어 풀이")
    st.markdown(MANUAL_TERMS)

    st.markdown("### 자주 묻는 질문")
    st.markdown(MANUAL_FAQ)

    st.markdown("### 파일 준비와 실행 (관리자용)")
    with st.expander("폴더에 넣을 파일, 실행 방법, 계수 고치는 곳"):
        st.markdown(MANUAL_FILES)

    st.caption(MANUAL_NOTE)
