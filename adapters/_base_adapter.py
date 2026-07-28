from __future__ import annotations

from typing import Protocol

from common.models import Product, ProductDetail


class MallAdapter(Protocol):
    """모든 몰(쇼핑몰) 어댑터가 구현해야 하는 표준 계약.

    Product Scout / Capture / QA 등 파이프라인 에이전트는 이 인터페이스만 알면 되고,
    실제 몰이 어디인지(지그재그, 오늘의집, ...)는 신경 쓰지 않는다.
    """

    def search_products(self, category: str, topic: str, count: int) -> list[Product]:
        ...

    def get_product_detail(self, product_id: str) -> ProductDetail:
        ...

    def check_stock(self, product_id: str) -> bool:
        ...

    def get_product_url(self, product_id: str) -> str:
        ...


class AdapterRegistry:
    """job.mall 값으로 어댑터 인스턴스를 동적으로 조회하는 레지스트리."""

    _adapters: dict[str, MallAdapter] = {}

    @classmethod
    def register(cls, mall: str, adapter: MallAdapter) -> None:
        cls._adapters[mall] = adapter

    @classmethod
    def get(cls, mall: str) -> MallAdapter:
        try:
            return cls._adapters[mall]
        except KeyError as e:
            raise ValueError(
                f"등록되지 않은 mall '{mall}'. 사용 가능: {list(cls._adapters)}"
            ) from e
