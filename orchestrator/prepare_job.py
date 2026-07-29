"""Copywriter(Claude API 호출) 이전까지만 실행하는 준비 단계.

Product Scout + Capture Agent만 돌려서 상품/이미지 데이터를 JSON으로 저장한다.
API 크레딧이 전혀 필요 없다 — agents.copywriter/publisher/notifier를 임포트하지 않는다.

이후 "글쓰기"는 사람이 직접(또는 Claude Code 스케줄 에이전트가) 이 JSON을 읽어서
body/feed_captions를 작성해 copy.json으로 저장하고, finish_job.py로 이어간다.
자세한 흐름은 .claude/skills/write-daily-post/SKILL.md 참고.

사용법:
    python -m orchestrator.prepare_job --mall zigzag
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from datetime import date
from pathlib import Path

import adapters  # noqa: F401  (import만으로 어댑터들을 AdapterRegistry에 등록)
from agents import capture_agent, product_scout
from orchestrator.job_loader import load_jobs_for_today

STATE_DIR = Path(__file__).resolve().parent.parent / ".autopost_state"


def prepare(job) -> Path:  # noqa: ANN001
    print(f"[prepare_job] 시작: mall={job.mall} category={job.category} topic={job.topic}")

    products = product_scout.run(job)
    if not products:
        print("[prepare_job] 신규 상품이 없어 종료합니다.")
        raise SystemExit(0)

    image_paths = capture_agent.run(products)

    job_id = f"{job.mall}_{date.today().isoformat()}"
    job_dir = STATE_DIR / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    input_data = {
        "job_id": job_id,
        "job": dataclasses.asdict(job),
        "products": [dataclasses.asdict(p) for p in products],
        "image_paths": image_paths,
    }
    input_path = job_dir / "input.json"
    with open(input_path, "w", encoding="utf-8") as f:
        json.dump(input_data, f, ensure_ascii=False, indent=2)

    print(f"[prepare_job] 저장됨: {input_path}")
    print(
        f"[prepare_job] 다음 단계: {job.style_profile}용 SKILL.md 규칙에 따라 "
        f"body/feed_captions를 작성해 {job_dir / 'copy.json'} 로 저장한 뒤 "
        f"`python -m orchestrator.finish_job {job_id}` 실행"
    )
    return input_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Copywriter 이전 단계(상품/이미지 수집)만 실행")
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
            prepare(job)
        except SystemExit:
            raise
        except Exception as e:  # noqa: BLE001
            print(f"[prepare_job] {job.mall} 처리 중 오류: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()
