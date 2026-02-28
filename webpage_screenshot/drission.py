"""
DrissionPage 截图模块 - 使用 DrissionPage 进行网页截图

DrissionPage 是一个基于 Python 的浏览器自动化工具，具有更强的反检测能力。
安装：pip install DrissionPage
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional


def find_chrome_binary():
    """查找 Chrome 浏览器路径"""
    paths_to_check = [
        # Docker/Linux
        "/usr/bin/google-chrome",
        "/usr/bin/google-chrome-stable",
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        # macOS
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Google Chrome for Testing.app/Contents/MacOS/Google Chrome",
        # Windows
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for path in paths_to_check:
        if os.path.exists(path):
            return path
    # 检查环境变量
    chrome_bin = os.environ.get("CHROME_BIN")
    if chrome_bin and os.path.exists(chrome_bin):
        return chrome_bin
    return None


def setup_drission_page(headless: bool = False, window_width: int = 1920,
                        window_height: int = 1080, verbose: bool = True,
                        session_name: Optional[str] = None) -> 'ChromiumPage':
    """
    使用 DrissionPage 配置浏览器

    参数:
        headless: 是否使用无头模式
        window_width: 窗口宽度
        window_height: 窗口高度
        verbose: 是否显示详细信息
        session_name: 会话名称（可选）

    返回:
        ChromiumPage 实例
    """
    from DrissionPage import ChromiumPage, ChromiumOptions

    chrome_binary = find_chrome_binary()
    if not chrome_binary:
        raise RuntimeError("未找到 Chrome 浏览器")

    if verbose:
        print(f"使用 DrissionPage 启动...", file=sys.stderr)

    # 配置 Chrome 选项
    co = ChromiumOptions()
    co.set_binary_path(chrome_binary)
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-gpu')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_argument(f'--window-size={window_width},{window_height}')

    # 用户数据目录
    if session_name:
        from webpage_screenshot.session import get_session_dir, create_session
        user_data_dir = get_session_dir(session_name)
        if not os.path.exists(user_data_dir):
            create_session(session_name)
        co.set_argument(f'--user-data-dir={user_data_dir}')
        if verbose:
            print(f"会话目录：{user_data_dir}", file=sys.stderr)

    if headless:
        co.set_argument('--headless=new')

    if verbose:
        print(f"使用 Chrome: {chrome_binary}", file=sys.stderr)

    # 启动浏览器
    page = ChromiumPage(co)
    return page


def take_screenshot_drission(url: str, output_path: str = "screenshot.png",
                             headless: bool = False, full_page: bool = True,
                             wait_time: int = 3, verbose: bool = True,
                             session_name: Optional[str] = None) -> bool:
    """
    使用 DrissionPage 进行截图

    参数:
        url: 要访问的网页 URL
        output_path: 输出图片路径
        headless: 是否使用无头模式
        full_page: 是否截取完整页面
        wait_time: 等待时间（秒）
        verbose: 是否显示详细信息
        session_name: 会话名称（可选）

    返回:
        bool: 操作是否成功
    """
    page = None
    try:
        if verbose:
            print(f"正在访问：{url}", file=sys.stderr)

        # 启动浏览器
        page = setup_drission_page(
            headless=headless,
            verbose=verbose,
            session_name=session_name
        )

        # 访问页面
        page.get(url)

        # 等待页面加载
        time.sleep(wait_time)

        # 截取完整页面
        if full_page:
            # 滚动到页面底部
            page.scroll.to_bottom()
            time.sleep(1)
            # 截图
            page.get_screenshot(path=output_path, full_page=True)
        else:
            page.get_screenshot(path=output_path)

        if verbose:
            print(f"截图已保存至：{Path(output_path).absolute()}", file=sys.stderr)
        return True

    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        return False

    finally:
        if page:
            page.quit()


def login_and_screenshot(url: str, session_name: str, output_path: str = "screenshot.png",
                         headless: bool = False, wait_time: int = 3,
                         verbose: bool = True) -> bool:
    """
    登录并截图（手动登录后自动继续）

    参数:
        url: 要访问的网页 URL
        session_name: 会话名称
        output_path: 输出图片路径
        headless: 是否使用无头模式
        wait_time: 等待时间（秒）
        verbose: 是否显示详细信息

    返回:
        bool: 操作是否成功
    """
    page = None
    try:
        if verbose:
            print(f"正在访问：{url}", file=sys.stderr)
            print("请在浏览器中完成登录...", file=sys.stderr)
            print("页面将每 2 秒检查一次登录状态，登录后会自动继续...", file=sys.stderr)

        # 启动浏览器
        page = setup_drission_page(
            headless=headless,
            verbose=verbose,
            session_name=session_name
        )

        # 访问页面
        page.get(url)

        # 循环检查登录状态
        max_attempts = 60  # 最多等待 2 分钟
        for i in range(max_attempts):
            time.sleep(2)

            # 检查是否已登录（检测登录弹窗是否消失）
            login_modal = page.ele('xpath://*[contains(text(), "登录")]')
            if not login_modal:
                if verbose:
                    print("检测到登录完成！", file=sys.stderr)
                break

            if verbose and (i + 1) % 10 == 0:
                print(f"等待登录中... ({(i + 1) * 2}秒)", file=sys.stderr)

        # 额外等待
        time.sleep(wait_time)

        # 截图
        page.get_screenshot(path=output_path, full_page=True)

        if verbose:
            print(f"截图已保存至：{Path(output_path).absolute()}", file=sys.stderr)
        return True

    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        return False

    finally:
        if page:
            page.quit()
