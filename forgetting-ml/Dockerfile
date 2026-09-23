# ContextIQ Forgetting Prediction Engine
# Multi-purpose image: train or serve (serve default).

FROM python:3.12-slim

WORKDIR /app

# System deps: scientific wheels sometimes need a compiler; curl/wget for healthchecks.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

EXPOSE 8000

# Default command serves the API. Train first-boot auto-generates dataset and trains if missing
# (handled by docker-compose command). To train manually inside container:
#   docker run --rm -v $(pwd)/artifacts:/app/artifacts <image> \
#     sh -c "python -m ml.data.generate_dataset && python -m ml.training.train"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
