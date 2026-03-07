FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

# Persist model files (mount volume in compose)
ENV MODEL_DIR=/app/models
RUN mkdir -p /app/models

EXPOSE 5051

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "5051"]
