# ============================================================
#  Backend Dockerfile — multi-stage build
#  Stage 1: base        — wspólne zależności
#  Stage 2: development — hot-reload, dev tools
#  Stage 3: production  — Gunicorn, minimal image
# ============================================================

# ----------------------------------------------------------
#  BASE — instalacja zależności Python
# ----------------------------------------------------------
FROM python:3.12-slim AS base

WORKDIR /app

# Zmienne środowiskowe dla Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Systemowe zależności (psycopg2, Pillow itp.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Skopiuj i zainstaluj zależności Pythona
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# ----------------------------------------------------------
#  DEVELOPMENT — hot-reload przez Flask dev server
# ----------------------------------------------------------
FROM base AS development

# Dev-only pakiety
RUN pip install \
    flask-shell-ipython \
    ipython \
    watchdog

# Kod montowany jako volume — nie kopiujemy tutaj
EXPOSE 5000

CMD ["python", "-m", "flask", "run", \
     "--host=0.0.0.0", \
     "--port=5000", \
     "--reload", \
     "--debugger"]

# ----------------------------------------------------------
#  PRODUCTION — Gunicorn, bez dev tools, bez source mount
# ----------------------------------------------------------
FROM base AS production

# Skopiuj cały kod aplikacji do obrazu
COPY . .

# Stwórz nieprivilegowanego użytkownika
RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser \
    && chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000

# Gunicorn: workers = 2*CPU+1, threads dla I/O-bound (DB calls)
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "4", \
     "--threads", "2", \
     "--timeout", "120", \
     "--keep-alive", "5", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "wsgi:app"]
