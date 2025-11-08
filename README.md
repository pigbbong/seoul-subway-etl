# 🏙️ Seoul Subway ETL Pipeline

서울시 지하철 승하차 인원 데이터를  
**Oracle → BigQuery → Power BI**로 연동하여  
ETL 파이프라인을 자동화한 프로젝트입니다.

---

## 데이터 흐름 요약

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
  └─ BigQuery로부터 데이터를 로드 후 시각화

---

## 초기 세팅 과정

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

### Power BI
``` plaintext
1. 데이터 가져오기에서 Google Bigquery 선택

2. Google Workspace(기업용 Google 계정) 또는 BigQuery 서비스 계정(JSON 키) 을 이용해 연결
  -> Power BI에서는 개인 Gmail 계정(@gmail.com) 은 BigQuery 연동이 불가

3. 데이터 선택 및 로드
```

---

## Power BI 시각화 예시

![Power BI Visualization](https://github.com/user-attachments/assets/1ea4c0de-4e5c-4ba2-b28d-a02dbffbd404)

---

## 사용 기술 스택

- **Language**: Python 3.10  
- **Orchestration**: Apache Airflow 2.9.3  
- **Database**: Oracle XE 21c (Docker)  
- **Data Warehouse**: Google BigQuery  
- **Visualization**: Power BI  
- **Containerization**: Docker, Docker Compose  


## 참고 정보

- **데이터 출처**: [서울 열린데이터 광장 - 지하철 승하차 인원](https://data.seoul.go.kr/dataList/OA-12914/S/1/datasetView.do)
