FROM python:3.10-slim

WORKDIR /app

# 设置时区及非交互安装模式
ENV TZ=Asia/Shanghai \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOST=0.0.0.0 \
    PORT=8080 \
    ENVIRONMENT=prod

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 声明构建代理与 pip 国内镜像加速参数（可自由传入覆写）
ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG ALL_PROXY
ARG NO_PROXY="localhost,127.0.0.1,mirrors.aliyun.com,mirrors.cloud.tencent.com,npmmirror.com"
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ARG PIP_EXTRA_INDEX_URL=https://mirrors.cloud.tencent.com/pypi/simple/
ARG PIP_TRUSTED_HOST="mirrors.aliyun.com mirrors.cloud.tencent.com"

# 配置代理、国内加速下载镜像及 Playwright 全局固化存储路径
ENV http_proxy=$HTTP_PROXY \
    https_proxy=$HTTPS_PROXY \
    all_proxy=$ALL_PROXY \
    no_proxy=$NO_PROXY \
    PIP_INDEX_URL=$PIP_INDEX_URL \
    PIP_EXTRA_INDEX_URL=$PIP_EXTRA_INDEX_URL \
    PIP_TRUSTED_HOST=$PIP_TRUSTED_HOST \
    PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright \
    PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright \
    RENDER_STORAGE_PATH=/root/.cache/ms-playwright \
    render_storage_path=/root/.cache/ms-playwright

# 1. 自动换成国内 Debian 镜像源（阿里源），国内秒速直连下载，彻底解决 apt 龟速问题
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || true && \
    sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list 2>/dev/null || true && \
    sed -i 's/security.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list 2>/dev/null || true && \
    # 永久配置国内阿里源走 DIRECT（直连），防止后续 playwright 安装底层库时因代理连不上宿主机导致卡死
    echo 'Acquire::http::Proxy::mirrors.aliyun.com "DIRECT";' > /etc/apt/apt.conf.d/00aliyun && \
    echo 'Acquire::https::Proxy::mirrors.aliyun.com "DIRECT";' >> /etc/apt/apt.conf.d/00aliyun && \
    apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    fontconfig \
    fonts-wqy-microhei \
    fonts-wqy-zenhei \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 2. 依赖预热层：利用 Docker 分层缓存机制大幅加速二次构建
# 占位结构预装 Python 依赖包、playwright 与 fastapi 驱动，避免每次修改代码都重新拉取轮子
COPY pyproject.toml README.md ./
RUN mkdir -p nonebot_plugin_jx3 && touch nonebot_plugin_jx3/__init__.py && \
    pip install --no-cache-dir . "nonebot2[fastapi]>=2.0.0" "playwright>=1.26.0" "nonebot-plugin-htmlrender>=0.2.0,<0.8.0" && \
    rm -rf nonebot_plugin_jx3

# 3. 清理构建期代理，确保后续 Playwright 纯国内直连且容器运行时不误走代理
ENV HTTP_PROXY="" \
    HTTPS_PROXY="" \
    ALL_PROXY="" \
    http_proxy="" \
    https_proxy="" \
    all_proxy=""

# 4. 固化安装 Playwright Chromium、Headless-Shell、FFmpeg 及其系统底层依赖（彻底在构建期打入镜像，杜绝运行期联网下载）
RUN mkdir -p /root/.cache/ms-playwright /root/.local/share/nonebot2 && \
    ln -snf /root/.cache/ms-playwright /root/.local/share/nonebot2/nonebot_plugin_htmlrender && \
    ln -snf /root/.cache/ms-playwright /ms-playwright && \
    python -m playwright install --with-deps chromium chromium-headless-shell ffmpeg && \
    chmod -R 777 /root/.cache /root/.local /ms-playwright && \
    rm -rf /var/lib/apt/lists/*

# 5. 复制机器人其余代码并以可编辑模式注册插件
COPY . .
RUN pip install --no-cache-dir --no-deps -e .

# 暴露 NoneBot 服务端口（供 OneBot 正向/反向 WebSocket 接入）
EXPOSE 8080

# 启动 NoneBot 服务（使用标准 bot.py 启动入口，支持 python -m nonebot_plugin_jx3 双模式）
CMD ["python", "bot.py"]
