# 신뢰할 수 있는 설비 모니터링: Cascade 이상 감지와 Saliency 기반 검사

**arXiv:2512.24755** | 2026-02-22 업데이트  
**저자**: Sungwoo Kang (Korea University)  
**키워드**: #예측정비 #이상감지 #XAI #멀티모달융합 #RandomForest #설비모니터링

---

## Executive Summary

산업 현장의 예측 정비(Predictive Maintenance)는 정확한 이상 감지뿐만 아니라, 정비 엔지니어가 신뢰하고 즉각 행동할 수 있는 **해석 가능한 설명**을 요구한다. 본 논문은 센서 시계열과 열화상 이미지를 결합한 멀티모달 학습에서, **단순 융합(naive fusion)이 오히려 성능을 저하**시킬 수 있음을 실증적으로 입증하고, **Cascade 아키텍처**가 end-to-end 융합보다 우수한 이유를 체계적으로 제시한다.

### 핵심 발견

- **Random Forest (94.70% F1) > LSTM (91.22%) > Multimodal Fusion (85.40%)**: 통계적 특징 기반 전통적 ML이 딥러닝 및 융합 모델을 **통계적으로 유의미하게(Cohen's d = 3.04–8.81)** 능가
- **2단계 Cascade 설계**: Stage 1(센서 기반 이상 감지) + Stage 2(열화상 기반 공간 해석)로 작업을 분리하여 각 모달리티를 최적화
- **Modality Bias 진단 프로토콜**: Gate weight 분석으로 융합 모델이 정보량이 적은 열화상 이미지에 과도하게 의존하는 현상 정량화
- **통합 XAI 파이프라인**: TreeSHAP(센서 중요도) + Spatial Attention(열화상 검사 영역)으로 엔지니어가 즉각 활용 가능한 해석성 제공

---

## 1. 문제 정의: 왜 Cascade인가?

### 1.1 멀티모달 학습의 함정

산업 설비 모니터링은 이질적인 센서를 배치한다:
- **전기/진동 센서**: 내부 상태 변화에 거의 즉각 반응
- **열화상 카메라**: 열 관성(thermal inertia)으로 인해 표면 온도 변화가 지연

**정보량 비대칭성(Informativeness Asymmetry)**이 존재하는 상황에서, 동시 융합은 두 모달리티를 동등하게 처리하려다 오히려 성능을 저하시킨다. 본 논문은 다음과 같은 설계 철학을 제안한다:

> **센서는 "결함이 있는가?"를 답하고, 열화상은 "어디를 검사할 것인가?"를 제시한다.**

두 작업을 하나의 융합 모델에 강제로 통합하면 감지(detection)와 공간 해석(spatial interpretation)이라는 서로 다른 목적이 뒤섞이게 된다.

### 1.2 OHT/AGV 데이터셋

- **데이터**: AI Hub Korea의 OHT(Overhead Hoist Transport)/AGV(Automated Guided Vehicle) 설비 모니터링 데이터
- **센서**: 8개 채널 (전압, 전류, 진동 등)
- **열화상**: 1Hz 샘플링, 시간 정렬
- **클래스**: Normal / Caution / Warning / Danger (4-class severity grading)
- **샘플 수**: 총 13,121개

---

## 2. 방법론: Hybrid Cascaded Framework

### 2.1 Stage 1: 통계적 특징 기반 Random Forest

#### 2.1.1 특징 추출

센서 시계열 $\mathbf{X}_s \in \mathbb{R}^{T \times D}$ (T=시퀀스 길이, D=센서 수)에서 각 센서별로 4개 통계량 추출:

$$
\mathbf{f}_d = [\mu_d, \sigma_d, \min_d, \max_d]
$$

8개 센서 × 4개 통계량 = **32차원 특징 벡터**

#### 2.1.2 Random Forest 분류

- **앙상블 크기**: 100 trees
- **최대 깊이**: 15
- **클래스 가중치**: 불균형 데이터 대응
- **전처리**: StandardScaler 정규화

**성능**: 94.70% macro F1, 99.47% AUROC

### 2.2 Stage 2: CNN 기반 열화상 공간 해석

Stage 1이 이상을 감지하면 **조건부로 활성화**되어 열화상 이미지를 분석:

#### 2.2.1 ResNet-18 Encoder

ImageNet pretrained ResNet-18로 열화상 특징 추출:

$$
\mathbf{F} = \text{ResNet}(\mathbf{X}_t) \in \mathbb{R}^{C_f \times H' \times W'}
$$

#### 2.2.2 Spatial Attention

1×1 convolution으로 공간 attention map 생성:

$$
\mathbf{A}_{\text{spatial}} = \sigma(\text{Conv}_{1 \times 1}(\mathbf{F}))
$$

- **목적**: 열적으로 중요한 영역(thermally salient regions) 하이라이팅
- **활용**: 정비 검사 시 우선 점검 위치 제시

---

## 3. 왜 Random Forest가 LSTM/Fusion을 능가하는가?

### 3.1 실험 결과

| 모델 | Macro F1 | AUROC |
|------|----------|-------|
| **Random Forest** (통계 특징) | **94.70%** | **99.47%** |
| LSTM (BiLSTM + Temporal Attention) | 91.22% | 98.12% |
| Multimodal Fusion (Gated) | 85.40% | 96.33% |

**통계적 유의성**: Cohen's d = 3.04–8.81 (매우 큰 효과 크기)

### 3.2 이유 분석

#### 3.2.1 데이터 효율성

- **중소규모 데이터셋(13,121 샘플)**: Transformer나 대형 신경망이 용량 우위를 발휘하기에는 부족
- **통계적 특징 압축**: 시계열 전체를 4개 통계량으로 압축하여 학습 데이터 필요량 대폭 감소
- **Learning Curve**: RF는 전체 데이터의 20%만으로도 LSTM의 전체 데이터 성능 근접

#### 3.2.2 저잡음 산업 센서

산업용 센서는 사전 필터링되어 **저잡음, 고신호 품질**을 가진다. 이 경우:
- 딥러닝의 복잡한 시간 커널(temporal kernels)보다
- 단순한 통계적 집계(mean, std, min, max)가 더 robust

#### 3.2.3 해석 가능성

- **TreeSHAP**: Random Forest는 정확한 Shapley 값 계산 가능 (O(TLD²) 복잡도)
- **신뢰성**: 정비 엔지니어가 "왜 이 결함을 예측했는가?"를 즉각 이해 가능

### 3.3 Multimodal Fusion의 실패 원인

#### 3.3.1 Modality Bias

Fusion 모델의 gate weight 분석 결과:
- **이론적 최적 gate 가중치**: $g^* = 0.241$ (센서 F1 vs 열화상 F1 비율 기반)
- **실제 학습된 gate 가중치**: $\mathbb{E}[g] = 0.67$
- **Modality Bias**: $\mathcal{B} = 0.67 - 0.241 = 0.429$

융합 모델이 **정보량이 적은 열화상 이미지(30.01% F1)에 과도하게 의존**함

#### 3.3.2 형식적 분석

**Gradient-to-Signal Ratio (GSR)** 정의:

$$
\rho_m = \frac{\mathbb{E}[\|\mathbf{g}_m\|]}{\mathcal{I}(Y; \mathbf{X}_m)}
$$

고차원 열화상 이미지의 고분산 잡음이 최적화 landscape를 지배하여, 저차원 센서 신호의 낮은 분산보다 gradient 업데이트가 과도하게 집중됨

**Cascaded Error Bound**:

$$
\epsilon_F \geq \epsilon_s + \delta(\dim(\mathbf{X}_t), N^{-1})
$$

융합 모델의 오류는 센서 단독 오류 $\epsilon_s$에 열화상 차원과 샘플 수에 의존하는 과적합 패널티 $\delta$가 추가됨

---

## 4. Explainability Pipeline

### 4.1 TreeSHAP: 센서 중요도 순위

각 통계 특징의 Shapley 값 계산:

$$
\phi_i(f,x) = \sum_{S \subseteq N \setminus \{i\}} \frac{|S|!(M-|S|-1)!}{M!} [f_x(S \cup \{i\}) - f_x(S)]
$$

센서별 집계:

$$
\Phi_d = |\phi_{\mu_d}| + |\phi_{\sigma_d}| + |\phi_{\min_d}| + |\phi_{\max_d}|
$$

**결과**: 정비 엔지니어가 즉시 확인해야 할 센서 우선순위 제공

### 4.2 Spatial Attention: 열화상 검사 영역

- **Deletion Metric**: attention이 높은 영역을 제거했을 때 예측 신뢰도 감소 확인
- **Binary Fault Detection**: 열화상 CNN이 severity grading은 실패(30.01% F1)하지만, **binary fault detection은 78.49% F1** 달성
  - **해석**: attention은 class-discriminative localizer가 아닌 **spatial regularizer**로 작동
  - 결함의 존재는 감지하지만, 심각도 구분에는 한계

### 4.3 Perturbation Audit

센서 읽기값과 attention 통계 간 상관관계 분석 결과:
- **상관계수**: 거의 0에 근접
- **결론**: attention은 동시 센서 신호가 아닌 **열적 패턴 자체**에 반응

---

## 5. 실무 적용 가이드라인

### 5.1 Cascade를 선택해야 하는 경우

1. **정보량 비대칭성**: 한 모달리티가 다른 것보다 훨씬 유용할 때
   - 예: 진동 센서(즉각 반응) vs 열화상(지연 반응)

2. **작업 분리 가능**: 감지(detection)와 해석(interpretation)이 분리 가능할 때

3. **중소규모 데이터**: 대형 신경망 학습에 충분하지 않은 샘플 수

### 5.2 Fusion 도입 전 진단 체크리스트

1. **단일 모달리티 평가**: 각 모달리티를 독립적으로 평가하여 정보량 격차 정량화
2. **Gate Weight 검사**: 학습된 attention/gate가 모달리티 편향을 보이는지 확인
3. **Modality Corruption Test**: 한 입력을 0으로 만들었을 때 성능 변화 측정

### 5.3 시스템 장점

- **경량화**: Random Forest는 CPU에서 sub-millisecond 추론 가능
- **해석성**: Shapley 값(센서 순위) + Attention 오버레이(검사 영역)
- **신뢰성**: 엔지니어가 모델 결정 근거를 즉시 이해하고 검증 가능

---

## 6. 기술적 기여 요약

| 기여 | 설명 |
|------|------|
| **실증적 증거** | RF가 LSTM/Fusion보다 우수함을 p<0.001 수준에서 입증 |
| **형식적 분석** | Modality Bias와 Cascaded Error Bound 수식화 |
| **진단 프로토콜** | Gate weight 분석으로 융합 모델의 모달리티 편향 정량화 |
| **통합 XAI** | TreeSHAP + Spatial Attention + Perturbation Audit |
| **실무 가이드** | Cascade vs Fusion 선택을 위한 의사결정 체크리스트 |

---

## 7. 한계 및 향후 연구

### 7.1 현재 한계

1. **공간적 Ground Truth 부재**: 열화상 attention의 localization 정확도를 직접 검증 불가
   - 현재는 deletion metric과 binary detection으로 간접 검증
   
2. **4-class Severity Grading**: 열화상 CNN의 severity 구분 성능 미흡(30.01% F1)
   - Binary fault detection(78.49% F1)은 성공적이나, 세밀한 등급 구분은 추가 연구 필요

3. **단일 도메인**: OHT/AGV 데이터셋에 한정
   - 타 산업 설비(발전소, 철도 등)로의 일반화 검증 필요

### 7.2 향후 방향

- **Few-shot Learning**: 소량 데이터로 신규 설비 적응
- **Continual Learning**: 온라인 환경에서 지속적 모델 업데이트
- **Domain Adaptation**: 시뮬레이션 → 실제 설비 전이 학습

---

## 8. 결론

본 논문은 **"멀티모달 융합이 항상 최선은 아니다"**라는 중요한 교훈을 실증적으로 제시한다. 정보량 비대칭성이 존재하고 작업이 분리 가능한 산업 모니터링 환경에서는:

- **Cascade 아키텍처**가 end-to-end fusion보다 우수
- **전통적 ML**(Random Forest)이 딥러닝(LSTM)보다 데이터 효율적이고 해석 가능
- **Modality Bias 진단**이 융합 모델 설계의 필수 과정

정비 엔지니어가 신뢰할 수 있는 XAI 파이프라인(TreeSHAP + Spatial Attention)을 통해, 이론적 성능뿐 아니라 **실무 적용 가능성**까지 확보한 연구다.

---

**References**  
- arXiv:2512.24755 (v3, 2026-02-22)  
- Dataset: AI Hub Korea OHT/AGV Monitoring  
- Code & Models: Upon publication (announced)

**Related Topics**  
`#PredictiveMaintenance` `#AnomalyDetection` `#MultimodalLearning` `#ExplainableAI` `#IndustrialAI` `#RandomForest` `#ThermalImaging` `#CBM` `#PHM`
