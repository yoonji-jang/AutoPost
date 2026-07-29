# AutoPost

여러 쇼핑몰(지그재그, 오늘의집, ...)에서 상품을 골라 네이버 블로그 글을 자동으로 작성·발행하는
멀티 에이전트 파이프라인. 사람 손 최소화가 목표이며, 발행 직전 한 번의 검수 게이트를 둔다.

## 아키텍처

오케스트레이터-워커 패턴. `configs/jobs.yaml`의 job 설정(mall/category/topic/style_profile)만
바꾸면 같은 파이프라인 코드로 다른 쇼핑몰·카테고리를 처리할 수 있다.

Product Scout/Capture/QA/Assembler는 두 실행 경로가 공유하고, "글쓰기"만 방식이 다르다.

- **경로 A (전체 자동, Anthropic API 크레딧 필요)**: `run_job.py`가 Copywriter까지 전부 자동 호출
- **경로 B (무료, 지금 쓰는 경로)**: Claude Code가 먼저 WebSearch+`topic_history`로 오늘의 주제를
  직접 정하고, `prepare_job.py --topic "..."`로 상품/이미지만 모으고,
  `skills/<style_profile>/SKILL.md` 규칙에 따라 직접 글을 쓴 뒤 `finish_job.py`로 QA·조립 마무리,
  `send_email.py`로 이메일 발송까지. API 키 없이도 동작한다 — 자세한 절차는
  `.claude/skills/write-daily-post/SKILL.md` 참고. 매주 월/수/금 08:00 KST에 로컬 Windows 작업
  스케줄러(`AutoPost-WriteDailyPost`)로 자동 실행됨

```
경로 A: [스케줄러] → Product Scout → Capture → Copywriter(API) → QA → Assembler → Publisher(임시저장) → Notifier
경로 B: (Claude Code가 트렌드 조사로 주제 선정) → prepare_job → Product Scout → Capture
        → (Claude Code가 직접 작성) → finish_job → QA → Assembler → drafts/*.html → 이메일 발송
```

| 구성 요소 | 역할 |
|---|---|
| `orchestrator/job_loader.py` | `configs/jobs.yaml`에서 오늘 실행할 job 선택 (공통 로직) |
| `orchestrator/prepare_job.py` / `finish_job.py` | 경로 B의 앞/뒤 단계 (크레딧 불필요) |
| `orchestrator/run_job.py` | 경로 A 진입점 (크레딧 필요) |
| `orchestrator/approve_and_publish.py` | 사람이 임시저장 글을 확인한 뒤 실제 발행으로 전환 (네이버 연동 보류 중) |
| `agents/` | 7개 에이전트 (product_scout, capture_agent, copywriter, qa_agent, assembler, publisher, notifier) |
| `adapters/` | 몰별 어댑터. `_base_adapter.py`의 `MallAdapter` Protocol을 구현 |
| `skills/<style_profile>/SKILL.md` | 몰별 카피 톤 규칙 |
| `tools/` | 몰 무관 범용 유틸 (캡쳐, HTML 조립, QA 검사, 중복 방지, 네이버 OAuth, 이메일 발송, 주제 이력) |
| `configs/jobs.yaml` | 몰/카테고리/스케줄 설정. `topic`은 최초 예시일 뿐 — 실행마다 트렌드 조사로 덮어씀 |
| `history_db/postings.db` | 중복 게시 방지용 이력 (최초 실행 시 자동 생성) |
| `history_db/topic_history.json` | 최근 3주 내 다룬 주제 이력 (같은 topic 반복 방지) |
| `.autopost_state/`, `drafts/` | 경로 B의 중간/결과 산출물 (gitignore됨, 배송은 이메일로) |

자세한 설계 배경과 안전 기본값은 [`CLAUDE.md`](./CLAUDE.md) 참고.

## 설치

```bash
pip install -r requirements.txt
playwright install chromium   # Capture Agent 폴백(스크린샷)용 헤드리스 브라우저
```

`.env.example`을 `.env`로 복사하고 값을 채운다. **경로 B만 쓴다면 이 단계는 건너뛰어도 된다** —
Product Scout/Capture/QA/Assembler는 자격증명이 필요 없다.

```bash
cp .env.example .env
```

| 변수 | 설명 |
|---|---|
| `ANTHROPIC_API_KEY` | 경로 A의 Copywriter가 Claude API 호출에 사용 (경로 B는 불필요) |
| `NAVER_CLIENT_ID` / `NAVER_CLIENT_SECRET` / `NAVER_REFRESH_TOKEN` | 네이버 블로그 글쓰기 오픈 API OAuth (현재 발행 자체가 보류 중) |
| `SLACK_WEBHOOK_URL` | (선택) Notifier가 콘솔 출력 대신 Slack으로 알림 |
| `NAVER_SMTP_USER` / `NAVER_SMTP_APP_PASSWORD` / `NOTIFY_EMAIL_TO` | 경로 B의 초안을 이메일로 보낼 때 사용 (네이버 SMTP) |

## 실행

**중요**: 반드시 `-m` 모듈 문법으로 실행할 것 (`python orchestrator/run_job.py`처럼 직접 경로로
실행하면 내부 패키지 import가 깨져서 `ModuleNotFoundError`가 난다).

### 경로 B — 무료 (지금 쓰는 방식)

가장 간단한 방법은 Claude Code에서 `/write-daily-post` 실행 (주제 선정부터 메일 발송까지 전부 처리).
수동으로 단계를 밟으려면:

```bash
python -m tools.topic_history recent zigzag       # 최근 다룬 주제 확인 (반복 회피용)
python -m orchestrator.prepare_job --mall zigzag --topic "플리츠 블라우스"
# .autopost_state/<job_id>/input.json 생성됨
# → 직접 copy.json 작성 (body/feed_captions)

python -m orchestrator.finish_job <job_id>
# QA + HTML 조립 → drafts/<job_id>.html, drafts/<job_id>_captions.json 생성

python -m tools.send_email <job_id> drafts/<job_id>.html   # 이메일로 발송
```

매주 월/수/금 08:00 KST에는 로컬 Windows 작업 스케줄러(`AutoPost-WriteDailyPost`)가
`run_write_daily_post.bat`를 통해 위 과정 전체를 자동으로 실행한다.

### 경로 A — 전체 자동 (API 크레딧 필요)

```bash
python -m orchestrator.run_job                 # 오늘 스케줄에 걸린 job 전부 실행
python -m orchestrator.run_job --mall zigzag   # 특정 mall만 강제 실행 (테스트용)
```

파이프라인은 발행 직전에 **임시저장**까지만 자동으로 하고 멈춘다. 확인 후 실제 발행하려면
(네이버 연동 재개 후):

```bash
python -m orchestrator.approve_and_publish --mall zigzag --category "..." --title "..." --html-file draft.html
```

## 새 쇼핑몰 추가하기

`adapters/<mall>_mcp/` 어댑터 하나 + `skills/<style_profile>/SKILL.md` 하나만 만들면 되고,
나머지 에이전트는 손댈 필요가 없다. Claude Code에서 `/add-mall-adapter` 스킬로 스켈레톤을 생성할 수 있다.

## 현재 상태 (미구현/TODO)

- `adapters/zigzag_mcp` — 구현 완료 (지그재그 내부 공개 GraphQL API 사용, 제휴 프로그램 없음 확인됨)
- `adapters/ohouse_mcp` — 보류. Akamai WAF가 모든 요청을 403 차단해서 스크래핑 불가 판정.
  파트너스 API 신청 또는 다른 몰로 교체 필요
- 네이버 발행 — 보류. Client ID/Secret은 있으나 refresh_token 발급(OAuth 인가) 미완료,
  API 파라미터도 재검증 필요
- Anthropic API 크레딧 없음 — 경로 A는 QA 이전까지만 테스트 가능. 경로 B가 현재 사실상의 운영 경로
- 스케줄링 구성 완료 — 로컬 Windows 작업 스케줄러(월/수/금 08:00 KST)로 자동 실행됨
- 테스트 스위트 없음
