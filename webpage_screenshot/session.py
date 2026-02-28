"""
会话管理模块 - 管理 Chrome 浏览器用户配置目录

基于 Chrome 持久化用户目录的会话管理方案：
- 使用 --user-data-dir 参数指定持久化浏览器配置目录
- 用户登录状态自动保存在该目录中，无需手动导出 Cookie
- Docker 卷挂载该目录，实现会话持久化和跨容器共享
"""

import os
import sys
import shutil
import subprocess
import time
from pathlib import Path
from typing import List, Optional, Dict, Any


def get_base_dir() -> Path:
    """获取会话存储基础目录"""
    # Docker 环境
    if os.path.exists("/data/sessions"):
        return Path("/data/sessions")
    # 本地环境
    return Path.home() / ".webpage_screenshot" / "sessions"


def get_session_dir(session_name: str) -> str:
    """
    获取会话目录路径

    参数:
        session_name: 会话名称

    返回:
        会话目录的绝对路径字符串
    """
    base_dir = get_base_dir()
    session_dir = base_dir / session_name
    return str(session_dir)


def create_session(session_name: str) -> str:
    """
    创建新会话目录

    参数:
        session_name: 会话名称

    返回:
        创建的会话目录路径

    异常:
        ValueError: 如果会话已存在
    """
    session_dir = get_session_dir(session_name)
    path = Path(session_dir)

    if path.exists():
        raise ValueError(f"会话 '{session_name}' 已存在：{session_dir}")

    path.mkdir(parents=True, exist_ok=True)
    print(f"已创建会话 '{session_name}': {session_dir}", file=sys.stderr)
    return session_dir


def list_sessions() -> List[str]:
    """
    列出所有可用会话

    返回:
        会话名称列表
    """
    base_dir = get_base_dir()

    if not base_dir.exists():
        return []

    sessions = []
    for item in base_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            sessions.append(item.name)

    return sorted(sessions)


def delete_session(session_name: str) -> bool:
    """
    删除会话

    参数:
        session_name: 会话名称

    返回:
        是否删除成功

    异常:
        ValueError: 如果会话不存在
    """
    session_dir = get_session_dir(session_name)
    path = Path(session_dir)

    if not path.exists():
        raise ValueError(f"会话 '{session_name}' 不存在")

    shutil.rmtree(path)
    print(f"已删除会话 '{session_name}'", file=sys.stderr)
    return True


def launch_browser_for_login(url: str, session_name: str, headless: bool = False) -> bool:
    """
    启动浏览器供用户手动登录

    浏览器会保持打开状态，用户可以在其中登录网站。
    关闭浏览器后，登录状态会保存在会话目录中。

    参数:
        url: 要访问的网页 URL（如登录页面）
        session_name: 会话名称
        headless: 是否使用无头模式（登录场景通常设为 False）

    返回:
        是否成功启动浏览器
    """
    from webpage_screenshot.screenshot import find_chrome_binary, find_chromedriver

    session_dir = get_session_dir(session_name)

    # 确保会话目录存在
    if not os.path.exists(session_dir):
        create_session(session_name)

    chrome_binary = find_chrome_binary()
    if not chrome_binary:
        print("错误：未找到 Chrome 浏览器", file=sys.stderr)
        return False

    # 构建 Chrome 启动命令
    cmd = [
        chrome_binary,
        f"--user-data-dir={session_dir}",
        f"--remote-debugging-port=9222",
        "--disable-blink-features=AutomationControlled",
        "--disable-dev-shm-usage",
        "--no-sandbox",
    ]

    if not headless:
        # 非无头模式下可以正常显示登录界面
        pass
    else:
        cmd.append("--headless=new")

    # 添加 URL
    cmd.append(url)

    print(f"启动浏览器登录：{url}", file=sys.stderr)
    print(f"会话目录：{session_dir}", file=sys.stderr)
    print("请在浏览器中完成登录...", file=sys.stderr)
    print("关闭浏览器后，登录状态将自动保存", file=sys.stderr)

    try:
        # 启动浏览器（阻塞直到浏览器关闭）
        subprocess.run(cmd, check=False)
        print("浏览器已关闭，登录状态已保存", file=sys.stderr)
        return True
    except Exception as e:
        print(f"启动浏览器失败：{e}", file=sys.stderr)
        return False


def get_session_info(session_name: str) -> dict:
    """
    获取会话详细信息

    参数:
        session_name: 会话名称

    返回:
        包含会话信息的字典

    异常:
        ValueError: 如果会话不存在
    """
    session_dir = Path(get_session_dir(session_name))

    if not session_dir.exists():
        raise ValueError(f"会话 '{session_name}' 不存在")

    # 获取目录信息
    total_size = 0
    file_count = 0
    for dirpath, dirnames, filenames in os.walk(session_dir):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            try:
                total_size += os.path.getsize(file_path)
                file_count += 1
            except OSError:
                pass

    # 获取创建和修改时间
    try:
        stat_info = session_dir.stat()
        created_time = stat_info.st_ctime
        modified_time = stat_info.st_mtime
    except OSError:
        created_time = 0
        modified_time = 0

    return {
        "name": session_name,
        "path": str(session_dir),
        "size_bytes": total_size,
        "file_count": file_count,
        "created_time": created_time,
        "modified_time": modified_time,
    }


def check_login_status(url: str, session_name: str, timeout: int = 120) -> Dict[str, Any]:
    """
    检查会话的登录状态

    通过 Selenium 访问页面并检测登录相关的 DOM 元素来判断是否已登录。

    参数:
        url: 要检查的网站 URL
        session_name: 会话名称
        timeout: 检查超时时间（秒）

    返回:
        包含检查结果的字典：
        - logged_in: bool, 是否已登录
        - indicators: dict, 检测到的登录指示器
        - message: str, 检查结果描述
    """
    from webpage_screenshot.screenshot import setup_driver, find_chrome_binary

    chrome_binary = find_chrome_binary()
    if not chrome_binary:
        return {
            "logged_in": False,
            "indicators": {},
            "message": "未找到 Chrome 浏览器"
        }

    driver = None
    try:
        # 使用会话目录启动浏览器
        driver = setup_driver(
            headless=False,  # 使用可见模式以便用户看到检查过程
            verbose=False,
            session_name=session_name,
            page_load_timeout=30
        )

        print(f"正在检查登录状态：{url}", file=sys.stderr)
        driver.get(url)

        # 等待页面加载
        time.sleep(3)

        # 小红书登录状态检测逻辑
        if "xiaohongshu" in url.lower():
            return _check_xiaohongshu_login(driver)

        # 通用登录检测逻辑
        return _check_generic_login(driver)

    except Exception as e:
        return {
            "logged_in": False,
            "indicators": {},
            "message": f"检查失败：{str(e)}"
        }
    finally:
        if driver:
            driver.quit()


def _check_xiaohongshu_login(driver) -> Dict[str, Any]:
    """
    检查小红书登录状态（增强版）

    检测指标：
    1. 页面右上角用户信息（已登录）
    2. 登录弹窗（未登录）
    3. Cookie 中的关键 token
    4. LocalStorage 中的用户数据
    """
    indicators = {}
    messages = []

    try:
        # 等待页面稳定
        time.sleep(2)

        # 1. 检测登录弹窗（未登录标志）- 使用更精确的选择器
        login_modal = driver.execute_script("""
            return document.querySelector('[class*="login"], [class*="LoginModal"]') !== null ||
                   document.querySelector('[aria-label*="登录"]') !== null ||
                   document.querySelector('.login-container') !== null ||
                   (document.querySelector('img[src*="qr_code"]') !== null &&
                    document.querySelector('button[class*="login-btn"]') !== null);
        """)
        indicators["login_modal_visible"] = login_modal
        if login_modal:
            messages.append("检测到登录弹窗")

        # 2. 检测页面右上角的用户信息区域（已登录标志）
        user_area = driver.execute_script("""
            // 检查右上角是否有用户信息
            const headerSelectors = [
                '.user-info',
                '[class*="UserProfile"]',
                '[class*="user-info"]',
                '.header-user-info',
                '[data-type="user"]'
            ];

            for (const selector of headerSelectors) {
                if (document.querySelector(selector) !== null) return true;
            }

            // 检查是否有头像图片在 header 区域
            const header = document.querySelector('header, .header, [role="banner"]');
            if (header) {
                const avatar = header.querySelector('img[alt*="头像"], img[src*="avatar"]');
                if (avatar) return true;
            }

            return false;
        """)
        indicators["user_area_visible"] = user_area
        if user_area:
            messages.append("检测到用户信息区域")

        # 3. 检测 Cookie 中的登录 token（关键指标）
        has_login_cookie = driver.execute_script("""
            const cookies = document.cookie;
            // 小红书关键 Cookie
            const importantCookies = [
                'session',
                'token',
                'access_token',
                'web_session',
                'xh_token',
                'gid'
            ];
            return importantCookies.some(name => cookies.includes(name + '='));
        """)
        indicators["has_login_cookie"] = has_login_cookie
        if has_login_cookie:
            messages.append("检测到登录 Cookie")

        # 4. 检测 LocalStorage 中的用户数据
        has_user_storage = driver.execute_script("""
            try {
                // 检查 localStorage
                const storageKeys = Object.keys(localStorage);
                const userKeys = ['token', 'user', 'profile', 'xh_', 'user_id', 'nickname'];
                const hasUserKey = storageKeys.some(k =>
                    userKeys.some(uk => k.toLowerCase().includes(uk))
                );

                // 检查是否有用户 ID 相关数据
                const hasUserId = storageKeys.some(k =>
                    k.toLowerCase().includes('user') &&
                    k.toLowerCase().includes('id')
                );

                return hasUserKey || hasUserId;
            } catch(e) {
                return false;
            }
        """)
        indicators["has_user_storage"] = has_user_storage
        if has_user_storage:
            messages.append("检测到用户本地存储")

        # 5. 检查页面 URL（登录后通常不会在登录页）
        current_url = driver.current_url
        is_on_login_page = '/login' in current_url.lower()
        indicators["is_on_login_page"] = is_on_login_page

        # 6. 检查侧边栏（已登录用户有完整的侧边栏导航）
        sidebar_complete = driver.execute_script("""
            const sidebar = document.querySelector('aside, .sidebar, [role="navigation"]');
            if (!sidebar) return false;

            // 检查侧边栏是否有创作中心、消息等菜单项
            const menuItems = ['创作中心', '消息', '收藏', '赞过'];
            const sidebarText = sidebar.textContent;
            return menuItems.some(item => sidebarText.includes(item));
        """)
        indicators["sidebar_complete"] = sidebar_complete
        if sidebar_complete:
            messages.append("检测到完整侧边栏")

        # 综合判断
        # 已登录条件：有用户区域或完整侧边栏，或 Cookie+Storage 都有
        logged_in = (
            (user_area and not login_modal) or
            (sidebar_complete and not login_modal) or
            (has_login_cookie and has_user_storage and not is_on_login_page)
        )

        if logged_in:
            message = f"已登录：{', '.join(messages)}"
        else:
            message = f"未登录：{messages if messages else '无登录标志'}"

        return {
            "logged_in": logged_in,
            "indicators": indicators,
            "message": message,
            "confidence": "high" if (user_area or sidebar_complete) else "low"
        }

    except Exception as e:
        return {
            "logged_in": False,
            "indicators": indicators,
            "message": f"检测异常：{str(e)}",
            "confidence": "error"
        }


def _check_generic_login(driver) -> Dict[str, Any]:
    """
    通用登录状态检测

    检测常见的登录指示器
    """
    indicators = {}

    try:
        # 检测登出链接
        logout_visible = driver.execute_script("""
            return Array.from(document.querySelectorAll('a')).some(el =>
                el.textContent.toLowerCase().includes('logout') ||
                el.textContent.toLowerCase().includes('退出') ||
                el.textContent.toLowerCase().includes('登出')
            );
        """)
        indicators["logout_visible"] = logout_visible

        # 检测登录链接
        login_visible = driver.execute_script("""
            return Array.from(document.querySelectorAll('a, button')).some(el =>
                el.textContent.toLowerCase().includes('login') ||
                el.textContent.toLowerCase().includes('登录')
            );
        """)
        indicators["login_visible"] = login_visible

        # 用户相关元素
        user_element = driver.execute_script("""
            return document.querySelector('[class*="user"], [class*="profile"], [class*="account"]') !== null;
        """)
        indicators["user_element"] = user_element

        logged_in = indicators.get("logout_visible") or (
            indicators.get("user_element") and not indicators.get("login_visible")
        )

        message = "已登录" if logged_in else "未登录"

        return {
            "logged_in": logged_in,
            "indicators": indicators,
            "message": message
        }

    except Exception as e:
        return {
            "logged_in": False,
            "indicators": indicators,
            "message": f"检测异常：{str(e)}"
        }


def launch_browser_for_login(
    url: str,
    session_name: str,
    headless: bool = False,
    check_login: bool = True,
    auto_close: bool = False,
    wait_after_login: int = 3
) -> bool:
    """
    启动浏览器供用户手动登录

    浏览器会保持打开状态，用户可以在其中登录网站。
    关闭浏览器后，登录状态会保存在会话目录中。

    参数:
        url: 要访问的网页 URL（如登录页面）
        session_name: 会话名称
        headless: 是否使用无头模式（登录场景通常设为 False）
        check_login: 是否在登录后检查登录状态
        auto_close: 是否检测到登录后自动关闭浏览器
        wait_after_login: 登录后等待时间（秒），用于等待页面稳定

    返回:
        是否成功完成登录
    """
    from webpage_screenshot.screenshot import find_chrome_binary, find_chromedriver

    session_dir = get_session_dir(session_name)

    # 确保会话目录存在
    if not os.path.exists(session_dir):
        create_session(session_name)

    chrome_binary = find_chrome_binary()
    if not chrome_binary:
        print("错误：未找到 Chrome 浏览器", file=sys.stderr)
        return False

    # 构建 Chrome 启动命令（带反检测配置）
    cmd = [
        chrome_binary,
        f"--user-data-dir={session_dir}",
        f"--remote-debugging-port=9222",
        "--disable-blink-features=AutomationControlled",
        "--disable-features=IsolateOrigins,site-per-process",
        "--disable-site-isolation-trials",
        "--disable-dev-shm-usage",
        "--no-sandbox",
        "--disable-gpu-sandbox",
        "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
    ]

    if not headless:
        # 非无头模式下可以正常显示登录界面
        pass
    else:
        cmd.append("--headless=new")

    # 添加 URL
    cmd.append(url)

    print(f"启动浏览器登录：{url}", file=sys.stderr)
    print(f"会话目录：{session_dir}", file=sys.stderr)
    print("请在浏览器中完成登录...", file=sys.stderr)
    print("登录完成后，请使用 'webpage-screenshot session check' 验证登录状态", file=sys.stderr)
    print("按 Ctrl+C 或关闭浏览器结束", file=sys.stderr)

    try:
        # 启动浏览器（阻塞直到浏览器关闭）
        process = subprocess.Popen(cmd)

        # 如果需要检查登录状态且启用了自动关闭
        if check_login and auto_close:
            print("等待登录完成...", file=sys.stderr)
            start_time = time.time()
            max_wait = 120  # 最多等待 2 分钟

            while process.poll() is None:  # 浏览器还在运行
                elapsed = time.time() - start_time
                if elapsed > max_wait:
                    print("等待超时，请手动关闭浏览器", file=sys.stderr)
                    break

                # 使用 Selenium 检查登录状态
                login_status = check_login_status(url, session_name)
                if login_status["logged_in"]:
                    print(f"✓ {login_status['message']}", file=sys.stderr)
                    time.sleep(wait_after_login)
                    print("正在关闭浏览器...", file=sys.stderr)
                    process.terminate()
                    process.wait(timeout=5)
                    print("浏览器已关闭，登录状态已保存", file=sys.stderr)
                    return True

                time.sleep(2)
                if int(elapsed) % 10 == 0:
                    print(f"等待中... ({int(elapsed)}秒)", file=sys.stderr)
        else:
            # 等待浏览器关闭
            process.wait()
            print("浏览器已关闭，登录状态已保存", file=sys.stderr)

        return True

    except Exception as e:
        print(f"启动浏览器失败：{e}", file=sys.stderr)
        return False
