# -*- coding: utf-8 -*-
"""로그인 게이트(Firebase) 검증.

app.py 전체를 띄우지 않고 로그인 구간만 잘라 AppTest로 돌린다. Firebase Auth REST와
Firestore는 가짜 서버로 가로채므로 네트워크 없이 실행된다.
검증 범위: 가입 허용 도메인/예외 이메일, 이메일 인증, 비밀번호 재설정,
회원 명부·로그인·이용 기록 저장, Firestore 값 변환.
"""
from pathlib import Path
import datetime as dt
import textwrap

import pytest

st_testing = pytest.importorskip("streamlit.testing.v1")
AppTest = st_testing.AppTest

APP = Path(__file__).resolve().parents[1] / "app.py"
START = "# ================================================================ 회원가입/로그인"
END = "# ---------------------------------------------------------------- AI 호출"
_SRC = APP.read_text(encoding="utf-8")
SEG = _SRC[_SRC.index(START):_SRC.index(END)]

SECRETS = {
    "FIREBASE_WEB_API_KEY": "AIza-test",
    "FIREBASE_PROJECT_ID": "demo-proj",
    "AUTH_REQUIRED": "true",
    "ALLOWED_EMAIL_DOMAINS": "korea.kr, go.kr",
    "ALLOWED_EMAILS": "friend@gmail.com",
    "ADMIN_EMAILS": "boss@naver.com",
}


# ---------------------------------------------------------------- 순수 함수
@pytest.fixture(scope="module")
def ns():
    import numpy as np, pandas as pd
    import streamlit as st
    n = {"st": st, "np": np, "pd": pd, "_requests": None}
    exec(SEG, n)
    return n


def _cfg(**over):
    base = {"allowed_domains": ["korea.kr", "go.kr"],
            "allowed_emails": {"friend@gmail.com"}, "admins": {"boss@naver.com"}}
    base.update(over)
    return base


@pytest.mark.parametrize("email,ok", [
    ("kim@korea.kr", True),
    ("KIM@Korea.KR ", True),            # 대소문자·공백
    ("lee@rda.go.kr", True),            # 하위 도메인
    ("friend@gmail.com", True),         # 예외 이메일
    ("boss@naver.com", True),           # 관리자는 자동 허용
    ("stranger@gmail.com", False),
    ("x@notkorea.kr", False),           # 끝부분만 같은 가짜 도메인
    ("x@korea.kr.evil.com", False),
    ("no-at-sign", False),
    ("", False),
])
def test_email_allowed(ns, email, ok):
    assert ns["_email_allowed"](email, _cfg()) is ok


def test_no_rules_means_everyone(ns):
    assert ns["_email_allowed"]("anyone@gmail.com", _cfg(allowed_domains=[], allowed_emails=set()))


def test_firestore_value_roundtrip(ns):
    enc, dec = ns["_fs_encode"], ns["_fs_decode"]
    when = dt.datetime(2026, 9, 29, 6, 30, tzinfo=dt.timezone.utc)
    src = {"s": "경북", "i": 3, "f": 1.5, "b": True, "n": None, "t": when}
    out = dec({k: enc(v) for k, v in src.items()})
    assert out["s"] == "경북" and out["i"] == 3 and out["f"] == 1.5 and out["b"] is True
    assert out["n"] is None and out["t"].startswith("2026-09-29T06:30:00")


def test_error_messages_are_korean(ns):
    t = ns["_fb_error_text"]
    assert "비밀번호" in t("INVALID_LOGIN_CREDENTIALS")
    assert "8자" in t("WEAK_PASSWORD : Password should be at least 6 characters")
    assert "이미 가입" in t("EMAIL_EXISTS")
    assert "연결" in t("NETWORK:ConnectionError")


def test_service_account_from_json_string(ns, monkeypatch):
    import json
    info = {"client_email": "a@b.iam.gserviceaccount.com", "project_id": "p1",
            "private_key": "-----BEGIN PRIVATE KEY-----\\nABC\\n-----END PRIVATE KEY-----\\n"}
    monkeypatch.setenv("FIREBASE_SERVICE_ACCOUNT", json.dumps(info))
    got = ns["_service_account_info"]()
    assert got["project_id"] == "p1" and "\n" in got["private_key"] and "\\n" not in got["private_key"]


# ---------------------------------------------------------------- 화면 흐름
def _script():
    return textwrap.dedent(f'''
        import streamlit as st, numpy as np, pandas as pd, json, re
        S = st.session_state
        S.setdefault("_calls", [])
        S.setdefault("_users", {{}})          # 가짜 Firebase 계정: email -> dict
        S.setdefault("_docs", {{}})           # 가짜 Firestore: "col/id" -> fields
        S.setdefault("_seq", 0)

        class R:
            def __init__(self, code, js):
                self.status_code, self._js, self.text = code, js, json.dumps(js)
            def json(self):
                return self._js

        def err(msg):
            return R(400, {{"error": {{"message": msg}}}})

        class FakeRequests:
            def post(self, url, params=None, json=None, headers=None, data=None, timeout=None):
                ep = url.rsplit(":", 1)[-1] if "identitytoolkit" in url else "refresh"
                S["_calls"].append((ep, json or data))
                U = S["_users"]
                if ep == "signUp":
                    if json["email"] in U:
                        return err("EMAIL_EXISTS")
                    U[json["email"]] = {{"pw": json["password"], "verified": False,
                                         "uid": "uid-" + json["email"].split("@")[0]}}
                    u = U[json["email"]]
                    return R(200, {{"idToken": "tok-" + json["email"], "refreshToken": "rt",
                                     "expiresIn": "3600", "localId": u["uid"], "email": json["email"]}})
                if ep == "signInWithPassword":
                    u = U.get(json["email"])
                    if not u or u["pw"] != json["password"]:
                        return err("INVALID_LOGIN_CREDENTIALS")
                    return R(200, {{"idToken": "tok-" + json["email"], "refreshToken": "rt",
                                     "expiresIn": "3600", "localId": u["uid"], "email": json["email"]}})
                if ep == "lookup":
                    email = json["idToken"][4:]
                    return R(200, {{"users": [{{"email": email, "emailVerified": U[email]["verified"]}}]}})
                if ep == "sendOobCode" or ep == "update":
                    return R(200, {{}})
                return R(200, {{}})

        class FakeFirestore:
            def _path(self, url):
                return url.split("/documents/", 1)[1] if "/documents/" in url else ""
            def patch(self, url, params=None, json=None, timeout=None):
                p = self._path(url)
                cur = S["_docs"].setdefault(p, {{}})
                cur.update(json["fields"])
                return R(200, {{"fields": cur}})
            def post(self, url, json=None, timeout=None):
                if url.endswith(":runQuery"):
                    q = json["structuredQuery"]
                    col = q["from"][0]["collectionId"]
                    f = q["orderBy"][0]["field"]["fieldPath"]
                    docs = [v for k, v in S["_docs"].items() if k.split("/")[0] == col and f in v]
                    docs.sort(key=lambda d: d[f]["timestampValue"], reverse=True)
                    return R(200, [{{"document": {{"fields": d}}}} for d in docs[:q["limit"]]])
                S["_seq"] += 1
                S["_docs"][self._path(url) + "/auto" + str(S["_seq"])] = json["fields"]
                return R(200, {{}})
            def get(self, url, params=None, timeout=None):
                p = self._path(url)
                if "/" in p:
                    return R(200, {{"fields": S["_docs"][p]}}) if p in S["_docs"] else R(404, {{}})
                docs = [{{"fields": v}} for k, v in S["_docs"].items() if k.split("/")[0] == p]
                return R(200, {{"documents": docs}})

        _requests = FakeRequests()
        _src = open({str(APP)!r}, encoding="utf-8").read()
        exec(_src[_src.index({START!r}):_src.index({END!r})])
        _fs_session = lambda: FakeFirestore()
        def smart_table(df, **kw):
            st.dataframe(df)
        def dataframe_to_styled_xlsx(df, title=""):
            return b"x"

        render_auth_gate()
        st.write("APP_OPEN")
        if st.session_state.get("_do_usage"):
            _record_usage("일원분산분석")
        if _is_admin_user():
            render_admin_dashboard()
    ''')


def _new_app(**secrets_over):
    at = AppTest.from_string(_script(), default_timeout=30)
    for k, v in {**SECRETS, **secrets_over}.items():
        at.secrets[k] = v
    return at.run()


def _opened(at):
    return any("APP_OPEN" in str(m.value) for m in at.markdown)


def _calls(at, ep):
    return [c[1] for c in at.session_state["_calls"] if c[0] == ep]


def _docs(at, col):
    return {k: v for k, v in at.session_state["_docs"].items() if k.split("/")[0] == col}


def _signup(at, email, pw="password123", org="경상북도농업기술원"):
    at.text_input(key="auth_name").input("홍길동")
    at.text_input(key="auth_signup_email").input(email)
    at.text_input(key="auth_signup_pw").input(pw)
    at.text_input(key="auth_org").input(org)
    at.text_input(key="auth_dept").input("영양고추연구소")
    at.checkbox(key="auth_consent").check()
    return at.button(key="auth_signup_btn").click().run()


def _login(at, email, pw="password123"):
    at.text_input(key="auth_login_email").input(email)
    at.text_input(key="auth_login_pw").input(pw)
    return at.button(key="auth_login_btn").click().run()


def _verify(at, email):
    at.session_state["_users"][email]["verified"] = True


def test_gate_is_off_without_auth_required():
    assert _opened(_new_app(AUTH_REQUIRED="false"))


def test_gate_is_off_without_api_key():
    assert _opened(_new_app(FIREBASE_WEB_API_KEY=""))


def test_gate_blocks_when_on():
    at = _new_app()
    assert not _opened(at)
    assert at.button(key="auth_login_btn")


def test_signup_rejects_personal_mail_without_calling_firebase():
    at = _signup(_new_app(), "stranger@gmail.com")
    assert any("허용되지 않은" in e.value for e in at.error)
    assert not _calls(at, "signUp")
    assert not _opened(at)


def test_signup_sends_verification_and_saves_profile():
    at = _signup(_new_app(), "hong@korea.kr")
    assert _calls(at, "signUp")
    assert _calls(at, "sendOobCode")[-1]["requestType"] == "VERIFY_EMAIL"
    assert any("인증 메일" in s.value for s in at.success)
    assert not _opened(at)                                   # 인증 전에는 로그인 안 됨
    prof = _docs(at, "profiles")["profiles/uid-hong"]
    assert prof["organization"]["stringValue"] == "경상북도농업기술원"
    assert prof["department"]["stringValue"] == "영양고추연구소"
    assert "created_at" in prof


def test_unverified_login_blocked_then_verified_login_ok():
    at = _signup(_new_app(), "hong@korea.kr")
    at = _login(at, "hong@korea.kr")
    assert not _opened(at)
    assert any("인증이 아직" in w.value for w in at.warning)
    at.button(key="auth_resend_verify").click().run()
    assert _calls(at, "sendOobCode")[-1]["requestType"] == "VERIFY_EMAIL"
    _verify(at, "hong@korea.kr")
    at = _login(at, "hong@korea.kr")
    assert _opened(at)
    user = at.session_state["auth_user"]
    assert user["user_metadata"]["organization"] == "경상북도농업기술원"   # Firestore에서 불러옴
    assert _docs(at, "login_events")
    assert "last_login_at" in _docs(at, "profiles")["profiles/uid-hong"]


def test_verification_can_be_turned_off():
    at = _signup(_new_app(REQUIRE_EMAIL_VERIFICATION="false"), "hong@korea.kr")
    assert _opened(at)
    assert not [c for c in _calls(at, "sendOobCode") if c.get("requestType") == "VERIFY_EMAIL"]


def test_wrong_password_message():
    at = _signup(_new_app(), "hong@korea.kr")
    at = _login(at, "hong@korea.kr", pw="wrongpass1")
    assert any("올바르지 않습니다" in e.value for e in at.error)
    assert not _opened(at)


def test_duplicate_signup_message():
    at = _signup(_new_app(), "hong@korea.kr")
    at = _signup(at, "hong@korea.kr")
    assert any("이미 가입" in e.value for e in at.error)


def test_login_blocked_for_existing_account_outside_allowlist():
    """허용 목록을 나중에 좁혀도, 예전에 가입한 계정이 로그인으로 들어오면 안 된다."""
    at = _new_app()
    at.session_state["_users"]["old@gmail.com"] = {"pw": "password123", "verified": True, "uid": "u-old"}
    at = _login(at, "old@gmail.com")
    assert not _opened(at)
    assert any("허용되지 않은" in e.value for e in at.error)
    assert "auth_user" not in at.session_state


def test_password_reset_sends_mail_without_revealing_accounts():
    at = _new_app()
    at.text_input(key="auth_reset_email").input("nobody@korea.kr")
    at.button(key="auth_reset_btn").click().run()
    req = _calls(at, "sendOobCode")[-1]
    assert req == {"requestType": "PASSWORD_RESET", "email": "nobody@korea.kr"}
    assert any("재설정 메일" in s.value for s in at.success)


def test_usage_logging_and_admin_dashboard():
    at = _new_app()
    for email in ("hong@korea.kr", "boss@naver.com"):
        at = _signup(at, email)
        _verify(at, email)
    at = _login(at, "hong@korea.kr")
    at.session_state["_do_usage"] = True
    at = at.run()
    use = list(_docs(at, "usage_events").values())
    assert use and use[0]["action"]["stringValue"] == "일원분산분석"
    assert use[0]["organization"]["stringValue"] == "경상북도농업기술원"
    assert not any("관리자" in t.value for t in at.title)    # 일반 사용자는 관리자 화면 없음

    at.session_state["_do_usage"] = False
    at.session_state["auth_user"] = None
    at = _login(at.run(), "boss@naver.com")
    assert any("관리자" in t.value for t in at.title)
    labels = {m.label: m.value for m in at.metric}
    assert labels["가입 사용자"] == "2명"
    assert labels["기능 이용 기록"] == "1회"


def test_no_restriction_lets_anyone_sign_up():
    """허용 목록을 비우면 기관 메일이 아니어도 가입된다."""
    at = _signup(_new_app(ALLOWED_EMAIL_DOMAINS="", ALLOWED_EMAILS=""), "farmer@gmail.com")
    assert _calls(at, "signUp")
    assert any("인증 메일" in s.value for s in at.success)
    assert not any("가입할 수 있습니다" in c.value for c in at.caption)   # 도메인 안내 문구 없음


def test_individual_without_organization():
    at = _new_app(ALLOWED_EMAIL_DOMAINS="", ALLOWED_EMAILS="")
    at.text_input(key="auth_name").input("김농부")
    at.text_input(key="auth_signup_email").input("farmer@naver.com")
    at.text_input(key="auth_signup_pw").input("password123")
    at.selectbox(key="auth_org_type").select("개인 (소속 없음)").run()
    assert not [t for t in at.text_input if t.key == "auth_org"]     # 소속기관 칸이 사라짐
    at.checkbox(key="auth_consent").check()
    at = at.button(key="auth_signup_btn").click().run()
    prof = _docs(at, "profiles")["profiles/uid-farmer"]
    assert prof["organization"]["stringValue"] == "개인"
    assert prof["organization_type"]["stringValue"] == "개인 (소속 없음)"
