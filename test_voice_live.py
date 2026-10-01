# -*- coding: utf-8 -*-
"""음성 문장 → 행 규칙(voice_parse_local) 검증.

실시간 받아쓰기 화면은 같은 규칙을 자바스크립트(VP)로 돌린다. 파이썬 결과를 먼저 확인하고,
node가 설치돼 있으면 자바스크립트도 같은 결과를 내는지 비교한다(없으면 그 부분만 건너뜀).
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "app.py"
_SRC = APP.read_text(encoding="utf-8")

C4 = ["처리구", "반복", "초장", "수량(kg/10a)"]
CASES = [
    # (문장, 열, 기대 행)
    ("처리구 A, 반복 1, 초장 72.3, 수량 615.4", C4,
     {"처리구": "A", "반복": 1, "초장": 72.3, "수량(kg/10a)": 615.4}),
    ("처리구 에이 반복 일 초장 칠십이 점 삼 수량 육백십오 점 사", C4,
     {"처리구": "A", "반복": 1, "초장": 72.3, "수량(kg/10a)": 615.4}),
    ("처리구는 대조구 반복은 3 수량이 1,234kg 초장 72점5", C4,
     {"처리구": "대조구", "반복": 3, "초장": 72.5, "수량(kg/10a)": 1234}),
    ("처리구 B 반복 2 초장 70 아니 71 수량 600", C4,
     {"처리구": "B", "반복": 2, "초장": 71, "수량(kg/10a)": 600}),
    ("반복 이 처리구 처리1", C4,
     {"처리구": "처리1", "반복": 2, "초장": None, "수량(kg/10a)": None}),
    ("초 장 65 센티 수량 마이너스 3", C4,
     {"처리구": None, "반복": None, "초장": 65, "수량(kg/10a)": -3}),
    ("조사시기 1차 착과수 23개 상품수량 500 수량 520", ["조사시기", "착과수", "수량", "상품수량"],
     {"조사시기": "1차", "착과수": 23, "수량": 520, "상품수량": 500}),
    ("수량 천이백 반복 삼", ["반복", "수량"], {"반복": 3, "수량": 1200}),
    ("처리구 A 반복 1 초장 72 점 3 수량 615.4", [],
     {"처리구": "A", "반복": 1, "초장": 72.3, "수량": 615.4}),
    ("처리구 비 반복 이", [], {"처리구": "B", "반복": 2}),
]
SPLITS = [
    ("처리구 A 반복 1 다음 처리구 B 취소 처리구 C 반복 2", (["처리구 A 반복 1"], "처리구 C 반복 2")),
    ("수량 600 다음 행 수량 700 다음", (["수량 600", "수량 700"], "")),
    ("다음주 조사 수량 600", ([], "다음주 조사 수량 600")),          # '다음주'는 넘김 말이 아님
]


@pytest.fixture(scope="module")
def vp():
    ns = {"re": re}
    exec(_SRC[_SRC.index("_VP_DIG = {"):_SRC.index("def voice_text_to_row")], ns)
    return ns


def _same(a, b):
    assert set(a) == set(b), (a, b)
    for k in a:
        if isinstance(b[k], (int, float)) and not isinstance(b[k], bool):
            assert a[k] == pytest.approx(b[k]), (k, a, b)
        else:
            assert a[k] == b[k], (k, a, b)


@pytest.mark.parametrize("text,cols,want", CASES)
def test_python_parser(vp, text, cols, want):
    _same(vp["voice_parse_local"](text, cols), want)


@pytest.mark.parametrize("text,want", SPLITS)
def test_python_split(vp, text, want):
    assert vp["voice_split_rows"](text) == want


@pytest.mark.parametrize("w,n", [("육백십오", 615), ("천이백", 1200), ("일이삼", 123), ("이만삼천", 23000),
                                 ("십", 10), ("공일", 1), ("이삼백", None)])
def test_sino_korean_numbers(vp, w, n):
    assert vp["_vp_sino"](w) == n


def test_local_parse_skips_second_ai_call(vp, monkeypatch):
    """열을 알고 모든 열이 말해졌으면 AI(ai_call)를 다시 부르지 않는다."""
    ns = dict(vp)
    exec(_SRC[_SRC.index("def voice_text_to_row"):_SRC.index("def ai_disclaimer")], ns)
    calls = []
    ns["ai_call"] = lambda *a, **k: calls.append(a) or '{"row": {"처리구": "Z"}, "warnings": []}'
    ns["_json_from_ai_text"] = lambda t: json.loads(t)
    row, warn = ns["voice_text_to_row"]("처리구 A 반복 1 수량 600", ["처리구", "반복", "수량"])
    assert row == {"처리구": "A", "반복": 1, "수량": 600} and not calls
    row, _ = ns["voice_text_to_row"]("처리구 A 반복 1", ["처리구", "반복", "수량"])   # 수량 빠짐 → AI
    assert calls and row["처리구"] == "Z"


def _js_parser():
    html = _SRC[_SRC.index('_VOICE_LIVE_HTML = r"""'):]
    return html[html.index("// ==== VOICE PARSER START"):html.index("// ==== VOICE PARSER END")]


def test_javascript_parser_matches_python(vp):
    node = shutil.which("node")
    if not node:
        pytest.skip("node가 없어 자바스크립트 비교는 건너뜁니다.")
    script = _js_parser() + """
const cases = JSON.parse(process.argv[1]);
const out = cases.parse.map(c => VP.parse(c[0], c[1]));
const sp = cases.split.map(t => { const r = VP.splitRows(t); return [r.done, r.rest]; });
console.log(JSON.stringify({parse: out, split: sp}));
"""
    payload = json.dumps({"parse": [[t, c] for t, c, _ in CASES], "split": [t for t, _ in SPLITS]},
                         ensure_ascii=False)
    res = subprocess.run([node, "-e", script, payload], capture_output=True, text=True, timeout=30)
    assert res.returncode == 0, res.stderr
    got = json.loads(res.stdout)
    for (text, cols, want), js in zip(CASES, got["parse"]):
        _same(js, want)
        _same(js, vp["voice_parse_local"](text, cols))
    for (text, want), js in zip(SPLITS, got["split"]):
        assert (js[0], js[1]) == want, text
