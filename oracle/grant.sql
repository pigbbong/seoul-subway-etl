-- 관리자 계정으로 실행해야함

-- 세션을 XEPDB1 컨테이너로 전환
ALTER SESSION SET CONTAINER = XEPDB1;

-- 계정 생성
CREATE USER subway IDENTIFIED BY "subway";

-- 권한 부여
GRANT CREATE SESSION, CONNECT, RESOURCE, CREATE VIEW TO subway;

-- USERS 테이블스페이스에 무제한 할당
ALTER USER subway QUOTA UNLIMITED ON USERS;

--  실행 권한 부여
GRANT EXECUTE ON DBMS_SCHEDULER TO subway;

-- 잡 생성 권한 부여
GRANT CREATE JOB TO subway;

-- 자신 소유의 잡 관리 권한도 부여
GRANT MANAGE SCHEDULER TO subway;
