"""configs/jobs.yaml에서 오늘 실행할 job을 골라내는 공통 로직.

API 크레딧이 필요한 agents(copywriter/publisher/notifier)를 전혀 임포트하지 않는다 —
prepare_job.py처럼 자격증명 없이도 동작해야 하는 스크립트가 이 모듈만 의존하게 하기 위함.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import yaml

from common.models import JobConfig

CONFIG_PATH = Path(__file__).resolve().parent.parent / "configs" / "jobs.yaml"

WEEKDAY_CODES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def load_jobs_for_today(today: datetime | None = None) -> list[JobConfig]:
    today = today or datetime.now()
    code = WEEKDAY_CODES[today.weekday()]

    with open(CONFIG_PATH, encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    jobs = []
    for entry in raw.get("jobs", []):
        schedule = {s.strip() for s in entry.get("schedule", "").split(",") if s.strip()}
        if not schedule or code in schedule:
            jobs.append(
                JobConfig(
                    **{k: v for k, v in entry.items() if k != "schedule"},
                    schedule=entry.get("schedule"),
                )
            )

    return jobs
