# -*- coding: utf-8 -*-
"""휴대폰 음성 입력 화면(?mode=voice) 검증.

음성 입력 구간만 잘라 AppTest로 돌리고, AI 전사·Firestore는 가짜로 바꾼다.
검증 범위: 열 이름 적용, 행 누적·계정별 저장·다른 기기에서 이어 불러오기,
마지막 행 취소, Claude 선택 시 음성 가능한 제공사로 전환, 전체 화면 복귀,
실시간 받아쓰기 부품이 보낸 행 반영(중복 없음·취소한 행이 되살아나지 않음).
"""
from pathlib import Path
import textwrap

import pytest

st_testing = pytest.importorskip("streamlit.testing.v1")
AppTest = st_testing.AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"
START = "# ================================================================ 휴대폰 음성 입력 전용 화면"
END = "# Firebase가 설정되고 AUTH_REQUIRED=true이면"


def _script():
    return textwrap.dedent(f'''
        import streamlit as st, pandas as pd, re, json
        S = st.session_state
        STORE = S.setdefault("_store", {{}})
        S.setdefault("_calls", [])

        _AI_PROVIDERS = {{
            "Claude (Anthropic)": {{"models": ["c1"], "key_hint": "c"}},
            "Gemini (Google)": {{"models": ["g1", "g2"], "key_hint": "g"}},
            "ChatGPT (OpenAI)": {{"models": ["o1"], "key_hint": "o"}},
        }}

        def ai_multimodal_text(binary, mime, prompt, kind="image"):
            return S.get("_tr", "")

        def voice_text_to_row(tr, cols):
            S["_calls"].append(("row", tr, list(cols)))
            vals = dict(re.findall(r"(\\S+) (\\S+)", tr))
            keys = cols or list(vals.keys())
            return {{k: vals.get(k) for k in keys}}, []

        _current_auth_user = lambda: {{"id": "u1", "email": "a@b.c"}}
        _fs_session = lambda: object()
        def _fs_set(col, doc, data):
            STORE.setdefault(col + "/" + doc, {{}}).update(data)
        def _fs_get(col, doc):
            return dict(STORE.get(col + "/" + doc) or {{}}) or None
        _now_utc = lambda: "2026-09-30T00:00:00Z"
        _record_usage = lambda action: S["_calls"].append(("usage", action))
        _ai_remember_widget = lambda: None
        dataframe_to_styled_xlsx = lambda df, *a, **k: b"x"
        clean_columns = lambda df: df

        _src = open({str(APP)!r}, encoding="utf-8").read()
        exec(_src[_src.index({START!r}):_src.index({END!r})])

        if "_live" in S:
            _voice_live_absorb(S.pop("_live"))

        if S.pop("_simulate", False):
            row, tr, warn = _voice_process(b"wav", "audio/wav")
            S["voice_transcript"] = tr
            if row is not None:
                S.setdefault("voice_rows", []).append(row)
                _voice_draft_save()

        if _is_voice_mode():
            render_voice_mode()
        else:
            st.write("FULL_APP")
    ''')


RECORD = "🎙️ 녹음 후 AI 정리"


def _app(store=None, way=None):
    at = AppTest.from_string(_script(), default_timeout=30)
    at.query_params["mode"] = "voice"
    if store is not None:
        at.session_state["_store"] = store
    if way:
        at.session_state["voice_m_way"] = way
    return at.run()


def _say(at, text):
    at.session_state["_tr"] = text
    at.session_state["_simulate"] = True
    return at.run()


def _rows(at):
    return at.session_state["voice_rows"]


def test_live_mode_is_default_and_needs_no_key():
    at = _app()
    assert not at.exception
    assert at.radio(key="voice_m_way").value.startswith("⚡")
    assert [t.key for t in at.text_input] == ["voice_cols_text"]   # API 키 칸 없음
    assert not at.expander                                        # 설정 펼침도 없음


def test_record_mode_renders_with_settings_open_when_no_key():
    at = _app(way=RECORD)
    assert not at.exception
    assert [t.key for t in at.text_input] == ["voice_cols_text", "api_key"]
    assert at.expander[0].proto.expanded                         # 키가 없으면 설정이 펼쳐짐


def test_claude_is_switched_to_audio_capable_provider():
    at = AppTest.from_string(_script(), default_timeout=30)
    at.query_params["mode"] = "voice"
    at.session_state["voice_m_way"] = RECORD
    at.session_state["ai_provider"] = "Claude (Anthropic)"
    at = at.run()
    assert at.selectbox(key="ai_provider").value == "Gemini (Google)"
    assert "Claude (Anthropic)" not in at.selectbox(key="ai_provider").options
    assert at.session_state["ai_model_g"] == "g1"


def test_typed_columns_are_used_for_every_row():
    at = _app()
    at.text_input(key="voice_cols_text").input("처리구, 반복, 수량").run()
    at = _say(at, "처리구 A 반복 1 수량 615.4")
    assert _rows(at) == [{"처리구": "A", "반복": "1", "수량": "615.4"}]
    assert at.session_state["_calls"][-1] == ("row", "처리구 A 반복 1 수량 615.4", ["처리구", "반복", "수량"])


def test_without_columns_later_rows_follow_first_row():
    at = _app()
    at = _say(at, "처리구 A 수량 600")
    at = _say(at, "처리구 B 수량 700 비고 좋음")
    assert at.session_state["_calls"][-1][2] == ["처리구", "수량"]
    assert list(_rows(at)[1].keys()) == ["처리구", "수량"]


def test_rows_are_saved_and_resume_on_another_device():
    at = _app()
    at.text_input(key="voice_cols_text").input("처리구, 수량").run()
    at = _say(at, "처리구 A 수량 600")
    at = _say(at, "처리구 B 수량 700")
    doc = at.session_state["_store"]["voice_drafts/u1"]
    assert doc["count"] == 2 and doc["columns"] == "처리구, 수량"

    other = _app(store=at.session_state["_store"])                 # 새 기기/새 세션
    assert len(_rows(other)) == 2
    assert other.text_input(key="voice_cols_text").value == "처리구, 수량"
    assert any("2행" in m.value for m in other.markdown)


def test_undo_last_row_updates_saved_draft():
    at = _app()
    at = _say(at, "처리구 A 수량 600")
    at = _say(at, "처리구 B 수량 700")
    at = at.button(key="voice_m_undo").click().run()
    assert [r["처리구"] for r in _rows(at)] == ["A"]
    assert at.session_state["_store"]["voice_drafts/u1"]["count"] == 1


def test_back_to_full_app():
    at = _app()
    at = at.button(key="voice_m_full").click().run()
    assert any("FULL_APP" in str(m.value) for m in at.markdown)


# ---------------------------------------------------------------- 실시간 받아쓰기
def _live(at, sid, rows):
    """부품이 보낸 값(누적 행)을 흉내 낸다."""
    at.session_state["_live"] = {"sid": sid, "rows": rows}
    return at.run()


def test_live_rows_are_added_once_and_saved():
    at = _app()
    at.text_input(key="voice_cols_text").input("처리구, 수량").run()
    r1 = {"처리구": "A", "수량": 600}
    r2 = {"처리구": "B", "수량": 700, "덤": 1}               # 열 밖 값은 버림
    at = _live(at, "s1", [r1])
    at = _live(at, "s1", [r1, r2])                          # 누적으로 다시 보내도
    at = _live(at, "s1", [r1, r2])                          # 같은 값이 또 와도
    assert _rows(at) == [{"처리구": "A", "수량": 600}, {"처리구": "B", "수량": 700}]
    assert at.session_state["_store"]["voice_drafts/u1"]["count"] == 2
    assert ("usage", "음성 입력(실시간)") in at.session_state["_calls"]


def test_live_undo_and_clear_do_not_bring_rows_back():
    at = _app()
    at = _live(at, "s1", [{"처리구": "A", "수량": 600}, {"처리구": "B", "수량": 700}])
    at = at.button(key="voice_m_undo").click().run()
    at = _live(at, "s1", [{"처리구": "A", "수량": 600}, {"처리구": "B", "수량": 700}])
    assert [r["처리구"] for r in _rows(at)] == ["A"]
    at = _live(at, "s1", [{"처리구": "A", "수량": 600}, {"처리구": "B", "수량": 700},
                          {"처리구": "C", "수량": 800}])
    assert [r["처리구"] for r in _rows(at)] == ["A", "C"]


def test_live_new_session_id_counts_from_zero():
    """페이지를 새로 열어 부품이 다시 시작되면(새 sid) 그 행도 빠짐없이 들어온다."""
    at = _app()
    at = _live(at, "s1", [{"처리구": "A"}])
    at = _live(at, "s2", [{"처리구": "B"}])
    assert [r["처리구"] for r in _rows(at)] == ["A", "B"]


def test_live_without_columns_follows_first_row():
    at = _app()
    at = _live(at, "s1", [{"처리구": "A", "수량": 600}, {"처리구": "B", "수량": 700, "비고": "좋음"}])
    assert list(_rows(at)[1].keys()) == ["처리구", "수량"]


def test_live_ignores_bad_values():
    at = _app()
    for bad in (None, "x", {"sid": "", "rows": [{"a": 1}]}, {"sid": "s", "rows": "nope"}):
        at.session_state["_live"] = bad
        at = at.run()
        assert not at.exception
    assert not at.session_state["voice_rows"] if "voice_rows" in at.session_state else True
