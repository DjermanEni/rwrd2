"""Асинхронный кэш персонажей и активных тем, поиск по кэшу.

update_characters_cache() параллелит загрузку анкет: все темы запускаются
одновременно, но semaphore ограничивает число одновременных запросов
(PARSE_CONCURRENCY). Пауза REQUEST_DELAY — «между волнами»: её засыпает
каждый i-й task (i % PARSE_CONCURRENCY == 0), поэтому новые запросы
стартуют пачками раз в REQUEST_DELAY секунд. Средняя скорость обращений
к форуму та же, что у последовательной версии, но сеть не простаивает:
ускорение ~PARSE_CONCURRENCY раз (2 минуты -> ~15-20 секунд).
"""

import asyncio
import re
import time

from bot.config import CACHE_TTL, RECENT_TTL, REQUEST_DELAY, PARSE_CONCURRENCY, logger
from bot.parser import get_forum_topics, parse_character_sheet, get_active_topics

characters_cache = {}
last_update = 0

recent_topics_cache = []
last_recent_update = 0

# Lock защищает от одновременного обновления кэша несколькими запросами
# (например, если двое прислали /char до первого заполнения).
_cache_lock = asyncio.Lock()
_recent_lock = asyncio.Lock()


async def _parse_one(idx, topic, sem, done_counter, total):
    """Парсит одну тему; семафор ограничивает параллелизм, пауза — щадит форум."""
    async with sem:
        # имитация «волн»: каждый N-й запущенный task притормаживает старт
        # следующих, сохраняя исходный rate-limit REQUEST_DELAY
        if idx % PARSE_CONCURRENCY == 0:
            await asyncio.sleep(REQUEST_DELAY)
        cd = await parse_character_sheet(topic["url"])
    done_counter[0] += 1
    if done_counter[0] % 25 == 0 or done_counter[0] == total:
        logger.info(f"Парсинг анкет: {done_counter[0]}/{total}")
    return topic, cd


async def update_characters_cache():
    """Загружает все темы раздела и параллельно парсит анкеты в кэш."""
    global characters_cache, last_update
    logger.info("Обновление кэша персонажей...")
    topics = await get_forum_topics()
    nc = {}
    if not topics:
        logger.error("Темы не найдены!")
        return
    sem = asyncio.Semaphore(PARSE_CONCURRENCY)
    done_counter = [0]
    results = await asyncio.gather(*(_parse_one(i, t, sem, done_counter, len(topics))
                                     for i, t in enumerate(topics)))

    for topic, cd in results:
        if cd:
            entry = {**cd, "topic_id": topic["id"], "topic_url": topic["url"],
                     "topic_title": topic["title_full"], "author": topic["author"]}
            if not entry.get("name"):
                entry["name"] = topic["title"]
            if "year" not in entry and topic["year"]:
                entry["year"] = topic["year"]
            nc[topic["id"]] = entry

    characters_cache = nc
    last_update = time.time()
    logger.info(f"Кэш обновлён. Найдено персонажей: {len(characters_cache)}")


async def ensure_cache():
    """Обновляет кэш персонажей, если он пуст или устарел (CACHE_TTL)."""
    if characters_cache and (time.time() - last_update) <= CACHE_TTL:
        return
    async with _cache_lock:
        # повторная проверка: пока ждали lock, кэш мог обновить другой task
        if not characters_cache or (time.time() - last_update) > CACHE_TTL:
            await update_characters_cache()


def get_numbered_list():
    """Список персонажей, отсортированный по алфавиту; каждому присвоен номер (1..N)."""
    ordered = sorted(characters_cache.values(), key=lambda x: x.get("name", "").lower())
    return ordered


async def search_character(q):
    """Ищет персонажа по имени, позывному, номеру в /list или названию темы."""
    await ensure_cache()
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


async def ensure_recent_cache():
    """Кэш активных тем обновляется не чаще одного раза в RECENT_TTL (30 минут)."""
    global recent_topics_cache, last_recent_update
    if recent_topics_cache and (time.time() - last_recent_update) <= RECENT_TTL:
        return recent_topics_cache
    async with _recent_lock:
        # double-check под локом
        if not recent_topics_cache or (time.time() - last_recent_update) > RECENT_TTL:
            fresh = await get_active_topics()
            if fresh:
                recent_topics_cache = fresh
                last_recent_update = time.time()
            elif not recent_topics_cache:
                return []
    return recent_topics_cache
