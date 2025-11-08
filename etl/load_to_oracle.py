import os
import cx_Oracle
import pandas as pd


def validate_dataframe(df):
    """
    지하철 데이터 DataFrame 검증 함수.
    - 필수 컬럼 존재 여부 확인
    - 빈 데이터 검증
    - 음수값 제거
    - 날짜 형식 검증
    """
    required_cols = ["USE_YMD", "SBWY_ROUT_LN_NM", "SBWY_STNS_NM", "GTON_TNOPE", "GTOFF_TNOPE"]

    # 필수 컬럼 확인
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"누락된 컬럼 존재: {missing_cols}")

    # 빈 데이터 확인
    if df.empty:
        raise ValueError("CSV 파일에 데이터가 없습니다.")

    # 승차·하차 인원 음수 / 이상치 필터링
    invalid_rows = df[(df['GTON_TNOPE'] < 0) | (df['GTOFF_TNOPE'] < 0)]
    if not invalid_rows.empty:
        print(f"음수 데이터 {len(invalid_rows)}건 제거")
        df = df[(df['GTON_TNOPE'] >= 0) & (df['GTOFF_TNOPE'] >= 0)]

    # 날짜 형식 검증
    try:
        pd.to_datetime(df['USE_YMD'], format='%Y%m%d')
        df['USE_YMD'] = df['USE_YMD'].astype(str).str.zfill(8)
    except Exception as e:
        raise ValueError(f"날짜 형식 오류: {e}")

    print(f"데이터 검증 완료: {len(df)}건")
    return df


# CSV 파일이 있는 폴더 경로
DATASET_DIR = "/app/dataset"

# subway_YYYY-MM.csv 형식의 최신 파일 찾기
csv_files = [f for f in os.listdir(DATASET_DIR) if f.endswith(".csv") and f[0:4].isdigit()]

# 파일이 없을 경우 예외 처리
if not csv_files:
    raise FileNotFoundError("YYYY-MM.csv 형식의 파일이 존재하지 않습니다.")

# 파일명에서 날짜 부분(YYYY-MM)을 기준으로 최신 파일 선택
latest_file = max(csv_files, key=lambda x: [int(x.split('-')[0]), int(x.split('-')[1].split('.')[0])])
latest_path = os.path.join(DATASET_DIR, latest_file)
print(f"최신 파일: {latest_file}")

# CSV 파일 읽기
df = pd.read_csv(latest_path)

# 데이터 검증
df = validate_dataframe(df)

# Oracle 연결
conn = cx_Oracle.connect("subway", "subway", "oracle-db:1521/xepdb1")
cursor = conn.cursor()

# 데이터 튜플 리스트 생성
data_tuples = [
    (
        str(row['USE_YMD']),
        row['SBWY_ROUT_LN_NM'],
        row['SBWY_STNS_NM'],
        int(row['GTON_TNOPE']),
        int(row['GTOFF_TNOPE'])
    )
    for _, row in df.iterrows()
]

sql = """
INSERT INTO SUBWAY_TMP (USE_YMD, SBWY_ROUT_LN_NM, SBWY_STNS_NM, GTON_TNOPE, GTOFF_TNOPE)
VALUES (TO_DATE(:1, 'YYYYMMDD'), :2, :3, :4, :5)
"""

try:
    cursor.executemany(sql, data_tuples, batcherrors=True)
    conn.commit()
    print(f"Oracle 적재 완료 ({len(data_tuples)}건, 파일: {latest_file})")
except cx_Oracle.IntegrityError:
    print("중복 데이터 발생 (UNIQUE 제약조건 위반 가능)")
    conn.rollback()
except Exception as e:
    print(f"오류 발생: {e}")
    conn.rollback()
finally:
    conn.close()

print(f"Oracle 적재 완료 ({latest_file})")
