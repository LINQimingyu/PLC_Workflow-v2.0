# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS frontend
WORKDIR /build
COPY app/web/package.json app/web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY app/web/ ./
RUN npm run build && npm test

FROM python:3.13-slim-bookworm AS runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUTF8=1 \
    PYTHONPATH=/opt/plc/app/src \
    HOME=/data \
    HAYSTACK_TELEMETRY_ENABLED=false \
    DO_NOT_TRACK=1 \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1
WORKDIR /opt/plc/app
COPY app/requirements/factory-linux-py313.lock.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt \
    && groupadd --gid 10001 plc \
    && useradd --uid 10001 --gid plc --no-create-home --home-dir /data plc \
    && mkdir /data && chown plc:plc /data
COPY app/src/ ./src/
COPY app/resources/ ./resources/
COPY app/agents/ ./agents/
COPY app/skills/ ./skills/
COPY app/process-packs/ ./process-packs/
COPY app/creation-agent.json app/UPSTREAM.json app/LICENSE app/LICENSE-SCOPE.md app/NOTICE app/THIRD_PARTY_NOTICES.md ./
COPY --from=frontend /build/dist/ ./web/dist/
COPY deploy/healthcheck.py /opt/plc/healthcheck.py
USER 10001:10001
VOLUME ["/data"]
EXPOSE 8772
HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=5 CMD ["python", "/opt/plc/healthcheck.py"]
ENTRYPOINT ["python", "-m", "cim.launch"]
CMD ["--host", "0.0.0.0", "--port", "8772", "--workspace", "/data"]

FROM runtime AS test
COPY app/evals/ ./evals/
RUN python -m pytest evals -q -p no:cacheprovider

FROM runtime AS production
