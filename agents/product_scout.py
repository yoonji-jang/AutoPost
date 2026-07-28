"""① Product Scout: 주제 입력받아 몰에서 상품 후보를 선정한다.

- 최근 N일 내 이미 다룬 상품은 dedup_checker로 걸러낸다.
- 스크래핑 권한은 이 에이전트(및 어댑터)에만 있고, 다른 에이전트는 직접 스크래핑하지 않는다.
"""

from __future__ import annotations

from adapters._base_adapter import AdapterRegistry
from common.models import JobConfig, Product
from tools.dedup_checker import was_recently_posted


def run(job: JobConfig) -> list[Product]:
    adapter = AdapterRegistry.get(job.mall)

    candidates = adapter.search_products(job.category, job.topic, job.item_count * 2)

    fresh = [
        p
        for p in candidates
        if not was_recently_posted(job.mall, job.category, p.product_id)
    ]

    return fresh[: job.item_count]
