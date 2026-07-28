"""이미지 + 본문 + 상품 링크를 블로그 에디터용 HTML로 조립한다. 몰 무관 범용 템플릿."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from common.models import Product

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=True)


def assemble_post_html(
    topic: str, body_text: str, products: list[Product], image_paths: dict[str, str]
) -> str:
    template = _env.get_template("post.html.j2")
    return template.render(
        topic=topic,
        body_text=body_text,
        products=products,
        image_paths=image_paths,
    )
