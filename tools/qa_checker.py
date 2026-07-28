"""발행 전 품질/컴플라이언스 검사.

- 금지 표현 검사 (style_profile별로 분기)
- 재고 재확인 (Product Scout 실행 시점과 발행 시점 사이 시차 대응)
- 중복 게시 여부는 tools/dedup_checker.py 에 위임
"""

from __future__ import annotations

from adapters._base_adapter import MallAdapter
from common.models import Product

BANNED_PHRASES_BY_PROFILE: dict[str, list[str]] = {
    "zigzag_zipmag": ["마법", "실화", "인생템", "완전 대박"],
    "ohouse_living": ["마법", "실화", "인생템"],
}


class QAFailure(Exception):
    pass


def check_banned_phrases(text: str, style_profile: str) -> list[str]:
    """금지 표현이 포함되어 있으면 걸린 표현 목록을 반환한다 (빈 리스트면 통과)."""
    banned = BANNED_PHRASES_BY_PROFILE.get(style_profile, [])
    return [phrase for phrase in banned if phrase in text]


def check_stock_all(products: list[Product], adapter: MallAdapter) -> list[Product]:
    """발행 직전 재고를 재조회해 품절 상품을 걸러낸다."""
    return [p for p in products if adapter.check_stock(p.product_id)]


def run_qa(
    body_html: str, style_profile: str, products: list[Product], adapter: MallAdapter
) -> None:
    """QA 실패 시 QAFailure를 발생시킨다. 통과하면 아무 것도 반환하지 않는다."""
    hits = check_banned_phrases(body_html, style_profile)
    if hits:
        raise QAFailure(f"금지 표현 발견: {hits}")

    in_stock = check_stock_all(products, adapter)
    if len(in_stock) < len(products):
        sold_out = {p.product_id for p in products} - {p.product_id for p in in_stock}
        raise QAFailure(f"품절 상품 발견: {sold_out}")
