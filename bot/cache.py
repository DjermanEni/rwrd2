"""Кэш персонажей и активных тем, поиск по кэшу."""

import re
import time

from bot.config import CACHE_TTL, RECENT_TTL, REQUEST_DELAY, logger
from bot.parser import get_forum_topics, parse_character_sheet, get_active_topics

characters_cache = {}
last_update = 0

recent_topics_cache = []
last_recent_update = 0


def update_characters_cache():
    """Загружает все темы раздела и парсит анкеты в кэш."""
    global characters_cache, last_update
    logger.info("Обновление кэша персонажей...")
    topics = get_forum_topics()
    nc = {}
    if not topics:
        logger.error("Темы не найдены!")
        return
    for i, topic in enumerate(topics):
        logger.info(f"Парсинг темы {i+1}/{len(topics)}: {topic['title']}")
        cd = parse_character_sheet(topic["url"])
        if cd:
            nc[topic["id"]] = {**cd, "topic_id": topic["id"], "topic_url": topic["url"], "topic_title": topic["title_full"], "author": topic["author"]}
            if "name" not in nc[topic["id"]] or not nc[topic["id"]].get("name"):
                nc[topic["id"]]["name"] = topic["title"]
            if "year" not in nc[topic["id"]] and topic["year"]:
                nc[topic["id"]]["year"] = topic["year"]
        time.sleep(REQUEST_DELAY)
    characters_cache = nc
    last_update = time.time()
    logger.info(f"Кэш обновлён. Найдено персонажей: {len(characters_cache)}")


def ensure_cache():
    """Обновляет кэш персонажей, если он пуст или устарел (CACHE_TTL)."""
    if not characters_cache or (time.time() - last_update) > CACHE_TTL:
        update_characters_cache()


def get_numbered_list():
    """Список персонажей, отсортированный по алфавиту; каждому присвоен номер (1..N)."""
    ensure_cache()
    ordered = sorted(characters_cache.values(), key=lambda x: x.get("name", "").lower())
    return ordered


def search_character(q):
    """Ищет персонажа по имени, позывному, номеру в /list или названию темы."""
    ensure_cache()
    ql = q.lower().strip()
    # 1) Точное совпадение по имени
    for c in characters_cache.values():
        if c.get("name", "").lower() == ql:
            return c
    # 2) Точное совпадение по позывному
    for c in characters_cache.values():
        if c.get("moniker", "").lower() == ql:
            return c
    # 3) Номер из списка /list (например "7" или "#7")
    num_m = re.fullmatch(r"#?(\d+)", ql)
    if num_m:
        ordered = get_numbered_list()
        idx = int(num_m.group(1))
        if 1 <= idx <= len(ordered):
            return ordered[idx - 1]
    # 4) Частичное совпадение по имени
    for c in characters_cache.values():
        if ql in c.get("name", "").lower():
            return c
    # 5) Частичное совпадение по позывному
    for c in characters_cache.values():
        if ql in c.get("moniker", "").lower():
            return c
    # 6) Частичное совпадение по названию темы
    for c in characters_cache.values():
        if ql in c.get("topic_title", "").lower():
            return c
    return None


def ensure_recent_cache():
    """Кэш активных тем обновляется не чаще одного раза в RECENT_TTL (30 минут)."""
    global recent_topics_cache, last_recent_update
    if not recent_topics_cache or (time.time() - last_recent_update) > RECENT_TTL:
        fresh = get_active_topics()
        if fresh:
            recent_topics_cache = fresh
            last_recent_update = time.time()
        elif not recent_topics_cache:
            return []
    return recent_topics_cache
