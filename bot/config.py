"""Конфигурация бота: настройки из переменных окружения и логирование."""

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
CACHE_TTL = 3600            # кэш анкет персонажей — 1 час
RECENT_TTL = 1800           # кэш активных тем (/atem) — 30 минут
MAX_PAGES = 25
REQUEST_TIMEOUT = 15        # секунд на один HTTP-запрос
REQUEST_DELAY = 0.5         # вежливая пауза между запросами к форуму
PARSE_CONCURRENCY = 8       # сколько анкет грузить параллельно

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

# Лог пишется в консоль И в файл (по умолчанию bot.log рядом с bot.py;
# путь можно задать переменной окружения LOG_FILE).
LOG_FILE = os.getenv("LOG_FILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "bot.log"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)
