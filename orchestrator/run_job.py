"""오케스트레이터: configs/jobs.yaml에서 오늘 실행할 job을 골라 전체 파이프라인을 순서대로 돌린다.

[스케줄러] 매일 정해진 시간 트리거
  -> ① Product Scout: 상품 후보 수집
  -> ② Capture: 상세페이지 이미지 확보
  -> ③ Copywriter: 본문/캡션 생성
  -> ④ QA: 실패 시 Copywriter 재시도(최대 1회) 후에도 실패하면 사람에게 알리고 중단
  -> ⑤ Assembler: HTML 조립
  -> ⑥ Publisher: 임시저장 (완전 발행은 사람 승인 후 별도 실행)
  -> ⑦ Notifier: 승인 요청 알림
"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

load_dotenv()  # agents.publisher/copywriter가 임포트 시점에 env var를 읽으므로 먼저 실행

import adapters  # noqa: E402, F401  (import만으로 어댑터들을 AdapterRegistry에 등록)
from agents import (  # noqa: E402
    assembler,
    capture_agent,
    copywriter,
    notifier,
    product_scout,
    publisher,
)
from agents.qa_agent import QAFailure  # noqa: E402
from agents.qa_agent import check as run_qa  # noqa: E402
from common.models import JobConfig  # noqa: E402
from orchestrator.job_loader import load_jobs_for_today  # noqa: E402

MAX_COPYWRITER_RETRIES = 1


def run_job(job: JobConfig) -> None:
    print(f"[run_job] 시작: mall={job.mall} category={job.category} topic={job.topic}")

    products = product_scout.run(job)
    if not products:
        print("[run_job] 신규 상품이 없어 종료합니다.")
        return

    image_paths = capture_agent.run(products)

    body_html, feed_captions = copywriter.run(job, products)

    for attempt in range(MAX_COPYWRITER_RETRIES + 1):
        try:
            run_qa(job, body_html, products)
            break
        except QAFailure as e:
            print(f"[run_job] QA 실패 (시도 {attempt + 1}): {e}")
            if attempt >= MAX_COPYWRITER_RETRIES:
                print("[run_job] QA 재시도 초과. 사람 확인이 필요합니다.")
                return
            body_html, feed_captions = copywriter.run(job, products)

    post_html = assembler.run(job, body_html, products, image_paths)

    title = f"{job.topic} 추천 {len(products)}선"
    draft_result = publisher.save_draft(job, title, post_html)

    notifier.notify_draft_ready(job, title, draft_result)

    print(
        "[run_job] 임시저장 완료. 승인 후 발행하려면 "
        "python -m orchestrator.approve_and_publish 를 실행하세요."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="오늘 실행할 job들을 파이프라인으로 처리")
    parser.add_argument("--mall", help="특정 mall만 강제로 실행 (테스트용)")
    args = parser.parse_args()

    jobs = load_jobs_for_today()
    if args.mall:
        jobs = [j for j in jobs if j.mall == args.mall]

    if not jobs:
        print("오늘 예정된 job이 없습니다.")
        return

    for job in jobs:
        try:
            run_job(job)
        except Exception as e:  # noqa: BLE001
            print(f"[run_job] {job.mall} 처리 중 오류: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
