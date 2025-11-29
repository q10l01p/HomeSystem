# OCR Service Docker Image - MinerU API Only
# 轻量级镜像，仅使用 MinerU 云端 API，无需 PaddleOCR

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8
ENV TZ=Asia/Shanghai

# Install minimal system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install requirements
COPY ocr_service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy shared module
COPY shared /app/shared

# Copy application code
COPY ocr_service/*.py /app/
COPY ocr_service/utils /app/utils

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
