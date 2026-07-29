---
name: write-daily-post
description: API 크레딧 없이 매일 블로그 초안을 만든다. 트렌드 조사로 오늘의 주제를 직접 정하고, prepare_job.py로 상품/이미지를 모으고, Claude Code(자신)가 직접 카피라이터 역할로 본문/캡션을 쓴 뒤, finish_job.py로 QA·조립까지 마무리해서 메일로 보낸다. 스케줄된 자동 실행 또는 사용자가 "오늘 초안 써줘"라고 할 때 사용.
disable-model-invocation: true
---

인자: `$ARGUMENTS` = `<mall_key>` (생략하면 오늘 요일 스케줄에 걸린 job 전체 처리)

이 스킬은 `agents/copywriter.py`(Anthropic API 직접 호출, 크레딧 필요)를 쓰지 않는다.
대신 "주제 선정"과 "글쓰기" 둘 다 **지금 실행 중인 나 자신(Claude Code)** 이 대신한다 —
구독 한도 안에서 무료로 동작하는 게 핵심이다.

## 절차

1. **오늘 job 확인**: 실행
   ```
   python -c "from orchestrator.job_loader import load_jobs_for_today; [print(f'{j.mall}|{j.category}|{j.style_profile}') for j in load_jobs_for_today()]"
   ```
   `$ARGUMENTS`가 있으면 그 mall만 남긴다. 결과가 없으면 "오늘 예정된 job 없음"을 보고하고 종료.

2. **주제 선정** (job마다 반복):
   - `python -m tools.topic_history recent <mall>` 로 최근 3주 내 이 몰에서 다룬 주제 목록을 확인한다
     (아래 목록과 겹치는 주제는 고르지 않는다).
   - 오늘 날짜/계절을 감안하고, WebSearch로 `<category>` 관련 "요즘 트렌드", "인기 검색어",
     "~월 유행" 등을 조사해서 **검색 유입이 많을 만한 구체적인 주제 하나**를 고른다.
     예: "여성의류 > 블라우스" + 7월이면 "여름 하객룩"류가 아니라, 실제로 그 시기 유행하는
     더 구체적인 키워드(소재/핏/시즌 이슈 등)를 조사해서 정할 것 — `configs/jobs.yaml`의
     `topic` 값은 최초 예시일 뿐이니 그대로 재사용하지 않는다.
   - `python -m tools.topic_history record <mall> "<선택한 topic>"` 으로 기록한다.

3. **준비**: 실행
   ```
   python -m orchestrator.prepare_job --mall <mall> --topic "<2단계에서 고른 topic>"
   ```
   출력에서 `job_id`(예: `zigzag_2026-07-29`)와 `.autopost_state/<job_id>/input.json` 경로를 확인.
   "신규 상품이 없어 종료"면 해당 job은 건너뛰고 다음 job으로.

4. **input.json 읽기**: `job.style_profile`, `products`(product_id/name/price/url/category),
   `image_paths`를 확인한다.

5. **스타일 규칙 읽기**: `skills/<style_profile>/SKILL.md`를 읽는다 (예: `skills/zigzag_zipmag/SKILL.md`).
   여기 적힌 문체/금지 표현 규칙을 그대로 따른다 — 이 프로젝트의 다른 몰에도 같은 방식으로
   확장되므로 규칙을 임의로 무시하거나 완화하지 않는다.

6. **직접 작성**: 아래 형식으로 본문과 캡션을 쓴다.
   - `body`: 네이버 블로그 본문. **HTML 태그 없이 일반 텍스트**로 쓰고, 문단 사이는 **빈 줄(\n\n)**로
     구분한다 (조립 단계에서 자동으로 `<p>`로 변환됨).
   - `feed_captions`: `{"<product_id>": "짧은 인스타 캡션", ...}` — products의 모든 product_id를 키로 포함.

7. **copy.json 저장**: Write 도구로 `.autopost_state/<job_id>/copy.json`에 아래 형식으로 저장.
   ```json
   { "body": "...", "feed_captions": { "165463199": "...", "...": "..." } }
   ```

8. **마무리**: `python -m orchestrator.finish_job <job_id>` 실행.
   - QA 실패(금지어/품절)로 종료되면, 에러 메시지를 보고 **본인이 직접** copy.json의 `body`를
     규칙에 맞게 고쳐서 다시 7→8단계를 재시도한다 (최대 1~2회). 계속 실패하면 사람에게 보고하고 중단.
   - 성공하면 `drafts/<job_id>.html`(초안)과 `drafts/<job_id>_captions.json`(인스타 캡션)이 생성된다.

9. **메일 발송**: 성공한 job마다
   ```
   python -m tools.send_email <job_id> drafts/<job_id>.html
   ```
   `NAVER_SMTP_USER`/`NAVER_SMTP_APP_PASSWORD`/`NOTIFY_EMAIL_TO`가 `.env`에 없거나 발송이
   실패하면, 결과는 이미 로컬 `drafts/<job_id>.html`에 저장되어 있으니 그 경로를 알리는 것으로
   충분하다 (자동 재시도하지 않음). 이 결과물은 git에 커밋하지 않는다.

10. **알림**: PushNotification으로 결과를 한 줄로 알린다 (터미널이 없는 완전 백그라운드 실행이면
    전송되지 않을 수 있는데, 정상이다 — 메일이 주 배송 수단이다).
    - 성공: `"오늘의 블로그 초안 메일 발송됨: <job_id> — 주제: <topic> (상품 N개, QA 통과)"`
    - 신규 상품 없음/실패: 이유를 포함해 알림 (예: `"AutoPost: 오늘 지그재그 신규 상품 없음"`,
      `"AutoPost: QA 재시도 2회 실패, 확인 필요"`)

11. **보고**: 어떤 job을 처리했는지, 고른 주제와 그 근거(어떤 트렌드를 참고했는지), 초안 경로,
    메일 발송 여부, QA 결과를 간단히 요약해서 알려준다. 네이버 발행은 이 스킬의 범위가 아니다 —
    사람이 초안을 확인 후 별도로 처리한다 (현재 네이버 연동 자체가 보류 상태임을 CLAUDE.md 참고).
