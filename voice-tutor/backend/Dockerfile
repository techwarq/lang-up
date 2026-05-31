FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Railway sets PORT automatically; WS server listens on PORT
# For local dev, set WS_PORT=8765 in your environment
EXPOSE 8765

CMD ["python", "main.py"]
