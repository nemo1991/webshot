"""
网页截图工具 - 使用 Selenium 访问网页并保存为图片
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

__version__ = "1.0.0"
__all__ = [
    "take_screenshot", "main", "wait_for_page_loaded", "wait_for_images_loaded",
    "app", "run_server",
    "create_session", "list_sessions", "delete_session",
    "get_session_dir", "launch_browser_for_login", "get_session_info",
    "check_login_status",
    "export_cookies", "import_cookies", "list_cookie_files"
]
