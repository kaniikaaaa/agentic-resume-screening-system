# One image, one process: the interface is built to static files and FastAPI
# serves them next to the API. Render's native Python runtime has no Node, so
# the Node build happens here in its own stage.

# ── stage 1: build the interface ──────────────────────────────────────
FROM node:20-slim AS web

WORKDIR /build

# Copied first so npm ci is only re-run when the dependencies actually change.
COPY package.json package-lock.json ./
RUN npm ci

COPY next.config.mjs tsconfig.json ./
COPY app ./app
COPY components ./components
COPY lib ./lib
COPY public ./public

# Emits out/ instead of a Next server, and drops the Vercel rewrite.
ENV STATIC_EXPORT=1
RUN npm run build


# ── stage 2: runtime ──────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /srv

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY api ./api
COPY screening ./screening
COPY --from=web /build/out ./out

# Node and the whole npm tree stay behind in stage 1 — only the built files
# come across.

# Don't run as root.
RUN useradd --create-home --uid 1001 quorum
USER quorum

EXPOSE 8000

# Shell form so ${PORT} expands. Render assigns the port at runtime; the
# default keeps `docker run` working locally.
CMD uvicorn api.index:app --host 0.0.0.0 --port ${PORT:-8000}
