"""주제(topic) 로테이션 이력을 기록해 최근에 다룬 주제를 반복하지 않게 한다.

configs/jobs.yaml의 topic은 고정값이라 그대로 두면 매번 똑같은 주제로 검색하게 된다.
write-daily-post 스킬이 매번 실행 전 이 모듈로 최근 이력을 확인하고, 트렌드 조사 후
고른 새 주제를 기록한다.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

HISTORY_PATH = Path(__file__).resolve().parent.parent / "history_db" / "topic_history.json"


def _load() -> list[dict]:
    if not HISTORY_PATH.exists():
        return []
    with open(HISTORY_PATH, encoding="utf-8") as f:
        return json.load(f)


def recent_topics(mall: str, within_days: int = 21) -> list[str]:
    """최근 N일 내 해당 몰에서 다룬 topic 목록 (최신순, 중복 제거)."""
    cutoff = (date.today() - timedelta(days=within_days)).isoformat()
    entries = [e for e in _load() if e["mall"] == mall and e["date"] >= cutoff]
    entries.sort(key=lambda e: e["date"], reverse=True)
    seen: list[str] = []
    for e in entries:
        if e["topic"] not in seen:
            seen.append(e["topic"])
    return seen


def record_topic(mall: str, topic: str) -> None:
    entries = _load()
    entries.append({"date": date.today().isoformat(), "mall": mall, "topic": topic})
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("사용법: python -m tools.topic_history recent <mall> | record <mall> <topic>")
        raise SystemExit(1)

    command, mall = sys.argv[1], sys.argv[2]
    if command == "recent":
        for t in recent_topics(mall):
            print(t)
    elif command == "record":
        if len(sys.argv) < 4:
            print("record에는 topic 인자가 필요합니다.")
            raise SystemExit(1)
        record_topic(mall, sys.argv[3])
        print(f"기록됨: {mall} / {sys.argv[3]}")
    else:
        print(f"알 수 없는 명령: {command}")
        raise SystemExit(1)
