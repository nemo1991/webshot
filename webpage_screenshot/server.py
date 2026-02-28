"""
HTTP API 服务 - 使用 FastAPI 提供网页截图接口
"""

import base64
import io
import argparse
from typing import Optional

from fastapi import FastAPI, Response, HTTPException
from pydantic import BaseModel

from webpage_screenshot.screenshot import take_screenshot

app = FastAPI(
    title="Webpage Screenshot API",
    description="网页截图服务 - 使用 Selenium 访问网页并保存为图片",
    version="1.0.0"
)


class ScreenshotParams(BaseModel):
    """截图请求参数"""
    url: str
    output_path: Optional[str] = None
    full_page: bool = True
    wait_time: int = 3
    auto_wait: bool = True
    window_width: int = 1920
    window_height: int = 1080
    return_format: str = "binary"  # "binary" or "base64"
    session_name: Optional[str] = None  # 会话名称


@app.post("/screenshot")
async def screenshot(params: ScreenshotParams) -> Response:
    """
    网页截图接口

    返回格式：
    - return_format=binary: 直接返回 PNG 图片
    - return_format=base64: 返回 JSON 包含 base64 编码的图片
    """
    from webpage_screenshot.screenshot import setup_driver, wait_for_page_loaded, wait_for_images_loaded
    from selenium.webdriver.support.ui import WebDriverWait
    import time

    driver = None
    try:
        # 设置 driver 用于获取截图
        driver = setup_driver(
            headless=True,
            window_width=params.window_width,
            window_height=params.window_height,
            verbose=False,
            page_load_timeout=120,  # 增加页面加载超时时间
            session_name=params.session_name
        )
        driver.get(params.url)

        if params.auto_wait:
            wait_for_page_loaded(driver, timeout=params.wait_time * 10, verbose=False)
            wait_for_images_loaded(driver, timeout=params.wait_time, verbose=False)
        else:
            WebDriverWait(driver, params.wait_time).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            time.sleep(params.wait_time)

        if params.full_page:
            total_height = driver.execute_script("return document.body.scrollHeight")
            total_width = driver.execute_script("return document.body.scrollWidth")
            driver.set_window_size(max(total_width, params.window_width), max(total_height, params.window_height))

        result = driver.execute_cdp_cmd("Page.captureScreenshot", {
            "captureBeyondViewport": params.full_page,
            "fromSurface": True
        })

        image_data = base64.b64decode(result['data'])

        # 如果需要保存到文件
        if params.output_path:
            from pathlib import Path
            output_file = Path(params.output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'wb') as f:
                f.write(image_data)

        # 返回格式处理
        if params.return_format == "base64":
            return {"success": True, "image": base64.b64encode(image_data).decode('utf-8')}
        else:
            return Response(content=image_data, media_type="image/png")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if driver:
            driver.quit()


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok"}


# ========== 会话管理 API ==========

from pydantic import BaseModel


class SessionCreate(BaseModel):
    """创建会话请求"""
    name: str


class SessionInfo(BaseModel):
    """会话信息响应"""
    name: str
    path: str
    size_bytes: int
    file_count: int
    created_time: float
    modified_time: float


@app.get("/sessions", response_model=list[str], tags=["Session Management"])
async def list_sessions_api():
    """列出所有会话"""
    from webpage_screenshot.session import list_sessions
    return list_sessions()


@app.get("/sessions/{session_name}", response_model=SessionInfo, tags=["Session Management"])
async def get_session_api(session_name: str):
    """获取会话详细信息"""
    from webpage_screenshot.session import get_session_info
    try:
        info = get_session_info(session_name)
        return SessionInfo(**info)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/sessions", response_model=dict, tags=["Session Management"])
async def create_session_api(session: SessionCreate):
    """创建新会话"""
    from webpage_screenshot.session import create_session
    try:
        session_dir = create_session(session.name)
        return {"success": True, "path": session_dir}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/sessions/{session_name}", response_model=dict, tags=["Session Management"])
async def delete_session_api(session_name: str):
    """删除会话"""
    from webpage_screenshot.session import delete_session
    try:
        delete_session(session_name)
        return {"success": True}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/sessions/{session_name}/login", response_model=dict, tags=["Session Management"])
async def login_session_api(session_name: str, url: str, headless: bool = True):
    """
    启动浏览器登录会话

    注意：此接口在服务器模式下可能无法正常工作，因为浏览器需要在可见模式下登录。
    建议在本地使用 CLI 命令进行登录操作。
    """
    from webpage_screenshot.session import launch_browser_for_login
    try:
        # 在服务器模式下，默认使用无头模式
        success = launch_browser_for_login(url, session_name, headless=headless)
        if success:
            return {"success": True, "message": "登录完成，会话已保存"}
        else:
            raise HTTPException(status_code=500, detail="启动浏览器失败")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


def run_server():
    """命令行启动服务器"""
    parser = argparse.ArgumentParser(description="网页截图 HTTP 服务")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址 (默认：0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="监听端口 (默认：8000)")
    parser.add_argument("--reload", action="store_true", help="启用自动重载（开发模式）")

    args = parser.parse_args()

    import uvicorn
    uvicorn.run(
        "webpage_screenshot.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    run_server()
