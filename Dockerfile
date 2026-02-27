# Dockerfile - 默认构建当前平台
#
# 构建命令:
#   docker build -t webpage-screenshot .
#
# 对于跨平台构建，请使用 Dockerfile.multi 和 buildx

FROM crpi-sd251gdf7qgra3xz.cn-hangzhou.personal.cr.aliyuncs.com/tiarea/linux_amd64_python:3.11-slim

WORKDIR /app

# 安装 Chrome 依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    curl \
    ca-certificates \
    && curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/google-chrome.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY pyproject.toml .
COPY webpage_screenshot/ webpage_screenshot/

# 安装 Python 依赖
RUN pip install --no-cache-dir -e .

# 设置 Chrome 路径
ENV CHROME_BIN=/usr/bin/google-chrome

ENTRYPOINT ["webpage-screenshot"]
