FROM apache/airflow:2.7.1

USER root

# 1. Install Java (OpenJDK 17), build-essentials, and system utilities
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    procps \
    curl \
    wget \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. Download and Install Apache Spark (3.4.1)
RUN wget https://archive.apache.org/dist/spark/spark-3.4.1/spark-3.4.1-bin-hadoop3.tgz && \
    tar -xzf spark-3.4.1-bin-hadoop3.tgz && \
    mv spark-3.4.1-bin-hadoop3 /opt/spark && \
    rm spark-3.4.1-bin-hadoop3.tgz

# 3. Set Environment Variables for Spark and Java
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV SPARK_HOME=/opt/spark
ENV PATH="/home/airflow/.local/bin:$SPARK_HOME/bin:$JAVA_HOME/bin:$PATH"

# 4. Set directory permissions
RUN chown -R airflow: /opt/spark

USER airflow

# 5. Upgrade pip
RUN pip install --upgrade pip

# 6. SECTION A: Core Heavy Data Tools (Checkpoint 1)
RUN pip install --no-cache-dir --default-timeout=1000 \
    pyspark==3.4.1 \
    pandas \
    psycopg2-binary

# 7. SECTION B: Data Quality & Cloud Connectors (Checkpoint 2)
# Fix: Remove version constraint to avoid conflicts with Airflow's cryptography
RUN pip install --no-cache-dir --default-timeout=1000 \
    great_expectations \
    "cloud-sql-python-connector<1.12.0" \
    google-cloud-storage \
    google-cloud-kms

# 8. SECTION C: Airflow Providers (Final Section)
# Note: Airflow core is already installed in the base image
RUN pip install --no-cache-dir --default-timeout=1000 \
    apache-airflow-providers-hashicorp \
    apache-airflow-providers-google \
    apache-airflow-providers-amazon \
    apache-airflow-providers-microsoft-azure

# 9. Pre-set Great Expectations config directory
ENV GX_HOME=/opt/airflow/gx
