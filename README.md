# AutoPost

여러 쇼핑몰(지그재그, 오늘의집, ...)에서 상품을 골라 네이버 블로그 글을 자동으로 작성·발행하는
멀티 에이전트 파이프라인. 사람 손 최소화가 목표이며, 발행 직전 한 번의 검수 게이트를 둔다.

## 아키텍처

오케스트레이터-워커 패턴. `configs/jobs.yaml`의 job 설정(mall/category/topic/style_profile)만
바꾸면 같은 파이프라인 코드로 다른 쇼핑몰·카테고리를 처리할 수 있다.

```
[스케줄러] → Product Scout → Capture → Copywriter → QA → Assembler → Publisher(임시저장) → Notifier(승인 요청)
```

| 구성 요소 | 역할 |
|---|---|
| `orchestrator/run_job.py` | 파이프라인 진입점. 오늘 요일 스케줄에 해당하는 job 실행 |
| `orchestrator/approve_and_publish.py` | 사람이 임시저장 글을 확인한 뒤 실제 발행으로 전환 |
| `agents/` | 7개 에이전트 (product_scout, capture_agent, copywriter, qa_agent, assembler, publisher, notifier) |
| `adapters/` | 몰별 어댑터. `_base_adapter.py`의 `MallAdapter` Protocol을 구현 |
| `skills/<style_profile>/SKILL.md` | 몰별 카피 톤 규칙 (Copywriter 시스템 프롬프트) |
| `tools/` | 몰 무관 범용 유틸 (캡쳐, HTML 조립, QA 검사, 중복 방지, 네이버 OAuth) |
| `configs/jobs.yaml` | 몰/카테고리/스케줄 설정 |
| `history_db/postings.db` | 중복 게시 방지용 이력 (최초 실행 시 자동 생성) |

자세한 설계 배경과 안전 기본값은 [`CLAUDE.md`](./CLAUDE.md) 참고.

## 설치

```bash
pip install -r requirements.txt
playwright install chromium   # Capture Agent가 사용하는 헤드리스 브라우저
```

`.env.example`을 `.env`로 복사하고 값을 채운다.

```bash
cp .env.example .env
```

| 변수 | 설명 |
|---|---|
| `ANTHROPIC_API_KEY` | Copywriter가 Claude API 호출에 사용 |
| `NAVER_CLIENT_ID` / `NAVER_CLIENT_SECRET` / `NAVER_REFRESH_TOKEN` | 네이버 블로그 글쓰기 오픈 API OAuth |
| `SLACK_WEBHOOK_URL` | (선택) Notifier가 콘솔 출력 대신 Slack으로 알림 |

## 실행

```bash
python orchestrator/run_job.py                 # 오늘 스케줄에 걸린 job 전부 실행
python orchestrator/run_job.py --mall zigzag   # 특정 mall만 강제 실행 (테스트용)
```

파이프라인은 발행 직전에 **임시저장**까지만 자동으로 하고 멈춘다. 확인 후 실제 발행하려면:

```bash
python orchestrator/approve_and_publish.py --mall zigzag --category "..." --title "..." --html-file draft.html
```

## 새 쇼핑몰 추가하기

`adapters/<mall>_mcp/` 어댑터 하나 + `skills/<style_profile>/SKILL.md` 하나만 만들면 되고,
나머지 에이전트는 손댈 필요가 없다. Claude Code에서 `/add-mall-adapter` 스킬로 스켈레톤을 생성할 수 있다.

## 현재 상태 (미구현/TODO)

- `adapters/zigzag_mcp`, `adapters/ohouse_mcp` — 실제 API/스크래핑 로직 미구현 (스텁 상태)
- `tools/naver_oauth_client.py` — 요청 파라미터는 네이버 개발자센터 최신 문서 기준 재검증 필요
- 테스트 스위트 없음
