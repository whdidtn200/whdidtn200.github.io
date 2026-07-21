---
title: "PHM Inspection Evidence Pack Guide: 점검 티켓이 열렸을 때 무엇을 한 묶음으로 남겨야 하는가"
date: 2026-07-21 11:00:00 +0900
slug: phm-inspection-evidence-pack-guide
tags:
  - PHM
  - Maintenance
  - Operations
  - Guide
  - Condition Monitoring
  - Data Quality
categories:
  - Guide
  - PHM
summary: "PHM 경보가 실제 inspection ticket으로 이어질 때 파형, context, 모델 버전, 비교 기준, 사진, 작업 결과, 종결 label을 어떤 순서로 묶어야 하는지 정리한 현장형 가이드."
---

# PHM Inspection Evidence Pack Guide: 점검 티켓이 열렸을 때 무엇을 한 묶음으로 남겨야 하는가

## 점검이 끝났는데도 경보 품질이 안 좋아지는 이유

점검 티켓이 열렸다고 해서 학습 가능한 운영 데이터가 자동으로 남는 것은 아니다. 많은 조직이 경보는 남기지만, 현장에 무엇을 보고 보냈는지와 현장이 무엇을 확인했는지를 같은 묶음으로 저장하지 않는다. 그러면 false positive를 줄이려 해도 근거가 흩어져 다시 같은 논쟁을 반복하게 된다.

좋은 evidence pack은 "왜 열렸는가, 무엇을 봤는가, 무엇을 했는가, 무엇으로 닫았는가"를 한 사건 안에 묶는다. 그래야 threshold 조정, sensor health 개선, 모델 재학습이 모두 같은 기록을 참조할 수 있다.

## evidence pack의 여섯 조각

1. Trigger snapshot: 경보가 열린 시점의 점수, threshold, severity, persistence 결과
2. Context snapshot: 속도, 하중, 운전 mode, 최근 정비 상태, 센서 health
3. Signal excerpt: 대표 파형, 특징 추세, baseline 대비 변화량
4. Field proof: 현장 사진, 냄새·온도·소리 같은 관찰 메모, 분해 결과
5. Action record: 작업 지시, 교체 부품, 재가동 조건, 운행 제한 여부
6. Closure label: true positive, false positive, inconclusive, sensor issue 중 하나와 근거

## 티켓을 열 때 반드시 붙여야 할 첫 화면 정보

- `alert_id`, 자산·부품·센서, 발생 시각
- 모델 버전, feature 버전, threshold 버전
- 점수 단독인지 evidence bundle인지, persistence rule이 무엇이었는지
- 최근 24시간 동일 자산의 반복 경보 여부
- 최근 정비, 교체, 캘리브레이션 이력

첫 화면만 보고도 현장 담당자가 "이번엔 무엇이 다른가"를 파악할 수 있어야 한다. 경보 원문을 길게 붙이기보다 차이를 설명하는 필드를 먼저 배치하는 것이 낫다.

## 파형과 특징은 어떻게 붙일까

신호를 모두 덤프하는 것은 evidence pack이 아니다. 다음 네 장이면 대부분의 초기 판단이 가능하다.

- 경보 직전과 직후의 짧은 파형 또는 스펙트럼 발췌
- 지난 7일 baseline 대비 변화 추세
- 동일 조건 healthy 구간과의 비교
- 센서 health 상태와 누락/포화/이상치 여부

그래프는 많을수록 좋은 것이 아니라, 경보가 열린 이유와 현장 점검 방향을 좁혀 주는 순서로 있어야 한다.

## 사진과 현장 메모가 중요한 이유

같은 vibration anomaly라도 실제 원인은 윤활 부족, 느슨한 체결, 센서 고정 불량, 외부 충격, 운전 조건 변화일 수 있다. 이 차이는 숫자만으로는 닫히지 않는다. 현장 사진 한 장, 냄새·온도·마찰음 메모 한 줄이 나중에 false positive인지 early warning인지 가르는 경우가 많다.

사진은 "대표 사진 1장"이 아니라 최소한 다음 세 종류가 좋다.

- 설치 상태와 배선 상태를 보여주는 넓은 사진
- 의심 부위를 가까이서 보여주는 근접 사진
- 조치 후 재조립 상태를 보여주는 완료 사진

## evidence bundle 실험이 주는 시사점

MALT의 공개 실험에서는 score 하나보다 `score + diff_rms`, `score + diff_rms + kurtosis`처럼 서로 다른 증거를 묶은 정책이 복합 조건의 nuisance burden을 줄일 가능성을 보였다. 이는 점검 티켓 자체도 "어떤 증거 묶음으로 열렸는가"를 함께 저장해야 한다는 뜻이다.

점검 결과를 남길 때도 마찬가지다. 파형 하나만 남기지 말고, context와 현장 proof를 묶어야 나중에 모델이 아닌 운영 규칙을 먼저 고쳐야 하는지 판단할 수 있다.

## 종결 label을 강제해야 하는 이유

종결을 자유 서술로만 남기면 다시 학습 데이터로 쓰기 어렵다. 최소한 네 가지 label은 강제하는 편이 낫다.

| Label | 의미 | 다음 액션 |
|---|---|---|
| true_positive | 실제 이상 또는 열화 징후 확인 | 정책 유지 또는 조기화 검토 |
| false_positive | 이상 없음, 불필요 경보 | threshold/persistence/evidence bundle 재검토 |
| inconclusive | 충분한 근거 없이 종료 | 추가 계측 또는 짧은 재관찰 |
| sensor_issue | 센서/배선/수집 문제 | 센서 health와 설치 품질 개선 |

자유 메모는 label 뒤에 붙여야 한다. label이 먼저 있어야 주간 리뷰와 재학습 전 필터링이 가능하다.

## 보존 기간과 링크 구조도 설계해야 한다

evidence pack은 작성하는 순간만 중요한 것이 아니다. 최소한 경보 원문, 대표 그래프, 현장 사진, 작업 결과, 종결 label이 같은 `alert_id`로 다시 찾아질 수 있어야 한다. 파일 서버, CMMS, 메신저, 이메일에 증거가 따로 흩어져 있으면 다음 threshold 리뷰 때 다시 수작업으로 모아야 한다.

가장 단순한 원칙은 "한 경보, 한 사건, 한 링크"다. 경보 페이지 하나에서 관련 그래프, 사진, 작업 지시, 종결 메모로 모두 이동할 수 있어야 하며, 반대로 작업 지시에서도 원래 경보와 baseline 비교 그래프로 돌아올 수 있어야 한다. 이 연결성 자체가 운영 자산이다.

## 주간 리뷰에서 evidence pack을 쓰는 법

주간 리뷰에서는 모델 정확도보다 evidence pack이 비어 있는 티켓을 먼저 본다. 파형이 없는 경보, 종결 label이 없는 티켓, 현장 사진이 없는 true positive는 다음 주의 개선 우선순위다. 기록 구조가 비어 있으면 성능 조정도 결국 추측이 된다.

리뷰 회의는 다음 네 줄로 정리할 수 있어야 한다.

- 어떤 evidence bundle이 실제 점검 전환율을 높였는가
- 어떤 sensor issue가 경보 품질을 가장 많이 해쳤는가
- 어떤 라벨이 과도하게 `inconclusive`에 몰렸는가
- 다음 주에 비워둘 수 없는 evidence field가 무엇인가

## 30일 도입 순서

첫 2주에는 label 강제와 대표 그래프 2장, 사진 2장만 의무화한다. 3주차에는 model/threshold/persistence 버전을 티켓 상단에 노출한다. 4주차에는 CMMS와 연동해 작업 결과와 closure label이 자동으로 다시 경보 기록으로 돌아오게 만든다.

처음부터 모든 사진, 모든 파형을 강제하면 현장만 피로해진다. 핵심은 "다시 판단할 수 있는 최소 증거 묶음"을 먼저 표준화하는 것이다.

## 한계와 적용 범위

이 가이드는 특정 CMMS 제품이나 철도 운영사의 승인 체계를 대체하지 않는다. 다만 어떤 시스템을 쓰든 evidence pack의 구조는 별도로 설계해야 하며, 그렇지 않으면 경보와 정비가 다시 분리된다.

## 출처와 연결 자료

- [NIST AI RMF 1.0](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10)
- [PHM Alert Governance Guide](/phm-alert-governance-guide.html)
- [다중 신호 경보 번들 실험](/posts/2026-07-21-multi-signal-alarm-bundle-lab.html)
- [경보 지속 규칙 실험](/posts/2026-07-17-alarm-persistence-rule-lab.html)

이 글은 Codex 기반 AI 자동화가 초안 구성을 보조했으며, MALT의 공개 실험과 공개 표준 설명을 현장 점검 증거 패키지 관점으로 재구성했다.
