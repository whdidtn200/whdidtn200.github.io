---
title: "Predictive Maintenance KPI and ROI Guide: 예지보전 성과를 무엇으로 측정해야 하는가"
date: 2026-06-17
slug: "predictive-maintenance-kpi-roi-guide"
categories: ["maintenance", "analytics", "roi", "guide"]
tags: ["Predictive Maintenance", "KPI", "ROI", "Lead Time", "False Alarms", "Operations"]
draft: true
generated_by: "MALT"
workflow: "AI-managed publication"
---

# Predictive Maintenance KPI and ROI Guide: 예지보전 성과를 무엇으로 측정해야 하는가

예지보전 프로젝트가 실패하는 가장 흔한 이유 중 하나는 기술이 아니라 성과 측정 방식입니다.

정확도나 F1 score만 보고 시작하면, 운영팀은 '그래서 실제로 어떤 비용이 줄었는가'라는 질문에 답을 듣지 못합니다.

이 글은 predictive maintenance KPI와 ROI를 어떻게 잡아야 하는지 고민하는 운영 리더와 유지보수 책임자를 위한 실무형 가이드입니다.

## 왜 정확도가 핵심 사업 KPI가 아닌가

모델 정확도는 중요한 기술 지표이지만, 사업 지표는 아닙니다. 유지보수 조직이 실제로 궁금한 것은 경보가 얼마나 일찍 왔는지, 불필요한 작업을 줄였는지, 다운타임을 줄였는지입니다.

특히 드문 고장 환경에서는 accuracy가 높아 보여도 현장 가치는 거의 없을 수 있습니다. 정상 데이터가 대부분이기 때문입니다.

## Leading indicator와 lagging indicator를 나눠서 보라

예지보전 KPI는 즉시 반응 지표와 결과 지표를 분리해서 봐야 합니다. lead time, alert quality, inspection conversion은 leading indicator이고, downtime avoided, MTBF improvement, spare usage reduction은 lagging indicator에 가깝습니다.

이 구분이 없으면 프로젝트 초기에 기대치가 과도하게 커지거나, 반대로 의미 있는 초기 개선을 놓치게 됩니다.

- Leading: detection lead time, alert precision, inspection conversion
- Lagging: downtime reduction, maintenance cost avoidance, asset availability

## 실제로 중요한 유지보수 KPI

현업에서는 다음 KPI들이 가장 자주 의미를 가집니다. lead time은 계획 정비 가능성을 보여주고, false alarm burden은 조직 피로도를 보여주며, work order conversion은 모델이 운영 체계에 들어왔는지를 보여줍니다.

여기에 downtime avoided와 repeat failure recurrence까지 보면, 예지보전이 단순 탐지 시스템인지 실제 운영 개선 장치인지 구분할 수 있습니다.

- Detection lead time
- False alarm burden
- Work order conversion rate
- Unplanned downtime avoided
- Repeat failure recurrence
- Maintenance labor efficiency

## ROI는 어떻게 계산해야 하나

예지보전 ROI는 단순히 장비 1건 고장을 막은 비용으로 계산하면 왜곡되기 쉽습니다. 센서, 데이터 수집, 분석 운영, 작업자 교육, false positive 대응 비용까지 함께 봐야 합니다.

초기 파일럿에서는 full ROI보다 `decision-quality improvement`와 `avoidable event reduction`을 먼저 추적하는 편이 현실적입니다. 이후 파일럿이 반복되면서 비용 모델을 더 정확히 만들 수 있습니다.

## 철도와 회전체 프로그램에 맞는 scorecard 예시

철도나 회전체 설비에서는 자산 특성상 안전과 운영 지연 비용이 함께 걸려 있습니다. 따라서 KPI scorecard도 기술팀, 정비팀, 운영팀이 같이 읽을 수 있어야 합니다.

예를 들어 corridor별 lead time, depot별 false alarm burden, axle or bearing family별 repeat-fault rate처럼 운영 구조에 맞춘 차원을 쓰는 편이 좋습니다.

- 주간 경보 건수와 inspection 전환율
- 월간 false alarm burden과 점검 소요 시간
- 분기별 다운타임 회피 시간과 비용 추정
- 자산군별 recurrence rate

## 파일럿에서 기대치를 어떻게 관리할까

초기 90일 동안은 ROI를 과하게 약속하지 않는 편이 좋습니다. 먼저 baseline을 만들고, 어디에서 의미 있는 조기 경고가 나오는지 확인해야 합니다.

그다음 6개월 단위에서 lead time, work order conversion, false alarm burden 추세를 보고, 그 이후에 downtime avoided를 더 본격적으로 추정하는 편이 현실적입니다.

## MALT가 추천하는 다음 읽을거리

- [2026-03-01-wayside-condition-monitoring-review](/posts/2026-03-01-wayside-condition-monitoring-review.html)
- [[arXiv Daily] Low-Data Predictive Maintenance of Railway Station Doors and Elevators Using Bayesian Proxy Flow Modeling](/posts/2026-03-15-260314384v1-low-data-predictive-maintenance-of-railway-station-doors-and-elevat.html)

## 마무리

예지보전의 성과는 모델이 얼마나 똑똑한지보다, 조직이 그 신호를 얼마나 일관되게 행동으로 바꾸는지에서 갈립니다.

그래서 MALT 관점에서 KPI의 출발점은 '정확도가 몇 퍼센트인가'가 아니라, **'이 경보가 실제로 어떤 비용과 위험을 줄였는가'** 입니다.

## 출처

- MALT 큐레이션 내부 아카이브와 관련 포스트를 바탕으로 정리
- 개별 논문/사례 해석은 연결된 내부 글과 원문을 함께 검토하는 편이 좋음

## 발행 메모

- MALT 큐레이션 장문 가이드 초안
- 맥미니 자동 편집 워크플로가 outline을 확장해 생성한 문서
- 발행 전 비교표, 표준 체크리스트, CTA를 추가하면 더 강해짐
