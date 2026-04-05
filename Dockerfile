FROM apache/airflow:3.1.5

USER root

# Install Java + system tools
RUN apt-get update && apt-get install -y \
    openjdk-17-jdk \
    procps \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Environment Variables
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV SPARK_HOME=/opt/spark
ENV PATH="/home/airflow/.local/bin:$SPARK_HOME/bin:$JAVA_HOME/bin:$PATH"

USER airflow

# Install pyspark inside the image build
RUN pip install --no-cache-dir pyspark
