# ================================================================
# 阶段 1：依赖阶段
# ================================================================
FROM python:3.9-slim AS deps

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 复制 requirements.txt（在 app/ 目录下）
COPY requirements.txt .

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn

RUN pip install --no-cache-dir -r requirements.txt --target /app/dependencies


# ================================================================
# 阶段 2：运行阶段
# ================================================================
FROM python:3.9-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/dependencies

WORKDIR /app

COPY --from=deps /app/dependencies /app/dependencies

# ✅ 修复：复制整个 app 目录下的所有文件（不是只复制 app.py）
COPY . .

RUN addgroup --gid 1001 --system appuser && \
    adduser --uid 1001 --system --ingroup appuser appuser && \
    chown -R appuser:appuser /app

USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000')" || exit 1

EXPOSE 5000

CMD ["python", "-u", "-m", "gunicorn", "-b", "0.0.0.0:5000", "-w", "4", "--access-logfile", "-", "--error-logfile", "-", "app:app"]