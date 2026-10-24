"""Конфигурация бота — настройки, токены, параметры запросов."""

import os
import logging

# Токен лучше задавать через переменную окружения BOT_TOKEN,
# а не хранить прямо в коде.
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# Аккаунт форума (нужен, если какие-то разделы/темы скрыты от гостей).
FORUM_USERNAME = os.getenv("FORUM_USERNAME", "")
FORUM_PASSWORD = os.getenv("FORUM_PASSWORD", "")

# Альтернатива логину по паролю — куки авторизованной сессии из браузера:
# uid=...; pass=...  (см. README)
FORUM_COOKIE = os.getenv("FORUM_COOKIE", "")

FORUM_URL = "https://rwrd.rusff.me"
FORUM_ID = 25

CACHE_TTL = 3600
RECENT_TTL = 1800  # кэш активных тем (/atem) — 30 минут
MAX_PAGES = 25
REQUEST_TIMEOUT = 15

# Параметры асинхронного парсинга (httpx)
PARSE_CONCURRENCY = 8   # сколько тем парсим одновременно
REQUEST_DELAY = 0.5     # пауза между «волнами» запросов, чтобы не душить форум

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)
