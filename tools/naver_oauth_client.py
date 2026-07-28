"""네이버 로그인 오픈 API의 블로그 글쓰기 기능을 감싸는 클라이언트.

OAuth2 액세스 토큰 발급/갱신과 save_draft / publish_post / upload_image를 제공한다.
Publisher 에이전트(agents/publisher)가 이 모듈을 통해서만 네이버와 통신한다.

주의: 실제 요청 파라미터명(title/contents/blogId 등)은 네이버 개발자센터 문서
(https://developers.naver.com/docs/login/api/api.md, blog write API)를 최신 기준으로
반드시 재확인할 것. 아래는 구조를 보여주는 스켈레톤이다.
"""

from __future__ import annotations

import os
import time

import requests

TOKEN_URL = "https://nid.naver.com/oauth2.0/token"
BLOG_WRITE_URL = "https://openapi.naver.com/blog/writePost.json"


class NaverOAuthClient:
    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        refresh_token: str | None = None,
    ) -> None:
        self.client_id = client_id or os.environ["NAVER_CLIENT_ID"]
        self.client_secret = client_secret or os.environ["NAVER_CLIENT_SECRET"]
        self.refresh_token = refresh_token or os.environ["NAVER_REFRESH_TOKEN"]
        self._access_token: str | None = None
        self._expires_at: float = 0.0

    def _refresh_access_token(self) -> str:
        resp = requests.post(
            TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        self._access_token = data["access_token"]
        self._expires_at = time.time() + int(data.get("expires_in", 3600)) - 60
        return self._access_token

    def _get_access_token(self) -> str:
        if not self._access_token or time.time() >= self._expires_at:
            return self._refresh_access_token()
        return self._access_token

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._get_access_token()}"}

    def save_draft(self, title: str, contents_html: str, category_no: str | None = None) -> dict:
        """임시저장으로 등록한다 (기본 안전 옵션 — 완전 자동 발행보다 우선 추천)."""
        return self._write_post(title, contents_html, category_no, publish=False)

    def publish_post(self, title: str, contents_html: str, category_no: str | None = None) -> dict:
        """실제 발행. 보통 Notifier의 사람 승인 이후 호출된다."""
        return self._write_post(title, contents_html, category_no, publish=True)

    def _write_post(
        self, title: str, contents_html: str, category_no: str | None, publish: bool
    ) -> dict:
        payload = {
            "title": title,
            "contents": contents_html,
            "publish": "true" if publish else "false",
        }
        if category_no:
            payload["categoryNo"] = category_no

        resp = requests.post(BLOG_WRITE_URL, headers=self._headers(), data=payload, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def upload_image(self, image_path: str) -> str:
        """이미지를 업로드하고 본문에 넣을 수 있는 URL을 반환한다."""
        raise NotImplementedError(
            "TODO: 네이버 블로그 이미지 업로드 API 연동 (문서 재확인 필요)"
        )
