# -*- coding: utf-8 -*-
"""
대구 응급의료 뉴스 자동 수집 스크립트
- 구글 뉴스 RSS를 이용 (무료, API 키 불필요)
- GitHub Actions에서 매일 자동 실행되어 data.json을 갱신함
"""
import json
import re
import urllib.request
import urllib.parse
from xml.etree import ElementTree as ET
from datetime import datetime, timezone

CATEGORIES = [
    {"id": "er_runaround", "label": "응급실 뺑뺑이",
     "query_national": "응급실 뺑뺑이 OR 응급실 미수용 OR 응급실 표류",
     "query_daegu": "대구 응급실 뺑뺑이 OR 대구 응급실 미수용"},
    {"id": "pediatric", "label": "소아응급의료",
     "query_national": "소아응급의료 OR 소아전문응급의료센터 OR 소아 응급실",
     "query_daegu": "대구 소아응급 OR 대구 소아과 응급실 OR 대구 달빛어린이병원"},
    {"id": "holiday", "label": "명절비상진료",
     "query_national": "명절 비상진료 OR 명절 응급실 OR 명절 문여는병원",
     "query_daegu": "대구 명절 비상진료 OR 대구 설 추석 병원"},
    {"id": "injury", "label": "손상예방·관리",
     "query_national": "손상예방관리 OR 안전사고 통계 OR 손상예방",
     "query_daegu": "대구 손상예방 OR 대구 안전사고"},
    {"id": "cpr_aed", "label": "CPR·AED",
     "query_national": "심폐소생술 교육 OR 자동심장충격기 OR AED 설치",
     "query_daegu": "대구 심폐소생술 OR 대구 자동심장충격기 OR 대구 AED"},
    {"id": "blood", "label": "헌혈",
     "query_national": "헌혈 부족 OR 헌혈 캠페인 OR 혈액수급",
     "query_daegu": "대구 헌혈 OR 대구 혈액원"},
    {"id": "disaster_trauma", "label": "재난의료·권역외상센터",
     "query_national": "재난의료 OR 권역외상센터",
     "query_daegu": "대구 재난의료 OR 대구 권역외상센터 OR 경북권역외상센터"},
    {"id": "emergency_general", "label": "응급의료 일반",
     "query_national": "응급의료 정책 OR 응급의료기관 OR 응급실 과밀화",
     "query_daegu": "대구 응급의료 OR 대구 응급실 OR 대구 응급의료기관"},
]

MAX_ITEMS_PER_QUERY = 6   # 전국/대구 검색어 각각에서 가져올 최대 건수
MAX_ITEMS_TOTAL = 10      # 카테고리당 최종 노출 최대 건수


def fetch_query(query, region, max_items=MAX_ITEMS_PER_QUERY):
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    items = []
    for item in root.findall("./channel/item")[:max_items]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pubdate = (item.findtext("pubDate") or "").strip()
        source_el = item.find("source")
        source = source_el.text.strip() if source_el is not None and source_el.text else ""
        # 구글 뉴스는 종종 제목 끝에 " - 언론사명"을 붙임 -> 제거
        title_clean = title
        if source:
            title_clean = re.sub(r"\s*-\s*" + re.escape(source) + r"\s*$", "", title).strip()
        items.append({
            "title": title_clean,
            "source": source,
            "date": pubdate,
            "url": link,
            "region": region,   # "daegu" 또는 "national"
        })
    return items


def fetch_category(cat):
    """대구 검색어 결과를 먼저, 그 다음 전국 검색어 결과를 이어 붙임 (중복 제목 제거)"""
    daegu_items = fetch_query(cat["query_daegu"], "daegu")
    national_items = fetch_query(cat["query_national"], "national")

    merged = []
    seen_titles = set()
    # 1) 대구 기사를 먼저 채움
    for item in daegu_items:
        if len(merged) >= MAX_ITEMS_TOTAL:
            break
        key = item["title"][:30]
        if key not in seen_titles:
            seen_titles.add(key)
            merged.append(item)
    # 2) 남은 자리를 전국 기사로 채움
    for item in national_items:
        if len(merged) >= MAX_ITEMS_TOTAL:
            break
        key = item["title"][:30]
        if key not in seen_titles:
            seen_titles.add(key)
            merged.append(item)
    return merged


def main():
    result = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "categories": {}
    }
    for cat in CATEGORIES:
        try:
            items = fetch_category(cat)
            result["categories"][cat["id"]] = {
                "label": cat["label"], "items": items, "error": None
            }
        except Exception as e:
            result["categories"][cat["id"]] = {
                "label": cat["label"], "items": [], "error": str(e)
            }

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print("data.json 갱신 완료:", result["generatedAt"])


if __name__ == "__main__":
    main()
