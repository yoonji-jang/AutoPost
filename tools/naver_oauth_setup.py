"""네이버 로그인 최초 1회 인가 플로우를 자동화하는 setup 스크립트.

NAVER_CLIENT_ID/SECRET은 .env에서 읽고, redirect_uri의 localhost 포트에 임시 HTTP 서버를
띄워 인가 콜백(code)을 직접 받은 뒤 refresh_token까지 교환해서 .env에 저장한다.

사용법:
    python tools/naver_oauth_setup.py --redirect-uri http://localhost:8080/callback

실행하면 브라우저에서 열어야 할 인가 URL을 출력한다. 그 URL을 열어 네이버 로그인/동의를
완료하면, 이 스크립트가 콜백을 받아 자동으로 refresh_token을 .env에 기록하고 종료된다.
"""

from __future__ import annotations

import argparse
import os
import secrets
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import requests
from dotenv import load_dotenv, set_key

load_dotenv()

AUTH_URL = "https://nid.naver.com/oauth2.0/authorize"
TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

RESULT: dict = {}


def make_handler(expected_state: str):
    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            if parsed.path != "/callback":
                self.send_response(404)
                self.end_headers()
                return

            params = parse_qs(parsed.query)
            code = params.get("code", [None])[0]
            state = params.get("state", [None])[0]
            error = params.get("error", [None])[0]

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()

            if error or not code:
                self.wfile.write(
                    f"<h1>인가 실패</h1><p>{error or 'code 없음'}</p>".encode("utf-8")
                )
                RESULT["error"] = error or "code missing"
            elif state != expected_state:
                self.wfile.write("<h1>state 불일치 — 요청을 다시 시작하세요</h1>".encode("utf-8"))
                RESULT["error"] = "state mismatch"
            else:
                self.wfile.write(
                    "<h1>인증 완료</h1><p>이 창은 닫아도 됩니다.</p>".encode("utf-8")
                )
                RESULT["code"] = code

        def log_message(self, format, *args):  # noqa: A002
            pass  # 콘솔 노이즈 억제

    return CallbackHandler


def exchange_code_for_tokens(client_id: str, client_secret: str, code: str, state: str) -> dict:
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "state": state,
        },
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    parser = argparse.ArgumentParser(description="네이버 OAuth 최초 인가 및 refresh_token 발급")
    parser.add_argument(
        "--redirect-uri",
        default="http://localhost:8080/callback",
        help="네이버 개발자센터에 등록한 Callback URL과 정확히 일치해야 함",
    )
    parser.add_argument(
        "--state",
        default=None,
        help="미리 생성한 state 값을 재사용하고 싶을 때 지정 (생략하면 랜덤 생성)",
    )
    args = parser.parse_args()

    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    if not client_id or not client_secret:
        print("NAVER_CLIENT_ID / NAVER_CLIENT_SECRET이 .env에 없습니다.", file=sys.stderr)
        raise SystemExit(1)

    redirect_uri = args.redirect_uri
    parsed_redirect = urlparse(redirect_uri)
    port = parsed_redirect.port or 8080

    state = args.state or secrets.token_urlsafe(16)
    auth_url = (
        f"{AUTH_URL}?response_type=code&client_id={client_id}"
        f"&redirect_uri={redirect_uri}&state={state}"
    )

    print("아래 URL을 브라우저에서 열어 네이버 로그인/동의를 완료하세요:")
    print(auth_url)
    webbrowser.open(auth_url)

    server = HTTPServer(("localhost", port), make_handler(state))
    print(f"localhost:{port}에서 콜백을 기다리는 중... (Ctrl+C로 취소)")
    while "code" not in RESULT and "error" not in RESULT:
        server.handle_request()

    if "error" in RESULT:
        print(f"인가 실패: {RESULT['error']}", file=sys.stderr)
        raise SystemExit(1)

    print("code 수신 완료, access_token/refresh_token 교환 중...")
    tokens = exchange_code_for_tokens(client_id, client_secret, RESULT["code"], state)

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        print(f"토큰 응답에 refresh_token이 없습니다: {tokens}", file=sys.stderr)
        raise SystemExit(1)

    set_key(ENV_PATH, "NAVER_REFRESH_TOKEN", refresh_token)
    print(f"NAVER_REFRESH_TOKEN을 {ENV_PATH}에 저장했습니다.")


if __name__ == "__main__":
    main()
