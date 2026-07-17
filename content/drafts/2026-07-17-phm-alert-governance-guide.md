---
title: "PHM Alert Governance Guide: 모델 점수를 정비 행동으로 바꾸는 경보 운영 설계"
date: 2026-07-17 19:30:00 +0900
slug: phm-alert-governance-guide
tags:
  - PHM
  - Alarm Design
  - Maintenance
  - Operations
  - Guide
  - Data Quality
categories:
  - Guide
  - PHM
summary: "상태 감시 모델의 점수를 관찰, 검증, 분류, 점검, 작업 지시, 종결로 연결하기 위한 경보 상태·책임·데이터 필드·KPI·90일 도입 절차를 정리한 운영 가이드."
---

# PHM Alert Governance Guide: 모델 점수를 정비 행동으로 바꾸는 경보 운영 설계

## 경보가 많아도 예지보전이 아닌 이유

모델 점수와 정비 경보는 같은 것이 아니다. 점수는 계산 결과이고, 경보는 누가 언제 어떤 근거로 무엇을 확인해야 하는지 정의된 운영 객체다. 임계치를 넘었다는 이유만으로 작업 지시를 만들면 오경보가 정비팀의 시간을 소모하고 결국 시스템 신뢰가 무너진다.

좋은 경보 운영은 `Observe → Qualify → Triage → Inspect → Act → Close` 흐름을 가진다. 마지막 점검 결과와 실제 조치가 baseline과 모델 검토로 돌아와야 학습 루프가 닫힌다.

## 여섯 단계 상태 모델

1. Observe: 센서 값, 모델 점수, 속도·하중·환경 조건을 함께 저장한다.
2. Qualify: persistence, 중복 억제, 센서 건강도, maintenance mode를 확인한다.
3. Triage: 안전 영향, 운행 영향, 고장 진행 속도로 우선순위를 정하고 owner를 배정한다.
4. Inspect: 파형, 추세, 최근 정비 이력과 현장 점검 결과를 한 사건에 묶는다.
5. Act: 작업 지시, 운행 제한, 추가 계측 또는 관찰 유지 중 하나를 명시한다.
6. Close: true positive, false positive, inconclusive, sensor issue로 종결하고 근거를 남긴다.

## 경보 레코드에 반드시 남길 필드

- `alert_id`, asset, component, sensor, 발생·확인·종결 시각
- 모델 버전, feature 버전, threshold 버전, 입력 데이터 품질 상태
- 속도, 하중, 노선, 계절, 운전 mode 같은 context
- 단일 점수뿐 아니라 baseline 대비 변화량과 persistence 결과
- severity, confidence, owner, due time, escalation rule
- 연결된 inspection, work order, 교체 부품, 실제 발견 결함
- 종결 label과 판단 근거, 재발 여부, baseline 반영 여부

이 필드가 없으면 정확도가 나빠졌을 때 모델 문제인지 센서 문제인지, 운전 조건 변화인지 구분할 수 없다.

## Severity와 Confidence를 분리하라

Severity는 틀렸을 때의 영향이고 confidence는 현재 증거의 강도다. 안전 영향이 큰 저신뢰 경보는 무시할 대상이 아니라 추가 센서 확인이나 짧은 재측정으로 보내야 한다. 고신뢰라도 영향이 낮으면 계획 정비 backlog로 보낼 수 있다.

| Severity | 의미 | 기본 행동 |
|---|---|---|
| S1 | 추세 관찰 | 다음 주기까지 watch |
| S2 | 성능 저하 가능 | 원격 검토와 추가 데이터 |
| S3 | 정비 필요 가능성 | inspection ticket |
| S4 | 안전·운행 영향 가능 | 즉시 escalation |

## Persistence와 억제 규칙

단일 초과 경보는 구현하기 쉽지만 이벤트 단위 오경보를 키울 수 있다. `2-of-3`, `3-of-5`, hysteresis, cooldown을 자산별로 조합해야 한다. 다만 persistence는 탐지를 늦출 수 있으므로 window 길이와 고장 진행 시간을 함께 정한다.

다음 상황은 경보를 삭제하지 말고 `suppressed` 상태와 이유를 기록한다.

- 계획 정비 중 센서 분리
- 시운전 또는 비정상 운전 mode
- 센서 고장·통신 장애
- 동일 root cause에서 파생된 중복 경보

## 역할과 승인 경계

- Data/PHM engineer: threshold와 모델 버전, 데이터 품질, drift를 관리한다.
- Maintenance planner: inspection 우선순위와 작업 일정을 정한다.
- Field maintainer: 실제 상태, 조치, 부품 정보를 기록한다.
- Operations controller: 운행 영향과 즉시 대응을 결정한다.
- Asset owner: 위험 수용, 정책 변경, KPI를 승인한다.

AI가 자동으로 할 수 있는 범위는 후보 묶기, 관련 이력 찾기, 설명 초안, 반복 경보 요약까지다. 안전 영향이 있는 작업 지시와 운행 제한은 책임자의 승인 경계를 유지한다.

## 경보 품질 KPI

- Alert-to-inspection conversion: 경보가 실제 점검으로 전환된 비율
- Confirmed finding rate: 점검에서 이상이 확인된 비율
- Detection lead time: 조치 가능 시점보다 얼마나 먼저 알렸는가
- Nuisance burden: 자산·노선·근무조별 불필요 경보 수
- Time to acknowledge / triage / close
- Repeat alert rate after closure
- Unknown outcome rate: 종결 label 없이 닫힌 경보 비율

정확도와 F1만으로는 정비 부담, 지연, 미종결 사건을 설명할 수 없다.

## 주간 경보 리뷰 회의 양식

주간 리뷰는 모델 성능 발표가 아니라 경보 정책을 조정하는 운영 회의여야 한다. 지난 7일의 신규 경보, 미종결 경보, 반복 경보, false positive 상위 자산을 먼저 본다. 각 경보에는 owner와 다음 행동, 기한을 붙이고 회의에서 threshold를 즉시 바꾸기보다 변경 후보와 근거를 별도 queue에 남긴다.

회의 결과는 최소한 다음 네 가지로 끝나야 한다.

- 바로 점검할 경보와 관찰을 유지할 경보의 분리
- 센서 문제·운전 조건 변화·모델 drift 중 원인 가설
- threshold 또는 persistence 변경의 예상 효과와 rollback 기준
- 종결 label이 없는 과거 경보의 보완 담당자와 기한

경보 payload에는 `model_version`, `threshold_version`, `context`, `persistence`, `severity`, `owner`, `linked_work_order`, `closure_label`을 포함한다. 이 구조가 있으면 정책 변경 전후를 비교하고 문제가 생겼을 때 어느 버전으로 되돌아갈지 판단할 수 있다.

## 30·60·90일 도입 순서

첫 30일에는 자산 한 종류와 severity 두 단계만 사용한다. 경보 record schema와 owner, 종결 label을 먼저 만든다. 60일까지 persistence와 suppression reason을 적용하고 주간 false alarm review를 시작한다. 90일까지 CMMS 작업 지시와 연결하고, threshold 변경 전후의 workload와 lead time을 비교한다.

모델 재학습은 90일 계획의 마지막이다. 점검 결과가 안정적으로 되돌아오지 않는 상태에서 재학습부터 자동화하면 잘못된 label을 더 빠르게 증폭시킬 수 있다.

## 한계와 적용 범위

이 가이드는 특정 철도 운영사의 안전 규정이나 승인 절차를 대체하지 않는다. 자산의 위험 등급, 법규, 운행 규칙에 맞춰 severity와 승인 경계를 다시 정의해야 한다. 제시한 KPI도 데이터 수집 가능성과 정비 프로세스에 따라 조정해야 한다.

## 출처와 연결 자료

- [ISO 13374-2 condition monitoring data processing](https://www.iso.org/standard/36645.html)
- [ISO 13374-4 presentation and decision support](https://www.iso.org/standard/54933.html)
- [NIST AI Risk Management Framework 1.0](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10)
- [베어링 임계치 강건성 실험](/posts/2026-07-17-bearing-alarm-threshold-robustness-lab.html)
- [경보 persistence rule 실험](/posts/2026-07-17-alarm-persistence-rule-lab.html)

이 글은 Codex 기반 AI 자동화가 초안 구성을 보조했으며, MALT의 공개 실험 결과와 표준 기관의 공개 설명을 현장형 체크리스트로 재구성했다.
