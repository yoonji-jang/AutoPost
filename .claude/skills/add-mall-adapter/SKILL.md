---
name: add-mall-adapter
description: 새 쇼핑몰을 AutoPost 파이프라인에 추가할 스켈레톤(adapter + SKILL.md + AdapterRegistry 등록 + configs/jobs.yaml 항목)을 생성한다. 사용자가 "새 몰 추가해줘", "무신사/쿠팡 어댑터 만들어줘" 라고 할 때 사용.
disable-model-invocation: true
---

인자: `$ARGUMENTS` = `<mall_key> <style_profile>` (예: `musinsa musinsa_streetwear`)

`$ARGUMENTS`가 비어 있으면 mall_key(영문 소문자, 폴더/registry 키로 쓰임)와 style_profile 이름을
사용자에게 먼저 물어볼 것.

## 해야 할 일

1. `adapters/<mall_key>_mcp/` 생성
   - `adapter.py` — `adapters/_base_adapter.py`의 `MallAdapter` Protocol을 구현하는 `<MallKey>Adapter` 클래스.
     `zigzag_mcp/adapter.py`와 `ohouse_mcp/adapter.py`를 템플릿으로 삼되, 4개 메서드
     (search_products, get_product_detail, check_stock, get_product_url)를 전부
     `NotImplementedError("TODO: ...")` 스텁으로 두고, 파일 끝에
     `AdapterRegistry.register("<mall_key>", <MallKey>Adapter())` 를 추가한다.
   - `__init__.py` — `from adapters.<mall_key>_mcp.adapter import <MallKey>Adapter  # noqa: F401`
2. `adapters/__init__.py`에 새 몰 모듈을 import 목록에 추가해서 앱 시작 시 자동 등록되게 한다.
3. `skills/<style_profile>/SKILL.md` 생성 — `skills/zigzag_zipmag/SKILL.md`,
   `skills/ohouse_living/SKILL.md`를 참고해 문체/금지 표현/출력물/입력 섹션을 갖춘 톤 가이드 작성.
   실제 톤 규칙은 사용자에게 물어보고 채운다 (모르면 초안만 남기고 TODO 표시).
4. `configs/jobs.yaml`에 새 job 항목 하나 추가 (mall, category, topic, item_count, style_profile,
   publish_target: naver_blog, schedule는 사용자에게 물어보거나 미정이면 생략).
5. `python -m py_compile adapters/<mall_key>_mcp/adapter.py adapters/__init__.py`로 문법 확인.
6. 제휴/크리에이터 프로그램 API가 있는지 먼저 확인하라는 점, 없으면 스크래핑은 이 어댑터 안에만
   격리해야 한다는 점을 사용자에게 상기시킨다 (CLAUDE.md 참고).

완료 후 무엇을 만들었는지 간단히 요약하고, 실제 API/스크래핑 로직 구현은 별도 작업임을 알린다.
