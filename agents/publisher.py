"""⑥ Publisher: 네이버 블로그에 임시저장 또는 발행하고 이력을 기록한다.

기본값은 "임시저장"이다 — 완전 자동 발행보다 안전하며, 사람이 승인하면
publish() 를 다시 호출해 실제 발행으로 전환한다.
"""

from __future__ import annotations

from common.models import JobConfig, Product
from tools.dedup_checker import record_posting
from tools.naver_oauth_client import NaverOAuthClient

_client = NaverOAuthClient()


def save_draft(job: JobConfig, title: str, body_html: str) -> dict:
    return _client.save_draft(title, body_html)


def publish(job: JobConfig, title: str, body_html: str, products: list[Product]) -> dict:
    result = _client.publish_post(title, body_html)
    for product in products:
        record_posting(job.mall, job.category, product.product_id)
    return result
