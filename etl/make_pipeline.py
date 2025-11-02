import subprocess
import cx_Oracle
import os
import sys

# 컨테이너 내부 경로 설정
BASE_DIR = "/app"
ETL_DIR = os.path.join(BASE_DIR, "etl")
PYTHON = "python"  # 컨테이너 내부 Python 사용

# 1단계: 크롤링
print("\n[1/4] 서울 지하철 데이터 크롤링 시작...", flush=True)
try:
    subprocess.run([PYTHON, os.path.join(ETL_DIR, "crawl.py")], check=True)
    print("데이터 크롤링 성공", flush=True)
except subprocess.CalledProcessError as e:
    print(f"크롤링 오류 발생: {e}", flush=True)
    sys.exit(1)

# 2단계: Oracle 테이블 적재
print("\n[2/4] Oracle 테이블 적재 중...", flush=True)
try:
    subprocess.run([PYTHON, os.path.join(ETL_DIR, "load_to_oracle.py")], check=True)
    print("Oracle 적재 성공", flush=True)
except subprocess.CalledProcessError as e:
    print(f"Oracle 적재 오류 발생: {e}", flush=True)
    sys.exit(1)

# 3단계: Oracle 파티션 교체
print("\n[3/4] Oracle 파티션 교체 실행...", flush=True)
exchange_sql_path = os.path.join(ETL_DIR, "staging_exchange.sql")

try:
    # docker-compose 서비스 이름 기준으로 연결
    connection = cx_Oracle.connect("subway", "subway", "oracle-db:1521/xepdb1")
    cursor = connection.cursor()

    with open(exchange_sql_path, "r", encoding="utf-8") as f:
        exchange_sql = f.read()

    cursor.execute(exchange_sql)
    connection.commit()
    print("파티션 교체 SQL 실행 성공", flush=True)

except (cx_Oracle.DatabaseError, FileNotFoundError) as e:
    print(f"파티션 교체 중 오류 발생: {e}", flush=True)
    sys.exit(1)

finally:
    if 'cursor' in locals():
        cursor.close()
    if 'connection' in locals():
        connection.close()

# 4단계: BigQuery 업로드
print("\n[4/4] BigQuery 업로드 중...", flush=True)
try:
    subprocess.run([PYTHON, os.path.join(ETL_DIR, "load_to_bigquery.py")], check=True)
    print("BigQuery 업로드 성공", flush=True)
except subprocess.CalledProcessError as e:
    print(f"BigQuery 업로드 중 오류 발생: {e}", flush=True)
    sys.exit(1)

print("\n파이프라인 전체 완료! (crawl → oracle → partition → bigquery)", flush=True)
