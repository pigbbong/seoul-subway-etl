FROM apache/airflow:2.9.3-python3.10

USER root
RUN apt-get update && apt-get install -y libaio1 unzip wget && \
    mkdir -p /opt/oracle && \
    cd /opt/oracle && \
    wget https://download.oracle.com/otn_software/linux/instantclient/219000/instantclient-basiclite-linux.x64-21.9.0.0.0dbru.zip && \
    unzip instantclient-basiclite-linux.x64-21.9.0.0.0dbru.zip && \
    rm instantclient-basiclite-linux.x64-21.9.0.0.0dbru.zip && \
    echo "/opt/oracle/instantclient_21_9" > /etc/ld.so.conf.d/oracle-instantclient.conf && \
    ldconfig

ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_21_9:${LD_LIBRARY_PATH}

USER airflow

# Airflow 먼저 설치
RUN pip install --no-cache-dir \
    apache-airflow==2.9.3 \
    apache-airflow-providers-postgres \
    apache-airflow-providers-oracle \
    psycopg2-binary oracledb

# 기타 requirements 설치
COPY --chown=airflow:root ./requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# PATH 강제 지정 + CLI 링크 보장
ENV PATH="/home/airflow/.local/bin:/usr/local/bin:/usr/bin:/bin:${PATH}"
RUN ln -sf /home/airflow/.local/bin/airflow /usr/local/bin/airflow || true

# 한국 시간대(KST) 설정 추가
ENV TZ=Asia/Seoul
ENV AIRFLOW__CORE__DEFAULT_TIMEZONE=Asia/Seoul