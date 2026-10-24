"""Хендлер команды /list — нумерованный список персонажей."""

from bot.config import logger
from bot.cache import ensure_cache, get_numbered_list, characters_cache
from bot.utils import esc_md, split_message


async def list_cmd(update, ctx):
    sm = await update.message.reply_text("📋 Загружаю список...")
    try:
        await ensure_cache()
        if not characters_cache:
            await sm.edit_text("❌ Не удалось загрузить список.")
            return
        ordered = get_numbered_list()
        L = [f"📋 *Персонажи ({len(ordered)}):*\n"]
        L.append("*№ | Имя Фамилия | Позывной | Ссылка*")
        L.append("_")   ← одиночный "_" это НЕвалидный Markdown
        for i, c in enumerate(ordered, 1):
            n = esc_md(c.get("name", "?"))
            mon = esc_md(c.get("moniker", "")) or "—"
            url = c.get("topic_url", "")
            line = f"{i}. {n} | {mon} | [анкета]({url})"
            L.append(line)
        msg = "\n".join(L)
        parts = split_message(msg, max_len=3900)
        for i, p in enumerate(parts):
            if i == 0:
                await sm.edit_text(p, parse_mode="Markdown", disable_web_page_preview=True)
            else:
                await update.message.reply_text(p, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"List error: {e}")
        await sm.edit_text(f"⚠️ Ошибка: {str(e)[:200]}")
