# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AutoPost — 여러 쇼핑몰(지그재그, 오늘의집, ...)에서 상품을 골라 네이버 블로그 글로 자동 발행하는
멀티 에이전트 파이프라인. 사람 손 최소화가 목표이며, 발행 직전 한 번의 검수 게이트를 둔다.
네이버 발행 연동은 현재 보류 상태(아래 참고) — 지금은 초안(HTML) 생성까지가 실질 범위.

## Architecture

오케스트레이터-워커 패턴. `configs/jobs.yaml`의 job(mall/category/topic/style_profile)만 바꾸면
같은 파이프라인 코드로 다른 쇼핑몰·카테고리를 처리한다.

두 가지 실행 경로가 있다 (둘 다 Product Scout/Capture/QA/Assembler 로직을 그대로 공유):

**경로 A — 전체 자동 (`run_job.py`, Anthropic API 크레딧 필요)**
```
[스케줄러] → Product Scout → Capture → Copywriter(API) → QA → Assembler → Publisher(임시저장) → Notifier
```

**경로 B — 무료 (`prepare_job.py` + Claude Code + `finish_job.py`, 크레딧 불필요, 현재 운영 경로)**
```
(Claude Code가 WebSearch+topic_history로 오늘의 주제를 직접 선정 — /write-daily-post 스킬 1~2단계)
                                                          ↓
prepare_job.py --topic "..." → Product Scout → Capture → .autopost_state/<job_id>/input.json 저장
                                                          ↓
        (Claude Code가 SKILL.md 규칙대로 직접 글을 써서 copy.json 저장)
                                                          ↓
finish_job.py → QA → Assembler → drafts/<job_id>.html → send_email.py로 메일 발송
```
경로 B는 Anthropic API를 전혀 호출하지 않는다 — "주제 선정"과 "글쓰기" 둘 다 Claude Code
세션(구독 한도) 자신이 대신하기 때문. 매주 월/수/금 08:00 KST에 로컬 Windows 작업 스케줄러
(`AutoPost-WriteDailyPost`, `run_write_daily_post.bat`가 `claude -p "/write-daily-post"
--permission-mode bypassPermissions`를 실행)로 자동 트리거된다.

- `orchestrator/job_loader.py` — `configs/jobs.yaml`에서 오늘 실행할 job을 고르는 공통 로직 (자격증명 불필요, run_job/prepare_job 둘 다 사용)
- `orchestrator/run_job.py` — 경로 A 진입점
- `orchestrator/prepare_job.py` / `orchestrator/finish_job.py` — 경로 B의 앞/뒤 단계. `prepare_job.py --topic "..."`로 job.topic을 이번 실행에만 덮어쓸 수 있음. 자세한 절차는 `.claude/skills/write-daily-post/SKILL.md` 참고
- `orchestrator/approve_and_publish.py` — 사람이 임시저장 글을 확인한 뒤 실제 발행으로 전환 (네이버 연동 보류 중이라 현재 미사용)
- `agents/` — 7개 에이전트(product_scout, capture_agent, copywriter, qa_agent, assembler, publisher, notifier). 각자 좁은 역할 하나만 수행 (최소 권한 원칙). copywriter/publisher/notifier는 경로 B(prepare_job/finish_job)에서는 임포트되지 않음
- `adapters/_base_adapter.py` — `MallAdapter` Protocol(search_products/get_product_detail/check_stock/get_product_url)과 `AdapterRegistry`. 새 어댑터는 모듈 import 시점에 `AdapterRegistry.register()`로 자기 자신을 등록한다 (`adapters/__init__.py` 참고)
- `skills/<style_profile>/SKILL.md` — 몰별 카피 톤 규칙. `agents/copywriter.py`(경로 A) 또는 Claude Code 자신(경로 B, `/write-daily-post`)이 `job.style_profile`로 골라 따른다
- `tools/` — 몰 무관 범용 유틸(playwright_capture, html_assembler, qa_checker, dedup_checker, naver_oauth_client, send_email, topic_history)
- `history_db/postings.db` — (mall, category, product_id) 복합키로 중복 게시 방지. `tools/dedup_checker.py`가 최초 호출 시 스키마를 생성함
- `history_db/topic_history.json` — (date, mall, topic) 이력. `tools/topic_history.py`가 최근 3주 내 다룬 주제를
  조회/기록해 같은 topic 반복을 피하게 함 (`configs/jobs.yaml`의 `topic` 값은 최초 예시일 뿐, 실행마다
  WebSearch로 조사한 실제 트렌드로 덮어써야 함)
- `.autopost_state/`, `drafts/` — 경로 B의 중간/결과 산출물, gitignore됨 (배송은 git이 아니라 이메일로 함)

## 새 쇼핑몰 추가하기

`adapters/<mall>_mcp/` 어댑터 하나 + `skills/<style_profile>/SKILL.md` 하나만 만들면 되고,
나머지 6개 에이전트는 손댈 필요가 없다. `/add-mall-adapter` 스킬로 스켈레톤을 생성할 수 있다.

## Commands

**중요**: 패키지 간 상호 임포트 때문에 반드시 `-m` 모듈 문법으로 실행해야 한다.
`python orchestrator/run_job.py`처럼 직접 경로로 실행하면 `ModuleNotFoundError`가 난다
(AutoPost/ 루트가 아니라 orchestrator/가 sys.path에 잡히기 때문).

```
pip install -r requirements.txt
playwright install chromium              # Capture Agent 폴백(스크린샷)용 헤드리스 브라우저

python -m orchestrator.prepare_job --mall zigzag   # 경로 B: 상품/이미지만 수집 (크레딧 불필요)
python -m orchestrator.finish_job <job_id>         # 경로 B: copy.json 작성 후 QA+조립
python -m orchestrator.run_job --mall zigzag       # 경로 A: 전체 자동 (API 크레딧 필요)
python -m py_compile <file>.py && ruff check .     # 문법 검사 + 린트
```

`.env.example`을 `.env`로 복사하고 값을 채운다. 경로 B만 쓴다면 `ANTHROPIC_API_KEY`/`NAVER_*`는
당장 필요 없음 (Product Scout/Capture/QA/Assembler는 자격증명 없이 동작).

## 중요한 미구현/불확실 지점 (TODO)

- `adapters/zigzag_mcp` — **구현 완료**. 제휴 프로그램이 없어(2026-07 확인) 사이트 내부 공개 GraphQL API
  (`api.zigzag.kr/api/2/graphql/GetSearchResult`, `GetCatalogProductDetailPageOption`)를 그대로 호출.
  쿠키/로그인 불필요, `requests`만으로 동작 확인 완료. 쿼리 문자열은 `queries/*.graphql`에 원본 그대로 보관 —
  사이트 스키마가 바뀌면 브라우저 네트워크 탭에서 재캡처해서 교체해야 함
- `adapters/ohouse_mcp` — **보류**. `ohou.se`는 Akamai 엣지 WAF가 모든 요청(Playwright, 순수 `requests`
  둘 다)을 403으로 차단함. 헤더/셀렉터 문제가 아니라 네트워크 단 봇 차단이라 우회는 시도하지 않기로 함.
  재개하려면: (a) 오늘의집 파트너스/제휴 API 공식 신청, 또는 (b) 봇 차단이 약한 다른 리빙 카테고리 몰로 교체
- 네이버 발행(경로 A의 Publisher, `tools/naver_oauth_client.py`) — **보류**. Client ID/Secret은 `.env`에
  있으나 refresh_token 발급(최초 OAuth 인가)을 사용자가 아직 완료하지 않음. 요청 파라미터명
  (title/contents/blogId 등)도 네이버 개발자센터 최신 문서 기준 재검증 필요. 재개 전엔 경로 B로 초안까지만 생성
- Anthropic API 크레딧 없음 — 경로 A(`run_job.py`, `agents/copywriter.py`)는 크레딧 충전 전까지 QA 이후
  단계를 테스트할 수 없음. 그 전까지는 경로 B가 사실상의 운영 경로
- 스케줄링 구성 완료 — 로컬 Windows 작업 스케줄러(`AutoPost-WriteDailyPost`, 월/수/금 08:00 KST)로
  등록됨. 클라우드 routine(`/schedule`)은 시도했으나 결과물을 사람에게 전달할 방법(git push는
  보류, 이메일 MCP 커넥터 미연결)이 마땅치 않아 로컬 방식으로 전환함
- 테스트 스위트 없음. 변경 후에는 최소한 `python -m py_compile` + `ruff check .`로 확인할 것

## 안전 기본값

- `Publisher`는 기본이 `save_draft`(임시저장)다. `publish()`(실제 발행)는 `Notifier` 알림 후 사람이
  승인했을 때만 `approve_and_publish.py`로 별도 호출한다 — 완전 무검수 자동 발행으로 바꾸지 말 것
- `QA/Compliance`는 실패 시 Copywriter를 재시도하고(경로 A: 최대 1회 자동 재호출, 경로 B: Claude Code가
  직접 고쳐서 재시도), 그래도 실패하면 발행하지 않고 사람에게 알린다
