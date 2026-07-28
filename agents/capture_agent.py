"""② Capture Agent: 선정된 상품의 이미지를 확보한다.

URL 방문/캡쳐(또는 URL 재사용)만 하고, 상품 재선정 로직은 절대 갖지 않는다.

몰 어댑터가 이미 공식 이미지 URL(Product.thumbnail_url)을 제공하면 그걸 그대로 쓰고,
스크린샷은 찍지 않는다. thumbnail_url이 없는 몰(제휴/공개 이미지 API가 없는 경우)에서만
Playwright로 상세페이지를 캡쳐하는 폴백을 탄다.
"""

from __future__ import annotations

from common.models import Product
from tools.playwright_capture import capture_product_image


def run(products: list[Product]) -> dict[str, str]:
    """product_id -> 이미지 경로 또는 URL."""
    image_paths: dict[str, str] = {}
    for product in products:
        if product.thumbnail_url:
            image_paths[product.product_id] = product.thumbnail_url
        else:
            image_paths[product.product_id] = capture_product_image(
                product.url, product.product_id
            )
    return image_paths
