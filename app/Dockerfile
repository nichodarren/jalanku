FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    JALANKU_MODE=prod \
    JALANKU_DATA=/data \
    PORT=8000

WORKDIR /app
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock

COPY jalanku/ ./jalanku/
RUN useradd --system --user-group jalanku \
    && install -d -o jalanku -g jalanku /data

USER jalanku
VOLUME ["/data"]
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ['PORT'] + '/api/kesehatan', timeout=3).close()"
CMD ["sh", "-c", "exec python -m jalanku jalan --host 0.0.0.0 --port \"$PORT\""]
