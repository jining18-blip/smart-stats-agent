# -*- coding: utf-8 -*-
"""최종 점검에서 고친 오류들의 회귀 테스트.

- 대문자 확장자(.CSV) 파일도 CSV로 읽는다
- 원클릭 분석: 조사 시기·반복측정 자료 경고
- 자동 인지: 처리구에 따라 정해지는 글자 열(등급)을 두 번째 요인으로 보지 않는다
- 머신러닝: 작은 시험의 수량(소수)은 기본이 '회귀'
"""
from pathlib import Path
import re

import numpy as np
import pandas as pd
import pytest

APP = Path(__file__).resolve().parents[1] / "app.py"
_SRC = APP.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def design():
    ns = {"np": np, "pd": pd, "re": re}
    exec(_SRC[_SRC.index("_BLOCK_KEYS ="):_SRC.index("def _josa")], ns)
    return ns


def _rcbd(extra_grade=False):
    rows = []
    for b in (1, 2, 3):
        for t, e in [("대조구", 0), ("처리1", 25), ("처리2", 40), ("처리3", 10)]:
            r = {"처리구": t, "반복": b, "수량": 600.0 + e + b}
            if extra_grade:
                r["등급"] = "상" if e > 20 else "중"
            rows.append(r)
    return pd.DataFrame(rows)


def _repeated():
    return pd.DataFrame([{"개체": i, "처리": "A" if i <= 4 else "B", "시기": s, "초장": 20.0 + s * 8 + i}
                         for i in range(1, 9) for s in (1, 2, 3, 4)])


def test_csv_extension_checks_ignore_case():
    assert not re.search(r"\.name\.endswith\(\s*[\"']\.csv", _SRC)


def test_confounded_text_column_is_not_second_factor(design):
    res = design["detect_design"](_rcbd(extra_grade=True))
    assert res["design"].startswith("난괴법(RCBD")
    assert res["sub"] is None


def test_real_two_factor_design_still_detected(design):
    d = pd.DataFrame([{"반복": r, "질소": n, "품종": v, "수량": 500.0 + r}
                      for r in (1, 2, 3) for n in ("N0", "N1") for v in ("A", "B", "C")])
    res = design["detect_design"](d)
    assert res["design"].startswith("난괴법 요인배치")


def test_time_hint(design):
    hint = design["_v1_time_hint"]
    assert "반복측정" in hint(_repeated(), "처리")
    d = _rcbd()
    d = pd.concat([d.assign(조사시기="1차"), d.assign(조사시기="2차")], ignore_index=True)
    msg = hint(d, "처리구", "반복")
    assert msg and "조사시기" in msg and "반복측정 자료" not in msg
    assert hint(_rcbd(), "처리구", "반복") is None
    w = pd.DataFrame({"처리구": ["A", "B"] * 4, "width": [1, 2] * 4, "수량": range(8)})
    assert hint(w, "처리구") is None                    # 'width'의 id는 개체 열이 아님


# ---------------------------------------------------------------- 앱 화면
def _app(data, menu):
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(str(APP), default_timeout=300)
    at.session_state["files"] = {"d": data}
    at.session_state["cur_key"] = "d"
    at.session_state["df"] = data.copy()
    at.session_state["_checkup_seen"] = {"d"}
    at.session_state["menu_choice"] = menu
    at.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def test_oneclick_warns_on_repeated_measures():
    at = _app(_repeated(), "⚡ 원클릭 분석")
    assert any("반복측정" in str(w.value) for w in at.main.warning)
    at2 = _app(_rcbd(), "⚡ 원클릭 분석")
    assert not any("시기" in str(w.value) for w in at2.main.warning)


def _ml(at, target):
    at.radio(key="stat_sub").set_value("🤖 머신러닝 예측").run()
    at.selectbox(key="ml_y").set_value(target).run()
    return [r for r in at.main.radio if str(r.label) == "문제 유형"][0].value


def test_ml_small_trial_yield_defaults_to_regression():
    d = pd.DataFrame({"처리구": np.repeat(["대조구", "처리1", "처리2"], 3), "반복": np.tile([1, 2, 3], 3),
                      "초장": [70.1, 71.3, 69.8, 74.2, 75.0, 73.9, 78.4, 77.6, 79.1],
                      "수량": [600.5, 612.3, 605.1, 640.2, 633.8, 645.0, 680.4, 671.2, 690.7]})
    at = _app(d, "📊 통계분석")
    assert _ml(at, "수량").startswith("회귀")


def test_ml_grade_scores_default_to_classification():
    rng = np.random.default_rng(1)
    d = pd.DataFrame({"초장": rng.normal(70, 5, 60), "착과수": rng.normal(30, 3, 60),
                      "등급": rng.integers(1, 6, 60)})
    at = _app(d, "📊 통계분석")
    assert _ml(at, "등급").startswith("분류")


def test_admin_menu_opens_without_data():
    """데이터를 올리기 전에도 관리자 메뉴는 홈 화면이 아니라 관리자 화면이 떠야 한다."""
    guard = re.search(r"if df is None and menu not in \(([^)]*)\):", _SRC).group(1)
    assert "👑 관리자" in guard
