"""Хендлер команды /list — нумерованный список персонажей.

Решение: обычный ТЕКСТ без parse_mode. Данные из форума (имена, позывные)
содержат слишком много спецсимволов (* _ [ ] . - = и т.д.), которые ломают
и Markdown, и MarkdownV2 — Telegram отвечал BadRequest, и бот писал
"Не удалось загрузить список". Ссылки в текстовом сообщении Telegram
автоматически делает кликабельными сам.
"""

from bot.config import logger
from bot.cache import ensure_cache, get_numbered_list, characters_cache
from bot.utils import split_message


async def list_cmd(update, ctx):
    sm = await update.message.reply_text("📋 Загружаю список...")
    try:
        await ensure_cache()
        if not characters_cache:
            await sm.edit_text("❌ Не удалось загрузить список.")
            return
        ordered = get_numbered_list()
        L = [f"📋 Персонажи ({len(ordered)}):\n",
             "№ | Имя Фамилия | Позывной | Ссылка"]
        for i, c in enumerate(ordered, 1):
            name = c.get("name", "?")
            mon = c.get("moniker", "") or "—"
            url = c.get("topic_url", "")
            L.append(f"{i}. {name} | {mon}")
            L.append(f"   🔗 {url}")
        msg = "\n".join(L)
        parts = split_message(msg, max_len=3900)
        for i, p in enumerate(parts):
            if i == 0:
                await sm.edit_text(p, disable_web_page_preview=True)
            else:
                await update.message.reply_text(p, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"List error: {e}", exc_info=True)
        try:
            await sm.edit_text(f"⚠️ Ошибка: {str(e)[:200]}")
        except Exception:
            pass
