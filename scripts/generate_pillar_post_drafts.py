#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import html
import pathlib
import re
from typing import Iterable


ROOT = pathlib.Path(__file__).resolve().parent.parent
DRAFTS_DIR = ROOT / "content" / "drafts"


GUIDE_BLUEPRINTS = {
    "wayside-condition-monitoring-guide": {
        "title": "Wayside Condition Monitoring Guide: 철도 선로변 상태 감시를 실제 운영 체계로 만드는 방법",
        "categories": ["railway", "condition-monitoring", "wayside", "guide"],
        "tags": ["Wayside", "Railway", "Condition Monitoring", "WILD", "Acoustic", "PHM"],
        "intro": [
            "선로변 상태 감시는 차량 내부 센서만으로는 놓치기 쉬운 이상 징후를 반복적이고 표준화된 방식으로 읽어내는 체계입니다.",
            "특히 차량 편차, 센서 유지보수 부담, 구간별 위험도 차이를 함께 다뤄야 하는 철도 운영에서는 `onboard-only monitoring`보다 더 실무적인 출발점이 될 수 있습니다.",
            "이 글은 wayside condition monitoring을 기획하거나, 이미 설치된 선로변 설비를 더 운영 가치 있게 쓰고 싶은 팀을 위한 실무형 가이드입니다.",
        ],
        "sections": [
            {
                "heading": "Wayside Condition Monitoring이 onboard monitoring보다 나은 지점",
                "paragraphs": [
                    "선로변 상태 감시는 같은 위치에서 여러 차량을 반복 관측할 수 있다는 점이 가장 큽니다. 이 구조 덕분에 설비별 편차보다 `통과 패턴의 차이`를 보기 쉬워지고, 개별 차량마다 센서를 대규모로 붙이지 않아도 됩니다.",
                    "또한 유지보수 관점에서도 선로변 설비는 접근성과 표준화 면에서 유리합니다. onboard 센서 네트워크는 차량 수가 늘수록 유지 비용이 함께 증가하지만, wayside 설비는 핵심 구간에 집중 배치하는 방식으로 운영할 수 있습니다.",
                ],
                "bullets": [
                    "같은 구간을 지나는 다수 차량을 동일 조건에서 비교 가능",
                    "차량별 센서 설치 비용을 줄이고 핵심 구간에 투입 가능",
                    "이상 징후를 노선 운영 위험과 직접 연결하기 쉬움",
                ],
            },
            {
                "heading": "무엇을 측정해야 하나",
                "paragraphs": [
                    "선로변 시스템은 하나의 센서로 끝나지 않습니다. 바퀴 충격, 차축 상태, 베어링 이상, 통과 소음, 열 이상, 기하학적 편차처럼 서로 다른 신호를 조합해서 봐야 운영적 해석력이 생깁니다.",
                    "중요한 것은 센서 종류보다 `어떤 고장 모드를 조기에 잡고 싶은지`를 먼저 정하는 일입니다. wheel impact load detector와 acoustic wayside system은 잡아내는 신호가 다르고, 이후 정비 조치도 달라집니다.",
                ],
                "bullets": [
                    "WILD: wheel flat, impact, 비정상 충격 하중 추적",
                    "Acoustic monitoring: 베어링/회전체 소음 특성 감지",
                    "Thermal monitoring: 과열, 마찰 증가, hot box 계열 경보",
                    "Vision or profile systems: 형상 편차, 표면 결함 보완",
                ],
            },
            {
                "heading": "KPI는 어떻게 잡아야 하나",
                "paragraphs": [
                    "wayside 시스템의 KPI는 단순 검출률이 아니라 운영 결과로 이어져야 합니다. 경보가 몇 건 발생했는지보다, 그 경보가 실제 inspection, speed restriction, component replacement 같은 조치로 얼마나 이어졌는지가 더 중요합니다.",
                    "특히 철도 운영에서는 false alarm burden을 별도 KPI로 관리하지 않으면 현장 신뢰가 급격히 떨어집니다. 신뢰를 잃은 경보 시스템은 정확도가 높아도 무시되기 쉽습니다.",
                ],
                "bullets": [
                    "Detection lead time",
                    "Alert-to-inspection conversion rate",
                    "False alarm burden per corridor or depot",
                    "Unplanned downtime avoided",
                    "Repeat-fault recurrence after intervention",
                ],
            },
            {
                "heading": "데이터 지연과 정비 출동 흐름",
                "paragraphs": [
                    "선로변 감시는 실시간 점수화와 운영 큐레이션이 함께 있어야 가치가 큽니다. 센서 데이터가 쌓이는 것만으로는 부족하고, 어느 임계치를 넘었을 때 어떤 차량을 어떤 depot에서 점검할지까지 이어져야 합니다.",
                    "그래서 wayside 시스템은 모델보다 먼저 `데이터 수집 -> 점수화 -> 경보 검토 -> 작업 지시` 흐름이 정의되어야 합니다. 실제 현장에서는 점수화보다 티켓 생성 규칙이 먼저 병목이 되는 경우가 많습니다.",
                ],
            },
            {
                "heading": "AI는 어디에 붙이는 편이 좋은가",
                "paragraphs": [
                    "선로변 감시에서 AI의 첫 역할은 완전 자동 판단보다 `우선순위 정렬`에 가깝습니다. 즉시 교체가 필요한 차량을 선별하거나, 반복적으로 비슷한 경향을 보이는 차량을 랭킹하는 쪽이 더 현실적입니다.",
                    "고도화 단계에서는 멀티센서 score fusion, route-aware anomaly scoring, maintenance recommendation까지 갈 수 있지만, 초기에는 경보 triage와 false positive 감소에 집중하는 편이 낫습니다.",
                ],
                "bullets": [
                    "초기: rule-based scoring + threshold review",
                    "중간: sensor fusion + anomaly ranking",
                    "고도화: corridor-aware prioritization + maintenance decision support",
                ],
            },
            {
                "heading": "파일럿 구간은 이렇게 시작하는 편이 좋다",
                "paragraphs": [
                    "wayside condition monitoring 파일럿은 노선 전체가 아니라 고장 비용이 큰 구간 하나에서 시작하는 편이 좋습니다. 차량 종류, 통과 빈도, 기존 정비 절차, 장애 이력까지 함께 고려해야 실제 운영 전환이 가능합니다.",
                    "처음에는 sensor coverage를 넓히기보다, 경보가 실제 점검으로 이어지고 그 결과가 다시 데이터로 남는 폐쇄 루프를 만드는 것이 우선입니다.",
                ],
                "bullets": [
                    "1개 corridor 또는 hotspot부터 시작",
                    "경보 후 inspection feedback을 구조화해 저장",
                    "3개월 단위로 false alarm burden과 lead time을 재평가",
                ],
            },
        ],
        "closing": [
            "Wayside condition monitoring의 강점은 더 많은 데이터를 모으는 데 있지 않습니다. `같은 위치에서 반복적으로 비교하고, 그 차이를 정비 행동으로 바꾸는 구조`에 있습니다.",
            "그래서 MALT 관점에서 wayside 시스템의 핵심 질문은 '센서를 더 붙일까'가 아니라, **'어떤 이상 징후를 어느 시점에 현장 팀이 믿고 행동하게 만들 것인가'** 입니다.",
        ],
    },
    "railway-bearing-sensor-guide": {
        "title": "Railway Bearing Sensor Guide: 철도 베어링 모니터링 센서를 어떻게 고르고 배치할 것인가",
        "categories": ["railway", "bearing", "sensors", "guide"],
        "tags": ["Bearing", "Sensors", "Railway", "Vibration", "AE", "Condition Monitoring"],
        "intro": [
            "철도 베어링 모니터링은 모델을 잘 고르는 문제 이전에 `센서와 데이터 수집 구조를 어떻게 설계하느냐`의 문제입니다.",
            "실제로 많은 프로젝트가 AI 성능 부족이 아니라 샘플링 불일치, 장착 위치 편차, 동기화 실패, 운영 환경 노이즈 때문에 무너집니다.",
            "이 글은 railway bearing monitoring sensors를 고르거나 wheel bearing 조기 경보 체계를 설계하려는 팀을 위한 실무형 가이드입니다.",
        ],
        "sections": [
            {
                "heading": "왜 센서 단계에서 이미 실패하는가",
                "paragraphs": [
                    "베어링 모니터링은 같은 결함이라도 센서 위치, 하우징 구조, 회전수, 하중에 따라 파형이 크게 달라집니다. 그래서 센서를 아무 데나 붙이고 모델이 알아서 해결해주길 기대하면 실패 확률이 높습니다.",
                    "현장에서는 특히 센서 표준화와 설치 재현성이 중요합니다. 같은 fleet 내에서도 설치 차이가 크면, 장비 간 비교 자체가 흔들립니다.",
                ],
            },
            {
                "heading": "주요 센서 선택지와 장단점",
                "paragraphs": [
                    "진동 센서는 여전히 기본 선택입니다. 특징 주파수 기반 분석과 딥러닝 접근 모두에 잘 맞고, 해석 가능성도 상대적으로 좋습니다.",
                    "AE 센서는 초기 미세 결함에 더 민감할 수 있지만, 취득 장비와 현장 노이즈 관리 난이도가 올라갑니다. 온도 센서는 느리지만 운영자가 이해하기 쉬운 보조 지표이고, 전류 기반 신호는 추가 센서 설치가 어려운 구간에서 현실적 대안이 될 수 있습니다.",
                ],
                "bullets": [
                    "Vibration: 가장 범용적이고 분석 생태계가 풍부함",
                    "AE: 초기 충격성 결함에 민감하지만 장비 비용과 해석 난이도 존재",
                    "Temperature: 추세 모니터링 보조 지표로 유용",
                    "Electrical/current signals: 센서 추가가 어려운 환경에서 대안",
                ],
            },
            {
                "heading": "배치와 샘플링이 모델보다 중요할 때",
                "paragraphs": [
                    "샘플링 주파수와 동기화 품질은 이후 모든 분석을 좌우합니다. envelope analysis나 time-frequency 방법을 쓸 계획이라면 필요한 대역폭을 먼저 확보해야 하고, 열차 속도 변화가 큰 환경이라면 속도 정보까지 함께 저장해야 합니다.",
                    "또한 periodic inspection과 online monitoring은 설계 철학이 다릅니다. 주기 점검은 고품질 정밀 측정에 유리하고, 온라인 감시는 장기 추세와 조기 경보에 유리합니다. 둘을 섞어 쓰되 목적을 구분해야 합니다.",
                ],
            },
            {
                "heading": "현장 노이즈와 환경 변수를 어떻게 다뤄야 하나",
                "paragraphs": [
                    "철도 환경은 진동만 깔끔하게 들어오지 않습니다. 선로 상태, 속도 변화, 하중, 기상 조건, 차체 구조 공진이 함께 섞입니다. 그래서 raw signal만 저장하는 것보다 운영 맥락 데이터까지 묶어 저장하는 편이 훨씬 중요합니다.",
                    "실무적으로는 sensor signal 옆에 speed, axle position, ambient temperature, maintenance event 같은 보조 필드를 같이 남기는 것이 이후 해석력과 일반화를 크게 높입니다.",
                ],
                "bullets": [
                    "speed reference 또는 tachometer 연동",
                    "환경 조건과 운영 조건 메타데이터 저장",
                    "maintenance event와 데이터 타임라인 연결",
                ],
            },
            {
                "heading": "모델링 전에 체크해야 할 데이터 품질 기준",
                "paragraphs": [
                    "모델을 돌리기 전에 먼저 물어야 할 질문은 간단합니다. 같은 결함이 장비마다 비슷하게 보이는가, 정상 상태의 변동 폭을 알고 있는가, 라벨이 충분하지 않다면 anomaly scoring부터 갈 수 있는가 입니다.",
                    "특히 철도 베어링은 rare fault 문제가 강하기 때문에, 완전한 supervised classification보다 quality-controlled anomaly monitoring으로 시작하는 편이 더 빠를 수 있습니다.",
                ],
                "bullets": [
                    "센서 위치 표준화 여부",
                    "샘플링/동기화 일관성 여부",
                    "정상 baseline 확보 여부",
                    "고장 라벨과 정비 이력 연결 여부",
                ],
            },
            {
                "heading": "실제 배치에서 자주 나오는 함정",
                "paragraphs": [
                    "가장 흔한 함정은 실험실 데이터로는 잘 되던 모델이 실제 fleet에서는 흔들리는 경우입니다. 이는 대부분 센서 설치 편차, 속도 범위 차이, 장비 구조 차이 때문입니다.",
                    "그래서 railway bearing sensor 프로젝트는 처음부터 `장비 간 전이 가능성`과 `운영팀이 이해할 수 있는 경보 설명 방식`을 같이 설계해야 합니다.",
                ],
            },
        ],
        "closing": [
            "Railway bearing monitoring에서 센서는 단순 입력 장치가 아니라 진단 체계의 일부입니다. 센서 구조가 불안정하면 모델은 그 불안정을 그대로 학습할 뿐입니다.",
            "그래서 MALT 관점에서 첫 질문은 '어떤 딥러닝 모델을 쓸까'가 아니라, **'우리 센서 배치가 결함을 일관되게 읽어낼 수 있는가'** 입니다.",
        ],
    },
    "predictive-maintenance-kpi-roi-guide": {
        "title": "Predictive Maintenance KPI and ROI Guide: 예지보전 성과를 무엇으로 측정해야 하는가",
        "categories": ["maintenance", "analytics", "roi", "guide"],
        "tags": ["Predictive Maintenance", "KPI", "ROI", "Lead Time", "False Alarms", "Operations"],
        "intro": [
            "예지보전 프로젝트가 실패하는 가장 흔한 이유 중 하나는 기술이 아니라 성과 측정 방식입니다.",
            "정확도나 F1 score만 보고 시작하면, 운영팀은 '그래서 실제로 어떤 비용이 줄었는가'라는 질문에 답을 듣지 못합니다.",
            "이 글은 predictive maintenance KPI와 ROI를 어떻게 잡아야 하는지 고민하는 운영 리더와 유지보수 책임자를 위한 실무형 가이드입니다.",
        ],
        "sections": [
            {
                "heading": "왜 정확도가 핵심 사업 KPI가 아닌가",
                "paragraphs": [
                    "모델 정확도는 중요한 기술 지표이지만, 사업 지표는 아닙니다. 유지보수 조직이 실제로 궁금한 것은 경보가 얼마나 일찍 왔는지, 불필요한 작업을 줄였는지, 다운타임을 줄였는지입니다.",
                    "특히 드문 고장 환경에서는 accuracy가 높아 보여도 현장 가치는 거의 없을 수 있습니다. 정상 데이터가 대부분이기 때문입니다.",
                ],
            },
            {
                "heading": "Leading indicator와 lagging indicator를 나눠서 보라",
                "paragraphs": [
                    "예지보전 KPI는 즉시 반응 지표와 결과 지표를 분리해서 봐야 합니다. lead time, alert quality, inspection conversion은 leading indicator이고, downtime avoided, MTBF improvement, spare usage reduction은 lagging indicator에 가깝습니다.",
                    "이 구분이 없으면 프로젝트 초기에 기대치가 과도하게 커지거나, 반대로 의미 있는 초기 개선을 놓치게 됩니다.",
                ],
                "bullets": [
                    "Leading: detection lead time, alert precision, inspection conversion",
                    "Lagging: downtime reduction, maintenance cost avoidance, asset availability",
                ],
            },
            {
                "heading": "실제로 중요한 유지보수 KPI",
                "paragraphs": [
                    "현업에서는 다음 KPI들이 가장 자주 의미를 가집니다. lead time은 계획 정비 가능성을 보여주고, false alarm burden은 조직 피로도를 보여주며, work order conversion은 모델이 운영 체계에 들어왔는지를 보여줍니다.",
                    "여기에 downtime avoided와 repeat failure recurrence까지 보면, 예지보전이 단순 탐지 시스템인지 실제 운영 개선 장치인지 구분할 수 있습니다.",
                ],
                "bullets": [
                    "Detection lead time",
                    "False alarm burden",
                    "Work order conversion rate",
                    "Unplanned downtime avoided",
                    "Repeat failure recurrence",
                    "Maintenance labor efficiency",
                ],
            },
            {
                "heading": "ROI는 어떻게 계산해야 하나",
                "paragraphs": [
                    "예지보전 ROI는 단순히 장비 1건 고장을 막은 비용으로 계산하면 왜곡되기 쉽습니다. 센서, 데이터 수집, 분석 운영, 작업자 교육, false positive 대응 비용까지 함께 봐야 합니다.",
                    "초기 파일럿에서는 full ROI보다 `decision-quality improvement`와 `avoidable event reduction`을 먼저 추적하는 편이 현실적입니다. 이후 파일럿이 반복되면서 비용 모델을 더 정확히 만들 수 있습니다.",
                ],
            },
            {
                "heading": "철도와 회전체 프로그램에 맞는 scorecard 예시",
                "paragraphs": [
                    "철도나 회전체 설비에서는 자산 특성상 안전과 운영 지연 비용이 함께 걸려 있습니다. 따라서 KPI scorecard도 기술팀, 정비팀, 운영팀이 같이 읽을 수 있어야 합니다.",
                    "예를 들어 corridor별 lead time, depot별 false alarm burden, axle or bearing family별 repeat-fault rate처럼 운영 구조에 맞춘 차원을 쓰는 편이 좋습니다.",
                ],
                "bullets": [
                    "주간 경보 건수와 inspection 전환율",
                    "월간 false alarm burden과 점검 소요 시간",
                    "분기별 다운타임 회피 시간과 비용 추정",
                    "자산군별 recurrence rate",
                ],
            },
            {
                "heading": "파일럿에서 기대치를 어떻게 관리할까",
                "paragraphs": [
                    "초기 90일 동안은 ROI를 과하게 약속하지 않는 편이 좋습니다. 먼저 baseline을 만들고, 어디에서 의미 있는 조기 경고가 나오는지 확인해야 합니다.",
                    "그다음 6개월 단위에서 lead time, work order conversion, false alarm burden 추세를 보고, 그 이후에 downtime avoided를 더 본격적으로 추정하는 편이 현실적입니다.",
                ],
            },
        ],
        "closing": [
            "예지보전의 성과는 모델이 얼마나 똑똑한지보다, 조직이 그 신호를 얼마나 일관되게 행동으로 바꾸는지에서 갈립니다.",
            "그래서 MALT 관점에서 KPI의 출발점은 '정확도가 몇 퍼센트인가'가 아니라, **'이 경보가 실제로 어떤 비용과 위험을 줄였는가'** 입니다.",
        ],
    },
    "agentic-ai-industrial-maintenance-guide": {
        "title": "Agentic AI for Industrial Maintenance Guide: 산업 유지보수에 에이전트형 AI를 어디까지 붙일 수 있을까",
        "categories": ["ai", "maintenance", "agentic-ai", "guide"],
        "tags": ["Agentic AI", "Maintenance", "Workflow", "Observability", "Human in the Loop"],
        "intro": [
            "산업 유지보수에서 Agentic AI의 가치는 단순히 답변을 생성하는 데 있지 않습니다. 경보를 읽고, 관련 이력을 모으고, 보고서를 쓰고, 다음 작업 후보를 제안하는 `실행 흐름`을 자동화하는 데 있습니다.",
            "하지만 유지보수 현장은 hallucination과 승인 누락이 곧 운영 리스크로 이어질 수 있기 때문에, 일반적인 챗봇보다 더 보수적인 구조가 필요합니다.",
            "이 글은 agentic AI를 산업 유지보수 업무에 붙이고 싶은 팀이 어디까지 자동화할 수 있고, 어디서 사람 검수가 반드시 필요한지 판단하도록 돕는 가이드입니다.",
        ],
        "sections": [
            {
                "heading": "Agentic AI는 대시보드와 무엇이 다른가",
                "paragraphs": [
                    "대시보드는 정보를 보여주고, 에이전트는 그 정보를 바탕으로 다음 작업을 제안하거나 실행합니다. 예를 들어 경보를 읽고 관련 장비 이력을 검색해 요약 보고서를 만들고, 점검 티켓 초안까지 준비하는 흐름이 가능합니다.",
                    "즉 agentic AI의 핵심은 `정보 제공`이 아니라 `업무 흐름 조정`입니다. 그래서 유지보수 조직에서는 단순 알림보다 triage, 문서화, root-cause lookup 같은 영역에서 먼저 가치가 나타납니다.",
                ],
            },
            {
                "heading": "어떤 업무부터 자동화하는 편이 좋은가",
                "paragraphs": [
                    "초기에는 결정권이 큰 작업보다 반복적이고 설명 가능한 작업부터 자동화하는 편이 좋습니다. 경보 분류, 관련 문서 검색, shift handoff note 작성, inspection report 초안 정리 같은 업무가 대표적입니다.",
                    "반면 부품 교체 승인, 안전 임계치 변경, 운행 제한 판단 같은 항목은 human approval을 강하게 두어야 합니다.",
                ],
                "bullets": [
                    "초기 적합: triage, summary writing, history lookup, checklist assembly",
                    "후기 적합: scheduling suggestion, risk ranking, maintenance planning assist",
                    "사람 승인 필수: safety-critical change, dispatch commitment, replacement approval",
                ],
            },
            {
                "heading": "환각 위험이 운영 위험이 되는 지점",
                "paragraphs": [
                    "유지보수에서 agent hallucination은 단순 정보 오류가 아니라 작업 오류로 이어질 수 있습니다. 잘못된 부품 이력 요약, 존재하지 않는 점검 기준 인용, 근거 없는 우선순위 제안은 모두 운영 리스크입니다.",
                    "그래서 에이전트는 답을 길게 잘 쓰는 것보다 `어떤 출처를 보고 어떤 판단을 했는지`를 남겨야 합니다. 설명 가능성과 traceability가 정확도만큼 중요합니다.",
                ],
            },
            {
                "heading": "Observability와 승인 체크포인트",
                "paragraphs": [
                    "Agentic maintenance workflow에는 최소한 입력 스냅샷, 도구 호출 이력, 생성 결과, 승인 여부, 실패 사유가 남아야 합니다. 그래야 나중에 왜 잘못된 작업 제안이 나왔는지 역추적할 수 있습니다.",
                    "또한 승인 체크포인트는 한 번만 두는 것이 아니라, high-risk action 앞에서 여러 단계로 나누는 편이 좋습니다. 예를 들어 summary draft는 자동 허용, inspection ticket 생성은 supervisor 확인, dispatch 확정은 현장 책임자 승인 식으로 나눌 수 있습니다.",
                ],
            },
            {
                "heading": "Human-in-the-loop 패턴은 어떻게 잡아야 하나",
                "paragraphs": [
                    "유지보수 현장에서 가장 실용적인 패턴은 `AI가 초안을 만들고 사람이 승인하는 구조`입니다. 이 방식은 속도와 통제력을 동시에 가져갈 수 있습니다.",
                    "또한 리뷰 피드백을 다시 데이터로 저장하면, 이후 에이전트가 어떤 판단을 반복적으로 수정당하는지 파악할 수 있어 품질 개선 루프가 생깁니다.",
                ],
                "bullets": [
                    "AI draft -> engineer review -> supervisor approval",
                    "AI ranking -> human pick -> ticket creation",
                    "AI summary -> maintenance note archive -> later audit",
                ],
            },
            {
                "heading": "로컬 우선 배치 구조는 어떻게 생겼나",
                "paragraphs": [
                    "산업 유지보수에서는 데이터 민감도와 운영 연속성 때문에 local-first 구조가 자주 유리합니다. 센서 데이터, 정비 이력, 작업 로그는 로컬 저장소에 두고, 에이전트는 그 위에서 요약과 triage를 수행하는 구조가 현실적입니다.",
                    "이때 중요한 것은 단일 대형 에이전트보다 역할별 경량 에이전트 체계입니다. 예를 들어 ingestion agent, summarization agent, approval agent, publish agent를 나눠두면 장애 격리와 감사가 쉬워집니다.",
                ],
            },
        ],
        "closing": [
            "산업 유지보수에서 Agentic AI의 핵심은 사람을 완전히 빼는 것이 아니라, 사람이 더 적은 인지 부하로 더 좋은 판단을 하게 만드는 것입니다.",
            "그래서 MALT 관점에서 agentic maintenance의 첫 질문은 '얼마나 자동화할 수 있나'가 아니라, **'어떤 단계는 자동화하고 어떤 단계는 반드시 승인받게 할 것인가'** 입니다.",
        ],
    },
}


def slug_from_path(path: pathlib.Path) -> str:
    parts = path.stem.split("-", 3)
    return parts[3] if len(parts) >= 4 else path.stem


def extract_outline_links(text: str) -> list[str]:
    links = []
    capture = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if capture:
                break
            continue
        if line.startswith("## Existing MALT posts to link"):
            capture = True
            continue
        if capture and line.startswith("- "):
            links.append(line[2:].strip())
            continue
        if capture and line.startswith("## "):
            break
    return links


def read_title_from_post(path: pathlib.Path) -> str:
    if not path.exists():
        return path.name
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".html":
        match = re.search(r"<title>(.*?)\s+\|\s+MALT Tech Blog</title>", text, re.S | re.I)
        if match:
            return html.unescape(match.group(1).strip())
        match = re.search(r'<h1[^>]*>(.*?)</h1>', text, re.S | re.I)
        if match:
            return re.sub(r"<[^>]+>", "", html.unescape(match.group(1))).strip()
    else:
        match = re.search(r'^title:\s*"(.+?)"$', text, re.M)
        if match:
            return match.group(1).strip()
        match = re.search(r"^#\s+(.+)$", text, re.M)
        if match:
            return match.group(1).strip()
    return path.stem


def resolve_related_links(raw_links: Iterable[str]) -> list[tuple[str, str]]:
    resolved = []
    for raw_link in raw_links:
        cleaned = raw_link.strip()
        if not cleaned:
            continue
        relative = cleaned
        if cleaned.startswith("/"):
            relative = cleaned[1:]
        target = ROOT / relative
        title = read_title_from_post(target)
        href = cleaned if cleaned.startswith("/") else f"/{cleaned}"
        resolved.append((title, href))
    return resolved


def has_complete_frontmatter(text: str) -> bool:
    return text.startswith("---\n") and "workflow: \"AI-managed publication\"" in text


def render_frontmatter(title: str, date: str, slug: str, categories: list[str], tags: list[str]) -> str:
    quoted_categories = ", ".join(f'"{item}"' for item in categories)
    quoted_tags = ", ".join(f'"{item}"' for item in tags)
    return "\n".join(
        [
            "---",
            f'title: "{title}"',
            f"date: {date}",
            f'slug: "{slug}"',
            f"categories: [{quoted_categories}]",
            f"tags: [{quoted_tags}]",
            "draft: true",
            'generated_by: "MALT"',
            'workflow: "AI-managed publication"',
            "---",
            "",
        ]
    )


def render_section(section: dict) -> str:
    lines = [f"## {section['heading']}", ""]
    for paragraph in section.get("paragraphs", []):
        lines.append(paragraph)
        lines.append("")
    for bullet in section.get("bullets", []):
        lines.append(f"- {bullet}")
    if section.get("bullets"):
        lines.append("")
    return "\n".join(lines).rstrip()


def render_related_links(links: list[tuple[str, str]]) -> str:
    if not links:
        return ""
    lines = ["## MALT가 추천하는 다음 읽을거리", ""]
    for title, href in links:
        lines.append(f"- [{title}]({href})")
    lines.append("")
    return "\n".join(lines)


def render_markdown(slug: str, outline_text: str, blueprint: dict, source_path: pathlib.Path) -> str:
    date = source_path.stem[:10]
    title = blueprint["title"]
    frontmatter = render_frontmatter(title, date, slug, blueprint["categories"], blueprint["tags"])
    lines = [frontmatter, f"# {title}", ""]
    lines.extend([f"{paragraph}\n" for paragraph in blueprint["intro"]])
    for section in blueprint["sections"]:
        lines.append(render_section(section))
        lines.append("")
    links = resolve_related_links(extract_outline_links(outline_text))
    related = render_related_links(links)
    if related:
        lines.append(related.rstrip())
        lines.append("")
    lines.append("## 마무리")
    lines.append("")
    for paragraph in blueprint["closing"]:
        lines.append(paragraph)
        lines.append("")
    lines.append("## 출처")
    lines.append("")
    lines.append("- MALT 큐레이션 내부 아카이브와 관련 포스트를 바탕으로 정리")
    lines.append("- 개별 논문/사례 해석은 연결된 내부 글과 원문을 함께 검토하는 편이 좋음")
    lines.append("")
    lines.append("## 발행 메모")
    lines.append("")
    lines.append("- MALT 큐레이션 장문 가이드 초안")
    lines.append("- 맥미니 자동 편집 워크플로가 outline을 확장해 생성한 문서")
    lines.append("- 발행 전 비교표, 표준 체크리스트, CTA를 추가하면 더 강해짐")
    lines.append("")
    return "\n".join(lines).strip() + "\n"


def expand_outline(path: pathlib.Path) -> bool:
    text = path.read_text(encoding="utf-8")
    if has_complete_frontmatter(text):
        return False
    slug = slug_from_path(path)
    blueprint = GUIDE_BLUEPRINTS.get(slug)
    if not blueprint:
        return False
    path.write_text(render_markdown(slug, text, blueprint, path), encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Expand pillar post outlines into long-form draft articles.")
    parser.add_argument("--all", action="store_true", help="Expand every eligible outline draft")
    args = parser.parse_args()

    changed = 0
    for path in sorted(DRAFTS_DIR.glob("*.md")):
        if expand_outline(path):
            changed += 1
            print(path.relative_to(ROOT))
            if not args.all:
                break

    if changed == 0:
        print("no eligible outline drafts found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
