from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Product:
    product_id: str
    name: str
    price: int
    url: str
    category: str
    thumbnail_url: str | None = None
    in_stock: bool = True


@dataclass
class ProductDetail:
    product_id: str
    name: str
    price: int
    url: str
    description: str
    image_urls: list[str] = field(default_factory=list)
    in_stock: bool = True


@dataclass
class JobConfig:
    mall: str
    category: str
    topic: str
    item_count: int
    style_profile: str
    publish_target: str = "naver_blog"
    schedule: str | None = None


@dataclass
class DraftPost:
    job: JobConfig
    products: list[Product]
    body_html: str
    feed_captions: dict[str, str]
    image_paths: dict[str, str]
