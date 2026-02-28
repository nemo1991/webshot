"""
命令行接口模块
"""

import argparse
import sys


def get_screenshot_parser() -> argparse.ArgumentParser:
    """创建 screenshot 命令的解析器"""
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
  webpage-screenshot https://xiaohongshu.com --session mysession  # 使用会话登录
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
    parser.add_argument("--session", type=str, default=None,
                        help="会话名称，使用已保存的登录状态")
    parser.add_argument("--uc", action="store_true",
                        help="使用 undetected-chromedriver（增强反检测）")
    parser.add_argument("--drission", action="store_true",
                        help="使用 DrissionPage（更强反检测，需安装）")
    parser.add_argument("-q", "--quiet", action="store_true",
                        help="安静模式，不输出详细信息")

    return parser


def get_session_parser() -> argparse.ArgumentParser:
    """创建 session 命令的解析器"""
    parser = argparse.ArgumentParser(
        prog="webpage-screenshot session",
        description="会话管理 - 管理浏览器登录状态",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
会话管理示例:
  webpage-screenshot session list                        # 列出所有会话
  webpage-screenshot session create mysession            # 创建新会话
  webpage-screenshot session login mysession https://xiaohongshu.com  # 登录并保存会话
  webpage-screenshot session delete mysession            # 删除会话
  webpage-screenshot session check mysession https://xiaohongshu.com  # 检查登录状态
  webpage-screenshot session cookie export mysession     # 导出 Cookie
  webpage-screenshot session cookie import mysession cookies.json  # 导入 Cookie
        """
    )

    subparsers = parser.add_subparsers(dest="session_command", help="会话管理命令")

    # session list
    session_list_parser = subparsers.add_parser("list", help="列出所有会话")

    # session create
    session_create_parser = subparsers.add_parser("create", help="创建新会话")
    session_create_parser.add_argument("name", help="会话名称")

    # session delete
    session_delete_parser = subparsers.add_parser("delete", help="删除会话")
    session_delete_parser.add_argument("name", help="会话名称")

    # session login
    session_login_parser = subparsers.add_parser("login", help="启动浏览器登录并保存会话")
    session_login_parser.add_argument("name", help="会话名称")
    session_login_parser.add_argument("url", help="要访问的网页 URL（如登录页面）")
    session_login_parser.add_argument("--visible", action="store_true", default=True,
                                       help="显示浏览器窗口（非无头模式，默认启用）")
    session_login_parser.add_argument("--no-check-login", action="store_false", dest="check_login",
                                       help="禁用登录状态自动检测")
    session_login_parser.add_argument("--auto-close", action="store_true",
                                       help="检测到登录后自动关闭浏览器")
    session_login_parser.add_argument("--check-only", action="store_true",
                                       help="仅检查登录状态，不启动浏览器")

    # session check
    session_check_parser = subparsers.add_parser("check", help="检查会话登录状态")
    session_check_parser.add_argument("name", help="会话名称")
    session_check_parser.add_argument("url", help="要检查的网页 URL")

    # session cookie
    session_cookie_parser = subparsers.add_parser("cookie", help="Cookie 管理")
    cookie_subparsers = session_cookie_parser.add_subparsers(dest="cookie_command", help="Cookie 命令")

    # session cookie export
    cookie_export_parser = cookie_subparsers.add_parser("export", help="导出 Cookie")
    cookie_export_parser.add_argument("name", help="会话名称")
    cookie_export_parser.add_argument("-o", "--output", help="输出文件路径")

    # session cookie import
    cookie_import_parser = cookie_subparsers.add_parser("import", help="导入 Cookie")
    cookie_import_parser.add_argument("name", help="会话名称")
    cookie_import_parser.add_argument("cookie_file", help="Cookie 文件路径")

    return parser


def handle_session_command(args, quiet: bool = False) -> int:
    """处理 session 子命令"""
    from webpage_screenshot.session import (
        create_session, list_sessions, delete_session,
        launch_browser_for_login, get_session_info, check_login_status
    )
    from webpage_screenshot.cookie import export_cookies, import_cookies, list_cookie_files

    session_command = getattr(args, 'session_command', None)

    if session_command is None:
        print("请使用 'webpage-screenshot session --help' 查看可用命令", file=sys.stderr)
        return 1

    if session_command == "list":
        sessions = list_sessions()
        if not sessions:
            if not quiet:
                print("暂无会话", file=sys.stderr)
        else:
            if not quiet:
                print(f"找到 {len(sessions)} 个会话:")
            for name in sessions:
                try:
                    info = get_session_info(name)
                    size_mb = info["size_bytes"] / (1024 * 1024)
                    if not quiet:
                        print(f"  - {name} ({size_mb:.2f} MB, {info['file_count']} 文件)")
                except Exception:
                    if not quiet:
                        print(f"  - {name}")
        return 0

    elif session_command == "create":
        try:
            session_dir = create_session(args.name)
            if not quiet:
                print(f"已创建会话 '{args.name}': {session_dir}")
            return 0
        except ValueError as e:
            print(f"错误：{e}", file=sys.stderr)
            return 1

    elif session_command == "delete":
        try:
            delete_session(args.name)
            if not quiet:
                print(f"已删除会话 '{args.name}'")
            return 0
        except ValueError as e:
            print(f"错误：{e}", file=sys.stderr)
            return 1

    elif session_command == "login":
        # 仅检查登录状态
        if getattr(args, 'check_only', False):
            print(f"检查会话 '{args.name}' 的登录状态...", file=sys.stderr)
            login_status = check_login_status(args.url, args.name)
            if login_status["logged_in"]:
                print(f"✓ 已登录：{login_status['message']}", file=sys.stderr)
                return 0
            else:
                print(f"✗ 未登录：{login_status['message']}", file=sys.stderr)
                return 1

        # 启动浏览器登录
        headless = not args.visible
        check_login = getattr(args, 'check_login', True)
        auto_close = getattr(args, 'auto_close', False)
        success = launch_browser_for_login(
            args.url, args.name,
            headless=headless,
            check_login=check_login,
            auto_close=auto_close
        )
        return 0 if success else 1

    elif session_command == "check":
        # 检查会话登录状态
        print(f"检查会话 '{args.name}' 的登录状态...", file=sys.stderr)
        login_status = check_login_status(args.url, args.name)

        # 输出详细信息
        if not quiet:
            print(f"登录状态：{'已登录 ✓' if login_status['logged_in'] else '未登录 ✗'}", file=sys.stderr)
            print(f"检测结果：{login_status['message']}", file=sys.stderr)
            if login_status.get('indicators'):
                print("检测指标:", file=sys.stderr)
                for key, value in login_status['indicators'].items():
                    status = "✓" if value else "✗"
                    print(f"  {status} {key}: {value}", file=sys.stderr)

        return 0 if login_status["logged_in"] else 1

    elif session_command == "cookie":
        # Cookie 管理
        cookie_command = getattr(args, 'cookie_command', None)

        if cookie_command == "export":
            output_path = getattr(args, 'output', None)
            try:
                result = export_cookies(args.name, output_path)
                if not quiet:
                    print(f"Cookie 已导出到：{result}", file=sys.stderr)
                return 0
            except Exception as e:
                print(f"导出失败：{e}", file=sys.stderr)
                return 1

        elif cookie_command == "import":
            success = import_cookies(args.name, args.cookie_file)
            if success:
                if not quiet:
                    print(f"Cookie 已导入到会话 '{args.name}'", file=sys.stderr)
                return 0
            else:
                print("导入失败", file=sys.stderr)
                return 1

        elif cookie_command is None:
            # 列出所有 Cookie 文件
            cookies = list_cookie_files()
            if not cookies:
                if not quiet:
                    print("暂无保存的 Cookie 文件", file=sys.stderr)
            else:
                if not quiet:
                    print(f"找到 {len(cookies)} 个 Cookie 文件:")
                for c in cookies:
                    if not quiet:
                        print(f"  - {c['session']}: {c['path']} ({c['cookie_count']} cookies)")
            return 0

        else:
            print(f"未知的 cookie 命令：{cookie_command}", file=sys.stderr)
            return 1

    else:
        print(f"未知的会话命令：{session_command}", file=sys.stderr)
        return 1


def run_screenshot(args) -> int:
    """执行截图命令"""
    from webpage_screenshot.screenshot import take_screenshot

    url = args.url
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
        if not getattr(args, 'quiet', False):
            print(f"自动添加协议前缀：{url}", file=sys.stderr)

    # 使用 DrissionPage
    if getattr(args, 'drission', False):
        try:
            from webpage_screenshot.drission import take_screenshot_drission
            success = take_screenshot_drission(
                url=url,
                output_path=args.output,
                headless=not getattr(args, 'visible', False),
                full_page=getattr(args, 'full_page', True),
                wait_time=getattr(args, 'wait', 3),
                verbose=not getattr(args, 'quiet', False),
                session_name=getattr(args, 'session', None)
            )
            return 0 if success else 1
        except ImportError:
            print("错误：DrissionPage 未安装，请运行：pip install DrissionPage", file=sys.stderr)
            return 1

    # 使用普通 Selenium
    success = take_screenshot(
        url=url,
        output_path=args.output,
        headless=not getattr(args, 'visible', False),
        full_page=getattr(args, 'full_page', True),
        wait_time=getattr(args, 'wait', 2),
        auto_wait=getattr(args, 'auto_wait', True),
        window_width=getattr(args, 'width', 1920),
        window_height=getattr(args, 'height', 1080),
        verbose=not getattr(args, 'quiet', False),
        session_name=getattr(args, 'session', None),
        use_uc=getattr(args, 'uc', False)
    )

    return 0 if success else 1


def main():
    """命令行入口函数"""
    # 检查命令行参数
    if len(sys.argv) == 0:
        get_screenshot_parser().print_help()
        sys.exit(1)

    # 第一个参数可能是命令或 URL
    first_arg = sys.argv[1] if len(sys.argv) > 1 else None

    if first_arg == 'session':
        # Session 命令
        parser = get_session_parser()
        args = parser.parse_args(sys.argv[2:])
        sys.exit(handle_session_command(args))

    elif first_arg == 'screenshot':
        # Screenshot 命令
        parser = get_screenshot_parser()
        args = parser.parse_args(sys.argv[2:])
        sys.exit(run_screenshot(args))

    else:
        # 默认模式：直接截图
        parser = get_screenshot_parser()
        args = parser.parse_args()
        sys.exit(run_screenshot(args))
