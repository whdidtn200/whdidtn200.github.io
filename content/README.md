# Content Pipeline

이 디렉터리는 MALT의 AI 관리형 콘텐츠 파이프라인을 위한 작업 공간입니다.

## 폴더

- `archive/`
  수집한 원본 소스 메모와 리서치 스냅샷
- `drafts/`
  자동 생성된 Markdown 초안

## 사용 예시

```bash
python3 scripts/extract_internal_source.py posts/2026-02-22-xai-industrial-iot-anomaly-detection-bearing.md
python3 scripts/generate_draft.py content/archive/sources/2026-06-15-agentic-observability.json
python3 scripts/generate_pillar_post_drafts.py --all
python3 scripts/arxiv_pipeline.py
```

생성된 초안은 `content/drafts/`에 저장됩니다.

그 다음 흐름:

1. 소스를 `archive/sources/`에 보관
2. 미발행 논문은 `archive/unpublished/`에 따로 유지
3. 발행된 논문은 `archive/published/`로 이동
4. 기존 블로그의 논문 프리뷰/리뷰 글을 `extract_internal_source.py`로 source JSON으로 변환
5. 초안 내용 점검
6. 필요한 해석 보강
7. `posts/`로 이동 또는 복사
8. `python3 scripts/validate_post.py`로 변경 포스트 검사

## Pillar Draft Automation

- `scripts/generate_pillar_post_drafts.py`는 `content/drafts/` 안의 outline 형태 가이드 초안을 장문 evergreen draft로 확장합니다.
- 이미 frontmatter가 있는 완성형 초안은 건드리지 않고, outline 상태인 가이드만 대상으로 삼습니다.
- `scripts/run_daily_publish.sh`는 매일 발행 전에 이 스크립트를 한 번 실행해서 미완성 가이드가 남아 있으면 하나씩 자동으로 채웁니다.

## Daily Publish

- `scripts/arxiv_pipeline.py`는 arXiv API에서 논문을 수집하고, 새 source를 archive에 저장한 뒤, 미발행 논문 1개를 골라 `posts/`에 발행합니다.
- 발행되지 않은 논문은 `content/archive/unpublished/`에 계속 쌓이고, 발행된 논문은 `content/archive/published/`로 이동합니다.
- 현재 대기 중인 논문 목록은 `content/archive/state/queue_snapshot.json`에 저장됩니다.
- GitHub Actions workflow `.github/workflows/daily-arxiv-publish.yml`은 매일 `00:17 UTC`에 이 파이프라인을 실행합니다.
