# 🏙️ Seoul Subway ETL Pipeline

서울시 지하철 승하차 인원 데이터를  
**Oracle → BigQuery → Power BI**로 연동하여  
ETL 파이프라인을 자동화한 프로젝트입니다.

---

## 📘 프로젝트 개요

이 프로젝트는 **서울 열린데이터 광장**의 “지하철 승하차 인원 데이터” Open API를 사용하여  
매월 데이터를 자동으로 수집(crawling)하고,  
Oracle DB에 적재 후 BigQuery로 동기화하여 시각화 도구(Power BI)와 연동하는 과정을 포함합니다.

- **데이터 출처**: [서울 열린데이터 광장 - 지하철 승하차 인원](https://data.seoul.go.kr/dataList/OA-12914/S/1/datasetView.do)
- **주요 구성 요소**:
  - 🧩 **Airflow**: ETL 스케줄링 및 자동화
  - 🧱 **Oracle XE**: 임시 스테이징 및 파티셔닝 관리
  - ☁️ **BigQuery**: 데이터 저장 및 Power BI 연동
  - 📊 **Power BI**: 시각화 및 대시보드 제작

---

## 📁 폴더 구조

```plaintext
seoul_subway/
│
├── dags/                      # Airflow DAG 스케줄러 파일
│   └── subway_dags.py
│
├── etl/                       # ETL 파이프라인 코드
│   ├── crawl.py               # 서울시 Open API 크롤링
│   ├── load_to_oracle.py      # Oracle DB 적재
│   ├── load_to_bigquery.py    # BigQuery 업로드
│   ├── make_pipeline.py       # 전체 ETL 파이프라인 실행 스크립트
│   └── staging_exchange.sql   # Oracle 파티션 교체 스크립트
│
├── oracle/                    # Oracle 초기 설정 SQL
│   ├── grant.sql              # 권한 및 사용자 생성
│   └── staging_setting.sql    # 파티션 테이블 및 프로시저 생성
│
├── docker-compose.yml         # 전체 환경 구성
├── Dockerfile                 # Airflow 컨테이너 빌드 설정
└── requirements.txt           # 파이썬 의존성 패키지
```

## ⚙️ 초기 세팅 과정

### Docker
```plaintext
1. 새로 빌드 (캐시 없이)
docker-compose build --no-cache

2. 컨테이너 실행
docker-compose up -d

3. Airflow 메타데이터 DB 초기화
docker exec -it airflow-webserver airflow db init

4. Airflow 관리자 계정 생성
docker exec -it airflow-webserver airflow users create \
  --username admin \
  --firstname admin \
  --lastname user \
  --role Admin \
  --email admin@example.com \
  --password admin

5. Oracle DB 접속
docker exec -it oracle-db sqlplus system/subway@//localhost:1521/freepdb1

6. Oracle 초기 설정 SQL 실행
@/container-entrypoint-initdb.d/grant.sql
@/container-entrypoint-initdb.d/staging_setting.sql

7. Airflow DAG 확인

7-1. 브라우저에서 http://localhost:8080 접속
7-2. admin / admin 로그인
7-3. subway_pipeline DAG가 활성화되어 있는지 확인
7-4. 수동 실행 또는 매월 4일 12:30 KST 스케줄 자동 실행 확인
```

### BigQuery
``` plaintext
1. Google Cloud Console -> 새 프로젝트 만들기 ex)이름 예: subway-475903

2. 좌측 메뉴 → “BigQuery” 검색 → “API 사용 설정(Enable)” 클릭

3. Dataset 생성
  · 프로젝트 내 → “+ Dataset 만들기” 클릭
  · Dataset ID: subway
  · 데이터 위치(Location): US (Power BI 연동은 US 리전에 있어야 함)

4. 서비스 계정 생성 (Airflow 접근용)
  · 메뉴 -> IAM & Admin -> 서비스 계정(Service Accounts)
  · + 서비스 계정 만들기(Create Service Account) 클릭
  · 이름: subway-etl

5. 서비스 계정 권한(Role) 부여
다음 역할 4개 추가:
  · BigQuery 관리자
  · BigQuery 데이터 편집자
  · BigQuery 데이터 뷰어
  · BigQuery 작업 사용자

6. JSON 키 생성 (Airflow용)
  · 생성한 subway-etl 계정 -> 키(Keys) 탭 -> “새 키 추가(Create new key)”
  · 형식: JSON -> 만들기(Create)
```

Power BI
``` plaintext
1. 데이터 가져오기에서 Google Bigquery 선택

2. BigQuery에서 생성한 프로젝트 이메일과 서비스 계정 JSON 키를 이용해 연결

3. 데이터 선택 및 로드
```
