# 📡 WAVAE: 시계열 이상 탐지를 위한 자기지도학습 기반 VAE의 진화

## 1. 서론: 왜 다시 VAE인가?

재구성 기반의 시계열 이상 탐지(Time Series Anomaly Detection, TSAD)에서 **Variational Autoencoder(VAE)**는 불확실성 추정과 비지도 학습 능력 덕분에 오랫동안 사랑받아왔습니다. 하지만 실제 산업 현장에서는 **데이터 부족(Data Scarcity)**이라는 큰 벽에 부딪히곤 합니다.

충분한 정상 데이터가 확보되지 않은 상태에서 VAE를 학습시키면, 잠재 공간(Latent Space)에 불연속적인 영역인 **'Latent Hole'**이 발생합니다. 이 영역에 이상치가 매핑되면 모델이 이를 정상으로 오인하거나 재구성이 불안정해지는 문제가 발생하죠.

오늘 소개할 **WAVAE(Weakly Augmented Variational Autoencoder)**는 이 문제를 해결하기 위해 VAE와 **자기지도학습(Self-Supervised Learning, SSL)**을 결합한 혁신적인 프레임워크입니다.

---

## 2. 핵심 문제: Latent Hole 현상

VAE의 인코더가 학습 데이터에 없는 패턴(이상치)을 잠재 공간으로 보낼 때, 주변에 이를 교정해줄 정상 데이터가 부족하면 잠재 공간이 매끄럽게 형성되지 않습니다.

- **문제점**: 불연속적인 잠재 공간에서 샘플링된 값은 입력 데이터와 재구성 데이터 간의 불일치를 유발합니다.
- **결과**: 이상 탐지 성능이 저하되고 모델의 견고성(Robustness)이 깨지게 됩니다.

---

## 3. WAVAE의 해결 전략: 데이터 증강 + 상호 정보량 극대화

WAVAE는 단순히 데이터를 복제하는 것이 아니라, **약한 증강(Weak Augmentation)**을 통해 잠재 공간의 밀도를 높이고 모델을 더 견고하게 만듭니다.

### ① 이중 생성 모델 구조 (Dual Generative Model)
WAVAE는 원본 데이터($x_r$)를 처리하는 모델과 증강된 데이터($x_a$)를 처리하는 모델을 동시에 운영합니다. 두 모델은 각각의 잠재 변수($z_r, z_a$)를 생성하지만, 결국 **하나의 최적화된 데이터 분포**로 수렴하도록 설계되었습니다.

### ② 상호 정보량(Mutual Information) 최적화
두 모델의 학습 결과를 동기화하기 위해 **ELBO(Evidence Lower Bound)** 내에서 잠재 변수 간의 상호 정보량을 극대화합니다.
- **Shallow Learning**: 대조 학습(Contrastive Learning)을 통해 정보량 근사.
- **Deep Learning**: 적대적 전략(Adversarial Strategy)을 활용한 심층 신경망 최적화.

---

## 4. 왜 'WAVAE'가 실무에 강한가?

1. **데이터 효율성**: 소량의 시계열 데이터만으로도 SSL을 통해 풍부한 표현형(Representation)을 학습할 수 있습니다.
2. **견고한 재구성**: Latent Hole을 메워줌으로써 이상치에 대한 민감도는 높이고, 정상 데이터에 대한 재구성 성능은 안정화합니다.
3. **범용성**: 특정 도메인에 종속된 Prior(사전 확률) 설계 없이도 시공간적 의존성을 효과적으로 포착합니다.

---

## 5. 실험 결과 및 시사점

WAVAE는 5개의 공개 데이터셋(합성 및 실제 데이터)에서 기존 SOTA(State-of-the-Art) 모델들을 뛰어넘는 **ROC-AUC 및 PR-AUC 점수**를 기록했습니다. 특히 시계열 데이터의 전처리 방식과 하이퍼파라미터 민감도 분석을 통해 딥러닝 최적화의 새로운 가이드라인을 제시했다는 평가를 받습니다.

---

## 결론: 에이전틱 PHM으로의 연결

WAVAE와 같은 견고한 이상 탐지 모델은 단순히 "이상이 있다"고 말하는 단계를 넘어, **MALT 시스템**이 "왜 이상인지" 해석하고 "어떤 조치를 취해야 하는지" 결정하는 **에이전틱 워크플로우**의 핵심 엔진이 됩니다.

수치적 이상 수치($z$)를 의미론적 정비 용어(Semantic Metadata)로 변환하는 과정에서, WAVAE가 제공하는 안정적인 잠재 공간은 더 정확한 RAG 검색과 리포트 생성을 가능하게 할 것입니다.

---
**참고 문헌**: *Wu, Z., & Cao, L. (2024). Weakly Augmented Variational Autoencoder in Time Series Anomaly Detection. arXiv preprint arXiv:2401.03341.*
