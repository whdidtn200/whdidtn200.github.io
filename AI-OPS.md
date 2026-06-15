# AI Operations

MALT Tech Blog는 `AI가 운영 사실을 숨기지 않는` 기술 발행 시스템입니다.

## 운영 방식

1. **수집**
   MALT가 논문, GitHub 저장소, 기술 문서, 산업 동향 소스를 수집합니다.
2. **초안 생성**
   수집한 소스를 바탕으로 제목 후보, 핵심 요약, 본문 초안을 생성합니다.
3. **품질 점검**
   출처 존재 여부, 섹션 구조, 길이, 중복 위험을 검사합니다.
4. **발행 준비**
   품질 기준을 통과한 글만 정적 페이지로 반영합니다.

## 자동 초안 입력

- `content/archive/sources/`에 JSON 소스 메모를 보관합니다.
- 기존 `posts/`, `malt/`, `phm/`, `ai/` 아래 논문 프리뷰 글을 source JSON으로 변환해 재사용할 수 있습니다.
- `python3 scripts/generate_draft.py <json 파일>`을 실행하면 `content/drafts/`에 Markdown 초안이 생성됩니다.
- 생성된 초안은 `운영자 해석`, `현업 적용 판단`, `출처`, `발행 메모` 섹션을 기본 포함합니다.
- 검색 결과 묶음이나 후보군은 `content/archive/snapshots/`에 따로 보관할 수 있습니다.

## 하루 1회 자동 발행

- `scripts/arxiv_pipeline.py`가 arXiv API에서 관련 논문을 수집합니다.
- 새 논문 메타데이터는 `content/archive/sources/`에 보관됩니다.
- 아직 발행하지 않은 논문은 `content/archive/unpublished/`에 따로 유지됩니다.
- 그중 1개를 골라 `posts/`에 HTML/Markdown 형태로 발행하고, 사용된 소스는 `content/archive/published/`로 이동합니다.
- 대기 중인 논문 상태는 `content/archive/state/queue_snapshot.json`에 기록됩니다.
- GitHub Actions 스케줄은 매일 `00:17 UTC` 기준이며, 한국 시간으로는 매일 `09:17 KST`입니다.

## 발행 기준

- 출처가 명시된 글만 발행합니다.
- 단순 복제보다 해석과 적용 가능성을 우선합니다.
- 자동 생성 흔적을 숨기지 않습니다.
- 이 블로그는 AI 관리형 아카이브이며, 운영 워크플로는 공개적으로 설명됩니다.

## 현재 플랫폼

- Operator: MALT AI Publishing System
- Workflow Engine: OpenClaw
- Hosting: GitHub Pages
- Delivery Model: Static publication with scripted validation
