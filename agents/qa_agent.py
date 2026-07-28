"""④ QA/Compliance: 품절 재확인, 금지표현, 중복 게시를 검사한다.

실패 시 Orchestrator가 Copywriter를 재호출(재시도)하거나 사람에게 알린다.
"""

from __future__ import annotations

from adapters._base_adapter import AdapterRegistry
from common.models import JobConfig, Product
from tools.qa_checker import QAFailure, run_qa


def check(job: JobConfig, body_html: str, products: list[Product]) -> None:
    """통과하면 None, 실패하면 QAFailure를 발생시킨다."""
    adapter = AdapterRegistry.get(job.mall)
    run_qa(body_html, job.style_profile, products, adapter)


__all__ = ["check", "QAFailure"]
