---
name: run-pipeline
description: orchestrator.run_job(경로 A, 전체 자동/API 크레딧 필요)을 실행해 특정 mall(또는 오늘 스케줄 전체)의 파이프라인을 수동으로 테스트한다. 크레딧 없이 테스트하려면 write-daily-post 스킬(경로 B)을 대신 쓴다. 사용자가 "파이프라인 돌려봐", "지그재그 job 테스트해줘" 라고 할 때 사용.
disable-model-invocation: true
---

인자: `$ARGUMENTS` = `<mall_key>` (생략하면 오늘 요일 스케줄에 걸린 job 전체 실행)

이 스킬은 **경로 A(전체 자동)**를 테스트한다 — `agents/copywriter.py`가 Anthropic API를 직접
호출하므로 `ANTHROPIC_API_KEY`에 크레딧이 있어야 QA 단계까지 진행된다. 크레딧이 없다면
`/write-daily-post`(경로 B, Claude Code가 직접 카피라이터 역할)를 대신 쓰라고 안내한다.

## 해야 할 일

1. `.env` 파일 존재 확인. 없으면 `.env.example`을 복사하라고 안내하고 중단
   (`ANTHROPIC_API_KEY`, `NAVER_CLIENT_ID/SECRET/REFRESH_TOKEN` 필요).
2. 의존성 설치 여부가 불확실하면 `pip show anthropic playwright jinja2 pyyaml requests python-dotenv markupsafe`로 빠르게 확인.
3. 실행 (반드시 `-m` 모듈 문법 — 직접 경로 실행은 `ModuleNotFoundError` 남):
   - `$ARGUMENTS`가 있으면 `python -m orchestrator.run_job --mall $ARGUMENTS`
   - 없으면 `python -m orchestrator.run_job`
4. 어댑터가 아직 `NotImplementedError` 스텁이면 그 지점에서 실패하는 게 정상이다 —
   에러 메시지를 그대로 사용자에게 보여주고, `/add-mall-adapter`로 먼저 어댑터를 구현해야 한다고 안내한다.
5. `anthropic.BadRequestError: ... credit balance is too low`가 나면 크레딧 문제임을 알리고
   `/write-daily-post`(경로 B)를 대신 제안한다.
6. 성공 시 임시저장 결과(`Publisher.save_draft` 반환값)와 Notifier 알림 내용을 요약해서 보여준다.
   실제 발행은 이 스킬의 범위가 아니다 — `orchestrator.approve_and_publish`는 사람이 직접 승인 후 실행.
