#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt
import html
import json
import os
import pathlib
import random
import re
import textwrap
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


ROOT = pathlib.Path(__file__).resolve().parent.parent
ARCHIVE_DIR = ROOT / "content" / "archive" / "sources"
UNPUBLISHED_DIR = ROOT / "content" / "archive" / "unpublished"
PUBLISHED_DIR = ROOT / "content" / "archive" / "published"
STATE_DIR = ROOT / "content" / "archive" / "state"
POSTS_DIR = ROOT / "posts"
POSTS_INDEX = ROOT / "posts.html"
HOME_INDEX = ROOT / "index.html"

ARXIV_API_URL = "https://export.arxiv.org/api/query"
SITE_BASE = "https://whdidtn200.github.io"
TOPIC_QUERIES = [
    {
        "name": "railway-phm",
        "query": 'all:"railway" AND (all:"predictive maintenance" OR all:"condition monitoring" OR all:"fault diagnosis")',
        "category": "phm",
    },
    {
        "name": "agent-ops",
        "query": 'all:"agent system" AND (all:"observability" OR all:"agentops" OR all:"anomaly detection")',
        "category": "ai",
    },
    {
        "name": "bearing-diagnosis",
        "query": 'all:"bearing fault diagnosis" AND (all:"time series" OR all:"anomaly detection" OR all:"railway")',
        "category": "phm",
    },
]
TOPIC_PRIORITY = {
    "railway-phm": 0,
    "bearing-diagnosis": 1,
    "agent-ops": 2,
}
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}
SECTION_HINTS = {
    "intro": ["introduction", "background", "motivation", "overview"],
    "method": ["method", "approach", "framework", "proposed", "model"],
    "experiment": ["experiment", "evaluation", "results", "performance"],
    "conclusion": ["conclusion", "discussion", "ablation"],
}
STOP_TERMS = {
    "introduction",
    "method",
    "methods",
    "results",
    "conclusion",
    "figure",
    "table",
    "railway",
    "predictive",
    "maintenance",
    "the",
    "this",
    "these",
    "those",
    "our",
    "their",
    "source",
}


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9가-힣\s-]", "", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-") or "malt-daily-paper"


def sentence_split(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [part.strip() for part in parts if len(part.strip()) > 20]


def summarize_abstract(text: str) -> list[str]:
    sentences = sentence_split(text)
    return sentences[:3] or [text[:220].strip()]


def contains_any(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    for keyword in keywords:
        token = keyword.lower()
        if re.search(r"[a-z]", token):
            pattern = r"\b" + re.escape(token).replace(r"\ ", r"\s+") + r"\b"
            if re.search(pattern, lowered):
                return True
        elif token in lowered:
            return True
    return False


def clean_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\[[0-9,\s]+\]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fetch_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "MALT Tech Blog Bot/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8", "ignore")


def resolve_source_urls(source: dict) -> dict[str, str]:
    arxiv_id = source.get("arxiv_id", "")
    entry_id = source.get("entry_id", "")
    abs_url = entry_id or (f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else "")
    html_url = f"https://arxiv.org/html/{arxiv_id}" if arxiv_id else ""
    pdf_url = ""
    for item in source.get("sources", []):
        if item.get("label") == "arXiv pdf":
            pdf_url = item.get("url", "")
            break
    return {"abs": abs_url, "html": html_url, "pdf": pdf_url}


def split_sentences(text: str) -> list[str]:
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+", text) if len(item.strip()) > 40]


def compress_text(text: str, max_sentences: int = 2, max_chars: int = 360) -> str:
    sentences = split_sentences(text)
    if not sentences:
        return text[:max_chars].strip()
    joined = " ".join(sentences[:max_sentences])
    return joined[:max_chars].strip()


def extract_named_terms(text: str, limit: int = 5) -> list[str]:
    matches = re.findall(r"\b(?:[A-Z]{2,}[A-Za-z0-9-]*|(?:[A-Z][a-z]+(?:[- ][A-Z][a-zA-Z0-9]+)+))\b", text)
    terms = []
    for match in matches:
        token = match.strip(" ,.;:()")
        if len(token) < 3:
            continue
        first_word = token.split()[0].lower()
        if token.lower() in STOP_TERMS or first_word in STOP_TERMS:
            continue
        if token not in terms:
            terms.append(token)
        if len(terms) >= limit:
            break
    return terms


def extract_metric_signals(text: str, limit: int = 5) -> list[str]:
    pattern = re.compile(
        r"\b(?:AP(?:\^\w+)?|mAP|F1(?:-score)?|AUC|IoU|FPS|Recall|Precision|Accuracy|Params?)\s*(?:=|:)?\s*[\d.]+%?\b",
        re.I,
    )
    metrics = []
    for match in pattern.findall(text):
        cleaned = re.sub(r"\s+", " ", match).strip()
        if cleaned not in metrics:
            metrics.append(cleaned)
        if len(metrics) >= limit:
            break
    return metrics


def extract_sections_from_html(document: str) -> dict[str, str]:
    headings = list(
        re.finditer(r'<h2[^>]*class="[^"]*ltx_title_section[^"]*"[^>]*>(.*?)</h2>', document, re.S | re.I)
    )
    sections: dict[str, str] = {}
    for index, heading in enumerate(headings):
        start = heading.end()
        end = headings[index + 1].start() if index + 1 < len(headings) else len(document)
        raw_heading = clean_text(heading.group(1)).lower()
        raw_block = document[start:end]
        paragraphs = [
            clean_text(fragment)
            for fragment in re.findall(r'<p[^>]*class="[^"]*ltx_p[^"]*"[^>]*>(.*?)</p>', raw_block, re.S | re.I)
        ]
        block_text = " ".join(item for item in paragraphs if len(item) > 40)
        if block_text:
            sections[raw_heading] = block_text
    return sections


def find_section_text(sections: dict[str, str], keys: list[str]) -> str:
    for heading, text in sections.items():
        if any(key in heading for key in keys):
            return text
    return ""


def infer_domain(source: dict) -> str:
    merged = f"{source.get('title', '')} {source.get('abstract', '')}".lower()
    if contains_any(merged, ["segmentation", "image", "vision", "camera", "inspection"]):
        return "vision"
    if contains_any(merged, ["bearing", "vibration", "signal", "time series", "spectrum"]):
        return "bearing"
    if contains_any(merged, ["agent", "observability", "runtime", "llm"]):
        return "agent"
    return "general"


def detect_focus_signals(text: str) -> list[str]:
    hints = [
        (["speed fluctuation", "variable speed", "speed variation"], "속도 변동"),
        (["few fault samples", "few-shot", "low-data", "limited samples"], "고장 샘플 부족"),
        (["cross-machine", "domain adaptation", "cross-domain", "transfer"], "설비 간 도메인 차이"),
        (["real-time", "online", "continual"], "온라인 감시"),
        (["segmentation", "mask"], "정밀 경계 추출"),
        (["wear"], "마모량 판단"),
        (["noise", "occlusion", "blur"], "노이즈와 가림"),
        (["energy", "carbon"], "운영 비용"),
    ]
    found = []
    for keys, label in hints:
        if contains_any(text, keys) and label not in found:
            found.append(label)
    return found


def build_reader_fit(domain: str, source: dict) -> list[str]:
    title = source.get("title", "").lower()
    abstract = source.get("abstract", "").lower()
    merged = f"{title} {abstract}"
    if domain == "bearing":
        return [
            "철도/회전체 설비의 상태 감시 체계를 설계하는 PHM 엔지니어",
            "진동·주파수·시간-주파수 특징을 실제 고장 진단 파이프라인에 붙여야 하는 데이터 분석가",
            "실험실 성능이 아니라 속도 변화, 부하 변화, 장비 차이까지 보고 싶은 운영 담당자",
        ]
    if domain == "vision":
        return [
            "카메라 기반 외관 점검이나 결함 세그멘테이션을 운영하려는 컴퓨터 비전 엔지니어",
            "조명 변화, 가림, 오염 같은 현장 조건에서 모델이 얼마나 버티는지 확인해야 하는 품질 팀",
            "정밀 경계 추출 결과를 교체 판단이나 유지보수 티켓으로 연결하려는 운영 담당자",
        ]
    if domain == "agent":
        return [
            "에이전트 런타임, 관찰 가능성, 자동화 실패 복구를 다루는 AI Ops 엔지니어",
            "LLM 기반 워크플로를 실제 운영 환경에 올려놓고 안정성을 관리해야 하는 팀",
            "정답률보다 실행 흐름과 도구 호출 품질을 중요하게 보는 운영 책임자",
        ]
    if "maintenance" in merged or "fault" in merged:
        return [
            "예지보전 로드맵을 만들고 있는 현장 기술 리더",
            "센서 데이터와 운영 의사결정을 연결해야 하는 분석 담당자",
            "연구 논문을 실제 점검 절차로 번역하려는 엔지니어",
        ]
    return [
        "최신 연구를 현장 운영 문제로 번역해서 읽고 싶은 엔지니어",
        "논문 요약보다 적용 조건과 한계를 먼저 확인하고 싶은 실무자",
        "AI 자동화 시스템이 어떤 기준으로 기술 콘텐츠를 고르는지 궁금한 독자",
    ]


def build_operational_takeaways(domain: str, source: dict) -> list[str]:
    focus_signals = detect_focus_signals(f"{source.get('title', '')} {source.get('abstract', '')}".lower())
    focus_text = ", ".join(focus_signals[:2]) if focus_signals else "운영 제약"
    common = [
        "논문 수치만 보지 말고, 우리 데이터 조건과 입력 품질이 논문 조건과 얼마나 다른지 먼저 비교한다.",
        "모델 도입 전에 경보 이후의 사람 작업 흐름까지 같이 설계해야 실제 운영 가치가 생긴다.",
    ]
    if domain == "bearing":
        return [
            "센서 배치, 샘플링 주기, 회전 속도 정보가 우리 설비에서 얼마나 안정적으로 확보되는지 먼저 확인한다.",
            f"특히 {focus_text} 조건에서 성능이 유지되는지 별도 검증용 데이터셋을 따로 잡아두는 편이 좋다.",
            "파일럿 단계에서는 조기 경보의 민감도보다 오탐 이후 작업 부담이 얼마나 생기는지도 같이 측정한다.",
            *common,
        ]
    if domain == "vision":
        return [
            "카메라 위치, 조명, 오염 상태가 현장마다 얼마나 다른지부터 점검하고 테스트 이미지를 따로 모아둔다.",
            f"특히 {focus_text}가 심한 장면에서 경계가 무너지는지 먼저 보는 편이 실무적이다.",
            "결함 검출 결과를 바로 교체 판단으로 쓰지 말고, 작업자 검수 단계와 연결하는 것이 안전하다.",
            *common,
        ]
    if domain == "agent":
        return [
            "도구 호출 실패, 단계 누락, 재시도 정책 같은 운영 로그를 먼저 남길 수 있어야 논문 아이디어를 살릴 수 있다.",
            f"특히 {focus_text} 상황에서 에이전트가 어떤 방식으로 무너지는지 실패 분류 체계를 같이 둔다.",
            "정답률보다도 실패를 얼마나 빨리 발견하고 롤백할 수 있는지가 운영 품질에 더 중요하다.",
            *common,
        ]
    return [
        f"이 논문은 {focus_text}를 다룰 때 어떤 데이터와 절차가 필요한지 역으로 정리해 보는 식으로 읽는 편이 좋다.",
        "바로 도입하기보다 현재 운영 절차에서 어디에 붙일 수 있는지 체크리스트를 먼저 만든다.",
        *common,
    ]


def build_taxonomy_tags(domain: str, source: dict) -> list[str]:
    base = ["arXiv", "MALT", "PHM", "Fault Diagnosis"]
    merged = f"{source.get('title', '')} {source.get('abstract', '')}".lower()
    if domain == "bearing":
        base.extend(["Bearing", "Sensors"])
    elif domain == "vision":
        base.extend(["Railway", "Computer Vision"])
    elif domain == "agent":
        base.extend(["Agentic AI", "Observability"])
    else:
        base.extend(["Railway", "Condition Monitoring"])

    if contains_any(merged, ["railway", "train", "wheelset", "wayside", "freight"]):
        base.append("Railway")
    if contains_any(merged, ["condition monitoring", "predictive maintenance", "maintenance"]):
        base.append("Condition Monitoring")
    if contains_any(merged, ["sensor", "vibration", "signal", "acoustic", "ae"]):
        base.append("Sensors")

    tags: list[str] = []
    for item in base:
        if item not in tags:
            tags.append(item)
    return tags[:8]


def fetch_paper_context(source: dict) -> dict:
    if source.get("paper_context"):
        return source["paper_context"]
    urls = resolve_source_urls(source)
    sections: dict[str, str] = {}
    abs_text = ""
    html_error = ""
    if urls["html"]:
        try:
            document = fetch_text(urls["html"])
            sections = extract_sections_from_html(document)
        except Exception as exc:
            html_error = str(exc)
    if urls["abs"]:
        try:
            abs_page = fetch_text(urls["abs"])
            match = re.search(r'<blockquote class="abstract[^"]*">\s*<span[^>]*>Abstract:</span>(.*?)</blockquote>', abs_page, re.S | re.I)
            if match:
                abs_text = clean_text(match.group(1))
        except Exception:
            abs_text = source.get("abstract", "")
    context = {
        "urls": urls,
        "sections": sections,
        "intro": find_section_text(sections, SECTION_HINTS["intro"]),
        "method": find_section_text(sections, SECTION_HINTS["method"]),
        "experiment": find_section_text(sections, SECTION_HINTS["experiment"]),
        "conclusion": find_section_text(sections, SECTION_HINTS["conclusion"]),
        "abstract": abs_text or source.get("abstract", ""),
        "html_error": html_error,
    }
    source["paper_context"] = context
    return context


def build_detailed_analysis(source: dict) -> dict:
    if source.get("analysis"):
        return source["analysis"]
    context = fetch_paper_context(source)
    domain = infer_domain(source)
    abstract = context.get("abstract") or source.get("abstract", "")
    intro = context.get("intro", "")
    method = context.get("method", "")
    experiment = context.get("experiment", "")
    conclusion = context.get("conclusion", "")
    merged = " ".join([source.get("title", ""), abstract, intro, method, experiment, conclusion])
    method_terms = extract_named_terms(f"{source.get('title', '')} {method} {abstract}")
    metric_signals = extract_metric_signals(f"{experiment} {abstract}")
    focus_signals = detect_focus_signals(merged.lower())
    focus_text = ", ".join(focus_signals[:3]) if focus_signals else "현장 적용 조건"

    if domain == "vision":
        one_line = (
            "이 논문은 카메라 점검 이미지에서 결함 부위를 더 정확히 잘라내고, 그 결과를 실제 철도 점검 흐름에 붙이려는 시도다."
        )
        problem = (
            "핵심 문제는 `어디에 이상이 있는지 찾는 것`에서 끝나지 않고, 경계를 얼마나 정확히 잡아 교체 판단까지 연결하느냐다. "
            "철도 점검 이미지는 오염, 그림자, 가림, 촬영 각도 변화가 많아서 일반 비전 모델이 쉽게 흔들린다."
        )
        why_now = (
            f"이번 글에서 볼 포인트는 성능 수치 하나보다 `{focus_text}` 같은 실전 조건을 어떻게 다뤘는가다. "
            "철도 외관 점검은 현장마다 배경과 조명이 달라서, 일반 비전 모델을 그대로 가져다 쓰면 금방 흔들린다."
        )
        method_overview = (
            f"본문에서 눈에 띄는 구성은 {', '.join(method_terms[:4]) or '도메인 맞춤 모듈 조합'} 쪽이다. "
            "쉽게 말하면 큰 범용 모델을 그대로 쓰지 않고, 철도 이미지에서 필요한 힌트를 자동으로 만들거나 경계를 더 또렷하게 잡는 방향으로 재설계한 흐름이다."
        )
        experiment_read = (
            "실험은 단순 정확도 비교보다, 가림이나 노이즈가 있을 때도 경계가 얼마나 덜 무너지는지, 그리고 실제 점검에서 필요한 마모·부품 구분 수준까지 도달하는지를 보는 식으로 읽는 편이 맞다."
        )
    elif domain == "bearing":
        one_line = (
            "이 논문은 베어링이나 회전체 신호에서 미세한 이상 징후를 더 안정적으로 분리해, 조기 고장 진단에 쓰려는 접근이다."
        )
        problem = (
            "핵심 문제는 정상과 이상 신호가 서로 섞여 있고, 속도 변화나 부하 변화 때문에 같은 고장도 다르게 보인다는 점이다. "
            "그래서 논문은 `신호를 더 잘 펼쳐 보고`, `다른 환경에서도 덜 무너지게` 만드는 방향을 택한다."
        )
        why_now = (
            f"이번 글에서 중요한 건 베어링 진단에서 늘 어려웠던 `{focus_text}`를 한 번에 다루려 했다는 점이다. "
            "철도 wheelset 쪽 논문은 실험실 데이터에서는 좋아 보여도, 속도와 부하가 달라지면 성능이 크게 흔들리는 경우가 많다."
        )
        method_overview = (
            f"본문에서 눈에 띄는 구성은 {', '.join(method_terms[:4]) or '스펙트럼 기반 특징 추출과 전이 학습'} 쪽이다. "
            "쉽게 말하면 신호를 시간축 그대로 보지 않고 주파수나 시간-주파수 표현으로 다시 펼친 뒤, 장비가 바뀌어도 특징이 덜 무너지도록 학습시키는 흐름이다."
        )
        experiment_read = (
            "실험은 한 장비나 한 속도 조건에서 배운 모델이 다른 조건으로 넘어갔을 때도 버티는지를 보는 데 초점이 있다. "
            "그래서 최고 정확도 숫자 하나보다 `다른 조건에서도 유지되는가`를 먼저 읽는 편이 실무에 더 가깝다."
        )
    elif domain == "agent":
        one_line = (
            "이 논문은 에이전트 시스템이 실제 운영 중 어떤 실패 징후를 보이는지 읽고, 관찰과 제어 루프를 더 안정적으로 만들려는 시도다."
        )
        problem = (
            "LLM 에이전트는 데모에서는 잘 보여도 운영 환경에서는 단계 누락, 장기 의존성, 도구 호출 실패처럼 보이지 않는 문제가 많다. "
            "이 논문은 그런 운영형 실패를 어떻게 관찰하고 분류할지에 초점을 둔다."
        )
        why_now = (
            f"이번 글에서 볼 포인트는 `{focus_text}` 같은 운영 이슈를 얼마나 구조적으로 다루는가다. "
            "에이전트 시스템은 답변 품질뿐 아니라, 실행 흐름이 언제 어떻게 무너지는지를 같이 봐야 실제 운영 가치가 생긴다."
        )
        method_overview = (
            f"본문에서 눈에 띄는 구성은 {', '.join(method_terms[:4]) or '런타임 계측과 분류 규칙'} 쪽이다. "
            "쉽게 말하면 에이전트의 행동 로그를 더 잘 관찰하고, 실패 패턴을 운영 가능한 단위로 나눠 보려는 접근으로 읽힌다."
        )
        experiment_read = (
            "실험은 정답률만 보는 것이 아니라, 실패 탐지 속도나 잘못된 행동을 얼마나 빨리 포착하는지까지 같이 보는 식으로 읽는 편이 맞다."
        )
    else:
        one_line = "이 논문은 최신 모델 소개보다, 실제 운영 문제에 어떤 방식으로 연결될 수 있는지를 보여주는 연구다."
        problem = (
            "핵심은 성능 수치를 하나 더 올리는 것이 아니라, 현장에서 흔들리는 입력과 운영 제약 속에서도 의미 있는 판단을 낼 수 있느냐다."
        )
        why_now = (
            f"이번 글에서 볼 포인트는 `{focus_text}` 같은 실전 조건을 논문이 어떻게 다뤘는가다. "
            "즉, 연구 아이디어를 운영 문제로 번역할 수 있는지가 핵심이다."
        )
        method_overview = (
            f"본문에서 눈에 띄는 구성은 {', '.join(method_terms[:4]) or '도메인 맞춤 전처리와 모델 결합'} 쪽이다. "
            "쉽게 말하면 입력을 더 잘 정리하고, 운영 환경에서 덜 흔들리는 표현을 만들려는 접근에 가깝다."
        )
        experiment_read = (
            "실험 파트는 최고 성능보다도 입력 조건이 바뀔 때 결과가 얼마나 유지되는지, 그리고 실제 운영 의사결정으로 이어질 만한 출력을 내는지에 초점을 맞춰 읽는 편이 낫다."
        )

    method_steps = [
        "먼저 문제를 현장 단위로 다시 정의한다. 즉, 단순 분류가 아니라 실제 점검이나 유지보수 판단에 필요한 출력 형태를 만든다.",
        f"그다음 모델 쪽에서는 {', '.join(method_terms[:3]) or '핵심 모듈'} 같은 요소를 묶어 성능과 배치 가능성의 균형을 맞춘다.",
        "마지막으로 결과를 바로 숫자 자랑으로 끝내지 않고, 잡음·환경 변화·실시간 처리 같은 운영 조건에서 버티는지 확인하려 한다.",
    ]
    experiment_points = [
        "논문이 제시한 비교는 단일 정확도보다, 기존 방식 대비 어디서 덜 무너지는지를 보는 게 중요하다.",
        f"본문과 초록에서 바로 읽히는 수치 신호는 {', '.join(metric_signals) if metric_signals else '정확도, 처리 속도, 모델 크기'} 쪽이다.",
        "실무적으로는 최고 점수보다도 데이터 조건이 달라져도 결과가 유지되는지, 그리고 경보 이후 작업 흐름에 연결되는지가 더 중요하다.",
    ]
    interpretation = (
        "내가 이 논문을 발행 가치가 있다고 보는 이유는, `좋은 모델 하나`보다 `운영에 붙일 수 있는 구조`를 보여주기 때문이다. "
        "블로그 관점에서는 이 논문을 읽고 나면 어떤 센서나 이미지가 들어오고, 어떤 판단 출력으로 이어져야 하는지 머릿속에 그릴 수 있어야 한다."
    )
    if domain == "bearing":
        field_reality = (
            "베어링 진단 논문은 실험실에서는 좋아 보여도 실제 운영에 붙이면 신호 품질, 회전 속도 변동, 장비 차이, 라벨 부족 때문에 성능이 빠르게 흔들릴 수 있습니다. "
            "그래서 이 글은 모델 이름보다도 어떤 조건에서 성능이 유지되는지, 그리고 경보가 정비 의사결정으로 자연스럽게 이어질 수 있는지를 중심으로 읽는 편이 좋습니다."
        )
        evaluation_questions = [
            "실험 데이터의 속도·부하 조건이 실제 노선이나 설비 조건과 얼마나 비슷한가",
            "학습한 특징이 다른 장비나 다른 계절 조건으로 넘어가도 유지되는가",
            "경보 결과를 사람이 재검수하거나 정비 우선순위로 연결할 절차가 있는가",
        ]
    elif domain == "vision":
        field_reality = (
            "철도 비전 논문은 데모 화면만 보면 좋아 보이지만, 실제 현장에서는 조명 변화, 오염, 가림, 촬영 각도 차이 때문에 경계 품질이 크게 흔들릴 수 있습니다. "
            "결국 중요한 것은 한 장의 예쁜 결과 이미지가 아니라, 다양한 현장 조건에서도 검출 결과를 유지하고 작업자 검수 흐름과 자연스럽게 연결할 수 있는가입니다."
        )
        evaluation_questions = [
            "야간, 우천, 오염, 역광 조건에서도 같은 수준의 경계 품질을 유지하는가",
            "오탐과 미탐이 실제 교체 판단이나 재점검 비용에 어떤 영향을 주는가",
            "검출 결과를 작업자 검수 단계와 함께 설계했는가",
        ]
    elif domain == "agent":
        field_reality = (
            "에이전트 논문은 답변 품질만 보면 안정적으로 보여도, 운영 환경에서는 도구 호출 실패, 단계 누락, 장기 상태 관리 실패가 더 큰 문제로 드러나는 경우가 많습니다. "
            "그래서 실제 가치는 모델 이름보다도 실패를 얼마나 빨리 관찰하고 통제 가능한 흐름으로 바꾸는지에서 갈립니다."
        )
        evaluation_questions = [
            "실패 유형을 로그와 메트릭으로 분리해서 관찰할 수 있는가",
            "재시도와 롤백 규칙이 결과 품질보다 먼저 설계되어 있는가",
            "운영 중 변하는 입력 환경에서도 실행 흐름이 무너지지 않는가",
        ]
    else:
        field_reality = (
            "이런 유형의 논문은 성능 수치 자체보다, 입력 조건이 바뀌었을 때도 판단 품질이 유지되는지와 실제 운영 절차에 붙일 수 있는지가 더 중요합니다. "
            "블로그 글로 읽을 때도 요약보다 적용 조건과 검증 질문을 먼저 붙여 보는 편이 더 실전적입니다."
        )
        evaluation_questions = [
            "논문 조건과 우리 운영 데이터 사이의 차이를 먼저 설명할 수 있는가",
            "결과를 실제 사람 작업 흐름이나 운영 의사결정과 연결할 수 있는가",
            "최고 정확도보다 재현성과 유지 가능성을 검증했는가",
        ]
    limitations = [
        "본문이 제시하는 실험 조건이 다른 노선, 다른 장비, 다른 계절에도 그대로 유지되는지는 추가 검증이 필요하다.",
        "실제 유지보수에서는 오탐 비용과 미탐 위험을 함께 봐야 하므로, 논문 성능 수치만으로 바로 운영 정책을 정하긴 어렵다.",
        "현장 배포 단계에서는 모델 자체보다 데이터 수집, 라벨 품질, 검수 프로세스가 병목이 될 가능성이 크다.",
    ]
    closing = (
        "쉽게 말해 이 논문은 `이론적으로 좋아 보이는 방법`을 넘어서, 현장에 붙일 때 무엇을 더 챙겨야 하는지 생각하게 만드는 타입이다. "
        "그래서 하루치 자동 발행 글이어도, 단순 초록 번역보다 운영 해석을 중심으로 읽는 편이 맞다."
    )
    reader_fit = build_reader_fit(domain, source)
    operational_takeaways = build_operational_takeaways(domain, source)
    analysis = {
        "one_line": one_line,
        "why_now": why_now,
        "problem": problem,
        "method_overview": method_overview,
        "method_steps": method_steps,
        "experiment_read": experiment_read,
        "experiment_points": experiment_points,
        "interpretation": interpretation,
        "field_reality": field_reality,
        "evaluation_questions": evaluation_questions,
        "limitations": limitations,
        "closing": closing,
        "reader_fit": reader_fit,
        "operational_takeaways": operational_takeaways,
    }
    source["analysis"] = analysis
    return analysis


def build_review(source: dict) -> dict:
    title = source.get("title", "")
    abstract = source.get("abstract", "")
    topic = source.get("topic", "")
    merged = f"{title} {abstract}".lower()

    if contains_any(merged, ["railway", "track", "wayside", "wheel", "bearing", "train"]):
        why_selected = (
            "이 논문은 철도 설비, 센서, 고장 진단 같은 블로그 핵심 축과 직접 연결된다. "
            "그래서 단순히 최신 논문이라서가 아니라, 지금 블로그 독자에게 바로 설명할 이유가 있는 후보로 봤다."
        )
    elif contains_any(merged, ["agent", "observability", "runtime", "anomaly"]):
        why_selected = (
            "이 논문은 운영 자동화와 관찰가능성 관점에서는 흥미롭다. "
            "다만 철도 PHM과의 직접 연결은 약해서, 발행하더라도 내가 연결 해석을 붙여야 가치가 생기는 타입으로 판단했다."
        )
    else:
        why_selected = (
            "주제는 블로그 범위 안에 있지만, 제목만으로 현장 가치가 즉시 드러나는 논문은 아니다. "
            "그래서 발행 여부는 내가 실무 연결고리를 얼마나 분명하게 설명할 수 있는지에 달려 있다고 봤다."
        )

    if contains_any(merged, ["continual", "online", "stream", "real-time"]):
        interpretation = (
            "내가 이 논문에서 중요하게 보는 건 알고리즘 이름보다도 `운영 중 변하는 데이터에 버틸 수 있는가`다. "
            "철도처럼 계절, 속도, 하중, 노선 상태가 흔들리는 환경에서는 오프라인 정확도보다 온라인 적응력이 더 실질적인 경쟁력이다."
        )
    elif contains_any(merged, ["deep neural", "transformer", "foundation model", "network"]):
        interpretation = (
            "이 논문은 성능 숫자보다 배치 위치를 봐야 한다. "
            "어떤 센서를 받아 어떤 경보나 유지보수 판단으로 이어지는지 설명할 수 있을 때 비로소 블로그 글로서 의미가 생긴다."
        )
    else:
        interpretation = (
            "이 논문은 개별 기술의 새로움보다도 시스템 안에 어떻게 연결되는지가 더 중요해 보인다. "
            "그래서 발행할 때는 결과 요약보다 운영 맥락 해석을 앞에 두는 편이 맞다."
        )

    if contains_any(merged, ["predictive maintenance", "fault", "failure", "diagnostics", "condition monitoring"]):
        applicability = (
            "실무 적용 장면도 비교적 선명하다. "
            "정비 시점 판단, 이상 징후 조기 탐지, 센서 이벤트 해석 같은 흐름으로 바로 이어 설명할 수 있다."
        )
    else:
        applicability = (
            "당장 현장에 꽂히는 타입은 아니고, 기존 글과 묶어서 해석형 포스트로 재구성할 때 더 힘을 받을 논문으로 본다."
        )

    if contains_any(merged, ["survey", "review", "benchmark", "taxonomy"]):
        caution = (
            "이런 류의 논문은 정리와 분류의 가치가 크지만, 그대로 발행하면 요약문처럼 보이기 쉽다. "
            "그래서 반드시 내가 왜 이 분류가 중요한지 해석을 덧붙여야 한다."
        )
    else:
        caution = (
            "초록만으로는 데이터셋 조건, 운영 제약, 오탐 비용 같은 실전 요소가 충분히 드러나지 않는다. "
            "그래서 발행할 때는 어디까지 믿고 적용할 수 있는지 한계를 같이 말해야 한다."
        )

    verdict = (
        "내 판단으로는 이 논문은 보관만 할 후보가 아니라, 해석을 붙여 발행할 만한 가치가 있다."
        if topic in {"railway-phm", "bearing-diagnosis"} or contains_any(merged, ["railway", "bearing", "track", "train"])
        else "내 판단으로는 일단 archive에는 남겨둘 가치가 있지만, 지금 바로 발행하기보다는 연결 해석이 더 생길 때 쓰는 편이 낫다."
    )

    return {
        "why_selected": why_selected,
        "interpretation": interpretation,
        "applicability": applicability,
        "caution": caution,
        "verdict": verdict,
    }


def enrich_source(source: dict) -> dict:
    enriched = dict(source)
    if not enriched.get("review"):
        enriched["review"] = build_review(enriched)
    return enriched


def fetch_feed(search_query: str, max_results: int = 6) -> ET.Element:
    params = urllib.parse.urlencode(
        {
            "search_query": search_query,
            "start": 0,
            "max_results": max_results,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
        }
    )
    with urllib.request.urlopen(f"{ARXIV_API_URL}?{params}", timeout=30) as response:
        payload = response.read()
    return ET.fromstring(payload)


def existing_source_keys() -> set[str]:
    keys = set()
    for base_dir in (ARCHIVE_DIR, UNPUBLISHED_DIR, PUBLISHED_DIR):
        for path in base_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            for key in ("arxiv_id", "entry_id", "source_url"):
                value = data.get(key)
                if value:
                    keys.add(str(value))
    return keys


def load_json(path: pathlib.Path) -> dict:
    return enrich_source(json.loads(path.read_text(encoding="utf-8")))


def ensure_archive_dirs() -> None:
    for path in (ARCHIVE_DIR, UNPUBLISHED_DIR, PUBLISHED_DIR, STATE_DIR):
        path.mkdir(parents=True, exist_ok=True)


def write_state_snapshot(candidates: list[dict]) -> None:
    snapshot = {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "queued_count": len(candidates),
        "queued_titles": [
            {
                "title": item.get("title"),
                "topic": item.get("topic"),
                "date": item.get("date"),
                "slug": item.get("slug"),
                "review_verdict": item.get("review", {}).get("verdict"),
            }
            for item in candidates[:50]
        ],
    }
    (STATE_DIR / "queue_snapshot.json").write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def sync_unpublished_pool() -> None:
    ensure_archive_dirs()
    published_keys = set()
    for path in PUBLISHED_DIR.glob("*.json"):
        try:
            data = load_json(path)
        except json.JSONDecodeError:
            continue
        for key in ("entry_id", "arxiv_id"):
            if data.get(key):
                published_keys.add(str(data[key]))

    for path in ARCHIVE_DIR.glob("*.json"):
        data = load_json(path)
        unique_key = str(data.get("entry_id") or data.get("arxiv_id") or "")
        target_path = UNPUBLISHED_DIR / path.name
        if data.get("source_type") != "arxiv-api":
            continue
        if unique_key and unique_key in published_keys:
            if target_path.exists():
                target_path.unlink()
            continue
        target_path.write_text(json.dumps(enrich_source(data), ensure_ascii=False, indent=2), encoding="utf-8")


def published_slugs() -> set[str]:
    return {path.stem for path in POSTS_DIR.glob("*.html")}


def thematic_score(item: dict) -> int:
    haystack = f"{item.get('title', '')} {item.get('abstract', '')}".lower()
    score = 0
    keyword_weights = {
        "railway": 5,
        "train": 4,
        "bearing": 4,
        "fault": 4,
        "predictive maintenance": 5,
        "condition monitoring": 5,
        "phm": 5,
        "wayside": 3,
        "freight": 2,
        "agent": 2,
        "agentic system": 3,
        "coding agent": 4,
        "tool calling": 4,
        "multi-agent": 3,
        "evaluator": 2,
        "trust": 2,
        "observability": 2,
        "anomaly": 3,
        "6g": -3,
        "office proficiency": -5,
        "healthcare": -4,
        "navigation": -3,
    }
    for keyword, weight in keyword_weights.items():
        if contains_any(haystack, [keyword]):
            score += weight
    return score


def is_publishable_candidate(item: dict) -> bool:
    haystack = f"{item.get('title', '')} {item.get('abstract', '')}".lower()
    required = [
        "railway",
        "train",
        "freight",
        "wheelset",
        "wayside",
        "bearing",
        "rolling bearing",
        "fault diagnosis",
        "condition monitoring",
        "predictive maintenance",
    ]
    blocked = [
        "6g",
        "iot network",
        "office proficiency",
        "guardrails",
        "carbon emissions",
        "healthcare",
        "medical",
        "robotnav",
        "navigation",
        "geo-intelligence",
        "disaster",
    ]
    agent_required = [
        "agentic system",
        "coding agent",
        "coding agents",
        "tool calling",
        "multi-agent llm",
        "multi-agent systems",
        "evaluator bias",
        "agent trust",
        "emergent misalignment",
        "agent observability",
    ]
    if contains_any(haystack, blocked):
        return False
    if item.get("topic") == "agent-ops" and os.environ.get("MALT_ALLOW_AGENT_OPS") != "1":
        return False
    if item.get("topic") == "agent-ops":
        return contains_any(haystack, agent_required)
    return contains_any(haystack, required)


def extract_entry(entry: ET.Element, topic: dict) -> dict:
    title = (entry.findtext("atom:title", default="", namespaces=NS) or "").strip()
    summary = (entry.findtext("atom:summary", default="", namespaces=NS) or "").strip()
    entry_id = (entry.findtext("atom:id", default="", namespaces=NS) or "").strip()
    published = (entry.findtext("atom:published", default="", namespaces=NS) or "").strip()
    authors = [
        (author.findtext("atom:name", default="", namespaces=NS) or "").strip()
        for author in entry.findall("atom:author", NS)
    ]
    primary_category = entry.find("arxiv:primary_category", NS)
    categories = [topic["category"]]
    if primary_category is not None:
        categories.append(primary_category.attrib.get("term", "arxiv"))
    links = []
    for link in entry.findall("atom:link", NS):
        href = link.attrib.get("href")
        if href:
            links.append({"label": link.attrib.get("title", link.attrib.get("rel", "link")), "url": href})
    pdf_url = ""
    for link in links:
        if "pdf" in link["url"]:
            pdf_url = link["url"]
            break

    date = published[:10] if published else dt.date.today().isoformat()
    arxiv_id = entry_id.rsplit("/", 1)[-1] if entry_id else slugify(title)
    slug = slugify(f"{arxiv_id}-{title}")[:72].strip("-")

    payload = {
        "date": date,
        "slug": slug,
        "title": title,
        "source_type": "arxiv-api",
        "topic": topic["name"],
        "categories": categories[:3],
        "tags": ["arXiv", "MALT", topic["name"]],
        "summary": summarize_abstract(summary),
        "key_points": summarize_abstract(summary)[1:] or summarize_abstract(summary),
        "operator_view": [
            "MALT는 논문 초록을 그대로 복제하지 않고, 철도 PHM과 운영 자동화 관점에서 다시 읽는다.",
            "예약 발행 체계에서는 최신성보다 실제 적용 가능성이 높은 논문을 우선한다.",
        ],
        "application_notes": [
            "현장 적용 시 어떤 센서, 운영 루프, 검증 절차와 연결할 수 있는지를 먼저 본다.",
            "기존 블로그의 PHM, Observability, Agentic AI 글과 연결될 수 있는 논문만 발행 후보로 삼는다.",
        ],
        "limitations": [
            "초록 기반 초안이라 세부 실험 설정과 한계는 발행 전 보강이 필요하다.",
            "실제 배포 전에는 본문 원문과 도표를 다시 확인하는 절차가 권장된다.",
        ],
        "sources": [{"label": "arXiv abs", "url": entry_id}] + ([{"label": "arXiv pdf", "url": pdf_url}] if pdf_url else []),
        "authors": authors,
        "abstract": summary,
        "entry_id": entry_id,
        "arxiv_id": arxiv_id,
        "published_at": published,
    }
    payload["review"] = build_review(payload)
    return payload


def store_new_sources() -> list[pathlib.Path]:
    ensure_archive_dirs()
    known = existing_source_keys()
    created = []
    for topic in TOPIC_QUERIES:
        feed = fetch_feed(topic["query"])
        for entry in feed.findall("atom:entry", NS):
            payload = extract_entry(entry, topic)
            unique_key = payload["entry_id"] or payload["arxiv_id"]
            if unique_key in known:
                continue
            out_path = ARCHIVE_DIR / f"{payload['date']}-{payload['slug']}.json"
            out_path.write_text(json.dumps(enrich_source(payload), ensure_ascii=False, indent=2), encoding="utf-8")
            known.add(unique_key)
            created.append(out_path)
    sync_unpublished_pool()
    return created


def load_candidate_sources() -> list[dict]:
    items = []
    published = published_slugs()
    for path in sorted(UNPUBLISHED_DIR.glob("*.json"), reverse=True):
        data = load_json(path)
        if data.get("slug") in published:
            continue
        if data.get("source_type") != "arxiv-api":
            continue
        items.append(data)
    return items


def choose_candidate() -> dict | None:
    candidates = [item for item in load_candidate_sources() if is_publishable_candidate(item)]
    if not candidates:
        return None
    candidates.sort(
        key=lambda item: (
            -thematic_score(item),
            TOPIC_PRIORITY.get(item.get("topic", "agent-ops"), 9),
            -(int(item.get("date", "1970-01-01").replace("-", ""))),
        )
    )
    return candidates[0]


def build_post_title(source: dict) -> str:
    return f"[arXiv Daily] {source['title']}"


def get_publish_date(source: dict) -> str:
    return source.get("publish_date") or dt.date.today().isoformat()


def post_basename(source: dict) -> str:
    slug = source["slug"]
    source_date = source.get("source_date") or source.get("date", "")
    date_prefix = f"{source_date}-" if source_date else ""
    if slug.startswith(date_prefix):
        slug = slug[len(date_prefix):]
    return f"{get_publish_date(source)}-{slug}"


def build_description(source: dict) -> str:
    analysis = build_detailed_analysis(source)
    return analysis.get("one_line", "")[:150]


def render_markdown(source: dict) -> str:
    title = build_post_title(source)
    publish_date = get_publish_date(source)
    source_date = source.get("source_date") or source.get("date", "")
    analysis = build_detailed_analysis(source)
    domain = infer_domain(source)
    context = fetch_paper_context(source)
    links = list(source.get("sources", []))
    if context.get("urls", {}).get("html"):
        links.append({"label": "arXiv html", "url": context["urls"]["html"]})
    source_links = "\n".join(f"- [{item['label']}]({item['url']})" for item in links)
    authors = ", ".join(source.get("authors", [])) or "Unknown authors"
    review = source.get("review", {})
    taxonomy_tags = build_taxonomy_tags(domain, source)
    tag_yaml = "\n".join(f"  - {item}" for item in taxonomy_tags)
    method_steps = "\n".join(f"- {item}" for item in analysis.get("method_steps", []))
    experiment_points = "\n".join(f"- {item}" for item in analysis.get("experiment_points", []))
    evaluation_questions = "\n".join(f"- {item}" for item in analysis.get("evaluation_questions", []))
    limitations = "\n".join(f"- {item}" for item in analysis.get("limitations", []))
    reader_fit = "\n".join(f"- {item}" for item in analysis.get("reader_fit", []))
    operational_takeaways = "\n".join(f"- {item}" for item in analysis.get("operational_takeaways", []))
    summary_line = analysis.get("one_line", "").replace('"', "'")

    return f"""---
title: "{title.replace('"', "'")}"
date: {publish_date} 09:17:00 +0900
tags:
{tag_yaml}
categories:
  - Daily arXiv
  - PHM
summary: "{summary_line}"
---

# {title}

**발행일**: {publish_date}  
**논문 공개일**: {source_date}  
**원문 논문**: {source['title']}  
**저자**: {authors}

## 한 줄 요약

{analysis.get("one_line", "")}

## 왜 지금 볼 만한가

{analysis.get("why_now", "")}

## 이 논문이 풀려는 문제를 쉽게 말하면

{analysis.get("problem", "")}

## 논문이 제안한 방법

{analysis.get("method_overview", "")}

{method_steps}

## 실험 결과를 어떻게 읽어야 하나

{analysis.get("experiment_read", "")}

{experiment_points}

## 현장에서는 왜 더 어려운가

{analysis.get("field_reality", "")}

## 누가 읽으면 특히 좋은가

{reader_fit}

## MALT 리뷰

### 왜 골랐는가
{review.get("why_selected", "")}

### 어떻게 읽어야 하는가
{review.get("interpretation", "")}

### 어디에 써먹을 수 있는가
{review.get("applicability", "")}

### 어떤 점을 조심해야 하는가
{review.get("caution", "")}

### 발행 판단
{review.get("verdict", "")}

## MALT 해석

{analysis.get("interpretation", "")}

## 도입 전에 확인할 질문
{evaluation_questions}

## 현업 적용 체크리스트
{operational_takeaways}

## 한계와 체크 포인트
{limitations}

## 쉽게 결론만 말하면

{analysis.get("closing", "")}

## 출처
{source_links}

## 발행 메모
- MALT daily arXiv pipeline이 생성한 자동 발행본
- MALT 큐레이션과 AI-managed editorial workflow를 거친 발행본
- 발행 전 원문 초록과 arXiv HTML 본문을 다시 확인함
- 자동 발행은 예약형으로 운영되지만, 글 구조는 `문제 -> 방법 -> 실험 -> 해석 -> 한계` 순서로 유지함
"""


def paragraphize(items: list[str]) -> str:
    return "\n".join(f"<li>{html.escape(item)}</li>" for item in items)


def render_tag_links(source: dict) -> str:
    tags = []
    for item in list(source.get("tags", [])) + list(source.get("categories", [])):
        label = str(item).strip()
        if not label:
            continue
        if re.search(r"[가-힣]", label):
            display = label
        elif label.isupper():
            display = label
        else:
            display = " ".join(part.title() for part in re.split(r"[-_\s]+", label) if part)
        if display not in tags:
            tags.append(display)
    links = []
    for tag in tags[:8]:
        slug = slugify(tag)
        links.append(f'<a class="tag-chip" href="/tags/{slug}.html">{html.escape(tag)}</a>')
    return "".join(links)


def render_html(source: dict) -> str:
    title = build_post_title(source)
    description = html.escape(build_description(source))
    publish_date = get_publish_date(source)
    published_iso = f"{publish_date}T09:17:00+09:00"
    basename = post_basename(source)
    canonical = f"{SITE_BASE}/posts/{basename}.html"
    authors = html.escape(", ".join(source.get("authors", [])) or "Unknown authors")
    review = source.get("review", {})
    analysis = build_detailed_analysis(source)
    domain = infer_domain(source)
    context = fetch_paper_context(source)
    links = list(source.get("sources", []))
    if context.get("urls", {}).get("html"):
        links.append({"label": "arXiv html", "url": context["urls"]["html"]})
    source_links = "\n".join(
        f'      <li><a href="{html.escape(item["url"])}">{html.escape(item["label"])}</a></li>'
        for item in links
    )
    return f"""<!DOCTYPE html>
<html lang="ko"><head>
  <meta charset="utf-8">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} | MALT Tech Blog</title>
  <meta name="description" content="{description}" />
  <link rel="canonical" href="{canonical}" />
  <meta property="og:title" content="{html.escape(title)}" />
  <meta property="og:description" content="{description}" />
  <meta property="og:url" content="{canonical}" />
  <meta property="og:site_name" content="MALT Tech Blog" />
  <meta property="og:type" content="article" />
  <meta property="article:published_time" content="{published_iso}" />
  <meta name="twitter:card" content="summary" />
  <link rel="stylesheet" href="/assets/main.css">
  <link type="application/atom+xml" rel="alternate" href="{SITE_BASE}/feed.xml" title="MALT Tech Blog" />
  <style>
    .malt-tag-rail{{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}}
    .malt-tag-rail .tag-chip{{display:inline-flex;align-items:center;padding:6px 11px;border-radius:999px;border:1px solid #d6e3ee;background:#f7fbfd;text-decoration:none;color:#0f6f8d;font-size:12px;font-weight:700}}
  </style>
</head>
<body><header class="site-header" role="banner">
  <div class="wrapper"><a class="site-title" rel="author" href="/">MALT Tech Blog</a><nav class="site-nav">
        <input type="checkbox" id="nav-trigger" class="nav-trigger" />
        <label for="nav-trigger">
          <span class="menu-icon">
            <svg viewBox="0 0 18 15" width="18px" height="15px">
              <path d="M18,1.484c0,0.82-0.665,1.484-1.484,1.484H1.484C0.665,2.969,0,2.304,0,1.484l0,0C0,0.665,0.665,0,1.484,0 h15.032C17.335,0,18,0.665,18,1.484L18,1.484z M18,7.516C18,8.335,17.335,9,16.516,9H1.484C0.665,9,0,8.335,0,7.516l0,0 c0-0.82,0.665-1.484,1.484-1.484h15.032C17.335,6.031,18,6.696,18,7.516L18,7.516z M18,13.516C18,14.335,17.335,15,16.516,15H1.484 C0.665,15,0,14.335,0,13.516l0,0c0-0.82,0.665-1.483,1.484-1.483h15.032C17.335,12.031,18,12.695,18,13.516L18,13.516z"/>
            </svg>
          </span>
        </label>
        <div class="trigger"><a class="page-link" href="/posts.html">Posts</a><a class="page-link" href="/AI-OPS.html">AI Ops</a><a class="page-link" href="/EDITORIAL.html">Editorial</a><a class="page-link" href="/ABOUT.html">About</a><a class="page-link" href="/CONTACT.html">Contact</a><a class="page-link" href="/PRIVACY.html">Privacy</a></div>
      </nav></div>
</header>
<main class="page-content" aria-label="Content">
  <div class="wrapper">
    <article class="post h-entry" itemscope itemtype="http://schema.org/BlogPosting">
      <header class="post-header">
        <h1 class="post-title p-name" itemprop="name headline">{html.escape(title)}</h1>
        <p class="post-meta"><time class="dt-published" datetime="{published_iso}" itemprop="datePublished">{html.escape(publish_date)}</time></p>
        <div class="malt-tag-rail">{render_tag_links(source)}</div>
      </header>
      <div class="post-content e-content" itemprop="articleBody">
        <p>이 글은 <strong>MALT daily arXiv pipeline</strong>이 주 1~2회 선별 발행하는 자동 큐레이션입니다. 원문 제목은 <em>{html.escape(source['title'])}</em>이며, 저자는 {authors}입니다. 논문 공개일은 {html.escape(source.get("source_date") or source.get("date", ""))}입니다.</p>

        <h2>한 줄 요약</h2>
        <p>{html.escape(analysis.get("one_line", ""))}</p>

        <h2>왜 지금 볼 만한가</h2>
        <p>{html.escape(analysis.get("why_now", ""))}</p>

        <h2>이 논문이 풀려는 문제를 쉽게 말하면</h2>
        <p>{html.escape(analysis.get("problem", ""))}</p>

        <h2>논문이 제안한 방법</h2>
        <p>{html.escape(analysis.get("method_overview", ""))}</p>
        <ul>
{paragraphize(analysis.get("method_steps", []))}
        </ul>

        <h2>실험 결과를 어떻게 읽어야 하나</h2>
        <p>{html.escape(analysis.get("experiment_read", ""))}</p>
        <ul>
{paragraphize(analysis.get("experiment_points", []))}
        </ul>

        <h2>현장에서는 왜 더 어려운가</h2>
        <p>{html.escape(analysis.get("field_reality", ""))}</p>

        <h2>누가 읽으면 특히 좋은가</h2>
        <ul>
{paragraphize(analysis.get("reader_fit", []))}
        </ul>

        <h2>MALT 리뷰</h2>
        <p><strong>왜 골랐는가.</strong> {html.escape(review.get("why_selected", ""))}</p>
        <p><strong>어떻게 읽어야 하는가.</strong> {html.escape(review.get("interpretation", ""))}</p>
        <p><strong>어디에 써먹을 수 있는가.</strong> {html.escape(review.get("applicability", ""))}</p>
        <p><strong>어떤 점을 조심해야 하는가.</strong> {html.escape(review.get("caution", ""))}</p>
        <p><strong>발행 판단.</strong> {html.escape(review.get("verdict", ""))}</p>

        <h2>MALT 해석</h2>
        <p>{html.escape(analysis.get("interpretation", ""))}</p>

        <h2>도입 전에 확인할 질문</h2>
        <ul>
{paragraphize(analysis.get("evaluation_questions", []))}
        </ul>

        <h2>현업 적용 체크리스트</h2>
        <ul>
{paragraphize(analysis.get("operational_takeaways", []))}
        </ul>

        <h2>한계와 체크 포인트</h2>
        <ul>
{paragraphize(analysis.get("limitations", []))}
        </ul>

        <h2>쉽게 결론만 말하면</h2>
        <p>{html.escape(analysis.get("closing", ""))}</p>

        <h2>출처</h2>
        <ul>
{source_links}
        </ul>
      </div><a class="u-url" href="/posts/{basename}.html" hidden></a>
    </article>
  </div>
</main><footer class="site-footer h-card">
  <data class="u-url" href="/"></data>
  <div class="wrapper">
    <h2 class="footer-heading">MALT Tech Blog</h2>
    <div class="footer-col-wrapper">
      <div class="footer-col footer-col-1">
        <ul class="contact-list">
          <li class="p-name">MALT Tech Blog</li><li><a href="/CONTACT.html">Contact &amp; Corrections</a></li><li><a href="https://github.com/whdidtn200/whdidtn200.github.io/issues">Repository Issues</a></li></ul>
      </div>
      <div class="footer-col footer-col-3">
        <p>AI-managed publication archive for Railway Intelligence, PHM, and Agentic AI</p>
      </div>
    </div>
  </div>
</footer>
</body>
</html>
"""


def write_post_files(source: dict) -> tuple[pathlib.Path, pathlib.Path]:
    basename = post_basename(source)
    md_path = POSTS_DIR / f"{basename}.md"
    html_path = POSTS_DIR / f"{basename}.html"
    md_path.write_text(render_markdown(source), encoding="utf-8")
    html_path.write_text(render_html(source), encoding="utf-8")
    return md_path, html_path


def update_posts_listing(title: str, html_filename: str) -> None:
    content = POSTS_INDEX.read_text(encoding="utf-8")
    marker = '<ul class="archive-grid">'
    list_start = content.find(marker)
    list_end = content.find("</ul>", list_start)
    if list_start == -1 or list_end == -1:
        raise SystemExit("posts.html list block not found")
    new_item = f'  <li><a href="/posts/{html_filename}">{html.escape(title)}</a></li>\n'
    block = content[list_start + len(marker):list_end]
    if new_item.strip() in block:
        return
    new_block = "\n" + new_item + block.lstrip("\n")
    POSTS_INDEX.write_text(content[:list_start + len(marker)] + new_block + content[list_end:], encoding="utf-8")


def update_home_latest_links() -> None:
    content = POSTS_INDEX.read_text(encoding="utf-8")
    marker = '<ul class="archive-grid">'
    list_start = content.find(marker)
    list_end = content.find("</ul>", list_start)
    if list_start == -1 or list_end == -1:
        raise SystemExit("posts.html list block not found")
    block = content[list_start:list_end]
    items = re.findall(r'<li><a href="([^"]+)">([^<]+)</a></li>', block)
    latest = items[:6]
    links_html = "\n".join(f'<a href="{href}">{text}</a>' for href, text in latest)

    home = HOME_INDEX.read_text(encoding="utf-8")
    marker = '<div id="latest-links" class="links">'
    start = home.find(marker)
    if start == -1:
        raise SystemExit("latest-links marker not found in index.html")
    end = home.find("</div>", start)
    if end == -1:
        raise SystemExit("latest-links closing tag not found in index.html")
    replacement = f'{marker}\n{links_html}\n'
    HOME_INDEX.write_text(home[:start] + replacement + home[end:], encoding="utf-8")


def publish_once() -> dict | None:
    store_new_sources()
    candidate = choose_candidate()
    write_state_snapshot(load_candidate_sources())
    if candidate is None:
        return None
    candidate = enrich_source(candidate)
    candidate["source_date"] = candidate.get("source_date") or candidate.get("date")
    candidate["publish_date"] = dt.date.today().isoformat()
    build_detailed_analysis(candidate)
    title = build_post_title(candidate)
    md_path, html_path = write_post_files(candidate)
    update_posts_listing(title, html_path.name)
    update_home_latest_links()
    source_filename = f"{candidate['date']}-{candidate['slug']}.json"
    unpublished_path = UNPUBLISHED_DIR / source_filename
    published_path = PUBLISHED_DIR / source_filename
    if unpublished_path.exists():
        unpublished_path.replace(published_path)
        published_path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        published_path.write_text(json.dumps(candidate, ensure_ascii=False, indent=2), encoding="utf-8")
    write_state_snapshot(load_candidate_sources())
    return {
        "source_title": candidate["title"],
        "post_title": title,
        "md_path": str(md_path.relative_to(ROOT)),
        "html_path": str(html_path.relative_to(ROOT)),
        "published_source_path": str(published_path.relative_to(ROOT)),
    }


if __name__ == "__main__":
    result = publish_once()
    if result is None:
        print("no unpublished arXiv sources available")
    else:
        print(json.dumps(result, ensure_ascii=False))
