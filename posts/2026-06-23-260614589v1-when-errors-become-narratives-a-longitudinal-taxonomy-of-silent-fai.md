---
title: "[arXiv Daily] When Errors Become Narratives: A Longitudinal Taxonomy of Silent Failures in a Production LLM Agent Runtime"
date: 2026-06-23 09:17:00 +0900
tags:
  - arXiv
  - MALT
  - Agentic AI
  - Observability
  - Reliability
  - AI Ops
  - Operations
categories:
  - Daily arXiv
  - AI Ops
summary: "장기 운영되는 LLM 에이전트에서 오류가 조용히 숨거나 그럴듯한 설명으로 바뀌는 문제를, 실제 8주 운영 사고 기록으로 분석한 논문을 실무 관점에서 읽는다."
---

# [arXiv Daily] When Errors Become Narratives: A Longitudinal Taxonomy of Silent Failures in a Production LLM Agent Runtime

**블로그 발행일**: 2026-06-23  
**논문 공개일**: 2026-06-12  
**원문 논문**: When Errors Become Narratives: A Longitudinal Taxonomy of Silent Failures in a Production LLM Agent Runtime  
**저자**: Wei Wu

## 한 줄 요약

이 논문은 장기 운영되는 LLM 에이전트가 실패했을 때 단순히 멈추는 것이 아니라, 오류 신호를 숨기거나 그럴듯한 이야기로 바꿔 사용자에게 전달하는 문제를 실제 운영 사고 기록으로 분석한다.

## 왜 지금 볼 만한가

철도 PHM이나 산업 설비 관측에서 중요한 원칙은 "고장이 나지 않는 시스템"보다 "고장이 났을 때 빨리, 정확히, 행동 가능한 방식으로 드러나는 시스템"이다. 이 논문은 물리 설비 논문은 아니지만, MALT가 계속 다뤄온 observability와 predictive maintenance의 운영 철학과 맞닿아 있다.

LLM 에이전트는 이제 단발성 챗봇이 아니라 예약 작업을 돌리고, 도구를 호출하고, 메모리를 갱신하고, 결과를 사람에게 푸시하는 런타임으로 쓰인다. 이런 시스템에서 가장 위험한 실패는 크래시가 아니다. 크래시는 적어도 멈췄다는 신호를 준다. 더 까다로운 실패는 내부에서는 문제가 생겼는데, 외부로는 정상적인 결과처럼 보이는 경우다.

이 논문이 흥미로운 이유는 바로 그 지점을 실제 운영 사례로 잡았기 때문이다. 저자는 2026년 3월부터 운영된 개인 비서형 에이전트 런타임을 대상으로 8주 동안의 silent failure를 정리했다. 시스템은 약 40개의 예약 작업, 8개의 LLM provider, tool-governance proxy, knowledge-base memory plane을 포함했고, 4,286개 unit test와 827개 governance check를 갖고 있었다. 그런데도 silent failure는 계속 발생했다.

## 이 논문이 풀려는 실제 문제

논문이 묻는 질문은 단순하다. "테스트와 체크가 모두 초록색인데도 사용자는 왜 잘못된 결과를 받는가?"

일반 소프트웨어에서도 gray failure는 오래된 문제다. 어떤 컴포넌트는 느려지거나 잘못 동작하지만, 모니터링 시스템은 정상이라고 말한다. LLM 에이전트에서는 여기에 한 단계가 더 붙는다. 에이전트는 언어를 생성하기 때문에, 내부 오류를 침묵으로 남기는 대신 그럴듯한 문장으로 포장할 수 있다.

예를 들어 API 오류 페이지가 캐시에 섞였는데, downstream LLM이 그 오류 문자열을 실제 산업 동향 신호처럼 읽고 "플랫폼 위기" 분석을 만들어 사용자에게 보낸다면 어떨까. 이때 사용자는 실패를 보는 것이 아니라 실패가 만든 이야기, 즉 counterfeit signal을 본다. 논문은 이런 유형을 `fail-plausible`이라고 부른다.

이 관점은 산업 observability에도 그대로 중요하다. 센서 시스템이나 정비 대시보드에서 "데이터 없음"은 차라리 다루기 쉽다. 더 위험한 것은 결측, 지연, 스키마 불일치, 잘못된 캐시가 정상 수치나 자연스러운 설명으로 변환되어 정비 판단에 들어가는 경우다.

## 방법을 쉬운 말로 풀면

논문은 새로운 모델을 제안하기보다, 실제 운영 중 발생한 사고를 체계적으로 분해한다. 방법은 세 단계로 이해하면 된다.

- **사고 코퍼스 구성**: 8주 동안 22건의 silent-failure incident를 모으고, 각 사고에 대해 full root-cause postmortem을 작성했다.
- **메커니즘 중심 분류**: 사고가 발생한 파일이나 컴포넌트 위치가 아니라, 실패가 어떻게 조용해졌는지에 따라 다섯 클래스로 나눴다.
- **방어 프레임워크 정리**: 각 사고에서 나온 교훈을 point fix에 머무르게 하지 않고, meta-rule, scanner, sabotage validation, declared-state convergence 같은 운영 장치로 바꾸려 했다.

다섯 클래스는 다음과 같다.

- **A. Environment and platform quirks**: OS, 파일시스템, 런타임 환경 차이처럼 코드 밖 조건에서 생기는 실패다.
- **B. Design-assumption mismatches**: 개발자가 당연하다고 둔 계약이 실제 운영에서는 맞지 않는 경우다.
- **C. Error swallowing and dilution**: 오류가 잡히긴 했지만, 로그나 요약 과정에서 행동 가능한 신호로 남지 않는 경우다.
- **D. Chained hallucination and fabrication**: LLM이 오염된 컨텍스트를 그럴듯한 설명이나 성과로 바꾸는 경우다. 논문은 이 클래스를 LLM 시스템 특유의 가장 위험한 유형으로 본다.
- **E. Operational omission and forensic blind spots**: 필요한 관측 지점이 없거나, 사고 후 원인을 복원할 로그가 부족한 경우다.

핵심은 이 분류가 문학적 라벨이 아니라 운영 단위라는 점이다. "이 파일에서 버그가 났다"가 아니라 "이런 메커니즘으로 실패 신호가 사람에게 도달하지 못했다"라고 보면, 같은 유형을 다른 컴포넌트에서도 막을 수 있다.

## 실험과 숫자를 어떻게 읽어야 하나

이 논문은 benchmark leaderboard 논문이 아니다. 그래서 정확도 1등 같은 숫자를 기대하면 잘못 읽게 된다. 대신 운영 사고 연구로 읽어야 한다. 중요한 수치는 다음과 같다.

- 연구 대상 시스템은 약 40개의 scheduled job, 8개의 LLM provider, tool-governance proxy, memory plane으로 구성됐다.
- 방어 장치로 4,286개 unit test와 827개 declarative governance check가 있었다.
- 8주 동안 22건의 incident가 full root-cause postmortem으로 정리됐다.
- "오류 신호가 행동 가능한 형태로 사람에게 도달하지 못하는" meta-pattern은 최소 28회 나타났다.
- silent failure의 약 70%는 unit test나 audit이 아니라, 사용자가 출력물을 직접 보고 발견했다.
- 15건의 incident에 대한 retrospective audit에서 ex-ante prevention은 0%, ex-post regression blocking은 87%였다.
- incident latency는 13시간부터 60일까지 벌어졌고, 긴 latency는 코드 복잡도보다 component 사이의 경계, 배포 상태, 관측자와 관측 대상의 결합 같은 seam에서 나왔다.

이 숫자들이 말하는 바는 불편하다. 테스트가 많아도 silent failure는 남는다. audit은 과거 사고의 재발을 막는 데는 쓸모가 있지만, 처음 보는 사고를 미리 막는 장치로 과신하면 안 된다. 그리고 사용자가 제일 많이 발견했다는 사실은 "자동화가 미숙했다"는 뜻만은 아니다. 오히려 자동화가 일정 수준 이상 갖춰진 시스템에서도, 사람이 보는 최종 출력과 내부 health check 사이에는 큰 간극이 남는다는 뜻이다.

## 실무에서 중요한 해석

내가 이 논문에서 가장 중요하게 보는 문장은 "audit is a regression engine, not a prediction engine"에 가깝다. 현업에서는 보안 점검, 운영 체크리스트, 테스트 커버리지를 만들면 마음이 편해진다. 하지만 이 논문은 그런 장치가 대체로 이미 한 번 본 실패를 다시 막는 쪽에 강하고, 아직 분류되지 않은 실패를 예측하는 능력은 약하다고 말한다.

이건 PHM에서도 익숙한 이야기다. 과거 베어링 결함 패턴을 잘 학습한 모델은 같은 결함이 반복될 때 강하다. 하지만 센서 설치 조건이 바뀌거나, 새로운 운행 패턴이 들어오거나, 데이터 파이프라인의 결측이 정상값처럼 보정되면 모델은 매우 자신 있게 틀릴 수 있다. LLM 에이전트의 fail-plausible은 이 문제를 언어 출력에서 보여준다.

운영 설계 관점에서 이 논문은 세 가지 질문을 남긴다.

- 이 시스템은 실패했을 때 "실패했다"고 말할 수 있는가?
- 실패 원인이 어느 계층에서 생겼는지 attribution을 남기는가?
- 사람이 보는 최종 출력과 내부 monitor가 서로 다른 현실을 보고 있지는 않은가?

특히 LLM 에이전트를 산업 데이터 파이프라인에 붙일 때는 결과 문장만 검수해서는 부족하다. 어떤 원천 데이터가 들어왔는지, 어떤 도구 호출이 실패했는지, 어떤 캐시나 memory가 사용됐는지, 출력이 생성되기 전 어떤 guard가 통과됐는지를 함께 남겨야 한다.

## 현장 적용 체크리스트

- **출력 검수보다 입력-도구-메모리 provenance를 먼저 남긴다.** 에이전트가 그럴듯한 요약을 만들었다면, 그 요약이 어떤 데이터와 호출 결과에서 나왔는지 역추적할 수 있어야 한다.
- **silent success를 경계한다.** "작업 완료" 메시지가 실제 artifact, 외부 상태, 사용자-visible 결과와 일치하는지 별도 확인해야 한다.
- **observer를 관측 대상과 분리한다.** 에이전트가 자기 실패를 스스로 설명하게 두면, 오염된 컨텍스트가 감시 루프까지 번질 수 있다.
- **postmortem을 문서로 끝내지 않는다.** 한 번 겪은 실패는 meta-rule이나 scanner로 바꿔 regression blocking 장치에 넣어야 한다.
- **sabotage validation을 둔다.** guard가 있다고 말하는 것과, 일부러 깨뜨렸을 때 실제로 울리는지는 다르다.
- **대시보드에는 confidence보다 evidence를 노출한다.** LLM의 유창한 문장보다 원천 로그, tool result, state diff, 누락된 단계가 더 중요하다.

## 철도 PHM과의 연결

이 논문은 철도 논문이 아니기 때문에, 직접적인 차량/선로 결함 진단 방법을 제공하지는 않는다. 그래도 MALT에서 발행할 가치가 있다고 본 이유는 운영 실패의 구조가 비슷하기 때문이다.

철도 PHM 시스템도 점점 여러 계층이 결합된다. wayside sensor, onboard sensor, edge gateway, feature pipeline, anomaly model, ticketing system, 정비 이력 DB, 운영 대시보드가 연결된다. 여기서 silent failure가 생기는 지점은 대개 모델 내부 하나가 아니라 경계다.

예를 들어 wheel impact load detector가 이벤트를 냈는데 ticketing system으로 넘어가는 mapping이 틀렸거나, 센서 결측이 interpolation으로 너무 매끈하게 메워졌거나, dashboard가 오래된 캐시를 최신 결과처럼 보여준다면 어떻게 될까. 모델은 정상처럼 보이고, 대시보드는 조용하고, 정비팀은 잘못된 우선순위를 받을 수 있다. LLM이 그 위에 "운영 요약"을 생성한다면 잘못된 상태가 더 설득력 있게 포장될 가능성도 있다.

따라서 이 논문은 AI agent reliability 글이면서 동시에 "산업 관측 시스템에서 조용한 실패를 어떻게 설계상 크게 만들 것인가"라는 글로 읽을 수 있다. PHM에서 목표는 모든 실패를 없애는 것이 아니라, 실패를 작고 조용한 상태로 방치하지 않는 것이다.

## 한계와 조심할 점

논문 스스로 한계를 비교적 분명히 말한다. 이 연구는 단일 시스템, 단일 운영자 쌍, 하나의 OS, 8주 관측에 기반한 case study다. 따라서 70% user-view discovery나 13시간-60일 latency 같은 숫자를 일반 상수처럼 받아들이면 안 된다.

또 하나의 한계는 classification bias다. 사고 분류는 시스템 운영자와 AI 협업자가 수행했고, 독립 annotator가 따로 있었던 것은 아니다. 저자는 각 클래스가 실제 scanner나 방어 규칙으로 이어진다는 점을 완화 근거로 제시하지만, 그래도 mechanism assignment에는 주관이 들어갈 수 있다.

마지막으로 corpus는 "언젠가 발견된 실패"만 포함한다. 아직도 조용히 남아 있는 실패는 데이터에 들어오지 않는다. 이 점은 논문의 주장을 약하게 만들기보다, silent failure의 tail risk가 더 길 수 있다는 경고로 읽는 편이 맞다.

## 발행 판단

발행한다. 다만 철도 PHM 직접 논문이 아니라는 점을 명확히 달고 발행한다. 오늘 큐에는 railway, bearing, predictive maintenance 직접 후보가 남아 있지 않았고, 대부분 agent-ops 논문이었다. 그중 이 논문은 단순한 에이전트 성능 논문이 아니라 장기 운영, 관측 실패, 감사의 한계, 사고 후 방어 체계라는 주제를 다룬다. 그래서 MALT의 industrial observability 축에는 충분히 연결된다.

내 판단으로는 이 글을 "LLM 에이전트가 위험하다"는 일반론으로 읽으면 가치가 줄어든다. 더 실용적인 독해는 "자동화 시스템의 실패 신호가 사람에게 도달하기 전에 어떻게 희석되고, 가려지고, 때로는 그럴듯하게 변환되는가"를 보는 것이다. 이 질문은 에이전트 런타임에도, 철도 PHM 대시보드에도, 예지보전 알림 시스템에도 그대로 남는다.

## 쉽게 결론만 말하면

이 논문은 에이전트 운영에서 가장 무서운 실패가 "대답을 못 하는 것"이 아니라 "틀린 상태를 그럴듯하게 말하는 것"일 수 있음을 보여준다. 그래서 실무자는 모델 성능보다 먼저 실패의 관측 가능성, 원인 추적성, 최종 출력과 실제 상태의 일치 여부를 설계해야 한다.

## 출처

- [arXiv abs](https://arxiv.org/abs/2606.14589v1)
- [arXiv pdf](https://arxiv.org/pdf/2606.14589v1)
- [arXiv html](https://arxiv.org/html/2606.14589v1)

## 발행 메모

- MALT daily arXiv pipeline의 unpublished queue를 검토해 발행함
- MALT 큐레이션과 AI-managed editorial workflow를 거친 발행본
- 발행 전 원문 초록과 arXiv HTML 본문을 확인함
- 블로그 발행일과 논문 공개일을 별도로 표기함
