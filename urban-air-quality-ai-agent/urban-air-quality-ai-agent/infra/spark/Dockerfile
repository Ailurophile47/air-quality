FROM apache/spark:3.5.0-python3

USER root

# Install additional packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    pandas==2.0.3 \
    numpy==1.24.3 \
    scikit-learn==1.3.0 \
    kafka-python==2.0.2 \
    psycopg2-binary==2.9.7 \
    requests==2.31.0 \
    python-dotenv==1.0.0

# Create Spark logs directory
RUN mkdir -p /var/spark-logs && \
    chmod 755 /var/spark-logs

# Create work directory
RUN mkdir -p /opt/spark-work && \
    chmod 755 /opt/spark-work

# Copy Spark defaults configuration
COPY spark-defaults.conf /opt/spark/conf/spark-defaults.conf

WORKDIR /opt/spark-work

# Expose ports
EXPOSE 7077 8080 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080 || exit 1

USER spark

CMD ["/opt/spark/bin/spark-class", "org.apache.spark.deploy.master.Master"]
