from __future__ import annotations

from adapters._base_adapter import AdapterRegistry
from common.models import Product, ProductDetail


class OhouseAdapter:
    """오늘의집 몰 어댑터.

    TODO: 오늘의집 파트너스/제휴 API 유무 확인 후 동일한 방식으로 구현.
    """

    def search_products(self, category: str, topic: str, count: int) -> list[Product]:
        raise NotImplementedError(
            "TODO: 오늘의집 제휴 API 또는 검색 페이지 파싱으로 상품 후보 수집"
        )

    def get_product_detail(self, product_id: str) -> ProductDetail:
        raise NotImplementedError("TODO: 상세페이지에서 설명/이미지 URL 목록 수집")

    def check_stock(self, product_id: str) -> bool:
        raise NotImplementedError("TODO: 재고 상태 재조회")

    def get_product_url(self, product_id: str) -> str:
        raise NotImplementedError("TODO: product_id -> 상품 URL 변환")


AdapterRegistry.register("ohouse", OhouseAdapter())
