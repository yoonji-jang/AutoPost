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
        "위 스타일 규칙을 지켜서 다음 두 가지를 JSON으로만 출력해줘 "
        "(다른 설명이나 코드펜스 없이):\n"
        '{"body": "네이버 블로그 본문(상품 5개를 엮은 글). '
        'HTML 태그 없이 일반 텍스트로 쓰고, 문단 사이는 빈 줄(\\n\\n)로 구분", '
        '"feed_captions": {"<product_id>": "인스타 피드 캡션", ...}}'
    )


def _extract_json(text: str) -> dict:
    """모델이 코드펜스나 잡담을 섞어 보내는 경우까지 방어적으로 JSON을 추출한다."""
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else text
        text = text.rsplit("```", 1)[0]
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"응답에서 JSON을 찾을 수 없음: {text[:200]}")
    return json.loads(text[start : end + 1])


def run(job: JobConfig, products: list[Product]) -> tuple[str, dict[str, str]]:
    skill = _load_skill(job.style_profile)

    message = _client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=skill,
        messages=[{"role": "user", "content": _build_prompt(job, products)}],
    )

    result = _extract_json(message.content[0].text)
    return result["body"], result["feed_captions"]
