# 网页截图工具

使用 Selenium 访问网页并保存为图片的命令行工具。

## 安装

### 本地安装开发
```bash
pip install -e .
```

### Docker 方式

```bash
# 构建镜像（当前平台）
docker build -t webpage-screenshot .

# 使用
docker run --rm -v $(pwd):/output webpage-screenshot https://www.example.com -o /output/example.png

# 构建指定平台镜像
docker build -f Dockerfile.amd64 -t webpage-screenshot:amd64 .  # x86_64
docker build -f Dockerfile.arm64 -t webpage-screenshot:arm64 .  # ARM64

# 构建多平台镜像（需要先设置 buildx）
docker buildx build --platform linux/amd64,linux/arm64 -t webpage-screenshot:latest --push .
```

### 全局使用
安装后可在命令行直接使用：
```bash
webpage-screenshot https://www.example.com -o output.png
```

## 依赖

- Python 3.8+
- Google Chrome 浏览器
- Selenium 4.15.0+

### Docker 依赖

- Docker
- 无需安装 Chrome 和 Python 依赖，镜像已包含完整环境

## 使用方法

```bash
# 基本用法（自动等待页面加载完成）
webpage-screenshot https://www.example.com

# 指定输出文件
webpage-screenshot https://www.google.com -o google.png

# 截取完整页面（滚动截图）
webpage-screenshot https://github.com --full-page

# 仅截取当前视口
webpage-screenshot https://example.com --no-full-page

# 调整等待时间（auto_wait 模式下为最大等待时间）
webpage-screenshot https://example.com --wait 5

# 禁用自动等待，使用固定等待时间
webpage-screenshot https://example.com --no-auto-wait --wait 3

# 自定义窗口尺寸
webpage-screenshot https://example.com --width 1920 --height 1080

# 显示浏览器窗口（调试用）
webpage-screenshot https://example.com --visible

# 安静模式
webpage-screenshot https://example.com -o out.png -q
```

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `url` | 要截图的网页 URL | 必填 |
| `-o, --output` | 输出图片路径 | screenshot.png |
| `--full-page` | 截取完整页面 | 启用 |
| `--no-full-page` | 仅截取当前视口 | 禁用 |
| `--wait` | 等待时间（秒），auto_wait 模式下为最大等待时间 | 2 |
| `--no-auto-wait` | 禁用自动等待，使用固定等待时间 | 启用自动等待 |
| `--width` | 窗口宽度 | 1920 |
| `--height` | 窗口高度 | 1080 |
| `--visible` | 显示浏览器窗口 | 禁用 |
| `-q, --quiet` | 安静模式 | 禁用 |

## 作为 Python 模块使用

```python
from webpage_screenshot import take_screenshot, wait_for_page_loaded, wait_for_images_loaded

# 基本用法（自动等待页面加载完成）
take_screenshot("https://www.example.com", "output.png")

# 高级用法
take_screenshot(
    url="https://www.example.com",
    output_path="output.png",
    full_page=True,
    wait_time=5,          # auto_wait 模式下为最大等待时间
    auto_wait=True,       # 自动等待页面资源加载完成
    window_width=1920,
    window_height=1080
)

# 禁用自动等待，使用固定等待时间
take_screenshot(
    url="https://www.example.com",
    output_path="output.png",
    auto_wait=False,
    wait_time=3
)
```

# demo

```
webpage-screenshot https://mp.weixin.qq.com/s/JURbCsOTCYWssETvXOjoeg -o weixin.png --full-page --wait 5 

```


