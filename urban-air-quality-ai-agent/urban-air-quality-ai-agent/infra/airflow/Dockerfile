FROM apache/airflow:2.7.0-python3.11

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Install Python dependencies
RUN pip install --no-cache-dir \
    apache-airflow-providers-kafka==0.3.0 \
    apache-airflow-providers-postgres==5.10.0 \
    apache-airflow-providers-apache-spark==4.11.1 \
    pandas==2.0.3 \
    numpy==1.24.3 \
    psycopg2-binary==2.9.7 \
    requests==2.31.0 \
    python-dotenv==1.0.0

# Create dags, logs, and plugins directories
RUN mkdir -p /home/airflow/airflow/dags && \
    mkdir -p /home/airflow/airflow/logs && \
    mkdir -p /home/airflow/airflow/plugins

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1
