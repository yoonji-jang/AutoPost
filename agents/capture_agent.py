"""② Capture Agent: 선정된 상품 상세페이지 이미지를 확보한다.

URL 방문 + 캡쳐만 하고, 상품 재선정 로직은 절대 갖지 않는다.
"""

from __future__ import annotations

from common.models import Product
from tools.playwright_capture import capture_product_image


def run(products: list[Product]) -> dict[str, str]:
    """product_id -> 캡쳐된 이미지 경로."""
    image_paths: dict[str, str] = {}
    for product in products:
        image_paths[product.product_id] = capture_product_image(
            product.url, product.product_id
        )
    return image_paths
