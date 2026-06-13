FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

HEALTHCHECK --interval=2s --timeout=3s --start-period=10s --retries=10 \
  CMD curl -sf http://localhost:5000/api/health || exit 1

CMD ["python", "app.py"]
