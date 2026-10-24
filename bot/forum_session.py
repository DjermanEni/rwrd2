"""HTTP-сессия форума с авторизацией (куки или логин/пароль), на базе httpx.

Асинхронная версия: один AsyncClient переиспользуется всеми запросами,
куки авторизации хранятся в его cookie-хранилище.
"""

import re
import httpx
from bs4 import BeautifulSoup

from bot.config import (
    FORUM_URL, FORUM_USERNAME, FORUM_PASSWORD, FORUM_COOKIE,
    HEADERS, REQUEST_TIMEOUT, logger
)

_client = None


def client():
    """Общий асинхронный HTTP-клиент для запросов к форуму.

    Если заданы FORUM_USERNAME/FORUM_PASSWORD — бот логинится на форуме,
    если задан FORUM_COOKIE — использует куки авторизованной сессии из браузера.
    Без учётных данных запросы идут как гость (сервер выдаёт только куку uid,
    этого достаточно для публичных разделов вроде viewforum и show_recent).
    """
    global _client
    if _client is not None:
        return _client

    c = httpx.AsyncClient(
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
        follow_redirects=True,
    )

    # «прогреваем» сессию синхронно, чтобы сервер выдал гостевую куку uid.
    # Дёшево и безопасно делать это до входа в event loop.
    try:
        warm = httpx.Client(headers=HEADERS, timeout=REQUEST_TIMEOUT, follow_redirects=True)
        r = warm.get(f"{FORUM_URL}/index.php")
        for k, v in r.cookies.items():
            c.cookies.set(k, v)
        warm.close()
    except httpx.HTTPError as e:
        logger.warning(f"Не удалось получить гостевую куку: {e}")

    if FORUM_COOKIE:
        # куки вида "uid=...; pass=..." из DevTools браузера
        for part in FORUM_COOKIE.split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                c.cookies.set(k.strip(), v.strip())
        logger.info("Форум: используются куки авторизованной сессии (FORUM_COOKIE)")
    elif FORUM_USERNAME and FORUM_PASSWORD:
        logger.info(f"Форум: логин под пользователем '{FORUM_USERNAME}'...")
        # Логин делаем один раз синхронно (до старта event loop) и переносим
        # полученные куки (sid и др.) в асинхронный клиент.
        _sync_login(c)
    else:
        logger.info("Форум: учётные данные не заданы — запросы от имени гостя")

    _client = c
    return c


def _sync_login(async_c):
    """Одноразовый синхронный логин; полученные куки переносим в AsyncClient."""
    s = httpx.Client(headers=HEADERS, timeout=REQUEST_TIMEOUT, follow_redirects=True)
    try:
        r = s.get(f"{FORUM_URL}/login.php")
        soup = BeautifulSoup(r.text, "html.parser")
        form = soup.find("form", attrs={"action": re.compile(r"login\.php\?action=in")})
        data = {"form_sent": "1", "redirect_url": "",
                "req_username": FORUM_USERNAME, "req_password": FORUM_PASSWORD,
                "login": "Вход"}
        if form:
            for h in form.find_all("input", type="hidden"):
                if h.get("name"):
                    data[h["name"]] = h.get("value", "")
        r2 = s.post(f"{FORUM_URL}/login.php?action=in", data=data)
        page = BeautifulSoup(r2.text, "html.parser")
        err = page.find("div", class_="blockerror") or page.find("p", class_="error")
        if err and ("Неверн" in err.get_text() or "неправильн" in err.get_text().lower()):
            logger.error("Форум: неверный логин/пароль — бот продолжит работать как гость")
        else:
            logger.info("Форум: вход выполнен")
        # переносим куки (sid и др.) в асинхронный клиент
        for k, v in s.cookies.items():
            async_c.cookies.set(k, v)
    except httpx.HTTPError as e:
        logger.error(f"Форум: ошибка при логине ({e}) — работа как гость")
    finally:
        s.close()


async def close_client():
    """Закрывает общий клиент (вызывается при остановке бота)."""
    global _client
    if _client is not None:
        try:
            await _client.aclose()
        except Exception as e:
            logger.warning(f"Ошибка при закрытии HTTP-клиента: {e}")
        _client = None
