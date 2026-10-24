"""Хендлер команды /atem — последние активные темы форума (обычный текст)."""

from bot.config import logger
from bot.cache import ensure_recent_cache
from bot.utils import split_message


async def atem_cmd(update, ctx):
    sm = await update.message.reply_text("🔍 Загружаю активные темы...")
    try:
        topics = await ensure_recent_cache()
        if not topics:
            await sm.edit_text("❌ Не удалось загрузить активные темы.")
            return
        L = [f"🔥 Активные темы ({len(topics)}):\n"]
        for i, t in enumerate(topics, 1):
            line = f"{i}. {t['title']}"
            meta_parts = []
            if t.get("forum"):
                meta_parts.append(t["forum"])
            if t.get("replies"):
                meta_parts.append(f"💬 {t['replies']}")
            tail = " · ".join(meta_parts)
            post_info = t["last_post_time"]
            if t["last_author"]:
                post_info += f" — {t['last_author']}"
            line += f"\n   └ {tail} · {post_info}" if tail else f"\n   └ {post_info}"
            line += f"\n   🔗 {t['last_post_url']}"
            L.append(line)
        msg = "\n\n".join(L)
        parts = split_message(msg, max_len=3900)
        for i, p in enumerate(parts):
            if i == 0:
                await sm.edit_text(p, disable_web_page_preview=True)
            else:
                await update.message.reply_text(p, disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Atem error: {e}", exc_info=True)
        try:
            await sm.edit_text(f"⚠️ Ошибка: {str(e)[:200]}")
        except Exception:
            pass
