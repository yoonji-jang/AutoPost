"""사람이 임시저장 글을 확인한 뒤 실제 발행으로 전환할 때 실행하는 스크립트.

네이버 블로그 관리자 화면에서 직접 '발행' 버튼을 누르는 것으로도 충분하다면
이 스크립트는 선택 사항이다. API로 발행까지 자동화하고 싶을 때 사용한다.
"""

from __future__ import annotations

import argparse

from agents import publisher
from common.models import JobConfig


def main() -> None:
    parser = argparse.ArgumentParser(description="임시저장된 글을 실제 발행으로 전환")
    parser.add_argument("--mall", required=True)
    parser.add_argument("--category", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--html-file", required=True, help="발행할 본문 HTML 파일 경로")
    args = parser.parse_args()

    job = JobConfig(
        mall=args.mall, category=args.category, topic="", item_count=0, style_profile=""
    )

    with open(args.html_file, encoding="utf-8") as f:
        body_html = f.read()

    result = publisher.publish(job, args.title, body_html, products=[])
    print(f"발행 완료: {result}")


if __name__ == "__main__":
    main()
