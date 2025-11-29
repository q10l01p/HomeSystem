# OCR Service - MinerU API Only
# 轻量级镜像，仅使用 MinerU 云端 API

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV TZ=Asia/Shanghai

# Install minimal dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py /app/
COPY shared /app/shared
COPY utils /app/utils

# Create directories
RUN mkdir -p /tmp/ocr_service /tmp/ocr_results /app/logs

# Create non-root user
RUN useradd -m -u 1000 ocruser && \
    chown -R ocruser:ocruser /app /tmp/ocr_service /tmp/ocr_results
USER ocruser

EXPOSE 5001

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5001/api/health || exit 1

CMD ["python", "app.py"]
