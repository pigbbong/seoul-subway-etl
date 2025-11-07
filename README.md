# 🏙️ Seoul Subway ETL Pipeline

서울시 지하철 승하차 인원 데이터를  
**Oracle → BigQuery → Power BI**로 연동하여  
ETL 파이프라인을 자동화한 프로젝트입니다.

---

## 📘 프로젝트 개요

이 프로젝트는 **서울 열린데이터 광장**의 “지하철 승하차 인원 데이터” Open API를 사용하여  
매월 데이터를 자동으로 수집(crawling)하고,  
Oracle DB에 적재 후 BigQuery로 동기화하여 시각화 도구(Power BI)와 연동하는 과정을 포함합니다.

---

## 🔧 주요 구성 요소 및 선택 이유
### 🧩 Airflow — ETL 스케줄링 및 자동화
매월 서울시 열린데이터 광장의 “지하철 승하차 인원 데이터”를 자동으로 수집하고,
Oracle → BigQuery 적재 과정을 순차적으로 실행하기 위해 사용했습니다.
DAG(Directed Acyclic Graph) 기반으로 각 단계를 정의해,
데이터 수집·정제·적재를 자동화할 수 있습니다.

### 🧱 Oracle XE — 데이터 정제 및 스테이징(DB Layer)
BigQuery 무료 버전은 데이터 조회(read) 는 가능하지만 DML(INSERT/UPDATE) 작업이 제한되어 있습니다.
따라서 BigQuery에 바로 적재하지 않고,
중간 계층인 Oracle을 사용해 데이터를 정제·검증한 뒤 적재했습니다.
특히, PL/SQL 기반으로 음수·누락값 검증, 데이터 형식 통일,
월별 파티션 교체(Partition Exchange) 를 구현하여 안정적으로 데이터를 관리했습니다.

### ☁️ BigQuery — 데이터 웨어하우스(DW) 계층
Oracle에서 정제된 데이터를 BigQuery에 업로드하여 DW 환경을 구성했습니다.
BigQuery는 서버리스 아키텍처로 대규모 데이터를 빠르게 분석할 수 있고,
실무에서도 Airflow·Power BI 등과 함께 가장 많이 쓰이는 조합 중 하나입니다.
또한 서비스 계정(JSON Key)을 활용해 Airflow와 안전하게 연동하는 과정을 직접 구성했습니다.

### 📊 Power BI — 데이터 시각화 및 분석
BigQuery와 직접 연동하여 쿼리 결과를 실시간으로 시각화했습니다.
노선별/월별 승하차 인원, 시간대별 혼잡도 등의 주요 지표를
막대그래프·누적차트 등으로 표현해 데이터 분석의 흐름을 한눈에 확인할 수 있습니다.
이를 통해 실제 DW–BI 연계 구조를 체험하며, 실무형 대시보드 구축 프로세스를 학습했습니다.

### 🐳 Docker — 환경 재현 및 컨테이너 기반 실행
Airflow, Oracle, PostgreSQL 환경을 각각 컨테이너로 구성하여
로컬 환경에서도 동일한 설정으로 파이프라인을 실행할 수 있도록 했습니다.
docker-compose.yml을 통해 각 서비스 간 네트워크 연결과 볼륨 마운트를 자동화했으며,
Airflow–Oracle 간 의존성 및 라이브러리 충돌 문제를 최소화했습니다.
이를 통해 개발 환경과 배포 환경 간의 일관성을 확보하고,
프로젝트 실행 과정을 누구나 손쉽게 재현할 수 있습니다.


---

## 🧭 데이터 흐름 요약

```plaintext
[서울 열린데이터 광장 API]
        ↓
[Airflow DAG 실행]
        ↓
[Oracle Staging Table]
  └─ 데이터 품질 검증 (음수/NULL 제거, 컬럼 형식 확인)
        ↓
[Oracle Main Table]
  └─ 월별 파티션 교체 및 정제 데이터 확정
        ↓
[BigQuery Dataset]
  └─ Oracle → BigQuery 연동 후 Power BI 연결
        ↓
[Power BI Dashboard]
  └─ 노선/월별 승하차 추이, 혼잡도 분석 시각화
```

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

---

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

2. Google Workspace(기업용 Google 계정) 또는 BigQuery 서비스 계정(JSON 키) 을 이용해 연결
  -> Power BI에서는 개인 Gmail 계정(@gmail.com) 은 BigQuery 연동이 불가

3. 데이터 선택 및 로드
```

---

## 🎨 Power BI 시각화

Power BI에서 BigQuery 데이터를 기반으로 노선별 평균 승하차 인원을 트리맵(Tree Map)으로 간단하게 시각화해본 사진입니다.


![Power BI Visualization](https://github.com/user-attachments/assets/1ea4c0de-4e5c-4ba2-b28d-a02dbffbd404)

---

## 🧩 사용 기술 스택

- **Language**: Python 3.10  
- **Orchestration**: Apache Airflow 2.9.3  
- **Database**: Oracle XE 21c (Docker)  
- **Data Warehouse**: Google BigQuery  
- **Visualization**: Power BI  
- **Containerization**: Docker, Docker Compose  


## 🧭 참고 정보

- **데이터 출처**: [서울 열린데이터 광장 - 지하철 승하차 인원](https://data.seoul.go.kr/dataList/OA-12914/S/1/datasetView.do)
- **프로젝트 저장소**: [GitHub Repository](https://github.com/pigbbong/seoul-subway-etl)
