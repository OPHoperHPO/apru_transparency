from __future__ import annotations
"""
Асинхронный (asyncio) интерактивный обход сайта на Playwright
с хранением состояния в ToolContext.
Ключевые отличия:
- Используется playwright.async_api (полностью async).
- Экземпляры Playwright/Browser/Context/Page резолвятся через ToolContext
  и процесс-локальный реестр по session id.
- В tool_context.state кладём только строковый sid (__browser_sid__), а сами
  объекты живут в процесс-локальном реестре _REGISTRY.
- Если среда не позволяет поднять браузер, инструменты возвращают
  {"status":"disabled", ...} с понятной причиной.
Экспортируемые инструменты (все async):
- open_url(url, tool_context)
- get_html(limit=200_000, tool_context)
- get_current_url(tool_context)
- scroll_by(pixels=800, tool_context)
- click_text(text, exact=False, tool_context)
- click_css(selector, tool_context)
- type_css(selector, text, clear=True, tool_context)
- take_screenshot(tool_context)
- browser_shutdown(tool_context)
"""
import os
import time
import uuid
import pathlib
import asyncio
from dataclasses import dataclass
from typing import Optional, Dict, Any, Tuple
from google.adk.tools import ToolContext
from google.genai.types import Part
HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "true").strip().lower() in ("1", "true", "yes")
USER_AGENT = os.getenv("PLAYWRIGHT_UA", "Mozilla/5.0 (compatible; SEOAgent/1.0)")
VIEWPORT = (1920, 1080)
@dataclass
class _BrowserSession:
    pw: Any
    browser: Any
    context: Any
    page: Any
_REGISTRY: Dict[str, _BrowserSession] = {}
def _disabled(reason: str) -> dict:
    return {"status": "disabled", "enabled": False, "message": reason}
async def _get_or_create_session(tool_context: ToolContext) -> Tuple[Optional[_BrowserSession], dict]:
    """
    Возвращает (session, meta). При невозможности — (None, {"status":"disabled", ...})
    """
    sid = tool_context.state.get("__browser_sid__")
    if sid and sid in _REGISTRY:
        return _REGISTRY[sid], {"reused": True, "sid": sid}
    try:
        from playwright.async_api import async_playwright
    except Exception as ex:
        return None, _disabled(f"Playwright недоступен: {ex!r}")
    try:
        pw = await async_playwright().start()
        args = ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--window-size=1920,1080"]
        browser = await pw.chromium.launch(headless=HEADLESS, args=args)
        context = await browser.new_context(
            viewport={"width": VIEWPORT[0], "height": VIEWPORT[1]},
            user_agent=USER_AGENT,
            accept_downloads=False,
        )
        page = await context.new_page()
        sid = sid or f"br-{uuid.uuid4().hex}"
        _REGISTRY[sid] = _BrowserSession(pw=pw, browser=browser, context=context, page=page)
        tool_context.state["__browser_sid__"] = sid
        return _REGISTRY[sid], {"reused": False, "sid": sid}
    except Exception as ex:
        return None, _disabled(f"Не удалось запустить Chromium: {ex!r}")
async def open_url(url: str, tool_context: ToolContext) -> dict:
    sess, meta = await _get_or_create_session(tool_context)
    if not sess:
        return meta  # disabled/error
    try:
        await sess.page.goto(url.strip(), wait_until="domcontentloaded", timeout=30_000)
        return {"status": "ok", "url": url, **meta}
    except Exception as ex:
        return {"status": "error", "message": str(ex), **meta}
async def get_current_url(tool_context: ToolContext) -> dict:
    sess, meta = await _get_or_create_session(tool_context)
    if not sess:
        return meta
    try:
        return {"status": "ok", "url": sess.page.url, **meta}
    except Exception as ex:
        return {"status": "error", "message": str(ex), **meta}
async def get_html(limit: int = 200_000, tool_context: ToolContext | None = None) -> dict:
    assert tool_context is not None, "ToolContext обязателен"
    sess, meta = await _get_or_create_session(tool_context)
    if not sess:
        return meta
    try:
        html = await sess.page.content()
        if limit and limit > 0:
            html = html[:limit]
            return {"status": "ok", "html": html, "truncated": True, **meta}
        return {"status": "ok", "html": html, "truncated": False, **meta}
    except Exception as ex:
        return {"status": "error", "message": str(ex), **meta}
async def scroll_by(pixels: int = 800, tool_context: ToolContext | None = None) -> dict:
    assert tool_context is not None
    sess, meta = await _get_or_create_session(tool_context)
    if not sess:
        return meta
    try:
        await sess.page.evaluate("window.scrollBy(0, arguments[0]);", int(pixels))
        await sess.page.wait_for_timeout(200)
        return {"status": "ok", "pixels": int(pixels), **meta}
    except Exception as ex:
        return {"status": "error", "message": str(ex), **meta}
async def click_text(text: str, exact: bool = False, tool_context: ToolContext | None = None) -> dict:
    assert tool_context is not None
    sess, meta = await _get_or_create_session(tool_context)
    if not sess:
        return meta
    try:
        locator = sess.page.get_by_text(text, exact=bool(exact))
        count = await locator.count()
        if count == 0:
            return {"status": "not_found", "by": "text", "query": text, "exact": bool(exact), **meta}
        first = locator.first
        await first.scroll_into_view_if_needed(timeout=5_000)
        await first.click(timeout=5_000)
        return {"status": "ok", "by": "text", "query": text, "exact": bool(exact), **meta}
    except Exception as ex:
        return {"status": "error", "message": str(ex), "by": "text", "query": text, "exact": bool(exact), **meta}
async def click_css(selector: str, tool_context: ToolContext | None = None) -> dict:
    assert tool_context is not None
    sess, meta = await _get_or_create_session(tool_context)
    if not sess:
        return meta
    try:
        loc = sess.page.locator(selector).first
        count = await loc.count()
        if count == 0:
            return {"status": "not_found", "by": "css", "selector": selector, **meta}
        await loc.scroll_into_view_if_needed(timeout=5_000)
        await loc.click(timeout=5_000)
        return {"status": "ok", "by": "css", "selector": selector, **meta}
    except Exception as ex:
        return {"status": "error", "message": str(ex), "selector": selector, **meta}
async def type_css(selector: str, text: str, clear: bool = True, tool_context: ToolContext | None = None) -> dict:
    assert tool_context is not None
    sess, meta = await _get_or_create_session(tool_context)
    if not sess:
        return meta
    try:
        loc = sess.page.locator(selector).first
        count = await loc.count()
        if count == 0:
            return {"status": "not_found", "selector": selector, **meta}
        await loc.scroll_into_view_if_needed(timeout=5_000)
        if clear:
            await loc.fill(text, timeout=5_000)
        else:
            await loc.type(text, timeout=5_000)
        return {"status": "ok", "selector": selector, "typed": len(text), "cleared": bool(clear), **meta}
    except Exception as ex:
        return {"status": "error", "message": str(ex), "selector": selector, **meta}
async def take_screenshot(tool_context: ToolContext) -> dict:
    sess, meta = await _get_or_create_session(tool_context)
    if not sess:
        return meta
    try:
        out_dir = pathlib.Path("output/screenshots")
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d-%H%M%S")
        fpath = out_dir / f"screenshot_{ts}.png"
        await sess.page.screenshot(path=str(fpath), full_page=False)
        with open(fpath, "rb") as rf:
            part = Part.from_bytes(data=rf.read(), mime_type="image/png")
        await tool_context.save_artifact(str(fpath), part)
        return {"status": "ok", "path": str(fpath), **meta}
    except Exception as ex:
        return {"status": "error", "message": str(ex), **meta}
async def browser_shutdown(tool_context: ToolContext) -> dict:
    sid = tool_context.state.get("__browser_sid__")
    sess = _REGISTRY.pop(sid, None) if sid else None
    tool_context.state.pop("__browser_sid__", None)
    if not sess:
        return {"status": "ok", "message": "no active browser", "sid": sid or None}
    try:
        try:
            await sess.context.close()
        except Exception:
            pass
        try:
            await sess.browser.close()
        except Exception:
            pass
        try:
            await sess.pw.stop()
        except Exception:
            pass
        return {"status": "ok", "message": "browser closed", "sid": sid}
    except Exception as ex:
        return {"status": "error", "message": str(ex), "sid": sid}
