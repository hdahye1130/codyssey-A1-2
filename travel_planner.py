#!/usr/bin/env python3
"""
국내 여행 추천 프로그램
- Google Gemini API: 여행 지역 추천 및 최종 리포트 생성
- Naver Local API: 맛집 검색
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv
from google import genai


def load_config():
    """환경 변수 및 설정값 로드"""
    load_dotenv()
    
    gemini_key = os.getenv("GEMINI_API_KEY")
    naver_key_id = os.getenv("NAVER_API_KEY_ID")
    naver_key = os.getenv("NAVER_API_KEY")
    
    if not gemini_key:
        print("❌ 오류: GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
        print("   README.md의 '설정 및 실행 방법'을 참고하여 설정하세요.")
        sys.exit(1)
    
    if not naver_key_id or not naver_key:
        print("❌ 오류: NAVER API 키가 설정되지 않았습니다.")
        print("   NAVER_API_KEY_ID, NAVER_API_KEY를 확인하세요.")
        sys.exit(1)
    
    return {
        "gemini_key": gemini_key,
        "naver_key_id": naver_key_id,
        "naver_key": naver_key,
        "gemini_model": "gemini-3.6-flash"  # 최신 안정화된 Gemini 모델
    }


def validate_date(date_str):
    """날짜 형식 검증 (YYYY-MM-DD)"""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def call_llm_for_recommendation(client, date_str):
    """
    1단계: Google Gemini API로 여행 지역 추천
    반환: JSON 파싱된 dict (필수 키: recommended_city, weather, events, reason)
    """
    prompt = f"""당신은 한국 여행 전문가입니다.

주어진 날짜 '{date_str}'에 국내 여행을 가기에 가장 좋은 지역을 추천해주세요.

다음 JSON 형식으로만 응답해주세요. 다른 텍스트는 절대 포함하지 마세요:
{{
  "recommended_city": "지역명 (예: 제주, 강릉, 서울)",
  "weather": "해당 시기 일반적인 날씨 요약 (2-3문장)",
  "events": ["행사1", "행사2", "행사3"],
  "reason": "이 지역을 추천하는 이유 (2-4문장)"
}}

필수 조건:
1. 반드시 JSON만 반환하세요.
2. JSON이 파싱 가능해야 합니다.
3. recommended_city는 실제 국내 도시/지역명이어야 합니다."""

    try:
        print("  → 1차 추천 생성 중...")
        # Chat API 사용
        chat = client.chats.create(model="gemini-3.6-flash")
        response = chat.send_message(prompt)
        
        response_text = response.text.strip()
        
        # JSON 추출 (```json ... ``` 형식 제거)
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        
        recommendation = json.loads(response_text)
        
        # 필수 키 검증
        required_keys = {"recommended_city", "weather", "events", "reason"}
        if not required_keys.issubset(recommendation.keys()):
            raise ValueError(f"필수 키 누락: {required_keys - recommendation.keys()}")
        
        return recommendation, None
    
    except json.JSONDecodeError as e:
        # 재시도: 더 간단한 프롬프트
        print("  ⚠️  JSON 파싱 실패. 재시도 중...")
        retry_prompt = f"""반드시 다음 JSON 형식으로만 응답하세요:
{{
  "recommended_city": "도시명",
  "weather": "날씨",
  "events": ["행사1"],
  "reason": "이유"
}}

날짜: {date_str}
다른 설명 없이 필수 키를 포함한 유효한 JSON만 출력하세요."""
        
        try:
            chat = client.chats.create(model="gemini-3.6-flash")
            response = chat.send_message(retry_prompt)
            response_text = response.text.strip()
            json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            recommendation = json.loads(response_text)
            return recommendation, None
        except Exception as retry_error:
            error_msg = f"LLM JSON 파싱 재시도 실패: {str(retry_error)}"
            return None, {"step": "llm_recommendation", "type": "JSON_PARSE_ERROR", "message": error_msg}
    
    except Exception as e:
        error_msg = f"LLM 1차 추천 실패: {str(e)}"
        return None, {"step": "llm_recommendation", "type": "API_ERROR", "message": error_msg}


def search_restaurants(naver_key_id, naver_key, city):
    """
    2단계: Naver 지도 API로 맛집 검색
    반환: 정규화된 맛집 리스트 (이름, 주소, 카테고리, URL, 좌표)
    """
    url = "https://naverapihub.apigw.ntruss.com/search/v1/local"
    headers = {
        "X-NCP-APIGW-API-KEY-ID": naver_key_id,
        "X-NCP-APIGW-API-KEY": naver_key
    }
    params = {
        "query": f"{city} 맛집",
        "display": 5,
        "start": 1,
        "sort": "comment",
        "format": "json"
    }
    
    try:
        print(f"  → 맛집 검색 중 ({city})...")
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 401:
            error_msg = "인증 실패(401). API 키 설정을 확인하세요."
            return [], {"step": "place_search", "type": "AUTH_ERROR", "message": f"HTTP {response.status_code}: {error_msg}"}
        elif response.status_code == 403:
            error_msg = "권한 없음(403). API 키 권한을 확인하세요."
            return [], {"step": "place_search", "type": "AUTH_ERROR", "message": f"HTTP {response.status_code}: {error_msg}"}
        elif response.status_code != 200:
            error_msg = f"HTTP {response.status_code}"
            return [], {"step": "place_search", "type": "API_ERROR", "message": error_msg}
        
        data = response.json()
        items = data.get("items", [])
        
        if not items:
            return [], {"step": "place_search", "type": "EMPTY_RESULT", "message": f"검색 결과 0건 (query={params['query']})"}
        
        # 정규화
        restaurants = []
        for item in items:
            # HTML 태그 제거 (title에서)
            name = re.sub(r'<[^>]+>', '', item.get("title", ""))
            
            address = item.get("roadAddress") or item.get("address", "")
            category = item.get("category", "")
            url = item.get("link", "")
            
            # 좌표 변환 (문자열 → float)
            try:
                x = float(item.get("mapx", 0)) if item.get("mapx") else 0.0
                y = float(item.get("mapy", 0)) if item.get("mapy") else 0.0
            except (ValueError, TypeError):
                x, y = 0.0, 0.0
            
            restaurants.append({
                "name": name,
                "address": address,
                "category": category,
                "url": url,
                "x": x,
                "y": y
            })
        
        print(f"  ✓ 맛집 {len(restaurants)}곳 검색 완료")
        return restaurants, None
    
    except requests.Timeout:
        error_msg = "Naver API 타임아웃 (10초)"
        return [], {"step": "place_search", "type": "TIMEOUT_ERROR", "message": error_msg}
    except Exception as e:
        error_msg = f"맛집 검색 실패: {str(e)}"
        return [], {"step": "place_search", "type": "API_ERROR", "message": error_msg}


def call_llm_for_report(client, recommendation, restaurants):
    """
    3단계: Google Gemini API로 최종 여행 리포트 생성
    반환: Markdown 리포트 텍스트
    """
    city = recommendation.get("recommended_city", "")
    weather = recommendation.get("weather", "")
    events = recommendation.get("events", [])
    reason = recommendation.get("reason", "")
    
    # 맛집 리스트 포맷
    if restaurants:
        restaurant_text = "\n".join(
            f"- **{r['name']}** ({r['category']})\n  주소: {r['address']}\n  URL: {r['url']}" 
            if r['url'] else f"- **{r['name']}** ({r['category']})\n  주소: {r['address']}"
            for r in restaurants
        )
    else:
        restaurant_text = "- 데이터 없음"
    
    events_text = "\n".join(f"- {e}" for e in events) if events else "- 정보 없음"
    
    prompt = f"""다음 정보를 바탕으로 국내 여행 추천 리포트를 Markdown 형식으로 작성해주세요.

추천 지역: {city}
날씨: {weather}
행사/축제: {events_text}
추천 이유: {reason}
맛집 정보:
{restaurant_text}

다음 구조의 Markdown을 생성하세요:
# 여행 리포트

## 추천 지역

## 추천 이유

## 날씨 요약

## 행사/축제

## 맛집 추천

## 1일 일정 제안

각 섹션은 2-3문장 또는 리스트로 작성하세요."""

    try:
        print("  → 최종 리포트 생성 중...")
        chat = client.chats.create(model="gemini-3.6-flash")
        response = chat.send_message(prompt)
        report = response.text.strip()
        print("  ✓ 리포트 생성 완료")
        return report, None
    except Exception as e:
        error_msg = f"리포트 생성 실패: {str(e)}"
        return None, {"step": "report_generation", "type": "API_ERROR", "message": error_msg}


def create_results_directory():
    """results/ 폴더 생성"""
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    return results_dir


def save_results(date_str, recommendation, restaurants, report, errors):
    """
    결과 저장: JSON(원본 데이터) + Markdown(리포트)
    """
    results_dir = create_results_directory()
    
    # 파일명 생성 (날짜 기반)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"{date_str}_{timestamp}_data.json"
    md_filename = f"{date_str}_{timestamp}_report.md"
    
    # 원본 JSON 저장
    json_data = {
        "date": date_str,
        "generated_at": datetime.now().isoformat(),
        "recommendation": recommendation,
        "restaurants": restaurants,
        "errors": errors
    }
    
    json_path = results_dir / json_filename
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    # Markdown 리포트 저장
    if report:
        md_path = results_dir / md_filename
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# {date_str} 국내 여행 추천 리포트\n\n")
            f.write(report)
            if errors:
                f.write("\n\n## 오류 요약\n")
                for err in errors:
                    f.write(f"- [{err['step']}] {err['type']}: {err['message']}\n")
    
    return json_path, md_path if report else None


def main():
    # CLI 파싱
    parser = argparse.ArgumentParser(
        description="국내 여행 추천 프로그램"
    )
    parser.add_argument(
        "-date",
        required=True,
        help="여행 날짜 (형식: YYYY-MM-DD)"
    )
    
    args = parser.parse_args()
    date_str = args.date
    
    # 날짜 검증
    if not validate_date(date_str):
        print(f"❌ 오류: 잘못된 날짜 형식 '{date_str}'")
        print(f"사용법: python travel_planner.py -date \"YYYY-MM-DD\"")
        print(f"예시: python travel_planner.py -date \"2026-03-15\"")
        sys.exit(1)
    
    print(f"\n🌍 여행 추천 프로그램 시작 (날짜: {date_str})")
    print("=" * 60)
    
    # 설정 로드
    config = load_config()
    
    # Google Gemini 클라이언트 초기화
    client = genai.Client(api_key=config["gemini_key"])
    
    errors = []
    
    # 1단계: 1차 추천
    print("\n[1/3] 1차 추천 생성 중(LLM)...")
    recommendation, error = call_llm_for_recommendation(client, date_str)
    if error:
        print(f"❌ {error['message']}")
        recommendation = {
            "recommended_city": "추천 실패",
            "weather": "정보 없음",
            "events": [],
            "reason": "LLM API 호출 실패"
        }
        errors.append(error)
    else:
        print(f"  ✓ 추천 지역: {recommendation['recommended_city']}")
    
    # 2단계: 맛집 검색
    print("\n[2/3] 맛집 검색 중(지도/장소 API)...")
    restaurants = []
    if recommendation.get("recommended_city") != "추천 실패":
        restaurants, error = search_restaurants(
            config["naver_key_id"],
            config["naver_key"],
            recommendation["recommended_city"]
        )
        if error:
            print(f"  ⚠️  {error['message']}")
            errors.append(error)
    
    # 3단계: 최종 리포트 생성
    print("\n[3/3] 최종 리포트 생성 중(LLM)...")
    report = None
    if recommendation.get("recommended_city") != "추천 실패":
        report, error = call_llm_for_report(client, recommendation, restaurants)
        if error:
            print(f"❌ {error['message']}")
            errors.append(error)
    
    # 결과 저장
    print("\n결과 저장 중...")
    json_path, md_path = save_results(date_str, recommendation, restaurants, report, errors)
    print(f"  ✓ 데이터: {json_path}")
    if md_path:
        print(f"  ✓ 리포트: {md_path}")
    
    # 완료
    print("\n" + "=" * 60)
    print("✅ 완료!")
    print(f"📁 results/ 폴더에서 결과를 확인하세요.")
    if errors:
        print(f"⚠️  주의: {len(errors)}개의 오류가 발생했습니다. 리포트에 기록되었습니다.")


if __name__ == "__main__":
    main()
