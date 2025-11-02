from google.cloud import bigquery
import pandas as pd
import cx_Oracle
import os
from datetime import datetime, timedelta

# 환경 변수 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/app/ ... "  # ...에 빅쿼리에서 받은 AMI json 키를 입력

# BigQuery 설정
project_id = "subway-475903"
dataset_id = "subway"
table_id = "subway_stats"
table_full_id = f"{project_id}.{dataset_id}.{table_id}"

# Oracle 설정
oracle_user = "subway"
oracle_pwd = "subway"
oracle_dsn = "oracle-db:1521/xepdb1"

# 업로드할 대상 월 (이전 달)
today = datetime.today()
first_day_this_month = datetime(today.year, today.month, 1)
last_month = first_day_this_month - timedelta(days=1)
target_month = f"{last_month.year}-{last_month.month:02d}"
print(f"업로드 대상 월: {target_month}")

# Oracle 데이터 조회
conn = cx_Oracle.connect(oracle_user, oracle_pwd, oracle_dsn)
query = f"""
    SELECT
        TO_CHAR(USE_YMD, 'YYYYMMDD') AS USE_YMD,
        SBWY_ROUT_LN_NM,
        SBWY_STNS_NM,
        GTON_TNOPE,
        GTOFF_TNOPE
    FROM SUBWAY_STATS
    WHERE TO_CHAR(USE_YMD, 'YYYY-MM') = '{target_month}'
"""
oracle_df = pd.read_sql(query, conn)
conn.close()

if oracle_df.empty:
    print(f"{target_month} 데이터가 Oracle에 없습니다. 업로드를 건너뜁니다.")
    exit()

print(f"Oracle 조회 완료: {len(oracle_df)}건")

# 날짜 형식으로 변환
oracle_df['USE_YMD'] = pd.to_datetime(oracle_df['USE_YMD'], format='%Y%m%d').dt.date

# BigQuery 클라이언트 생성
client = bigquery.Client(project=project_id)

# BigQuery에서 해당 월 데이터만 조회
print(f"BigQuery에서 {target_month} 데이터 조회 중...")
query_bq = f"""
    SELECT USE_YMD, SBWY_ROUT_LN_NM, SBWY_STNS_NM
    FROM `{table_full_id}`
    WHERE FORMAT_DATE('%Y-%m', USE_YMD) = '{target_month}'
"""
bq_df = client.query(query_bq).to_dataframe()
print(f"BigQuery {target_month} 데이터 {len(bq_df)}건 확인 완료")

# 신규 데이터 추출
merged_df = oracle_df.merge(
    bq_df,
    on=['USE_YMD', 'SBWY_ROUT_LN_NM', 'SBWY_STNS_NM'],
    how='left',
    indicator=True
)
new_df = merged_df[merged_df['_merge'] == 'left_only'].drop(columns=['_merge'])
print(f"신규 데이터: {len(new_df)}건")

if new_df.empty:
    print("신규 데이터가 없습니다. 업로드를 건너뜁니다.")
    exit()

# BigQuery 업로드
job_config = bigquery.LoadJobConfig(
    write_disposition="WRITE_APPEND",  # 기존 데이터 유지 + 신규만 추가
    autodetect=True
)

print(f"BigQuery 업로드 시작: {len(new_df)}건 ({target_month})")
job = client.load_table_from_dataframe(new_df, table_full_id, job_config=job_config)
job.result()
print(f"BigQuery 업로드 완료: {len(new_df)}건 ({target_month})")
