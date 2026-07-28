# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

AutoPost — 여러 쇼핑몰(지그재그, 오늘의집, ...)에서 상품을 골라 네이버 블로그 글로 자동 발행하는
멀티 에이전트 파이프라인. 사람 손 최소화가 목표이며, 발행 직전 한 번의 검수 게이트를 둔다.

## Architecture

오케스트레이터-워커 패턴. `configs/jobs.yaml`의 job(mall/category/topic/style_profile)만 바꾸면
같은 파이프라인 코드로 다른 쇼핑몰·카테고리를 처리한다.

```
[스케줄러] → Product Scout → Capture → Copywriter → QA → Assembler → Publisher(임시저장) → Notifier(승인 요청)
```

- `orchestrator/run_job.py` — 파이프라인 진입점. `configs/jobs.yaml`의 `schedule` 필드로 오늘 실행할 job을 고름
- `orchestrator/approve_and_publish.py` — 사람이 임시저장 글을 확인한 뒤 실제 발행으로 전환
- `agents/` — 7개 에이전트(product_scout, capture_agent, copywriter, qa_agent, assembler, publisher, notifier). 각자 좁은 역할 하나만 수행 (최소 권한 원칙)
- `adapters/_base_adapter.py` — `MallAdapter` Protocol(search_products/get_product_detail/check_stock/get_product_url)과 `AdapterRegistry`. 새 어댑터는 모듈 import 시점에 `AdapterRegistry.register()`로 자기 자신을 등록한다 (`adapters/__init__.py` 참고)
- `skills/<style_profile>/SKILL.md` — 몰별 카피 톤 규칙. `agents/copywriter.py`가 `job.style_profile`로 골라 시스템 프롬프트에 삽입
- `tools/` — 몰 무관 범용 유틸(playwright_capture, html_assembler, qa_checker, dedup_checker, naver_oauth_client)
- `history_db/postings.db` — (mall, category, product_id) 복합키로 중복 게시 방지. `tools/dedup_checker.py`가 최초 호출 시 스키마를 생성함

## 새 쇼핑몰 추가하기

`adapters/<mall>_mcp/` 어댑터 하나 + `skills/<style_profile>/SKILL.md` 하나만 만들면 되고,
나머지 6개 에이전트는 손댈 필요가 없다. `/add-mall-adapter` 스킬로 스켈레톤을 생성할 수 있다.

## Commands

```
pip install -r requirements.txt
playwright install chromium        # Capture Agent가 사용하는 헤드리스 브라우저 설치

python orchestrator/run_job.py                # 오늘 요일(schedule)에 해당하는 job 전부 실행
python orchestrator/run_job.py --mall zigzag  # 특정 mall만 강제 실행 (테스트용)
python -m py_compile <file>.py                # 문법 검사 (린터 미도입 상태의 최소 안전망)
```

`.env.example`을 `.env`로 복사하고 `ANTHROPIC_API_KEY`, `NAVER_CLIENT_ID/SECRET/REFRESH_TOKEN`을 채워야 실행 가능.

## 중요한 미구현/불확실 지점 (TODO)

- `adapters/zigzag_mcp` — **구현 완료**. 제휴 프로그램이 없어(2026-07 확인) 사이트 내부 공개 GraphQL API
  (`api.zigzag.kr/api/2/graphql/GetSearchResult`, `GetCatalogProductDetailPageOption`)를 그대로 호출.
  쿠키/로그인 불필요, `requests`만으로 동작 확인 완료. 쿼리 문자열은 `queries/*.graphql`에 원본 그대로 보관 —
  사이트 스키마가 바뀌면 브라우저 네트워크 탭에서 재캡처해서 교체해야 함
- `adapters/ohouse_mcp` — **보류**. `ohou.se`는 Akamai 엣지 WAF가 모든 요청(Playwright, 순수 `requests`
  둘 다)을 403으로 차단함. 헤더/셀렉터 문제가 아니라 네트워크 단 봇 차단이라 우회는 시도하지 않기로 함.
  재개하려면: (a) 오늘의집 파트너스/제휴 API 공식 신청, 또는 (b) 봇 차단이 약한 다른 리빙 카테고리 몰로 교체
- `tools/naver_oauth_client.py` — 요청 파라미터명(title/contents/blogId 등)은 네이버 개발자센터 최신 문서
  기준으로 반드시 재검증. 코드는 구조만 맞춰둔 상태. 최초 1회 OAuth 인가(authorization code → refresh_token)
  플로우도 아직 없음
- 테스트 스위트 없음. 변경 후에는 최소한 `python -m py_compile` + `ruff check .`로 확인할 것

## 안전 기본값

- `Publisher`는 기본이 `save_draft`(임시저장)다. `publish()`(실제 발행)는 `Notifier` 알림 후 사람이
  승인했을 때만 `approve_and_publish.py`로 별도 호출한다 — 완전 무검수 자동 발행으로 바꾸지 말 것
- `QA/Compliance`는 실패 시 Copywriter를 1회만 재시도하고, 그래도 실패하면 발행하지 않고 사람에게 알린다
  (`orchestrator/run_job.py`의 `MAX_COPYWRITER_RETRIES`)
