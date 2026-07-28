from __future__ import annotations

from adapters._base_adapter import AdapterRegistry
from common.models import Product, ProductDetail


class ZigzagAdapter:
    """지그재그 몰 어댑터.

    TODO: 지그재그에 제휴/크리에이터 프로그램이 있는지 먼저 확인할 것.
    있으면 공식 상품 피드 API로 교체 (가장 안전/안정적).
    없으면 Playwright 스크래핑으로 대체하되, 이 어댑터 안에서만 스크래핑 권한을 갖고
    다른 에이전트는 절대 직접 스크래핑하지 않는다 (리스크 격리).
    """

    def search_products(self, category: str, topic: str, count: int) -> list[Product]:
        raise NotImplementedError(
            "TODO: 지그재그 제휴 API 또는 검색 페이지 파싱으로 상품 후보 수집"
        )

    def get_product_detail(self, product_id: str) -> ProductDetail:
        raise NotImplementedError("TODO: 상세페이지에서 설명/이미지 URL 목록 수집")

    def check_stock(self, product_id: str) -> bool:
        raise NotImplementedError("TODO: 재고 상태 재조회")

    def get_product_url(self, product_id: str) -> str:
        raise NotImplementedError("TODO: product_id -> 상품 URL 변환")


AdapterRegistry.register("zigzag", ZigzagAdapter())
