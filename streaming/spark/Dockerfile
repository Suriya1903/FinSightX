
FROM apache/spark:4.0.1-python3

WORKDIR /opt/finsightx

# ----------------------------------------------------------
# System tools
# ----------------------------------------------------------

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ----------------------------------------------------------
# Python dependency for MinIO access
# ----------------------------------------------------------

RUN pip install --no-cache-dir minio

# ----------------------------------------------------------
# PostgreSQL JDBC driver
# ----------------------------------------------------------

RUN curl -fL --retry 5 --retry-delay 5 \
    -o /opt/spark/jars/postgresql-42.7.8.jar \
    https://repo.maven.apache.org/maven2/org/postgresql/postgresql/42.7.8/postgresql-42.7.8.jar

# ----------------------------------------------------------
# Hadoop AWS / MinIO support
#
# Hadoop AWS 3.4.1 uses AWS SDK 2.24.6.
# Install these once into the image instead of resolving
# them every time spark-submit is executed.
# ----------------------------------------------------------

RUN curl -fL --retry 5 --retry-delay 5 \
    -o /opt/spark/jars/hadoop-aws-3.4.1.jar \
    https://repo.maven.apache.org/maven2/org/apache/hadoop/hadoop-aws/3.4.1/hadoop-aws-3.4.1.jar

RUN curl -fL --retry 5 --retry-delay 5 \
    -o /opt/spark/jars/aws-sdk-bundle-2.24.6.jar \
    https://repo.maven.apache.org/maven2/software/amazon/awssdk/bundle/2.24.6/bundle-2.24.6.jar

# ----------------------------------------------------------
# Application
# ----------------------------------------------------------

COPY app ./app

RUN mkdir -p /opt/finsightx/checkpoints \
    && mkdir -p /opt/finsightx/lake

# ----------------------------------------------------------
# Environment
# ----------------------------------------------------------

ENV MINIO_ENDPOINT=http://minio:9000
ENV MINIO_ACCESS_KEY=minioadmin
ENV MINIO_SECRET_KEY=change_me
ENV MINIO_BUCKET=finsightx-data

ENV POSTGRES_HOST=postgres
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=finsightx
ENV POSTGRES_USER=finsightx
ENV POSTGRES_PASSWORD=change_me

USER root
