"""
AI-HUB 后端 Dockerfile
多阶段构建，使用 python:3.12-slim 作为基础镜像
"""

# ========== 阶段一：依赖安装 ==========
FROM python:3.12-slim AS builder

WORKDIR /app

# 安装系统依赖（编译所需）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY pyproject.toml .
RUN pip install --no-cache-dir uv && uv pip install --system .


# ========== 阶段二：运行镜像 ==========
FROM python:3.12-slim AS runtime

WORKDIR /app

# 安装运行时系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# 从 builder 阶段复制已安装的包
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制应用代码
COPY app /app/app
COPY alembic.ini /app/
COPY alembic /app/alembic

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
