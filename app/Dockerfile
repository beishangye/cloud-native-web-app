# ================================================================
# 生产级 Python Flask 应用 Dockerfile
# 整合：多阶段构建 + 非 root 用户 + 健康检查 + 分层优化
# ================================================================

# ================================================================
# 阶段 1：依赖阶段（分离依赖下载，利用 Docker 缓存）
# ================================================================
FROM python:3.9-slim AS deps

# 优化点：设置环境变量，禁止生成 .pyc 字节码，不缓冲日志
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 设置工作目录
WORKDIR /app

# 优化点：只复制依赖文件（变化频率低 → 缓存命中率高）
COPY requirements.txt .

# 配置 pip 使用国内镜像源（加速下载）
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn

# 优化点：安装依赖到指定目录，便于后续只复制需要的文件
# --no-cache-dir：不保存 pip 缓存，减小镜像体积
RUN pip install --no-cache-dir -r requirements.txt --target /app/dependencies


# ================================================================
# 阶段 2：运行阶段（只拷贝需要的文件，最小化镜像体积）
# ================================================================
FROM python:3.9-slim AS runtime

# 优化点：设置环境变量（与 deps 阶段保持一致）
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app/dependencies   

# 设置工作目录
WORKDIR /app

# 优化点：从 deps 阶段只拷贝依赖（不拷贝源码和缓存）
COPY --from=deps /app/dependencies /app/dependencies

# 优化点：复制应用源码（放在后面，因为变化频率高）
COPY app.py .

# ================================================================
# 优化点：创建非 root 用户（安全基线）
# ================================================================
# 原理：最小权限原则，容器内应用不应该以 root 运行
# 如果容器被攻破，攻击者获得的是普通用户权限，而非 root
# 使用完整的参数名，避免歧义
RUN addgroup --gid 1001 --system appuser && \
    adduser --uid 1001 --system --ingroup appuser appuser && \
    chown -R appuser:appuser /app

# 切换到非 root 用户
USER appuser

# ================================================================
# 优化点：健康检查（生产环境必备）
# ================================================================
# 原理：K8s/Docker Compose 会定期检查容器是否存活
# 如果连续失败，会自动重启容器，实现服务自愈
# 
# 参数说明：
#   --interval=30s   ：每 30 秒检查一次
#   --timeout=10s    ：检查超时时间 10 秒
#   --start-period=5s：启动后等待 5 秒再开始检查（给应用启动时间）
#   --retries=3      ：连续失败 3 次才判定为不健康
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000')" || exit 1

# 暴露端口（文档作用）
EXPOSE 5000

# ================================================================
# 优化点：启动命令（使用 exec 形式，信号传递更准确）
# ================================================================
# 使用 python -u 确保日志实时输出
CMD ["python", "-m", "gunicorn", "-b", "0.0.0.0:5000", "-w", "4", "--access-logfile", "-", "--error-logfile", "-", "app:app"]
