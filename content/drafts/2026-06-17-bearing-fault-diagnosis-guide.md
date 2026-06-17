---
title: "Bearing Fault Diagnosis Guide: 진동 분석부터 딥러닝까지, 베어링 고장 진단을 제대로 시작하는 방법"
date: 2026-06-17
slug: "bearing-fault-diagnosis-guide"
categories: ["phm", "bearing", "condition-monitoring", "guide"]
tags: ["Bearing", "Fault Diagnosis", "Vibration Analysis", "AE", "Deep Learning", "Predictive Maintenance"]
draft: true
generated_by: "MALT"
workflow: "AI-managed publication"
---

# Bearing Fault Diagnosis Guide: 진동 분석부터 딥러닝까지, 베어링 고장 진단을 제대로 시작하는 방법

베어링 고장 진단은 회전체 설비 유지보전에서 가장 널리 다뤄지는 주제 중 하나입니다. 하지만 현장에서는 여전히 같은 질문이 반복됩니다. `진동 분석만으로 충분한가`, `FFT와 envelope analysis는 아직 유효한가`, `딥러닝 모델이 실제로 더 나은가`, `속도가 바뀌는 장비에서는 무엇이 달라지는가` 같은 질문들입니다.

이 글은 `bearing fault diagnosis`를 처음 설계하거나, 전통적 신호처리와 최신 AI 접근 사이에서 무엇을 먼저 도입할지 판단해야 하는 독자를 위한 실무형 가이드입니다.

이 글에서 다루는 핵심 질문은 다음과 같습니다.

- 베어링 고장 진단은 실제로 무엇을 찾아내는 일인가
- 어떤 센서 조합이 가장 현실적인가
- FFT, envelope, spectrogram, learned feature는 각각 어디에 강한가
- classical ML과 CNN, Transformer는 언제 쓰는 편이 좋은가
- variable speed와 cross-machine 환경에서는 무엇이 달라지는가
- 논문 정확도와 운영 성과가 왜 자주 다르게 나오는가

먼저 결론부터 말하면, 베어링 고장 진단의 핵심은 `모델 선택`보다 `고장 모드 이해`, `신호 품질`, `운영 조건 보정`, `오탐 비용 관리`에 있습니다. 고급 모델을 쓴다고 자동으로 현장 성능이 좋아지지는 않습니다.

## 베어링 고장 진단은 무엇을 찾아내는 일인가

베어링 고장 진단은 단순히 "정상/비정상"을 나누는 문제가 아닙니다. 실제로는 다음 질문에 답하는 체계에 가깝습니다.

1. 지금 이상 징후가 있는가
2. 있다면 어디에서 시작된 문제인가
3. 외륜, 내륜, rolling element, cage 중 어느 고장 모드에 가까운가
4. 운영을 계속해도 되는가, 아니면 점검을 앞당겨야 하는가

즉 베어링 고장 진단은 `이상 탐지`, `고장 모드 분류`, `위험도 판단`, `정비 연결`까지 이어져야 실무 가치가 생깁니다.

연구실에선 종종 fault label이 깔끔한 데이터셋으로 고장 종류를 분류하지만, 현장에서는 다음처럼 더 복잡합니다.

- 속도가 계속 바뀜
- 하중 조건이 일정하지 않음
- 센서 부착 위치가 장비마다 다름
- 동일 설비라도 설치 환경이 다름
- 고장 데이터가 매우 적고 불균형함

그래서 베어링 고장 진단을 잘하려면 먼저 `신호의 모양`보다 `그 신호가 어떤 물리적 상황에서 나왔는지`를 같이 봐야 합니다.

## 어떤 센서를 먼저 써야 하나

대부분의 팀은 진동 센서부터 시작합니다. 그 선택은 여전히 유효합니다. 다만 특정 상황에서는 다른 센서가 더 좋은 출발점이 될 수 있습니다.

### 1. Vibration

가장 전형적이고 여전히 가장 강력한 선택입니다.

- 고장 특징 주파수와 sideband를 보기 좋음
- FFT, envelope, cepstrum, time-frequency 분석과 연결이 쉬움
- 전통적 방법부터 딥러닝까지 거의 모든 파이프라인에 잘 맞음

단점도 있습니다.

- 구조 공진과 외부 잡음 영향을 많이 받음
- 장착 위치와 방향에 민감함
- variable speed 환경에서 주파수 해석이 흔들릴 수 있음

### 2. Acoustic Emission (AE)

초기 결함이나 미세 충격을 더 민감하게 보려는 경우 강점이 있습니다.

- 초기 crack이나 작은 surface defect 포착 가능성
- 고주파 영역에서 충격성 이벤트를 보기 좋음
- 진동보다 조기 징후에 민감할 수 있음

관련 내부 글:

- [단일 AE 센서와 Matching Pursuit를 활용한 베어링 결함 진단 기술의 혁신](/Users/yangsoo/Documents/Codex/2026-06-15/new-chat/work/whdidtn200.github.io/posts/2026-02-19-bearing-ae-sensor.html)

다만 AE는 다음을 같이 고려해야 합니다.

- 센서와 취득 장비 비용
- 설치 재현성
- 현장 잡음과 신호 해석 난이도

### 3. Temperature

온도만으로 정밀 진단을 하긴 어렵지만, 운영 모니터링의 보조 신호로 매우 유용합니다.

- 장시간 추세 감시
- 윤활 문제, 마찰 증가, 과열 징후 확인
- 운영자에게 설명하기 쉬운 지표

문제는 반응이 느리다는 점입니다. 이미 상태가 꽤 나빠진 뒤에야 차이가 보이는 경우가 많습니다.

### 4. Current / Motor electrical signals

센서를 추가 설치하기 어렵거나, 모터-구동계 쪽에서 간접적으로 상태를 보고 싶을 때 현실적입니다.

- 추가 센서 설치가 어려운 환경에서 유리
- 전기적 상태와 기계적 상태를 함께 볼 수 있음
- 일부 자산에서는 비용 대비 효율이 좋음

하지만 베어링 자체의 미세 결함 해상도는 진동/AE보다 떨어질 수 있습니다.

## 신호처리 파이프라인은 어떻게 잡는가

베어링 진단에서 신호처리는 아직도 매우 중요합니다. 딥러닝이 강해졌다고 해서 전처리를 무시하면 오히려 성능이 불안정해집니다.

### 1. Time-domain features

가장 빠르게 시작할 수 있는 방식입니다.

- RMS
- Kurtosis
- Crest factor
- Skewness
- Peak-to-peak

장점은 단순하고 설명이 쉽다는 점입니다. 다만 고장 모드 분리력은 제한적일 수 있습니다.

### 2. FFT 기반 주파수 분석

여전히 가장 기본이 되는 방법입니다.

- characteristic frequency 근처 에너지 확인
- harmonics와 sideband 확인
- 상태 변화 추세를 보기 좋음

관련 내부 글:

- [철도 변속기 시스템의 복합 결함 진단을 위한 FFT-1DCNN 프레임워크](/Users/yangsoo/Documents/Codex/2026-06-15/new-chat/work/whdidtn200.github.io/posts/2026-02-21-railway-phm-fft-1dcnn.html)

속도가 일정하고 센서 설치가 안정적이면 FFT만으로도 충분히 강력합니다.

### 3. Envelope analysis

베어링 결함의 충격성 성분을 드러내는 데 매우 유용합니다.

- 초기 spall이나 반복 충격 계열에 강함
- resonance band를 이용해 미세 결함 강조 가능
- 진동 데이터 기반 베어링 진단에서 실무적 활용도가 높음

단점은 band 선택과 필터 설정에 따라 결과가 많이 달라질 수 있다는 점입니다.

### 4. Time-frequency representation

속도 변화나 비정상 상태가 시간에 따라 움직이는 경우 중요합니다.

- STFT spectrogram
- wavelet scalogram
- Wigner-Ville 계열
- synchrosqueezing 계열

이 표현은 CNN 기반 모델과도 잘 맞습니다. 대신 이미지처럼 만들었다고 해서 자동으로 일반화가 좋아지는 것은 아닙니다.

### 5. Learned features

raw signal이나 time-frequency map에서 모델이 특징을 직접 학습하게 하는 방식입니다.

- 수작업 feature engineering 부담 감소
- 복합 고장 구조를 다루기 좋음
- 대규모 데이터가 있으면 강력

하지만 데이터가 적고 도메인 편차가 큰 환경에서는 쉽게 과적합될 수 있습니다.

## Classical ML과 Deep Learning은 언제 나뉘는가

이 질문에는 조직 상황을 같이 넣어 답해야 합니다.

### 전통적 방법이 유리한 경우

- 센서 수가 적고 데이터셋 규모가 작음
- 현장 설명 가능성이 중요함
- 빠른 파일럿이 목적임
- 속도와 하중이 상대적으로 안정적임

이 경우 다음 조합이 여전히 강합니다.

- feature extraction + SVM
- feature extraction + Random Forest
- FFT / envelope + threshold or anomaly scoring

### CNN 계열이 유리한 경우

- 클래스별 샘플이 어느 정도 있음
- time-frequency 이미지 표현이 안정적임
- 고장 모드 분류 정확도를 높이고 싶음
- 동일 계열 장비가 반복적으로 많음

CNN은 특히 spectrogram, scalogram, envelope spectrum 이미지와 잘 맞습니다.

### Transformer 계열이 유리한 경우

- 긴 시계열 문맥이 중요함
- 복수 센서나 멀티모달 입력을 다룸
- 조건 변화에 따라 패턴 길이가 달라짐
- 충분한 데이터와 검증 체계가 있음

다만 많은 현장에서는 Transformer가 무조건 더 낫다고 보기 어렵습니다. 계산 비용, 데이터 요구량, 안정성까지 함께 봐야 합니다.

### 전이학습과 도메인 적응이 중요한 경우

실무에서는 이쪽이 오히려 더 중요할 수 있습니다.

- 장비 A에서 배운 모델을 장비 B에 옮기고 싶을 때
- 실험실 데이터에서 학습하고 현장 데이터에 적용할 때
- 센서 위치나 속도 범위가 달라질 때

현업에서는 "최고 정확도 모델"보다 `새 자산에 얼마나 덜 깨지고 넘어가느냐`가 더 중요합니다.

## Variable Speed에서는 무엇이 달라지는가

많은 논문이 고정 속도에서 높은 정확도를 보이지만, 실제 자산은 속도가 바뀌는 경우가 많습니다. 이때 문제가 생깁니다.

- 특징 주파수가 이동함
- 스펙트럼 피크가 퍼짐
- 고정 윈도우 기반 특징이 일관성을 잃음
- 정상과 비정상의 경계가 속도 조건에 따라 달라짐

그래서 variable speed 환경에서는 다음 전략이 중요합니다.

### 1. Tachometer 또는 speed reference를 같이 저장

속도 정보 없이 고장 진단을 안정적으로 하기는 어렵습니다.

### 2. Order tracking 또는 speed normalization 고려

회전수 기반 정렬을 해주면 같은 현상을 더 일관되게 비교할 수 있습니다.

### 3. 조건 정보를 모델 입력에 같이 넣기

속도, 하중, 온도 같은 운영 맥락을 추가 입력으로 주는 방식이 일반화에 도움이 됩니다.

### 4. 한 장비의 높은 정확도보다 조건 전반의 강건성을 평가

속도 구간별로 따로 성능을 봐야 합니다. 평균 정확도만 보면 위험합니다.

## 논문 정확도가 높은데 현장 성과가 약한 이유

이건 정말 자주 생깁니다.

### 1. 데이터 누수

같은 런에서 잘린 조각이 train/test에 함께 들어가면 점수가 과하게 좋아집니다.

### 2. 실험실 데이터셋 편향

대표적인 공개 데이터셋은 출발점으로 좋지만, 현장 잡음과 설치 편차를 충분히 반영하지 못할 수 있습니다.

### 3. 불균형 데이터 무시

실제론 정상 데이터가 대부분이고 고장은 드뭅니다. balanced accuracy나 event-level 성능을 따로 봐야 합니다.

### 4. 조기 경고 성능 대신 class accuracy만 봄

현장에선 몇 시간, 며칠, 몇 주 먼저 잡았는지가 훨씬 중요할 수 있습니다.

### 5. 오탐 비용이 평가식에 없음

정확도 98%라도 오탐이 운영팀을 지치게 만들면 오래 못 갑니다.

## 실무 배치를 위한 체크리스트

베어링 고장 진단을 운영으로 옮길 때는 아래 질문에 답할 수 있어야 합니다.

- 센서 설치 위치와 방향이 표준화되어 있는가
- 속도와 하중 같은 운영 맥락 데이터를 함께 저장하는가
- 정비 이력과 고장 판정 데이터가 연결되는가
- 경보 임계치와 리뷰 절차가 정의되어 있는가
- 오탐이 발생했을 때 누가 어떻게 피드백을 남기는가
- 같은 모델을 다른 장비에 옮길 때 재보정 절차가 있는가
- 모델 정확도 외에 lead time과 unnecessary inspection burden을 측정하는가

이 체크리스트에 빈칸이 많다면, 모델 교체보다 데이터 파이프라인과 운영 절차 정비가 먼저입니다.

## MALT가 추천하는 읽을거리

이 글과 함께 보면 좋은 내부 글은 아래입니다.

- [철도 변속기 시스템의 복합 결함 진단을 위한 FFT-1DCNN 프레임워크](/Users/yangsoo/Documents/Codex/2026-06-15/new-chat/work/whdidtn200.github.io/posts/2026-02-21-railway-phm-fft-1dcnn.html)
- [단일 AE 센서와 Matching Pursuit를 활용한 베어링 결함 진단 기술의 혁신](/Users/yangsoo/Documents/Codex/2026-06-15/new-chat/work/whdidtn200.github.io/posts/2026-02-19-bearing-ae-sensor.html)
- [Neural Factorization based Bearing Fault Diagnosis](/Users/yangsoo/Documents/Codex/2026-06-15/new-chat/work/whdidtn200.github.io/posts/2026-06-16-251206837v1-neural-factorization-based-bearing-fault-diagnosis.html)
- [LLM-based Framework for Bearing Fault Diagnosis](/Users/yangsoo/Documents/Codex/2026-06-15/new-chat/work/whdidtn200.github.io/posts/2026-06-16-241102718v1-llm-based-framework-for-bearing-fault-diagnosis.html)

## 마무리

베어링 고장 진단에서 정말 중요한 건 가장 화려한 모델을 고르는 일이 아닙니다. `어떤 결함을 얼마나 일찍, 얼마나 신뢰할 수 있게, 현장 정비팀이 실제 행동으로 옮길 수 있는 형태로 보여줄 것인가`가 더 중요합니다.

그래서 MALT 관점에서 bearing fault diagnosis의 시작점은 "딥러닝을 쓸까?"가 아니라, **"우리 장비에서 어떤 신호가 가장 안정적으로 고장 징후를 보여주며, 그 신호를 어떤 운영 판단으로 바꿀 것인가"** 입니다.

## 발행 메모

- 이 문서는 검색 유입용 evergreen guide 초안입니다.
- 향후 발행 전에는 센서별 비교표와 모델 선택 매트릭스를 추가하면 더 강해집니다.
- 일간 논문 요약 글로 내부 링크를 보내는 허브 역할을 목표로 합니다.
