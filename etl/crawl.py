import requests
import pandas as pd
from datetime import datetime, timedelta
import calendar
import os
import time

API_KEY = ""  # 서울 데이터 광장의 API 키 입력
SERVICE = "CardSubwayStatsNew"
TYPE = "json"

SAVE_DIR = "/app/dataset"
os.makedirs(SAVE_DIR, exist_ok=True)

today = datetime.today()

# 이번 달이 1월이면, 작년 12월로 설정
if today.month == 1:
    target_year = today.year - 1
    target_month = 12
else:
    target_year = today.year
    target_month = today.month - 1

# 지난달의 1일 ~ 말일
start_date = datetime(target_year, target_month, 1)
_, last_day = calendar.monthrange(target_year, target_month)
end_date = datetime(target_year, target_month, last_day)

print(f"수집 대상 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")

all_rows = []

# 지난달 1일부터 말일까지 반복
for i in range((end_date - start_date).days + 1):
    date_check = (start_date + timedelta(days=i)).strftime("%Y%m%d")
    start = 1
    step = 1000
    print(f"\n{date_check} 날짜 데이터 수집 시작")

    while True:
        end = start + step - 1
        url = f"http://openapi.seoul.go.kr:8088/{API_KEY}/{TYPE}/{SERVICE}/{start}/{end}/{date_check}/"
        res = requests.get(url)
        data = res.json()

        if SERVICE not in data or "row" not in data[SERVICE]:
            print(f"{date_check} 데이터 없음 (start={start})")
            break

        rows = data[SERVICE]["row"]
        all_rows.extend(rows)
        print(f"{len(rows)}건 수집 (누적 {len(all_rows)}건)")

        if len(rows) < step:
            break

        start += step
        time.sleep(0.1)

# DataFrame 생성
if all_rows:
    bus_df = pd.DataFrame(all_rows)
    file_path = os.path.join(SAVE_DIR, f"{target_year}-{target_month}.csv")
    bus_df.to_csv(file_path, index=False, encoding="utf-8")
    print(f"\n데이터 수집 완료 ({len(bus_df)}건)")
    print(f"CSV 파일 저장 완료 -> {file_path}")
else:
    print("데이터를 수집하지 못했습니다.")
