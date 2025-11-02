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
