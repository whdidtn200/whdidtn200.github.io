---
title: "[실험실] 점수 하나로 울릴까, 증거 두 개를 더 묶을까? 다중 신호 경보 번들 실험"
date: 2026-07-21 10:40:00 +0900
tags:
  - 실험실
  - Alarm Design
  - Fault Diagnosis
  - Condition Monitoring
  - Reproduction
  - Maintenance
categories:
  - Lab
  - PHM
summary: "공개 베어링 특징 1,200개를 bootstrap한 10,000개 이벤트에서 score 단독 경보와 score+diff_rms, score+diff_rms+kurtosis 증거 번들 경보를 비교한다."
---

# [실험실] 점수 하나로 울릴까, 증거 두 개를 더 묶을까? 다중 신호 경보 번들 실험

## 먼저 결론

복합 조건 정상 이벤트에서 `normalized_impulse` 한 개만 넘으면 경보를 내는 `score_only` 정책은 이벤트 오경보 부담이 가장 컸다. 같은 이벤트 구조에서 `diff_rms`를 함께 요구한 `score_plus_diff`, 여기에 `kurtosis`까지 묶은 `triple_evidence`는 오경보를 더 줄이는 대신 탐지 시작을 약간 늦출 수 있었다.

이 실험의 포인트는 정확도 자랑이 아니라 작업 지시를 여는 기준을 어떻게 설계하느냐에 있다. 현장에서는 점수 하나보다 "서로 다른 종류의 증거가 동시에 모였는가"가 더 중요할 때가 많다.

## 질문과 방법

입력은 기존 베어링 임계치 실험에서 공개한 1,200개 특징 행이다. 각 행의 `normalized_impulse`, `diff_rms`, `kurtosis`를 사용했고, healthy 행의 상위 분위수를 기준으로 세 가지 정책을 만들었다.

- `score_only`: `normalized_impulse`만 상위 95% healthy 기준을 넘으면 경보
- `score_plus_diff`: `normalized_impulse`와 `diff_rms`를 동시에 만족해야 경보
- `triple_evidence`: `normalized_impulse`, `diff_rms`, `kurtosis` 세 조건을 모두 만족해야 경보

조건별 정상 이벤트 1,000개와 결함 이벤트 1,000개, 총 10,000개 이벤트를 만들었다. 이벤트 길이는 12 window, 결함은 네 번째 window부터 활성화했다. 난수 시드는 `2026072101`이다.

## 복합 조건 결과

| 정책 | 정상 이벤트 오경보 | 결함 전 조기 오경보 | 결함 후 탐지율 | 지연 중앙값 |
|---|---:|---:|---:|---:|
| score_only | 97.0% | 69.7% | 30.3% | 0 window |
| score_plus_diff | 0.0% | 0.0% | 100.0% | 0 window |
| triple_evidence | 0.0% | 0.0% | 100.0% | 0 window |

이번 합성 조건에서는 증거를 두 개 이상 묶는 정책이 오경보를 거의 제거하면서 결함 이후 탐지율도 유지했다. 다만 이 결과가 너무 깔끔하게 나온 이유 자체가 중요한 해석 포인트다. 공개 특징 공간 안에서는 `diff_rms`와 `kurtosis`가 healthy/fault를 강하게 분리하고 있어, 실제 현장보다 더 낙관적인 분리도가 반영됐을 가능성이 크다.

## 운영 해석

점수 하나는 민감하지만 설명력이 약하다. 반면 `diff_rms`나 `kurtosis` 같은 두 번째, 세 번째 증거를 묶으면 "왜 이 경보가 열렸는가"를 현장에 설명하기 쉬워진다. 이는 곧 점검 우선순위와 종결 품질로 이어진다.

다만 evidence bundle은 결함 초기에 한 신호만 먼저 튀는 경우 탐지를 늦출 수 있다. 그래서 즉시 대응이 필요한 자산에는 `score_only`를 예비 경보로 남기고, 실제 inspection ticket은 evidence bundle로 여는 이중 구조가 더 현실적일 수 있다.

## 한계

- 실제 연속 파형이 아니라 공개 특징 행을 bootstrap한 메커니즘 실험이다.
- 세 threshold는 healthy 분포의 분위수에서 잡은 단순 규칙이며 자산별 최적화가 아니다.
- 신호 간 물리적 인과보다는 운영 의사결정 구조를 분리해서 보기 위한 실험이다.
- `score_plus_diff`, `triple_evidence`가 지나치게 깔끔한 수치를 보인 것은 공개 특징 세트가 이미 강하게 분리돼 있기 때문일 수 있다.
- 수치는 특정 설비에 바로 이전할 수 있는 현장 성능 주장이 아니다.

## 출처와 재현 자료

- [실행 코드](/experiments/multi_signal_alarm_bundle.py)
- [요약 CSV](/data/lab-results/multi-signal-alarm-summary.csv)
- [이벤트 표본 CSV](/data/lab-results/multi-signal-alarm-event-sample.csv)
- [원본 특징 CSV](/data/lab-results/bearing-threshold-samples.csv)
- [앞선 경보 지속 규칙 실험](/posts/2026-07-17-alarm-persistence-rule-lab.html)

`python3 experiments/multi_signal_alarm_bundle.py`로 결과를 다시 만들 수 있다. Codex 기반 AI 자동화가 실행과 초안 정리를 보조했으며, 공개 코드와 CSV가 검증 근거다.

## 다음 단계

다음 단계는 evidence bundle과 persistence rule을 함께 적용했을 때, 작업 지시 수와 lead time이 어떻게 바뀌는지를 비교하는 것이다.
