"""prepare_job.py + (사람 또는 Claude Code가 작성한) copy.json을 이어받아
QA→Assembler까지 마무리한다.

API 크레딧이 필요 없다 — agents.copywriter/publisher/notifier를 임포트하지 않는다.
결과는 drafts/<job_id>.html로 저장되는 초안이며, 네이버 발행은 별도(현재 보류 중)다.

사용법:
    python -m orchestrator.finish_job zigzag_2026-07-29
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import adapters  # noqa: F401  (import만으로 어댑터들을 AdapterRegistry에 등록)
from agents import assembler
from agents.qa_agent import QAFailure
from agents.qa_agent import check as run_qa
from common.models import JobConfig, Product

STATE_DIR = Path(__file__).resolve().parent.parent / ".autopost_state"
DRAFTS_DIR = Path(__file__).resolve().parent.parent / "drafts"


def finish(job_id: str) -> Path:
    job_dir = STATE_DIR / job_id
    input_path = job_dir / "input.json"
    copy_path = job_dir / "copy.json"

    if not input_path.exists():
        raise SystemExit(f"{input_path} 없음 — 먼저 prepare_job.py를 실행하세요.")
    if not copy_path.exists():
        raise SystemExit(
            f"{copy_path} 없음 — SKILL.md 규칙에 따라 body/feed_captions를 작성해 저장하세요."
        )

    with open(input_path, encoding="utf-8") as f:
        input_data = json.load(f)
    with open(copy_path, encoding="utf-8") as f:
        copy_data = json.load(f)

    job = JobConfig(**input_data["job"])
    products = [Product(**p) for p in input_data["products"]]
    image_paths = input_data["image_paths"]
    body_text = copy_data["body"]
    feed_captions = copy_data["feed_captions"]

    print(f"[finish_job] QA 검사 중... ({job_id})")
    try:
        run_qa(job, body_text, products)
    except QAFailure as e:
        raise SystemExit(
            f"QA 실패: {e}\ncopy.json의 body를 수정한 뒤 다시 실행하세요."
        ) from e

    post_html = assembler.run(job, body_text, products, image_paths)

    DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = DRAFTS_DIR / f"{job_id}.html"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(post_html)

    captions_path = DRAFTS_DIR / f"{job_id}_captions.json"
    with open(captions_path, "w", encoding="utf-8") as f:
        json.dump(feed_captions, f, ensure_ascii=False, indent=2)

    print(f"[finish_job] QA 통과. 초안 저장됨: {out_path}")
    print(f"[finish_job] 인스타 피드 캡션: {captions_path}")
    print("[finish_job] 네이버 발행은 보류 중 — 확인 후 필요 시 수동으로 게시하세요.")
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="QA→Assembler를 마무리해 초안 HTML을 만든다")
    parser.add_argument("job_id", help="prepare_job.py가 출력한 job_id (예: zigzag_2026-07-29)")
    args = parser.parse_args()
    finish(args.job_id)


if __name__ == "__main__":
    main()
