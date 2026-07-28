"""⑤ Assembler: 이미지 + 본문 + 상품 링크를 블로그 포맷(HTML)으로 조립한다. 몰 무관."""

from __future__ import annotations

from common.models import JobConfig, Product
from tools.html_assembler import assemble_post_html


def run(
    job: JobConfig, body_text: str, products: list[Product], image_paths: dict[str, str]
) -> str:
    return assemble_post_html(job.topic, body_text, products, image_paths)
