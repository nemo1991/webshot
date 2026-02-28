"""
Cookie 管理模块 - 导出和导入浏览器 Cookie

用于在不同浏览器实例之间迁移登录状态
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


def get_cookie_file(session_name: str) -> Path:
    """获取 Cookie 文件路径"""
    from webpage_screenshot.session import get_session_dir
    session_dir = Path(get_session_dir(session_name))
    return session_dir / "cookies.json"


def export_cookies(session_name: str, output_path: Optional[str] = None) -> str:
    """
    从 Chrome 会话导出 Cookie 到 JSON 文件

    参数:
        session_name: 会话名称
        output_path: 输出文件路径（可选，默认为会话目录中的 cookies.json）

    返回:
        导出文件路径
    """
    from webpage_screenshot.screenshot import setup_driver

    driver = None
    try:
        driver = setup_driver(
            headless=False,
            verbose=False,
            session_name=session_name,
            disable_automation_detection=True
        )

        # 访问小红书首页以加载 Cookie
        driver.get("https://www.xiaohongshu.com")

        # 获取所有 Cookie
        cookies = driver.get_cookies()

        # 确定输出路径
        if output_path:
            cookie_file = Path(output_path)
        else:
            cookie_file = get_cookie_file(session_name)

        # 保存 Cookie
        cookie_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cookie_file, 'w', encoding='utf-8') as f:
            json.dump({
                "exported_at": datetime.now().isoformat(),
                "domain": "xiaohongshu.com",
                "cookies": cookies
            }, f, indent=2, ensure_ascii=False)

        print(f"已导出 {len(cookies)} 个 Cookie 到：{cookie_file}", file=__import__('sys').stderr)
        return str(cookie_file)

    except Exception as e:
        print(f"导出 Cookie 失败：{e}", file=__import__('sys').stderr)
        raise
    finally:
        if driver:
            driver.quit()


def import_cookies(session_name: str, cookie_file: str) -> bool:
    """
    从 JSON 文件导入 Cookie 到会话

    参数:
        session_name: 会话名称
        cookie_file: Cookie 文件路径

    返回:
        是否导入成功
    """
    from webpage_screenshot.screenshot import setup_driver

    # 读取 Cookie 文件
    with open(cookie_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    cookies = data.get("cookies", data if isinstance(data, list) else [])

    driver = None
    try:
        driver = setup_driver(
            headless=False,
            verbose=False,
            session_name=session_name,
            disable_automation_detection=True
        )

        # 访问目标网站
        driver.get("https://www.xiaohongshu.com")

        # 导入 Cookie
        imported = 0
        for cookie in cookies:
            try:
                # 清理 Cookie 格式
                clean_cookie = {
                    "name": cookie["name"],
                    "value": cookie["value"],
                    "domain": cookie.get("domain", ".xiaohongshu.com"),
                    "path": cookie.get("path", "/"),
                }
                if "expiry" in cookie:
                    clean_cookie["expiry"] = cookie["expiry"]
                if "secure" in cookie:
                    clean_cookie["secure"] = cookie["secure"]

                driver.add_cookie(clean_cookie)
                imported += 1
            except Exception as e:
                pass  # 跳过无效的 Cookie

        print(f"已导入 {imported}/{len(cookies)} 个 Cookie", file=__import__('sys').stderr)

        # 刷新页面使 Cookie 生效
        driver.refresh()

        return True

    except Exception as e:
        print(f"导入 Cookie 失败：{e}", file=__import__('sys').stderr)
        return False
    finally:
        if driver:
            driver.quit()


def check_cookies_valid(session_name: str) -> Dict:
    """
    检查会话 Cookie 是否有效

    参数:
        session_name: 会话名称

    返回:
        检查结果字典
    """
    from webpage_screenshot.session import check_login_status

    return check_login_status("https://www.xiaohongshu.com", session_name)


def list_cookie_files() -> List[Dict]:
    """
    列出所有保存的 Cookie 文件

    返回:
        Cookie 文件信息列表
    """
    from webpage_screenshot.session import get_base_dir

    base_dir = get_base_dir()
    cookie_files = []

    if not base_dir.exists():
        return cookie_files

    for session_dir in base_dir.iterdir():
        if session_dir.is_dir() and not session_dir.name.startswith('.'):
            cookie_file = session_dir / "cookies.json"
            if cookie_file.exists():
                try:
                    stat = cookie_file.stat()
                    with open(cookie_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    cookie_files.append({
                        "session": session_dir.name,
                        "path": str(cookie_file),
                        "size": stat.st_size,
                        "modified": stat.st_mtime,
                        "cookie_count": len(data.get("cookies", []))
                    })
                except Exception:
                    pass

    return cookie_files
