"""HTTP-сессия форума с авторизацией (куки или логин/пароль)."""

import re
import requests
from bs4 import BeautifulSoup

from bot.config import (
    FORUM_URL, FORUM_USERNAME, FORUM_PASSWORD, FORUM_COOKIE,
    HEADERS, REQUEST_TIMEOUT, logger
)

_forum_session = None


def forum_session():
    """Общая HTTP-сессия для запросов к форуму.

    Если заданы FORUM_USERNAME/FORUM_PASSWORD — бот логинится на форуме,
    если задан FORUM_COOKIE — использует куки авторизованной сессии из браузера.
    Без учётных данных запросы идут как гость (сервер выдаёт только куку uid,
    этого достаточно для публичных разделов вроде viewforum и show_recent).
    """
    global _forum_session
    if _forum_session is not None:
        return _forum_session

    s = requests.Session()
    s.headers.update(HEADERS)
    # «прогреваем» сессию, чтобы сервер выдал гостевую куку uid
    try:
        s.get(f"{FORUM_URL}/index.php", timeout=REQUEST_TIMEOUT)
    except requests.RequestException as e:
        logger.warning(f"Не удалось получить гостевую куку: {e}")

    if FORUM_COOKIE:
        # куки вида "uid=...; pass=..." из DevTools браузера
        for part in FORUM_COOKIE.split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                s.cookies.set(k.strip(), v.strip())
        logger.info("Форум: используются куки авторизованной сессии (FORUM_COOKIE)")
    elif FORUM_USERNAME and FORUM_PASSWORD:
        logger.info(f"Форум: логин под пользователем '{FORUM_USERNAME}'...")
        try:
            r = s.get(f"{FORUM_URL}/login.php", timeout=REQUEST_TIMEOUT)
            soup = BeautifulSoup(r.text, "html.parser")
            form = soup.find("form", attrs={"action": re.compile(r"login\.php\?action=in")})
            data = {"form_sent": "1", "redirect_url": "",
                    "req_username": FORUM_USERNAME, "req_password": FORUM_PASSWORD,
                    "login": "Вход"}
            if form:
                for h in form.find_all("input", type="hidden"):
                    if h.get("name"):
                        data[h["name"]] = h.get("value", "")
            r2 = s.post(f"{FORUM_URL}/login.php?action=in", data=data, timeout=REQUEST_TIMEOUT)
            page = BeautifulSoup(r2.text, "html.parser")
            err = page.find("div", class_="blockerror") or page.find("p", class_="error")
            if err and ("Неверн" in err.get_text() or "неправильн" in err.get_text().lower()):
                logger.error("Форум: неверный логин/пароль — бот продолжит работать как гость")
            else:
                logger.info("Форум: вход выполнен")
        except requests.RequestException as e:
            logger.error(f"Форум: ошибка при логине ({e}) — работа как гость")
    else:
        logger.info("Форум: учётные данные не заданы — запросы от имени гостя")

    _forum_session = s
    return s
