"""⑦ Notifier: 결과 요약을 사람에게 전달하고 발행 승인을 요청한다.

TODO: Slack 웹훅 또는 이메일 연동. 지금은 콘솔 출력으로 대체.
"""

from __future__ import annotations

import os

import requests

from common.models import JobConfig

SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")


def notify_draft_ready(job: JobConfig, title: str, draft_result: dict) -> None:
    message = (
        f"[{job.mall}/{job.category}] '{title}' 임시저장 완료.\n"
        f"확인 후 발행해주세요: {draft_result}"
    )

    if SLACK_WEBHOOK_URL:
        requests.post(SLACK_WEBHOOK_URL, json={"text": message}, timeout=10)
    else:
        print(message)
