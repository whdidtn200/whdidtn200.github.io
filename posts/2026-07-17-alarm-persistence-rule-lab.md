---
title: "[실험실] 한 번 넘으면 경보? 2-of-3와 3-of-5 지속 규칙을 10,000개 이벤트로 비교"
date: 2026-07-17 19:10:00 +0900
tags:
  - 실험실
  - Alarm Design
  - Fault Diagnosis
  - Condition Monitoring
  - Reproduction
  - Data Quality
categories:
  - Lab
  - PHM
summary: "앞선 베어링 합성 신호 1,200개의 공개 특징을 bootstrap해 10,000개 이벤트를 만들고, 단일 초과·2-of-3·3-of-5 경보 규칙의 오경보와 탐지 지연을 비교한다."
---

# [실험실] 한 번 넘으면 경보? 2-of-3와 3-of-5 지속 규칙을 10,000개 이벤트로 비교

## 먼저 결론

한 window가 임계치를 넘는 즉시 경보를 내는 `1-of-1` 규칙은 복합 운전 조건의 정상 이벤트 96.8%에서 한 번 이상 경보를 냈다. `2-of-3`는 59.7%, `3-of-5`는 32.7%로 낮아졌다. 결함 이벤트에서 결함이 시작되기 전 잘못 울린 비율은 각각 68.6%, 20.6%, 6.0%였다.

`3-of-5`는 결함 시작 이후 탐지율 94.0%와 탐지 지연 중앙값 1 window를 보였다. 지속 규칙은 공짜 개선이 아니라 오경보와 지연 사이의 교환관계다.

## 질문과 방법

앞선 베어링 임계치 실험에서 공개한 1,200개 `normalized_impulse` 특징을 조건·정상/결함별 pool로 사용했다. 각 이벤트는 12개 window로 구성하고, 결함 이벤트는 네 번째 window부터 결함 pool을 sampling했다. 조건별 정상 1,000개와 결함 1,000개, 총 10,000개 이벤트를 seed `2026071702`로 bootstrap했다.

- `1-of-1`: 현재 window 하나가 임계치를 넘으면 경보
- `2-of-3`: 최근 3개 중 2개 이상이 넘으면 경보
- `3-of-5`: 최근 5개 중 3개 이상이 넘으면 경보

평가 지표는 이벤트 단위 오경보율, 결함 시작 전 조기 오경보율, 결함 시작 후 탐지율, 탐지 지연 window 수다.

## 복합 조건 결과

| 규칙 | 정상 이벤트 오경보 | 결함 전 조기 오경보 | 결함 후 탐지율 | 지연 중앙값 |
|---|---:|---:|---:|---:|
| 1-of-1 | 96.8% | 68.6% | 31.4% | 0 window |
| 2-of-3 | 59.7% | 20.6% | 79.4% | 1 window |
| 3-of-5 | 32.7% | 6.0% | 94.0% | 1 window |

`1-of-1`의 결함 후 탐지율이 낮아 보이는 이유는 결함 전에 이미 경보가 난 이벤트를 정상적인 결함 탐지로 세지 않았기 때문이다. 센서가 민감해서가 아니라 baseline이 흔들려 경보의 시간 의미가 사라진 상태다.

## 운영 해석

지속 규칙은 단일 spike를 걸러내지만 모든 문제를 해결하지 않는다. 복합 조건에서 `3-of-5`도 정상 이벤트 세 건 중 한 건꼴로 울렸다. 먼저 조건별 baseline을 안정화하고, 그 위에 persistence를 적용해야 한다.

window 길이가 10초라면 중앙값 1 window 지연은 약 10초지만, 10분 집계라면 10분이 된다. 그래서 `3-of-5`라는 숫자만 복사하지 말고 자산의 고장 진행 속도, 출동 시간, window 길이를 함께 정해야 한다.

## 한계

- 실제 시간 연속 신호가 아니라 공개 특징 행을 bootstrap한 메커니즘 실험이다.
- 인접 window의 물리적 자기상관을 직접 모델링하지 않았다.
- 결함 시작점을 네 번째 window로 고정해 다양한 고장 진행 속도를 표현하지 못한다.
- 복합 조건 외 네 조건에서 오경보가 0%였던 것은 원본 합성 데이터의 분리도가 높았기 때문이다.

## 출처와 재현 자료

- [실행 코드](/experiments/alarm_persistence_benchmark.py)
- [요약 CSV](/data/lab-results/alarm-persistence-summary.csv)
- [이벤트 표본 CSV](/data/lab-results/alarm-persistence-event-sample.csv)
- [원본 특징 CSV](/data/lab-results/bearing-threshold-samples.csv)
- [앞선 임계치 실험](/posts/2026-07-17-bearing-alarm-threshold-robustness-lab.html)

`python3 experiments/alarm_persistence_benchmark.py`로 같은 결과를 다시 만들 수 있다. Codex 기반 AI 자동화가 실행과 초안 정리를 보조했으며, 공개 코드와 CSV가 검증 근거다.

## 다음 실험

다음 단계는 실제 공개 베어링 데이터에서 window 길이와 `k-of-n` 조합을 바꾸고, 오경보율만이 아니라 lead time과 maintenance workload까지 함께 비교하는 것이다.

