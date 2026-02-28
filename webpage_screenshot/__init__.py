"""
网页截图工具 - 使用 Selenium 访问网页并保存为图片

支持多种浏览器引擎:
- Selenium (默认)
- undetected-chromedriver (需要安装)
- DrissionPage (可选，pip install webpage-screenshot[drission])
"""

from webpage_screenshot.screenshot import take_screenshot, wait_for_page_loaded, wait_for_images_loaded
from webpage_screenshot.cli import main
from webpage_screenshot.server import app, run_server
from webpage_screenshot.session import (
    create_session, list_sessions, delete_session,
    get_session_dir, launch_browser_for_login, get_session_info,
    check_login_status
)
from webpage_screenshot.cookie import export_cookies, import_cookies, list_cookie_files

# DrissionPage 模块（可选）
try:
    from webpage_screenshot.drission import take_screenshot_drission, login_and_screenshot
except ImportError:
    pass

__version__ = "2.1.0"
__all__ = [
    "take_screenshot", "main", "wait_for_page_loaded", "wait_for_images_loaded",
    "app", "run_server",
    "create_session", "list_sessions", "delete_session",
    "get_session_dir", "launch_browser_for_login", "get_session_info",
    "check_login_status",
    "export_cookies", "import_cookies", "list_cookie_files",
]
