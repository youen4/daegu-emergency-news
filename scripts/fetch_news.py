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
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

KST = timezone(timedelta(hours=9))
WEEKDAYS_KO = ["월", "화", "수", "목", "금", "토", "일"]  # 0=월요일 ... 6=일요일


def parse_and_format_date(pubdate_raw):
    """RFC822 날짜 문자열 -> (정렬용 timestamp, 화면표시용 '2026.03.05.(목) 16:00' 문자열)"""
    if not pubdate_raw:
        return 0, ""
    try:
        dt = parsedate_to_datetime(pubdate_raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt_kst = dt.astimezone(KST)
        weekday = WEEKDAYS_KO[dt_kst.weekday()]
        display = dt_kst.strftime(f"%Y.%m.%d.({weekday}) %H:%M")
        return dt_kst.timestamp(), display
    except Exception:
        return 0, pubdate_raw

CATEGORIES = [
    {"id": "emergency_general", "label": "응급의료 일반", "limit": 20,
     "topics": [
         {"query_national": "응급의료 정책 OR 응급의료기관 OR 응급의료센터 OR 응급실 과밀화 OR 권역외상센터 OR 권역응급의료센터",
          "query_daegu": "대구 응급의료 OR 대구 응급실 OR 대구 응급의료기관 OR 대구 응급의료센터 OR 대구 권역외상센터 OR 대구 권역응급의료센터"},
     ]},
    {"id": "er_runaround", "label": "응급실 뺑뺑이", "limit": 20,
     "topics": [
         {"query_national": "응급실 뺑뺑이 OR 응급실 미수용 OR 응급실 표류 OR 응급실 이송 지연 OR 환자 이송 지연 OR 골든타임 놓쳐",
          "query_daegu": "대구 응급실 뺑뺑이 OR 대구 응급실 미수용 OR 대구 응급실 이송 지연 OR 대구 환자 이송 지연"},
     ]},
    {"id": "disaster", "label": "재난의료", "limit": 20,
     "topics": [
         {"query_national": "재난의료", "query_daegu": "대구 재난의료"},
     ]},
    {"id": "pediatric", "label": "소아응급의료", "limit": 20,
     "topics": [
         {"query_national": "소아응급의료 OR 응급소아의료 OR 소아전문응급의료센터 OR 소아 응급실 OR 신생아중환자실 OR NICU OR 신생아 사망 OR 고위험 분만 OR 필수의료",
          "query_daegu": "대구 소아응급 OR 대구 소아과 응급실 OR 대구 달빛어린이병원 OR 대구 신생아중환자실 OR 대구 NICU OR 대구 고위험 분만 OR 대구 필수의료"},
     ]},
    {"id": "etc_misc", "label": "기타", "limit": 30,
     "topics": [
         {"query_national": "명절 비상진료 OR 명절 응급실 OR 명절 문여는병원",
          "query_daegu": "대구 명절 비상진료 OR 대구 설 추석 병원"},
         {"query_national": "손상예방관리 OR 안전사고 통계 OR 손상예방",
          "query_daegu": "대구 손상예방 OR 대구 안전사고"},
         {"query_national": "심폐소생술 교육 OR 자동심장충격기 OR AED 설치",
          "query_daegu": "대구 심폐소생술 OR 대구 자동심장충격기 OR 대구 AED"},
         {"query_national": "헌혈 부족 OR 헌혈 캠페인 OR 혈액수급",
          "query_daegu": "대구 헌혈 OR 대구 혈액원"},
     ]},
]

MAX_ITEMS_PER_QUERY = 15   # 전국/대구 검색어 각각에서 가져올 최대 건수


def fetch_query(query, region, max_items=MAX_ITEMS_PER_QUERY):
    RECENCY_FILTER = "when:2d"
    q = urllib.parse.quote(f"{query} {RECENCY_FILTER}")
    url = f"https://news.google.com/rss/search?q={q}&hl=ko&gl=KR&ceid=KR:ko"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    items = []
    for item in root.findall("./channel/item")[:max_items]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pubdate_raw = (item.findtext("pubDate") or "").strip()
        source_el = item.find("source")
        source = source_el.text.strip() if source_el is not None and source_el.text else ""
        # 구글 뉴스는 종종 제목 끝에 " - 언론사명"을 붙임 -> 제거
        title_clean = title
        if source:
            title_clean = re.sub(r"\s*-\s*" + re.escape(source) + r"\s*$", "", title).strip()
        ts, display_date = parse_and_format_date(pubdate_raw)
        items.append({
            "title": title_clean,
            "source": source,
            "date": display_date,
            "url": link,
            "region": region,
            "_ts": ts,   # 정렬 전용, 최종 출력 전에 제거됨
        })
    return items


def fetch_category(cat):
    """카테고리에 속한 모든 topic(대구+전국)의 결과를 합쳐서 최신순 정렬 후 중복 제거"""
    all_items = []
    for topic in cat["topics"]:
        all_items += fetch_query(topic["query_daegu"], "daegu")
        all_items += fetch_query(topic["query_national"], "national")

    all_items.sort(key=lambda x: x["_ts"], reverse=True)  # 최신순

    limit = cat.get("limit", 15)
    merged = []
    seen_titles = set()
    for item in all_items:
        if len(merged) >= limit:
            break
        key = item["title"][:30]
        if key not in seen_titles:
            seen_titles.add(key)
            item.pop("_ts", None)
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
