"""Хендлер команды /atem — последние активные темы форума."""

from bot.config import logger
from bot.cache import ensure_recent_cache
from bot.utils import esc_md


async def atem_cmd(update, ctx):
    sm = await update.message.reply_text("🔍 Загружаю активные темы...")
    try:
        topics = await ensure_recent_cache()
        if not topics:
            await sm.edit_text("❌ Не удалось загрузить активные темы.")
            return
        L = [f"🔥 *Активные темы ({len(topics)}):*\n"]
        for i, t in enumerate(topics, 1):
            line = f"{i}. [{esc_md(t['title'])}]({t['last_post_url']})"
            meta_parts = []
            if t.get("forum"):
                meta_parts.append(esc_md(t["forum"]))
            if t.get("replies"):
                meta_parts.append(f"💬 {t['replies']}")
            tail = " · ".join(meta_parts)
            post_info = esc_md(t["last_post_time"])
            if t["last_author"]:
                post_info += f" — {esc_md(t['last_author'])}"
            if tail:
                line += f"\n   └ {tail} · {post_info}"
            else:
                line += f"\n   └ {post_info}"
            L.append(line)
        msg = "\n\n".join(L)
        if len(msg) > 4000:
            parts, cur = [], ""
            for line in L:
                if len(cur) + len(line) + 2 > 3900:
                    parts.append(cur)
                    cur = line + "\n\n"
                else:
                    cur += line + "\n\n"
            if cur:
                parts.append(cur)
            for i, p in enumerate(parts):
                if i == 0:
                    await sm.edit_text(p, parse_mode="Markdown", disable_web_page_preview=True)
                else:
                    await update.message.reply_text(p, parse_mode="Markdown", disable_web_page_preview=True)
        else:
            await sm.edit_text(msg, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Atem error: {e}")
        await sm.edit_text(f"⚠️ Ошибка: {str(e)[:200]}")
