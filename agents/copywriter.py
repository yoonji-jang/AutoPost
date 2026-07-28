"""③ Copywriter: SKILL.md 스타일 규칙을 시스템 프롬프트로 고정하고 Claude API로 카피를 생성한다."""

from __future__ import annotations

import json
from pathlib import Path

import anthropic

from common.models import JobConfig, Product

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"

MODEL = "claude-sonnet-5"

_client = anthropic.Anthropic()


def _load_skill(style_profile: str) -> str:
    path = SKILLS_DIR / style_profile / "SKILL.md"
    return path.read_text(encoding="utf-8")


def _build_prompt(job: JobConfig, products: list[Product]) -> str:
    product_lines = "\n".join(
        f"- [{p.product_id}] {p.name} / {p.price:,}원 / {p.url}" for p in products
    )
    return (
        f"주제: {job.topic}\n"
        f"카테고리: {job.category}\n"
        f"상품 목록:\n{product_lines}\n\n"
        "위 스타일 규칙을 지켜서 다음 두 가지를 JSON으로 출력해줘:\n"
        '{"body": "네이버 블로그 본문(상품 5개를 엮은 글)", '
        '"feed_captions": {"<product_id>": "인스타 피드 캡션", ...}}'
    )


def run(job: JobConfig, products: list[Product]) -> tuple[str, dict[str, str]]:
    skill = _load_skill(job.style_profile)

    message = _client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=skill,
        messages=[{"role": "user", "content": _build_prompt(job, products)}],
    )

    result = json.loads(message.content[0].text)
    return result["body"], result["feed_captions"]
