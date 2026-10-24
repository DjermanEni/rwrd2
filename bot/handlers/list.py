"""Хендлер команды /list — нумерованный список персонажей.

Использует MarkdownV2: esc_md() экранирует ВСЕ спецсимволы v2, а md_link()
строит корректные ссылки. Классический Markdown (v1) ломался на именах с
"_", "[", "-" и т.п. (Telegram возвращал BadRequest, бот писал
"Не удалось загрузить список").
"""

from bot.config import logger
from bot.cache import ensure_cache, get_numbered_list, characters_cache
from bot.utils import esc_md, md_link, split_message


async def _send(update, sm, text, first=False):
    """Отправляет часть списка; при любой ошибке — фолбэк обычным текстом."""
    try:
        if first:
            await sm.edit_text(text, parse_mode="MarkdownV2", disable_web_page_preview=True)
        else:
            await update.message.reply_text(
                text, parse_mode="MarkdownV2", disable_web_page_preview=True
            )
    except Exception as e:
        logger.warning(f"MarkdownV2 не принят ({e}), отправляю обычным текстом")
        plain = text.replace("\\", "")
        try:
            if first:
                await sm.edit_text(plain, disable_web_page_preview=True)
            else:
                await update.message.reply_text(plain, disable_web_page_preview=True)
        except Exception as e2:
            logger.error(f"Фолбэк-отправка тоже не удалась: {e2}")


async def list_cmd(update, ctx):
    sm = await update.message.reply_text("📋 Загружаю список...")
    try:
        await ensure_cache()
        if not characters_cache:
            await sm.edit_text("❌ Не удалось загрузить список.")
            return
        ordered = get_numbered_list()
        L = [f"📋 *Персонажи \\({len(ordered)}\\):*"]
        L.append("*№ | Имя Фамилия | Позывной | Ссылка*")
        for i, c in enumerate(ordered, 1):
            n = esc_md(c.get("name", "?"))
            mon = esc_md(c.get("moniker", "")) or "—"
            link = md_link("анкета", c.get("topic_url", ""))
            L.append(f"{i}\\. {n} | {mon} | {link}")
        msg = "\n".join(L)
        parts = split_message(msg, max_len=3900)
        for i, p in enumerate(parts):
            await _send(update, sm, p, first=(i == 0))
    except Exception as e:
        logger.error(f"List error: {e}", exc_info=True)
        try:
            await sm.edit_text(f"⚠️ Ошибка: {str(e)[:200]}")
        except Exception:
            pass
