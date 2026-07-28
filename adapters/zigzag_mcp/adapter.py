"""지그재그 몰 어댑터.

지그재그는 별도 제휴/크리에이터 프로그램 API가 없어(2026-07 확인 기준), 사이트가 내부적으로
쓰는 공개 GraphQL API(api.zigzag.kr)를 그대로 호출한다. 로그인/쿠키 없이 접근 가능한
공개 상품 검색·상세 데이터만 사용하며, 스크래핑 권한은 이 어댑터 안에만 격리한다.

쿼리 문자열(queries/*.graphql)은 실제 브라우저 네트워크 요청을 그대로 캡처한 것이라
필드가 많아 보이지만, 사이트가 리뉴얼되어 스키마가 바뀌면 다시 캡처해서 교체해야 한다.
"""

from __future__ import annotations

from pathlib import Path

import requests

from adapters._base_adapter import AdapterRegistry
from common.models import Product, ProductDetail

QUERIES_DIR = Path(__file__).resolve().parent / "queries"
SEARCH_QUERY = (QUERIES_DIR / "search.graphql").read_text(encoding="utf-8")
DETAIL_QUERY = (QUERIES_DIR / "detail.graphql").read_text(encoding="utf-8")

GRAPHQL_URL = "https://api.zigzag.kr/api/2/graphql/{operation}"

HEADERS = {
    "content-type": "application/json",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "origin": "https://zigzag.kr",
    "referer": "https://zigzag.kr/",
}


def _post(operation: str, query: str, variables: dict) -> dict:
    resp = requests.post(
        GRAPHQL_URL.format(operation=operation),
        headers=HEADERS,
        json={"query": query, "variables": variables},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("errors"):
        raise RuntimeError(f"zigzag GraphQL error ({operation}): {data['errors']}")
    return data["data"]


class ZigzagAdapter:
    def search_products(self, category: str, topic: str, count: int) -> list[Product]:
        keyword = f"{category.split('>')[-1].strip()} {topic}".strip()
        data = _post(
            "GetSearchResult",
            SEARCH_QUERY,
            {
                "input": {
                    "enable_guided_keyword_search": True,
                    "initial": True,
                    "page_id": "srp_item",
                    "q": keyword,
                    "filter_id_list": [],
                    "filter_list": [],
                    "sub_filter_id_list": [],
                    "after": None,
                }
            },
        )
        items = data["search_result"]["ui_item_list"]
        goods = [i for i in items if i.get("type") == "UX_GOODS_CARD_ITEM"]

        return [
            Product(
                product_id=g["catalog_product_id"],
                name=g["title"],
                price=g["final_price"],
                url=self.get_product_url(g["catalog_product_id"]),
                category=category,
                thumbnail_url=g.get("image_url"),
                in_stock=g.get("sellable_status", "ON_SALE") == "ON_SALE",
            )
            for g in goods[:count]
        ]

    def get_product_detail(self, product_id: str) -> ProductDetail:
        cp = self._fetch_catalog_product(product_id)
        image_urls = [img["url"] for img in cp.get("product_image_list", [])]
        price = cp["product_price"].get("final_discount_info", {}).get(
            "discount_price"
        ) or cp["product_price"].get("max_price_info", {}).get("price", 0)

        return ProductDetail(
            product_id=product_id,
            name=cp["name"],
            price=price,
            url=self.get_product_url(product_id),
            # 지그재그 상세페이지는 텍스트 설명이 따로 없고 이미지(상세컷) 위주라
            # description은 상품명으로 대체 — 실제 카피는 Copywriter가 새로 작성한다.
            description=cp["name"],
            image_urls=image_urls,
            in_stock=self.check_stock(product_id, _catalog_product=cp),
        )

    def check_stock(self, product_id: str, _catalog_product: dict | None = None) -> bool:
        cp = _catalog_product or self._fetch_catalog_product(product_id)
        items = cp.get("matched_item_list") or []
        return any(item.get("sales_status") == "ON_SALE" for item in items)

    def get_product_url(self, product_id: str) -> str:
        return f"https://store.zigzag.kr/app/catalog/products/{product_id}"

    def _fetch_catalog_product(self, product_id: str) -> dict:
        data = _post(
            "GetCatalogProductDetailPageOption",
            DETAIL_QUERY,
            {
                "catalog_product_id": product_id,
                "input": {"catalog_product_id": product_id},
            },
        )
        return data["pdp_option_info"]["catalog_product"]


AdapterRegistry.register("zigzag", ZigzagAdapter())
