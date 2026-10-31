from flask import Flask, jsonify

app = Flask(__name__)


@app.route('/')
def hello():
    return "Hello, Docker! This is a Python Web App."


@app.route('/healthz')
def healthz():
    """健康检查专用端点（2026-10 新增）。

    设计原则：liveness 只检查进程自身能否响应，不查询任何下游依赖
    （数据库 / 缓存 / 第三方 API）。

    不要把健康检查直接打在 `/` 上：一旦 `/` 后面接了数据库，
    一次下游抖动会让所有副本同时被判定为不健康并被 kubelet 重启，
    本来是局部故障，会被放大成整站不可用（级联故障）。

    正确的分工是：
      - livenessProbe  -> /healthz ：只返回 200，证明进程还活着
      - readinessProbe -> /healthz ：依赖就绪的判定后续在这里单独加
      - startupProbe   -> /healthz ：启动阶段允许慢响应
    """
    return jsonify(status="ok"), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
