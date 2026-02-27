"""
网页截图核心功能模块
"""

import os
import time
import base64
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait


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


def find_chromedriver():
    """查找 ChromeDriver 路径"""
    paths_to_check = [
        "/usr/bin/chromedriver",
        "/usr/local/bin/chromedriver",
    ]
    for path in paths_to_check:
        if os.path.exists(path):
            return path
    # 检查环境变量
    chromedriver = os.environ.get("CHROMEDRIVER")
    if chromedriver and os.path.exists(chromedriver):
        return chromedriver
    return None


def setup_driver(headless: bool = True, window_width: int = 1920,
                 window_height: int = 1080, verbose: bool = True) -> webdriver.Chrome:
    """
    配置并返回 Chrome WebDriver

    参数:
        headless: 是否使用无头模式
        window_width: 窗口宽度
        window_height: 窗口高度
        verbose: 是否显示详细信息

    返回:
        Chrome WebDriver 实例
    """
    from selenium.webdriver.chrome.service import Service

    chrome_options = Options()

    if headless:
        chrome_options.add_argument("--headless=new")

    chrome_options.add_argument(f"--window-size={window_width},{window_height}")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    chrome_binary = find_chrome_binary()
    if chrome_binary:
        chrome_options.binary_location = chrome_binary
        if verbose:
            print(f"使用 Chrome: {chrome_binary}", file=sys.stderr)

    # 显式指定 chromedriver 路径
    chromedriver_path = find_chromedriver()
    if chromedriver_path:
        service = Service(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        driver = webdriver.Chrome(options=chrome_options)

    driver.set_page_load_timeout(30)
    return driver


def wait_for_page_loaded(driver, timeout: int = 30, verbose: bool = False) -> bool:
    """
    等待页面完全加载（包括动态资源和网络空闲）

    参数:
        driver: WebDriver 实例
        timeout: 超时时间（秒）
        verbose: 是否显示详细信息

    返回:
        bool: 是否成功等待完成
    """
    try:
        # 等待 document.readyState 完成
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

        # 等待网络空闲：检查页面资源是否仍在加载
        start_time = time.time()
        idle_threshold = 0.5  # 网络空闲判定阈值（秒）
        idle_start = None

        while time.time() - start_time < timeout:
            # 检查页面是否有正在加载的资源
            loading = driver.execute_script("""
                return document.readyState !== 'complete' ||
                       window.performance?.getEntriesByType('resource')?.filter(
                           r => r.transferSize === undefined || r.duration > 0
                       ).length > 0;
            """)

            if not loading:
                if idle_start is None:
                    idle_start = time.time()
                elif time.time() - idle_start >= idle_threshold:
                    if verbose:
                        print("页面资源加载完成", file=sys.stderr)
                    return True
            else:
                idle_start = None

            time.sleep(0.1)

        if verbose:
            print("等待超时，继续执行", file=sys.stderr)
        return True

    except Exception as e:
        if verbose:
            print(f"等待页面加载时出错：{e}", file=sys.stderr)
        return True  # 即使出错也继续执行


def wait_for_images_loaded(driver, timeout: int = 10, verbose: bool = False) -> bool:
    """
    等待所有图片加载完成

    参数:
        driver: WebDriver 实例
        timeout: 超时时间（秒）
        verbose: 是否显示详细信息

    返回:
        bool: 是否所有图片加载完成
    """
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("""
                var images = document.getElementsByTagName('img');
                for (var i = 0; i < images.length; i++) {
                    if (images[i].complete === false ||
                        images[i].naturalHeight === 0) {
                        return false;
                    }
                }
                return true;
            """)
        )
        if verbose:
            print("图片加载完成", file=sys.stderr)
        return True
    except Exception:
        if verbose:
            print("图片等待超时，继续执行", file=sys.stderr)
        return True


def take_screenshot(url: str, output_path: str = "screenshot.png",
                    headless: bool = True, full_page: bool = True,
                    wait_time: int = 3, auto_wait: bool = True,
                    window_width: int = 1920, window_height: int = 1080,
                    verbose: bool = True) -> bool:
    """
    访问网页并保存为图片

    参数:
        url: 要访问的网页 URL
        output_path: 输出图片路径
        headless: 是否使用无头模式
        full_page: 是否截取完整页面
        wait_time: 等待时间（秒），auto_wait=True 时作为最大等待时间
        auto_wait: 是否自动等待页面资源加载完成
        window_width: 窗口宽度
        window_height: 窗口高度
        verbose: 是否显示详细信息

    返回:
        bool: 操作是否成功
    """
    import sys
    driver = None
    try:
        if verbose:
            print(f"正在访问：{url}", file=sys.stderr)

        driver = setup_driver(headless, window_width, window_height, verbose)
        driver.get(url)

        if auto_wait:
            # 智能等待模式
            wait_for_page_loaded(driver, timeout=wait_time * 10, verbose=verbose)
            wait_for_images_loaded(driver, timeout=wait_time, verbose=verbose)
        else:
            # 传统固定等待模式
            WebDriverWait(driver, wait_time).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(wait_time)

        if full_page:
            total_height = driver.execute_script("return document.body.scrollHeight")
            total_width = driver.execute_script("return document.body.scrollWidth")
            driver.set_window_size(max(total_width, window_width),max(total_height,window_height))

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
