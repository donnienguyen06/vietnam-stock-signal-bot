FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 FINTECH_DATA_DIR=/app/data
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 fintech \
    && mkdir -p /app/data && chown fintech:fintech /app/data
COPY --chown=fintech:fintech fintech ./fintech
COPY --chown=fintech:fintech static ./static
COPY --chown=fintech:fintech run.py ./run.py
USER fintech
EXPOSE 8010
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8010/healthz', timeout=4)"
CMD ["python", "run.py"]
