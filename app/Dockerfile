# ================================================================
# 阶段 1：依赖阶段（deps）
#
# ⚠️ 复盘说明（2026-10）：
#   本阶段与 runtime 使用【同一个基础镜像 python:3.11-slim】，
#   因此多阶段构建在这里【不产生任何镜像体积收益】——此前 README 中
#   “多阶段构建使镜像体积下降 60%” 的说法站不住，已一并修正。
#
#   多阶段构建的真正收益场景是：
#     builder 阶段用带编译工具链的镜像（gcc / make / musl-dev），
#     runtime 阶段用 slim / alpine / distroless，只把编译产物拷过去。
#     省掉的是【编译器和头文件】，而不是运行期依赖。
#   本项目 Flask / gunicorn 均为纯 Python 包（py3-none-any wheel），
#   不需要编译工具链，所以保留多阶段只为了两件事：
#     ① 依赖层与代码层分离 → 改 app.py 不会触发 pip install，缓存命中率高
#     ② 依赖产物集中在单一 prefix 下 → runtime 阶段一行 COPY 即可取走
# ================================================================
FROM python:3.11-slim AS deps

# PYTHONDONTWRITEBYTECODE : 不生成 .pyc，减小镜像层
# PYTHONUNBUFFERED        : stdout/stderr 不缓冲，等价于 python -u，容器日志实时可见
# PIP_NO_CACHE_DIR        : 不落 pip 缓存（--no-cache-dir 的 ENV 兜底）
# PIP_DISABLE_PIP_VERSION_CHECK : 去掉每次安装时的版本检查输出
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 只复制依赖清单，放在最前以最大化构建缓存命中
COPY requirements.txt .

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set install.trusted-host pypi.tuna.tsinghua.edu.cn

# 用 --prefix 替代原先的 --target /app/dependencies。
# 旧的 --target 写法有三个副作用，2026-10 已修复：
#   ① 不生成 console script → 没有 /usr/local/bin/gunicorn，被迫写成 python -m gunicorn
#   ② 不做依赖冲突检查     → 同名包被静默覆盖，绕开了 pip 的保护机制
#   ③ 需要额外挂 PYTHONPATH → 多一层隐式依赖，改动 ENV 就会导致服务起不来且难排查
# --prefix=/install 会生成标准目录结构：
#   /install/lib/python3.11/site-packages  （包体）
#   /install/bin/gunicorn                  （入口脚本）
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ================================================================
# 阶段 2：运行阶段（runtime）
#   Python 3.9 已于 2025-10 EOL（不再提供安全更新），2026-10 统一升级到 3.11
# ================================================================
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 一行拷入全部产物：包体 + gunicorn 入口脚本。
# python:3.11-slim 的 site-packages 正是 /usr/local/lib/python3.11/site-packages，
# 与 deps 阶段 --prefix=/install 生成的 lib 路径对齐，所以可以直接覆盖到 /usr/local。
COPY --from=deps /install /usr/local

# 代码层放最后：改一行代码不会让上面的依赖层缓存失效。
# 必须配合同级目录下的 .dockerignore，否则 .git / __pycache__ / 本地 .venv
# 会被一并打进镜像（requirements.txt 不能忽略，构建需要它）。
COPY . .

# 非 root 运行：容器逃逸时拿到的也不是 root
RUN addgroup --gid 1001 --system appuser && \
    adduser --uid 1001 --system --ingroup appuser appuser && \
    chown -R appuser:appuser /app

USER appuser

# ⚠️ 边界说明：Dockerfile 的 HEALTHCHECK 只对 docker run / compose / swarm 生效，
#    kubelet 完全忽略它。K8s 侧的健康检查由 Pod 的
#    startupProbe / livenessProbe / readinessProbe 负责，见 k8s/deployment.yaml。
#    这里保留 HEALTHCHECK 是为了本地 docker ps 能直接看到 healthy/unhealthy。
#    端点改用独立的 /healthz：不查任何下游依赖，避免把依赖抖动放大成容器重启，
#    也避免每 30 秒一条健康检查记录污染 / 的 access log。
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:5000/healthz').status == 200 else 1)"

EXPOSE 5000

# exec 形式（JSON 数组）而非 shell 形式：
#   写成 CMD "gunicorn ..." 会被包一层 /bin/sh -c，gunicorn 就不再是 PID 1，
#   收不到 SIGTERM，Pod 删除时只能等 terminationGracePeriod 超时后被 SIGKILL（硬杀）。
#   exec 形式下 gunicorn 是 PID 1，收到 SIGTERM 后能在 graceful timeout 内
#   处理完存量请求再退出。
#
# --workers 2：
#   sync worker 一个进程同时只能处理一个请求，所以 workers 就是本 Pod 的最大并发。
#   官方公式 workers = 2 × CPU + 1，但【容器里 os.cpu_count() 读到的是节点核数，
#   而 CFS 配额是按 limits.cpu 给的】——必须按 limits（1000m = 1 核）算才对。
#   理论值 2×1+1 = 3，这里取 2：requests 只有 250m，常态拿不满 1 核，
#   给 master 进程和探针处理留一点余量。
#   注意原先这里写 -w 4 而 limits.cpu 是 500m：4 个 worker 抢 0.5 核会立刻触发
#   CPU throttling，表现为监控上 CPU 没打满但延迟飙升、P99 剧烈抖动，非常难排查。
#   若要更高并发，正确解法是换协程模型（-k gevent --worker-connections 1000）
#   把并发从 2 拉到数百，而不是继续堆 worker 进程。
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", \
     "--access-logfile", "-", "--error-logfile", "-", "app:app"]
