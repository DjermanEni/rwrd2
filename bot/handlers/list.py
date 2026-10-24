"""Хендлер команды /list — нумерованный список персонажей.

Обычный ТЕКСТ без parse_mode (спецсимволы из форума ломали Markdown).
Дополнительно: если кэш пуст или устарел, обновление запускается
фон-задачей, а пользователю сразу приходит частичный список (если он
есть) — чтобы /list не падал с «Не удалось загрузить список» при
временных проблемах сети/форума.
"""

import asyncio

from bot.config import logger
import bot.cache as cache
from bot.cache import get_numbered_list
from bot.utils import split_message


def _build_parts():
    ordered = get_numbered_list()
    L = [f"📋 Персонажи ({len(ordered)}):\n",
         "№ | Имя Фамилия | Позывной"]
    for i, c in enumerate(ordered, 1):
        name = c.get("name", "?")
        mon = c.get("moniker", "") or "—"
        url = c.get("topic_url", "")
        L.append(f"{i}. {name} | {mon}")
        if url:
            L.append(f"   🔗 {url}")
    return split_message("\n".join(L), max_len=3900)


async def _send_parts(update, sm, parts):
    for i, p in enumerate(parts):
        try:
            if i == 0:
                await sm.edit_text(p, disable_web_page_preview=True)
            else:
                await update.message.reply_text(p, disable_web_page_preview=True)
        except Exception as e:
            logger.error(f"List send error: {e}", exc_info=True)
            # черным по белому: пробуем отправить коротким текстом без ссылок
            try:
                fallback = "\n".join(l.split("   🔗")[0] for l in p.splitlines())[:4000]
                if i == 0:
                    await sm.edit_text(fallback)
                else:
                    await update.message.reply_text(fallback)
            except Exception as e2:
                logger.error(f"List fallback error: {e2}", exc_info=True)


async def list_cmd(update, ctx):
    sm = await update.message.reply_text("📋 Загружаю список...")
    try:
        # 1) Быстрая попытка: если кэш уже есть — отдаём его сразу,
        #    обновление (при необходимости) — фоном, не блокируя ответ.
        if cache.characters_cache:
            await _send_parts(update, sm, _build_parts())
            asyncio.create_task(_bg_refresh())
            return

        # 2) Кэша нет — дожидаемся загрузки (таймаут, чтобы не зависнуть
        #    навсегда при проблемах с форумом; сетевые ошибки ensure_cache
        #    внутри себя логирует и оставляет кэш пустым).
        try:
            await asyncio.wait_for(cache.ensure_cache(), timeout=120)
        except (asyncio.TimeoutError, Exception) as e:
            logger.error(f"List error: загрузка кэша не удалась: {e}", exc_info=True)

        if cache.characters_cache:
            await _send_parts(update, sm, _build_parts())
        else:
            await sm.edit_text(
                "❌ Не удалось загрузить список: форум недоступен или "
                "изменилась вёрстка.\nПопробуйте позже; поиск /char по "
                "имени может работать по уже загруженным анкетам."
            )
    except Exception as e:
        logger.error(f"List error: {e}", exc_info=True)
        try:
            await sm.edit_text(f"⚠️ Ошибка: {str(e)[:200]}")
        except Exception:
            pass


async def _bg_refresh():
    """Фоновое обновление кэша после мгновенного ответа по старым данным."""
    try:
        await cache.ensure_cache()
    except Exception as e:
        logger.warning(f"Фоновое обновление кэша не удалось: {e}")
