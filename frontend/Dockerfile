# ============================================================
#  Frontend Dockerfile — multi-stage
#  Stage 1: development — serwuje pliki z volume (hot-reload)
#  Stage 2: production  — minimalna nginx z wbudowanymi plikami
# ============================================================

FROM nginx:1.25-alpine AS development

# W dev pliki montowane jako volume — nginx tylko serwuje
COPY nginx-dev.conf /etc/nginx/conf.d/default.conf
EXPOSE 80

# ----------------------------------------------------------
FROM nginx:1.25-alpine AS production

# Skopiuj statyczne pliki do obrazu
COPY src/ /usr/share/nginx/html/

# Konfiguracja nginx dla SPA (Single Page App)
COPY nginx-prod.conf /etc/nginx/conf.d/default.conf

# Usuń domyślną konfigurację
RUN rm -f /etc/nginx/conf.d/default.conf.bak

EXPOSE 80

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s \
  CMD wget -qO- http://localhost/index.html || exit 1
