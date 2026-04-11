FROM apache/airflow:2.7.1

USER root

# 1. Install Java (OpenJDK 17) and system utilities
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    procps \
    curl \
    wget \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 2. Download and Install Apache Spark
# We install Spark 3.4.1 to be compatible with PySpark 3.x
RUN wget https://archive.apache.org/dist/spark/spark-3.4.1/spark-3.4.1-bin-hadoop3.tgz && \
    tar -xzf spark-3.4.1-bin-hadoop3.tgz && \
    mv spark-3.4.1-bin-hadoop3 /opt/spark && \
    rm spark-3.4.1-bin-hadoop3.tgz

# 3. Set Environment Variables for Spark and Java
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV SPARK_HOME=/opt/spark
ENV PATH="/home/airflow/.local/bin:$SPARK_HOME/bin:$JAVA_HOME/bin:$PATH"

# 4. Set directory permissions so Airflow user can run Spark
RUN chown -R airflow: /opt/spark

USER airflow

# 5. Upgrade pip to avoid connection timeout issues
RUN pip install --upgrade pip

# 6. Install Python Dependencies (Topic 2 requirements)
# Installing these in one layer makes the image stable
RUN pip install --no-cache-dir \
    pyspark==3.4.1 \
    great_expectations \
    pandas \
    apache-airflow-providers-hashicorp \
    apache-airflow-providers-google \
    apache-airflow-providers-amazon \
    apache-airflow-providers-microsoft-azure
