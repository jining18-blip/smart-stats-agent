# -*- coding: utf-8 -*-
"""앱 전체를 AppTest로 돌려 화면 흐름을 확인한다 (홈 · 점검 알림 · 교차분석 · CV 경고).

로그인 설정(secrets)이 없으면 로그인 없이 열리므로 그대로 실행된다.
"""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def _run(data=None, menu=None, seen=True):
    at = AppTest.from_file(APP, default_timeout=300)
    if data is not None:
        at.session_state["files"] = {"d": data}
        at.session_state["cur_key"] = "d"
        at.session_state["df"] = data.copy()
        if seen:
            at.session_state["_checkup_seen"] = {"d"}
    if menu:
        at.session_state["menu_choice"] = menu
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def _md(at):
    return "\n".join([str(m.value) for m in at.markdown] + [str(c.value) for c in at.caption])


def _click(at, word):
    b = [x for x in at.button if word in str(x.label)]
    assert b, [x.label for x in at.button]
    b[0].click()
    at.run()
    assert not at.exception, [e.value for e in at.exception]


def test_home_shows_steps_and_menu_table():
    at = _run()
    md = _md(at)
    assert "처음 오셨나요" in md and "h-table" in md
    assert "📘 데이터 작성 가이드" in md
    assert "Version 2 열기" in md and "smart-stats-agent-v2.streamlit.app" in md   # Version 2 버튼
    assert "Version 1" in md                   # 사이드바 브랜드


def test_home_hint_when_menu_picked_without_data():
    at = _run()
    assert not any("먼저 왼쪽" in str(i.value) for i in at.info)      # 첫 화면·새로고침에는 없음
    at.run()
    assert not any("먼저 왼쪽" in str(i.value) for i in at.info)
    at.session_state["menu_choice"] = "📊 통계분석"
    at.run()
    assert any("먼저 왼쪽" in str(i.value) for i in at.info)


def _messy():
    return pd.DataFrame({"처리구": ["대조구", "대조구", "처리1", "처리1"],
                         "수량": ["600", "610kg", "650", "640"]})


def test_checkup_notice_reappears_when_same_name_changes():
    at = _run(_messy(), "⚡ 원클릭 분석", seen=False)
    assert "방금 불러온 'd' 데이터를 점검" in _md(at)
    _click(at, "확인했어요")
    assert "방금 불러온 'd' 데이터를 점검" not in _md(at)
    # 같은 이름으로 내용만 바뀐 파일을 다시 올린 상황
    fixed = _messy()
    fixed.loc[1, "수량"] = "615kg"
    at.session_state["files"] = {"d": fixed}
    at.session_state["df"] = fixed.copy()
    at.run()
    assert "방금 불러온 'd' 데이터를 점검" in _md(at)


def _survey():
    rng = np.random.default_rng(3)
    n = 60
    return pd.DataFrame({"응답자구분": rng.choice(["농가", "센터", "연구소"], n),
                         "선호기술": rng.choice(["관수", "방제", "통합"], n),
                         "Q1 만족도": rng.integers(1, 6, n)})


def test_crosstab_has_no_ratio_radio_and_explains_percent():
    at = _run(_survey(), "📋 설문조사 분석")
    r = at.radio(key="svy_type")
    r.set_value(r.options[5]).run()
    at.selectbox(key="ct_r").set_value("응답자구분").run()
    at.selectbox(key="ct_c").set_value("선호기술").run()
    _click(at, "교차분석 실행")
    labels = [str(x.label) for x in at.radio]
    assert not any("비율" in l and "기준" in l for l in labels), labels
    md = _md(at)
    assert "가로 합계 100%" in md
    assert any("다른 방향으로 보기" in str(e.label) for e in at.expander)
    assert "cap_ct" in at.session_state


def test_one_way_anova_warns_on_tiny_cv():
    d = pd.DataFrame({"처리구": np.repeat(["대조구", "처리1", "처리2"], 3),
                      "반복": np.tile([1, 2, 3], 3),
                      "수량": [600.0, 600.1, 600.0, 650.0, 650.1, 650.0, 700.0, 700.0, 700.1]})
    at = _run(d, "📊 통계분석")
    r = at.radio(key="stat_sub")
    r.set_value(r.options[1]).run()
    _click(at, "ANOVA 분석 실행")
    assert any("1% 미만" in str(w.value) or "너무 낮" in str(w.value) for w in at.warning), \
        [str(w.value)[:80] for w in at.warning]


def test_contact_shown_in_sidebar_and_manual():
    at = _run()
    side = " ".join(str(c.value) for c in at.sidebar.caption)
    assert "hyo99@korea.kr" in side and "영양고추연구소" in side and "이효진" in side
    at.session_state["menu_choice"] = "📖 사용설명서"
    at.run()
    assert "## 17. 문의" in _md(at) and "hyo99@korea.kr" in _md(at)
