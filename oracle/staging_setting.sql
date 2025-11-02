ALTER SESSION SET CONTAINER = XEPDB1;
ALTER SESSION SET CURRENT_SCHEMA = subway;

-- 메인 테이블 (월별 RANGE 파티션)
CREATE TABLE SUBWAY_STATS (
    USE_YMD          DATE,
    SBWY_ROUT_LN_NM  VARCHAR2(20),
    SBWY_STNS_NM     VARCHAR2(50),
    GTON_TNOPE       NUMBER,
    GTOFF_TNOPE      NUMBER
)
PARTITION BY RANGE (USE_YMD)
(
    PARTITION P202508 VALUES LESS THAN (TO_DATE('2025-09-01', 'YYYY-MM-DD')),
    PARTITION P_MAX VALUES LESS THAN (MAXVALUE)
);

ALTER TABLE SUBWAY_STATS
ADD CONSTRAINT PK_SUBWAY_STATS
PRIMARY KEY (USE_YMD, SBWY_ROUT_LN_NM, SBWY_STNS_NM);



-- 임시 적재용 테이블
CREATE TABLE SUBWAY_TMP AS
SELECT * FROM SUBWAY_STATS WHERE 1 = 0;


-- =====================================================
-- 월별 파티션 자동 추가 프로시저 (P_MAX 자동 관리)
-- =====================================================
CREATE OR REPLACE PROCEDURE MANAGE_SUBWAY_PARTITIONS IS
    v_prev_month      DATE;
    v_prev_month_str  VARCHAR2(6);
    v_partition_name  VARCHAR2(10);
    v_sql             VARCHAR2(4000);
    v_exists          NUMBER := 0;
    v_has_max         NUMBER := 0;
BEGIN
    -- 지난달 기준으로 파티션명 계산
    v_prev_month := ADD_MONTHS(TRUNC(SYSDATE, 'MONTH'), -1);  -- 만약 다른 월별의 데이터를 삽입하고자 할 때는 ADD_MONTHS 인자를 수정하고 컴파일 할 것
    v_prev_month_str := TO_CHAR(v_prev_month, 'YYYYMM');
    v_partition_name := 'P' || v_prev_month_str;

    -- 이미 존재하는지 확인
    SELECT COUNT(*) INTO v_exists
      FROM USER_TAB_PARTITIONS
     WHERE UPPER(TABLE_NAME) = 'SUBWAY_STATS'
       AND PARTITION_NAME = v_partition_name;

    IF v_exists = 0 THEN
        -- MAXVALUE 파티션이 존재하는지 확인
        SELECT COUNT(*) INTO v_has_max
          FROM USER_TAB_PARTITIONS
         WHERE UPPER(TABLE_NAME) = 'SUBWAY_STATS'
           AND PARTITION_NAME = 'P_MAX';

        -- MAXVALUE 파티션 제거
        IF v_has_max > 0 THEN
            EXECUTE IMMEDIATE 'ALTER TABLE SUBWAY_STATS DROP PARTITION P_MAX';
            DBMS_OUTPUT.PUT_LINE('Dropped P_MAX partition temporarily');
        END IF;

        --  새로운 월 파티션 추가
        v_sql := 'ALTER TABLE SUBWAY_STATS ADD PARTITION ' || v_partition_name ||
                 ' VALUES LESS THAN (TO_DATE(''' ||
                 TO_CHAR(ADD_MONTHS(v_prev_month, 1), 'YYYY-MM-DD') ||
                 ''', ''YYYY-MM-DD''))';
        EXECUTE IMMEDIATE v_sql;
        DBMS_OUTPUT.PUT_LINE('Created partition: ' || v_partition_name);

        -- MAXVALUE 파티션 다시 추가
        EXECUTE IMMEDIATE 'ALTER TABLE SUBWAY_STATS ADD PARTITION P_MAX VALUES LESS THAN (MAXVALUE)';
        DBMS_OUTPUT.PUT_LINE('Re-added P_MAX partition');
    ELSE
        DBMS_OUTPUT.PUT_LINE('ℹ️ Partition already exists: ' || v_partition_name);
    END IF;

EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Error in MANAGE_SUBWAY_PARTITIONS: ' || SQLERRM);
        RAISE;
END;
/


-- =====================================================
-- 파티션 교체 프로시저 (지난달 데이터 교체)
-- =====================================================
CREATE OR REPLACE PROCEDURE EXCHANGE_SUBWAY_PARTITION IS
    v_prev_month      DATE;
    v_prev_month_str  VARCHAR2(6);
    v_partition_name  VARCHAR2(10);
    v_sql             VARCHAR2(4000);
BEGIN
    v_prev_month := ADD_MONTHS(TRUNC(SYSDATE, 'MONTH'), -1);  -- 만약 다른 월별의 데이터를 삽입하고자 할 때는 ADD_MONTHS 인자를 수정하고 컴파일 할 것
    v_prev_month_str := TO_CHAR(v_prev_month, 'YYYYMM');
    v_partition_name := 'P' || v_prev_month_str;

    -- 제약조건 비활성화 (PK)
    EXECUTE IMMEDIATE 'ALTER TABLE SUBWAY_STATS DISABLE CONSTRAINT PK_SUBWAY_STATS';
    DBMS_OUTPUT.PUT_LINE('Disabled constraint: PK_SUBWAY_STATS');

    -- 파티션 교체 수행
    v_sql := 'ALTER TABLE SUBWAY_STATS EXCHANGE PARTITION ' || v_partition_name ||
             ' WITH TABLE SUBWAY_TMP WITHOUT VALIDATION';
    EXECUTE IMMEDIATE v_sql;
    DBMS_OUTPUT.PUT_LINE('Exchanged data into partition ' || v_partition_name);

    -- TMP 테이블 초기화
    EXECUTE IMMEDIATE 'TRUNCATE TABLE SUBWAY_TMP';
    DBMS_OUTPUT.PUT_LINE(' Truncated SUBWAY_TMP');

    -- 제약조건 재활성화 (NOVALIDATE)
    EXECUTE IMMEDIATE 'ALTER TABLE SUBWAY_STATS ENABLE NOVALIDATE CONSTRAINT PK_SUBWAY_STATS';
    DBMS_OUTPUT.PUT_LINE('Re-enabled constraint: PK_SUBWAY_STATS');

EXCEPTION
    WHEN OTHERS THEN
        DBMS_OUTPUT.PUT_LINE('Error in EXCHANGE_SUBWAY_PARTITION: ' || SQLERRM);
        RAISE;
END;
/
