"""
增强版网页截图模块 - 使用 undetected-chromedriver 绕过检测
"""

import os
import time
import base64
import sys
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


def setup_uc_driver(headless: bool = False, window_width: int = 1920,
                    window_height: int = 1080, verbose: bool = True,
                    page_load_timeout: int = 60,
                    session_name: Optional[str] = None,
                    user_data_dir: Optional[str] = None) -> 'webdriver.Chrome':
    """
    使用 undetected-chromedriver 配置驱动（增强反检测）

    参数:
        headless: 是否使用无头模式
        window_width: 窗口宽度
        window_height: 窗口高度
        verbose: 是否显示详细信息
        page_load_timeout: 页面加载超时时间（秒）
        session_name: 会话名称（可选）
        user_data_dir: 用户数据目录（可选）

    返回:
        Chrome WebDriver 实例
    """
    import undetected_chromedriver as uc

    # 获取 Chrome 路径
    chrome_binary = find_chrome_binary()
    if not chrome_binary:
        raise RuntimeError("未找到 Chrome 浏览器")

    # 获取会话目录
    if session_name:
        from webpage_screenshot.session import get_session_dir, create_session
        user_data = get_session_dir(session_name)
        if not os.path.exists(user_data):
            create_session(session_name)
        user_data_dir = user_data

    if verbose:
        print(f"使用 undetected-chromedriver 启动...", file=sys.stderr)
        if user_data_dir:
            print(f"会话目录：{user_data_dir}", file=sys.stderr)
        print(f"使用 Chrome: {chrome_binary}", file=sys.stderr)

    # 配置 Chrome 选项
    chrome_options = uc.ChromeOptions()
    chrome_options.binary_location = chrome_binary

    if headless:
        chrome_options.add_argument("--headless=new")

    chrome_options.add_argument(f"--window-size={window_width},{window_height}")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # 反检测配置 - uc 会自动处理
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-features=IsolateOrigins,site-per-process")

    # 用户数据目录
    if user_data_dir:
        chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

    # 启动浏览器
    driver = uc.Chrome(
        options=chrome_options,
        use_subprocess=True,
        auto_keep_alive=True
    )

    driver.set_page_load_timeout(page_load_timeout)
    return driver


def take_screenshot_uc(url: str, output_path: str = "screenshot.png",
                       headless: bool = False, full_page: bool = True,
                       wait_time: int = 3, auto_wait: bool = True,
                       window_width: int = 1920, window_height: int = 1080,
                       verbose: bool = True,
                       session_name: Optional[str] = None) -> bool:
    """
    使用 undetected-chromedriver 进行截图

    参数:
        url: 要访问的网页 URL
        output_path: 输出图片路径
        headless: 是否使用无头模式
        full_page: 是否截取完整页面
        wait_time: 等待时间（秒）
        auto_wait: 是否自动等待页面资源加载完成
        window_width: 窗口宽度
        window_height: 窗口高度
        verbose: 是否显示详细信息
        session_name: 会话名称（可选）

    返回:
        bool: 操作是否成功
    """
    driver = None
    try:
        if verbose:
            print(f"正在访问：{url}", file=sys.stderr)

        driver = setup_uc_driver(
            headless=headless,
            window_width=window_width,
            window_height=window_height,
            verbose=verbose,
            session_name=session_name
        )

        driver.get(url)

        if auto_wait:
            # 智能等待模式
            time.sleep(wait_time)
            driver.execute_script("return document.readyState")
        else:
            time.sleep(wait_time)

        if full_page:
            total_height = driver.execute_script("return document.body.scrollHeight")
            total_width = driver.execute_script("return document.body.scrollWidth")
            driver.set_window_size(max(total_width, window_width), max(total_height, window_height))

        result = driver.execute_cdp_cmd("Page.captureScreenshot", {
            "captureBeyondViewport": full_page,
            "fromSurface": True
        })

        image_data = base64.b64decode(result['data'])

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'wb') as f:
            f.write(image_data)

        if verbose:
            print(f"截图已保存至：{output_file.absolute()}", file=sys.stderr)
        return True

    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        return False

    finally:
        if driver:
            driver.quit()
