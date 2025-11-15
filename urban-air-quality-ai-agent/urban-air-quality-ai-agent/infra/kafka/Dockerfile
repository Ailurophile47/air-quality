FROM confluentinc/cp-kafka:7.5.0

# Install additional tools
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Create kafka data directory
RUN mkdir -p /var/lib/kafka/data && \
    chmod 755 /var/lib/kafka/data

# Expose ports
EXPOSE 9092 29092

# Set environment variables
ENV KAFKA_BROKER_ID=1
ENV KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181
ENV KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
ENV KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=PLAINTEXT:PLAINTEXT
ENV KAFKA_INTER_BROKER_LISTENER_NAME=PLAINTEXT
ENV KAFKA_AUTO_CREATE_TOPICS_ENABLE=true
ENV KAFKA_DELETE_TOPIC_ENABLE=true
ENV KAFKA_LOG_RETENTION_HOURS=168
ENV KAFKA_NUM_PARTITIONS=3
ENV KAFKA_DEFAULT_REPLICATION_FACTOR=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD kafka-topics --bootstrap-server localhost:9092 --list || exit 1

CMD ["sh", "-c", "exec /etc/confluent/docker/run"]
