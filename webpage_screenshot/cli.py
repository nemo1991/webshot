"""
命令行接口模块
"""

import argparse
import sys


def create_parser() -> argparse.ArgumentParser:
    """创建并返回命令行参数解析器"""
    parser = argparse.ArgumentParser(
        prog="webpage-screenshot",
        description="网页截图工具 - 使用 Selenium 访问网页并保存为图片",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  webpage-screenshot https://www.example.com -o screenshot.png
  webpage-screenshot https://www.google.com --full-page
  webpage-screenshot https://github.com -o github.jpg --wait 5
  webpage-screenshot example.com                    # 自动添加 https://
  webpage-screenshot https://example.com --no-auto-wait  # 禁用自动等待
        """
    )

    parser.add_argument("url", help="要截图的网页 URL")
    parser.add_argument("-o", "--output", default="screenshot.png",
                        help="输出图片路径 (默认：screenshot.png)")
    parser.add_argument("--full-page", action="store_true", default=True,
                        help="截取完整页面（滚动截图，默认启用）")
    parser.add_argument("--no-full-page", action="store_false", dest="full_page",
                        help="仅截取当前视口")
    parser.add_argument("--wait", type=int, default=2,
                        help="等待时间（秒），auto_wait 模式下为最大等待时间 (默认：2)")
    parser.add_argument("--no-auto-wait", action="store_false", dest="auto_wait",
                        help="禁用自动等待，使用固定等待时间")
    parser.add_argument("--width", type=int, default=1920,
                        help="浏览器窗口宽度（默认：1920）")
    parser.add_argument("--height", type=int, default=1080,
                        help="浏览器窗口高度（默认：1080）")
    parser.add_argument("--visible", action="store_true",
                        help="显示浏览器窗口（非无头模式）")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="安静模式，不输出详细信息")

    return parser


def main():
    """命令行入口函数"""
    from webpage_screenshot.screenshot import take_screenshot

    parser = create_parser()
    args = parser.parse_args()

    url = args.url
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        if not args.quiet:
            print(f"自动添加协议前缀：{url}", file=sys.stderr)

    success = take_screenshot(
        url=url,
        output_path=args.output,
        headless=not args.visible,
        full_page=args.full_page,
        wait_time=args.wait,
        auto_wait=args.auto_wait,
        window_width=args.width,
        window_height=args.height,
        verbose=not args.quiet
    )

    sys.exit(0 if success else 1)
